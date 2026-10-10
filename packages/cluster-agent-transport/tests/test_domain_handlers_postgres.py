import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
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


def test_pending_node_cannot_claim_tasks_and_active_node_with_empty_inbox_gets_none():
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    pending_node, pending_credential = uuid4(), uuid4()
    active_node, active_credential = uuid4(), uuid4()
    try:
        with connect() as conn:
            for node_id, credential_id, state in (
                (pending_node, pending_credential, "pending"),
                (active_node, active_credential, "active"),
            ):
                conn.execute(
                    "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, %s)",
                    (node_id, "test-claim-" + str(node_id), state),
                )
                conn.execute(
                    """
                    INSERT INTO geelark_control.node_credentials
                        (credential_id, node_id, token_sha256, status, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        credential_id, node_id,
                        hashlib.sha256(secrets.token_hex(32).encode()).hexdigest(),
                        state, datetime.now(timezone.utc) + timedelta(hours=1),
                    ),
                )

        pending = AgentPrincipal(str(pending_node), str(pending_credential), "pending", "pending")
        with connect() as conn:
            with pytest.raises(HTTPException) as exc:
                handlers[Operation.TASK_FETCH](conn=conn, principal=pending, payload={"schema_version": 1})
            assert exc.value.status_code == 403

        active = AgentPrincipal(str(active_node), str(active_credential), "active", "active")
        with connect() as conn:
            assert handlers[Operation.TASK_FETCH](conn=conn, principal=active, payload={"schema_version": 1}) == {"task": None}
    finally:
        with connect() as conn:
            for node_id in (pending_node, active_node):
                conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
