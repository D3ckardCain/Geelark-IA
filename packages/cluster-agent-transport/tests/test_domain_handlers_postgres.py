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
    auth_now = datetime.now(timezone.utc)
    principal = AgentPrincipal(str(node_id), str(credential_id), "pending", "pending", auth_now + timedelta(hours=1), auth_now)
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
        assert hb["reported_health_state"] == "healthy"
        assert hb["health_state"] == "healthy"
        assert state["reported_health_state"] == "healthy"
        assert state["health_state"] == "healthy"
        with connect() as conn:
            persisted_health = conn.execute(
                "SELECT reported_health_state, health_state FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            ).fetchone()
        assert persisted_health == ("healthy", "healthy")
        assert state["capabilities"] == {"version": 1, "items": ["heartbeat", "status"]}

        # A stale report must not remain authoritative just because the Worker
        # last reported "healthy"; the Master derives health from server time.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET last_seen_at = now() - interval '5 minutes' WHERE node_id = %s",
                (node_id,),
            )
        stale_state = handlers[Operation.STATUS_READ](principal=principal)
        assert stale_state["reported_health_state"] == "healthy"
        assert stale_state["health_state"] == "offline"

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


def test_active_module_inventory_is_persisted_and_stale_reports_become_unknown():
    node_id, credential_id = uuid4(), uuid4()
    token_hash = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    auth_now = datetime.now(timezone.utc)
    principal = AgentPrincipal(str(node_id), str(credential_id), "active", "active", auth_now + timedelta(hours=1), auth_now)
    payload = {"schema_version": 1, "modules": [
        {"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0", "error_code": None},
        {"module_id": "android-engine", "state": "not-installed", "version": None, "error_code": None},
    ]}
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, last_seen_at) VALUES (%s, %s, 'active', now())",
                (node_id, "test-modules-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, %s)
                """,
                (credential_id, node_id, token_hash, datetime.now(timezone.utc) + timedelta(hours=1), datetime.now(timezone.utc)),
            )
        with connect() as conn:
            result = handlers[Operation.MODULES_REPORT](conn=conn, principal=principal, payload=payload)
        assert result["module_count"] == 2
        state = handlers[Operation.STATUS_READ](principal=principal)
        assert [item["module_id"] for item in state["modules"]] == ["agent-supervisor", "android-engine"]
        assert state["modules"][0]["state"] == "operational"
        assert state["modules"][0]["source"] == "agent-report"
        assert state["modules"][1]["state"] == "not-installed"

        with connect() as conn:
            conn.execute(
                """
                UPDATE geelark_control.nodes
                   SET module_reports = jsonb_set(
                       module_reports, '{0,checked_at}', to_jsonb((now() - interval '10 minutes')::text)
                   )
                 WHERE node_id = %s
                """,
                (node_id,),
            )
        stale = handlers[Operation.STATUS_READ](principal=principal)
        assert stale["modules"][0]["state"] == "unknown"
        assert stale["modules"][0]["source"] == "master-check"
        assert stale["modules"][0]["error_code"] == "REPORT_STALE"
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
