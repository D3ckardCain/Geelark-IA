"""Política de autorización por operación para el futuro transporte de agentes.

Este módulo NO autentica tokens, no consulta PostgreSQL y no abre sockets.
El transporte debe validar la credencial y recuperar el estado actual del nodo
antes de invocar esta política. La autorización falla cerrada.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AgentOperation(StrEnum):
    HEARTBEAT = "heartbeat"
    PUBLISH_CAPABILITIES = "publish_capabilities"
    REPORT_MODULES = "report_modules"
    READ_OWN_STATUS = "read_own_status"
    CLAIM_TASK = "claim_task"
    ACCEPT_TASK = "accept_task"
    REPORT_PROGRESS = "report_progress"
    REPORT_RESULT = "report_result"
    RECONCILE = "reconcile"


class AgentAuthorizationError(PermissionError):
    """Error de autorización; code es seguro para diagnóstico."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class AgentAuthorizationContext:
    node_admin_state: str
    credential_status: str
    credential_expires_at: datetime


_PENDING_ALLOWED = frozenset({
    AgentOperation.HEARTBEAT,
    AgentOperation.PUBLISH_CAPABILITIES,
    AgentOperation.READ_OWN_STATUS,
})


def authorize_agent_operation(
    context: AgentAuthorizationContext,
    operation: AgentOperation | str,
    *,
    now: datetime,
) -> None:
    """Autoriza una operación o lanza un error tipado.

    Nodos pending solo pueden enviar telemetría básica y consultar su propio
    estado. La aprobación no se infiere de la autenticación. Nodos o credenciales
    revocados, expirados o con estados desconocidos se rechazan siempre.
    El caller debe pasar `now` desde el reloj autoritativo (PostgreSQL en el
    servidor); esta política no sustituye ese reloj con la hora local.
    """
    if not isinstance(context, AgentAuthorizationContext):
        raise AgentAuthorizationError("AUTHORIZATION_CONTEXT_INVALID")
    if not isinstance(context.node_admin_state, str) or not isinstance(context.credential_status, str):
        raise AgentAuthorizationError("AUTHORIZATION_CONTEXT_INVALID")

    try:
        operation_value = AgentOperation(operation)
    except (ValueError, TypeError):
        raise AgentAuthorizationError("OPERATION_NOT_ALLOWED") from None

    current_time = now
    if (
        not isinstance(current_time, datetime)
        or current_time.tzinfo is None
        or current_time.utcoffset() is None
    ):
        raise AgentAuthorizationError("AUTHORIZATION_TIME_INVALID")

    expiry = context.credential_expires_at
    if (
        not isinstance(expiry, datetime)
        or expiry.tzinfo is None
        or expiry.utcoffset() is None
    ):
        raise AgentAuthorizationError("CREDENTIAL_EXPIRY_INVALID")

    if context.credential_status in {"revoked", "expired"}:
        raise AgentAuthorizationError("CREDENTIAL_NOT_VALID")
    if expiry <= current_time:
        raise AgentAuthorizationError("CREDENTIAL_NOT_VALID")

    if context.node_admin_state == "pending":
        if context.credential_status != "pending":
            raise AgentAuthorizationError("PENDING_NODE_CREDENTIAL_STATE_INVALID")
        if operation_value not in _PENDING_ALLOWED:
            raise AgentAuthorizationError("NODE_PENDING_APPROVAL_REQUIRED")
        return

    if context.node_admin_state == "active":
        if context.credential_status != "active":
            raise AgentAuthorizationError("CREDENTIAL_NOT_ACTIVE")
        return

    raise AgentAuthorizationError("NODE_NOT_ACTIVE")
