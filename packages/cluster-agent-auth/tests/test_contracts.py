from datetime import timedelta
from uuid import uuid4

import pytest

from cluster_agent_auth.service import (
    AuthenticationError,
    EnrollmentError,
    authenticate_bearer,
    begin_credential_rotation,
    consume_enrollment,
    revoke_credential,
    rotate_credential,
)


def test_authentication_rejects_malformed_secret_before_database_access():
    with pytest.raises(AuthenticationError):
        authenticate_bearer(None, "bad")


def test_enrollment_rejects_malformed_token_before_database_access():
    with pytest.raises(EnrollmentError):
        consume_enrollment(None, "bad", "node")


def test_enrollment_rejects_invalid_display_name_before_database_access():
    with pytest.raises(ValueError):
        consume_enrollment(None, "a" * 64, "  ")


def test_rotation_rejects_invalid_ttl_before_database_access():
    with pytest.raises(ValueError):
        begin_credential_rotation(None, uuid4(), timedelta(0))
    with pytest.raises(ValueError):
        begin_credential_rotation(None, uuid4(), timedelta(days=366))


def test_enrollment_rejects_credential_ttl_above_one_year_before_database_access():
    with pytest.raises(ValueError):
        consume_enrollment(None, "a" * 64, "node", credential_ttl=timedelta(days=366))


def test_rotation_and_revocation_require_database_for_valid_ids():
    # Con IDs válidos se necesita conexión real; aquí comprobamos que no se
    # intenta simular éxito cuando no hay conexión de persistencia.
    with pytest.raises((AttributeError, TypeError)):
        rotate_credential(None, uuid4(), uuid4())
    with pytest.raises((AttributeError, TypeError)):
        revoke_credential(None, uuid4(), uuid4())
