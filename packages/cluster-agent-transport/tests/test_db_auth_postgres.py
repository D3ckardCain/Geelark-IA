import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_transport.db_auth import InvalidAgentCredential, make_database_authenticator


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_database_authenticator_allows_pending_limited_principal_then_active_and_rejects_revoked():
    node_id, credential_id = uuid4(), uuid4()
    token = secrets.token_hex(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    connect = lambda: psycopg.connect(DATABASE_URL)
    authenticate = make_database_authenticator(connect)

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                (node_id, "test-auth-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at)
                VALUES (%s, %s, %s, 'pending', %s)
                """,
                (credential_id, node_id, token_hash, datetime.now(timezone.utc) + timedelta(hours=1)),
            )

        pending = authenticate(token)
        assert pending.node_id == str(node_id)
        assert pending.credential_id == str(credential_id)
        assert (pending.admin_state, pending.credential_status) == ("pending", "pending")

        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (credential_id,),
            )
            conn.execute("UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s", (node_id,))

        active = authenticate(token)
        assert (active.admin_state, active.credential_status) == ("active", "active")

        with connect() as conn:
            conn.execute("UPDATE geelark_control.nodes SET revoked_at = now() WHERE node_id = %s", (node_id,))
        with pytest.raises(InvalidAgentCredential):
            authenticate(token)
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
