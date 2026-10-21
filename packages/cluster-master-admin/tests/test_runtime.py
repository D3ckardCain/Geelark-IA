from __future__ import annotations

import os
from pathlib import Path

import pytest

from geelark_master_admin.runtime import _database_connector, main


@pytest.fixture(autouse=True)
def isolated_libpq_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Keep developer/runner libpq settings from silently changing unit-test behavior.
    for name in ("PGSERVICE", "PGSERVICEFILE", "PGHOSTADDR", "PGPORT", "PGSSLROOTCERT", "PGPASSWORD", "PGOPTIONS"):
        monkeypatch.delenv(name, raising=False)
    passfile = tmp_path / "pgpass"
    passfile.write_text("localhost:5432:geelark:geelark_master_reader:test-only\n", encoding="utf-8")
    if os.name == "posix":
        passfile.chmod(0o600)
    monkeypatch.setenv("PGPASSFILE", str(passfile))
    ca_file = tmp_path / "test-root.crt"
    ca_file.write_text("test-only public CA placeholder\\n", encoding="utf-8")
    monkeypatch.setenv("TEST_PG_CA_CERT", str(ca_file))


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
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        f"postgresql://geelark_master_reader@db.example.test:5432/geelark?sslmode=verify-full&sslrootcert={os.environ['TEST_PG_CA_CERT']}",
    )
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
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        f"postgresql://geelark_master_reader@db.example.test:5432/geelark?hostaddr=203.0.113.10&sslmode=verify-full&sslrootcert={os.environ['TEST_PG_CA_CERT']}",
    )
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
        f"host=db1.example.test,db2.example.test "
        f"hostaddr=203.0.113.10,203.0.113.11 "
        f"user=geelark_master_reader dbname=geelark sslmode=verify-full sslrootcert={os.environ['TEST_PG_CA_CERT']}",
    )
    assert callable(_database_connector())


def test_database_connector_sets_gssencmode_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    from geelark_master_admin import runtime as runtime_module

    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        f"host=db.example.test user=geelark_master_reader dbname=geelark "
        f"sslmode=verify-full gssencmode=prefer sslrootcert={os.environ['TEST_PG_CA_CERT']} "
        "options='-c default_transaction_read_only=off -c statement_timeout=0 -c lock_timeout=0'",
    )
    calls: list[dict[str, object]] = []
    sentinel = object()

    def fake_connect(dsn: str, **kwargs: object) -> object:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setenv(
        "PGOPTIONS",
        "-c default_transaction_read_only=off -c statement_timeout=0 -c lock_timeout=0",
    )
    monkeypatch.setattr(runtime_module.psycopg, "connect", fake_connect)
    connector = _database_connector()
    assert connector() is sentinel
    assert calls[0]["gssencmode"] == "disable"
    assert calls[0]["sslrootcert"] == str(Path(os.environ["TEST_PG_CA_CERT"]).resolve())
    assert calls[0]["connect_timeout"] == 3
    assert calls[0]["options"] == (
        "-c default_transaction_read_only=on "
        "-c statement_timeout=1500 "
        "-c lock_timeout=500"
    )


def test_database_connector_requires_explicit_passfile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PGPASSFILE", raising=False)
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="PGPASSFILE"):
        _database_connector()


@pytest.mark.parametrize("environment_name", ["PGSERVICE", "PGSERVICEFILE"])
def test_database_connector_rejects_external_service_environment(
    monkeypatch: pytest.MonkeyPatch, environment_name: str
) -> None:
    monkeypatch.setenv(environment_name, "external-service")
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="perfiles libpq externos"):
        _database_connector()


def test_database_connector_rejects_servicefile_in_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "servicefile=/tmp/pg_service.conf host=localhost "
        "user=geelark_master_reader dbname=geelark",
    )
    # libpq rejects servicefile as an unknown DSN option before application checks.
    with pytest.raises(RuntimeError, match="DSN PostgreSQL válido"):
        _database_connector()


def test_database_connector_rejects_implicit_hostaddr_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGHOSTADDR", "203.0.113.10")
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="PGHOSTADDR"):
        _database_connector()


def test_database_connector_requires_explicit_host_even_if_pghost_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGHOST", "db.example.test")
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="host= o hostaddr= explícito"):
        _database_connector()


def test_database_connector_requires_explicit_database_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader",
    )
    with pytest.raises(RuntimeError, match="dbname explícito"):
        _database_connector()


def test_database_connector_rejects_implicit_port_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGPORT", "55432")
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="PGPORT"):
        _database_connector()


def test_database_connector_rejects_implicit_remote_ssl_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGSSLROOTCERT", "/tmp/unreviewed-root.crt")
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db.example.test user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="PGSSLROOTCERT"):
        _database_connector()


def test_database_connector_rejects_password_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "environment-password-must-not-be-used"
    monkeypatch.setenv("PGPASSWORD", secret)
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(RuntimeError, match="PGPASSWORD") as exc:
        _database_connector()
    assert secret not in str(exc.value)


@pytest.mark.skipif(os.name != "posix", reason="Los permisos POSIX no aplican en Windows.")
def test_database_connector_rejects_group_or_world_readable_passfile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    passfile = Path(os.environ["PGPASSFILE"])
    passfile.chmod(0o644)
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(PermissionError, match="permisos 0600"):
        _database_connector()


@pytest.mark.skipif(os.name != "posix", reason="Los permisos POSIX no aplican en Windows.")
def test_database_connector_rejects_passfile_in_group_writable_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    shared_dir.chmod(0o777)
    passfile = shared_dir / "pgpass"
    passfile.write_text(
        "localhost:5432:geelark:geelark_master_reader:test-only\\n",
        encoding="utf-8",
    )
    passfile.chmod(0o600)
    monkeypatch.setenv("PGPASSFILE", str(passfile))
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(PermissionError, match="directorio contenedor"):
        _database_connector()


def test_database_connector_rejects_passfile_override_in_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark passfile=/tmp/alternate-passfile",
    )
    with pytest.raises(RuntimeError) as exc:
        _database_connector()
    assert "passfile dentro de GEELARK_ADMIN_DATABASE_URL" in str(exc.value) or (
        "DSN PostgreSQL válido" in str(exc.value)
    )


@pytest.mark.skipif(os.name != "posix", reason="La prueba de enlaces POSIX no aplica en Windows.")
def test_database_connector_rejects_symlink_passfile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "real-pgpass"
    target.write_text(
        "localhost:5432:geelark:geelark_master_reader:test-only\\n",
        encoding="utf-8",
    )
    target.chmod(0o600)
    alias = tmp_path / "pgpass-link"
    alias.symlink_to(target)
    monkeypatch.setenv("PGPASSFILE", str(alias))
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    with pytest.raises(PermissionError, match="enlace simbólico"):
        _database_connector()


def test_database_connector_canonicalizes_valid_passfile_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = Path(os.environ["PGPASSFILE"])
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=localhost user=geelark_master_reader dbname=geelark",
    )
    assert callable(_database_connector())
    assert os.environ["PGPASSFILE"] == str(configured.resolve())


def test_database_connector_requires_explicit_remote_ca(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db.example.test user=geelark_master_reader dbname=geelark sslmode=verify-full",
    )
    with pytest.raises(RuntimeError, match="sslrootcert explícito"):
        _database_connector()


def test_database_connector_rejects_missing_remote_ca_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GEELARK_ADMIN_DATABASE_URL",
        "host=db.example.test user=geelark_master_reader dbname=geelark "
        "sslmode=verify-full sslrootcert=/tmp/geelark-nonexistent-ca.crt",
    )
    with pytest.raises(RuntimeError, match="archivo CA existente"):
        _database_connector()
