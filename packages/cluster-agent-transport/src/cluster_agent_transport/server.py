"""Configuración explícita del listener HTTPS privado; nunca se inicia al importar."""
from __future__ import annotations

import ipaddress
from pathlib import Path

from .network import is_private_lan_address
from typing import Any


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
    for label, value in (("certificado", certfile), ("clave privada", keyfile)):
        path = Path(value)
        if not path.is_file() or not path.stat().st_size:
            raise TransportConfigurationError(f"No existe el archivo de {label} o está vacío.")
    if Path(certfile).resolve() == Path(keyfile).resolve():
        raise TransportConfigurationError("Certificado y clave privada deben ser archivos distintos.")


def make_uvicorn_config(app: Any, *, host: str, port: int, certfile: str, keyfile: str) -> Any:
    """Construye configuración TLS, pero no ejecuta ni abre el listener."""
    validate_https_listener(host=host, port=port, certfile=certfile, keyfile=keyfile)
    import uvicorn

    return uvicorn.Config(
        app,
        host=host,
        port=port,
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
        access_log=False,
        log_config=None,
    )
