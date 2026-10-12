"""Idempotencia transaccional para escrituras de agentes.

La función execute debe realizar su operación de dominio usando la misma
conexión recibida. El resultado y la mutación quedan en una sola transacción.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


# Garantía de replay por tipo de operación. Scopes desconocidos quedan sin expiración.
_IDEMPOTENCY_TTL_SECONDS = {
    "heartbeat": 24 * 60 * 60,
    "capabilities": 24 * 60 * 60,
    "modules_report": 24 * 60 * 60,
    "status_read": 24 * 60 * 60,
    "task_fetch": 90 * 24 * 60 * 60,
    "task_accept": 90 * 24 * 60 * 60,
    "task_progress": 90 * 24 * 60 * 60,
    "task_result": 90 * 24 * 60 * 60,
    "reconcile": 90 * 24 * 60 * 60,
    "reconcile_inventory": 90 * 24 * 60 * 60,
}


def _idempotency_ttl_seconds(scope: str) -> int | None:
    if not scope.startswith("agent:"):
        return None
    operation = scope.rsplit(":", 1)[-1]
    return _IDEMPOTENCY_TTL_SECONDS.get(operation)


class IdempotencyConflict(Exception):
    """La clave ya existe asociada a otro payload."""


class IdempotencyInProgress(Exception):
    """Hay una clave reservada sin resultado confirmado; no repetir la acción."""


def payload_digest(payload: Any) -> str:
    try:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("El payload debe ser JSON finito y serializable.") from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def execute_idempotent(
    conn: psycopg.Connection,
    *,
    scope: str,
    key: str,
    payload: Any,
    execute: Callable[[psycopg.Connection], dict[str, Any]],
) -> dict[str, Any]:
    """Ejecuta una vez y conserva el snapshot de respuesta junto a la mutación."""
    if not isinstance(scope, str) or not scope.strip() or len(scope) > 128:
        raise ValueError("scope debe tener entre 1 y 128 caracteres.")
    if not isinstance(key, str) or not 16 <= len(key) <= 200 or not re.fullmatch(r"[A-Za-z0-9._:-]+", key):
        raise ValueError("Idempotency-Key debe tener 16-200 caracteres seguros.")
    digest = payload_digest(payload)

    with conn.transaction():
        inserted = conn.execute(
            """
            INSERT INTO geelark_control.idempotency_records
                (scope, idempotency_key, payload_sha256, response_snapshot, expires_at)
            VALUES (%s, %s, %s, NULL, now() + (%s * interval '1 second'))
            ON CONFLICT (scope, idempotency_key) DO NOTHING
            RETURNING scope
            """,
            (scope, key, digest, _idempotency_ttl_seconds(scope)),
        ).fetchone()
        row = conn.execute(
            """
            SELECT payload_sha256, response_snapshot
              FROM geelark_control.idempotency_records
             WHERE scope = %s AND idempotency_key = %s
             FOR UPDATE
            """,
            (scope, key),
        ).fetchone()
        if row is None:
            raise RuntimeError("No se pudo recuperar el registro idempotente.")
        stored_digest, response = row
        if stored_digest.strip() != digest:
            raise IdempotencyConflict("La clave ya se usó con otro payload.")
        if inserted is None:
            if response is None:
                raise IdempotencyInProgress("La clave existe sin resultado confirmado.")
            if not isinstance(response, dict):
                raise RuntimeError("Snapshot idempotente inválido.")
            return response

        result = execute(conn)
        if not isinstance(result, dict):
            raise ValueError("La operación idempotente debe devolver un objeto JSON.")
        conn.execute(
            """
            UPDATE geelark_control.idempotency_records
               SET response_snapshot = %s
             WHERE scope = %s AND idempotency_key = %s
            """,
            (Jsonb(result), scope, key),
        )
        return result


def make_database_idempotency_runner(connect: Callable[[], psycopg.Connection]):
    """Adaptador para inyectar en create_agent_app."""
    def run(*, principal: Any, operation: str, key: str, payload: Any, execute: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        scope = f"agent:{principal.node_id}:{operation}"
        with connect() as conn:
            return execute_idempotent(
                conn, scope=scope, key=key, payload=payload,
                execute=lambda transaction_conn: execute(transaction_conn),
            )
    return run
