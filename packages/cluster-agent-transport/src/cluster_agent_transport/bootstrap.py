"""Construcción explícita de los componentes del agente, sin iniciar hilos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any, Callable
from uuid import UUID

from .client import AgentHTTPSClient
from .credentials import CredentialProvider
from .lifecycle import AgentReceiptSyncLifecycle
from .runtime import AgentTransportRuntime
from .supervisor import AgentNodeSupervisor


@dataclass(frozen=True)
class AgentComponents:
    """Componentes ya configurados; el llamador controla el arranque y apagado."""

    client: AgentHTTPSClient
    runtime: AgentTransportRuntime
    receipt_lifecycle: AgentReceiptSyncLifecycle
    supervisor: AgentNodeSupervisor


def build_agent_components(
    *,
    base_url: str,
    ca_cert: str | Path,
    credential_provider: CredentialProvider,
    journal: Any,
    local_node_id: UUID,
    agent_version: str,
    capabilities: list[str],
    request_timeout_seconds: float = 5.0,
    receipt_batch_size: int = 100,
    heartbeat_interval_seconds: float = 30.0,
    capabilities_interval_seconds: float = 300.0,
    status_interval_seconds: float = 60.0,
    metrics_provider: Callable[[], dict[str, int | float]] | None = None,
    clock: Callable[..., Any] | None = None,
    on_error: Callable[[str], None] | None = None,
    monotonic_clock: Callable[[], float] = monotonic,
) -> AgentComponents:
    """Construye cliente TLS, runtime, sincronizador y supervisor, pero no los arranca.

    La URL/CA se validan antes de leer la credencial. El token solo se conserva en
    memoria dentro del runtime; no se imprime ni se escribe en archivos por esta fábrica.
    """
    if not callable(getattr(credential_provider, "load_bearer_token", None)):
        raise ValueError("credential_provider debe implementar load_bearer_token()")

    client = AgentHTTPSClient(
        base_url=base_url,
        ca_cert=str(ca_cert),
        timeout_seconds=request_timeout_seconds,
    )
    token = credential_provider.load_bearer_token()
    runtime_kwargs: dict[str, Any] = {
        "client": client,
        "bearer_token": token,
        "journal": journal,
        "local_node_id": local_node_id,
    }
    if clock is not None:
        runtime_kwargs["clock"] = clock
    runtime = AgentTransportRuntime(**runtime_kwargs)
    receipt_lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime,
        batch_size=receipt_batch_size,
    )
    supervisor = AgentNodeSupervisor(
        runtime=runtime,
        receipt_sync=receipt_lifecycle,
        agent_version=agent_version,
        capabilities=capabilities,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        capabilities_interval_seconds=capabilities_interval_seconds,
        status_interval_seconds=status_interval_seconds,
        metrics_provider=metrics_provider,
        on_error=on_error,
        monotonic=monotonic_clock,
    )
    return AgentComponents(
        client=client,
        runtime=runtime,
        receipt_lifecycle=receipt_lifecycle,
        supervisor=supervisor,
    )
