"""Adaptadores de dominio PostgreSQL para telemetría y consulta propia del agente.

No se implementan aquí handlers de tareas; esas operaciones permanecen sin
configurar hasta integrar y revisar la capa de operaciones/outbox.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .policy import AgentPrincipal, Operation


HEARTBEAT_STALE_AFTER = timedelta(seconds=90)


def _derive_health_state(reported_health_state: str, last_seen_at: datetime | None, *, now: datetime | None = None) -> str:
    """Deriva salud usando el reloj del controlador, nunca solo el valor del agente."""
    current_time = now or datetime.now(timezone.utc)
    if last_seen_at is None or last_seen_at <= current_time - HEARTBEAT_STALE_AFTER:
        return "offline"
    if reported_health_state in {"degraded", "unhealthy"}:
        return "degraded"
    if reported_health_state == "healthy":
        return "healthy"
    return "unknown"


def _assert_principal_current(conn: psycopg.Connection, principal: AgentPrincipal) -> None:
    row = conn.execute(
        """
        SELECT n.admin_state, c.status
          FROM geelark_control.nodes AS n
          JOIN geelark_control.node_credentials AS c ON c.node_id = n.node_id
         WHERE n.node_id = %s AND c.credential_id = %s
           AND c.expires_at > now() AND n.revoked_at IS NULL
         FOR UPDATE OF n, c
        """,
        (principal.node_id, principal.credential_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_FAILED"})
    if (row[0], row[1]) != (principal.admin_state, principal.credential_status):
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
    if (row[0], row[1]) not in {("pending", "pending"), ("active", "active")}:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})


def make_postgres_agent_handlers(connect: Callable[[], psycopg.Connection]) -> dict[Operation, Callable[..., Any]]:
    """Crea handlers mínimos de heartbeat, capacidades y estado del propio nodo."""

    def heartbeat(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        row = conn.execute(
            """
            UPDATE geelark_control.nodes
               SET agent_version = %s, reported_health_state = %s,
                   health_state = CASE
                       WHEN %s = 'healthy' THEN 'healthy'
                       WHEN %s IN ('degraded', 'unhealthy') THEN 'degraded'
                       ELSE 'unknown'
                   END,
                   last_seen_at = now(), last_sequence = last_sequence + 1,
                   updated_at = now()
             WHERE node_id = %s AND admin_state IN ('pending', 'active') AND revoked_at IS NULL
            RETURNING node_id, admin_state, reported_health_state, health_state, last_seen_at, last_sequence
            """,
            (payload["agent_version"], payload["health_state"], payload["health_state"], payload["health_state"], principal.node_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return {
            "ok": True,
            "node_id": str(row[0]),
            "admin_state": row[1],
            "reported_health_state": row[2],
            "health_state": row[3],
            "last_seen_at": row[4].astimezone(timezone.utc).isoformat(),
            "sequence": row[5],
        }

    def capabilities(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        snapshot = {"version": payload["capabilities_version"], "items": payload["capabilities"]}
        row = conn.execute(
            """
            UPDATE geelark_control.nodes
               SET capabilities = %s, updated_at = now()
             WHERE node_id = %s AND admin_state IN ('pending', 'active') AND revoked_at IS NULL
            RETURNING node_id, admin_state
            """,
            (Jsonb(snapshot), principal.node_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return {
            "ok": True,
            "node_id": str(row[0]),
            "admin_state": row[1],
            "capabilities_version": payload["capabilities_version"],
            "capability_count": len(payload["capabilities"]),
        }

    def status(*, principal: AgentPrincipal, payload: Any = None) -> dict[str, Any]:
        with connect() as conn:
            _assert_principal_current(conn, principal)
            row = conn.execute(
                """
                SELECT node_id, display_name, admin_state, reported_health_state, agent_version,
                       protocol_version, last_seen_at, last_sequence, capabilities
                  FROM geelark_control.nodes
                 WHERE node_id = %s
                """,
                (principal.node_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail={"code": "NODE_NOT_FOUND"})
            return {
                "node_id": str(row[0]),
                "display_name": row[1],
                "admin_state": row[2],
                "reported_health_state": row[3],
                "health_state": _derive_health_state(row[3], row[6]),
                "agent_version": row[4],
                "protocol_version": row[5],
                "last_seen_at": row[6].astimezone(timezone.utc).isoformat() if row[6] else None,
                "sequence": row[7],
                "capabilities": row[8],
            }

    return {
        Operation.HEARTBEAT: heartbeat,
        Operation.CAPABILITIES: capabilities,
        Operation.STATUS_READ: status,
    }
