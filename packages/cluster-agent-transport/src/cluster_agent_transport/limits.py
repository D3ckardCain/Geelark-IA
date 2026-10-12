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
        if (
            isinstance(max_requests, bool)
            or not isinstance(max_requests, int)
            or isinstance(window_seconds, bool)
            or not isinstance(window_seconds, int)
            or max_requests < 1
            or window_seconds < 1
        ):
            raise ValueError("Los límites deben ser enteros positivos.")
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



class PostgresRateLimiter:
    """Rate limit global por nodo mediante UPDATE atómico de la fila nodes.

    A diferencia del limitador en memoria, funciona entre workers/procesos.
    El contador se satura en max_requests + 1 y se reinicia al vencer la ventana.
    """

    def __init__(self, connect, *, max_requests: int = 60, window_seconds: int = 60) -> None:
        if (
            isinstance(max_requests, bool)
            or not isinstance(max_requests, int)
            or isinstance(window_seconds, bool)
            or not isinstance(window_seconds, int)
            or max_requests < 1
            or window_seconds < 1
        ):
            raise ValueError("Los límites deben ser enteros positivos.")
        self.connect = connect
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        from uuid import UUID

        try:
            node_id = UUID(key)
        except (TypeError, ValueError):
            return False
        with self.connect() as conn:
            row = conn.execute(
                """
                UPDATE geelark_control.nodes
                   SET agent_rate_window_count = CASE
                         WHEN agent_rate_window_started_at IS NULL
                           OR agent_rate_window_started_at <= now() - (%s * interval '1 second')
                         THEN 1
                         ELSE LEAST(agent_rate_window_count + 1, %s + 1)
                       END,
                       agent_rate_window_started_at = CASE
                         WHEN agent_rate_window_started_at IS NULL
                           OR agent_rate_window_started_at <= now() - (%s * interval '1 second')
                         THEN now()
                         ELSE agent_rate_window_started_at
                       END
                 WHERE node_id = %s
                   AND admin_state IN ('pending', 'active')
                   AND revoked_at IS NULL
                RETURNING agent_rate_window_count
                """,
                (self.window_seconds, self.max_requests, self.window_seconds, node_id),
            ).fetchone()
        return row is not None and row[0] <= self.max_requests
