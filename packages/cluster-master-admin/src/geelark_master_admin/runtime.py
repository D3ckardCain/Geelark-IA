"""Arranque explícito y local de la API PC-MASTER."""
from __future__ import annotations

import ipaddress
import json
import os
import stat
from pathlib import Path
from typing import Any

import psycopg
import uvicorn
from psycopg.conninfo import conninfo_to_dict

from .app import create_admin_app
from .auth import _restrict_windows_acl, _verify_windows_acl_no_untrusted_writers


def _required_path(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise RuntimeError(f"Falta configurar {name} con una ruta privada.")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"{name} debe apuntar a un archivo existente.")
    return path


def _required_directory(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise RuntimeError(f"Falta configurar {name} con un directorio privado.")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise RuntimeError(f"{name} debe apuntar a un directorio existente.")
    return path


def _check_private_file(path: Path, label: str) -> None:
    if os.name == "posix":
        info = path.stat()
        if info.st_uid != os.geteuid():
            raise PermissionError(f"{label} debe pertenecer al usuario que ejecuta PC-MASTER.")
        mode = stat.S_IMODE(info.st_mode)
        if not mode & 0o400 or mode & 0o077:
            raise PermissionError(
                f"{label} debe ser legible solo por el usuario (por ejemplo, 0600 o 0400); "
                f"permisos actuales: {mode:04o}."
            )
        parent_info = path.parent.stat()
        if parent_info.st_uid not in {os.geteuid(), 0}:
            raise PermissionError(
                f"El directorio contenedor de {label} debe pertenecer al usuario actual o a root."
            )
        parent_mode = stat.S_IMODE(parent_info.st_mode)
        if parent_mode & 0o022:
            raise PermissionError(
                f"El directorio contenedor de {label} no puede permitir escritura a grupo u otros."
            )
    elif os.name == "nt":
        _restrict_windows_acl(path, directory=False)


def _load_password_hash() -> str:
    path = _required_path("GEELARK_ADMIN_OPERATOR_AUTH_FILE")
    _check_private_file(path, "El archivo de hash de operador")
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "No se pudo leer la configuración privada del operador."
        ) from exc
    password_hash = payload.get("password_hash") if isinstance(payload, dict) else None
    if not isinstance(password_hash, str) or not password_hash.startswith("pbkdf2_sha256$"):
        raise RuntimeError("El archivo de operador no contiene un hash PBKDF2 válido.")
    return password_hash


def _database_connector():
    dsn = os.environ.get("GEELARK_ADMIN_DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError(
            "Falta GEELARK_ADMIN_DATABASE_URL; no se usa una base de datos por defecto."
        )
    if os.environ.get("PGSSLKEYLOGFILE", "").strip():
        raise RuntimeError(
            "No se permite registrar claves de sesión TLS; elimina PGSSLKEYLOGFILE."
        )
    try:
        details = conninfo_to_dict(dsn)
    except Exception as exc:
        raise RuntimeError(
            "GEELARK_ADMIN_DATABASE_URL no es un DSN PostgreSQL válido."
        ) from exc

    if details.get("sslkeylogfile"):
        raise RuntimeError(
            "No se permite registrar claves de sesión TLS mediante sslkeylogfile."
        )

    # No se admiten perfiles libpq externos: podrían ocultar host/SSL reales
    # en un archivo de servicio y eludir la validación de este runtime.
    if (
        details.get("service")
        or details.get("servicefile")
        or os.environ.get("PGSERVICE", "").strip()
        or os.environ.get("PGSERVICEFILE", "").strip()
    ):
        raise RuntimeError(
            "No se admiten perfiles libpq externos (service/servicefile/PGSERVICE); "
            "configura los parámetros de conexión directamente."
        )

    raw_host = details.get("host") or ""
    hosts = [item.strip() for item in raw_host.split(",")] if raw_host else []
    if any(not item for item in hosts):
        raise RuntimeError("GEELARK_ADMIN_DATABASE_URL no puede contener entradas host= vacías.")

    raw_hostaddr = details.get("hostaddr") or ""
    hostaddrs = [item.strip() for item in raw_hostaddr.split(",")] if raw_hostaddr else []
    if any(not item for item in hostaddrs):
        raise RuntimeError("GEELARK_ADMIN_DATABASE_URL no puede contener entradas hostaddr= vacías.")
    if not hosts and not hostaddrs:
        raise RuntimeError(
            "GEELARK_ADMIN_DATABASE_URL debe definir host= o hostaddr= explícito; no se usan valores por defecto de libpq."
        )
    if os.environ.get("PGHOSTADDR", "").strip() and not details.get("hostaddr"):
        raise RuntimeError(
            "PGHOSTADDR no se admite sin hostaddr explícito en GEELARK_ADMIN_DATABASE_URL."
        )
    if not details.get("dbname"):
        raise RuntimeError("GEELARK_ADMIN_DATABASE_URL debe definir dbname explícito.")
    if os.environ.get("PGPORT", "").strip() and not details.get("port"):
        raise RuntimeError("PGPORT no se admite sin port explícito en GEELARK_ADMIN_DATABASE_URL.")

    def is_loopback_host(item: str) -> bool:
        if item.lower() == "localhost" or item.startswith("/"):
            return True
        try:
            return ipaddress.ip_address(item).is_loopback
        except ValueError:
            return False

    if hostaddrs and hosts and len(hostaddrs) != len(hosts):
        raise RuntimeError(
            "hostaddr debe tener la misma cantidad de entradas IP que host para validar cada destino."
        )

    parsed_hostaddrs = []
    for index, address in enumerate(hostaddrs):
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError as exc:
            raise RuntimeError("hostaddr solo admite direcciones IP válidas.") from exc
        parsed_hostaddrs.append(parsed_address)
        if hosts and is_loopback_host(hosts[index]) and not parsed_address.is_loopback:
            raise RuntimeError(
                "hostaddr remoto no puede emparejarse con host loopback; usa host DNS/IP no-loopback."
            )

    remote = any(not is_loopback_host(item) for item in hosts)
    if any(not address.is_loopback for address in parsed_hostaddrs):
        remote = True

    if remote and os.environ.get("PGSSLROOTCERT", "").strip() and not details.get("sslrootcert"):
        raise RuntimeError(
            "PostgreSQL remoto requiere sslrootcert explícito si PGSSLROOTCERT está definido."
        )
    if remote and details.get("sslmode") != "verify-full":
        raise RuntimeError(
            "PostgreSQL remoto exige sslmode=verify-full y verificación del nombre del servidor."
        )
    if remote and not hosts:
        raise RuntimeError(
            "PostgreSQL remoto requiere host= explícito para verificar el nombre del servidor; hostaddr por sí solo no basta."
        )
    if remote:
        non_loopback_hosts = []
        for item in hosts:
            if item.startswith("/"):
                continue
            if item.lower() == "localhost":
                continue
            try:
                is_loopback_host = ipaddress.ip_address(item).is_loopback
            except ValueError:
                is_loopback_host = False
            if not is_loopback_host:
                non_loopback_hosts.append(item)
        if not non_loopback_hosts:
            raise RuntimeError(
                "PostgreSQL remoto requiere un host DNS/IP no-loopback; no se acepta verificar un destino remoto como localhost."
            )

    raw_sslrootcert = details.get("sslrootcert")
    sslrootcert_path: str | None = None
    if remote and not raw_sslrootcert:
        raise RuntimeError(
            "PostgreSQL remoto exige sslrootcert explícito; no se usa la CA predeterminada de libpq."
        )
    if raw_sslrootcert:
        ca_path = Path(raw_sslrootcert).expanduser().resolve()
        if not ca_path.is_file():
            raise RuntimeError("sslrootcert debe apuntar a un archivo CA existente.")
        if os.name == "posix":
            ca_info = ca_path.stat()
            if ca_info.st_uid not in {os.geteuid(), 0}:
                raise RuntimeError(
                    "El archivo sslrootcert debe pertenecer al usuario actual o a root."
                )
            ca_mode = stat.S_IMODE(ca_info.st_mode)
            if ca_mode & 0o022:
                raise RuntimeError(
                    "El archivo sslrootcert no puede ser modificable por grupo u otros."
                )
            ca_parent_info = ca_path.parent.stat()
            if ca_parent_info.st_uid not in {os.geteuid(), 0}:
                raise RuntimeError(
                    "El directorio contenedor de sslrootcert debe pertenecer al usuario actual o a root."
                )
            ca_parent_mode = stat.S_IMODE(ca_parent_info.st_mode)
            if ca_parent_mode & 0o022:
                raise RuntimeError(
                    "El directorio contenedor de sslrootcert no puede permitir escritura a grupo u otros."
                )
        elif os.name == "nt":
            _verify_windows_acl_no_untrusted_writers(ca_path)
            _verify_windows_acl_no_untrusted_writers(ca_path.parent)
        sslrootcert_path = str(ca_path)

    if details.get("user", "") != "geelark_master_reader":
        raise RuntimeError(
            "GEELARK_ADMIN_DATABASE_URL debe usar exactamente el rol dedicado "
            "geelark_master_reader."
        )

    if os.environ.get("PGPASSWORD", "").strip():
        raise RuntimeError("No se admite PGPASSWORD; usa un archivo PGPASSFILE protegido.")

    if details.get("passfile"):
        raise RuntimeError(
            "No se admite passfile dentro de GEELARK_ADMIN_DATABASE_URL; usa PGPASSFILE explícito."
        )

    # libpq may otherwise fall back to a platform-default password file whose
    # location and permissions are outside this service's explicit configuration.
    raw_passfile = os.environ.get("PGPASSFILE", "").strip()
    if not raw_passfile:
        raise RuntimeError("Falta configurar PGPASSFILE con una ruta privada explícita.")
    if Path(raw_passfile).expanduser().is_symlink():
        raise PermissionError("PGPASSFILE no puede ser un enlace simbólico.")
    passfile = _required_path("PGPASSFILE")
    _check_private_file(passfile, "El archivo de contraseñas PostgreSQL (PGPASSFILE)")
    # Ensure libpq opens the exact canonical path whose owner and permissions
    # were inspected above, not an unchecked alias from the environment.
    os.environ["PGPASSFILE"] = str(passfile)

    if details.get("password"):
        raise RuntimeError(
            "No incluyas la contraseña en GEELARK_ADMIN_DATABASE_URL; "
            "usa un archivo PGPASSFILE protegido."
        )

    def connect():
        connect_options = {
            # libpq may prefer GSS encryption over TLS even with sslmode=verify-full.
            "gssencmode": "disable",
            "connect_timeout": 3,
            "options": (
                "-c default_transaction_read_only=on "
                "-c statement_timeout=1500 "
                "-c lock_timeout=500 "
                "-c idle_in_transaction_session_timeout=5000"
            ),
        }
        if sslrootcert_path is not None:
            # Pin the canonical CA file that was checked above.
            connect_options["sslrootcert"] = sslrootcert_path
        return psycopg.connect(dsn, **connect_options)

    return connect


def build_app():
    """Construye la aplicación sin abrir sockets ni consultar PostgreSQL."""
    state_dir = _required_directory("GEELARK_ADMIN_STATE_DIR")
    if os.name == "posix" and stat.S_IMODE(state_dir.stat().st_mode) & 0o077:
        raise PermissionError("GEELARK_ADMIN_STATE_DIR debe tener permisos 0700.")

    return create_admin_app(
        connect=_database_connector(),
        operator_password_hash=_load_password_hash(),
        session_db_path=str(state_dir / "operator-sessions.sqlite3"),
        secure_cookie=True,
        panel_path=Path(__file__).with_name("panel.html"),
    )


def main() -> None:
    """Arranque explícito con TLS; el valor predeterminado es loopback."""
    host = os.environ.get("GEELARK_ADMIN_BIND_HOST", "127.0.0.1").strip()
    try:
        port = int(os.environ.get("GEELARK_ADMIN_PORT", "8765").strip())
    except ValueError as exc:
        raise RuntimeError(
            "GEELARK_ADMIN_PORT debe ser un entero entre 1 y 65535."
        ) from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("GEELARK_ADMIN_PORT debe estar entre 1 y 65535.")

    try:
        loopback = host.lower() == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if not loopback and os.environ.get("GEELARK_ADMIN_ALLOW_REMOTE") != "1":
        raise RuntimeError(
            "El bind remoto está bloqueado por defecto. No lo habilites sin revisión "
            "de certificado, firewall y acceso."
        )

    cert = _required_path("GEELARK_ADMIN_TLS_CERT")
    key = _required_path("GEELARK_ADMIN_TLS_KEY")
    _check_private_file(key, "La clave privada TLS")

    uvicorn.run(
        build_app(),
        host=host,
        port=port,
        ssl_certfile=str(cert),
        ssl_keyfile=str(key),
        proxy_headers=False,
        access_log=False,
        server_header=False,
        date_header=False,
        workers=1,
        timeout_keep_alive=5,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
