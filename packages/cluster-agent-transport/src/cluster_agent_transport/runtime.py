"""Puente entre el cliente HTTPS y un journal local compatible con AgentJournal.

No recibe ni ejecuta comandos. Los resultados se escriben primero en el journal
local; si la red falla, el recibo queda disponible para sincronizarse después.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID, uuid4

from .client import AgentHTTPSClient, AgentResponse, AgentTransportError
from .idempotency import payload_digest


class AgentTransportRuntime:
    """Adaptador saliente; nunca ejecuta tareas y conserva resultados si falla la red.

    Los recibos en estado accepted no se envían como si fueran resultados de tarea:
    solo running/succeeded/failed se transmiten por este adaptador.
    """

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

    def claim_next_task(self, *, idempotency_key: str) -> AgentResponse:
        """Reclama una tarea; conservar la misma clave si se reintenta por timeout."""
        return self._request(
            "POST", "/agent/v1/tasks/claim", {"schema_version": 1},
            idempotency_key=idempotency_key,
        )

    def accept_task(self, *, task_id: UUID, idempotency_key: str | None = None) -> AgentResponse:
        """Confirma recepción de una tarea sin ejecutarla."""
        key = idempotency_key or f"task-accept-{task_id}"
        return self._request(
            "POST", f"/agent/v1/tasks/{task_id}/accept",
            {"schema_version": 1, "state": "accepted", "details": {}},
            idempotency_key=key,
        )

    def reconcile(self, *, assignments: list[dict[str, Any]], idempotency_key: str) -> AgentResponse:
        """Envía una comparación de solo lectura; no aplica cambios en el controlador."""
        if not isinstance(assignments, list) or len(assignments) > 500:
            raise ValueError("assignments debe contener como máximo 500 elementos")
        if any(not isinstance(item, dict) for item in assignments):
            raise ValueError("cada elemento de assignments debe ser un objeto")
        return self._request(
            "POST", "/agent/v1/reconcile",
            {"schema_version": 1, "assignments": assignments},
            idempotency_key=idempotency_key,
        )

    def report_progress(
        self, *, operation_id: UUID, instance_id: UUID, assignment_epoch: int,
        result: dict[str, Any], task_id: UUID | None = None
    ) -> AgentResponse:
        self._record_local(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=assignment_epoch,
            status="running", result=result,
        )
        response = self._send_receipt(
            operation_id=operation_id, task_id=task_id, state="running", result=result, route="progress"
        )
        return response

    def report_result(
        self, *, operation_id: UUID, instance_id: UUID, assignment_epoch: int,
        status: str, result: dict[str, Any], task_id: UUID | None = None,
    ) -> AgentResponse:
        if status not in {"succeeded", "rejected", "failed", "unknown"}:
            raise ValueError("El resultado final debe ser succeeded o failed.")
        self._record_local(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=assignment_epoch,
            status=status, result=result,
        )
        response = self._send_receipt(
            operation_id=operation_id, task_id=task_id, state=status, result=result, route="result"
        )
        return response

    def sync_pending_receipts(self, *, limit: int = 100) -> tuple[int, int]:
        """Envía un lote acotado de recibos pendientes tras reconectar.

        Devuelve (confirmados, intentados). Un error de red detiene el lote y deja
        los recibos restantes en el journal para el siguiente ciclo.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit debe ser un entero entre 1 y 1000")
        list_pending = getattr(self.journal, "list_pending_receipts", None)
        if not callable(list_pending):
            raise ValueError("journal debe implementar list_pending_receipts(limit=...)")
        receipts = list_pending(limit=limit)
        confirmed = 0
        attempted = 0
        for receipt in receipts:
            attempted += 1
            try:
                response = self.sync_receipt(receipt)
            except AgentTransportError:
                break
            if response is not None and 200 <= response.status < 300:
                confirmed += 1
        return confirmed, attempted

    def sync_receipt(self, receipt: Any) -> AgentResponse | None:
        """Reintenta un recibo durable tras reconectar; el journal conserva el resultado."""
        if getattr(receipt, "node_id", None) != self.local_node_id:
            raise ValueError("El recibo no pertenece a este nodo.")
        status = getattr(receipt, "status", None)
        result = getattr(receipt, "result", None)
        operation_id = getattr(receipt, "operation_id", None)
        instance_id = getattr(receipt, "instance_id", None)
        epoch = getattr(receipt, "assignment_epoch", None)
        task_id = getattr(receipt, "task_id", operation_id)
        if not isinstance(operation_id, UUID) or not isinstance(instance_id, UUID):
            raise ValueError("Recibo local inválido.")
        if status == "running" and isinstance(result, dict):
            return self.report_progress(
                operation_id=operation_id, instance_id=instance_id,
                assignment_epoch=epoch, result=result, task_id=task_id,
            )
        if status in {"succeeded", "rejected", "failed", "unknown"} and isinstance(result, dict):
            return self.report_result(
                operation_id=operation_id, instance_id=instance_id,
                assignment_epoch=epoch, status=status, result=result, task_id=task_id,
            )
        return None

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
        self, *, operation_id: UUID, state: str, result: dict[str, Any], route: str,
        task_id: UUID | None = None
    ) -> AgentResponse:
        payload = {"schema_version": 1, "state": state, "details": result}
        digest = payload_digest(payload)[:32]
        key = f"{route}-{operation_id}-{digest}"
        response = self._request(
            "POST", f"/agent/v1/tasks/{task_id or operation_id}/{route}", payload, idempotency_key=key
        )
        if state in {"succeeded", "rejected", "failed"}:
            mark_synced = getattr(self.journal, "mark_receipt_synced", None)
            if callable(mark_synced):
                mark_synced(operation_id)
        return response

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
