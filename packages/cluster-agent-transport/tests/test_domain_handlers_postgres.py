import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb
from fastapi import HTTPException

from cluster_agent_transport.domain_handlers import make_postgres_agent_handlers
from cluster_agent_transport.policy import AgentPrincipal, Operation


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_pending_telemetry_persists_and_status_is_scoped_to_own_node():
    node_id, credential_id = uuid4(), uuid4()
    token_hash = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    principal = AgentPrincipal(str(node_id), str(credential_id), "pending", "pending")
    heartbeat = {
        "agent_version": "0.1.0",
        "health_state": "healthy",
        "cpu_load_percent": 12,
        "memory_total_bytes": 1000,
        "memory_available_bytes": 500,
        "storage_available_bytes": 2000,
        "schema_version": 1,
    }
    capabilities = {"capabilities_version": 1, "capabilities": ["heartbeat", "status"]}

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                (node_id, "test-domain-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at)
                VALUES (%s, %s, %s, 'pending', %s)
                """,
                (credential_id, node_id, token_hash, datetime.now(timezone.utc) + timedelta(hours=1)),
            )

        with connect() as conn:
            hb = handlers[Operation.HEARTBEAT](conn=conn, principal=principal, payload=heartbeat)
            caps = handlers[Operation.CAPABILITIES](conn=conn, principal=principal, payload=capabilities)
        state = handlers[Operation.STATUS_READ](principal=principal)

        assert hb["admin_state"] == "pending"
        assert hb["sequence"] == 1
        assert caps["capability_count"] == 2
        assert state["node_id"] == str(node_id)
        assert state["admin_state"] == "pending"
        assert state["capabilities"] == {"version": 1, "items": ["heartbeat", "status"]}

        with connect() as conn:
            conn.execute("UPDATE geelark_control.nodes SET revoked_at = now() WHERE node_id = %s", (node_id,))
        with connect() as conn:
            with pytest.raises(HTTPException) as exc:
                handlers[Operation.HEARTBEAT](conn=conn, principal=principal, payload=heartbeat)
            assert exc.value.status_code == 401
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))


def test_active_node_claims_durable_task_with_separate_delivery_and_instance_leases():
    node_id, credential_id = uuid4(), uuid4()
    instance_id, operation_id, task_id, request_id = uuid4(), uuid4(), uuid4(), uuid4()
    token_hash = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
    now = datetime.now(timezone.utc)
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    principal = AgentPrincipal(str(node_id), str(credential_id), "active", "active")

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'active')",
                (node_id, "test-task-claim-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, %s, %s)
                """,
                (credential_id, node_id, token_hash, now, now + timedelta(hours=1), now),
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
                    (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type, status)
                VALUES (%s, %s, %s, %s, 3, 'assign', 'accepted')
                """,
                (operation_id, request_id, instance_id, node_id),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_tasks
                    (task_id, operation_id, node_id, instance_id, assignment_epoch, payload)
                VALUES (%s, %s, %s, %s, 3, %s)
                """,
                (task_id, operation_id, node_id, instance_id, Jsonb({"desired_state": "running"})),
            )

        with connect() as conn:
            response = handlers[Operation.TASK_FETCH](
                conn=conn, principal=principal, payload={"schema_version": 1}
            )
        task = response["task"]
        with connect() as conn:
            second_claim = handlers[Operation.TASK_FETCH](
                conn=conn, principal=principal, payload={"schema_version": 1}
            )
        assert second_claim == {"task": None}
        assert task["task_id"] == str(task_id)
        assert task["operation_id"] == str(operation_id)
        assert task["assignment_epoch"] == 3
        assert task["desired_state"] == "running"
        assert datetime.fromisoformat(task["lease_expires_at"]) > now
        assert datetime.fromisoformat(task["instance_lease_expires_at"]) > datetime.fromisoformat(task["lease_expires_at"])

        with connect() as conn:
            stored = conn.execute(
                "SELECT status, delivery_attempts, delivery_lease_until FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
        assert stored[0] == "delivered"
        assert stored[1] == 1
        assert stored[2] is not None
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE task_id = %s", (task_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
