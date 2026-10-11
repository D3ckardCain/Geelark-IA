from __future__ import annotations

from pathlib import Path

import pytest

from geelark_master_admin.auth import (
    SESSION_TTL_SECONDS,
    SessionStore,
    hash_operator_password,
    verify_operator_password,
)


def test_password_hash_uses_random_salt_and_verifies() -> None:
    password = "Correct Horse Battery 2030!"
    first = hash_operator_password(password)
    second = hash_operator_password(password)
    assert first != second
    assert verify_operator_password(password, first)
    assert not verify_operator_password("wrong password", first)


def test_password_policy_and_malformed_hash_fail_closed() -> None:
    with pytest.raises(ValueError):
        hash_operator_password("short")
    with pytest.raises(ValueError):
        hash_operator_password("long-enough-password", iterations=1000)
    assert not verify_operator_password("password", "plaintext")
    assert not verify_operator_password("password", "pbkdf2_sha256$1$00$00")


def test_sessions_are_hashed_revocable_and_expire(tmp_path: Path) -> None:
    now = [1_000_000.0]
    store = SessionStore(tmp_path / "private" / "sessions.sqlite3", clock=lambda: now[0])
    token = store.create()
    assert token
    assert store.valid(token)
    with store._connect() as conn:
        row = conn.execute("SELECT token_hash FROM operator_sessions").fetchone()
    assert row[0] != token
    store.revoke(token)
    assert not store.valid(token)

    second = store.create()
    assert store.valid(second)
    now[0] += SESSION_TTL_SECONDS + 1
    assert not store.valid(second)


def test_session_database_permissions_are_restricted(tmp_path: Path) -> None:
    path = tmp_path / "private" / "sessions.sqlite3"
    SessionStore(path)
    assert path.exists()
    assert path.stat().st_mode & 0o077 == 0
