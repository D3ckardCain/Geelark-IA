"""Ciclo de vida para sincronizar recibos locales sin bloquear el agente.

Este coordinador solo transmite recibos ya persistidos en el journal. No reclama ni
ejecuta tareas, no abre listeners y no guarda credenciales. La sincronización corre
en un hilo separado para que un fallo de red no bloquee el heartbeat del agente.
"""
from __future__ import annotations

import random
import threading
from collections.abc import Callable
from typing import Any


class AgentReceiptSyncLifecycle:
    """Sincroniza recibos al iniciar y al reconectar, con reintentos acotados.

    El propietario del agente llama a start() una vez, a notify_reconnected() cuando
    detecta conectividad restaurada y a stop() durante el apagado ordenado. Un lote
    se limita mediante batch_size. El cliente HTTPS debe tener sus propios timeouts.
    """

    def __init__(
        self,
        *,
        runtime: Any,
        batch_size: int = 100,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 60.0,
        wait: Callable[[threading.Event, float], bool] | None = None,
        random_value: Callable[[], float] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 1 <= batch_size <= 1000:
            raise ValueError("batch_size debe ser un entero entre 1 y 1000")
        if initial_backoff_seconds <= 0 or max_backoff_seconds < initial_backoff_seconds:
            raise ValueError("El backoff máximo debe ser >= al inicial y ambos positivos")
        if not callable(getattr(runtime, "sync_pending_receipts", None)):
            raise ValueError("runtime debe implementar sync_pending_receipts(limit=...)")
        self.runtime = runtime
        self.batch_size = batch_size
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self._wait = wait or (lambda event, seconds: event.wait(seconds))
        self._random_value = random_value or random.random
        self._on_error = on_error or (lambda code: None)
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive() and not self._stop.is_set()

    def start(self) -> None:
        """Arranca una sola vez y solicita sincronización inmediata."""
        with self._lock:
            if self._thread is not None:
                if self._thread.is_alive():
                    return
                raise RuntimeError("El ciclo de vida ya fue detenido y no puede reiniciarse")
            self._thread = threading.Thread(
                target=self._run, name="geelark-receipt-sync", daemon=True
            )
            self._thread.start()
            self._wake.set()

    def notify_reconnected(self) -> None:
        """Despierta al sincronizador después de recuperar conectividad."""
        if not self._stop.is_set():
            self._wake.set()

    def stop(self, *, timeout: float = 5.0) -> bool:
        """Solicita cancelación y espera el hilo hasta timeout; devuelve si terminó."""
        if timeout < 0:
            raise ValueError("timeout no puede ser negativo")
        self._stop.set()
        self._wake.set()
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

    def _run(self) -> None:
        self._wake.wait()
        backoff = self.initial_backoff_seconds
        while not self._stop.is_set():
            self._wake.clear()
            try:
                confirmed, attempted = self.runtime.sync_pending_receipts(limit=self.batch_size)
                if confirmed < 0 or attempted < confirmed or confirmed > self.batch_size or attempted > self.batch_size:
                    raise ValueError("El runtime devolvió contadores de sincronización inválidos")
            except Exception:
                # No registrar excepciones ni cuerpos HTTP: podrían contener datos sensibles.
                self._on_error("RECEIPT_SYNC_FAILED")
                confirmed, attempted = 0, 1

            if self._stop.is_set():
                break
            if attempted > confirmed:
                # Jitter multiplicativo acotado: evita que muchos nodos reintenten juntos.
                factor = 0.5 + min(max(float(self._random_value()), 0.0), 1.0)
                delay = min(self.max_backoff_seconds, backoff * factor)
                self._wait(self._wake, delay)
                backoff = min(self.max_backoff_seconds, backoff * 2)
                # Si notify_reconnected() despertó antes, reintenta inmediatamente.
                continue
            backoff = self.initial_backoff_seconds
            if attempted == self.batch_size and confirmed == attempted:
                # El lote estaba lleno: drenar el siguiente lote sin esperar reconexión.
                continue
            # Cola vacía o drenada: no sondear la red repetidamente; esperar reconexión.
            self._wake.wait()
