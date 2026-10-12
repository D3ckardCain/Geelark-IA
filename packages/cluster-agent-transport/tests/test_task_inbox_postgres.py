import hashlib
import secrets
from concurrent.futures import ThreadPoolExecutor
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
    stale_instance_id, stale_operation_id, stale_task_id, stale_request_id = uuid4(), uuid4(), uuid4(), uuid4()
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
                    (credential_id, node_id, token_sha256, status, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, now())
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

        claim_keys = ["task-claim-" + str(uuid4()), "task-claim-" + str(uuid4())]

        def do_claim(key):
            with TestClient(app, base_url="https://testserver") as parallel_client:
                response = parallel_client.post(
                    "/agent/v1/tasks/claim",
                    headers=headers(key),
                    json={"schema_version": 1},
                )
                return key, response

        with ThreadPoolExecutor(max_workers=2) as pool:
            claim_results = list(pool.map(do_claim, claim_keys))
        winners = [(key, response) for key, response in claim_results if response.status_code == 200 and response.json()["task"] is not None]
        assert len(winners) == 1
        claim_key, claim = winners[0]
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

        # Una aceptación posterior a la lease de entrega debe fallar sin mutar la tarea.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET delivery_lease_until = now() - interval '1 second' WHERE task_id = %s",
                (task_id,),
            )
        expired_accept = client.post(
            f"/agent/v1/tasks/{task_id}/accept",
            headers=headers("task-accept-expired-" + str(uuid4())),
            json={"schema_version": 1, "state": "accepted", "details": {}},
        )
        assert expired_accept.status_code == 409
        assert expired_accept.json()["detail"]["code"] == "STALE_ASSIGNMENT"

        # Una nueva reclamación tras expirar la lease entrega el snapshot actualizado.
        reclaim_key = "task-claim-retry-" + str(uuid4())
        reclaimed = client.post(
            "/agent/v1/tasks/claim",
            headers=headers(reclaim_key),
            json={"schema_version": 1},
        )
        assert reclaimed.status_code == 200
        assert reclaimed.json()["task"]["task_id"] == str(task_id)
        assert reclaimed.json()["task"]["delivery_attempt"] == 2
        assert reclaimed.json()["task"]["lease_expires_at"]
        assert reclaimed.json()["task"]["instance_lease_expires_at"]

        accepted = client.post(
            f"/agent/v1/tasks/{task_id}/accept",
            headers=headers("task-accept-" + str(uuid4())),
            json={"schema_version": 1, "state": "accepted", "details": {}},
        )
        assert accepted.status_code == 200
        secret_progress = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-secret-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"access_token": "must-not-persist"}},
        )
        assert secret_progress.status_code == 422
        assert secret_progress.json()["detail"]["code"] == "SENSITIVE_RESULT_FIELD"
        camel_case_secret = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-camel-secret-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"apiKey": "must-not-persist"}},
        )
        assert camel_case_secret.status_code == 422
        assert camel_case_secret.json()["detail"]["code"] == "SENSITIVE_RESULT_FIELD"

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

        # Un resultado terminal idéntico sigue siendo idempotente aunque venza la lease de entrega.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET delivery_lease_until = now() - interval '1 second' WHERE task_id = %s",
                (task_id,),
            )
        duplicate_result = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-result-duplicate-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": True}},
        )
        assert duplicate_result.status_code == 200
        assert duplicate_result.json()["duplicate"] is True
        conflicting_result = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-result-conflict-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": False}},
        )
        assert conflicting_result.status_code == 409
        assert conflicting_result.json()["detail"]["code"] == "TASK_TERMINAL_CONFLICT"

        reconcile_payload = {
            "schema_version": 1,
            "assignments": [{
                "task_id": str(task_id),
                "operation_id": str(operation_id),
                "instance_id": str(instance_id),
                "assignment_epoch": 1,
                "observed_state": "succeeded",
                "result_summary": {"verified": True},
            }],
        }
        reconciled = client.post(
            "/agent/v1/reconcile",
            headers=headers("task-reconcile-" + str(uuid4())),
            json=reconcile_payload,
        )
        assert reconciled.status_code == 200, reconciled.text
        assert reconciled.json()["read_only"] is True
        assert reconciled.json()["mutations_applied"] == 0
        assert reconciled.json()["items"][0]["status"] == "in_sync"

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
            conn.execute(
                "UPDATE geelark_control.instances SET assignment_epoch = 2 WHERE instance_id = %s",
                (instance_id,),
            )

        stale_reconcile = client.post(
            "/agent/v1/reconcile",
            headers=headers("task-reconcile-stale-" + str(uuid4())),
            json=reconcile_payload,
        )
        assert stale_reconcile.status_code == 200
        assert stale_reconcile.json()["items"][0]["status"] == "stale_assignment"

        stale_result = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-stale-result-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": True}},
        )
        assert stale_result.status_code == 409
        assert stale_result.json()["detail"]["code"] == "STALE_ASSIGNMENT"

        # unknown se puede volver a confirmar como unknown, pero no auto-resolverse.
        unknown_summary = {"reason_code": "NETWORK_TIMEOUT"}
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET assignment_epoch = 1, lease_expires_at = now() + interval '5 minutes' WHERE instance_id = %s",
                (instance_id,),
            )
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET status = 'unknown', result_summary = %s, completed_at = NULL WHERE task_id = %s",
                (Jsonb(unknown_summary), task_id),
            )
            conn.execute(
                "UPDATE geelark_control.operations SET status = 'unknown', result_summary = %s, completed_at = NULL WHERE operation_id = %s",
                (Jsonb(unknown_summary), operation_id),
            )

        unknown_replay = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-unknown-replay-" + str(uuid4())),
            json={"schema_version": 1, "state": "unknown", "details": unknown_summary},
        )
        assert unknown_replay.status_code == 200
        assert unknown_replay.json()["duplicate"] is True

        attempted_auto_resolution = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-unknown-auto-resolution-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": True}},
        )
        assert attempted_auto_resolution.status_code == 409
        assert attempted_auto_resolution.json()["detail"]["code"] == "TASK_TERMINAL_CONFLICT"
        with connect() as conn:
            task = conn.execute(
                "SELECT status, result_summary, completed_at FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            operation = conn.execute(
                "SELECT status, result_summary, completed_at FROM geelark_control.operations WHERE operation_id = %s",
                (operation_id,),
            ).fetchone()
            assert task[0] == "unknown" and task[1] == unknown_summary and task[2] is None
            assert operation[0] == "unknown" and operation[1] == unknown_summary and operation[2] is None
        # Aunque el campo almacenado health_state siga siendo healthy, un heartbeat
        # de hace más de 90 s debe impedir que el Worker reclame otra tarea.
        stale_payload = {
            **payload,
            "operation_id": str(stale_operation_id),
            "request_id": str(stale_request_id),
            "instance_id": str(stale_instance_id),
            "lease_expires_at": lease_expires_at.isoformat(),
        }
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO geelark_control.instances
                    (instance_id, desired_state, observed_state, owner_node_id,
                     assignment_epoch, lease_expires_at, engine_name, engine_version,
                     image_digest, android_api_level, android_abi)
                VALUES (%s, 'running', 'reserved', %s, 1, %s, 'test-engine', '0.1',
                        %s, 35, 'x86_64')
                """,
                (stale_instance_id, node_id, lease_expires_at, "sha256:" + "b" * 64),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.operations
                    (operation_id, request_id, instance_id, node_id, assignment_epoch,
                     operation_type, status)
                VALUES (%s, %s, %s, %s, 1, 'assign', 'accepted')
                """,
                (stale_operation_id, stale_request_id, stale_instance_id, node_id),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_tasks
                    (task_id, operation_id, node_id, instance_id, assignment_epoch, payload)
                VALUES (%s, %s, %s, %s, 1, %s)
                """,
                (stale_task_id, stale_operation_id, node_id, stale_instance_id, Jsonb(stale_payload)),
            )
            conn.execute(
                """
                UPDATE geelark_control.nodes
                   SET last_seen_at = now() - interval '2 minutes',
                       health_state = 'healthy',
                       reported_health_state = 'healthy'
                 WHERE node_id = %s
                """,
                (node_id,),
            )
        stale_claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers("task-claim-stale-" + str(uuid4())),
            json={"schema_version": 1},
        )
        assert stale_claim.status_code == 200
        assert stale_claim.json() == {"task": None}
        with connect() as conn:
            stale_status = conn.execute(
                "SELECT status, delivery_lease_until FROM geelark_control.agent_tasks WHERE task_id = %s",
                (stale_task_id,),
            ).fetchone()
            assert stale_status == ("queued", None)

    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.idempotency_records WHERE scope LIKE %s", (f"agent:{node_id}:%",))
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (stale_operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (stale_instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
