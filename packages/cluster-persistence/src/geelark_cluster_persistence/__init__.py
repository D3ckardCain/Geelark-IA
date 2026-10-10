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
from .service import AssignmentRequest, assign_instance

__all__ = [
    "AssignmentError",
    "AssignmentRequest",
    "IdempotencyConflict",
    "IdempotencyRecordIncomplete",
    "InstanceAlreadyAssigned",
    "InstanceNotFound",
    "InstanceStateBlocked",
    "InsufficientCapacity",
    "InvalidAssignmentRequest",
    "NodeCapacityNotConfigured",
    "NodeNotEligible",
    "assign_instance",
]
