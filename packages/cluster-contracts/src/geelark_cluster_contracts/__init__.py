"""Contratos tipados del clúster Geelark-IA."""

from .state_machine import InstanceState, can_transition, require_transition

from .models import (
    AndroidRequirement,
    AssignmentCommand,
    Confidence,
    CpuTelemetry,
    ErrorCode,
    ErrorDetail,
    EngineRequirement,
    Heartbeat,
    MemoryTelemetry,
    NodeHealth,
    OperationResult,
    OperationStatus,
    ProtocolEnvelope,
    ResourceReservation,
    TelemetryResources,
    VolumeTelemetry,
)

__all__ = [
    "AndroidRequirement",
    "AssignmentCommand",
    "Confidence",
    "CpuTelemetry",
    "ErrorCode",
    "ErrorDetail",
    "EngineRequirement",
    "Heartbeat",
    "InstanceState",
    "MemoryTelemetry",
    "NodeHealth",
    "OperationResult",
    "OperationStatus",
    "ProtocolEnvelope",
    "ResourceReservation",
    "TelemetryResources",
    "VolumeTelemetry",
    "can_transition",
    "require_transition",
]
