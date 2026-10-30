import hashlib
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

import cluster_agent_transport.domain_handlers as domain_handlers

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


def test_active_node_claims_assignment_and_reports_fenced_result(monkeypatch):
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
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state, reported_health_state, last_seen_at) VALUES (%s, %s, 'active', 'healthy', 'healthy', now())",
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

        # Un nodo que dejó de enviar heartbeat no puede reclamar una tarea,
        # aunque su último health_state persistido siga siendo "healthy".
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET last_seen_at = now() - interval '2 minutes' WHERE node_id = %s",
                (node_id,),
            )

        stale_claim = client.post(
            "/agent/v1/tasks/claim",
            headers=headers("stale-heartbeat-claim-" + str(uuid4())),
            json={"schema_version": 1},
        )
        assert stale_claim.status_code == 200
        assert stale_claim.json() == {"task": None}
        with connect() as conn:
            untouched = conn.execute(
                "SELECT status, delivery_lease_until FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            assert untouched == ("queued", None)
            conn.execute(
                "UPDATE geelark_control.nodes SET last_seen_at = now() WHERE node_id = %s",
                (node_id,),
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

        # Regresión: una aceptación que espera por el lock de la instancia no
        # puede usar el timestamp anterior a la espera si la lease vence.
        with connect() as conn:
            lease_expiry = conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = clock_timestamp() + interval '2 seconds' WHERE instance_id = %s RETURNING lease_expires_at",
                (instance_id,),
            ).fetchone()[0]
        lock_conn = connect()
        pool = ThreadPoolExecutor(max_workers=1)
        blocked_request = None
        try:
            lock_conn.execute(
                "SELECT instance_id FROM geelark_control.instances WHERE instance_id = %s FOR UPDATE",
                (instance_id,),
            )
            blocked_request = pool.submit(
                lambda: client.post(
                    f"/agent/v1/tasks/{task_id}/accept",
                    headers=headers("task-accept-lock-expiry-" + str(uuid4())),
                    json={"schema_version": 1, "state": "accepted", "details": {}},
                )
            )
            deadline = time.monotonic() + 8
            waiting = False
            while time.monotonic() < deadline:
                with connect() as observer:
                    waiting = observer.execute(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM pg_stat_activity
                             WHERE wait_event_type = 'Lock'
                               AND state = 'active'
                               AND query LIKE '%FROM geelark_control.agent_tasks AS t%'
                        )
                        """
                    ).fetchone()[0]
                if waiting:
                    break
                time.sleep(0.05)
            assert waiting, "la petición no llegó a esperar por el lock PostgreSQL"
            while True:
                with connect() as observer:
                    still_valid = observer.execute(
                        "SELECT clock_timestamp() < %s", (lease_expiry,)
                    ).fetchone()[0]
                if not still_valid:
                    break
                time.sleep(0.05)
        finally:
            lock_conn.rollback()
            lock_conn.close()
        pool.shutdown(wait=True)
        assert blocked_request is not None
        blocked_response = blocked_request.result(timeout=8)
        assert blocked_response.status_code == 409
        assert blocked_response.json()["detail"]["code"] == "STALE_ASSIGNMENT"
        with connect() as conn:
            assert conn.execute(
                "SELECT status FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()[0] == "delivered"
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = clock_timestamp() + interval '5 minutes' WHERE instance_id = %s",
                (instance_id,),
            )

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

        # La validación de leases debe usar el reloj PostgreSQL, no el del proceso.
        # Con el reloj de aplicación adelantado una hora, una lease vigente sigue válida.
        real_datetime = domain_handlers.datetime

        class AppClockAhead(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return real_datetime.now(tz) + timedelta(hours=1)

        monkeypatch.setattr(domain_handlers, "datetime", AppClockAhead)
        # El reloj local adelantado no debe convertir el heartbeat reciente en offline.
        module_report = client.put(
            "/agent/v1/modules",
            headers=headers("module-report-clock-ahead-" + str(uuid4())),
            json={"schema_version": 1, "modules": [
                {"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0", "error_code": None}
            ]},
        )
        assert module_report.status_code == 200
        own_status = client.get(
            "/agent/v1/status",
            headers=headers("status-clock-ahead-" + str(uuid4())),
        )
        assert own_status.status_code == 200
        assert own_status.json()["health_state"] == "healthy"
        assert own_status.json()["modules"][0]["state"] == "operational"

        ahead_progress = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-clock-ahead-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"clock_test": "ahead"}},
        )
        assert ahead_progress.status_code == 200

        # Con el reloj de aplicación atrasado una hora, una lease vencida debe
        # seguir rechazándose porque la decisión se toma con now() de PostgreSQL.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() - interval '1 second' WHERE instance_id = %s",
                (instance_id,),
            )

        class AppClockBehind(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return real_datetime.now(tz) - timedelta(hours=1)

        monkeypatch.setattr(domain_handlers, "datetime", AppClockBehind)
        behind_progress = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-clock-behind-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"clock_test": "behind"}},
        )
        assert behind_progress.status_code == 409
        assert behind_progress.json()["detail"]["code"] == "STALE_ASSIGNMENT"
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() + interval '5 minutes' WHERE instance_id = %s",
                (instance_id,),
            )
        monkeypatch.setattr(domain_handlers, "datetime", real_datetime)

        # La lease de entrega solo protege la fase delivered. Una vez aceptada,
        # el progreso depende de la lease de instancia y del assignment_epoch.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.agent_tasks SET delivery_lease_until = now() - interval '1 second' WHERE task_id = %s",
                (task_id,),
            )
        accepted_after_delivery_lease = client.post(
            f"/agent/v1/tasks/{task_id}/progress",
            headers=headers("task-progress-after-delivery-lease-" + str(uuid4())),
            json={"schema_version": 1, "state": "running", "details": {"progress_percent": 10}},
        )
        assert accepted_after_delivery_lease.status_code == 200
        assert accepted_after_delivery_lease.json()["state"] == "running"

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
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() - interval '1 second' WHERE instance_id = %s",
                (instance_id,),
            )
        # Un reintento terminal idéntico se reconoce aun vencidas ambas leases,
        # siempre que no haya cambiado el propietario ni assignment_epoch.
        duplicate_result = client.post(
            f"/agent/v1/tasks/{task_id}/result",
            headers=headers("task-result-duplicate-" + str(uuid4())),
            json={"schema_version": 1, "state": "succeeded", "details": {"verified": True}},
        )
        assert duplicate_result.status_code == 200
        assert duplicate_result.json()["duplicate"] is True
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() + interval '5 minutes' WHERE instance_id = %s",
                (instance_id,),
            )
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

        # La reconciliación también debe usar el reloj de PostgreSQL.
        # Un reloj de aplicación adelantado no invalida una lease aún vigente.
        monkeypatch.setattr(domain_handlers, "datetime", AppClockAhead)
        ahead_reconcile = client.post(
            "/agent/v1/reconcile",
            headers=headers("task-reconcile-clock-ahead-" + str(uuid4())),
            json=reconcile_payload,
        )
        assert ahead_reconcile.status_code == 200
        assert ahead_reconcile.json()["items"][0]["status"] == "in_sync"

        # Un reloj de aplicación atrasado no debe ocultar una lease vencida.
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() - interval '1 second' WHERE instance_id = %s",
                (instance_id,),
            )
        monkeypatch.setattr(domain_handlers, "datetime", AppClockBehind)
        behind_reconcile = client.post(
            "/agent/v1/reconcile",
            headers=headers("task-reconcile-clock-behind-" + str(uuid4())),
            json=reconcile_payload,
        )
        assert behind_reconcile.status_code == 200
        assert behind_reconcile.json()["items"][0]["status"] == "stale_assignment"
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.instances SET lease_expires_at = now() + interval '5 minutes' WHERE instance_id = %s",
                (instance_id,),
            )
        monkeypatch.setattr(domain_handlers, "datetime", real_datetime)

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
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.idempotency_records WHERE scope LIKE %s", (f"agent:{node_id}:%",))
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
