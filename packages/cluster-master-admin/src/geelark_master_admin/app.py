"""API HTTP administrativa de solo lectura para PC-MASTER.

La fábrica no abre sockets. El proceso anfitrión debe montarla detrás de HTTPS,
en el mismo origen del panel, y proporcionar una conexión PostgreSQL SELECT-only.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from geelark_cluster_persistence.status_snapshot import build_status_snapshot
from .auth import LoginRateLimiter, SessionStore, verify_operator_password

SESSION_COOKIE = "__Host-geelark_master_session"
MAX_SNAPSHOTS = 500
MAX_RESPONSE_BYTES = 1_048_576


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=1024)


class RequireHTTPSMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and scope.get("scheme") != "https":
            response = JSONResponse({"error": {"code": "HTTPS_REQUIRED"}}, status_code=426)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class BodyLimitMiddleware:
    """Limita cuerpos ASGI incluso si no se declara Content-Length."""

    def __init__(self, app: Any, max_bytes: int = 16_384) -> None:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise ValueError("max_bytes debe ser un entero positivo")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                if int(raw_length) > self.max_bytes:
                    await self._respond(scope, receive, send, 413, "BODY_TOO_LARGE")
                    return
            except ValueError:
                await self._respond(scope, receive, send, 400, "INVALID_CONTENT_LENGTH")
                return

        chunks: list[bytes] = []
        total = 0
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > self.max_bytes:
                await self._respond(scope, receive, send, 413, "BODY_TOO_LARGE")
                return
            chunks.append(chunk)
            more = message.get("more_body", False)

        body = b"".join(chunks)
        delivered = False

        async def replay_receive() -> dict[str, Any]:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            # Preserve the original ASGI receive channel after replaying the
            # complete buffered body so the app can observe http.disconnect.
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _respond(
        scope: dict[str, Any], receive: Any, send: Any, status: int, code: str
    ) -> None:
        response = JSONResponse({"error": {"code": code}}, status_code=status)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        await response(scope, receive, send)


def _security_headers(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response


def _panel_csp(panel_path: Path) -> str:
    """Permite únicamente los bloques JS inline exactos incluidos en el panel versionado."""
    source = panel_path.read_text(encoding="utf-8")
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", source, flags=re.IGNORECASE | re.DOTALL)
    hashes = []
    for script in scripts:
        digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
        hashes.append("'sha256-" + digest + "'")
    script_policy = " ".join(["'self'", *hashes])
    return (
        "default-src 'self'; script-src " + script_policy +
        "; script-src-attr 'none'; style-src 'self' 'unsafe-inline'; connect-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'"
    )


def _same_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    return bool(origin and origin == request.base_url.scheme.rstrip(":/") + "://" + request.url.netloc)


def _read_snapshots(connect: Callable[[], Any]) -> tuple[str, list[dict[str, Any]]]:
    """Una consulta SELECT acotada; no lee payloads de tareas ni registros arbitrarios."""
    now = datetime.now(timezone.utc)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT node_id, display_name, admin_state, health_state AS reported_health_state,
                   agent_version, last_seen_at, capabilities, module_reports, revoked_at
              FROM geelark_control.nodes
             ORDER BY display_name ASC NULLS LAST, node_id ASC
             LIMIT %s
            """,
            (MAX_SNAPSHOTS,),
        ).fetchall()
    snapshots = [build_status_snapshot(row, now=now) for row in rows]
    return now.isoformat().replace("+00:00", "Z"), [item for item in snapshots if item is not None]


def create_admin_app(
    *,
    connect: Callable[[], Any],
    operator_password_hash: str,
    session_db_path: str,
    secure_cookie: bool = True,
    rate_limiter: LoginRateLimiter | None = None,
    panel_path: str | Path | None = None,
) -> FastAPI:
    """Crea rutas admin con autenticación local; no inicia listener ni hace deploy."""
    if not isinstance(operator_password_hash, str) or not operator_password_hash.startswith("pbkdf2_sha256$"):
        raise ValueError("operator_password_hash debe ser un hash PBKDF2 generado localmente.")
    sessions = SessionStore(session_db_path)
    limiter = rate_limiter or LoginRateLimiter()
    app = FastAPI(title="GeeLark-IA Master Admin API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(BodyLimitMiddleware, max_bytes=16_384)
    app.add_middleware(RequireHTTPSMiddleware)

    @app.exception_handler(RequestValidationError)
    async def safe_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # No devolver el contenido recibido: puede incluir la contraseña de login.
        return _security_headers(JSONResponse({"error": {"code": "INVALID_REQUEST"}}, status_code=400))

    @app.exception_handler(Exception)
    async def safe_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return _security_headers(JSONResponse({"error": {"code": "SERVICE_UNAVAILABLE"}}, status_code=503))

    @app.get("/", include_in_schema=False)
    async def panel() -> Response:
        if panel_path is None or not Path(panel_path).is_file():
            return _security_headers(JSONResponse({"error": {"code": "PANEL_NOT_CONFIGURED"}}, status_code=503))
        panel_file = Path(panel_path)
        return HTMLResponse(
            content=panel_file.read_text(encoding="utf-8"),
            headers={
                "Cache-Control": "no-store, max-age=0",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": _panel_csp(panel_file),
            },
        )

    @app.get("/admin/v1/session")
    async def session_status(request: Request) -> Response:
        valid = sessions.valid(request.cookies.get(SESSION_COOKIE))
        return _security_headers(JSONResponse({"authenticated": valid}, status_code=200))

    @app.post("/admin/v1/login")
    async def login(payload: LoginPayload, request: Request) -> Response:
        if not _same_origin(request):
            return _security_headers(JSONResponse({"error": {"code": "ORIGIN_REJECTED"}}, status_code=403))
        peer = request.client.host if request.client else "unknown"
        if not limiter.allowed(peer):
            return _security_headers(JSONResponse({"error": {"code": "LOGIN_RATE_LIMITED"}}, status_code=429))
        if not verify_operator_password(payload.password, operator_password_hash):
            limiter.failed(peer)
            return _security_headers(JSONResponse({"error": {"code": "INVALID_CREDENTIALS"}}, status_code=401))
        limiter.succeeded(peer)
        token = sessions.create()
        response = JSONResponse({"authenticated": True}, status_code=200)
        response.set_cookie(SESSION_COOKIE, token, max_age=8 * 60 * 60, httponly=True, secure=secure_cookie, samesite="strict", path="/")
        return _security_headers(response)

    @app.post("/admin/v1/logout")
    async def logout(request: Request) -> Response:
        if not _same_origin(request):
            return _security_headers(JSONResponse({"error": {"code": "ORIGIN_REJECTED"}}, status_code=403))
        sessions.revoke(request.cookies.get(SESSION_COOKIE))
        response = JSONResponse({"authenticated": False}, status_code=200)
        response.delete_cookie(SESSION_COOKIE, path="/", secure=secure_cookie, httponly=True, samesite="strict")
        return _security_headers(response)

    @app.get("/admin/v1/status/snapshots")
    async def status_snapshots(request: Request) -> Response:
        if not sessions.valid(request.cookies.get(SESSION_COOKIE)):
            return _security_headers(JSONResponse({"error": {"code": "AUTHENTICATION_REQUIRED"}}, status_code=401))
        generated_at, snapshots = _read_snapshots(connect)
        payload = {"schema_version": "1.0", "generated_at": generated_at, "snapshots": snapshots}
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_RESPONSE_BYTES:
            return _security_headers(JSONResponse({"error": {"code": "RESPONSE_TOO_LARGE"}}, status_code=503))
        return _security_headers(Response(content=encoded, status_code=200, media_type="application/json"))

    return app
