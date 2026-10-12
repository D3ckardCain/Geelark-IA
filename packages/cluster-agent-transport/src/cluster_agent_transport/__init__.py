"""Transporte HTTPS privado para agentes GeeLark-IA."""

from .app import create_agent_app, create_postgres_agent_app
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
from .credentials import CredentialProvider, CredentialProviderError, SystemdCredentialProvider
from .supervisor import AgentNodeSupervisor
from .bootstrap import AgentComponents, build_agent_components
from .lifecycle import AgentReceiptSyncLifecycle
from .policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation
from .replay import ReplayRejected, consume_request_nonce, make_database_nonce_consumer
from .runtime import AgentTransportRuntime
from .server import TransportConfigurationError, make_uvicorn_config, validate_https_listener

__all__ = [
    "AgentComponents", "AgentHTTPSClient", "AgentNodeSupervisor", "AgentReceiptSyncLifecycle", "AgentPrincipal", "AgentResponse", "AgentTransportError", "AgentTransportRuntime",
    "IdempotencyConflict", "IdempotencyInProgress",
    "CredentialProvider", "CredentialProviderError", "SystemdCredentialProvider",
    "InMemoryRateLimiter", "InvalidAgentCredential", "Operation", "PermissionDenied", "PostgresRateLimiter",
    "ReplayRejected", "TransportConfigurationError", "authorize_operation",
    "consume_request_nonce", "create_agent_app", "create_postgres_agent_app", "execute_idempotent",
    "build_agent_components", "make_database_authenticator", "make_database_idempotency_runner", "make_database_nonce_consumer",
    "make_postgres_agent_handlers",
    "make_uvicorn_config", "payload_digest", "validate_https_listener",
]
