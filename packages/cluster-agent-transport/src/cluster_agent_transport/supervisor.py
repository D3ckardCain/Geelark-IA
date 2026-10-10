"""Supervisor ligero del agente con workers independientes."""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable
from typing import Any


class AgentSupervisor:
    """Coordina heartbeat/capacidades, recibos durables y reconciliación opcional.

    Heartbeat/capacidades y reconciliación usan hilos separados; el sincronizador de
    recibos conserva su propio hilo. Ningún worker reclama ni ejecuta tareas Android.
    """

    def __init__(
        self,
        *,
        runtime: Any,
        receipt_lifecycle: Any,
        heartbeat_payload: Callable[[], dict[str, Any]],
        capabilities_payload: Callable[[], dict[str, Any]],
        heartbeat_interval_seconds: float = 30.0,
        reconcile_inventory: Callable[[], list[dict[str, Any]]] | None = None,
        on_reconciliation: Callable[[Any], None] | None = None,
        reconciliation_retry_interval_seconds: float = 60.0,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if (
            isinstance(heartbeat_interval_seconds, bool)
            or not isinstance(heartbeat_interval_seconds, (int, float))
            or not math.isfinite(heartbeat_interval_seconds)
            or not 0.1 <= heartbeat_interval_seconds <= 3600
        ):
            raise ValueError("heartbeat_interval_seconds debe estar entre 0.1 y 3600 segundos")
        if not callable(getattr(runtime, "send_heartbeat", None)):
            raise ValueError("runtime debe implementar send_heartbeat(payload)")
        if not callable(getattr(runtime, "publish_capabilities", None)):
            raise ValueError("runtime debe implementar publish_capabilities(payload)")
        if not callable(getattr(receipt_lifecycle, "start", None)):
            raise ValueError("receipt_lifecycle debe implementar start()")
        if not callable(getattr(receipt_lifecycle, "notify_reconnected", None)):
            raise ValueError("receipt_lifecycle debe implementar notify_reconnected()")
        if not callable(getattr(receipt_lifecycle, "stop", None)):
            raise ValueError("receipt_lifecycle debe implementar stop(timeout=...)")
        if not callable(heartbeat_payload) or not callable(capabilities_payload):
            raise ValueError("heartbeat_payload y capabilities_payload deben ser funciones")
        if (
            isinstance(reconciliation_retry_interval_seconds, bool)
            or not isinstance(reconciliation_retry_interval_seconds, (int, float))
            or not math.isfinite(reconciliation_retry_interval_seconds)
            or not 1 <= reconciliation_retry_interval_seconds <= 3600
        ):
            raise ValueError("reconciliation_retry_interval_seconds debe estar entre 1 y 3600")
        if reconcile_inventory is not None and not callable(reconcile_inventory):
            raise ValueError("reconcile_inventory debe ser callable")
        if on_reconciliation is not None and not callable(on_reconciliation):
            raise ValueError("on_reconciliation debe ser callable")
        if reconcile_inventory is not None and not callable(getattr(runtime, "reconcile_inventory", None)):
            raise ValueError("runtime debe implementar reconcile_inventory(inventory)")
        if on_error is not None and not callable(on_error):
            raise ValueError("on_error debe ser callable")

        self.runtime = runtime
        self.receipt_lifecycle = receipt_lifecycle
        self.heartbeat_payload = heartbeat_payload
        self.capabilities_payload = capabilities_payload
        self.reconcile_inventory = reconcile_inventory
        self.on_reconciliation = on_reconciliation
        self.reconciliation_retry_interval_seconds = float(reconciliation_retry_interval_seconds)
        self.heartbeat_interval_seconds = float(heartbeat_interval_seconds)
        self._on_error = on_error or (lambda code: None)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._reconciliation_wake = threading.Event()
        self._reconciliation_requested = threading.Event()
        if reconcile_inventory is not None:
            self._reconciliation_requested.set()
        self._thread: threading.Thread | None = None
        self._reconciliation_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._offline = False
        self._next_reconciliation_at = 0.0

    @property
    def running(self) -> bool:
        if self._stop.is_set():
            return False
        return any(
            thread is not None and thread.is_alive()
            for thread in (self._thread, self._reconciliation_thread)
        )

    def start(self) -> None:
        """Arranca una sola vez los workers de recibos, heartbeat y reconciliación."""
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("El supervisor ya fue detenido y no puede reiniciarse")
            if self._thread is not None:
                if self._thread.is_alive():
                    return
                raise RuntimeError("El supervisor ya fue detenido y no puede reiniciarse")

            self.receipt_lifecycle.start()
            try:
                if self.reconcile_inventory is not None:
                    self._reconciliation_thread = threading.Thread(
                        target=self._run_reconciliation,
                        name="geelark-agent-reconciliation",
                        daemon=True,
                    )
                    self._reconciliation_thread.start()
                self._thread = threading.Thread(
                    target=self._run, name="geelark-agent-supervisor", daemon=True
                )
                self._thread.start()
            except Exception:
                self._stop.set()
                self._wake.set()
                self._reconciliation_wake.set()
                if self._reconciliation_thread is not None:
                    self._reconciliation_thread.join(timeout=1)
                self.receipt_lifecycle.stop(timeout=1)
                raise

    def notify_reconnected(self) -> None:
        """Despierta heartbeat/recibos y solicita una comparación de inventario."""
        if self._stop.is_set():
            return
        if self.reconcile_inventory is not None:
            self._reconciliation_requested.set()
            self._next_reconciliation_at = 0.0
            self._reconciliation_wake.set()
        try:
            self.receipt_lifecycle.notify_reconnected()
        except Exception:
            self._report_error("RECEIPT_SYNC_WAKE_FAILED")
        self._wake.set()

    def stop(self, *, timeout: float = 5.0) -> bool:
        """Detiene todos los workers con un presupuesto temporal compartido."""
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout < 0
        ):
            raise ValueError("timeout debe ser un número finito no negativo")
        deadline = time.monotonic() + float(timeout)
        self._stop.set()
        self._wake.set()
        self._reconciliation_wake.set()

        def join_until(thread: threading.Thread | None) -> bool:
            if thread is None:
                return True
            if thread is threading.current_thread():
                # Un callback puede solicitar apagado desde un worker; no se hace self-join.
                return False
            thread.join(timeout=max(0.0, deadline - time.monotonic()))
            return not thread.is_alive()

        heartbeat_stopped = join_until(self._thread)
        reconciliation_stopped = join_until(self._reconciliation_thread)
        receipt_stopped = self.receipt_lifecycle.stop(
            timeout=max(0.0, deadline - time.monotonic())
        )
        return heartbeat_stopped and reconciliation_stopped and receipt_stopped

    def _report_error(self, code: str) -> None:
        try:
            self._on_error(code)
        except Exception:
            # Un callback de observabilidad defectuoso no debe detener un worker.
            pass

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.clear()
            try:
                self.runtime.send_heartbeat(self.heartbeat_payload())
            except Exception:
                self._offline = True
                self._report_error("HEARTBEAT_FAILED")
            else:
                if self._offline:
                    try:
                        self.receipt_lifecycle.notify_reconnected()
                        self._offline = False
                    except Exception:
                        self._report_error("RECEIPT_SYNC_WAKE_FAILED")
                if self.reconcile_inventory is not None and self._reconciliation_requested.is_set():
                    # El worker de reconciliación está separado; no bloquea heartbeat/capacidades.
                    self._reconciliation_wake.set()

            try:
                self.runtime.publish_capabilities(self.capabilities_payload())
            except Exception:
                self._report_error("CAPABILITIES_FAILED")

            if self._stop.is_set():
                break
            self._wake.wait(self.heartbeat_interval_seconds)

    def _run_reconciliation(self) -> None:
        while not self._stop.is_set():
            if self._reconciliation_requested.is_set():
                delay = max(0.0, self._next_reconciliation_at - time.monotonic())
                self._reconciliation_wake.wait(delay)
            else:
                self._reconciliation_wake.wait()
            if self._stop.is_set():
                break
            self._reconciliation_wake.clear()
            if not self._reconciliation_requested.is_set():
                continue
            if time.monotonic() < self._next_reconciliation_at:
                continue

            # Una notificación durante la llamada queda en el Event y dispara otro ciclo.
            self._reconciliation_requested.clear()
            try:
                inventory = self.reconcile_inventory()
                response = self.runtime.reconcile_inventory(inventory)
                if self.on_reconciliation is not None:
                    self.on_reconciliation(response)
            except Exception:
                self._reconciliation_requested.set()
                self._report_error("RECONCILIATION_FAILED")
                if not self._reconciliation_wake.is_set():
                    self._next_reconciliation_at = (
                        time.monotonic() + self.reconciliation_retry_interval_seconds
                    )
                else:
                    self._next_reconciliation_at = 0.0
            else:
                self._next_reconciliation_at = 0.0
                if self._reconciliation_requested.is_set():
                    self._reconciliation_wake.set()
