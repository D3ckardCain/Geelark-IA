import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_transport.replay import ReplayRejected, consume_request_nonce


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_nonce_is_persistently_single_use():
    node_id, credential_id = uuid4(), uuid4()
    nonce, request_id = uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
            (node_id, "test-replay-" + str(node_id)),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.node_credentials
                (credential_id, node_id, token_sha256, status, expires_at)
            VALUES (%s, %s, %s, 'pending', %s)
            """,
            (credential_id, node_id, __import__("hashlib").sha256(str(credential_id).encode()).hexdigest(), now + timedelta(hours=1)),
        )
        consume_request_nonce(
            conn, node_id=node_id, credential_id=credential_id, nonce=nonce,
            request_id=request_id, timestamp=now,
        )
        with pytest.raises(ReplayRejected):
            consume_request_nonce(
                conn, node_id=node_id, credential_id=credential_id, nonce=nonce,
                request_id=uuid4(), timestamp=now,
            )
        conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
        conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
        conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))


def test_old_timestamp_is_rejected_without_database_write():
    with psycopg.connect(DATABASE_URL) as conn:
        with pytest.raises(ReplayRejected):
            consume_request_nonce(
                conn, node_id=uuid4(), credential_id=uuid4(), nonce=uuid4(),
                request_id=uuid4(), timestamp=datetime.now(timezone.utc) - timedelta(minutes=6),
            )
