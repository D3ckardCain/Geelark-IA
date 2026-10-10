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
