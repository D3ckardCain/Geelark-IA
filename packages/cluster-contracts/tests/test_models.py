from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from geelark_cluster_contracts import (
    AssignmentCommand,
    Confidence,
    ErrorCode,
    ErrorDetail,
    Heartbeat,
    NodeHealth,
    OperationResult,
    OperationStatus,
)

NOW = datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc)
NODE_ID = UUID("22222222-2222-4222-8222-222222222222")
INSTANCE_ID = UUID("66666666-6666-4666-8666-666666666666")
OPERATION_ID = UUID("55555555-5555-4555-8555-555555555555")
REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")


def valid_heartbeat():
    return {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "node_id": str(NODE_ID),
        "sequence": 1,
        "health": "healthy",
        "resources": {
            "cpu": {
                "logical_cores": 8,
                "utilization_percent": 22.5,
                "confidence": "observed",
            },
            "memory": {
                "total_bytes": 16000000000,
                "available_bytes": 8000000000,
                "confidence": "observed",
            },
            "volumes": [
                {
                    "volume_id": "data",
                    "free_bytes": 100000000000,
                    "confidence": "observed",
                }
            ],
        },
        "active_assignments": [],
    }


def valid_assignment():
    return {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "operation_id": str(OPERATION_ID),
        "idempotency_key": "logical-operation-unique-01",
        "instance_id": str(INSTANCE_ID),
        "assignment_epoch": 1,
        "lease_expires_at": (NOW + timedelta(minutes=1)).isoformat(),
        "desired_state": "running",
        "engine": {"name": "test-engine", "version": "0.1"},
        "android": {
            "api_level": 35,
            "abi": "x86_64",
            "image_digest": "sha256:" + "a" * 64,
        },
        "resource_reservation": {
            "memory_bytes": 2000000000,
            "storage_bytes": 10000000000,
            "cpu_units": 2,
        },
    }


def test_valid_heartbeat_is_accepted():
    heartbeat = Heartbeat.model_validate(valid_heartbeat())
    assert heartbeat.sequence == 1
    assert heartbeat.resources.memory.available_bytes == 8_000_000_000


def test_unknown_fields_are_rejected():
    payload = valid_heartbeat()
    payload["shell_command"] = "not-allowed"
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_negative_memory_is_rejected():
    payload = valid_heartbeat()
    payload["resources"]["memory"]["available_bytes"] = -1
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_available_memory_cannot_exceed_total():
    payload = valid_heartbeat()
    payload["resources"]["memory"]["available_bytes"] = 20_000_000_000
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_cpu_percent_must_be_in_range():
    payload = valid_heartbeat()
    payload["resources"]["cpu"]["utilization_percent"] = 101
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_assignment_with_future_lease_is_accepted():
    assignment = AssignmentCommand.model_validate(valid_assignment())
    assert assignment.assignment_epoch == 1


def test_assignment_lease_must_be_after_sent_at():
    payload = valid_assignment()
    payload["lease_expires_at"] = NOW.isoformat()
    with pytest.raises(ValidationError):
        AssignmentCommand.model_validate(payload)


def test_assignment_rejects_short_idempotency_key():
    payload = valid_assignment()
    payload["idempotency_key"] = "short"
    with pytest.raises(ValidationError):
        AssignmentCommand.model_validate(payload)


def test_assignment_rejects_bad_image_digest():
    payload = valid_assignment()
    payload["android"]["image_digest"] = "sha256:not-a-digest"
    with pytest.raises(ValidationError):
        AssignmentCommand.model_validate(payload)


def test_rejected_result_requires_typed_error():
    payload = {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "operation_id": str(OPERATION_ID),
        "node_id": str(NODE_ID),
        "instance_id": str(INSTANCE_ID),
        "assignment_epoch": 1,
        "status": "rejected",
        "observed_state": "failed",
        "error": {
            "code": ErrorCode.NODE_NOT_ELIGIBLE.value,
            "message": "El nodo no cumple los requisitos",
            "retryable": False,
            "reasons": ["INSUFFICIENT_MEMORY"],
        },
    }
    assert OperationResult.model_validate(payload).status == OperationStatus.REJECTED


def test_rejected_result_without_error_is_invalid():
    payload = {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "operation_id": str(OPERATION_ID),
        "node_id": str(NODE_ID),
        "instance_id": str(INSTANCE_ID),
        "assignment_epoch": 1,
        "status": "rejected",
        "observed_state": "failed",
        "error": None,
    }
    with pytest.raises(ValidationError):
        OperationResult.model_validate(payload)

def test_naive_datetime_is_rejected():
    payload = valid_heartbeat()
    payload["sent_at"] = "2026-10-09T18:00:00"
    with pytest.raises(ValidationError):
        Heartbeat.model_validate(payload)


def test_failed_result_requires_typed_error():
    payload = {
        "protocol_version": "0.2",
        "request_id": str(REQUEST_ID),
        "sent_at": NOW.isoformat(),
        "operation_id": str(OPERATION_ID),
        "node_id": str(NODE_ID),
        "instance_id": str(INSTANCE_ID),
        "assignment_epoch": 1,
        "status": "failed",
        "observed_state": "failed",
        "error": {
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": "Fallo controlado de prueba",
            "retryable": False,
            "reasons": [],
        },
    }
    assert OperationResult.model_validate(payload).status == OperationStatus.FAILED
