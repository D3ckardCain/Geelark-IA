"""Pruebas reales contra PostgreSQL; CI proporciona TEST_DATABASE_URL."""
from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_auth.service import (
    AuthenticationError,
    EnrollmentError,
    authenticate_bearer,
    begin_credential_rotation,
    consume_enrollment,
    create_enrollment,
    revoke_credential,
    rotate_credential,
)

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere TEST_DATABASE_URL y migraciones aplicadas")


def connect():
    return psycopg.connect(DATABASE_URL)


def cleanup(node_ids, enrollment_ids):
    with connect() as conn:
        with conn.transaction():
            for node_id in node_ids:
                conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
                # Quitar primero credenciales de rotación que referencian a la anterior.
                conn.execute(
                    "DELETE FROM geelark_control.node_credentials WHERE node_id = %s AND replaces_credential_id IS NOT NULL",
                    (node_id,),
                )
                conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
                conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
            for enrollment_id in enrollment_ids:
                conn.execute("DELETE FROM geelark_control.node_enrollments WHERE enrollment_id = %s", (enrollment_id,))


def test_enrollment_is_one_time_and_node_starts_pending():
    node_id = uuid4()
    with connect() as conn:
        issued = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            credential = consume_enrollment(conn, issued.secret, "auth-integration-node")
        assert len(credential.secret) == 64
        with connect() as conn:
            with pytest.raises(EnrollmentError):
                consume_enrollment(conn, issued.secret, "auth-integration-node")
        with connect() as conn:
            row = conn.execute(
                """SELECT n.admin_state, c.status, e.consumed_at, c.token_sha256
                     FROM geelark_control.nodes n
                     JOIN geelark_control.node_credentials c ON c.node_id = n.node_id
                     JOIN geelark_control.node_enrollments e ON e.expected_node_id = n.node_id
                    WHERE n.node_id = %s""",
                (node_id,),
            ).fetchone()
            assert row[0] == "pending"
            assert row[1] == "pending"
            assert row[2] is not None
            assert row[3] != credential.secret
    finally:
        cleanup([node_id], [issued.record_id])


def test_authentication_requires_approved_node_and_active_credential():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            credential = consume_enrollment(conn, enrollment.secret, "auth-approved-node")
        with connect() as conn:
            with pytest.raises(AuthenticationError):
                authenticate_bearer(conn, credential.secret)
        with connect() as conn:
            conn.execute(
                """UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s""",
                (node_id,),
            )
            conn.execute(
                """UPDATE geelark_control.node_credentials
                      SET status = 'active', activated_at = now()
                    WHERE credential_id = %s""",
                (credential.record_id,),
            )
        with connect() as conn:
            principal = authenticate_bearer(conn, credential.secret)
        assert principal.node_id == node_id
        with connect() as conn:
            revoke_credential(conn, node_id, credential.record_id)
        with connect() as conn:
            with pytest.raises(AuthenticationError):
                authenticate_bearer(conn, credential.secret)
    finally:
        cleanup([node_id], [enrollment.record_id])


def test_rotation_revokes_old_and_activates_new_atomically():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            original = consume_enrollment(conn, enrollment.secret, "auth-rotation-node")
        with connect() as conn:
            conn.execute("UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s", (node_id,))
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (original.record_id,),
            )
        with connect() as conn:
            replacement = begin_credential_rotation(conn, node_id)
        with connect() as conn:
            rotate_credential(conn, node_id, replacement.record_id)
        with connect() as conn:
            with pytest.raises(AuthenticationError):
                authenticate_bearer(conn, original.secret)
        with connect() as conn:
            principal = authenticate_bearer(conn, replacement.secret)
        assert principal.node_id == node_id
    finally:
        cleanup([node_id], [enrollment.record_id])



def test_expired_enrollment_is_rejected():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
        conn.execute(
            """
            UPDATE geelark_control.node_enrollments
               SET created_at = now() - interval '2 minutes',
                   expires_at = now() - interval '1 minute'
             WHERE enrollment_id = %s
            """,
            (enrollment.record_id,),
        )
    try:
        with connect() as conn:
            with pytest.raises(EnrollmentError):
                consume_enrollment(conn, enrollment.secret, "expired-enrollment-node")
    finally:
        cleanup([node_id], [enrollment.record_id])


def test_expired_credential_is_rejected():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            credential = consume_enrollment(conn, enrollment.secret, "expired-credential-node")
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s",
                (node_id,),
            )
            conn.execute(
                """
                UPDATE geelark_control.node_credentials
                   SET status = 'active',
                       created_at = now() - interval '2 seconds',
                       activated_at = now() - interval '2 seconds',
                       expires_at = now() - interval '1 second'
                 WHERE credential_id = %s
                """,
                (credential.record_id,),
            )
        with connect() as conn:
            with pytest.raises(AuthenticationError):
                authenticate_bearer(conn, credential.secret)
    finally:
        cleanup([node_id], [enrollment.record_id])


def test_concurrent_rotation_allows_only_one_pending_credential():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            original = consume_enrollment(conn, enrollment.secret, "auth-concurrent-rotation-node")
        with connect() as conn:
            conn.execute("UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s", (node_id,))
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (original.record_id,),
            )

        def rotate():
            try:
                with connect() as conn:
                    return begin_credential_rotation(conn, node_id).record_id
            except AuthenticationError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: rotate(), range(2)))
        assert sum(result is not None for result in results) == 1
        with connect() as conn:
            pending = conn.execute(
                "SELECT count(*) FROM geelark_control.node_credentials WHERE node_id = %s AND status = 'pending'",
                (node_id,),
            ).fetchone()[0]
        assert pending == 1
    finally:
        cleanup([node_id], [enrollment.record_id])



def test_revoked_node_rejects_concurrent_authentication_attempts():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            credential = consume_enrollment(conn, enrollment.secret, "revoked-node-under-load")
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s",
                (node_id,),
            )
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (credential.record_id,),
            )
            conn.execute(
                "UPDATE geelark_control.nodes SET admin_state = 'revoked', revoked_at = now() WHERE node_id = %s",
                (node_id,),
            )

        def authenticate():
            try:
                with connect() as conn:
                    authenticate_bearer(conn, credential.secret)
                return False
            except AuthenticationError:
                return True

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: authenticate(), range(16)))
        assert all(results)
    finally:
        cleanup([node_id], [enrollment.record_id])


def test_concurrent_enrollment_consumption_only_succeeds_once():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")

    def consume():
        try:
            with connect() as conn:
                return consume_enrollment(conn, enrollment.secret, "auth-race-node").secret
        except EnrollmentError:
            return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: consume(), range(2)))
        assert sum(result is not None for result in results) == 1
    finally:
        cleanup([node_id], [enrollment.record_id])


def test_rotation_is_blocked_after_node_is_revoked():
    node_id = uuid4()
    with connect() as conn:
        enrollment = create_enrollment(conn, node_id, "test-admin")
    try:
        with connect() as conn:
            original = consume_enrollment(conn, enrollment.secret, "auth-rotation-revoked-node")
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET admin_state = 'active' WHERE node_id = %s",
                (node_id,),
            )
            conn.execute(
                "UPDATE geelark_control.node_credentials SET status = 'active', activated_at = now() WHERE credential_id = %s",
                (original.record_id,),
            )
        with connect() as conn:
            pending = begin_credential_rotation(conn, node_id)
        with connect() as conn:
            conn.execute(
                "UPDATE geelark_control.nodes SET admin_state = 'revoked', revoked_at = now() WHERE node_id = %s",
                (node_id,),
            )
        with connect() as conn:
            with pytest.raises(AuthenticationError, match="nodo no está activo"):
                rotate_credential(conn, node_id, pending.record_id)
        with connect() as conn:
            with pytest.raises(AuthenticationError, match="nodo no está activo"):
                begin_credential_rotation(conn, node_id)
        with connect() as conn:
            states = conn.execute(
                "SELECT credential_id, status FROM geelark_control.node_credentials WHERE node_id = %s ORDER BY credential_id",
                (node_id,),
            ).fetchall()
        assert {str(row[1]) for row in states} == {"active", "pending"}
    finally:
        cleanup([node_id], [enrollment.record_id])
