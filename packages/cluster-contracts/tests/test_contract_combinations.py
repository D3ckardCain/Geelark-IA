from datetime import datetime, timezone
from itertools import product
from uuid import UUID

import pytest
from pydantic import ValidationError

from geelark_cluster_contracts import (
    ErrorCode,
    InstanceState,
    OperationResult,
    OperationStatus,
    can_transition,
)

NOW = datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc)
REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")
NODE_ID = UUID("22222222-2222-4222-8222-222222222222")
INSTANCE_ID = UUID("66666666-6666-4666-8666-666666666666")
OPERATION_ID = UUID("55555555-5555-4555-8555-555555555555")

EXPECTED_TRANSITIONS = {
    (InstanceState.PENDING, InstanceState.RESERVED),
    (InstanceState.PENDING, InstanceState.FAILED),
    (InstanceState.RESERVED, InstanceState.STARTING),
    (InstanceState.RESERVED, InstanceState.STOPPED),
    (InstanceState.RESERVED, InstanceState.FAILED),
    (InstanceState.RESERVED, InstanceState.UNKNOWN),
    (InstanceState.STARTING, InstanceState.RUNNING),
    (InstanceState.STARTING, InstanceState.FAILED),
    (InstanceState.STARTING, InstanceState.UNKNOWN),
    (InstanceState.RUNNING, InstanceState.STOPPING),
    (InstanceState.RUNNING, InstanceState.UNKNOWN),
    (InstanceState.STOPPING, InstanceState.STOPPED),
    (InstanceState.STOPPING, InstanceState.FAILED),
    (InstanceState.STOPPING, InstanceState.UNKNOWN),
    (InstanceState.STOPPED, InstanceState.RESERVED),
    (InstanceState.UNKNOWN, InstanceState.RECONCILING),
    (InstanceState.RECONCILING, InstanceState.RUNNING),
    (InstanceState.RECONCILING, InstanceState.STOPPED),
    (InstanceState.RECONCILING, InstanceState.FAILED),
    (InstanceState.RECONCILING, InstanceState.UNKNOWN),
}

EXPECTED_RESULT_STATES = {
    OperationStatus.ACCEPTED: { "reserved", "starting" },
    OperationStatus.REJECTED: { "pending", "failed" },
    OperationStatus.RUNNING: { "running" },
    OperationStatus.STOPPED: { "stopped" },
    OperationStatus.FAILED: { "failed" },
    OperationStatus.UNKNOWN: { "unknown", "reconciling" },
}


def result_payload(status, observed_state, with_error):
    error = None
    if with_error:
        error = {
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": "fallo de prueba",
            "retryable": False,
            "reasons": [],
        }
    return {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "operation_id": str(OPERATION_ID),
        "node_id": str(NODE_ID),
        "instance_id": str(INSTANCE_ID),
        "assignment_epoch": 1,
        "status": status.value,
        "observed_state": observed_state,
        "error": error,
    }


@pytest.mark.parametrize(
    ("current", "target"),
    list(product(list(InstanceState), list(InstanceState))),
)
def test_state_machine_exhaustively_matches_transition_contract(current, target):
    assert can_transition(current, target) is ((current, target) in EXPECTED_TRANSITIONS)


@pytest.mark.parametrize(
    ("status", "observed_state", "with_error"),
    list(product(list(OperationStatus), sorted({s for states in EXPECTED_RESULT_STATES.values() for s in states} | {
        "pending", "reserved", "starting", "running", "stopping", "stopped", "failed", "unknown", "reconciling"
    }), [False, True])),
)
def test_operation_result_combinations_match_contract(status, observed_state, with_error):
    state_is_valid = observed_state in EXPECTED_RESULT_STATES[status]
    error_is_valid = (
        with_error if status in {OperationStatus.REJECTED, OperationStatus.FAILED}
        else True if status == OperationStatus.UNKNOWN
        else not with_error
    )
    expected_valid = state_is_valid and error_is_valid
    payload = result_payload(status, observed_state, with_error)

    if expected_valid:
        assert OperationResult.model_validate(payload).status == status
    else:
        with pytest.raises(ValidationError):
            OperationResult.model_validate(payload)
