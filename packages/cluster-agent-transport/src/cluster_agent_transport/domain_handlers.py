"""Adaptadores PostgreSQL para telemetría, inventario y bandeja durable del agente.

Las operaciones de tareas validan propiedad, epoch y leases bajo bloqueo de filas;
la reconciliación se mantiene de solo lectura y no resuelve estados inciertos.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any
from uuid import UUID, uuid4

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .policy import AgentPrincipal, Operation
from .module_registry import MODULE_REPORT_STALE_AFTER, SUPPORTED_MODULE_IDS


HEARTBEAT_STALE_AFTER = timedelta(seconds=90)


def _validate_result_summary(value: Any) -> dict[str, Any]:
    """Exige JSON compacto y rechaza campos que puedan contener secretos."""
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail={"code": "INVALID_RESULT_SUMMARY"})
    forbidden = ("token", "password", "secret", "authorization", "cookie", "credential", "apikey", "privatekey", "accesskey")

    def inspect(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if not isinstance(key, str):
                    raise HTTPException(status_code=422, detail={"code": "INVALID_RESULT_SUMMARY"})
                # Normalizar snake_case, kebab-case y camelCase por igual.
                normalized = "".join(character for character in key.casefold() if character.isalnum())
                if any(term in normalized for term in forbidden):
                    raise HTTPException(status_code=422, detail={"code": "SENSITIVE_RESULT_FIELD"})
                inspect(nested)
        elif isinstance(item, list):
            for nested in item:
                inspect(nested)

    inspect(value)
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail={"code": "INVALID_RESULT_SUMMARY"}) from None
    if len(encoded) > 1_000_000:
        raise HTTPException(status_code=413, detail={"code": "RESULT_SUMMARY_TOO_LARGE"})
    return value


def _derive_module_reports(reports: list[dict[str, Any]], last_seen_at: datetime | None, *, now: datetime | None = None) -> list[dict[str, Any]]:
    """Sanea filas persistidas y degrada a unknown datos obsoletos o incoherentes."""
    current_time = now or datetime.now(timezone.utc)
    node_stale = last_seen_at is None or last_seen_at <= current_time - HEARTBEAT_STALE_AFTER
    allowed_states = {"operational", "degraded", "not-installed", "unknown"}
    error_code_pattern = re.compile(r"^[A-Z0-9_]{1,64}$")
    result: list[dict[str, Any]] = []
    source_reports = reports[:32] if isinstance(reports, list) else []

    for item in source_reports:
        if not isinstance(item, dict):
            continue
        module_id = item.get("module_id")
        # No se reenvían identificadores arbitrarios desde una fila persistida.
        if not isinstance(module_id, str) or module_id not in SUPPORTED_MODULE_IDS:
            continue

        raw_checked_at = item.get("checked_at")
        try:
            checked_at = (
                datetime.fromisoformat(raw_checked_at.replace("Z", "+00:00"))
                if isinstance(raw_checked_at, str) else None
            )
            if checked_at is not None and (checked_at.tzinfo is None or checked_at.utcoffset() is None):
                checked_at = None
            elif checked_at is not None:
                checked_at = checked_at.astimezone(timezone.utc)
        except (ValueError, TypeError):
            checked_at = None

        state = item.get("state")
        source = item.get("source")
        error_code = item.get("error_code")
        version = item.get("version")
        if not isinstance(version, str) or not version.strip() or len(version) > 64:
            version = None
        if not isinstance(error_code, str) or not error_code_pattern.fullmatch(error_code):
            error_code = None

        if node_stale:
            state, source, error_code = "unknown", "master-check", "NODE_STALE"
        elif checked_at is None:
            state, source, error_code = "unknown", "master-check", "REPORT_MISSING"
        elif checked_at > current_time + timedelta(seconds=5):
            state, source, error_code = "unknown", "master-check", "REPORT_TIME_SKEW"
            checked_at = None
        elif current_time - checked_at >= MODULE_REPORT_STALE_AFTER:
            state, source, error_code = "unknown", "master-check", "REPORT_STALE"
        elif (not isinstance(state, str) or state not in allowed_states
              or not isinstance(source, str) or source != "agent-report"):
            state, source, error_code = "unknown", "master-check", "INVALID_MODULE_REPORT"

        result.append({
            "module_id": module_id,
            "state": state if isinstance(state, str) and state in allowed_states else "unknown",
            "version": version,
            "checked_at": checked_at.isoformat().replace("+00:00", "Z") if checked_at else None,
            "source": source if isinstance(source, str) and source in {"agent-report", "master-check", "unknown"} else "unknown",
            "error_code": error_code,
        })
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

    def _locked_task(conn: psycopg.Connection, principal: AgentPrincipal, task_id: UUID):
        row = conn.execute(
            """
            SELECT t.status, t.node_id, t.instance_id, t.assignment_epoch,
                   t.result_summary, i.owner_node_id, i.assignment_epoch,
                   i.lease_expires_at, o.status, t.delivery_lease_until
              FROM geelark_control.agent_tasks AS t
              JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
              JOIN geelark_control.operations AS o ON o.operation_id = t.operation_id
             WHERE t.task_id = %s
             FOR UPDATE OF t, i, o
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "TASK_NOT_FOUND"})
        if str(row[1]) != principal.node_id:
            raise HTTPException(status_code=403, detail={"code": "TASK_NOT_OWNED_BY_NODE"})
        if (
            row[5] is None or str(row[5]) != principal.node_id
            or row[6] != row[3] or row[7] is None or row[7] <= datetime.now(timezone.utc)
            or (
                row[0] in {"delivered", "accepted", "running"}
                and (row[9] is None or row[9] <= datetime.now(timezone.utc))
            )
        ):
            raise HTTPException(status_code=409, detail={"code": "STALE_ASSIGNMENT"})
        return row

    def claim_task(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        if (principal.admin_state, principal.credential_status) != ("active", "active"):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        row = conn.execute(
            """
            SELECT t.task_id, t.operation_id, t.instance_id, t.assignment_epoch,
                   t.payload, t.delivery_attempts, i.lease_expires_at
              FROM geelark_control.agent_tasks AS t
              JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
              JOIN geelark_control.operations AS o ON o.operation_id = t.operation_id
              JOIN geelark_control.nodes AS n ON n.node_id = t.node_id
             WHERE t.node_id = %s
               AND n.admin_state = 'active' AND n.health_state = 'healthy' AND n.revoked_at IS NULL
               AND t.status IN ('queued', 'delivered')
               AND (t.status = 'queued' OR t.delivery_lease_until IS NULL
                    OR t.delivery_lease_until <= now())
               AND o.operation_type = 'assign' AND o.status = 'accepted'
               AND i.owner_node_id = t.node_id
               AND i.assignment_epoch = t.assignment_epoch
               AND i.lease_expires_at > now()
             ORDER BY t.created_at, t.task_id
             LIMIT 1
             FOR UPDATE OF t, i, o SKIP LOCKED
            """,
            (principal.node_id,),
        ).fetchone()
        if row is None:
            return {"task": None}
        task_id, operation_id, instance_id, epoch, task_payload, attempts, instance_lease_expires_at = row
        delivery_lease_expires_at = conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = 'delivered',
                   delivery_attempts = delivery_attempts + 1,
                   delivery_lease_until = now() + interval '30 seconds',
                   delivered_at = COALESCE(delivered_at, now()),
                   updated_at = now()
             WHERE task_id = %s
             RETURNING delivery_lease_until
            """,
            (task_id,),
        ).fetchone()[0]
        body = dict(task_payload)
        body.update({
            "task_id": str(task_id),
            "operation_id": str(operation_id),
            "instance_id": str(instance_id),
            "node_id": principal.node_id,
            "assignment_epoch": epoch,
            "lease_expires_at": delivery_lease_expires_at.astimezone(timezone.utc).isoformat(),
            "instance_lease_expires_at": instance_lease_expires_at.astimezone(timezone.utc).isoformat(),
            "delivery_attempt": attempts + 1,
        })
        return {"task": body}

    def accept_task(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        if payload.get("state") != "accepted":
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_STATE"})
        try:
            task_id = UUID(payload["task_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_ID"}) from None
        row = _locked_task(conn, principal, task_id)
        status = row[0]
        if status == "accepted":
            return {"ok": True, "task_id": str(task_id), "state": "accepted", "duplicate": True}
        if status != "delivered":
            raise HTTPException(status_code=409, detail={"code": "TASK_STATE_CONFLICT"})
        conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = 'accepted', accepted_at = COALESCE(accepted_at, now()),
                   updated_at = now()
             WHERE task_id = %s
            """,
            (task_id,),
        )
        return {"ok": True, "task_id": str(task_id), "state": "accepted", "duplicate": False}

    def progress_task(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        if payload.get("state") not in {"running", "unknown"}:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_STATE"})
        try:
            task_id = UUID(payload["task_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_ID"}) from None
        row = _locked_task(conn, principal, task_id)
        if row[0] not in {"accepted", "running"}:
            raise HTTPException(status_code=409, detail={"code": "TASK_STATE_CONFLICT"})
        state = payload["state"]
        details = _validate_result_summary(payload.get("details", {}))
        conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = %s, result_summary = %s, updated_at = now()
             WHERE task_id = %s
            """,
            (state, Jsonb(details), task_id),
        )
        conn.execute(
            """
            UPDATE geelark_control.operations
               SET status = %s, result_summary = %s, updated_at = now()
             WHERE operation_id = (SELECT operation_id FROM geelark_control.agent_tasks WHERE task_id = %s)
            """,
            (state, Jsonb(details), task_id),
        )
        return {"ok": True, "task_id": str(task_id), "state": state}

    def result_task(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        _assert_principal_current(conn, principal)
        state = payload.get("state")
        if state not in {"succeeded", "rejected", "failed", "unknown"}:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_STATE"})
        try:
            task_id = UUID(payload["task_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_ID"}) from None
        row = _locked_task(conn, principal, task_id)
        old_status, old_summary = row[0], dict(row[4] or {})
        details = _validate_result_summary(payload.get("details", {}))
        if old_status in {"succeeded", "rejected", "failed", "unknown"}:
            if old_status == state and old_summary == details:
                return {"ok": True, "task_id": str(task_id), "state": state, "duplicate": True}
            raise HTTPException(status_code=409, detail={"code": "TASK_TERMINAL_CONFLICT"})
        if old_status not in {"accepted", "running"}:
            raise HTTPException(status_code=409, detail={"code": "TASK_STATE_CONFLICT"})
        terminal = state in {"succeeded", "rejected", "failed"}
        conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = %s, result_summary = %s,
                   completed_at = CASE WHEN %s THEN now() ELSE NULL END,
                   updated_at = now()
             WHERE task_id = %s
            """,
            (state, Jsonb(details), terminal, task_id),
        )
        conn.execute(
            """
            UPDATE geelark_control.operations
               SET status = %s, result_summary = %s,
                   completed_at = CASE WHEN %s THEN now() ELSE NULL END,
                   updated_at = now()
             WHERE operation_id = (SELECT operation_id FROM geelark_control.agent_tasks WHERE task_id = %s)
            """,
            (state, Jsonb(details), terminal, task_id),
        )
        return {"ok": True, "task_id": str(task_id), "state": state, "duplicate": False}

    def reconcile(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        """Compara el inventario informado con la autoridad central sin mutar estados."""
        _assert_principal_current(conn, principal)
        items = payload.get("assignments", [])
        if not isinstance(items, list) or len(items) > 500:
            raise HTTPException(status_code=422, detail={"code": "INVALID_RECONCILIATION_BATCH"})
        comparisons = []
        now = datetime.now(timezone.utc)
        for item in items:
            try:
                task_id = UUID(item["task_id"])
                operation_id = UUID(item["operation_id"])
                instance_id = UUID(item["instance_id"])
                epoch = item["assignment_epoch"]
                observed_state = item["observed_state"]
                observed_summary = item.get("result_summary", {})
            except (KeyError, TypeError, ValueError):
                raise HTTPException(status_code=422, detail={"code": "INVALID_RECONCILIATION_ITEM"}) from None
            if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 1:
                raise HTTPException(status_code=422, detail={"code": "INVALID_ASSIGNMENT_EPOCH"})
            observed_summary = _validate_result_summary(observed_summary)
            row = conn.execute(
                """
                SELECT t.status, t.result_summary, t.node_id, t.instance_id,
                       t.operation_id, t.assignment_epoch,
                       i.owner_node_id, i.assignment_epoch, i.lease_expires_at,
                       o.status
                  FROM geelark_control.agent_tasks AS t
                  JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
                  JOIN geelark_control.operations AS o ON o.operation_id = t.operation_id
                 WHERE t.task_id = %s AND t.node_id = %s
                   AND t.operation_id = %s AND t.instance_id = %s
                   AND t.assignment_epoch = %s
                """,
                (task_id, principal.node_id, operation_id, instance_id, epoch),
            ).fetchone()
            if row is None:
                comparisons.append({
                    "task_id": str(task_id),
                    "status": "not_found_or_not_owned",
                    "action": "do_not_execute",
                })
                continue
            server_state, server_summary = row[0], dict(row[1] or {})
            owner_node, current_epoch, lease_expires_at = row[6], row[7], row[8]
            if (
                owner_node is None or str(owner_node) != principal.node_id
                or current_epoch != epoch or lease_expires_at is None or lease_expires_at <= now
            ):
                comparisons.append({
                    "task_id": str(task_id),
                    "status": "stale_assignment",
                    "server_state": server_state,
                    "observed_state": observed_state,
                    "action": "operator_review_required",
                })
                continue
            if server_state in {"succeeded", "rejected", "failed"}:
                if server_state == observed_state and server_summary == observed_summary:
                    result_state = "in_sync"
                else:
                    result_state = "terminal_conflict"
            elif server_state == observed_state and server_summary == observed_summary:
                result_state = "in_sync"
            elif server_state == "unknown" or observed_state == "unknown":
                result_state = "uncertain_review_required"
            else:
                result_state = "review_required"
            comparisons.append({
                "task_id": str(task_id),
                "status": result_state,
                "server_state": server_state,
                "observed_state": observed_state,
                "action": "none" if result_state == "in_sync" else "operator_review_required",
            })
        return {
            "schema_version": 1,
            "read_only": True,
            "mutations_applied": 0,
            "items": comparisons,
        }

    def reconcile_inventory(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: dict[str, Any]) -> dict[str, Any]:
        """Compara inventario y epochs sin convertir estados inciertos automáticamente."""
        _assert_principal_current(conn, principal)
        if (principal.admin_state, principal.credential_status) != ("active", "active"):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        inventory = payload.get("inventory")
        if payload.get("schema_version") != 1 or not isinstance(inventory, list) or len(inventory) > 100:
            raise HTTPException(status_code=422, detail={"code": "INVALID_RECONCILIATION_PAYLOAD"})

        try:
            canonical_inventory = json.dumps(
                inventory, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            )
            inventory_hash = hashlib.sha256(canonical_inventory.encode("utf-8")).hexdigest()
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail={"code": "INVALID_RECONCILIATION_PAYLOAD"}) from None

        decisions: list[dict[str, Any]] = []
        seen_task_ids: set[UUID] = set()
        now = datetime.now(timezone.utc)

        for item in inventory:
            try:
                task_id = UUID(item["task_id"])
                operation_id = UUID(item["operation_id"])
                instance_id = UUID(item["instance_id"])
                epoch = item["assignment_epoch"]
                local_state = item["local_state"]
                local_summary = item.get("result_summary", {})
                if (
                    isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 1
                    or local_state not in {"accepted", "running", "succeeded", "failed", "unknown"}
                    or not isinstance(local_summary, dict)
                ):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise HTTPException(status_code=422, detail={"code": "INVALID_RECONCILIATION_ITEM"}) from None

            if task_id in seen_task_ids:
                raise HTTPException(status_code=422, detail={"code": "DUPLICATE_RECONCILIATION_TASK"})
            seen_task_ids.add(task_id)

            row = conn.execute(
                """
                SELECT t.task_id, t.operation_id, t.instance_id, t.node_id,
                       t.assignment_epoch, t.status, t.result_summary,
                       i.owner_node_id, i.assignment_epoch, i.lease_expires_at,
                       o.status, o.result_summary, t.delivery_lease_until,
                       o.node_id, o.instance_id, o.assignment_epoch
                  FROM geelark_control.agent_tasks AS t
                  JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
                  JOIN geelark_control.operations AS o ON o.operation_id = t.operation_id
                 WHERE t.task_id = %s AND t.node_id = %s
                 FOR UPDATE OF t, i, o
                """,
                (task_id, principal.node_id),
            ).fetchone()

            decision = "MANUAL_REVIEW_REQUIRED"
            if row is None:
                decision = "UNKNOWN_TASK"
            elif (
                str(row[1]) != str(operation_id)
                or str(row[2]) != str(instance_id)
            ):
                decision = "IDENTITY_MISMATCH"
            elif str(row[3]) != principal.node_id:
                decision = "TASK_NOT_OWNED_BY_NODE"
            elif (
                str(row[13]) != str(row[3])
                or str(row[14]) != str(row[2])
                or row[15] != row[4]
            ):
                decision = "SERVER_TASK_OPERATION_IDENTITY_MISMATCH"
            elif (
                row[7] is None or str(row[7]) != principal.node_id
                or row[8] != row[4] or epoch != row[4]
            ):
                decision = "STALE_ASSIGNMENT_EPOCH"
            elif row[5] == "unknown" or local_state == "unknown":
                decision = "MANUAL_REVIEW_REQUIRED"
            elif row[10] != row[5] or dict(row[11] or {}) != dict(row[6] or {}):
                decision = "SERVER_TASK_OPERATION_STATE_MISMATCH"
            elif row[5] in {"succeeded", "rejected", "failed", "cancelled"}:
                if row[5] == local_state and dict(row[6] or {}) == local_summary:
                    decision = "ALREADY_CONFIRMED"
                else:
                    decision = "TERMINAL_CONFLICT_MANUAL_REVIEW"
            elif row[9] is None or row[9] <= now:
                decision = "INSTANCE_LEASE_EXPIRED_HOLD"
            elif (
                row[5] in {"delivered", "accepted", "running"}
                and (row[12] is None or row[12] <= now)
            ):
                decision = "DELIVERY_LEASE_EXPIRED_HOLD"
            elif row[5] in {"accepted", "running"}:
                if local_state in {"succeeded", "failed"}:
                    decision = "RESEND_TERMINAL_RESULT"
                elif local_state == "running" and row[5] == "accepted":
                    decision = "RESEND_PROGRESS"
                elif local_state == "accepted" and row[5] == "running":
                    decision = "SERVER_AHEAD_HOLD"
                elif local_state == row[5] and local_summary == dict(row[6] or {}):
                    decision = "CONTINUE_SAME_EPOCH"
                else:
                    decision = "RESULT_SUMMARY_MISMATCH_MANUAL_REVIEW"
            else:
                decision = "TASK_NOT_ACCEPTED_HOLD"

            decisions.append({
                "task_id": str(task_id),
                "operation_id": str(operation_id),
                "instance_id": str(instance_id),
                "assignment_epoch": epoch,
                "local_state": local_state,
                "server_state": row[5] if row is not None else None,
                "decision": decision,
                "automatic_mutation": False,
            })

        # También reporta tareas activas del nodo que no aparecen en su inventario.
        missing_rows = conn.execute(
            """
            SELECT t.task_id, t.operation_id, t.instance_id, t.assignment_epoch,
                   t.status, o.status, o.result_summary, t.result_summary,
                   o.node_id, o.instance_id, o.assignment_epoch
              FROM geelark_control.agent_tasks AS t
              JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
              JOIN geelark_control.operations AS o ON o.operation_id = t.operation_id
             WHERE t.node_id = %s
               AND t.status IN ('accepted', 'running', 'unknown')
               AND i.owner_node_id = t.node_id
               AND i.assignment_epoch = t.assignment_epoch
             ORDER BY t.created_at, t.task_id
             FOR UPDATE OF t, i, o
            """,
            (principal.node_id,),
        ).fetchall()
        for row in missing_rows:
            if row[0] in seen_task_ids:
                continue
            decisions.append({
                "task_id": str(row[0]),
                "operation_id": str(row[1]),
                "instance_id": str(row[2]),
                "assignment_epoch": row[3],
                "local_state": None,
                "server_state": row[4],
                "decision": (
                    "MANUAL_REVIEW_REQUIRED"
                    if row[4] == "unknown"
                    else (
                        "SERVER_TASK_OPERATION_STATE_MISMATCH"
                        if row[5] != row[4] or dict(row[6] or {}) != dict(row[7] or {})
                        else (
                            "SERVER_TASK_OPERATION_IDENTITY_MISMATCH"
                            if str(row[8]) != str(principal.node_id)
                            or str(row[9]) != str(row[2])
                            or row[10] != row[3]
                            else "SERVER_TASK_MISSING_FROM_LOCAL_INVENTORY"
                        )
                    )
                ),
                "automatic_mutation": False,
            })

        report_id = uuid4()
        conn.execute(
            """
            INSERT INTO geelark_control.agent_reconciliation_reports
                (report_id, node_id, inventory_sha256, inventory_count, decisions)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (report_id, UUID(principal.node_id), inventory_hash, len(inventory), Jsonb(decisions)),
        )
        return {
            "ok": True,
            "report_id": str(report_id),
            "inventory_sha256": inventory_hash,
            "inventory_count": len(inventory),
            "decision_count": len(decisions),
            "decisions": decisions,
            "mutations_applied": False,
        }


    return {
        Operation.HEARTBEAT: heartbeat,
        Operation.CAPABILITIES: capabilities,
        Operation.MODULES_REPORT: modules,
        Operation.STATUS_READ: status,
        Operation.TASK_FETCH: claim_task,
        Operation.TASK_ACCEPT: accept_task,
        Operation.TASK_PROGRESS: progress_task,
        Operation.TASK_RESULT: result_task,
        Operation.RECONCILE: reconcile,
        Operation.RECONCILE_INVENTORY: reconcile_inventory,
    }
