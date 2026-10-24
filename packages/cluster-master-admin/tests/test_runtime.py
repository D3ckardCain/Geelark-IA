from __future__ import annotations

import io
from pathlib import Path

import pytest

import geelark_master_admin.runtime as runtime
from geelark_master_admin.runtime import _database_connector, _request_shutdown, main

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

def test_private_shutdown_command_requests_server_exit() -> None:
    class Server:
        should_exit = False

    server = Server()
    assert _request_shutdown(server, "STOP\n")
    assert server.should_exit is True

def test_private_shutdown_command_ignores_other_input() -> None:
    class Server:
        should_exit = False

    server = Server()
    assert not _request_shutdown(server, "anything else\n")
    assert server.should_exit is False

def test_stdin_eof_requests_server_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class Server:
        should_exit = False

    server = Server()
    monkeypatch.setattr(runtime.sys, "stdin", io.StringIO(""))

    runtime._watch_stdin_for_shutdown(server)

    assert server.should_exit is True

def test_stdin_error_requests_server_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class Server:
        should_exit = False

    class BrokenStdin:
        def __iter__(self):
            raise OSError("control pipe failed")

    server = Server()
    monkeypatch.setattr(runtime.sys, "stdin", BrokenStdin())

    runtime._watch_stdin_for_shutdown(server)

    assert server.should_exit is True
