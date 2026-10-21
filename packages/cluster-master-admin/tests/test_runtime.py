from __future__ import annotations

from pathlib import Path

import pytest

from geelark_master_admin.runtime import _database_connector, main


def test_database_connector_requires_dedicated_reader_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://postgres@localhost:5432/geelark")
    with pytest.raises(RuntimeError, match="geelark_master_reader"):
        _database_connector()



def test_database_connector_rejects_password_in_dsn_without_echoing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "must-not-appear-in-errors"
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        f"postgresql://geelark_master_reader:{secret}@localhost:5432/geelark",
    )
    with pytest.raises(RuntimeError, match="PGPASSFILE") as exc:
        _database_connector()
    assert secret not in str(exc.value)


def test_database_connector_requires_tls_verification_for_remote_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader@db.example.test:5432/geelark")
    with pytest.raises(RuntimeError, match="sslmode"):
        _database_connector()


def test_database_connector_accepts_remote_verified_tls_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader@db.example.test:5432/geelark?sslmode=verify-full")
    connector = _database_connector()
    assert callable(connector)

def test_database_connector_rejects_verify_ca_for_remote_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader:secret@db.example.test:5432/geelark?sslmode=verify-ca")
    with pytest.raises(RuntimeError, match="verify-full"):
        _database_connector()


def test_database_connector_detects_remote_hostaddr_without_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql:///geelark?user=geelark_master_reader&hostaddr=203.0.113.10&sslmode=disable")
    with pytest.raises(RuntimeError, match="verify-full"):
        _database_connector()

def test_database_connector_requires_hostname_for_remote_hostaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql:///geelark?user=geelark_master_reader&hostaddr=203.0.113.10&sslmode=verify-full")
    with pytest.raises(RuntimeError, match="host="):
        _database_connector()


def test_database_connector_rejects_uninspectable_service_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "service=remote-db user=geelark_master_reader")
    with pytest.raises(RuntimeError, match="service"):
        _database_connector()


def test_remote_bind_is_rejected_without_explicit_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_BIND_HOST", "0.0.0.0")
    monkeypatch.delenv("GEELARK_ADMIN_ALLOW_REMOTE", raising=False)
    with pytest.raises(RuntimeError, match="bind remoto está bloqueado"):
        main()

def test_database_connector_allows_loopback_hostaddr_without_remote_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader@localhost:5432/geelark?hostaddr=127.0.0.1&sslmode=disable")
    connector = _database_connector()
    assert callable(connector)

def test_database_connector_accepts_remote_hostaddr_with_explicit_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEELARK_ADMIN_DATABASE_URL", "postgresql://geelark_master_reader@db.example.test:5432/geelark?hostaddr=203.0.113.10&sslmode=verify-full")
    connector = _database_connector()
    assert callable(connector)

def test_database_connector_rejects_loopback_hostname_for_remote_hostaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "postgresql:///geelark?user=geelark_master_reader&host=localhost&hostaddr=203.0.113.10&sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="host DNS/IP no-loopback"):
        _database_connector()


def test_database_connector_rejects_hostaddr_list_with_wrong_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db1.example.test,db2.example.test hostaddr=203.0.113.10 "
        "user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="misma cantidad"):
        _database_connector()


def test_database_connector_rejects_remote_address_paired_with_loopback_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost,db.example.test hostaddr=203.0.113.10,127.0.0.1 "
        "user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="host DNS/IP no-loopback"):
        _database_connector()


def test_database_connector_rejects_non_ip_hostaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db.example.test hostaddr=not-an-ip "
        "user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="direcciones IP válidas"):
        _database_connector()


def test_database_connector_accepts_matching_remote_hostaddr_pairs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db1.example.test,db2.example.test "
        "hostaddr=203.0.113.10,203.0.113.11 "
        "user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    assert callable(_database_connector())


def test_database_connector_sets_gssencmode_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    from geelark_master_admin import runtime as runtime_module

    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db.example.test user=geelark_master_reader dbname=geelark "
        "sslmode=verify-full gssencmode=prefer",
    )
    calls: list[dict[str, object]] = []
    sentinel = object()

    def fake_connect(dsn: str, **kwargs: object) -> object:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(runtime_module.psycopg, "connect", fake_connect)
    connector = _database_connector()
    assert connector() is sentinel
    assert calls[0]["gssencmode"] == "disable"
    assert calls[0]["connect_timeout"] == 3
    assert "default_transaction_read_only=on" in str(calls[0]["options"])
    assert "statement_timeout=1500" in str(calls[0]["options"])
    assert "lock_timeout=500" in str(calls[0]["options"])
