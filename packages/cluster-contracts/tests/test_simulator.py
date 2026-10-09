from uuid import UUID

import pytest

from geelark_cluster_contracts.simulator import (
    IdempotencyConflict,
    RuntimeSimulator,
    StaleAssignmentEpoch,
)
from geelark_cluster_contracts.state_machine import InstanceState

INSTANCE_ID = UUID("66666666-6666-4666-8666-666666666666")
EPOCH = 3


@pytest.fixture
def runtime():
    simulator = RuntimeSimulator()
    simulator.register_instance(INSTANCE_ID, EPOCH)
    return simulator


def test_start_and_stop_follow_valid_state_paths(runtime):
    started = runtime.execute(
        INSTANCE_ID, assignment_epoch=EPOCH, desired_state="running",
        idempotency_key="start-instance-operation-01",
    )
    assert started.observed_state == InstanceState.RUNNING
    assert started.changed is True

    stopped = runtime.execute(
        INSTANCE_ID, assignment_epoch=EPOCH, desired_state="stopped",
        idempotency_key="stop-instance-operation-01",
    )
    assert stopped.observed_state == InstanceState.STOPPED
    assert stopped.changed is True


def test_repeated_same_idempotency_key_returns_original_result(runtime):
    first = runtime.execute(
        INSTANCE_ID, assignment_epoch=EPOCH, desired_state="running",
        idempotency_key="start-instance-operation-01",
    )
    second = runtime.execute(
        INSTANCE_ID, assignment_epoch=EPOCH, desired_state="running",
        idempotency_key="start-instance-operation-01",
    )
    assert second == first


def test_reusing_key_for_different_command_is_rejected(runtime):
    runtime.execute(
        INSTANCE_ID, assignment_epoch=EPOCH, desired_state="running",
        idempotency_key="logical-operation-unique-01",
    )
    with pytest.raises(IdempotencyConflict):
        runtime.execute(
            INSTANCE_ID, assignment_epoch=EPOCH, desired_state="stopped",
            idempotency_key="logical-operation-unique-01",
        )


def test_stale_or_future_epoch_is_rejected(runtime):
    for invalid_epoch in (EPOCH - 1, EPOCH + 1):
        with pytest.raises(StaleAssignmentEpoch):
            runtime.execute(
                INSTANCE_ID, assignment_epoch=invalid_epoch, desired_state="running",
                idempotency_key=f"epoch-check-operation-{invalid_epoch:02d}",
            )


def test_unknown_instance_is_rejected(runtime):
    unknown_id = UUID("77777777-7777-4777-8777-777777777777")
    with pytest.raises(RuntimeError, match="no registrada"):
        runtime.execute(
            unknown_id, assignment_epoch=EPOCH, desired_state="running",
            idempotency_key="unknown-instance-operation-01",
        )


def test_inspect_does_not_change_state(runtime):
    inspected = runtime.inspect(INSTANCE_ID)
    assert inspected.observed_state == InstanceState.STOPPED
    assert inspected.changed is False


def test_unsupported_desired_state_is_rejected(runtime):
    with pytest.raises(RuntimeError, match="solo admite"):
        runtime.execute(
            INSTANCE_ID, assignment_epoch=EPOCH, desired_state="deleted",
            idempotency_key="unsupported-operation-01",
        )
