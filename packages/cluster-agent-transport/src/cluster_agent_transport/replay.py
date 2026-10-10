"""Protección persistente contra repetición de solicitudes (PostgreSQL)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import psycopg


class ReplayRejected(Exception):
    """Nonce repetido o petición fuera de la ventana temporal permitida."""


def consume_request_nonce(
    conn: psycopg.Connection,
    *,
    node_id: UUID,
    credential_id: UUID,
    nonce: UUID,
    request_id: UUID,
    timestamp: datetime,
    window: timedelta = timedelta(minutes=5),
) -> None:
    """Consume nonce en PostgreSQL; la clave única impide replay entre workers."""
    if timestamp.tzinfo is None:
        raise ReplayRejected("Timestamp sin zona horaria.")
    now = datetime.now(timezone.utc)
    if abs(now - timestamp.astimezone(timezone.utc)) > window:
        raise ReplayRejected("Timestamp fuera de la ventana permitida.")

    try:
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO geelark_control.agent_request_nonces
                    (node_id, nonce, credential_id, request_id, seen_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (node_id, nonce, credential_id, request_id, now, now + window),
            )
    except psycopg.errors.UniqueViolation as exc:
        # El único índice único relevante para esta inserción es (node_id, nonce).
        if exc.diag.constraint_name == "agent_request_nonces_pkey":
            raise ReplayRejected("Nonce ya utilizado.") from exc
        raise
