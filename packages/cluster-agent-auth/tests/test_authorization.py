from datetime import datetime, timedelta, timezone

import pytest

from cluster_agent_auth.authorization import (
    AgentAuthorizationContext,
    AgentAuthorizationError,
    AgentOperation,
    authorize_agent_operation,
)


NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def context(node_state="active", credential_status="active", expires_at=None):
    return AgentAuthorizationContext(
        node_admin_state=node_state,
        credential_status=credential_status,
        credential_expires_at=expires_at or NOW + timedelta(minutes=5),
    )


@pytest.mark.parametrize(
    "operation",
    [
        AgentOperation.HEARTBEAT,
        AgentOperation.PUBLISH_CAPABILITIES,
        AgentOperation.READ_OWN_STATUS,
    ],
)
def test_pending_node_can_only_use_limited_telemetry_operations(operation):
    authorize_agent_operation(context("pending", "pending"), operation, now=NOW)


@pytest.mark.parametrize(
    "operation",
    [
        AgentOperation.ACCEPT_TASK,
        AgentOperation.REPORT_PROGRESS,
        AgentOperation.REPORT_RESULT,
        AgentOperation.RECONCILE,
    ],
)
def test_pending_node_cannot_use_operational_routes(operation):
    with pytest.raises(AgentAuthorizationError) as error:
        authorize_agent_operation(context("pending", "pending"), operation, now=NOW)
    assert error.value.code == "NODE_PENDING_APPROVAL_REQUIRED"


@pytest.mark.parametrize("operation", list(AgentOperation))
def test_active_node_with_active_credential_can_use_declared_operations(operation):
    authorize_agent_operation(context(), operation, now=NOW)


@pytest.mark.parametrize(
    ("node_state", "credential_status"),
    [
        ("revoked", "active"),
        ("disabled", "active"),
        ("active", "pending"),
        ("pending", "active"),
        ("active", "revoked"),
        ("active", "expired"),
    ],
)
def test_unknown_revoked_or_inconsistent_states_fail_closed(node_state, credential_status):
    with pytest.raises(AgentAuthorizationError):
        authorize_agent_operation(context(node_state, credential_status), AgentOperation.HEARTBEAT, now=NOW)


def test_expired_timestamp_is_rejected_even_if_status_has_not_been_updated():
    with pytest.raises(AgentAuthorizationError) as error:
        authorize_agent_operation(context(expires_at=NOW), AgentOperation.HEARTBEAT, now=NOW)
    assert error.value.code == "CREDENTIAL_NOT_VALID"


def test_naive_expiry_is_rejected():
    with pytest.raises(AgentAuthorizationError) as error:
        authorize_agent_operation(
            context(expires_at=datetime(2026, 10, 10, 12, 5)),
            AgentOperation.HEARTBEAT,
            now=NOW,
        )
    assert error.value.code == "CREDENTIAL_EXPIRY_INVALID"


def test_unknown_operation_is_rejected():
    with pytest.raises(AgentAuthorizationError) as error:
        authorize_agent_operation(context(), "execute_shell", now=NOW)
    assert error.value.code == "OPERATION_NOT_ALLOWED"
