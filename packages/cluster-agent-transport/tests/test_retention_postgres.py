import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_prune_agent_storage_preview_and_explicit_export_confirmation():
    connect = lambda: psycopg.connect(DATABASE_URL)
    node_id, credential_id = uuid4(), uuid4()
    old_nonce, fresh_nonce = uuid4(), uuid4()
    old_heartbeat_key = "heartbeat-" + str(uuid4())
    active_result_key = "task-result-" + str(uuid4())
    unknown_scope_key = "future-scope-" + str(uuid4())
    old_safe_report, old_review_report, old_conflict_report = uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    safe_decisions = Jsonb([{"decision": "ALREADY_CONFIRMED"}])
    review_decisions = Jsonb([{"decision": "UNKNOWN_TASK"}])
    conflict_decisions = Jsonb([{"decision": "TERMINAL_CONFLICT_MANUAL_REVIEW"}])
    token_hash = hashlib.sha256(credential_id.bytes).hexdigest()

    try:
        with connect() as conn:
            baseline = conn.execute(
                "SELECT * FROM geelark_control.prune_agent_storage(false, false)"
            ).fetchone()

            conn.execute(
                """
                INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state)
                VALUES (%s, %s, 'active', 'healthy')
                """,
                (node_id, "retention-test-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, %s, %s)
                """,
                (
                    credential_id, node_id, token_hash, now - timedelta(days=1),
                    now + timedelta(days=365), now - timedelta(days=1),
                ),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_request_nonces
                    (node_id, nonce, credential_id, request_id, seen_at, expires_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    node_id, old_nonce, credential_id, uuid4(),
                    now - timedelta(hours=2), now - timedelta(minutes=70),
                    node_id, fresh_nonce, credential_id, uuid4(),
                    now, now + timedelta(minutes=5),
                ),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.idempotency_records
                    (scope, idempotency_key, payload_sha256, response_snapshot, created_at, expires_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    f"agent:{node_id}:heartbeat", old_heartbeat_key,
                    hashlib.sha256(b"old-heartbeat").hexdigest(), Jsonb({"ok": True}),
                    now - timedelta(days=2), now - timedelta(days=1),
                    f"agent:{node_id}:task_result", active_result_key,
                    hashlib.sha256(b"active-result").hexdigest(), Jsonb({"ok": True}),
                    now, now + timedelta(days=90),
                    f"agent:{node_id}:future_operation", unknown_scope_key,
                    hashlib.sha256(b"unknown-scope").hexdigest(), Jsonb({"ok": True}),
                    now - timedelta(days=2), now - timedelta(days=1),
                ),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_reconciliation_reports
                    (report_id, node_id, inventory_sha256, inventory_count, decisions, created_at)
                VALUES
                    (%s, %s, %s, 0, %s, %s),
                    (%s, %s, %s, 0, %s, %s),
                    (%s, %s, %s, 0, %s, %s)
                """,
                (
                    old_safe_report, node_id, "a" * 64, safe_decisions, now - timedelta(days=100),
                    old_review_report, node_id, "c" * 64, review_decisions, now - timedelta(days=400),
                    old_conflict_report, node_id, "d" * 64, conflict_decisions, now - timedelta(days=500),
                ),
            )
            # 10,001 informes seguros recientes: se conserva el más nuevo por cada nodo hasta el límite 10.000.
            conn.execute(
                """
                INSERT INTO geelark_control.agent_reconciliation_reports
                    (report_id, node_id, inventory_sha256, inventory_count, decisions, created_at)
                SELECT gen_random_uuid(), %s, %s, 0, %s,
                       %s + series.n * interval '1 microsecond'
                  FROM generate_series(1, 10001) AS series(n)
                """,
                (node_id, "b" * 64, safe_decisions, now - timedelta(days=1)),
            )

        with connect() as conn:
            preview = conn.execute(
                "SELECT * FROM geelark_control.prune_agent_storage(false, false)"
            ).fetchone()
            assert preview[0] == baseline[0] + 1  # nonce vencido +1h de gracia
            assert preview[2] == baseline[2] + 1  # heartbeat vencido; scope futuro no se poda
            assert preview[4] == baseline[4] + 2  # informe de 100d + el seguro que supera 10.000
            assert preview[6] == baseline[6] + 2  # UNKNOWN_TASK y conflicto terminal >365d
            assert preview[1] == preview[3] == preview[5] == preview[7] == 0
            preview_audit = conn.execute(
                """
                SELECT confirmed_export, confirmed_review_evidence_export,
                       deleted_nonces, deleted_idempotency_records,
                       deleted_safe_reports, deleted_review_reports
                  FROM geelark_control.agent_storage_maintenance_runs
                 ORDER BY started_at DESC, run_id DESC LIMIT 1
                """
            ).fetchone()
            assert preview_audit == (False, False, 0, 0, 0, 0)

        # La confirmación genérica poda expirados y reportes seguros, pero conserva evidencia de revisión.
        with connect() as conn:
            confirmed = conn.execute(
                "SELECT * FROM geelark_control.prune_agent_storage(true, false)"
            ).fetchone()
            assert confirmed[1] == confirmed[0]
            assert confirmed[3] == confirmed[2]
            assert confirmed[5] == confirmed[4]
            assert confirmed[7] == 0
            confirmed_audit = conn.execute(
                """
                SELECT confirmed_export, confirmed_review_evidence_export,
                       deleted_nonces, deleted_idempotency_records,
                       deleted_safe_reports, deleted_review_reports
                  FROM geelark_control.agent_storage_maintenance_runs
                 ORDER BY started_at DESC, run_id DESC LIMIT 1
                """
            ).fetchone()
            assert confirmed_audit == (True, False, confirmed[1], confirmed[3], confirmed[5], 0)
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_request_nonces WHERE node_id = %s AND nonce = %s",
                (node_id, old_nonce),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_request_nonces WHERE node_id = %s AND nonce = %s",
                (node_id, fresh_nonce),
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
                (f"agent:{node_id}:heartbeat", old_heartbeat_key),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
                (f"agent:{node_id}:future_operation", unknown_scope_key),
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
                (f"agent:{node_id}:task_result", active_result_key),
            ).fetchone()[0] == 1  # snapshot no vencido, necesario para reintentos
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_reconciliation_reports WHERE report_id = %s",
                (old_review_report,),
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_reconciliation_reports WHERE report_id = %s",
                (old_conflict_report,),
            ).fetchone()[0] == 1

        # Solo la segunda confirmación permite eliminar evidencia de revisión exportada y >365 días.
        with connect() as conn:
            review_confirmed = conn.execute(
                "SELECT * FROM geelark_control.prune_agent_storage(true, true)"
            ).fetchone()
            assert review_confirmed[7] == review_confirmed[6]
            review_audit = conn.execute(
                """
                SELECT confirmed_export, confirmed_review_evidence_export,
                       deleted_review_reports
                  FROM geelark_control.agent_storage_maintenance_runs
                 ORDER BY started_at DESC, run_id DESC LIMIT 1
                """
            ).fetchone()
            assert review_audit == (True, True, review_confirmed[7])
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_reconciliation_reports WHERE report_id = %s",
                (old_review_report,),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT count(*) FROM geelark_control.agent_reconciliation_reports WHERE report_id = %s",
                (old_conflict_report,),
            ).fetchone()[0] == 0
    finally:
        with connect() as conn:
            conn.execute(
                "DELETE FROM geelark_control.agent_reconciliation_reports WHERE node_id = %s",
                (node_id,),
            )
            conn.execute(
                "DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s",
                (node_id,),
            )
            conn.execute(
                "DELETE FROM geelark_control.idempotency_records WHERE scope LIKE %s",
                (f"agent:{node_id}:%",),
            )
            conn.execute(
                "DELETE FROM geelark_control.node_credentials WHERE credential_id = %s",
                (credential_id,),
            )
            conn.execute(
                "DELETE FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            )
