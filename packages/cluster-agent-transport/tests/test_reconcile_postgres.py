import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb

from cluster_agent_transport.domain_handlers import make_postgres_agent_handlers
from cluster_agent_transport.policy import AgentPrincipal, Operation


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def seed_task(status="running", result_summary=None):
    connect = lambda: psycopg.connect(DATABASE_URL)
    node_id, credential_id = uuid4(), uuid4()
    instance_id, operation_id = uuid4(), uuid4()
    task_id = operation_id
    now = datetime.now(timezone.utc)
    summary = result_summary or {}
    terminal = status in {"succeeded", "rejected", "failed", "cancelled"}
    with connect() as conn:
        conn.execute(
            "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state) VALUES (%s, %s, 'active', 'healthy')",
            (node_id, "test-reconcile-" + str(node_id)),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.node_credentials
                (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at)
            VALUES (%s, %s, %s, 'active', %s, %s, %s)
            """,
            (
                credential_id, node_id, hashlib.sha256(b"test-token").hexdigest(),
                now, now + timedelta(hours=1), now,
            ),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.instances
                (instance_id, desired_state, observed_state, owner_node_id, assignment_epoch, lease_expires_at)
            VALUES (%s, 'running', 'reserved', %s, 3, %s)
            """,
            (instance_id, node_id, now + timedelta(minutes=5)),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.operations
                (operation_id, request_id, instance_id, node_id, assignment_epoch,
                 operation_type, status, result_summary, completed_at)
            VALUES (%s, %s, %s, %s, 3, 'assign', %s, %s, %s)
            """,
            (
                operation_id, uuid4(), instance_id, node_id, status,
                Jsonb(summary), now if terminal else None,
            ),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.agent_tasks
                (task_id, operation_id, node_id, instance_id, assignment_epoch, payload,
                 status, delivery_attempts, delivery_lease_until, delivered_at,
                 accepted_at, completed_at, result_summary)
            VALUES (%s, %s, %s, %s, 3, %s, %s, 1, %s, %s, %s, %s, %s)
            """,
            (
                task_id, operation_id, node_id, instance_id,
                Jsonb({"desired_state": "running"}), status,
                None if terminal else now + timedelta(minutes=2),
                now, now if status in {"accepted", "running"} or terminal else None,
                now if terminal else None, Jsonb(summary),
            ),
        )
    return connect, node_id, credential_id, instance_id, operation_id, task_id


def cleanup(connect, node_id, instance_id, operation_id, credential_id):
    with connect() as conn:
        conn.execute("DELETE FROM geelark_control.agent_reconciliation_reports WHERE node_id = %s", (node_id,))
        conn.execute("DELETE FROM geelark_control.agent_tasks WHERE operation_id = %s", (operation_id,))
        conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
        conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
        conn.execute("DELETE FROM geelark_control.node_credentials WHERE credential_id = %s", (credential_id,))
        conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))


def run_reconcile(connect, node_id, credential_id, inventory):
    principal = AgentPrincipal(str(node_id), str(credential_id), "active", "active", datetime.now(timezone.utc) + timedelta(hours=1))
    handler = make_postgres_agent_handlers(connect)[Operation.RECONCILE_INVENTORY]
    with connect() as conn:
        with conn.transaction():
            return handler(
                conn=conn,
                principal=principal,
                payload={"schema_version": 1, "inventory": inventory},
            )


def item(task_id, operation_id, instance_id, *, epoch=3, state="running", summary=None):
    return {
        "task_id": str(task_id),
        "operation_id": str(operation_id),
        "instance_id": str(instance_id),
        "assignment_epoch": epoch,
        "local_state": state,
        "result_summary": summary or {},
    }


def test_reconcile_matching_active_task_is_read_only_and_audited():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running")],
        )
        assert result["mutations_applied"] is False
        assert result["decisions"][0]["decision"] == "CONTINUE_SAME_EPOCH"
        with connect() as conn:
            task_status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
            reports = conn.execute(
                "SELECT inventory_count, decisions FROM geelark_control.agent_reconciliation_reports WHERE node_id = %s",
                (node,),
            ).fetchone()
        assert task_status == "running"
        assert reports[0] == 1
        assert reports[1][0]["decision"] == "CONTINUE_SAME_EPOCH"
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_stale_epoch_is_fenced_without_changing_task():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, epoch=2, state="running")],
        )
        assert result["decisions"][0]["decision"] == "STALE_ASSIGNMENT_EPOCH"
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "running"
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_expired_instance_lease_holds_without_mutation():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = %s WHERE instance_id = %s",
                (datetime.now(timezone.utc) - timedelta(minutes=1), instance),
            )
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running")],
        )
        assert result["decisions"][0]["decision"] == "INSTANCE_LEASE_EXPIRED_HOLD"
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "running"
        assert result["mutations_applied"] is False
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_expired_delivery_lease_holds_unaccepted_delivery_without_mutation():
    connect, node, credential, instance, operation, task = seed_task("delivered")
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET delivery_lease_until = %s WHERE task_id = %s",
                (datetime.now(timezone.utc) - timedelta(minutes=1), task),
            )
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running")],
        )
        assert result["decisions"][0]["decision"] == "DELIVERY_LEASE_EXPIRED_HOLD"
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "delivered"
        assert result["mutations_applied"] is False
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_running_task_ignores_expired_delivery_lease_after_acceptance():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET delivery_lease_until = %s WHERE task_id = %s",
                (datetime.now(timezone.utc) - timedelta(minutes=1), task),
            )
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running")],
        )
        assert result["decisions"][0]["decision"] == "CONTINUE_SAME_EPOCH"
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "running"
        assert result["mutations_applied"] is False
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_unknown_state_requires_manual_review_and_does_not_resolve_it():
    connect, node, credential, instance, operation, task = seed_task(
        "unknown", result_summary={"reason": "lost-contact"}
    )
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="unknown", summary={"reason": "lost-contact"})],
        )
        assert result["decisions"][0]["decision"] == "MANUAL_REVIEW_REQUIRED"
        with connect() as conn:
            task_status, operation_status = conn.execute(
                """
                SELECT t.status, o.status FROM geelark_control.agent_tasks t
                JOIN geelark_control.operations o ON o.operation_id = t.operation_id
                WHERE t.task_id = %s
                """,
                (task,),
            ).fetchone()
        assert task_status == "unknown"
        assert operation_status == "unknown"
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_confirmed_terminal_result_is_reported_as_already_confirmed():
    connect, node, credential, instance, operation, task = seed_task(
        "succeeded", result_summary={"exit_code": 0}
    )
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="succeeded", summary={"exit_code": 0})],
        )
        assert result["decisions"][0]["decision"] == "ALREADY_CONFIRMED"
        assert result["mutations_applied"] is False
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_reports_server_task_missing_from_local_inventory_without_reassignment():
    connect, node, credential, instance, operation, task = seed_task("accepted")
    try:
        result = run_reconcile(connect, node, credential, [])
        assert result["inventory_count"] == 0
        assert result["decisions"][0]["decision"] == "SERVER_TASK_MISSING_FROM_LOCAL_INVENTORY"
        assert result["decisions"][0]["automatic_mutation"] is False
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "accepted"
    finally:
        cleanup(connect, node, instance, operation, credential)



def test_reconcile_local_progress_ahead_requests_normal_idempotent_progress_endpoint():
    connect, node, credential, instance, operation, task = seed_task("accepted")
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running", summary={"step": 1})],
        )
        assert result["decisions"][0]["decision"] == "RESEND_PROGRESS"
        assert result["mutations_applied"] is False
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "accepted"
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_detects_task_operation_state_mismatch():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.operations SET status = 'accepted' WHERE operation_id = %s",
                (operation,),
            )
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="running")],
        )
        assert result["decisions"][0]["decision"] == "SERVER_TASK_OPERATION_STATE_MISMATCH"
        with connect() as conn:
            task_status, operation_status = conn.execute(
                """
                SELECT t.status, o.status FROM geelark_control.agent_tasks t
                JOIN geelark_control.operations o ON o.operation_id = t.operation_id
                WHERE t.task_id = %s
                """,
                (task,),
            ).fetchone()
        assert (task_status, operation_status) == ("running", "accepted")
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_terminal_result_conflict_requires_manual_review():
    connect, node, credential, instance, operation, task = seed_task(
        "succeeded", result_summary={"exit_code": 0}
    )
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="succeeded", summary={"exit_code": 1})],
        )
        assert result["decisions"][0]["decision"] == "TERMINAL_CONFLICT_MANUAL_REVIEW"
        with connect() as conn:
            summary = conn.execute(
                "SELECT result_summary FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task,),
            ).fetchone()[0]
        assert summary == {"exit_code": 0}
    finally:
        cleanup(connect, node, instance, operation, credential)



def test_reconcile_server_ahead_of_local_journal_does_not_roll_back():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="accepted")],
        )
        assert result["decisions"][0]["decision"] == "SERVER_AHEAD_HOLD"
        assert result["mutations_applied"] is False
    finally:
        cleanup(connect, node, instance, operation, credential)


def test_reconcile_local_terminal_result_requests_normal_result_endpoint():
    connect, node, credential, instance, operation, task = seed_task("accepted")
    try:
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, state="succeeded", summary={"exit_code": 0})],
        )
        assert result["decisions"][0]["decision"] == "RESEND_TERMINAL_RESULT"
        with connect() as conn:
            status = conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s", (task,)
            ).fetchone()[0]
        assert status == "accepted"
    finally:
        cleanup(connect, node, instance, operation, credential)



def test_reconcile_detects_operation_identity_epoch_mismatch():
    connect, node, credential, instance, operation, task = seed_task("running")
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.operations SET assignment_epoch = 2 WHERE operation_id = %s",
                (operation,),
            )
        result = run_reconcile(
            connect, node, credential,
            [item(task, operation, instance, epoch=3, state="running")],
        )
        assert result["decisions"][0]["decision"] == "SERVER_TASK_OPERATION_IDENTITY_MISMATCH"
    finally:
        cleanup(connect, node, instance, operation, credential)



def test_reconcile_does_not_disclose_tasks_owned_by_another_node():
    connect, node_a, credential_a, instance, operation, task = seed_task("running")
    node_b, credential_b = uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state) VALUES (%s, %s, 'active', 'healthy')",
                (node_b, "test-reconcile-other-" + str(node_b)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, %s, %s)
                """,
                (
                    credential_b, node_b, hashlib.sha256(str(uuid4()).encode()).hexdigest(),
                    now, now + timedelta(hours=1), now,
                ),
            )
        result = run_reconcile(
            connect, node_b, credential_b,
            [item(task, operation, instance, state="running")],
        )
        assert result["decisions"][0]["decision"] == "UNKNOWN_TASK"
    finally:
        with connect() as conn:
            conn.execute(
                "DELETE FROM geelark_control.agent_reconciliation_reports WHERE node_id = %s",
                (node_b,),
            )
            conn.execute(
                "DELETE FROM geelark_control.node_credentials WHERE credential_id = %s",
                (credential_b,),
            )
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_b,))
        cleanup(connect, node_a, instance, operation, credential_a)
