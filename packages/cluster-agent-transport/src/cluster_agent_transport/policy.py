"""Autorización por operación para el transporte privado de agentes.

El estado de autenticación no concede permisos generales. Los nodos pending
solo reciben acceso a telemetría y consulta de su propio estado.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"


class Operation(str, Enum):
    HEARTBEAT = "heartbeat"
    CAPABILITIES = "capabilities"
    STATUS_READ = "status_read"
    TASK_ACCEPT = "task_accept"
    TASK_PROGRESS = "task_progress"
    TASK_RESULT = "task_result"
    RECONCILE = "reconcile"


@dataclass(frozen=True)
class AgentPrincipal:
    node_id: str
    credential_id: str
    admin_state: str
    credential_status: str


class PermissionDenied(Exception):
    """El nodo está autenticado, pero no tiene permiso para la operación."""


_PENDING_ALLOWED = frozenset({
    Operation.HEARTBEAT,
    Operation.CAPABILITIES,
    Operation.STATUS_READ,
})
_ACTIVE_ALLOWED = frozenset({
    Operation.HEARTBEAT,
    Operation.CAPABILITIES,
    Operation.STATUS_READ,
    Operation.TASK_ACCEPT,
    Operation.TASK_PROGRESS,
    Operation.TASK_RESULT,
    Operation.RECONCILE,
})


def authorize_operation(principal: AgentPrincipal, operation: Operation) -> None:
    """Falla cerrada; no confía en el cuerpo, query string ni cabeceras proxy."""
    if principal.credential_status != "active" and not (
        principal.admin_state == "pending" and principal.credential_status == "pending"
    ):
        raise PermissionDenied("Credencial o estado administrativo no autorizado.")

    if principal.admin_state == "pending":
        if operation not in _PENDING_ALLOWED:
            raise PermissionDenied("Nodo pendiente: operación permitida solo para telemetría/consulta.")
        return

    if principal.admin_state == "active" and principal.credential_status == "active":
        if operation not in _ACTIVE_ALLOWED:
            raise PermissionDenied("Operación no autorizada.")
        return

    raise PermissionDenied("Nodo no autorizado.")
