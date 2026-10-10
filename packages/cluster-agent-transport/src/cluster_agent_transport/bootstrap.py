"""Construcción explícita de los componentes del agente, sin iniciar hilos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from .client import AgentHTTPSClient
from .credentials import CredentialProvider
from .lifecycle import AgentReceiptSyncLifecycle
from .runtime import AgentTransportRuntime
from .supervisor import AgentSupervisor


@dataclass(frozen=True)
class AgentComponents:
    """Componentes ya configurados; el llamador controla el arranque y apagado."""

    client: AgentHTTPSClient
    runtime: AgentTransportRuntime
    receipt_lifecycle: AgentReceiptSyncLifecycle
    supervisor: AgentSupervisor


def build_agent_components(
    *,
    base_url: str,
    ca_cert: str | Path,
    credential_provider: CredentialProvider,
    journal: Any,
    local_node_id: UUID,
    heartbeat_payload: Callable[[], dict[str, Any]],
    capabilities_payload: Callable[[], dict[str, Any]],
    request_timeout_seconds: float = 5.0,
    receipt_batch_size: int = 100,
    heartbeat_interval_seconds: float = 30.0,
    reconcile_inventory: Callable[[], list[dict[str, Any]]] | None = None,
    on_reconciliation: Callable[[Any], None] | None = None,
    reconciliation_retry_interval_seconds: float = 60.0,
    clock: Callable[..., Any] | None = None,
    on_error: Callable[[str], None] | None = None,
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
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=receipt_lifecycle,
        heartbeat_payload=heartbeat_payload,
        capabilities_payload=capabilities_payload,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        reconcile_inventory=reconcile_inventory,
        on_reconciliation=on_reconciliation,
        reconciliation_retry_interval_seconds=reconciliation_retry_interval_seconds,
        on_error=on_error,
    )
    return AgentComponents(
        client=client,
        runtime=runtime,
        receipt_lifecycle=receipt_lifecycle,
        supervisor=supervisor,
    )
