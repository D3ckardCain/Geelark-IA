"""Arranque explícito y local de la API PC-MASTER."""
from __future__ import annotations
import json, os, stat
from pathlib import Path
from typing import Any
import psycopg
import uvicorn
from psycopg.conninfo import conninfo_to_dict
from .app import create_admin_app

def _required_path(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw: raise RuntimeError(f"Falta configurar {name} con una ruta privada.")
    path = Path(raw).expanduser().resolve()
    if not path.is_file(): raise RuntimeError(f"{name} debe apuntar a un archivo existente.")
    return path

def _required_directory(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw: raise RuntimeError(f"Falta configurar {name} con un directorio privado.")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir(): raise RuntimeError(f"{name} debe apuntar a un directorio existente.")
    return path

def _check_private_file(path: Path, label: str) -> None:
    if os.name == "posix":
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077: raise PermissionError(f"{label} debe tener permisos 0600; permisos actuales: {mode:04o}.")
    # En Windows los bits POSIX no validan ACL NTFS; véase el manual de despliegue.

def _load_password_hash() -> str:
    path = _required_path("GEELARK_ADMIN_OPERATOR_AUTH_FILE")
    _check_private_file(path, "El archivo de hash de operador")
    try: payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise RuntimeError("No se pudo leer la configuración privada del operador.") from exc
    password_hash = payload.get("password_hash") if isinstance(payload, dict) else None
    if not isinstance(password_hash, str) or not password_hash.startswith("pbkdf2_sha256$"): raise RuntimeError("El archivo de operador no contiene un hash PBKDF2 válido.")
    return password_hash

def _database_connector():
    dsn = os.environ.get("GEELARK_ADMIN_DATABASE_URL", "").strip()
    if not dsn: raise RuntimeError("Falta GEELARK_ADMIN_DATABASE_URL; no se usa una base de datos por defecto.")
    try: details = conninfo_to_dict(dsn)
    except Exception as exc: raise RuntimeError("GEELARK_ADMIN_DATABASE_URL no es un DSN PostgreSQL válido.") from exc
    host = details.get("host", "")
    hosts = host.split(",") if host else [""]
    remote = [h for h in hosts if h and h not in {"localhost", "127.0.0.1", "::1"} and not h.startswith("/")]
    if remote and details.get("sslmode") not in {"verify-full", "verify-ca"}: raise RuntimeError("PostgreSQL remoto exige sslmode=verify-full o verify-ca.")
    if details.get("user", "") != "geelark_master_reader": raise RuntimeError("GEELARK_ADMIN_DATABASE_URL debe usar exactamente el rol dedicado geelark_master_reader.")
    def connect():
        return psycopg.connect(dsn, connect_timeout=3, options="-c default_transaction_read_only=on -c statement_timeout=1500 -c lock_timeout=500")
    return connect

def build_app():
    state_dir = _required_directory("GEELARK_ADMIN_STATE_DIR")
    if os.name == "posix" and stat.S_IMODE(state_dir.stat().st_mode) & 0o077: raise PermissionError("GEELARK_ADMIN_STATE_DIR debe tener permisos 0700.")
    return create_admin_app(connect=_database_connector(), operator_password_hash=_load_password_hash(), session_db_path=str(state_dir / "operator-sessions.sqlite3"), secure_cookie=True, panel_path=Path(__file__).with_name("panel.html"))

def main() -> None:
    host = os.environ.get("GEELARK_ADMIN_BIND_HOST", "127.0.0.1").strip()
    try: port = int(os.environ.get("GEELARK_ADMIN_PORT", "8765").strip())
    except ValueError as exc: raise RuntimeError("GEELARK_ADMIN_PORT debe ser un entero entre 1 y 65535.") from exc
    if not 1 <= port <= 65535: raise RuntimeError("GEELARK_ADMIN_PORT debe estar entre 1 y 65535.")
    cert = _required_path("GEELARK_ADMIN_TLS_CERT")
    key = _required_path("GEELARK_ADMIN_TLS_KEY")
    _check_private_file(key, "La clave privada TLS")
    uvicorn.run(build_app(), host=host, port=port, ssl_certfile=str(cert), ssl_keyfile=str(key), proxy_headers=False, access_log=False, server_header=False, date_header=False, workers=1, log_level="warning")

if __name__ == "__main__": main()
