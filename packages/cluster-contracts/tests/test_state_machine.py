import pytest

from geelark_cluster_contracts import InstanceState, can_transition, require_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (InstanceState.PENDING, InstanceState.RESERVED),
        (InstanceState.RESERVED, InstanceState.STARTING),
        (InstanceState.STARTING, InstanceState.RUNNING),
        (InstanceState.RUNNING, InstanceState.STOPPING),
        (InstanceState.STOPPING, InstanceState.STOPPED),
        (InstanceState.UNKNOWN, InstanceState.RECONCILING),
        (InstanceState.RECONCILING, InstanceState.RUNNING),
        (InstanceState.RECONCILING, InstanceState.STOPPED),
        (InstanceState.STOPPED, InstanceState.RESERVED),
    ],
)
def test_valid_transitions_are_allowed(current, target):
    assert can_transition(current, target)
    assert require_transition(current, target) == target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (InstanceState.UNKNOWN, InstanceState.STARTING),
        (InstanceState.RUNNING, InstanceState.STOPPED),
        (InstanceState.FAILED, InstanceState.RUNNING),
        (InstanceState.PENDING, InstanceState.RUNNING),
        (InstanceState.RECONCILING, InstanceState.STARTING),
    ],
)
def test_unsafe_transitions_are_rejected(current, target):
    assert not can_transition(current, target)
    with pytest.raises(ValueError):
        require_transition(current, target)


def test_unknown_state_name_is_not_accepted():
    assert not can_transition("invented-state", InstanceState.RUNNING)
    with pytest.raises(ValueError):
        require_transition("invented-state", InstanceState.RUNNING)
