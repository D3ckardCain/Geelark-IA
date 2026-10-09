import pytest
from pydantic import ValidationError

from geelark_cluster_contracts import ErrorCode, ErrorDetail, Heartbeat

from test_models import valid_heartbeat


@pytest.mark.parametrize("bad_float", [float("nan"), float("inf"), float("-inf")])
def test_cpu_utilization_rejects_non_finite_values(bad_float):
    payload = valid_heartbeat()
    payload["resources"]["cpu"]["utilization_percent"] = bad_float
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_duplicate_volume_ids_are_rejected():
    payload = valid_heartbeat()
    payload["resources"]["volumes"].append(payload["resources"]["volumes"][0].copy())
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_duplicate_active_assignments_are_rejected():
    payload = valid_heartbeat()
    payload["active_assignments"] = [
        "66666666-6666-4666-8666-666666666666",
        "66666666-6666-4666-8666-666666666666",
    ]
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_error_reasons_count_is_bounded():
    with pytest.raises(ValidationError):
        ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="test",
            retryable=False,
            reasons=[f"reason-{i}" for i in range(33)],
        )


def test_error_reason_length_is_bounded():
    with pytest.raises(ValidationError):
        ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="test",
            retryable=False,
            reasons=["x" * 129],
        )


from geelark_cluster_contracts import AssignmentCommand

from test_models import valid_assignment


@pytest.mark.parametrize("bad_float", [float("nan"), float("inf"), float("-inf")])
def test_cpu_reservation_rejects_non_finite_values(bad_float):
    payload = valid_assignment()
    payload["resource_reservation"]["cpu_units"] = bad_float
    with pytest.raises(ValidationError):
        AssignmentCommand.model_validate(payload)


def test_volume_count_is_bounded():
    payload = valid_heartbeat()
    payload["resources"]["volumes"] = [
        {
            "volume_id": f"volume-{i}",
            "free_bytes": 1,
            "confidence": "observed",
        }
        for i in range(65)
    ]
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_active_assignment_count_is_bounded():
    payload = valid_heartbeat()
    payload["active_assignments"] = [
        f"66666666-6666-4666-8666-{i:012d}" for i in range(4097)
    ]
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)
