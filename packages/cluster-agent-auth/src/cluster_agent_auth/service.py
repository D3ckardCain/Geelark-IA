"""Operaciones de dominio para credenciales; el transporte HTTPS se configura aparte.

Los métodos reciben una conexión psycopg ya configurada. Cada operación controla
su transacción y nunca registra ni persiste secretos en claro.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from uuid import UUID, uuid4

import psycopg

_TOKEN_RE = re.compile(r"^[0-9a-f]{64}$")
_DEFAULT_ENROLLMENT_TTL = timedelta(minutes=10)
_DEFAULT_CREDENTIAL_TTL = timedelta(days=90)
_MAX_CREDENTIAL_TTL = timedelta(days=365)


def _validate_credential_ttl(ttl: timedelta) -> None:
    if not isinstance(ttl, timedelta) or ttl <= timedelta(0) or ttl > _MAX_CREDENTIAL_TTL:
        raise ValueError("La vigencia de la credencial debe ser mayor que cero y <= 365 días.")


class EnrollmentError(Exception):
    """Enrolamiento inválido, expirado, revocado o ya consumido."""


class AuthenticationError(Exception):
    """Credencial ausente, inválida, revocada, expirada o nodo no aprobado."""


@dataclass(frozen=True)
class IssuedSecret:
    """Secreto mostrado una sola vez al emisor; no debe registrarse en logs."""

    secret: str
    record_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedNode:
    node_id: UUID
    credential_id: UUID
    display_name: str
    admin_state: str


def _new_secret() -> str:
    # token_hex(32) = 32 bytes de entropía criptográfica, codificados en 64 hex.
    return secrets.token_hex(32)


def _valid_secret(secret: str) -> bool:
    return isinstance(secret, str) and _TOKEN_RE.fullmatch(secret) is not None


def _secret_hash(secret: str) -> str:
    if not _valid_secret(secret):
        raise ValueError("El secreto debe ser un token hexadecimal de 256 bits.")
    return hashlib.sha256(secret.encode("ascii")).hexdigest()


def create_enrollment(
    conn: psycopg.Connection,
    expected_node_id: UUID,
    created_by: str,
    ttl: timedelta = _DEFAULT_ENROLLMENT_TTL,
) -> IssuedSecret:
    """Crea un token de alta de un solo uso. El llamador debe proteger el secreto."""
    if not created_by.strip() or len(created_by) > 128:
        raise ValueError("created_by debe tener entre 1 y 128 caracteres.")
    if ttl <= timedelta(0) or ttl > timedelta(hours=1):
        raise ValueError("La vigencia del enrolamiento debe ser mayor que cero y <= 1 hora.")
    secret = _new_secret()
    enrollment_id = uuid4()
    with conn.transaction():
        now = conn.execute("SELECT now()").fetchone()[0]
        expires_at = now + ttl
        conn.execute(
            """
            INSERT INTO geelark_control.node_enrollments
                (enrollment_id, expected_node_id, token_sha256, created_by, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (enrollment_id, expected_node_id, _secret_hash(secret), created_by.strip(), expires_at),
        )
    return IssuedSecret(secret, enrollment_id, expires_at)


def consume_enrollment(
    conn: psycopg.Connection,
    enrollment_token: str,
    display_name: str,
    *,
    agent_version: str | None = None,
    protocol_version: str | None = None,
    credential_ttl: timedelta = _DEFAULT_CREDENTIAL_TTL,
) -> IssuedSecret:
    """Consume atómicamente un alta y crea nodo pending + credencial pending."""
    if not _valid_secret(enrollment_token):
        raise EnrollmentError("Token de enrolamiento inválido.")
    if not display_name.strip() or len(display_name) > 128:
        raise ValueError("display_name debe tener entre 1 y 128 caracteres.")
    _validate_credential_ttl(credential_ttl)
    token_hash = _secret_hash(enrollment_token)
    credential = _new_secret()
    credential_id = uuid4()
    node_id: UUID | None = None
    with conn.transaction():
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        expires_at = now + credential_ttl
        row = conn.execute(
            """
            SELECT enrollment_id, expected_node_id, expires_at
              FROM geelark_control.node_enrollments
             WHERE token_sha256 = %s
               AND consumed_at IS NULL AND revoked_at IS NULL
             FOR UPDATE
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            raise EnrollmentError("Token de enrolamiento inválido, vencido o ya consumido.")
        if row[2] is None or row[2] <= conn.execute("SELECT clock_timestamp()").fetchone()[0]:
            raise EnrollmentError("Token de enrolamiento inválido, vencido o ya consumido.")
        _, node_id, _ = row
        # El UUID esperado no puede registrarse dos veces.
        exists = conn.execute(
            "SELECT 1 FROM geelark_control.nodes WHERE node_id = %s FOR UPDATE",
            (node_id,),
        ).fetchone()
        if exists:
            raise EnrollmentError("El nodo ya existe; se requiere un flujo administrativo de recuperación.")
        # El lock del nodo pudo consumir tiempo; valida el token otra vez y
        # ancla el TTL de la credencial al instante exacto de creación.
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        still_valid = conn.execute(
            "SELECT expires_at > %s FROM geelark_control.node_enrollments WHERE enrollment_id = %s",
            (now, row[0]),
        ).fetchone()
        if still_valid is None or not still_valid[0]:
            raise EnrollmentError("Token de enrolamiento inválido, vencido o ya consumido.")
        expires_at = now + credential_ttl
        conn.execute(
            """
            INSERT INTO geelark_control.nodes
                (node_id, display_name, agent_version, protocol_version, admin_state, health_state)
            VALUES (%s, %s, %s, %s, 'pending', 'unknown')
            """,
            (node_id, display_name.strip(), agent_version, protocol_version),
        )
        conn.execute(
            """
            INSERT INTO geelark_control.node_credentials
                (credential_id, node_id, token_sha256, status, created_at, expires_at)
            VALUES (%s, %s, %s, 'pending', %s, %s)
            """,
            (credential_id, node_id, _secret_hash(credential), now, expires_at),
        )
        # Comprueba una última vez el token tras las inserciones; si venció, la
        # transacción revierte el nodo y la credencial recién creados.
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        still_valid = conn.execute(
            "SELECT expires_at > %s FROM geelark_control.node_enrollments WHERE enrollment_id = %s",
            (now, row[0]),
        ).fetchone()
        if still_valid is None or not still_valid[0]:
            raise EnrollmentError("Token de enrolamiento inválido, vencido o ya consumido.")
        conn.execute(
            "UPDATE geelark_control.node_enrollments SET consumed_at = %s WHERE enrollment_id = %s",
            (now, row[0]),
        )
    return IssuedSecret(credential, credential_id, expires_at)


def authenticate_bearer(conn: psycopg.Connection, secret: str) -> AuthenticatedNode:
    """Autentica solo credenciales activas y nodos aprobados administrativamente."""
    if not _valid_secret(secret):
        raise AuthenticationError("Credencial no válida.")
    with conn.transaction():
        row = conn.execute(
            """
            SELECT n.node_id, c.credential_id, n.display_name, n.admin_state, c.expires_at
              FROM geelark_control.node_credentials AS c
              JOIN geelark_control.nodes AS n ON n.node_id = c.node_id
             WHERE c.token_sha256 = %s
               AND c.status = 'active'
               AND n.admin_state = 'active' AND n.revoked_at IS NULL
             FOR UPDATE OF c
            """,
            (_secret_hash(secret),),
        ).fetchone()
        if row is None:
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")
        database_now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        if row[4] is None or row[4] <= database_now:
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")
        conn.execute(
            "UPDATE geelark_control.node_credentials SET last_used_at = clock_timestamp() WHERE credential_id = %s",
            (row[1],),
        )
    return AuthenticatedNode(*row[:4])


def begin_credential_rotation(
    conn: psycopg.Connection,
    node_id: UUID,
    ttl: timedelta = _DEFAULT_CREDENTIAL_TTL,
) -> IssuedSecret:
    """Emite una credencial pendiente; la antigua continúa activa hasta confirmar."""
    _validate_credential_ttl(ttl)
    secret = _new_secret()
    credential_id = uuid4()
    try:
        with conn.transaction():
            old = conn.execute(
                """
                SELECT credential_id, expires_at FROM geelark_control.node_credentials
                 WHERE node_id = %s AND status = 'active'
                 FOR UPDATE
                """,
                (node_id,),
            ).fetchone()
            if old is None:
                raise AuthenticationError("No existe una credencial activa para rotar.")
            now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
            if old[1] is None or old[1] <= now:
                raise AuthenticationError("No existe una credencial activa para rotar.")
            expires_at = now + ttl
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, expires_at, replaces_credential_id)
                VALUES (%s, %s, %s, 'pending', %s, %s)
                """,
                (credential_id, node_id, _secret_hash(secret), expires_at, old[0]),
            )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name != "one_pending_credential_rotation_per_node":
            raise
        raise AuthenticationError("Ya existe una rotación pendiente para este nodo.") from exc
    return IssuedSecret(secret, credential_id, expires_at)


def rotate_credential(conn: psycopg.Connection, node_id: UUID, new_credential_id: UUID) -> None:
    """Activa una rotación de forma atómica, revocando primero la credencial anterior."""
    with conn.transaction():
        new = conn.execute(
            """
            SELECT replaces_credential_id, expires_at FROM geelark_control.node_credentials
             WHERE credential_id = %s AND node_id = %s
               AND status = 'pending'
             FOR UPDATE
            """,
            (new_credential_id, node_id),
        ).fetchone()
        if new is None or new[0] is None:
            raise AuthenticationError("Rotación pendiente inexistente o vencida.")
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        if new[1] is None or new[1] <= now:
            raise AuthenticationError("Rotación pendiente inexistente o vencida.")
        old_id = new[0]
        revoked = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'revoked', revoked_at = clock_timestamp()
             WHERE credential_id = %s AND node_id = %s AND status = 'active'
            RETURNING revoked_at
            """,
            (old_id, node_id),
        )
        revoked_row = revoked.fetchone()
        if revoked.rowcount != 1 or revoked_row is None:
            raise AuthenticationError("La credencial anterior ya no está activa.")
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        if new[1] <= now:
            raise AuthenticationError("Rotación pendiente inexistente o vencida.")
        activation_time = revoked_row[0]
        updated = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'active', activated_at = %s
             WHERE credential_id = %s AND node_id = %s AND status = 'pending'
               AND expires_at > clock_timestamp()
            """,
            (activation_time, new_credential_id, node_id),
        )
        if updated.rowcount != 1:
            raise AuthenticationError("No se pudo activar la nueva credencial.")


def revoke_credential(conn: psycopg.Connection, node_id: UUID, credential_id: UUID) -> None:
    """Revoca una credencial concreta de un nodo sin revelar el secreto."""
    with conn.transaction():
        updated = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'revoked', revoked_at = clock_timestamp()
             WHERE node_id = %s AND credential_id = %s
               AND status IN ('active', 'pending')
            """,
            (node_id, credential_id),
        )
        if updated.rowcount != 1:
            raise AuthenticationError("Credencial inexistente o ya no revocable.")
