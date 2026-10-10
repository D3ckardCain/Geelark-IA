from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from geelark_cluster_persistence.status_snapshot import (
    PostgresStatusSnapshotProvider,
    build_status_snapshot,
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
        return FakeCursor(self.row)


def test_postgres_provider_executes_select_only_and_returns_none_for_missing_node():
    row = make_row()
    connection = FakeConnection(row)
    provider = PostgresStatusSnapshotProvider(lambda: connection)
    result = provider.get_node_snapshot(NODE_ID)

    assert result["node"]["node_id"] == str(NODE_ID)
    assert connection.sql.lstrip().upper().startswith("SELECT")
    assert not any(word in connection.sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE "))
    assert connection.params == (NODE_ID,)

    missing_connection = FakeConnection(None)
    missing_provider = PostgresStatusSnapshotProvider(lambda: missing_connection)
    assert missing_provider.get_node_snapshot(NODE_ID) is None


def test_provider_rejects_non_uuid_node_identifiers():
    provider = PostgresStatusSnapshotProvider(lambda: FakeConnection(None))
    with pytest.raises(TypeError):
        provider.get_node_snapshot("not-a-uuid")
