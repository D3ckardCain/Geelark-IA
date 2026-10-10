"""Transporte HTTPS privado para agentes GeeLark-IA."""

from .app import create_agent_app
from .client import AgentHTTPSClient, AgentResponse, AgentTransportError
from .db_auth import InvalidAgentCredential, make_database_authenticator
from .domain_handlers import make_postgres_agent_handlers
from .idempotency import (
    IdempotencyConflict,
    IdempotencyInProgress,
    execute_idempotent,
    make_database_idempotency_runner,
    payload_digest,
)
from .limits import InMemoryRateLimiter, PostgresRateLimiter
from .policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation
from .replay import ReplayRejected, consume_request_nonce, make_database_nonce_consumer
from .server import TransportConfigurationError, make_uvicorn_config, validate_https_listener

__all__ = [
    "AgentHTTPSClient", "AgentPrincipal", "AgentResponse", "AgentTransportError",
    "IdempotencyConflict", "IdempotencyInProgress",
    "InMemoryRateLimiter", "InvalidAgentCredential", "Operation", "PermissionDenied", "PostgresRateLimiter",
    "ReplayRejected", "TransportConfigurationError", "authorize_operation",
    "consume_request_nonce", "create_agent_app", "execute_idempotent",
    "make_database_authenticator", "make_database_idempotency_runner", "make_database_nonce_consumer",
    "make_postgres_agent_handlers",
    "make_uvicorn_config", "payload_digest", "validate_https_listener",
]
