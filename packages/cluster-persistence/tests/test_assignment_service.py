from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest

from geelark_cluster_persistence import (
    AssignmentRequest,
    IdempotencyConflict,
    InstanceAlreadyAssigned,
    InvalidAssignmentRequest,
    InstanceStateBlocked,
    InsufficientCapacity,
    assign_instance,
)

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere TEST_DATABASE_URL con PostgreSQL de prueba")

NODE_A = UUID("22222222-2222-4222-8222-222222222222")
NODE_B = UUID("33333333-3333-4333-8333-333333333333")
INSTANCE_A = UUID("66666666-6666-4666-8666-666666666666")
INSTANCE_B = UUID("77777777-7777-4777-8777-777777777777")


@pytest.fixture(autouse=True)
def clean_database():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            TRUNCATE TABLE
                geelark_control.outbox_events,
                geelark_control.assignment_events,
                geelark_control.idempotency_records,
                geelark_control.resource_reservations,
                geelark_control.operations,
                geelark_control.instances,
                geelark_control.node_resource_capacity,
                geelark_control.nodes
            RESTART IDENTITY CASCADE
            """
        )
        conn.commit()
    yield


def seed_database(*, cpu_capacity=Decimal("2.000"), instance_states=None):
    instance_states = instance_states or {
        INSTANCE_A: ("stopped", None, 0, None),
        INSTANCE_B: ("stopped", None, 0, None),
    }
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO geelark_control.nodes
                (node_id, display_name, admin_state, health_state)
            VALUES
                (%s, 'node-a', 'active', 'healthy'),
                (%s, 'node-b', 'active', 'healthy')
            """,
            (NODE_A, NODE_B),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.node_resource_capacity
                (node_id, cpu_units, memory_capacity_bytes, storage_capacity_bytes,
                 memory_safety_margin_bytes, storage_safety_margin_bytes, measured_at, confidence)
            VALUES
                (%s, %s, 8192, 16384, 1024, 1024, now(), 'configured'),
                (%s, 2.0, 8192, 16384, 1024, 1024, now(), 'configured')
            """,
            (NODE_A, cpu_capacity, NODE_B),
        )
        for instance_id, (state, owner, epoch, lease) in instance_states.items():
            conn.execute(
                """
                INSERT INTO geelark_control.instances
                    (instance_id, desired_state, observed_state, owner_node_id,
                     assignment_epoch, lease_expires_at)
                VALUES (%s, 'stopped', %s, %s, %s, %s)
                """,
                (instance_id, state, owner, epoch, lease),
            )
        conn.commit()


def make_request(*, instance_id=INSTANCE_A, node_id=NODE_A, key=None, cpu=1, memory=1000, storage=2000):
    return AssignmentRequest(
        scope="test-suite",
        idempotency_key=key or f"test-idempotency-{uuid4()}",
        request_id=uuid4(),
        instance_id=instance_id,
        node_id=node_id,
        cpu_units=cpu,
        memory_bytes=memory,
        storage_bytes=storage,
        lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        engine_name="test-engine",
        engine_version="0.1",
        android_api_level=35,
        android_abi="x86_64",
        image_digest="sha256:" + "a" * 64,
    )


def test_assignment_commits_owner_reservation_operation_audit_and_outbox():
    seed_database()
    request = make_request()

    with psycopg.connect(DATABASE_URL) as conn:
        response = assign_instance(conn, request)

    assert response["status"] == "accepted"
    assert response["observed_state"] == "reserved"
    assert response["assignment_epoch"] == 1

    with psycopg.connect(DATABASE_URL) as conn:
        owner, epoch, state = conn.execute(
            "SELECT owner_node_id, assignment_epoch, observed_state FROM geelark_control.instances WHERE instance_id = %s",
            (INSTANCE_A,),
        ).fetchone()
        assert (owner, epoch, state) == (NODE_A, 1, "reserved")
        assert conn.execute("SELECT count(*) FROM geelark_control.resource_reservations WHERE instance_id = %s AND status = 'held'", (INSTANCE_A,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM geelark_control.operations WHERE instance_id = %s", (INSTANCE_A,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM geelark_control.assignment_events WHERE instance_id = %s", (INSTANCE_A,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM geelark_control.outbox_events WHERE instance_id = %s AND status = 'pending'", (INSTANCE_A,)).fetchone()[0] == 1


def test_same_idempotency_key_and_payload_returns_original_response():
    seed_database()
    request = make_request(key="idempotency-key-same-payload")

    with psycopg.connect(DATABASE_URL) as conn:
        first = assign_instance(conn, request)
    with psycopg.connect(DATABASE_URL) as conn:
        second = assign_instance(conn, request)

    assert second == first
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.operations").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM geelark_control.outbox_events").fetchone()[0] == 1


def test_same_idempotency_key_with_different_payload_is_conflict():
    seed_database()
    request = make_request(key="idempotency-key-conflict")

    with psycopg.connect(DATABASE_URL) as conn:
        assign_instance(conn, request)

    changed = replace(request, memory_bytes=request.memory_bytes + 1)
    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(IdempotencyConflict):
            assign_instance(conn, changed)


def test_concurrent_requests_cannot_assign_one_instance_twice():
    seed_database()
    requests = [
        make_request(node_id=NODE_A, key="concurrent-assignment-key-a"),
        make_request(node_id=NODE_B, key="concurrent-assignment-key-b"),
    ]
    barrier = Barrier(2)

    def worker(request):
        barrier.wait(timeout=10)
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                return ("accepted", assign_instance(conn, request))
        except InstanceAlreadyAssigned:
            return ("already-assigned", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, requests))

    assert sorted(result[0] for result in results) == ["accepted", "already-assigned"]
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.resource_reservations WHERE instance_id = %s AND status IN ('held', 'uncertain')", (INSTANCE_A,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM geelark_control.operations WHERE instance_id = %s", (INSTANCE_A,)).fetchone()[0] == 1


def test_concurrent_assignments_cannot_overbook_node_capacity():
    seed_database(cpu_capacity=Decimal("1.500"))
    requests = [
        make_request(instance_id=INSTANCE_A, node_id=NODE_A, key="capacity-race-key-a", cpu=1),
        make_request(instance_id=INSTANCE_B, node_id=NODE_A, key="capacity-race-key-b", cpu=1),
    ]
    barrier = Barrier(2)

    def worker(request):
        barrier.wait(timeout=10)
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                return ("accepted", assign_instance(conn, request))
        except InsufficientCapacity:
            return ("capacity-rejected", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, requests))

    assert sorted(result[0] for result in results) == ["accepted", "capacity-rejected"]
    with psycopg.connect(DATABASE_URL) as conn:
        used = conn.execute(
            "SELECT COALESCE(SUM(cpu_units), 0) FROM geelark_control.resource_reservations WHERE node_id = %s AND status IN ('held', 'uncertain')",
            (NODE_A,),
        ).fetchone()[0]
        assert Decimal(str(used)) <= Decimal("1.500")


def test_unknown_instance_state_blocks_reassignment_even_without_owner():
    seed_database(instance_states={
        INSTANCE_A: ("unknown", None, 0, None),
        INSTANCE_B: ("stopped", None, 0, None),
    })
    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(InstanceStateBlocked):
            assign_instance(conn, make_request())
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.operations").fetchone()[0] == 0


def test_expired_lease_and_uncertain_reservation_do_not_release_owner():
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    seed_database(instance_states={
        INSTANCE_A: ("unknown", NODE_A, 3, expired),
        INSTANCE_B: ("stopped", None, 0, None),
    })
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO geelark_control.resource_reservations
                (reservation_id, instance_id, node_id, assignment_epoch, cpu_units,
                 memory_bytes, storage_bytes, status)
            VALUES (%s, %s, %s, 3, 1, 1000, 2000, 'uncertain')
            """,
            (uuid4(), INSTANCE_A, NODE_A),
        )
        conn.commit()

    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(InstanceStateBlocked):
            assign_instance(conn, make_request(node_id=NODE_B))
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.resource_reservations WHERE instance_id = %s AND status = 'uncertain'", (INSTANCE_A,)).fetchone()[0] == 1


def test_non_finite_cpu_is_rejected_before_database_mutation():
    seed_database()
    request = replace(make_request(), cpu_units=float("nan"))
    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(InvalidAssignmentRequest):
            assign_instance(conn, request)
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.idempotency_records").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM geelark_control.operations").fetchone()[0] == 0


def test_failure_after_reservation_rolls_back_every_write():
    """Un fallo tras crear reservas no debe dejar filas parciales."""
    seed_database()
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            CREATE OR REPLACE FUNCTION geelark_control.test_reject_outbox_insert()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'injected outbox failure';
            END
            $$
            """
        )
        conn.execute(
            """
            CREATE TRIGGER test_reject_outbox_insert
            BEFORE INSERT ON geelark_control.outbox_events
            FOR EACH ROW EXECUTE FUNCTION geelark_control.test_reject_outbox_insert()
            """
        )
        conn.commit()

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with pytest.raises(psycopg.Error, match="injected outbox failure"):
                assign_instance(conn, make_request(key="rollback-injected-failure-key"))
    finally:
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute("DROP TRIGGER IF EXISTS test_reject_outbox_insert ON geelark_control.outbox_events")
            conn.execute("DROP FUNCTION IF EXISTS geelark_control.test_reject_outbox_insert()")
            conn.commit()

    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT owner_node_id FROM geelark_control.instances WHERE instance_id = %s", (INSTANCE_A,)).fetchone()[0] is None
        assert conn.execute("SELECT count(*) FROM geelark_control.resource_reservations").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM geelark_control.operations").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM geelark_control.assignment_events").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM geelark_control.outbox_events").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM geelark_control.idempotency_records").fetchone()[0] == 0


def test_active_observed_state_without_owner_fails_closed():
    seed_database(instance_states={
        INSTANCE_A: ("running", None, 0, None),
        INSTANCE_B: ("stopped", None, 0, None),
    })
    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(InstanceStateBlocked):
            assign_instance(conn, make_request())
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.operations").fetchone()[0] == 0
