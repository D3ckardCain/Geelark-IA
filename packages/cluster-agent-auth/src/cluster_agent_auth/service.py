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
    expires_at = datetime.now(timezone.utc) + ttl
    with conn.transaction():
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
        now = datetime.now(timezone.utc)
        if row is None or row[2] <= now:
            raise EnrollmentError("Token de enrolamiento inválido, vencido o ya consumido.")
        enrollment_id, node_id, _ = row
        expires_at = now + credential_ttl
        # El UUID esperado no puede registrarse dos veces.
        exists = conn.execute(
            "SELECT 1 FROM geelark_control.nodes WHERE node_id = %s FOR UPDATE",
            (node_id,),
        ).fetchone()
        if exists:
            raise EnrollmentError("El nodo ya existe; se requiere un flujo administrativo de recuperación.")
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
                (credential_id, node_id, token_sha256, status, expires_at)
            VALUES (%s, %s, %s, 'pending', %s)
            """,
            (credential_id, node_id, _secret_hash(credential), expires_at),
        )
        consumed = conn.execute(
            """
            UPDATE geelark_control.node_enrollments
               SET consumed_at = clock_timestamp()
             WHERE enrollment_id = %s
               AND consumed_at IS NULL AND revoked_at IS NULL
               AND expires_at > clock_timestamp()
            """,
            (enrollment_id,),
        )
        if consumed.rowcount != 1:
            raise EnrollmentError("Token de enrolamiento expirado o consumido durante la operación.")
    return IssuedSecret(credential, credential_id, expires_at)


def authenticate_bearer(conn: psycopg.Connection, secret: str) -> AuthenticatedNode:
    """Autentica solo credenciales activas y nodos aprobados administrativamente."""
    if not _valid_secret(secret):
        raise AuthenticationError("Credencial no válida.")
    token_hash = _secret_hash(secret)
    with conn.transaction():
        candidate = conn.execute(
            """
            SELECT credential_id, node_id
              FROM geelark_control.node_credentials
             WHERE token_sha256 = %s
            """,
            (token_hash,),
        ).fetchone()
        if candidate is None:
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")

        # Bloquear primero el nodo y luego la credencial: mismo orden que la rotación.
        node = conn.execute(
            """
            SELECT node_id, display_name, admin_state, revoked_at
              FROM geelark_control.nodes
             WHERE node_id = %s
             FOR UPDATE
            """,
            (candidate[1],),
        ).fetchone()
        if node is None or node[2] != "active" or node[3] is not None:
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")

        credential = conn.execute(
            """
            SELECT credential_id, status, expires_at
              FROM geelark_control.node_credentials
             WHERE credential_id = %s AND node_id = %s AND token_sha256 = %s
             FOR UPDATE
            """,
            (candidate[0], candidate[1], token_hash),
        ).fetchone()
        if (
            credential is None
            or credential[1] != "active"
            or credential[2] <= datetime.now(timezone.utc)
        ):
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")

        updated = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET last_used_at = clock_timestamp()
             WHERE credential_id = %s
               AND status = 'active'
               AND expires_at > clock_timestamp()
            """,
            (credential[0],),
        )
        if updated.rowcount != 1:
            raise AuthenticationError("Credencial no válida o nodo no autorizado.")
    return AuthenticatedNode(node[0], credential[0], node[1], node[2])


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
            node = conn.execute(
                """
                SELECT 1 FROM geelark_control.nodes
                 WHERE node_id = %s AND admin_state = 'active' AND revoked_at IS NULL
                 FOR UPDATE
                """,
                (node_id,),
            ).fetchone()
            if node is None:
                raise AuthenticationError("El nodo no está activo o fue revocado.")
            old = conn.execute(
                """
                SELECT credential_id, expires_at FROM geelark_control.node_credentials
                 WHERE node_id = %s AND status = 'active'
                 FOR UPDATE
                """,
                (node_id,),
            ).fetchone()
            if old is None or old[1] <= datetime.now(timezone.utc):
                raise AuthenticationError("No existe una credencial activa y vigente para rotar.")
            expires_at = datetime.now(timezone.utc) + ttl
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
        node = conn.execute(
            """
            SELECT 1 FROM geelark_control.nodes
             WHERE node_id = %s AND admin_state = 'active' AND revoked_at IS NULL
             FOR UPDATE
            """,
            (node_id,),
        ).fetchone()
        if node is None:
            raise AuthenticationError("El nodo no está activo o fue revocado.")
        new = conn.execute(
            """
            SELECT replaces_credential_id, expires_at FROM geelark_control.node_credentials
             WHERE credential_id = %s AND node_id = %s AND status = 'pending'
             FOR UPDATE
            """,
            (new_credential_id, node_id),
        ).fetchone()
        now = datetime.now(timezone.utc)
        if new is None or new[0] is None or new[1] <= now:
            raise AuthenticationError("Rotación pendiente inexistente o vencida.")
        old_id = new[0]
        revoked = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'revoked', revoked_at = clock_timestamp()
             WHERE credential_id = %s AND node_id = %s
               AND status = 'active' AND expires_at > clock_timestamp()
            """,
            (old_id, node_id),
        )
        if revoked.rowcount != 1:
            raise AuthenticationError("La credencial anterior ya no está activa.")
        updated = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'active', activated_at = clock_timestamp()
             WHERE credential_id = %s AND node_id = %s
               AND status = 'pending' AND expires_at > clock_timestamp()
            """,
            (new_credential_id, node_id),
        )
        if updated.rowcount != 1:
            raise AuthenticationError("No se pudo activar la nueva credencial.")


def revoke_credential(conn: psycopg.Connection, node_id: UUID, credential_id: UUID) -> None:
    """Revoca una credencial concreta de un nodo sin revelar el secreto."""
    with conn.transaction():
        updated = conn.execute(
            """
            UPDATE geelark_control.node_credentials
               SET status = 'revoked', revoked_at = now()
             WHERE node_id = %s AND credential_id = %s
               AND status IN ('active', 'pending')
            """,
            (node_id, credential_id),
        )
        if updated.rowcount != 1:
            raise AuthenticationError("Credencial inexistente o ya no revocable.")
