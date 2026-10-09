"""Modelos Pydantic estrictos para el protocolo del clúster.

Estos modelos validan la forma y coherencia local de mensajes. No implementan
autenticación, persistencia, fencing, idempotencia durable ni autorización.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    """Base estricta: no acepta campos desconocidos."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProtocolEnvelope(ContractModel):
    protocol_version: str = Field(pattern=r"^\d+\.\d+$")
    request_id: UUID
    sent_at: AwareDatetime


class Confidence(StrEnum):
    OBSERVED = "observed"
    CONFIGURED = "configured"
    UNKNOWN = "unknown"


class NodeHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CpuTelemetry(ContractModel):
    logical_cores: int = Field(ge=1)
    utilization_percent: float | None = Field(default=None, ge=0, le=100)
    confidence: Confidence


class MemoryTelemetry(ContractModel):
    total_bytes: int = Field(gt=0)
    available_bytes: int = Field(ge=0)
    confidence: Confidence

    @model_validator(mode="after")
    def available_not_above_total(self):
        if self.available_bytes > self.total_bytes:
            raise ValueError("available_bytes no puede superar total_bytes")
        return self


class VolumeTelemetry(ContractModel):
    volume_id: str = Field(min_length=1, max_length=128)
    free_bytes: int = Field(ge=0)
    confidence: Confidence


class TelemetryResources(ContractModel):
    cpu: CpuTelemetry
    memory: MemoryTelemetry
    volumes: list[VolumeTelemetry] = Field(default_factory=list)


class Heartbeat(ProtocolEnvelope):
    node_id: UUID
    sequence: int = Field(ge=0)
    health: NodeHealth
    resources: TelemetryResources
    active_assignments: list[UUID] = Field(default_factory=list)


class ResourceReservation(ContractModel):
    memory_bytes: int = Field(gt=0)
    storage_bytes: int = Field(gt=0)
    cpu_units: float = Field(gt=0)


class EngineRequirement(ContractModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)


class AndroidRequirement(ContractModel):
    api_level: int = Field(ge=1, le=100)
    abi: str = Field(min_length=1, max_length=32)
    image_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class AssignmentCommand(ProtocolEnvelope):
    operation_id: UUID
    idempotency_key: str = Field(min_length=16, max_length=200)
    instance_id: UUID
    assignment_epoch: int = Field(ge=1)
    lease_expires_at: AwareDatetime
    desired_state: Literal["running", "stopped"]
    engine: EngineRequirement
    android: AndroidRequirement
    resource_reservation: ResourceReservation

    @model_validator(mode="after")
    def lease_must_follow_message_time(self):
        if self.lease_expires_at <= self.sent_at:
            raise ValueError("lease_expires_at debe ser posterior a sent_at")
        return self


class OperationStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ErrorCode(StrEnum):
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    NODE_REVOKED = "NODE_REVOKED"
    PROTOCOL_VERSION_UNSUPPORTED = "PROTOCOL_VERSION_UNSUPPORTED"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    MESSAGE_EXPIRED = "MESSAGE_EXPIRED"
    STALE_SEQUENCE = "STALE_SEQUENCE"
    STALE_ASSIGNMENT_EPOCH = "STALE_ASSIGNMENT_EPOCH"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    INSTANCE_ALREADY_ASSIGNED = "INSTANCE_ALREADY_ASSIGNED"
    NODE_NOT_ELIGIBLE = "NODE_NOT_ELIGIBLE"
    INSUFFICIENT_MEMORY = "INSUFFICIENT_MEMORY"
    INSUFFICIENT_STORAGE = "INSUFFICIENT_STORAGE"
    ENGINE_UNAVAILABLE = "ENGINE_UNAVAILABLE"
    ANDROID_IMAGE_INCOMPATIBLE = "ANDROID_IMAGE_INCOMPATIBLE"
    CAPACITY_CHANGED = "CAPACITY_CHANGED"
    LEASE_STATE_UNCERTAIN = "LEASE_STATE_UNCERTAIN"
    OPERATION_RESULT_UNKNOWN = "OPERATION_RESULT_UNKNOWN"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(ContractModel):
    code: ErrorCode
    message: str = Field(min_length=1, max_length=500)
    retryable: bool
    reasons: list[str] = Field(default_factory=list)


class OperationResult(ProtocolEnvelope):
    operation_id: UUID
    node_id: UUID
    instance_id: UUID
    assignment_epoch: int = Field(ge=1)
    status: OperationStatus
    observed_state: Literal[
        "pending",
        "reserved",
        "starting",
        "running",
        "stopping",
        "stopped",
        "failed",
        "unknown",
        "reconciling",
    ]
    error: ErrorDetail | None = None

    @model_validator(mode="after")
    def rejected_result_requires_error(self):
        if self.status == OperationStatus.REJECTED and self.error is None:
            raise ValueError("Un resultado rejected debe incluir error")
        if self.status != OperationStatus.REJECTED and self.error is not None:
            raise ValueError("error solo se permite con status rejected en esta versión")
        return self
