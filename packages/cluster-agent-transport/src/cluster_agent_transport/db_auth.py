"""Adaptador PostgreSQL para autenticar credenciales activas y pendientes."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from uuid import UUID

import psycopg

from .policy import AgentPrincipal

_TOKEN_RE = re.compile(r"^[0-9a-f]{64}$")


class InvalidAgentCredential(Exception):
    """Credencial desconocida, vencida, revocada o inconsistente."""


def make_database_authenticator(
    connect: Callable[[], psycopg.Connection],
) -> Callable[[str], AgentPrincipal]:
    """Devuelve una función autenticadora sin guardar ni registrar el token.

    Se acepta estado pending únicamente si tanto nodo como credencial están
    pending. La autorización por operación se aplica después, en cada ruta.
    """
    def authenticate(secret: str) -> AgentPrincipal:
        if not isinstance(secret, str) or not _TOKEN_RE.fullmatch(secret):
            raise InvalidAgentCredential("Credencial no válida.")
        token_hash = hashlib.sha256(secret.encode("ascii")).hexdigest()
        with connect() as conn:
            row = conn.execute(
                """
                SELECT n.node_id, c.credential_id, n.admin_state, c.status, c.expires_at, now() AS authorized_at
                  FROM geelark_control.node_credentials AS c
                  JOIN geelark_control.nodes AS n ON n.node_id = c.node_id
                 WHERE c.token_sha256 = %s
                   AND c.expires_at > now()
                   AND c.status IN ('active', 'pending')
                   AND n.admin_state IN ('active', 'pending')
                   AND n.revoked_at IS NULL
                   AND (
                     (c.status = 'active' AND n.admin_state = 'active')
                     OR
                     (c.status = 'pending' AND n.admin_state = 'pending')
                   )
                """,
                (token_hash,),
            ).fetchone()
        if row is None:
            raise InvalidAgentCredential("Credencial no válida o nodo no autorizado.")
        return AgentPrincipal(
            node_id=str(row[0]),
            credential_id=str(row[1]),
            admin_state=row[2],
            credential_status=row[3],
            credential_expires_at=row[4],
            authorized_at=row[5],
        )
    return authenticate
