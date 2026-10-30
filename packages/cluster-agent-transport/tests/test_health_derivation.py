"""Pure unit tests for Master-derived health and heartbeat freshness."""
from datetime import datetime, timedelta, timezone

import pytest

from cluster_agent_transport.domain_handlers import HEARTBEAT_STALE_AFTER, _derive_health_state, _derive_module_reports


NOW = datetime(2026, 10, 10, 20, 0, tzinfo=timezone.utc)


def test_health_derivation_requires_authoritative_now():
    with pytest.raises(TypeError):
        _derive_health_state("healthy", NOW)
    with pytest.raises(TypeError):
        _derive_module_reports([], NOW)


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
