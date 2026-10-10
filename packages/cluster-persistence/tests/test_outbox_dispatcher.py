from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest

from geelark_cluster_persistence import (
    claim_outbox_batch,
    mark_outbox_delivered,
    retry_outbox_event,
)

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere TEST_DATABASE_URL con PostgreSQL de prueba")

NODE_ID = UUID("22222222-2222-4222-8222-222222222222")
INSTANCE_ID = UUID("66666666-6666-4666-8666-666666666666")
OPERATION_ID = UUID("55555555-5555-4555-8555-555555555555")
REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")


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


def seed_event():
    event_id = uuid4()
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state)
            VALUES (%s, 'node-outbox', 'active', 'healthy')
            """,
            (NODE_ID,),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.instances
                (instance_id, desired_state, observed_state, owner_node_id, assignment_epoch,
                 lease_expires_at, engine_name, engine_version, image_digest, android_api_level, android_abi)
            VALUES (%s, 'running', 'reserved', %s, 1, now() + interval '5 minutes',
                    'test-engine', '0.1', %s, 35, 'x86_64')
            """,
            (INSTANCE_ID, NODE_ID, "sha256:" + "a" * 64),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.operations
                (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type, status)
            VALUES (%s, %s, %s, %s, 1, 'assign', 'accepted')
            """,
            (OPERATION_ID, REQUEST_ID, INSTANCE_ID, NODE_ID),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.outbox_events
                (event_id, deduplication_key, instance_id, assignment_epoch,
                 operation_id, event_type, payload)
            VALUES (%s, %s, %s, 1, %s, 'assignment.requested', %s)
            """,
            (event_id, f"assignment:{INSTANCE_ID}:1", INSTANCE_ID, OPERATION_ID, psycopg.types.json.Jsonb({"operation_id": str(OPERATION_ID)})),
        )
        conn.commit()
    return event_id


def test_two_workers_never_claim_the_same_event_concurrently():
    seed_event()
    barrier = Barrier(2)
    workers = [uuid4(), uuid4()]

    def worker(worker_id):
        barrier.wait(timeout=10)
        with psycopg.connect(DATABASE_URL) as conn:
            return claim_outbox_batch(conn, worker_id, batch_size=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, workers))

    assert sorted(len(batch) for batch in results) == [0, 1]
    claimed = next(batch[0] for batch in results if batch)
    assert claimed.attempt_count == 1
    with psycopg.connect(DATABASE_URL) as conn:
        assert conn.execute("SELECT count(*) FROM geelark_control.outbox_events WHERE status = 'inflight'").fetchone()[0] == 1


def test_expired_claim_is_recovered_and_old_worker_cannot_ack():
    event_id = seed_event()
    old_worker = uuid4()
    new_worker = uuid4()
    with psycopg.connect(DATABASE_URL) as conn:
        first = claim_outbox_batch(conn, old_worker, lease_seconds=30)
    assert len(first) == 1

    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE geelark_control.outbox_events SET claim_until = now() - interval '1 second' WHERE event_id = %s",
            (event_id,),
        )
        conn.commit()

    with psycopg.connect(DATABASE_URL) as conn:
        recovered = claim_outbox_batch(conn, new_worker, lease_seconds=30)
    assert len(recovered) == 1
    assert recovered[0].attempt_count == 2
    assert recovered[0].event_id == event_id

    with psycopg.connect(DATABASE_URL) as conn:
        assert mark_outbox_delivered(conn, event_id, old_worker) is False
    with psycopg.connect(DATABASE_URL) as conn:
        assert mark_outbox_delivered(conn, event_id, new_worker) is True
    with psycopg.connect(DATABASE_URL) as conn:
        status, delivered_at = conn.execute(
            "SELECT status, delivered_at FROM geelark_control.outbox_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        assert status == "delivered"
        assert delivered_at is not None


def test_retry_backoff_and_max_attempts_move_event_to_dead():
    event_id = seed_event()
    worker = uuid4()
    with psycopg.connect(DATABASE_URL) as conn:
        first = claim_outbox_batch(conn, worker, lease_seconds=30)
    assert first[0].attempt_count == 1

    with psycopg.connect(DATABASE_URL) as conn:
        status = retry_outbox_event(
            conn, event_id, worker, error_code="AGENT_UNAVAILABLE",
            delay_seconds=3600, max_attempts=2,
        )
    assert status == "pending"
    with psycopg.connect(DATABASE_URL) as conn:
        available_at = conn.execute(
            "SELECT available_at FROM geelark_control.outbox_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()[0]
        assert available_at > datetime.now(timezone.utc)
        assert claim_outbox_batch(conn, worker, batch_size=1) == []

    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE geelark_control.outbox_events SET available_at = now() WHERE event_id = %s",
            (event_id,),
        )
        conn.commit()
    with psycopg.connect(DATABASE_URL) as conn:
        second = claim_outbox_batch(conn, worker, lease_seconds=30)
    assert second[0].attempt_count == 2

    with psycopg.connect(DATABASE_URL) as conn:
        status = retry_outbox_event(
            conn, event_id, worker, error_code="AGENT_UNAVAILABLE",
            delay_seconds=5, max_attempts=2,
        )
    assert status == "dead"
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT status, claimed_by, claim_until, attempt_count, last_error_code FROM geelark_control.outbox_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        assert row == ("dead", None, None, 2, "AGENT_UNAVAILABLE")


def test_old_worker_cannot_requeue_after_claim_is_replaced():
    event_id = seed_event()
    old_worker = uuid4()
    new_worker = uuid4()
    with psycopg.connect(DATABASE_URL) as conn:
        claim_outbox_batch(conn, old_worker, lease_seconds=30)
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE geelark_control.outbox_events SET claim_until = now() - interval '1 second' WHERE event_id = %s",
            (event_id,),
        )
        conn.commit()
    with psycopg.connect(DATABASE_URL) as conn:
        claim_outbox_batch(conn, new_worker, lease_seconds=30)

    with psycopg.connect(DATABASE_URL) as conn:
        result = retry_outbox_event(conn, event_id, old_worker, error_code="STALE_WORKER")
    assert result is None
    with psycopg.connect(DATABASE_URL) as conn:
        status, claimed_by = conn.execute(
            "SELECT status, claimed_by FROM geelark_control.outbox_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        assert status == "inflight"
        assert claimed_by == new_worker
