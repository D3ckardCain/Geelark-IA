"""Autorización por operación para el transporte privado de agentes.

El estado de autenticación no concede permisos generales. Los nodos pending
solo reciben acceso a telemetría y consulta de su propio estado.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Operation(str, Enum):
    HEARTBEAT = "heartbeat"
    CAPABILITIES = "capabilities"
    MODULES_REPORT = "modules_report"
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
    Operation.MODULES_REPORT,
    Operation.STATUS_READ,
    Operation.TASK_ACCEPT,
    Operation.TASK_PROGRESS,
    Operation.TASK_RESULT,
    Operation.RECONCILE,
})


def authorize_operation(principal: AgentPrincipal, operation: Operation) -> None:
    """Falla cerrada; exige combinaciones coherentes de estado/credencial."""
    pair = (principal.admin_state, principal.credential_status)
    if pair == ("pending", "pending"):
        if operation not in _PENDING_ALLOWED:
            raise PermissionDenied("Nodo pendiente: operación permitida solo para telemetría/consulta.")
        return
    if pair == ("active", "active"):
        if operation not in _ACTIVE_ALLOWED:
            raise PermissionDenied("Operación no autorizada.")
        return
    raise PermissionDenied("Credencial o estado administrativo no autorizado.")
