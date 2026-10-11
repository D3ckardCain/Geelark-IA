from __future__ import annotations

from pathlib import Path

import pytest

from geelark_master_admin.runtime import _database_connector


def test_database_connector_requires_dedicated_reader_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://postgres:secret@localhost:5432/geelark")
    with pytest.raises(RuntimeError, match="geelark_master_reader"):
        _database_connector()


def test_database_connector_requires_tls_verification_for_remote_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader:secret@db.example.test:5432/geelark")
    with pytest.raises(RuntimeError, match="sslmode"):
        _database_connector()


def test_database_connector_accepts_remote_verified_tls_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader:secret@db.example.test:5432/geelark?sslmode=verify-full")
    connector = _database_connector()
    assert callable(connector)
