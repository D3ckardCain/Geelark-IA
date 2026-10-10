"""Adaptadores PostgreSQL para telemetría, bandeja de tareas y resultados tipados.

No ejecuta motores Android ni shell/ADB. Toda transición valida nodo, epoch y lease.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .policy import AgentPrincipal, Operation


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
               SET agent_version = %s, health_state = %s,
                   last_seen_at = now(), last_sequence = last_sequence + 1,
                   updated_at = now()
             WHERE node_id = %s AND admin_state IN ('pending', 'active') AND revoked_at IS NULL
            RETURNING node_id, admin_state, health_state, last_seen_at, last_sequence
            """,
            (payload["agent_version"], payload["health_state"], principal.node_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return {
            "ok": True,
            "node_id": str(row[0]),
            "admin_state": row[1],
            "health_state": row[2],
            "last_seen_at": row[3].astimezone(timezone.utc).isoformat(),
            "sequence": row[4],
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
                SELECT node_id, display_name, admin_state, health_state, agent_version,
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
                "health_state": row[3],
                "agent_version": row[4],
                "protocol_version": row[5],
                "last_seen_at": row[6].astimezone(timezone.utc).isoformat() if row[6] else None,
                "sequence": row[7],
                "capabilities": row[8],
            }

    def _locked_task(conn: psycopg.Connection, principal: AgentPrincipal, task_id: UUID):
        row = conn.execute(
            """
            SELECT t.status, t.node_id, t.instance_id, t.assignment_epoch,
                   t.result_summary, i.owner_node_id, i.assignment_epoch,
                   i.lease_expires_at, o.status
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
             WHERE t.node_id = %s
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
        task_id, operation_id, instance_id, epoch, task_payload, attempts, lease_expires_at = row
        conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = 'delivered',
                   delivery_attempts = delivery_attempts + 1,
                   delivery_lease_until = now() + interval '30 seconds',
                   delivered_at = COALESCE(delivered_at, now()),
                   updated_at = now()
             WHERE task_id = %s
            """,
            (task_id,),
        )
        body = dict(task_payload)
        body.update({
            "task_id": str(task_id),
            "operation_id": str(operation_id),
            "instance_id": str(instance_id),
            "node_id": principal.node_id,
            "assignment_epoch": epoch,
            "lease_expires_at": lease_expires_at.astimezone(timezone.utc).isoformat(),
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
        details = payload.get("details", {})
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
        details = payload.get("details", {})
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

    def claim_task(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: Any = None) -> dict[str, Any]:
        """Entrega una tarea de la bandeja solo al nodo activo propietario."""
        row = conn.execute(
            """
            SELECT t.task_id, t.operation_id, t.instance_id, t.assignment_epoch,
                   t.payload, t.status, t.delivery_lease_until,
                   i.owner_node_id, i.assignment_epoch, i.lease_expires_at
              FROM geelark_control.agent_tasks AS t
              JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
              JOIN geelark_control.nodes AS n ON n.node_id = t.node_id
             WHERE t.node_id = %s
               AND n.admin_state = 'active'
               AND t.status IN ('queued', 'delivered')
               AND (t.delivery_lease_until IS NULL OR t.delivery_lease_until <= now())
               AND i.owner_node_id = t.node_id
               AND i.assignment_epoch = t.assignment_epoch
               AND i.lease_expires_at > now()
             ORDER BY t.created_at, t.task_id
             FOR UPDATE OF t SKIP LOCKED
             LIMIT 1
            """,
            (principal.node_id,),
        ).fetchone()
        if row is None:
            return {"task": None}
        task_id, operation_id, instance_id, epoch, task_payload, status, lease_until, owner, current_epoch, instance_lease = row
        lease = conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = 'delivered',
                   delivery_attempts = delivery_attempts + 1,
                   delivery_lease_until = now() + interval '60 seconds',
                   delivered_at = COALESCE(delivered_at, now()),
                   updated_at = now()
             WHERE task_id = %s
            RETURNING delivery_lease_until
            """,
            (task_id,),
        ).fetchone()[0]
        return {
            "task": {
                "task_id": str(task_id),
                "operation_id": str(operation_id),
                "instance_id": str(instance_id),
                "node_id": str(principal.node_id),
                "assignment_epoch": epoch,
                "lease_expires_at": lease.isoformat(),
                "instance_lease_expires_at": instance_lease.isoformat(),
                "payload": task_payload,
            }
        }

    def _task_update(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: Any, state: str) -> dict[str, Any]:
        task_id = UUID(str(payload["task_id"]))
        details = payload.get("details", {})
        if not isinstance(details, dict):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_DETAILS"})
        row = conn.execute(
            """
            SELECT t.operation_id, t.instance_id, t.assignment_epoch, t.status,
                   t.delivery_lease_until, i.owner_node_id, i.assignment_epoch AS current_epoch
              FROM geelark_control.agent_tasks AS t
              JOIN geelark_control.instances AS i ON i.instance_id = t.instance_id
              JOIN geelark_control.nodes AS n ON n.node_id = t.node_id
             WHERE t.task_id = %s AND t.node_id = %s AND n.admin_state = 'active'
             FOR UPDATE OF t
            """,
            (task_id, principal.node_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "TASK_NOT_FOUND"})
        operation_id, instance_id, epoch, current_status, lease_until, owner, current_epoch = row
        if owner is None or str(owner) != str(principal.node_id) or epoch != current_epoch:
            raise HTTPException(status_code=409, detail={"code": "STALE_ASSIGNMENT_EPOCH"})
        if lease_until is None or lease_until <= datetime.now(timezone.utc):
            raise HTTPException(status_code=409, detail={"code": "TASK_LEASE_EXPIRED"})
        if current_status in {"succeeded", "failed", "rejected", "cancelled"}:
            if current_status == state:
                return {"ok": True, "status": current_status, "idempotent": True}
            raise HTTPException(status_code=409, detail={"code": "TASK_TERMINAL"})
        if state == "accepted":
            new_task_status = "accepted"
            operation_status = "accepted"
        elif state == "running":
            new_task_status = "running"
            operation_status = "running"
        elif state in {"succeeded", "failed", "rejected", "unknown"}:
            new_task_status = state
            operation_status = "succeeded" if state == "succeeded" else ("rejected" if state == "rejected" else ("failed" if state == "failed" else "unknown"))
        else:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TASK_STATE"})
        terminal = new_task_status in {"succeeded", "failed", "rejected", "unknown"}
        summary = details if terminal else {}
        conn.execute(
            """
            UPDATE geelark_control.agent_tasks
               SET status = %s, result_summary = %s,
                   completed_at = CASE WHEN %s THEN now() ELSE completed_at END,
                   updated_at = now(), last_error_code = %s
             WHERE task_id = %s
            """,
            (new_task_status, Jsonb(summary), terminal, details.get("error_code"), task_id),
        )
        conn.execute(
            """
            UPDATE geelark_control.operations
               SET status = %s, result_summary = %s,
                   error_code = %s,
                   completed_at = CASE WHEN %s THEN now() ELSE completed_at END,
                   updated_at = now()
             WHERE operation_id = %s AND node_id = %s AND assignment_epoch = %s
            """,
            (operation_status, Jsonb(summary), details.get("error_code"), terminal, operation_id, principal.node_id, epoch),
        )
        return {"ok": True, "status": new_task_status, "operation_id": str(operation_id)}

    def task_accept(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: Any) -> dict[str, Any]:
        return _task_update(conn=conn, principal=principal, payload=payload, state="accepted")

    def task_progress(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: Any) -> dict[str, Any]:
        state = payload.get("state")
        if state not in {"running"}:
            raise HTTPException(status_code=422, detail={"code": "INVALID_PROGRESS_STATE"})
        return _task_update(conn=conn, principal=principal, payload=payload, state=state)

    def task_result(*, conn: psycopg.Connection, principal: AgentPrincipal, payload: Any) -> dict[str, Any]:
        state = payload.get("state")
        if state not in {"succeeded", "failed", "rejected", "unknown"}:
            raise HTTPException(status_code=422, detail={"code": "INVALID_RESULT_STATE"})
        return _task_update(conn=conn, principal=principal, payload=payload, state=state)

    return {
        Operation.HEARTBEAT: heartbeat,
        Operation.CAPABILITIES: capabilities,
        Operation.STATUS_READ: status,
        Operation.TASK_FETCH: claim_task,
        Operation.TASK_ACCEPT: task_accept,
        Operation.TASK_PROGRESS: task_progress,
        Operation.TASK_RESULT: task_result,
        Operation.TASK_FETCH: claim_task,
        Operation.TASK_ACCEPT: accept_task,
        Operation.TASK_PROGRESS: progress_task,
        Operation.TASK_RESULT: result_task,
    }
