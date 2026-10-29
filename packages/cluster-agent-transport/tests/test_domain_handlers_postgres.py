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
    principal = AgentPrincipal(str(node_id), str(credential_id), "pending", "pending", datetime.now(timezone.utc) + timedelta(hours=1))
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


def test_credential_for_node_a_cannot_read_or_mutate_node_b():
    """El node_id del principal nunca sustituye la asociación real de la credencial."""
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    node_a, node_b = uuid4(), uuid4()
    credential_a, credential_b = uuid4(), uuid4()
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    heartbeat = {
        "agent_version": "0.1.0",
        "health_state": "healthy",
        "cpu_load_percent": 10,
        "memory_total_bytes": 100,
        "memory_available_bytes": 50,
        "storage_available_bytes": 200,
        "schema_version": 1,
    }
    try:
        with connect() as conn:
            for node_id, credential_id in ((node_a, credential_a), (node_b, credential_b)):
                conn.execute(
                    "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                    (node_id, "isolation-" + str(node_id)),
                )
                conn.execute(
                    """
                    INSERT INTO geelark_control.node_credentials
                        (credential_id, node_id, token_sha256, status, expires_at)
                    VALUES (%s, %s, %s, 'pending', %s)
                    """,
                    (credential_id, node_id, hashlib.sha256(str(uuid4()).encode()).hexdigest(), expiry),
                )

        real_a = AgentPrincipal(str(node_a), str(credential_a), "pending", "pending", expiry)
        forged_b = AgentPrincipal(str(node_b), str(credential_a), "pending", "pending", expiry)
        assert handlers[Operation.STATUS_READ](principal=real_a)["node_id"] == str(node_a)
        with pytest.raises(HTTPException) as denied_read:
            handlers[Operation.STATUS_READ](principal=forged_b)
        assert denied_read.value.status_code == 401

        with connect() as conn:
            with pytest.raises(HTTPException) as denied_write:
                handlers[Operation.HEARTBEAT](conn=conn, principal=forged_b, payload=heartbeat)
        assert denied_write.value.status_code == 401
        with connect() as conn:
            row = conn.execute(
                "SELECT last_sequence, last_seen_at FROM geelark_control.nodes WHERE node_id = %s",
                (node_b,),
            ).fetchone()
        assert row == (0, None)
    finally:
        with connect() as conn:
            for node_id in (node_a, node_b):
                conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))


def test_expiry_while_waiting_for_node_lock_rejects_heartbeat():
    """La hora de inicio de la transacción NO debe permitir una escritura tras vencer."""
    import time
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    node_id, credential_id = uuid4(), uuid4()
    heartbeat = {
        "agent_version": "0.1.0",
        "health_state": "healthy",
        "cpu_load_percent": 10,
        "memory_total_bytes": 100,
        "memory_available_bytes": 50,
        "storage_available_bytes": 200,
        "schema_version": 1,
    }
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                (node_id, "lock-expiry-" + str(node_id)),
            )
            expiry = conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at)
                VALUES (%s, %s, %s, 'pending', clock_timestamp() + interval '2 seconds')
                RETURNING expires_at
                """,
                (credential_id, node_id, hashlib.sha256(str(uuid4()).encode()).hexdigest()),
            ).fetchone()[0]
        principal = AgentPrincipal(str(node_id), str(credential_id), "pending", "pending", expiry)
        started = Event()

        def write_during_lock():
            started.set()
            with connect() as worker_conn:
                return handlers[Operation.HEARTBEAT](
                    conn=worker_conn, principal=principal, payload=heartbeat,
                )

        with ThreadPoolExecutor(max_workers=1) as pool:
            with connect() as locked_conn:
                locked_conn.execute(
                    "SELECT node_id FROM geelark_control.nodes WHERE node_id = %s FOR UPDATE",
                    (node_id,),
                )
                future = pool.submit(write_during_lock)
                assert started.wait(timeout=5)
                # Aún retenemos la fila. El worker debe esperar mientras expira su credencial.
                while datetime.now(timezone.utc) <= expiry + timedelta(milliseconds=200):
                    time.sleep(0.02)
                assert not future.done()
            # Liberado el bloqueo, el worker debe reevaluar usando clock_timestamp().
            with pytest.raises(HTTPException) as rejected:
                future.result(timeout=10)
            assert rejected.value.status_code == 401

        with connect() as conn:
            assert conn.execute(
                "SELECT last_sequence FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            ).fetchone()[0] == 0
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
