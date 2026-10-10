"""Supervisor ligero del agente: heartbeat/capacidades separados de recibos.

No crea listeners ni reclama/ejecuta tareas. La configuración de TLS, la credencial
y el journal deben construirse externamente y entregarse al runtime por inyección.
"""
from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable
from typing import Any


class AgentSupervisor:
    """Coordina heartbeat periódico y sincronización durable sin bloquearlos entre sí.

    El heartbeat también detecta recuperación de conectividad: cuando vuelve a tener
    éxito tras un fallo, despierta el sincronizador de recibos. No implementa todavía
    almacenamiento de credenciales ni un entry point dependiente de un sistema operativo.
    """

    def __init__(
        self,
        *,
        runtime: Any,
        receipt_lifecycle: Any,
        heartbeat_payload: Callable[[], dict[str, Any]],
        capabilities_payload: Callable[[], dict[str, Any]],
        heartbeat_interval_seconds: float = 30.0,
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
        if on_error is not None and not callable(on_error):
            raise ValueError("on_error debe ser callable")

        self.runtime = runtime
        self.receipt_lifecycle = receipt_lifecycle
        self.heartbeat_payload = heartbeat_payload
        self.capabilities_payload = capabilities_payload
        self.heartbeat_interval_seconds = float(heartbeat_interval_seconds)
        self._on_error = on_error or (lambda code: None)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._offline = False

    @property
    def running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive() and not self._stop.is_set()

    def start(self) -> None:
        """Arranca el sincronizador y el ciclo periódico una sola vez."""
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("El supervisor ya fue detenido y no puede reiniciarse")
            if self._thread is not None:
                if self._thread.is_alive():
                    return
                raise RuntimeError("El supervisor ya fue detenido y no puede reiniciarse")
            self.receipt_lifecycle.start()
            self._thread = threading.Thread(
                target=self._run, name="geelark-agent-supervisor", daemon=True
            )
            try:
                self._thread.start()
            except Exception:
                self.receipt_lifecycle.stop(timeout=1)
                self._thread = None
                raise

    def notify_reconnected(self) -> None:
        """Solicita heartbeat inmediato y despierta la cola de recibos."""
        if self._stop.is_set():
            return
        try:
            self.receipt_lifecycle.notify_reconnected()
        except Exception:
            self._report_error("RECEIPT_SYNC_WAKE_FAILED")
        self._wake.set()

    def stop(self, *, timeout: float = 5.0) -> bool:
        """Detiene ambos ciclos dentro de un presupuesto temporal compartido."""
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
        thread = self._thread
        if thread is not None:
            thread.join(timeout=max(0.0, deadline - time.monotonic()))
        heartbeat_stopped = thread is None or not thread.is_alive()
        receipt_stopped = self.receipt_lifecycle.stop(
            timeout=max(0.0, deadline - __import__("time").monotonic())
        )
        return heartbeat_stopped and receipt_stopped

    def _report_error(self, code: str) -> None:
        try:
            self._on_error(code)
        except Exception:
            # Un callback de observabilidad defectuoso no debe detener el supervisor.
            pass

    def _run(self) -> None:
        while not self._stop.is_set():
            # Limpiar antes de trabajar: una notificación durante el ciclo queda pendiente
            # y hace que la espera siguiente termine inmediatamente.
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

            try:
                self.runtime.publish_capabilities(self.capabilities_payload())
            except Exception:
                self._report_error("CAPABILITIES_FAILED")

            if self._stop.is_set():
                break
            self._wake.wait(self.heartbeat_interval_seconds)
