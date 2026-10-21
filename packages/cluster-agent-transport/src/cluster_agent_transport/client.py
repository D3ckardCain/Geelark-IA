"""Cliente HTTPS mínimo con validación estricta de CA y sin seguir redirects."""
from __future__ import annotations

import ipaddress
import json
import os
import ssl
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from .network import is_private_lan_address


MAX_REQUEST_BYTES = 16_384


class AgentTransportError(Exception):
    """Error de transporte sin exponer secretos ni detalles TLS al llamador."""


@dataclass(frozen=True)
class AgentResponse:
    status: int
    body: bytes
    content_type: str | None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AgentHTTPSClient:
    """Cliente sin fallback HTTP, con CA explícita, timeout y límites de respuesta."""

    def __init__(
        self,
        *,
        base_url: str,
        ca_cert: str,
        timeout_seconds: float = 5.0,
        max_response_bytes: int = 1_048_576,
    ) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("base_url debe ser HTTPS y no contener credenciales.")
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("base_url solo debe contener esquema, host y puerto.")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError as exc:
            raise ValueError("El host del controlador debe ser una IP literal privada/loopback.") from exc
        if address.is_unspecified or not is_private_lan_address(address):
            raise ValueError("El controlador debe estar en una IP privada/loopback.")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not 0.1 <= timeout_seconds <= 60
        ):
            raise ValueError("timeout_seconds debe estar entre 0.1 y 60.")
        if (
            isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or not 1 <= max_response_bytes <= 16 * 1024 * 1024
        ):
            raise ValueError("max_response_bytes debe ser un entero entre 1 byte y 16 MiB.")
        ca_path = Path(ca_cert).expanduser().resolve()
        if not ca_path.is_file():
            raise ValueError("No existe el certificado público de la CA local.")
        if os.name == "posix":
            ca_info = ca_path.stat()
            if ca_info.st_uid not in {os.geteuid(), 0}:
                raise ValueError("El archivo CA debe pertenecer al usuario actual o a root.")
            ca_mode = stat.S_IMODE(ca_info.st_mode)
            if ca_mode & 0o022:
                raise ValueError("El archivo CA no puede ser modificable por grupo u otros.")
            ca_parent_info = ca_path.parent.stat()
            if ca_parent_info.st_uid not in {os.geteuid(), 0}:
                raise ValueError(
                    "El directorio contenedor del archivo CA debe pertenecer al usuario actual o a root."
                )
            ca_parent_mode = stat.S_IMODE(ca_parent_info.st_mode)
            if ca_parent_mode & 0o022:
                raise ValueError(
                    "El directorio contenedor del archivo CA no puede permitir escritura a grupo u otros."
                )

        self.base_url = f"https://{parsed.netloc}"
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max_response_bytes
        # Load the canonical, checked trust anchor rather than an unchecked alias.
        self.ssl_context = ssl.create_default_context(cafile=str(ca_path))
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.check_hostname = True
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        self._opener = build_opener(HTTPSHandler(context=self.ssl_context), _NoRedirect())

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> AgentResponse:
        method = method.upper()
        if method not in {"GET", "POST", "PUT"}:
            raise ValueError("Método HTTP no permitido.")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in path):
            raise ValueError(
                "La ruta debe ser local al controlador; no se permiten URL absolutas, caracteres de control, backslashes ni traversal."
            )
        parsed_path = urlsplit(path)
        decoded_path = parsed_path.path
        # Reject traversal after repeated URL decoding, including encoded backslashes.
        for _ in range(8):
            if "\\" in decoded_path:
                raise ValueError(
                    "La ruta debe ser local al controlador; no se permiten URL absolutas, caracteres de control, backslashes ni traversal."
                )
            normalized_parts = decoded_path.split("/")
            if any(part in {".", ".."} for part in normalized_parts):
                raise ValueError(
                    "La ruta debe ser local al controlador; no se permiten URL absolutas, caracteres de control, backslashes ni traversal."
                )
            next_path = unquote(decoded_path)
            if next_path == decoded_path:
                break
            decoded_path = next_path
        else:
            raise ValueError("La ruta contiene codificación anidada no permitida.")

        if (
            not path.startswith("/")
            or path.startswith("//")
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.fragment
        ):
            raise ValueError("La ruta debe ser local al controlador; no se permiten URL absolutas ni traversal.")

        request_headers = {"Accept": "application/json"}
        for name, value in (headers or {}).items():
            if not name or any(ch in name + value for ch in "\r\n"):
                raise ValueError("Cabecera HTTP inválida.")
            if name.lower() in {"host", "content-length", "connection", "transfer-encoding"}:
                raise ValueError("No se permite sobrescribir cabeceras de transporte.")
            request_headers[name] = value

        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
            if len(data) > MAX_REQUEST_BYTES:
                raise ValueError("El cuerpo de la solicitud excede 16 KiB, límite del servidor agente.")
            request_headers["Content-Type"] = "application/json"

        request = Request(self.base_url + path, data=data, headers=request_headers, method=method)
        try:
            response = self._opener.open(request, timeout=self.timeout_seconds)
        except HTTPError as exc:
            # HTTPError también representa respuestas 4xx/5xx y redirects no seguidos.
            response = exc
        except (URLError, TimeoutError, ssl.SSLError, OSError) as exc:
            raise AgentTransportError("Falló la conexión HTTPS verificada.") from None

        try:
            body = response.read(self.max_response_bytes + 1)
            if len(body) > self.max_response_bytes:
                raise AgentTransportError("La respuesta excede el límite configurado.")
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            if 300 <= status < 400:
                raise AgentTransportError("El controlador intentó redirigir la petición; no se siguió el redirect.")
            return AgentResponse(
                status=status,
                body=body,
                content_type=response.headers.get("Content-Type"),
            )
        finally:
            response.close()
