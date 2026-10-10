import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from cluster_agent_transport import (
    create_agent_app,
    make_database_authenticator,
    make_database_idempotency_runner,
    make_database_nonce_consumer,
    make_postgres_agent_handlers,
    PostgresRateLimiter,
)


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_pending_node_end_to_end_telemetry_idempotency_and_task_denial():
    node_id, credential_id = uuid4(), uuid4()
    token = secrets.token_hex(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    connect = lambda: psycopg.connect(DATABASE_URL)
    handlers = make_postgres_agent_handlers(connect)
    app = create_agent_app(
        authenticate=make_database_authenticator(connect),
        consume_nonce=make_database_nonce_consumer(connect),
        idempotency_runner=make_database_idempotency_runner(connect),
        rate_limiter=PostgresRateLimiter(connect, max_requests=60, window_seconds=60),
        handlers=handlers,
    )
    client = TestClient(app, base_url="https://testserver")
    heartbeat = {
        "schema_version": 1,
        "agent_version": "0.1.0",
        "health_state": "healthy",
        "cpu_load_percent": 12,
        "memory_total_bytes": 1000,
        "memory_available_bytes": 500,
        "storage_available_bytes": 2000,
    }

    def headers(key=None):
        result = {
            "Authorization": "Bearer " + token,
            "X-Agent-Nonce": str(uuid4()),
            "X-Agent-Timestamp": datetime.now(timezone.utc).isoformat(),
            "X-Request-ID": str(uuid4()),
        }
        if key is not None:
            result["Idempotency-Key"] = key
        return result

    heartbeat_key = "heartbeat-" + str(uuid4())
    capabilities_key = "capabilities-" + str(uuid4())

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                (node_id, "test-e2e-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at)
                VALUES (%s, %s, %s, 'pending', %s)
                """,
                (credential_id, node_id, token_hash, datetime.now(timezone.utc) + timedelta(hours=1)),
            )

        first = client.post("/agent/v1/heartbeat", headers=headers(heartbeat_key), json=heartbeat)
        assert first.status_code == 200
        assert first.json()["sequence"] == 1

        # Mismo key y payload devuelve el snapshot previo sin repetir la mutación.
        repeated = client.post("/agent/v1/heartbeat", headers=headers(heartbeat_key), json=heartbeat)
        assert repeated.status_code == 200
        assert repeated.json() == first.json()

        # Reutilizar la clave con otro payload se rechaza y no cambia la fila.
        mismatched_payload = {**heartbeat, "health_state": "degraded"}
        mismatch = client.post(
            "/agent/v1/heartbeat", headers=headers(heartbeat_key), json=mismatched_payload
        )
        assert mismatch.status_code == 409
        assert mismatch.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"

        capabilities = {"capabilities_version": 1, "capabilities": ["heartbeat", "status"]}
        caps = client.put(
            "/agent/v1/capabilities", headers=headers(capabilities_key), json=capabilities
        )
        assert caps.status_code == 200
        assert caps.json()["capability_count"] == 2

        status = client.get("/agent/v1/status", headers=headers())
        assert status.status_code == 200
        assert status.json()["node_id"] == str(node_id)
        assert status.json()["admin_state"] == "pending"
        assert status.json()["health_state"] == "healthy"
        assert status.json()["sequence"] == 1
        assert status.json()["capabilities"] == {"version": 1, "items": ["heartbeat", "status"]}

        denied_claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers("task-claim-" + str(uuid4())),
            json={"schema_version": 1},
        )
        assert denied_claim.status_code == 403

        denied = client.post(
            f"/agent/v1/tasks/{uuid4()}/accept",
            headers=headers("task-key-" + str(uuid4())),
            json={"schema_version": 1, "state": "accepted", "details": {}},
        )
        assert denied.status_code == 403
    finally:
        with connect() as conn:
            conn.execute(
                "DELETE FROM geelark_control.idempotency_records WHERE scope IN (%s, %s)",
                (f"agent:{node_id}:heartbeat", f"agent:{node_id}:capabilities"),
            )
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
