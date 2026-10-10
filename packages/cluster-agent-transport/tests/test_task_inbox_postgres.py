import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from cluster_agent_transport import (
    PostgresRateLimiter,
    create_agent_app,
    make_database_authenticator,
    make_database_idempotency_runner,
    make_database_nonce_consumer,
    make_postgres_agent_handlers,
)

DATABASE_URL = __import__("os").environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_active_node_claims_assignment_and_reports_fenced_result():
    node_id, credential_id, instance_id = uuid4(), uuid4(), uuid4()
    operation_id, task_id, request_id = uuid4(), uuid4(), uuid4()
    token = secrets.token_hex(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    connect = lambda: psycopg.connect(DATABASE_URL)
    now = datetime.now(timezone.utc)
    lease_expires_at = now + timedelta(minutes=5)
    payload = {
        "operation_id": str(operation_id),
        "request_id": str(request_id),
        "instance_id": str(instance_id),
        "node_id": str(node_id),
        "assignment_epoch": 1,
        "desired_state": "running",
        "lease_expires_at": lease_expires_at.isoformat(),
        "engine": {"name": "test-engine", "version": "0.1"},
        "android": {
            "api_level": 35,
            "abi": "x86_64",
            "image_digest": "sha256:" + "a" * 64,
        },
        "resource_reservation": {
            "cpu_units": 1,
            "memory_bytes": 1024,
            "storage_bytes": 4096,
        },
    }
    app = create_agent_app(
        authenticate=make_database_authenticator(connect),
        consume_nonce=make_database_nonce_consumer(connect),
        idempotency_runner=make_database_idempotency_runner(connect),
        rate_limiter=PostgresRateLimiter(connect, max_requests=60, window_seconds=60),
        handlers=make_postgres_agent_handlers(connect),
    )
    client = TestClient(app, base_url="https://testserver")

    def headers(key):
        return {
            "Authorization": "Bearer " + token,
            "X-Agent-Nonce": str(uuid4()),
            "X-Agent-Timestamp": datetime.now(timezone.utc).isoformat(),
            "X-Request-ID": str(uuid4()),
            "Idempotency-Key": key,
        }

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state) VALUES (%s, %s, 'active', 'healthy')",
                (node_id, "task-test-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at)
                VALUES (%s, %s, %s, 'active', %s)
                """,
                (credential_id, node_id, token_hash, lease_expires_at),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.instances
                    (instance_id, desired_state, observed_state, owner_node_id,
                     assignment_epoch, lease_expires_at, engine_name, engine_version,
                     image_digest, android_api_level, android_abi)
                VALUES (%s, 'running', 'reserved', %s, 1, %s, 'test-engine', '0.1',
                        %s, 35, 'x86_64')
                """,
                (instance_id, node_id, lease_expires_at, "sha256:" + "a" * 64),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.operations
                    (operation_id, request_id, instance_id, node_id, assignment_epoch,
                     operation_type, status)
                VALUES (%s, %s, %s, %s, 1, 'assign', 'accepted')
                """,
                (operation_id, request_id, instance_id, node_id),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_tasks
                    (task_id, operation_id, node_id, instance_id, assignment_epoch, payload)
                VALUES (%s, %s, %s, %s, 1, %s)
                """,
                (task_id, operation_id, node_id, instance_id, Jsonb(payload)),
            )

        claim_key = "task-claim-" + str(uuid4())
        claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers(claim_key),
            json={"schema_version": 1},
        )
        assert claim.status_code == 200
        assert claim.json()["task"]["task_id"] == str(task_id)
        assert claim.json()["task"]["assignment_epoch"] == 1

        # La misma clave devuelve el snapshot, no reclama otra tarea.
        repeated_claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers(claim_key),
            json={"schema_version": 1},
        )
        assert repeated_claim.status_code == 200
        assert repeated_claim.json() == claim.json()

        # Una clave nueva no puede reclamar la misma tarea mientras su lease de entrega vive.
        second_claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers("task-claim-" + str(uuid4())),
            json={"schema_version": 1},
        )
        assert second_claim.status_code == 200
        assert second_claim.json() == {"task": None}

        accepted = client.post(
            f"/agent/v1/tasks/{task_id}/accept",
            headers=headers("task-accept-" + str(uuid4())),
            json={"schema_version": 1, "state": "accepted", "details": {}},
        )
        assert accepted.status_code == 200
        progress = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"progress_percent": 25}},
        )
        assert progress.status_code == 200
        result = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-result-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": True}},
        )
        assert result.status_code == 200
        assert result.json()["state"] == "succeeded"

        with connect() as conn:
            task = conn.execute(
                "SELECT status, result_summary, completed_at FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            operation = conn.execute(
                "SELECT status, result_summary, completed_at FROM geelark_control.operations WHERE operation_id = %s",
                (operation_id,),
            ).fetchone()
            assert task[0] == "succeeded" and task[1] == {"verified": True} and task[2] is not None
            assert operation[0] == "succeeded" and operation[1] == {"verified": True} and operation[2] is not None
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.idempotency_records WHERE scope LIKE %s", (f"agent:{node_id}:%",))
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
