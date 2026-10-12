import os
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_transport.idempotency import IdempotencyConflict, execute_idempotent


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_idempotency_replays_same_response_and_rejects_payload_mismatch():
    scope = "transport-test-" + str(uuid4())
    key = "key-" + str(uuid4())
    calls = []

    with psycopg.connect(DATABASE_URL) as conn:
        first = execute_idempotent(
            conn, scope=scope, key=key, payload={"value": 1},
            execute=lambda tx: calls.append("first") or {"ok": True, "result": 7},
        )
        repeated = execute_idempotent(
            conn, scope=scope, key=key, payload={"value": 1},
            execute=lambda tx: calls.append("unexpected") or {"ok": False},
        )
        assert first == repeated == {"ok": True, "result": 7}
        assert calls == ["first"]

        with pytest.raises(IdempotencyConflict):
            execute_idempotent(
                conn, scope=scope, key=key, payload={"value": 2},
                execute=lambda tx: calls.append("mismatch") or {"ok": False},
            )
        assert calls == ["first"]
        conn.execute(
            "DELETE FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
            (scope, key),
        )


def test_idempotency_expiry_is_set_for_known_scope_and_unknown_scope_stays_null():
    from datetime import timedelta
    from uuid import uuid4

    node_id = uuid4()
    heartbeat_scope = f"agent:{node_id}:heartbeat"
    unknown_scope = f"agent:{node_id}:future_operation"
    heartbeat_key = "heartbeat-" + str(uuid4())
    unknown_key = "unknown-" + str(uuid4())
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            execute_idempotent(
                conn, scope=heartbeat_scope, key=heartbeat_key, payload={"kind": "heartbeat"},
                execute=lambda tx: {"ok": True},
            )
            execute_idempotent(
                conn, scope=unknown_scope, key=unknown_key, payload={"kind": "future"},
                execute=lambda tx: {"ok": True},
            )
            heartbeat_created, heartbeat_expires = conn.execute(
                "SELECT created_at, expires_at FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
                (heartbeat_scope, heartbeat_key),
            ).fetchone()
            unknown_expires = conn.execute(
                "SELECT expires_at FROM geelark_control.idempotency_records WHERE scope = %s AND idempotency_key = %s",
                (unknown_scope, unknown_key),
            ).fetchone()[0]
            assert timedelta(hours=23, minutes=59) <= heartbeat_expires - heartbeat_created <= timedelta(days=1, seconds=1)
            assert unknown_expires is None
    finally:
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute(
                "DELETE FROM geelark_control.idempotency_records WHERE (scope, idempotency_key) IN ((%s, %s), (%s, %s))",
                (heartbeat_scope, heartbeat_key, unknown_scope, unknown_key),
            )
