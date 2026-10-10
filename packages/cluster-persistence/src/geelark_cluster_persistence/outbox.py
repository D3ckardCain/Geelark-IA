"""Reclamación recuperable de eventos outbox; no realiza llamadas de red."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import Connection

_ERROR_CODE_RE = re.compile(r"^[A-Z0-9_]{1,64}$")


@dataclass(frozen=True, slots=True)
class ClaimedOutboxEvent:
    event_id: UUID
    deduplication_key: str
    instance_id: UUID
    assignment_epoch: int
    operation_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempt_count: int
    claim_until: datetime


def _positive_int(value: int, name: str, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ValueError(f"{name} debe ser un entero entre 1 y {maximum}")


def claim_outbox_batch(
    conn: Connection,
    worker_id: UUID,
    *,
    batch_size: int = 20,
    lease_seconds: int = 30,
) -> list[ClaimedOutboxEvent]:
    """Reclama eventos listos o con claim expirado usando SKIP LOCKED."""
    if not isinstance(worker_id, UUID):
        raise ValueError("worker_id debe ser UUID")
    _positive_int(batch_size, "batch_size", 500)
    _positive_int(lease_seconds, "lease_seconds", 300)

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH candidates AS (
                    SELECT event_id
                      FROM geelark_control.outbox_events
                     WHERE (status = 'pending' AND available_at <= now())
                        OR (status = 'inflight' AND claim_until <= now())
                     ORDER BY available_at, created_at
                     LIMIT %s
                     FOR UPDATE SKIP LOCKED
                )
                UPDATE geelark_control.outbox_events AS event
                   SET status = 'inflight',
                       claimed_by = %s,
                       claim_until = now() + (%s * interval '1 second'),
                       attempt_count = event.attempt_count + 1,
                       last_error_code = NULL
                  FROM candidates
                 WHERE event.event_id = candidates.event_id
                RETURNING event.event_id, event.deduplication_key, event.instance_id,
                          event.assignment_epoch, event.operation_id, event.event_type,
                          event.payload, event.attempt_count, event.claim_until
                """,
                (batch_size, worker_id, lease_seconds),
            )
            rows = cur.fetchall()
    return [
        ClaimedOutboxEvent(
            event_id=row[0],
            deduplication_key=row[1],
            instance_id=row[2],
            assignment_epoch=row[3],
            operation_id=row[4],
            event_type=row[5],
            payload=dict(row[6]),
            attempt_count=row[7],
            claim_until=row[8],
        )
        for row in rows
    ]


def mark_outbox_delivered(conn: Connection, event_id: UUID, worker_id: UUID) -> bool:
    """Confirma solo si el worker sigue siendo dueño de un claim vigente."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE geelark_control.outbox_events
                   SET status = 'delivered',
                       delivered_at = now(),
                       claimed_by = NULL,
                       claim_until = NULL,
                       last_error_code = NULL
                 WHERE event_id = %s
                   AND status = 'inflight'
                   AND claimed_by = %s
                   AND claim_until > now()
                """,
                (event_id, worker_id),
            )
            return cur.rowcount == 1


def retry_outbox_event(
    conn: Connection,
    event_id: UUID,
    worker_id: UUID,
    *,
    error_code: str,
    delay_seconds: int = 5,
    max_attempts: int = 8,
) -> str | None:
    """Reprograma el evento o lo marca dead; None significa claim perdido."""
    if not isinstance(worker_id, UUID) or not isinstance(event_id, UUID):
        raise ValueError("event_id y worker_id deben ser UUID")
    if not isinstance(error_code, str) or not _ERROR_CODE_RE.fullmatch(error_code):
        raise ValueError("error_code debe ser un código saneado A-Z/0-9/_ de hasta 64 caracteres")
    if not isinstance(delay_seconds, int) or isinstance(delay_seconds, bool) or not 0 <= delay_seconds <= 3600:
        raise ValueError("delay_seconds debe estar entre 0 y 3600")
    _positive_int(max_attempts, "max_attempts", 100)

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE geelark_control.outbox_events
                   SET status = CASE WHEN attempt_count >= %s THEN 'dead' ELSE 'pending' END,
                       available_at = CASE
                           WHEN attempt_count >= %s THEN available_at
                           ELSE now() + (%s * interval '1 second')
                       END,
                       claimed_by = NULL,
                       claim_until = NULL,
                       last_error_code = %s
                 WHERE event_id = %s
                   AND status = 'inflight'
                   AND claimed_by = %s
                   AND claim_until > now()
                RETURNING status
                """,
                (max_attempts, max_attempts, delay_seconds, error_code, event_id, worker_id),
            )
            row = cur.fetchone()
    return row[0] if row else None
