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
from .module_registry import MODULE_REPORT_STALE_AFTER


HEARTBEAT_STALE_AFTER = timedelta(seconds=90)


def _derive_module_reports(reports: list[dict[str, Any]], last_seen_at: datetime | None, *, now: datetime | None = None) -> list[dict[str, Any]]:
    """Los módulos pasan a unknown si el nodo o el propio reporte está obsoleto."""
    current_time = now or datetime.now(timezone.utc)
    node_stale = last_seen_at is None or last_seen_at <= current_time - HEARTBEAT_STALE_AFTER
    result: list[dict[str, Any]] = []
    for item in reports if isinstance(reports, list) else []:
        report = dict(item) if isinstance(item, dict) else {}
        raw_checked_at = report.get("checked_at")
        try:
            checked_at = datetime.fromisoformat(raw_checked_at.replace("Z", "+00:00")) if isinstance(raw_checked_at, str) else None
            if checked_at is not None and checked_at.tzinfo is None:
                checked_at = checked_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            checked_at = None
        report_stale = checked_at is None or checked_at <= current_time - MODULE_REPORT_STALE_AFTER
        if node_stale or report_stale:
            report["state"] = "unknown"
            report["source"] = "master-check"
            report["error_code"] = "NODE_STALE" if node_stale else "REPORT_STALE"
        result.append(report)
    return result


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

    def modules(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste inventario; el UPDATE solo permite nodos active."""
        _assert_principal_current(conn, principal)
        received_at = datetime.now(timezone.utc)
        normalized = [
            {"module_id": item["module_id"], "state": item["state"], "version": item.get("version"),
             "checked_at": received_at.isoformat(), "source": "agent-report", "error_code": item.get("error_code")}
            for item in payload["modules"]
        ]
        row = conn.execute(
            """
            UPDATE geelark_control.nodes
               SET module_reports = %s, updated_at = now()
             WHERE node_id = %s AND admin_state = 'active' AND revoked_at IS NULL
            RETURNING node_id, admin_state
            """,
            (Jsonb(normalized), principal.node_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return {"ok": True, "node_id": str(row[0]), "admin_state": row[1],
                "module_count": len(normalized), "received_at": received_at.isoformat()}

    def status(*, principal: AgentPrincipal, payload: Any = None) -> dict[str, Any]:
        with connect() as conn:
            _assert_principal_current(conn, principal)
            row = conn.execute(
                """
                SELECT node_id, display_name, admin_state, reported_health_state, agent_version,
                       protocol_version, last_seen_at, last_sequence, capabilities, module_reports
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
                "modules": _derive_module_reports(row[9], row[6]),
            }

    return {
        Operation.HEARTBEAT: heartbeat,
        Operation.CAPABILITIES: capabilities,
        Operation.MODULES_REPORT: modules,
        Operation.STATUS_READ: status,
    }
