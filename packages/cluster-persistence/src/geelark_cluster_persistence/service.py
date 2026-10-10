"""Servicio transaccional de asignación de instancias.

No envía órdenes a agentes. Solo persiste la intención y un evento outbox.
El dispatcher y el fencing del agente pertenecen a una etapa posterior.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from psycopg import Connection
from psycopg.types.json import Jsonb

from .domain import (
    IdempotencyConflict,
    IdempotencyRecordIncomplete,
    InstanceAlreadyAssigned,
    InstanceNotFound,
    InstanceStateBlocked,
    InsufficientCapacity,
    InvalidAssignmentRequest,
    NodeCapacityNotConfigured,
    NodeNotEligible,
)

_IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class AssignmentRequest:
    scope: str
    idempotency_key: str
    request_id: UUID
    instance_id: UUID
    node_id: UUID
    cpu_units: Decimal | int | float
    memory_bytes: int
    storage_bytes: int
    lease_expires_at: datetime
    engine_name: str
    engine_version: str
    image_digest: str
    desired_state: str = "running"


def _canonical_payload(request: AssignmentRequest, cpu_units: Decimal) -> dict[str, Any]:
    lease = request.lease_expires_at.astimezone(timezone.utc).isoformat()
    return {
        "instance_id": str(request.instance_id),
        "node_id": str(request.node_id),
        "desired_state": request.desired_state,
        "cpu_units": format(cpu_units.normalize(), "f"),
        "memory_bytes": request.memory_bytes,
        "storage_bytes": request.storage_bytes,
        "lease_expires_at": lease,
        "engine_name": request.engine_name,
        "engine_version": request.engine_version,
        "image_digest": request.image_digest,
    }


def _validate_request(request: AssignmentRequest) -> Decimal:
    if not request.scope.strip() or len(request.scope) > 128:
        raise InvalidAssignmentRequest("scope debe tener entre 1 y 128 caracteres")
    if not 16 <= len(request.idempotency_key) <= 200:
        raise InvalidAssignmentRequest("idempotency_key debe tener entre 16 y 200 caracteres")
    for name in ("request_id", "instance_id", "node_id"):
        if not isinstance(getattr(request, name), UUID):
            raise InvalidAssignmentRequest(f"{name} debe ser UUID")
    try:
        cpu_units = Decimal(str(request.cpu_units))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidAssignmentRequest("cpu_units no es un número válido") from exc
    if not cpu_units.is_finite() or cpu_units <= 0:
        raise InvalidAssignmentRequest("cpu_units debe ser finito y mayor que cero")
    if isinstance(request.memory_bytes, bool) or request.memory_bytes <= 0:
        raise InvalidAssignmentRequest("memory_bytes debe ser un entero positivo")
    if isinstance(request.storage_bytes, bool) or request.storage_bytes <= 0:
        raise InvalidAssignmentRequest("storage_bytes debe ser un entero positivo")
    if not isinstance(request.memory_bytes, int) or not isinstance(request.storage_bytes, int):
        raise InvalidAssignmentRequest("memory_bytes y storage_bytes deben ser enteros")
    if request.lease_expires_at.tzinfo is None or request.lease_expires_at.utcoffset() is None:
        raise InvalidAssignmentRequest("lease_expires_at debe incluir zona horaria")
    if request.lease_expires_at <= datetime.now(timezone.utc):
        raise InvalidAssignmentRequest("lease_expires_at debe estar en el futuro")
    if request.desired_state not in {"running", "stopped"}:
        raise InvalidAssignmentRequest("desired_state debe ser running o stopped")
    if not request.engine_name.strip() or len(request.engine_name) > 128:
        raise InvalidAssignmentRequest("engine_name no es válido")
    if not request.engine_version.strip() or len(request.engine_version) > 64:
        raise InvalidAssignmentRequest("engine_version no es válido")
    if not _IMAGE_DIGEST_RE.fullmatch(request.image_digest):
        raise InvalidAssignmentRequest("image_digest debe tener formato sha256")
    return cpu_units


def assign_instance(conn: Connection, request: AssignmentRequest) -> dict[str, Any]:
    """Reserva instancia, capacidad y outbox en una transacción indivisible.

    La conexión debe apuntar a PostgreSQL y tener permisos solo sobre el esquema
    necesario. No se ejecuta ningún proceso ni se contacta con el nodo.
    """
    cpu_units = _validate_request(request)
    payload = _canonical_payload(request, cpu_units)
    payload_sha256 = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    operation_id = uuid4()
    reservation_id = uuid4()
    outbox_event_id = uuid4()

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO geelark_control.idempotency_records
                    (scope, idempotency_key, payload_sha256)
                VALUES (%s, %s, %s)
                ON CONFLICT (scope, idempotency_key) DO NOTHING
                """,
                (request.scope, request.idempotency_key, payload_sha256),
            )
            cur.execute(
                """
                SELECT payload_sha256, operation_id, response_snapshot
                  FROM geelark_control.idempotency_records
                 WHERE scope = %s AND idempotency_key = %s
                 FOR UPDATE
                """,
                (request.scope, request.idempotency_key),
            )
            idempotency_row = cur.fetchone()
            if idempotency_row is None:
                raise RuntimeError("No se pudo recuperar el registro idempotente")
            stored_hash, stored_operation_id, stored_response = idempotency_row
            if stored_hash != payload_sha256:
                raise IdempotencyConflict("La clave idempotente ya se usó con otro payload")
            if stored_operation_id is not None:
                if stored_response is None:
                    raise IdempotencyRecordIncomplete("La clave existe sin respuesta persistida")
                return dict(stored_response)
            # A null operation_id is valid only for the row inserted by this transaction.
            # A pre-existing incomplete row must not be silently claimed.
            cur.execute(
                """
                SELECT created_at
                  FROM geelark_control.idempotency_records
                 WHERE scope = %s AND idempotency_key = %s
                """,
                (request.scope, request.idempotency_key),
            )
            # If the row was inserted earlier and committed incomplete, fail closed.
            # PostgreSQL's transaction-local xmin distinguishes the inserted row.
            cur.execute(
                """
                SELECT xmin = txid_current()::text::xid
                  FROM geelark_control.idempotency_records
                 WHERE scope = %s AND idempotency_key = %s
                """,
                (request.scope, request.idempotency_key),
            )
            inserted_in_this_transaction = cur.fetchone()[0]
            if not inserted_in_this_transaction:
                raise IdempotencyRecordIncomplete("La clave idempotente quedó incompleta; requiere reconciliación")

            cur.execute(
                """
                SELECT observed_state, owner_node_id, assignment_epoch
                  FROM geelark_control.instances
                 WHERE instance_id = %s
                 FOR UPDATE
                """,
                (request.instance_id,),
            )
            instance_row = cur.fetchone()
            if instance_row is None:
                raise InstanceNotFound("La instancia no está registrada")
            observed_state, owner_node_id, previous_epoch = instance_row
            if observed_state in {"unknown", "reconciling"}:
                raise InstanceStateBlocked("El estado incierto bloquea una nueva asignación")
            if owner_node_id is not None:
                raise InstanceAlreadyAssigned("La instancia ya tiene un propietario vigente")

            cur.execute(
                """
                SELECT admin_state, health_state
                  FROM geelark_control.nodes
                 WHERE node_id = %s
                 FOR UPDATE
                """,
                (request.node_id,),
            )
            node_row = cur.fetchone()
            if node_row is None or node_row[0] != "active" or node_row[1] != "healthy":
                raise NodeNotEligible("El nodo no está activo y saludable")

            cur.execute(
                """
                SELECT cpu_units, memory_capacity_bytes, storage_capacity_bytes,
                       memory_safety_margin_bytes, storage_safety_margin_bytes
                  FROM geelark_control.node_resource_capacity
                 WHERE node_id = %s
                 FOR UPDATE
                """,
                (request.node_id,),
            )
            capacity = cur.fetchone()
            if capacity is None:
                raise NodeCapacityNotConfigured("El nodo no tiene capacidad reservable configurada")
            cpu_capacity, memory_capacity, storage_capacity, memory_margin, storage_margin = capacity

            cur.execute(
                """
                SELECT COALESCE(SUM(cpu_units), 0),
                       COALESCE(SUM(memory_bytes), 0),
                       COALESCE(SUM(storage_bytes), 0)
                  FROM geelark_control.resource_reservations
                 WHERE node_id = %s AND status IN ('held', 'uncertain')
                """,
                (request.node_id,),
            )
            used_cpu, used_memory, used_storage = cur.fetchone()
            if Decimal(str(used_cpu)) + cpu_units > Decimal(str(cpu_capacity)):
                raise InsufficientCapacity("Capacidad de CPU insuficiente")
            if used_memory + request.memory_bytes > memory_capacity - memory_margin:
                raise InsufficientCapacity("Capacidad de RAM insuficiente")
            if used_storage + request.storage_bytes > storage_capacity - storage_margin:
                raise InsufficientCapacity("Capacidad de almacenamiento insuficiente")

            new_epoch = previous_epoch + 1
            cur.execute(
                """
                UPDATE geelark_control.instances
                   SET desired_state = %s,
                       observed_state = 'reserved',
                       owner_node_id = %s,
                       assignment_epoch = %s,
                       lease_expires_at = %s,
                       engine_name = %s,
                       engine_version = %s,
                       image_digest = %s,
                       updated_at = now()
                 WHERE instance_id = %s
                """,
                (
                    request.desired_state,
                    request.node_id,
                    new_epoch,
                    request.lease_expires_at,
                    request.engine_name,
                    request.engine_version,
                    request.image_digest,
                    request.instance_id,
                ),
            )
            cur.execute(
                """
                INSERT INTO geelark_control.operations
                    (operation_id, request_id, instance_id, node_id, assignment_epoch,
                     operation_type, status)
                VALUES (%s, %s, %s, %s, %s, 'assign', 'accepted')
                """,
                (operation_id, request.request_id, request.instance_id, request.node_id, new_epoch),
            )
            cur.execute(
                """
                INSERT INTO geelark_control.resource_reservations
                    (reservation_id, instance_id, node_id, assignment_epoch,
                     cpu_units, memory_bytes, storage_bytes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'held')
                """,
                (
                    reservation_id,
                    request.instance_id,
                    request.node_id,
                    new_epoch,
                    cpu_units,
                    request.memory_bytes,
                    request.storage_bytes,
                ),
            )
            cur.execute(
                """
                INSERT INTO geelark_control.assignment_events
                    (instance_id, assignment_epoch, previous_node_id, new_node_id,
                     previous_state, new_state, actor_type, actor_id, request_id,
                     operation_id, reason)
                VALUES (%s, %s, NULL, %s, %s, 'reserved', 'controller',
                        'assignment-service', %s, %s, 'assignment accepted')
                """,
                (
                    request.instance_id,
                    new_epoch,
                    request.node_id,
                    observed_state,
                    request.request_id,
                    operation_id,
                ),
            )
            outbox_payload = {
                "operation_id": str(operation_id),
                "request_id": str(request.request_id),
                "instance_id": str(request.instance_id),
                "node_id": str(request.node_id),
                "assignment_epoch": new_epoch,
                "desired_state": request.desired_state,
                "lease_expires_at": request.lease_expires_at.astimezone(timezone.utc).isoformat(),
                "engine": {"name": request.engine_name, "version": request.engine_version},
                "image_digest": request.image_digest,
            }
            cur.execute(
                """
                INSERT INTO geelark_control.outbox_events
                    (event_id, deduplication_key, instance_id, assignment_epoch,
                     operation_id, event_type, payload)
                VALUES (%s, %s, %s, %s, %s, 'assignment.requested', %s)
                """,
                (
                    outbox_event_id,
                    f"assignment:{request.instance_id}:{new_epoch}",
                    request.instance_id,
                    new_epoch,
                    operation_id,
                    Jsonb(outbox_payload),
                ),
            )
            response = {
                "operation_id": str(operation_id),
                "instance_id": str(request.instance_id),
                "node_id": str(request.node_id),
                "assignment_epoch": new_epoch,
                "status": "accepted",
                "observed_state": "reserved",
            }
            cur.execute(
                """
                UPDATE geelark_control.idempotency_records
                   SET operation_id = %s, response_snapshot = %s
                 WHERE scope = %s AND idempotency_key = %s
                """,
                (operation_id, Jsonb(response), request.scope, request.idempotency_key),
            )

    return response
