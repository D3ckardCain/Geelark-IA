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
