from cluster_agent_transport.idempotency import _idempotency_ttl_seconds


def test_idempotency_ttl_matches_transport_operation_scopes():
    one_day = 24 * 60 * 60
    ninety_days = 90 * 24 * 60 * 60

    for operation in ("heartbeat", "capabilities", "modules_report", "status_read"):
        assert _idempotency_ttl_seconds(f"agent:00000000-0000-0000-0000-000000000001:{operation}") == one_day

    for operation in (
        "task_fetch", "task_accept", "task_progress", "task_result",
        "reconcile", "reconcile_inventory",
    ):
        assert _idempotency_ttl_seconds(f"agent:00000000-0000-0000-0000-000000000001:{operation}") == ninety_days


def test_unknown_idempotency_scope_is_not_expired_automatically():
    assert _idempotency_ttl_seconds("agent:00000000-0000-0000-0000-000000000001:future_operation") is None
    assert _idempotency_ttl_seconds("custom:heartbeat") is None
