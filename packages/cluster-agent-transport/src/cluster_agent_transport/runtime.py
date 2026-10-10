"""Puente entre el cliente HTTPS y un journal local compatible con AgentJournal.

No recibe ni ejecuta comandos. Los resultados se escriben primero en el journal
local; si la red falla, el recibo queda disponible para sincronizarse después.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID, uuid4

from .client import AgentHTTPSClient, AgentResponse, AgentTransportError
from .idempotency import payload_digest


@dataclass(frozen=True)
class SyncSummary:
    attempted: int
    delivered: int
    blocked_operation_id: UUID | None = None


class AgentTransportRuntime:
    """Adaptador de comunicación saliente con persistencia previa de resultados."""

    def __init__(
        self,
        *,
        client: AgentHTTPSClient,
        bearer_token: str,
        journal: Any,
        local_node_id: UUID,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(bearer_token, str) or len(bearer_token) != 64:
            raise ValueError("La credencial bearer debe tener 256 bits en hexadecimal.")
        if any(ch not in "0123456789abcdef" for ch in bearer_token):
            raise ValueError("La credencial bearer debe estar en hexadecimal.")
        if not isinstance(local_node_id, UUID):
            raise ValueError("local_node_id debe ser UUID.")
        if not callable(getattr(journal, "record_result", None)):
            raise ValueError("journal debe implementar record_result.")
        self.client = client
        self._bearer_token = bearer_token
        self.journal = journal
        self.local_node_id = local_node_id
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def send_heartbeat(self, payload: dict[str, Any]) -> AgentResponse:
        return self._request(
            "POST", "/agent/v1/heartbeat", payload,
            idempotency_key="heartbeat-" + str(uuid4()),
        )

    def publish_capabilities(self, payload: dict[str, Any]) -> AgentResponse:
        return self._request(
            "PUT", "/agent/v1/capabilities", payload,
            idempotency_key="capabilities-" + str(uuid4()),
        )

    def read_status(self) -> AgentResponse:
        return self._request("GET", "/agent/v1/status", None)

    def report_progress(
        self, *, operation_id: UUID, instance_id: UUID, assignment_epoch: int, result: dict[str, Any]
    ) -> AgentResponse:
        self._record_local(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=assignment_epoch,
            status="running", result=result,
        )
        response = self._send_receipt(
            operation_id=operation_id, state="running", result=result, route="progress"
        )
        self._mark_delivered(operation_id, assignment_epoch)
        return response

    def report_result(
        self, *, operation_id: UUID, instance_id: UUID, assignment_epoch: int,
        status: str, result: dict[str, Any],
    ) -> AgentResponse:
        if status not in {"succeeded", "failed"}:
            raise ValueError("El resultado final debe ser succeeded o failed.")
        self._record_local(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=assignment_epoch,
            status=status, result=result,
        )
        response = self._send_receipt(
            operation_id=operation_id, state=status, result=result, route="result"
        )
        self._mark_delivered(operation_id, assignment_epoch)
        return response

    def sync_receipt(self, receipt: Any) -> AgentResponse | None:
        """Reintenta un recibo durable tras reconectar; el journal conserva el resultado."""
        if getattr(receipt, "node_id", None) != self.local_node_id:
            raise ValueError("El recibo no pertenece a este nodo.")
        status = getattr(receipt, "status", None)
        result = getattr(receipt, "result", None)
        operation_id = getattr(receipt, "operation_id", None)
        instance_id = getattr(receipt, "instance_id", None)
        epoch = getattr(receipt, "assignment_epoch", None)
        if not isinstance(operation_id, UUID) or not isinstance(instance_id, UUID):
            raise ValueError("Recibo local inválido.")
        if status == "accepted":
            response = self._send_receipt(
                operation_id=operation_id, state="accepted",
                result=result if isinstance(result, dict) else {}, route="accept",
            )
            self._mark_delivered(operation_id, epoch)
            return response
        if status == "running" and isinstance(result, dict):
            return self.report_progress(
                operation_id=operation_id, instance_id=instance_id,
                assignment_epoch=epoch, result=result,
            )
        if status in {"succeeded", "failed"} and isinstance(result, dict):
            return self.report_result(
                operation_id=operation_id, instance_id=instance_id,
                assignment_epoch=epoch, status=status, result=result,
            )
        if status == "unknown":
            response = self._send_receipt(
                operation_id=operation_id, state="unknown",
                result=result if isinstance(result, dict) else {}, route="progress",
            )
            self._mark_delivered(operation_id, epoch)
            return response
        return None

    def sync_pending_receipts(self, *, limit: int = 100) -> SyncSummary:
        """Envía un lote durable; se detiene ante el primer error y deja lo demás pendiente."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit debe estar entre 1 y 1000")
        list_pending = getattr(self.journal, "list_pending_receipts", None)
        mark_delivered = getattr(self.journal, "mark_receipt_delivered", None)
        if not callable(list_pending) or not callable(mark_delivered):
            raise ValueError("El journal debe implementar list_pending_receipts y mark_receipt_delivered.")
        receipts = list_pending(limit=limit)
        attempted = 0
        delivered = 0
        for receipt in receipts:
            attempted += 1
            try:
                response = self.sync_receipt(receipt)
            except AgentTransportError:
                return SyncSummary(attempted, delivered, receipt.operation_id)
            if response is not None:
                delivered += 1
        return SyncSummary(attempted, delivered, None)

    def _mark_delivered(self, operation_id: UUID, assignment_epoch: int) -> None:
        mark = getattr(self.journal, "mark_receipt_delivered", None)
        if callable(mark):
            mark(operation_id, assignment_epoch)

    def _record_local(
        self, *, operation_id: UUID, instance_id: UUID, assignment_epoch: int,
        status: str, result: dict[str, Any],
    ) -> Any:
        return self.journal.record_result(
            operation_id=operation_id,
            instance_id=instance_id,
            node_id=self.local_node_id,
            assignment_epoch=assignment_epoch,
            status=status,
            result=result,
        )

    def _send_receipt(
        self, *, operation_id: UUID, state: str, result: dict[str, Any], route: str
    ) -> AgentResponse:
        payload = {"schema_version": 1, "state": state, "details": result}
        digest = payload_digest(payload)[:32]
        key = f"{route}-{operation_id}-{digest}"
        return self._request(
            "POST", f"/agent/v1/tasks/{operation_id}/{route}", payload, idempotency_key=key
        )

    def _request(
        self, method: str, path: str, payload: Any, *, idempotency_key: str | None = None
    ) -> AgentResponse:
        now = self.clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock debe devolver datetime con zona horaria.")
        headers = {
            "Authorization": "Bearer " + self._bearer_token,
            "X-Agent-Nonce": str(uuid4()),
            "X-Agent-Timestamp": now.astimezone(timezone.utc).isoformat(),
            "X-Request-ID": str(uuid4()),
        }
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        response = self.client.request(method, path, payload=payload, headers=headers)
        if not 200 <= response.status < 300:
            raise AgentTransportError(f"El controlador rechazó la solicitud (HTTP {response.status}).")
        return response
