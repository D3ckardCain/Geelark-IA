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
