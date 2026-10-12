"""Journal SQLite local para deduplicación y fencing por epoch.

Este módulo no autentica mensajes ni ejecuta adaptadores Android. El caller debe
validar identidad/autorización antes de aceptar un comando.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


class AgentGuardError(Exception):
    """Error base del guardián local."""


class InvalidAgentCommand(AgentGuardError):
    """Comando local mal formado."""


class StaleAssignmentEpoch(AgentGuardError):
    """El comando usa un epoch anterior al journal local."""


class ExpiredAssignmentLease(AgentGuardError):
    """La lease de la asignación ya expiró."""


class AssignmentOwnerConflict(AgentGuardError):
    """El mismo epoch aparece asociado a otro nodo."""


class OperationIdConflict(AgentGuardError):
    """operation_id ya existe con otro payload semántico."""


class UnknownOperation(AgentGuardError):
    """No existe un recibo local para la operación."""


class StaleOperationResult(AgentGuardError):
    """Un resultado pertenece a un epoch/propietario que ya no es actual."""


class OperationResultConflict(AgentGuardError):
    """Una operación terminal recibió un resultado contradictorio."""


@dataclass(frozen=True, slots=True)
class AgentCommand:
    operation_id: UUID
    instance_id: UUID
    node_id: UUID
    assignment_epoch: int
    lease_expires_at: datetime
    payload: dict[str, Any]
    task_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OperationReceipt:
    operation_id: UUID
    instance_id: UUID
    node_id: UUID
    assignment_epoch: int
    status: str
    result: dict[str, Any] | None
    duplicate: bool = False
    task_id: UUID | None = None


class AgentJournal:
    """Journal durable de un solo nodo; usar archivo en disco local, no NFS."""

    _SCHEMA_VERSION = 3
    _STATUSES = {"accepted", "running", "succeeded", "rejected", "failed", "unknown"}
    _TERMINAL_STATUSES = {"succeeded", "rejected", "failed"}

    def __init__(self, db_path: str | Path, local_node_id: UUID):
        if str(db_path) == ":memory:":
            raise ValueError("El journal requiere un archivo SQLite persistente, no :memory:")
        if not isinstance(local_node_id, UUID):
            raise ValueError("local_node_id debe ser UUID")
        self.db_path = Path(db_path)
        self.local_node_id = local_node_id

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.db_path.is_symlink():
            raise AgentGuardError("El archivo del journal no puede ser un enlace simbólico")
        if self.db_path.exists() and not self.db_path.is_file():
            raise AgentGuardError("La ruta del journal debe ser un archivo regular")
        if not self.db_path.exists():
            try:
                descriptor = os.open(
                    self.db_path,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                    0o600,
                )
                os.close(descriptor)
            except FileExistsError:
                if self.db_path.is_symlink() or not self.db_path.is_file():
                    raise AgentGuardError("La ruta del journal cambió durante su creación")
        if os.name != "nt":
            os.chmod(self.db_path, 0o600)
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS instance_fences (
                    instance_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    assignment_epoch INTEGER NOT NULL CHECK (assignment_epoch >= 1),
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operation_receipts (
                    operation_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    instance_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    assignment_epoch INTEGER NOT NULL CHECK (assignment_epoch >= 1),
                    payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
                    status TEXT NOT NULL CHECK (status IN ('accepted', 'running', 'succeeded', 'rejected', 'failed', 'unknown')),
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS synced_receipts (
                    operation_id TEXT PRIMARY KEY,
                    synced_at TEXT NOT NULL,
                    FOREIGN KEY(operation_id) REFERENCES operation_receipts(operation_id)
                )
                """
            )
            version = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
            if version > self._SCHEMA_VERSION:
                raise AgentGuardError("La versión del journal es más nueva que este agente")
            if version == 0:
                # Un journal nuevo se crea directamente con el esquema más reciente.
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (1, ?)",
                    (self._now(),),
                )
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (2, ?)",
                    (self._now(),),
                )
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (3, ?)",
                    (self._now(),),
                )
            elif version == 1:
                # SQLite no permite ampliar un CHECK existente con ALTER COLUMN.
                # Se recrean las dos tablas en una transacción y se conservan los ACK.
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.execute("BEGIN IMMEDIATE")
                try:
                    conn.execute(
                        """
                        CREATE TABLE operation_receipts_v2 (
                            operation_id TEXT PRIMARY KEY,
                            instance_id TEXT NOT NULL,
                            node_id TEXT NOT NULL,
                            assignment_epoch INTEGER NOT NULL CHECK (assignment_epoch >= 1),
                            payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
                            status TEXT NOT NULL CHECK (status IN ('accepted', 'running', 'succeeded', 'rejected', 'failed', 'unknown')),
                            result_json TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                        """
                    )
                    conn.execute(
                        """
                        INSERT INTO operation_receipts_v2
                            (operation_id, instance_id, node_id, assignment_epoch,
                             payload_sha256, status, result_json, created_at, updated_at)
                        SELECT operation_id, instance_id, node_id, assignment_epoch,
                               payload_sha256, status, result_json, created_at, updated_at
                          FROM operation_receipts
                        """
                    )
                    conn.execute(
                        """
                        CREATE TABLE synced_receipts_v2 (
                            operation_id TEXT PRIMARY KEY,
                            synced_at TEXT NOT NULL,
                            FOREIGN KEY(operation_id) REFERENCES operation_receipts_v2(operation_id)
                        )
                        """
                    )
                    conn.execute(
                        """
                        INSERT INTO synced_receipts_v2(operation_id, synced_at)
                        SELECT operation_id, synced_at FROM synced_receipts
                        """
                    )
                    conn.execute("DROP TABLE synced_receipts")
                    conn.execute("DROP TABLE operation_receipts")
                    conn.execute("ALTER TABLE operation_receipts_v2 RENAME TO operation_receipts")
                    conn.execute("ALTER TABLE synced_receipts_v2 RENAME TO synced_receipts")
                    conn.execute(
                        "INSERT INTO schema_migrations(version, applied_at) VALUES (2, ?)",
                        (self._now(),),
                    )
                    conn.commit()
                    version = 2
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    conn.execute("PRAGMA foreign_keys = ON")
            if version == 2:
                conn.execute("ALTER TABLE operation_receipts ADD COLUMN task_id TEXT")
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (3, ?)",
                    (self._now(),),
                )
        finally:
            conn.close()

    def accept_command(self, command: AgentCommand) -> OperationReceipt:
        """Persiste aceptación o devuelve el recibo existente sin reejecutar."""
        payload_hash = self._command_hash(command)
        now = self._now()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                """
                SELECT operation_id, instance_id, node_id, assignment_epoch,
                       payload_sha256, status, result_json
                  FROM operation_receipts
                 WHERE operation_id = ?
                """,
                (str(command.operation_id),),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_hash:
                    raise OperationIdConflict("operation_id ya se usó con otro payload")
                conn.commit()
                return self._receipt(existing, duplicate=True)

            if command.lease_expires_at <= datetime.now(timezone.utc):
                raise ExpiredAssignmentLease("La lease de la asignación ya expiró")

            fence = conn.execute(
                "SELECT node_id, assignment_epoch FROM instance_fences WHERE instance_id = ?",
                (str(command.instance_id),),
            ).fetchone()
            if fence is not None:
                current_node = UUID(fence["node_id"])
                current_epoch = fence["assignment_epoch"]
                if command.assignment_epoch < current_epoch:
                    raise StaleAssignmentEpoch("El comando tiene un assignment_epoch obsoleto")
                if command.assignment_epoch == current_epoch and command.node_id != current_node:
                    raise AssignmentOwnerConflict("El mismo epoch no puede pertenecer a otro nodo")
                if command.assignment_epoch > current_epoch:
                    conn.execute(
                        """
                        UPDATE instance_fences
                           SET node_id = ?, assignment_epoch = ?, updated_at = ?
                         WHERE instance_id = ?
                        """,
                        (
                            str(command.node_id),
                            command.assignment_epoch,
                            now,
                            str(command.instance_id),
                        ),
                    )
            else:
                conn.execute(
                    """
                    INSERT INTO instance_fences(instance_id, node_id, assignment_epoch, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(command.instance_id), str(command.node_id), command.assignment_epoch, now),
                )

            conn.execute(
                """
                INSERT INTO operation_receipts
                    (operation_id, instance_id, node_id, assignment_epoch, payload_sha256,
                     status, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'accepted', NULL, ?, ?)
                """,
                (
                    str(command.operation_id),
                    str(command.instance_id),
                    str(command.node_id),
                    command.assignment_epoch,
                    payload_hash,
                    now,
                    now,
                ),
            )
            conn.commit()
            return OperationReceipt(
                operation_id=command.operation_id,
                instance_id=command.instance_id,
                node_id=command.node_id,
                assignment_epoch=command.assignment_epoch,
                status="accepted",
                result=None,
                duplicate=False,
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def record_result(
        self,
        *,
        operation_id: UUID,
        instance_id: UUID,
        node_id: UUID,
        assignment_epoch: int,
        status: str,
        result: dict[str, Any],
    ) -> OperationReceipt:
        """Guarda resultado solo si el epoch y propietario siguen vigentes."""
        if not all(isinstance(value, UUID) for value in (operation_id, instance_id, node_id)):
            raise InvalidAgentCommand("IDs de resultado deben ser UUID")
        if not isinstance(assignment_epoch, int) or isinstance(assignment_epoch, bool) or assignment_epoch < 1:
            raise InvalidAgentCommand("assignment_epoch de resultado debe ser entero positivo")
        if node_id != self.local_node_id:
            raise InvalidAgentCommand("El resultado no está dirigido a este nodo")
        if not isinstance(result, dict):
            raise InvalidAgentCommand("result debe ser un objeto JSON")
        if not isinstance(status, str) or status not in {"running", "succeeded", "rejected", "failed", "unknown"}:
            raise InvalidAgentCommand("status de resultado no válido")
        result_json = self._canonical_json(result)
        if len(result_json.encode("utf-8")) > 1_000_000:
            raise InvalidAgentCommand("El resultado supera 1 MB")
        now = self._now()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            fence = conn.execute(
                "SELECT node_id, assignment_epoch FROM instance_fences WHERE instance_id = ?",
                (str(instance_id),),
            ).fetchone()
            if (
                fence is None
                or fence["node_id"] != str(node_id)
                or fence["assignment_epoch"] != assignment_epoch
                or node_id != self.local_node_id
            ):
                raise StaleOperationResult("El resultado no pertenece al epoch/propietario vigente")

            row = conn.execute(
                """
                SELECT operation_id, instance_id, node_id, assignment_epoch,
                       payload_sha256, status, result_json
                  FROM operation_receipts
                 WHERE operation_id = ?
                """,
                (str(operation_id),),
            ).fetchone()
            if row is None:
                raise UnknownOperation("No existe recibo local para operation_id")
            if (
                row["instance_id"] != str(instance_id)
                or row["node_id"] != str(node_id)
                or row["assignment_epoch"] != assignment_epoch
            ):
                raise StaleOperationResult("El recibo no coincide con el epoch/propietario actual")

            old_result = json.loads(row["result_json"]) if row["result_json"] is not None else None
            if row["status"] in self._TERMINAL_STATUSES:
                if row["status"] != status or old_result != result:
                    raise OperationResultConflict("Una operación terminal no puede cambiar de resultado")
                conn.commit()
                return self._receipt(row, duplicate=True)

            conn.execute(
                """
                UPDATE operation_receipts
                   SET status = ?, result_json = ?, updated_at = ?
                 WHERE operation_id = ?
                """,
                (status, result_json, now, str(operation_id)),
            )
            # Cada nueva versión de progreso/resultado debe volver a la cola,
            # incluso si una versión anterior ya recibió ACK.
            conn.execute("DELETE FROM synced_receipts WHERE operation_id = ?", (str(operation_id),))
            conn.commit()
            return OperationReceipt(
                operation_id=operation_id,
                instance_id=instance_id,
                node_id=node_id,
                assignment_epoch=assignment_epoch,
                status=status,
                result=result,
                duplicate=False,
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_receipt(self, operation_id: UUID) -> OperationReceipt | None:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT operation_id, instance_id, node_id, assignment_epoch,
                       payload_sha256, status, result_json
                  FROM operation_receipts
                 WHERE operation_id = ?
                """,
                (str(operation_id),),
            ).fetchone()
            return self._receipt(row, duplicate=False) if row is not None else None
        finally:
            conn.close()

    def list_pending_receipts(self, *, limit: int = 100) -> list[OperationReceipt]:
        """Devuelve recibos de progreso/resultados todavía no confirmados por el servidor."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit debe ser un entero entre 1 y 1000")
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT r.operation_id, r.instance_id, r.node_id, r.assignment_epoch,
                       r.payload_sha256, r.status, r.result_json
                  FROM operation_receipts AS r
                 WHERE r.node_id = ?
                   AND r.status IN ('running', 'succeeded', 'rejected', 'failed', 'unknown')
                   AND NOT EXISTS (
                       SELECT 1 FROM synced_receipts AS s
                        WHERE s.operation_id = r.operation_id
                   )
                 ORDER BY r.updated_at ASC, r.operation_id ASC
                 LIMIT ?
                """,
                (str(self.local_node_id), limit),
            ).fetchall()
            return [self._receipt(row, duplicate=False) for row in rows]
        finally:
            conn.close()

    def mark_receipt_synced(
        self,
        operation_id: UUID,
        *,
        expected_status: str,
        expected_result: dict[str, Any],
    ) -> bool:
        """Confirma solo la versión exacta del recibo que recibió ACK HTTP 2xx.

        Si el resultado local cambió mientras la petición estaba en vuelo, devuelve
        False y no marca el recibo actual como sincronizado. Así un ACK tardío de una
        versión anterior no puede ocultar progreso/resultado más reciente.
        """
        if not isinstance(operation_id, UUID):
            raise InvalidAgentCommand("operation_id debe ser UUID")
        if not isinstance(expected_status, str) or expected_status not in (self._STATUSES - {"accepted"}):
            raise InvalidAgentCommand("expected_status no es un estado sincronizable")
        if not isinstance(expected_result, dict):
            raise InvalidAgentCommand("expected_result debe ser un objeto JSON")
        expected_json = self._canonical_json(expected_result)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT node_id, status, result_json FROM operation_receipts WHERE operation_id = ?",
                (str(operation_id),),
            ).fetchone()
            if row is None or row["node_id"] != str(self.local_node_id):
                raise UnknownOperation("El recibo no existe en este nodo")
            if row["status"] not in (self._STATUSES - {"accepted"}):
                raise InvalidAgentCommand("Solo progreso o resultado puede marcarse sincronizado")
            if row["status"] != expected_status or row["result_json"] != expected_json:
                conn.commit()
                return False
            conn.execute(
                """
                INSERT INTO synced_receipts(operation_id, synced_at)
                VALUES (?, ?)
                ON CONFLICT(operation_id) DO NOTHING
                """,
                (str(operation_id), self._now()),
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_fence(self, instance_id: UUID) -> tuple[UUID, int] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT node_id, assignment_epoch FROM instance_fences WHERE instance_id = ?",
                (str(instance_id),),
            ).fetchone()
            if row is None:
                return None
            return UUID(row["node_id"]), row["assignment_epoch"]
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _canonical_json(value: dict[str, Any]) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidAgentCommand("El payload debe ser JSON válido y no contener NaN/Infinity") from exc

    def _command_hash(self, command: AgentCommand) -> str:
        if not isinstance(command, AgentCommand):
            raise InvalidAgentCommand("command debe ser AgentCommand")
        if not all(isinstance(value, UUID) for value in (command.operation_id, command.instance_id, command.node_id)):
            raise InvalidAgentCommand("IDs deben ser UUID")
        if command.node_id != self.local_node_id:
            raise InvalidAgentCommand("El comando no está dirigido a este nodo")
        if not isinstance(command.assignment_epoch, int) or isinstance(command.assignment_epoch, bool) or command.assignment_epoch < 1:
            raise InvalidAgentCommand("assignment_epoch debe ser entero positivo")
        if not isinstance(command.lease_expires_at, datetime) or command.lease_expires_at.tzinfo is None or command.lease_expires_at.utcoffset() is None:
            raise InvalidAgentCommand("lease_expires_at debe ser datetime con zona horaria")
        if not isinstance(command.payload, dict):
            raise InvalidAgentCommand("payload debe ser un objeto JSON")
        canonical = {
            "instance_id": str(command.instance_id),
            "node_id": str(command.node_id),
            "assignment_epoch": command.assignment_epoch,
            "lease_expires_at": command.lease_expires_at.astimezone(timezone.utc).isoformat(),
            "payload": command.payload,
        }
        canonical_json = self._canonical_json(canonical)
        if len(canonical_json.encode("utf-8")) > 1_000_000:
            raise InvalidAgentCommand("El payload del comando supera 1 MB")
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def _receipt(self, row: sqlite3.Row, *, duplicate: bool) -> OperationReceipt:
        if UUID(row["node_id"]) != self.local_node_id:
            raise AssignmentOwnerConflict("El recibo pertenece a otro nodo local")
        result = json.loads(row["result_json"]) if row["result_json"] is not None else None
        return OperationReceipt(
            operation_id=UUID(row["operation_id"]),
            instance_id=UUID(row["instance_id"]),
            node_id=UUID(row["node_id"]),
            assignment_epoch=row["assignment_epoch"],
            status=row["status"],
            result=result,
            duplicate=duplicate,
        )
