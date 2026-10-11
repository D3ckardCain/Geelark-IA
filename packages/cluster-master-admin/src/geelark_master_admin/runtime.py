"""Arranque explícito y local de la API PC-MASTER.

No se ejecuta al importar. Requiere TLS configurado y credenciales por variables
de entorno/rutas privadas; no lee secretos del repositorio.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import psycopg
import uvicorn
from psycopg.conninfo import conninfo_to_dict

from .app import create_admin_app


def _required_path(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise RuntimeError(f"Falta configurar {name} con una ruta privada.")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"{name} debe apuntar a un archivo existente.")
    return path


def _check_private_file(path: Path, label: str) -> None:
    if os.name == "posix":
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise PermissionError(f"{label} debe tener permisos 0600; permisos actuales: {mode:04o}.")
    # En Windows, los bits POSIX no prueban que la ACL NTFS sea privada.
    # El manual exige ACL limitada al usuario que ejecuta PC-MASTER.


def _load_password_hash() -> str:
    path = _required_path("GEELARK_ADMIN_OPERATOR_AUTH_FILE")
    _check_private_file(path, "El archivo de hash de operador")
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("No se pudo leer la configuración privada del operador.") from exc
    password_hash = payload.get("password_hash") if isinstance(payload, dict) else None
    if not isinstance(password_hash, str) or not password_hash.startswith("pbkdf2_sha256$"):
        raise RuntimeError("El archivo de operador no contiene un hash PBKDF2 válido.")
    return password_hash


def _database_connector():
    dsn = os.environ.get("GEELARK_ADMIN_DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError("Falta GEELARK_ADMIN_DATABASE_URL; no se usa una base de datos por defecto.")
    try:
        details = conninfo_to_dict(dsn)
    except Exception as exc:
        raise RuntimeError("GEELARK_ADMIN_DATABASE_URL no es un DSN PostgreSQL válido.") from exc
    host = details.get("host", "")
    host_items = host.split(",") if host else [""]
    remote_hosts = [item for item in host_items if item and item not in {"localhost", "127.0.0.1", "::1"} and not item.startswith("/")]
    sslmode = details.get("sslmode", "")
    if remote_hosts and sslmode not in {"verify-full", "verify-ca"}:
        raise RuntimeError("PostgreSQL remoto exige sslmode=verify-full (recomendado) o verify-ca.")
    if details.get("user", "").lower() in {"postgres", "root", "admin", "supabase_admin"}:
        raise RuntimeError("No se permite usar una cuenta PostgreSQL privilegiada; configure el rol dedicado SELECT-only.")
    def connect():
        return psycopg.connect(
            dsn,
            connect_timeout=3,
            options="-c default_transaction_read_only=on -c statement_timeout=1500 -c lock_timeout=500",
        )
    return connect


def build_app():
    """Construye la aplicación sin abrir sockets ni realizar consultas a PostgreSQL."""
    state_dir = _required_path("GEELARK_ADMIN_STATE_DIR")
    if not state_dir.is_dir():
        raise RuntimeError("GEELARK_ADMIN_STATE_DIR debe ser un directorio existente y privado.")
    if os.name == "posix" and stat.S_IMODE(state_dir.stat().st_mode) & 0o077:
        raise PermissionError("GEELARK_ADMIN_STATE_DIR debe tener permisos 0700.")
    return create_admin_app(
        connect=_database_connector(),
        operator_password_hash=_load_password_hash(),
        session_db_path=str(state_dir / "operator-sessions.sqlite3"),
        secure_cookie=True,
    )


def main() -> None:
    """Arranque explícito con TLS; el valor predeterminado solo escucha en loopback."""
    host = os.environ.get("GEELARK_ADMIN_BIND_HOST", "127.0.0.1").strip()
    port_raw = os.environ.get("GEELARK_ADMIN_PORT", "8765").strip()
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError("GEELARK_ADMIN_PORT debe ser un entero entre 1 y 65535.") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("GEELARK_ADMIN_PORT debe estar entre 1 y 65535.")
    cert = _required_path("GEELARK_ADMIN_TLS_CERT")
    key = _required_path("GEELARK_ADMIN_TLS_KEY")
    _check_private_file(key, "La clave privada TLS")
    app = build_app()
    # Sin proxy headers: el esquema HTTPS lo proporciona Uvicorn mediante TLS,
    # no un encabezado reenviado que un cliente pudiera falsificar.
    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_certfile=str(cert),
        ssl_keyfile=str(key),
        proxy_headers=False,
        access_log=False,
        server_header=False,
        date_header=False,
        workers=1,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
