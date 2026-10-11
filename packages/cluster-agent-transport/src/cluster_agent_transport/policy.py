"""Adaptador de autorización del transporte hacia la política canónica del agente.

Este módulo traduce los nombres de ruta HTTP a operaciones de dominio. La
decisión de permisos y la validación de expiración viven en cluster_agent_auth.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from cluster_agent_auth.authorization import (
    AgentAuthorizationContext,
    AgentAuthorizationError,
    AgentOperation,
    authorize_agent_operation,
)


class Operation(str, Enum):
    HEARTBEAT = "heartbeat"
    CAPABILITIES = "capabilities"
    MODULES_REPORT = "modules_report"
    TASK_FETCH = "task_fetch"
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
    credential_expires_at: datetime


class PermissionDenied(Exception):
    """El nodo está autenticado, pero no tiene permiso para la operación."""


_OPERATION_MAP = {
    Operation.HEARTBEAT: AgentOperation.HEARTBEAT,
    Operation.CAPABILITIES: AgentOperation.PUBLISH_CAPABILITIES,
    Operation.MODULES_REPORT: AgentOperation.REPORT_MODULES,
    Operation.TASK_FETCH: AgentOperation.CLAIM_TASK,
    Operation.STATUS_READ: AgentOperation.READ_OWN_STATUS,
    Operation.TASK_ACCEPT: AgentOperation.ACCEPT_TASK,
    Operation.TASK_PROGRESS: AgentOperation.REPORT_PROGRESS,
    Operation.TASK_RESULT: AgentOperation.REPORT_RESULT,
    Operation.RECONCILE: AgentOperation.RECONCILE,
}


def authorize_operation(principal: AgentPrincipal, operation: Operation) -> None:
    """Aplica la política canónica con estado y expiración de la credencial."""
    if not isinstance(principal, AgentPrincipal):
        raise PermissionDenied("AUTHORIZATION_CONTEXT_INVALID")
    try:
        route_operation = operation if isinstance(operation, Operation) else Operation(operation)
        canonical_operation = _OPERATION_MAP[route_operation]
        context = AgentAuthorizationContext(
            node_admin_state=principal.admin_state,
            credential_status=principal.credential_status,
            credential_expires_at=principal.credential_expires_at,
        )
        authorize_agent_operation(context, canonical_operation)
    except (AgentAuthorizationError, KeyError, TypeError, ValueError) as exc:
        code = getattr(exc, "code", "OPERATION_NOT_ALLOWED")
        raise PermissionDenied(code) from None
