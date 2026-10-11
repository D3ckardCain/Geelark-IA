"""Capa transaccional de persistencia del clúster Geelark-IA."""

from .domain import (
    AssignmentError,
    IdempotencyConflict,
    IdempotencyRecordIncomplete,
    InstanceAlreadyAssigned,
    InstanceNotFound,
    InstanceStateBlocked,
    InsufficientCapacity,
    InvalidAssignmentRequest,
    NodeCapacityNotConfigured,
    NodeNotEligible,
)
from .outbox import ClaimedOutboxEvent, claim_outbox_batch, mark_outbox_delivered, retry_outbox_event
from .service import AssignmentRequest, assign_instance
from .status_snapshot import PostgresStatusSnapshotProvider, StatusSnapshotProvider, build_status_snapshot

__all__ = [
    "AssignmentError",
    "AssignmentRequest",
    "ClaimedOutboxEvent",
    "IdempotencyConflict",
    "IdempotencyRecordIncomplete",
    "InstanceAlreadyAssigned",
    "InstanceNotFound",
    "InstanceStateBlocked",
    "InsufficientCapacity",
    "InvalidAssignmentRequest",
    "NodeCapacityNotConfigured",
    "NodeNotEligible",
    "PostgresStatusSnapshotProvider",
    "StatusSnapshotProvider",
    "assign_instance",
    "build_status_snapshot",
    "claim_outbox_batch",
    "mark_outbox_delivered",
    "retry_outbox_event",
]
