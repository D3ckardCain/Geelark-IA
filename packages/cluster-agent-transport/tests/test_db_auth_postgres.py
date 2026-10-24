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
        assert pending.authorized_at.tzinfo is not None

        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (credential_id,),
            )
            conn.execute("UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s", (node_id,))

        active = authenticate(token)
        assert (active.admin_state, active.credential_status) == ("active", "active")
        assert active.authorized_at.tzinfo is not None

        with connect() as conn:
            conn.execute("UPDATE geelark_control.nodes SET revoked_at = now() WHERE node_id = %s", (node_id,))
        with pytest.raises(InvalidAgentCredential):
            authenticate(token)
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))

def test_database_authenticator_rejects_expired_revoked_and_mismatched_credentials():
    connect = lambda: psycopg.connect(DATABASE_URL)
    authenticate = make_database_authenticator(connect)
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(days=2)
    cases = (
        # name, admin state, credential status, expiry offset, revoked_at
        ("expired", "active", "expired", timedelta(hours=-1), None),
        ("revoked-credential", "active", "revoked", timedelta(hours=1), now),
        ("active-pending-credential", "active", "pending", timedelta(hours=1), None),
        ("pending-active-credential", "pending", "active", timedelta(hours=1), None),
        ("revoked-node", "active", "active", timedelta(hours=1), None),
    )
    records = []
    try:
        with connect() as conn:
            for name, admin_state, credential_status, expiry_offset, revoked_at in cases:
                node_id, credential_id = uuid4(), uuid4()
                token = secrets.token_hex(32)
                records.append((node_id, token))
                node_revoked_at = now if name == "revoked-node" else None
                conn.execute(
                    """
                    INSERT INTO geelark_control.nodes
                        (node_id, display_name, admin_state, revoked_at, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (node_id, "test-auth-" + name + "-" + str(node_id), admin_state, node_revoked_at, created_at),
                )
                credential_revoked_at = revoked_at if credential_status == "revoked" else None
                activated_at = None if credential_status == "pending" else created_at
                conn.execute(
                    """
                    INSERT INTO geelark_control.node_credentials
                        (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at, revoked_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        credential_id, node_id,
                        hashlib.sha256(token.encode("ascii")).hexdigest(),
                        credential_status, created_at, now + expiry_offset,
                        activated_at, credential_revoked_at,
                    ),
                )
        for _, token in records:
            with pytest.raises(InvalidAgentCredential):
                authenticate(token)
    finally:
        with connect() as conn:
            for node_id, _ in records:
                conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
