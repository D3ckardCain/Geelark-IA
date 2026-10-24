from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from geelark_cluster_persistence.status_snapshot import (
    PostgresStatusSnapshotProvider,
    build_status_snapshot,
    SUPPORTED_MODULE_IDS,
)

NOW = datetime(2026, 10, 10, 23, 0, tzinfo=timezone.utc)
NODE_ID = UUID("b8c1b201-77a3-49b7-a5f3-39b1d5f4a100")


def make_row(*, display_name="WORKER-01", admin_state="active", reported="healthy",
             last_seen=NOW - timedelta(seconds=10), modules=None, capabilities=None,
             revoked_at=None, agent_version="0.1.0"):
    return (
        NODE_ID,
        display_name,
        admin_state,
        reported,
        agent_version,
        last_seen,
        capabilities if capabilities is not None else {"version": 1, "items": ["heartbeat", "status", "untrusted-capability"]},
        modules if modules is not None else [{
            "module_id": "agent-supervisor",
            "state": "operational",
            "version": "0.1.0",
            "checked_at": (NOW - timedelta(seconds=10)).isoformat(),
            "source": "agent-report",
            "error_code": None,
        }],
        revoked_at,
    )


def test_snapshot_builder_requires_authoritative_now():
    with pytest.raises(TypeError):
        build_status_snapshot(make_row())


def test_fresh_snapshot_uses_master_clock_and_closed_capability_list():
    snapshot = build_status_snapshot(make_row(), now=NOW)

    assert snapshot["schema_version"] == "1.0"
    UUID(snapshot["snapshot_id"])
    assert snapshot["generated_at"] == "2026-10-10T23:00:00Z"
    assert snapshot["source"] == "master-live"
    assert snapshot["node"]["authorization_state"] == "active"
    assert snapshot["node"]["health_state"] == "healthy"
    assert snapshot["freshness"] == {
        "state": "fresh",
        "age_seconds": 10,
        "threshold_seconds": 90,
        "observed_at": "2026-10-10T22:59:50Z",
    }
    assert snapshot["node"]["capabilities"] == ["heartbeat-v1", "self-status-v1"]
    assert snapshot["node"]["modules"][0]["state"] == "operational"


def test_reported_health_is_not_read_from_derived_health_column():
    snapshot = build_status_snapshot(
        make_row(reported="unhealthy", last_seen=NOW - timedelta(seconds=10)),
        now=NOW,
    )
    assert snapshot["node"]["reported_health_state"] == "unhealthy"
    assert snapshot["node"]["health_state"] == "degraded"


def test_missing_or_stale_heartbeat_never_looks_healthy():
    missing = build_status_snapshot(make_row(last_seen=None), now=NOW)
    assert missing["freshness"]["state"] == "missing"
    assert missing["node"]["health_state"] == "offline"
    assert missing["node"]["modules"][0]["state"] == "unknown"
    assert missing["node"]["modules"][0]["error_code"] == "NODE_STALE"

    stale = build_status_snapshot(make_row(last_seen=NOW - timedelta(seconds=91)), now=NOW)
    assert stale["freshness"]["state"] == "stale"
    assert stale["node"]["health_state"] == "offline"


def test_unknown_report_and_future_timestamp_fail_conservatively():
    unknown = build_status_snapshot(make_row(reported="unknown"), now=NOW)
    assert unknown["node"]["health_state"] == "unknown"

    future = build_status_snapshot(make_row(last_seen=NOW + timedelta(minutes=1)), now=NOW)
    assert future["freshness"]["state"] == "unknown"
    assert future["freshness"]["age_seconds"] is None
    assert future["node"]["health_state"] == "unknown"


def test_revoked_and_unmapped_authorization_states_do_not_become_active():
    revoked = build_status_snapshot(make_row(revoked_at=NOW), now=NOW)
    assert revoked["node"]["authorization_state"] == "revoked"

    maintenance = build_status_snapshot(make_row(admin_state="maintenance"), now=NOW)
    assert maintenance["node"]["authorization_state"] == "unknown"


def test_invalid_display_name_and_module_report_are_sanitized():
    row = list(make_row(display_name="worker\nsecret", modules=[{
        "module_id": "agent-supervisor",
        "state": "operational",
        "version": "0.1.0",
        "checked_at": "not-a-timestamp",
        "source": "agent-report",
        "error_code": None,
    }]))
    snapshot = build_status_snapshot(tuple(row), now=NOW)
    assert snapshot["node"]["display_name"] == "WORKER-B8C1B201"
    assert snapshot["node"]["modules"][0]["state"] == "unknown"
    assert snapshot["node"]["modules"][0]["source"] == "master-check"
    assert snapshot["node"]["modules"][0]["error_code"] == "REPORT_MISSING"


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.sql = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.sql = sql
        self.params = params
        row = None if self.row is None else (*self.row, NOW)
        return FakeCursor(row)


def test_postgres_provider_executes_select_only_and_returns_none_for_missing_node():
    row = make_row()
    connection = FakeConnection(row)
    provider = PostgresStatusSnapshotProvider(lambda: connection)
    result = provider.get_node_snapshot(NODE_ID)

    assert result["node"]["node_id"] == str(NODE_ID)
    assert result["generated_at"] == "2026-10-10T23:00:00Z"
    assert connection.sql.lstrip().upper().startswith("SELECT")
    assert "now() as database_now" in connection.sql.lower()
    assert "reported_health_state" in connection.sql
    assert "health_state AS reported_health_state" not in connection.sql
    assert not any(word in connection.sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE "))
    assert connection.params == (NODE_ID,)

    missing_connection = FakeConnection(None)
    missing_provider = PostgresStatusSnapshotProvider(lambda: missing_connection)
    assert missing_provider.get_node_snapshot(NODE_ID) is None


def test_provider_rejects_non_uuid_node_identifiers():
    provider = PostgresStatusSnapshotProvider(lambda: FakeConnection(None))
    with pytest.raises(TypeError):
        provider.get_node_snapshot("not-a-uuid")


def test_module_without_trusted_source_cannot_be_operational():
    reports = [{
        "module_id": "agent-supervisor",
        "state": "operational",
        "version": "0.1.0",
        "checked_at": NOW.isoformat(),
        "source": "unknown",
        "error_code": None,
    }]
    snapshot = build_status_snapshot(make_row(modules=reports), now=NOW)
    assert snapshot["node"]["modules"][0]["state"] == "unknown"
    assert snapshot["node"]["modules"][0]["source"] == "master-check"
    assert snapshot["node"]["modules"][0]["error_code"] == "INVALID_MODULE_REPORT"


def test_snapshot_output_fields_stay_aligned_with_versioned_json_schema():
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "docs/contracts/master-worker-status-v1.schema.json").read_text())
    snapshot = build_status_snapshot(make_row(), now=NOW)
    node_schema = schema["properties"]["node"]
    freshness_schema = schema["properties"]["freshness"]
    module_schema = node_schema["properties"]["modules"]["items"]

    assert set(snapshot) == set(schema["required"])
    assert set(snapshot["node"]) == set(node_schema["required"])
    assert set(snapshot["freshness"]) == set(freshness_schema["required"])
    assert set(snapshot["node"]["modules"][0]) == set(module_schema["required"])
    assert snapshot["schema_version"] == schema["properties"]["schema_version"]["const"]
    assert snapshot["source"] in schema["properties"]["source"]["enum"]
    assert snapshot["node"]["health_state"] in node_schema["properties"]["health_state"]["enum"]
    assert snapshot["node"]["authorization_state"] in node_schema["properties"]["authorization_state"]["enum"]
    assert snapshot["freshness"]["state"] in freshness_schema["properties"]["state"]["enum"]


def test_future_module_timestamp_is_rejected_and_not_returned():
    reports = [{
        "module_id": "agent-supervisor",
        "state": "operational",
        "version": "0.1.0",
        "checked_at": (NOW + timedelta(minutes=1)).isoformat(),
        "source": "agent-report",
        "error_code": None,
    }]
    snapshot = build_status_snapshot(make_row(modules=reports), now=NOW)
    module = snapshot["node"]["modules"][0]

    assert module["state"] == "unknown"
    assert module["source"] == "master-check"
    assert module["error_code"] == "REPORT_TIME_SKEW"
    assert module["checked_at"] is None


def test_stale_module_report_cannot_remain_operational():
    reports = [{
        "module_id": "agent-supervisor",
        "state": "operational",
        "version": "0.1.0",
        "checked_at": (NOW - timedelta(minutes=6)).isoformat(),
        "source": "agent-report",
        "error_code": None,
    }]
    snapshot = build_status_snapshot(make_row(modules=reports), now=NOW)
    module = snapshot["node"]["modules"][0]

    assert module["state"] == "unknown"
    assert module["source"] == "master-check"
    assert module["error_code"] == "REPORT_STALE"


def test_generated_snapshot_validates_against_full_json_schema():
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "docs/contracts/master-worker-status-v1.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    valid_snapshot = build_status_snapshot(make_row(), now=NOW)
    errors = list(validator.iter_errors(valid_snapshot))
    assert not errors, "\\n".join(error.message for error in errors)

    stale_snapshot = build_status_snapshot(
        make_row(last_seen=NOW - timedelta(seconds=91)),
        now=NOW,
    )
    stale_snapshot["node"]["health_state"] = "healthy"
    assert list(validator.iter_errors(stale_snapshot)), (
        "The schema must reject healthy status when the heartbeat is stale"
    )

def test_postgres_read_role_can_select_but_cannot_mutate_when_database_is_available():
    """Comprueba privilegios reales en PostgreSQL; CI usa una BD desechable."""
    admin_dsn = os.getenv("TEST_DATABASE_URL")
    if not admin_dsn:
        pytest.skip("TEST_DATABASE_URL no está configurado; requiere PostgreSQL de pruebas")
    role_name = "snapshot_reader_" + uuid4().hex
    password = "reader-test-only-" + uuid4().hex
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(
            psycopg.sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                psycopg.sql.Identifier(role_name),
                psycopg.sql.Literal(password),
            )
        )
        try:
            admin.execute(
                psycopg.sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    psycopg.sql.Identifier(admin.info.dbname),
                    psycopg.sql.Identifier(role_name),
                )
            )
            admin.execute(
                psycopg.sql.SQL("GRANT USAGE ON SCHEMA geelark_control TO {}").format(
                    psycopg.sql.Identifier(role_name)
                )
            )
            admin.execute(
                psycopg.sql.SQL("GRANT SELECT ON TABLE geelark_control.nodes TO {}").format(
                    psycopg.sql.Identifier(role_name)
                )
            )
            reader_dsn = psycopg.conninfo.make_conninfo(
                admin_dsn, user=role_name, password=password
            )
            provider = PostgresStatusSnapshotProvider(lambda: psycopg.connect(reader_dsn))
            # Una lectura real con permisos limitados debe funcionar aunque el UUID no exista.
            assert provider.get_node_snapshot(UUID("00000000-0000-4000-8000-000000000001")) is None
            with psycopg.connect(reader_dsn) as reader:
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    reader.execute(
                        "UPDATE geelark_control.nodes SET display_name = display_name WHERE false"
                    )
        finally:
            admin.execute(
                psycopg.sql.SQL("DROP OWNED BY {}").format(psycopg.sql.Identifier(role_name))
            )
            admin.execute(
                psycopg.sql.SQL("DROP ROLE {}").format(psycopg.sql.Identifier(role_name))
            )


def test_unknown_module_id_is_not_trusted_even_if_report_is_fresh():
    reports = [{
        "module_id": "unregistered-module",
        "state": "operational",
        "version": "9.9.9",
        "checked_at": NOW.isoformat(),
        "source": "agent-report",
        "error_code": None,
    }]
    snapshot = build_status_snapshot(make_row(modules=reports), now=NOW)
    assert snapshot["node"]["modules"] == []


def test_snapshot_schema_uses_the_closed_module_registry():
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "docs/contracts/master-worker-status-v1.schema.json").read_text())
    module_id_schema = schema["properties"]["node"]["properties"]["modules"]["items"]["properties"]["module_id"]
    assert module_id_schema["enum"] == sorted(SUPPORTED_MODULE_IDS)
