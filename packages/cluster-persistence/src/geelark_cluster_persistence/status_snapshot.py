"""Proveedor interno de snapshots de solo lectura para PC-MASTER.

No expone HTTP ni crea listeners. El consumidor administrativo debe autenticar
al operador antes de invocar este puerto y usar una conexión PostgreSQL de solo
lectura. Este adaptador solo ejecuta SELECT.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

import psycopg

from .module_registry import SUPPORTED_MODULE_IDS, MODULE_REPORT_STALE_AFTER

HEARTBEAT_STALE_AFTER = timedelta(seconds=90)
CLOCK_SKEW_TOLERANCE = timedelta(seconds=5)
DISPLAY_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MODULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ERROR_CODE_RE = re.compile(r"^[A-Z0-9_]{1,64}$")
HEALTH_REPORTS = frozenset({"healthy", "degraded", "unhealthy", "unknown"})
MODULE_STATES = frozenset({"operational", "degraded", "not-installed", "unknown"})
MODULE_SOURCES = frozenset({"agent-report", "master-check", "unknown"})
CAPABILITY_ALIASES = {
    "heartbeat": "heartbeat-v1",
    "heartbeat-v1": "heartbeat-v1",
    "status": "self-status-v1",
    "self-status-v1": "self-status-v1",
    "capability_report": "capability-report-v1",
    "capability-report-v1": "capability-report-v1",
    "module_inventory": "module-inventory-v1",
    "module-inventory-v1": "module-inventory-v1",
    "resource_telemetry": "resource-telemetry-v1",
    "resource-telemetry-v1": "resource-telemetry-v1",
}


class StatusSnapshotProvider(Protocol):
    """Puerto interno; la capa HTTP/admin, si existe, autentica antes de usarlo."""

    def get_node_snapshot(self, node_id: UUID) -> dict[str, Any] | None:
        """Devuelve un snapshot v1 del nodo o None si no existe."""


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_utc(value: Any) -> datetime | None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


def _authorization_state(admin_state: Any, revoked_at: Any) -> str:
    if revoked_at is not None or admin_state == "revoked":
        return "revoked"
    if admin_state in {"pending", "active"}:
        return admin_state
    # draining/maintenance/quarantined are intentionally not collapsed to active.
    return "unknown"


def _health_state(reported: str | None, freshness: str) -> str:
    if freshness == "missing":
        return "offline"
    if freshness in {"stale", "unknown"}:
        return "offline" if freshness == "stale" else "unknown"
    if reported in {"degraded", "unhealthy"}:
        return "degraded"
    if reported == "healthy":
        return "healthy"
    return "unknown"


def _freshness(last_seen_at: datetime | None, now: datetime) -> tuple[dict[str, Any], str]:
    if last_seen_at is None:
        return ({
            "state": "missing",
            "age_seconds": None,
            "threshold_seconds": int(HEARTBEAT_STALE_AFTER.total_seconds()),
            "observed_at": None,
        }, "missing")
    delta = now - last_seen_at
    if delta < -CLOCK_SKEW_TOLERANCE:
        return ({
            "state": "unknown",
            "age_seconds": None,
            "threshold_seconds": int(HEARTBEAT_STALE_AFTER.total_seconds()),
            "observed_at": _iso_utc(last_seen_at),
        }, "unknown")
    age = max(0, delta.total_seconds())
    age_seconds = int(age)
    state = "stale" if age >= HEARTBEAT_STALE_AFTER.total_seconds() else "fresh"
    return ({
        "state": state,
        "age_seconds": age_seconds,
        "threshold_seconds": int(HEARTBEAT_STALE_AFTER.total_seconds()),
        "observed_at": _iso_utc(last_seen_at),
    }, state)


def _safe_capabilities(value: Any) -> list[str]:
    raw = value.get("items", []) if isinstance(value, dict) else []
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        normalized = CAPABILITY_ALIASES.get(item)
        if normalized and normalized not in result:
            result.append(normalized)
        if len(result) >= 32:
            break
    return result


def _safe_modules(value: Any, *, now: datetime, freshness_state: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in value[:128]:
        if not isinstance(raw, dict):
            continue
        module_id = raw.get("module_id")
        if not isinstance(module_id, str) or not MODULE_ID_RE.fullmatch(module_id):
            continue
        if module_id in seen:
            continue
        seen.add(module_id)
        raw_state = raw.get("state")
        state = raw_state if raw_state in MODULE_STATES else "unknown"
        version = raw.get("version")
        if not isinstance(version, str) or not version.strip() or len(version) > 64:
            version = None
        try:
            parsed_checked_at = datetime.fromisoformat(raw["checked_at"].replace("Z", "+00:00")) if isinstance(raw.get("checked_at"), str) else None
        except (ValueError, TypeError):
            parsed_checked_at = None
        checked_at = _as_utc(parsed_checked_at)
        source = raw.get("source")
        if not isinstance(source, str) or source not in MODULE_SOURCES:
            source = "unknown"
        error_code = raw.get("error_code")
        if not isinstance(error_code, str) or not ERROR_CODE_RE.fullmatch(error_code):
            error_code = None

        if freshness_state in {"missing", "stale"}:
            state, source, error_code = "unknown", "master-check", "NODE_STALE"
        elif checked_at is None:
            state, source, error_code = "unknown", "master-check", "REPORT_MISSING"
        elif checked_at - now > CLOCK_SKEW_TOLERANCE:
            state, source, error_code = "unknown", "master-check", "REPORT_TIME_SKEW"
            checked_at = None
        elif now - checked_at >= MODULE_REPORT_STALE_AFTER:
            state, source, error_code = "unknown", "master-check", "REPORT_STALE"
        elif not isinstance(raw_state, str) or raw_state not in MODULE_STATES or module_id not in SUPPORTED_MODULE_IDS:
            state, source, error_code = "unknown", "master-check", "INVALID_MODULE_REPORT"

        result.append({
            "module_id": module_id,
            "state": state,
            "version": version,
            "checked_at": _iso_utc(checked_at) if checked_at else None,
            "source": source,
            "error_code": error_code,
        })
    return result


def build_status_snapshot(row: Sequence[Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Convierte una fila SQL en el contrato de snapshot v1, fallando conservador."""
    if len(row) != 9:
        raise ValueError("La fila del snapshot debe contener exactamente nueve columnas")
    current = _as_utc(now or datetime.now(timezone.utc))
    if current is None:
        raise ValueError("now debe incluir zona horaria")
    node_id, display_name, admin_state, reported_health, agent_version, last_seen, capabilities, modules, revoked_at = row
    node_uuid = UUID(str(node_id))
    last_seen_at = _as_utc(last_seen)
    freshness, freshness_state = _freshness(last_seen_at, current)
    reported = reported_health if reported_health in HEALTH_REPORTS else "unknown"
    safe_name = display_name if isinstance(display_name, str) and DISPLAY_NAME_RE.fullmatch(display_name) else f"WORKER-{str(node_uuid).split('-')[0].upper()}"
    if not isinstance(agent_version, str) or len(agent_version) > 64:
        agent_version = None

    return {
        "schema_version": "1.0",
        "snapshot_id": str(uuid4()),
        "generated_at": _iso_utc(current),
        "source": "master-live",
        "node": {
            "node_id": str(node_uuid),
            "display_name": safe_name,
            "authorization_state": _authorization_state(admin_state, revoked_at),
            "health_state": _health_state(reported, freshness_state),
            "last_heartbeat_at": _iso_utc(last_seen_at) if last_seen_at else None,
            "agent_version": agent_version,
            "capabilities": _safe_capabilities(capabilities),
            "modules": _safe_modules(modules, now=current, freshness_state=freshness_state),
            "reported_health_state": reported,
        },
        "freshness": freshness,
    }


class PostgresStatusSnapshotProvider:
    """Adaptador de lectura para la fuente autoritativa PostgreSQL del Master."""

    def __init__(self, connect: Callable[[], psycopg.Connection]) -> None:
        self._connect = connect

    def get_node_snapshot(self, node_id: UUID) -> dict[str, Any] | None:
        if not isinstance(node_id, UUID):
            raise TypeError("node_id debe ser UUID")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT node_id, display_name, admin_state, reported_health_state,
                       agent_version, last_seen_at, capabilities, module_reports, revoked_at
                  FROM geelark_control.nodes
                 WHERE node_id = %s
                """,
                (node_id,),
            ).fetchone()
        return build_status_snapshot(row) if row is not None else None
