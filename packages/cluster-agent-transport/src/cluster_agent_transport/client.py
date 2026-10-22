"""Cliente HTTPS mínimo con validación estricta de CA y sin seguir redirects."""
from __future__ import annotations

import ipaddress
import json
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from .network import is_private_lan_address


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
        if not isinstance(timeout_seconds, (int, float)) or not 0.1 <= timeout_seconds <= 60:
            raise ValueError("timeout_seconds debe estar entre 0.1 y 60.")
        if isinstance(max_response_bytes, bool) or not 1 <= max_response_bytes <= 16 * 1024 * 1024:
            raise ValueError("max_response_bytes debe estar entre 1 byte y 16 MiB.")
        if not Path(ca_cert).is_file():
            raise ValueError("No existe el certificado público de la CA local.")

        self.base_url = f"https://{parsed.netloc}"
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max_response_bytes
        self.ssl_context = ssl.create_default_context(cafile=ca_cert)
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
        parsed_path = urlsplit(path)
        if (
            not path.startswith("/")
            or path.startswith("//")
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.fragment
            or any(part in {".", ".."} for part in unquote(parsed_path.path).split("/"))
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
            if len(data) > 1_048_576:
                raise ValueError("El cuerpo de la solicitud excede 1 MiB.")
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
