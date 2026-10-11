"""Pure unit tests for Master-derived health and heartbeat freshness."""
from datetime import datetime, timedelta, timezone

import pytest

from cluster_agent_transport.domain_handlers import HEARTBEAT_STALE_AFTER, _derive_health_state, _derive_module_reports


NOW = datetime(2026, 10, 10, 20, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("reported", "age", "expected"),
    [
        ("healthy", timedelta(seconds=1), "healthy"),
        ("degraded", timedelta(seconds=1), "degraded"),
        ("unhealthy", timedelta(seconds=1), "degraded"),
        ("unknown", timedelta(seconds=1), "unknown"),
        ("healthy", HEARTBEAT_STALE_AFTER, "offline"),
        ("healthy", HEARTBEAT_STALE_AFTER + timedelta(seconds=1), "offline"),
        ("degraded", HEARTBEAT_STALE_AFTER + timedelta(minutes=3), "offline"),
    ],
)
def test_health_uses_master_observation_time_and_reported_state(reported, age, expected):
    assert _derive_health_state(reported, NOW - age, now=NOW) == expected


@pytest.mark.parametrize("reported", ["healthy", "degraded", "unhealthy", "unknown"])
def test_missing_heartbeat_is_never_healthy(reported):
    assert _derive_health_state(reported, None, now=NOW) == "offline"


def test_worker_report_cannot_override_stale_master_health():
    reported_health_state = "healthy"
    last_seen_at = NOW - timedelta(minutes=5)
    assert _derive_health_state(reported_health_state, last_seen_at, now=NOW) == "offline"


def test_heartbeat_exactly_at_freshness_boundary_is_stale():
    assert _derive_health_state(
        "healthy",
        NOW - HEARTBEAT_STALE_AFTER,
        now=NOW,
    ) == "offline"


def test_module_report_is_unknown_when_node_heartbeat_is_stale():
    reports = [{"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0",
                "checked_at": NOW.isoformat(), "source": "agent-report", "error_code": None}]
    result = _derive_module_reports(reports, NOW - timedelta(minutes=5), now=NOW)
    assert result[0]["state"] == "unknown"
    assert result[0]["source"] == "master-check"
    assert result[0]["error_code"] == "NODE_STALE"


def test_module_report_is_unknown_when_its_observation_is_old():
    reports = [{"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0",
                "checked_at": (NOW - timedelta(minutes=10)).isoformat(), "source": "agent-report", "error_code": None}]
    result = _derive_module_reports(reports, NOW - timedelta(seconds=1), now=NOW)
    assert result[0]["state"] == "unknown"
    assert result[0]["source"] == "master-check"
    assert result[0]["error_code"] == "REPORT_STALE"

def test_future_or_malformed_module_report_cannot_appear_operational():
    reports = [
        {
            "module_id": "agent-supervisor",
            "state": "operational",
            "version": "0.1.0",
            "checked_at": (NOW + timedelta(minutes=1)).isoformat(),
            "source": "agent-report",
            "error_code": None,
            "secret": "must-not-leak",
        },
        {
            "module_id": "agent-transport",
            "state": ["operational"],
            "version": "0.1.0",
            "checked_at": NOW.isoformat(),
            "source": ["agent-report"],
            "error_code": None,
            "unexpected": "must-not-leak",
        },
        {
            "module_id": "unregistered-module",
            "state": "operational",
            "version": "0.1.0",
            "checked_at": NOW.isoformat(),
            "source": "agent-report",
            "error_code": None,
        },
    ]
    result = _derive_module_reports(reports, NOW - timedelta(seconds=1), now=NOW)

    assert len(result) == 2
    assert result[0]["state"] == "unknown"
    assert result[0]["source"] == "master-check"
    assert result[0]["error_code"] == "REPORT_TIME_SKEW"
    assert result[0]["checked_at"] is None
    assert set(result[0]) == {"module_id", "state", "version", "checked_at", "source", "error_code"}
    assert result[1]["state"] == "unknown"
    assert result[1]["source"] == "master-check"
    assert result[1]["error_code"] == "INVALID_MODULE_REPORT"
    assert set(result[1]) == {"module_id", "state", "version", "checked_at", "source", "error_code"}
