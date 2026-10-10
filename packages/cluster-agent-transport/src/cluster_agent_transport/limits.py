"""Límites defensivos locales para solicitudes HTTP del agente."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque


class InMemoryRateLimiter:
    """Límite por proceso; PostgreSQL nonce evita replay entre workers.

    Para despliegues multiworker, este límite es una defensa adicional, no
    un límite global. No requiere Redis ni servicios externos.
    """

    def __init__(self, *, max_requests: int = 60, window_seconds: int = 60) -> None:
        if max_requests < 1 or window_seconds < 1:
            raise ValueError("Los límites deben ser positivos.")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, *, now: float | None = None) -> bool:
        instant = time.monotonic() if now is None else now
        with self._lock:
            events = self._events[key]
            cutoff = instant - self.window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_requests:
                return False
            events.append(instant)
            return True
