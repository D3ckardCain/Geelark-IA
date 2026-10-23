"""Configuración explícita del listener HTTPS privado; nunca se inicia al importar."""
from __future__ import annotations

import ipaddress
import os
import stat
from pathlib import Path

from typing import Any

from .network import is_private_lan_address


class TransportConfigurationError(ValueError):
    """Configuración de escucha insegura o incompleta."""


def validate_https_listener(*, host: str, port: int, certfile: str, keyfile: str) -> None:
    """Exige IP literal privada/loopback y material TLS existente.

    No admite 0.0.0.0, nombres DNS ni fallback HTTP. El llamador debe
    distribuir la CA raíz local a los agentes por un canal de confianza.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise TransportConfigurationError("El host debe ser una IP literal privada o loopback.") from exc

    if address.is_unspecified or not is_private_lan_address(address):
        raise TransportConfigurationError("El listener solo puede enlazarse a una IP privada/loopback.")
    if isinstance(port, bool) or not 1 <= port <= 65535:
        raise TransportConfigurationError("El puerto debe estar entre 1 y 65535.")
    cert_path = Path(certfile).expanduser().resolve()
    key_path = Path(keyfile).expanduser().resolve()
    for label, path in (("certificado", cert_path), ("clave privada", key_path)):
        if not path.is_file() or not path.stat().st_size:
            raise TransportConfigurationError(f"No existe el archivo de {label} o está vacío.")
        if os.name == "posix":
            info = path.stat()
            parent_info = path.parent.stat()
            if info.st_uid not in {os.geteuid(), 0}:
                raise TransportConfigurationError(
                    f"El archivo de {label} debe pertenecer al usuario actual o a root."
                )
            if parent_info.st_uid not in {os.geteuid(), 0}:
                raise TransportConfigurationError(
                    f"El directorio contenedor de {label} debe pertenecer al usuario actual o a root."
                )
            if stat.S_IMODE(parent_info.st_mode) & 0o022:
                raise TransportConfigurationError(
                    f"El directorio contenedor de {label} no puede permitir escritura a grupo u otros."
                )
            mode = stat.S_IMODE(info.st_mode)
            if label == "clave privada":
                if info.st_uid != os.geteuid() or mode & 0o077:
                    raise TransportConfigurationError(
                        "La clave privada TLS debe pertenecer al usuario del proceso y no conceder permisos a grupo/otros."
                    )
            elif mode & 0o022:
                raise TransportConfigurationError(
                    "El certificado TLS no puede ser modificable por grupo u otros."
                )
    if cert_path == key_path:
        raise TransportConfigurationError("Certificado y clave privada deben ser archivos distintos.")


def make_uvicorn_config(app: Any, *, host: str, port: int, certfile: str, keyfile: str) -> Any:
    """Construye configuración TLS, pero no ejecuta ni abre el listener."""
    cert_path = str(Path(certfile).expanduser().resolve())
    key_path = str(Path(keyfile).expanduser().resolve())
    validate_https_listener(host=host, port=port, certfile=cert_path, keyfile=key_path)
    import uvicorn

    return uvicorn.Config(
        app,
        host=host,
        port=port,
        ssl_certfile=cert_path,
        ssl_keyfile=key_path,
        access_log=False,
        log_config=None,
    )
