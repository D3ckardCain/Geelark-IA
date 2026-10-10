"""Transporte HTTPS privado para agentes GeeLark-IA."""

from .app import create_agent_app
from .db_auth import InvalidAgentCredential, make_database_authenticator
from .idempotency import (
    IdempotencyConflict,
    IdempotencyInProgress,
    execute_idempotent,
    make_database_idempotency_runner,
    payload_digest,
)
from .limits import InMemoryRateLimiter
from .policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation
from .replay import ReplayRejected, consume_request_nonce
from .server import TransportConfigurationError, make_uvicorn_config, validate_https_listener

__all__ = [
    "AgentPrincipal", "IdempotencyConflict", "IdempotencyInProgress",
    "InMemoryRateLimiter", "InvalidAgentCredential", "Operation", "PermissionDenied",
    "ReplayRejected", "TransportConfigurationError", "authorize_operation",
    "consume_request_nonce", "create_agent_app", "execute_idempotent",
    "make_database_authenticator", "make_database_idempotency_runner",
    "make_uvicorn_config", "payload_digest", "validate_https_listener",
]
