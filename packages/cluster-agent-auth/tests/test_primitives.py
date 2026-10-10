from datetime import timedelta
from uuid import uuid4

import pytest

from cluster_agent_auth.service import (
    _new_secret,
    _secret_hash,
    _valid_secret,
    create_enrollment,
)


def test_generated_secret_is_256_bits_and_hash_is_one_way_representation():
    secret = _new_secret()
    assert len(secret) == 64
    assert _valid_secret(secret)
    digest = _secret_hash(secret)
    assert len(digest) == 64
    assert digest != secret


@pytest.mark.parametrize("value", ["", "x" * 64, "A" * 64, "ab" * 31, "ab" * 32 + "00", None])
def test_rejects_malformed_secrets(value):
    assert not _valid_secret(value)


def test_hash_rejects_malformed_secrets():
    with pytest.raises(ValueError):
        _secret_hash("not-a-token")


def test_enrollment_ttl_bounds_are_explicit():
    # La conexión no se utiliza porque la validación de TTL ocurre antes del SQL.
    with pytest.raises(ValueError):
        create_enrollment(None, uuid4(), "admin", timedelta(0))
    with pytest.raises(ValueError):
        create_enrollment(None, uuid4(), "admin", timedelta(hours=2))


def test_created_by_must_be_nonempty_and_bounded():
    with pytest.raises(ValueError):
        create_enrollment(None, uuid4(), "   ")
    with pytest.raises(ValueError):
        create_enrollment(None, uuid4(), "x" * 129)
