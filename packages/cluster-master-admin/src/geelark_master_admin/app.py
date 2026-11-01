"""API administrativa de PC-MASTER: inventario de solo lectura y control Android opcional.

La fábrica no abre sockets. El proceso anfitrión debe montarla detrás de HTTPS,
en el mismo origen del panel, y proporcionar una conexión PostgreSQL SELECT-only.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import asyncio
import anyio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import UUID

from fastapi import FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from geelark_cluster_persistence.status_snapshot import build_status_snapshot
from .auth import LoginRateLimiter, SessionStore, verify_operator_password

SESSION_COOKIE = "__Host-geelark_master_session"
MAX_SNAPSHOTS = 500
MAX_RESPONSE_BYTES = 1_048_576


class _ClosingStream(StreamingResponse):
    def __init__(self, *args, on_close, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_close = on_close

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            with anyio.CancelScope(shield=True):
                try:
                    await self.body_iterator.aclose()
                finally:
                    await self.on_close()


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=1024)


class AndroidActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["open", "disconnect", "recover"]
    password: str | None = Field(default=None, max_length=1024)


class AndroidInputPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    screen: str = Field(pattern=r"^[0-9a-f]{32}$")
    kind: Literal["touch", "key", "text"]
    action: int = Field(default=0, ge=0, le=2)
    x: int = Field(default=0, ge=0, le=8191)
    y: int = Field(default=0, ge=0, le=8191)
    key: Literal[3, 4, 187] = 3
    text: str = Field(default="", max_length=300)


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
    """Lecturas SELECT acotadas; vigencia calculada con el reloj de PostgreSQL."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT node_id, display_name, admin_state, reported_health_state,
                   agent_version, last_seen_at, capabilities, module_reports, revoked_at
              FROM geelark_control.nodes
             ORDER BY display_name ASC NULLS LAST, node_id ASC
             LIMIT %s
            """,
            (MAX_SNAPSHOTS,),
        ).fetchall()
        # Tomar el reloj después de leer las filas: no reutilizar la hora local
        # ni el timestamp fijado al inicio de una transacción prolongada.
        now: datetime = conn.execute("SELECT clock_timestamp()").fetchone()[0]
        now = now.astimezone(timezone.utc)
    snapshots = [build_status_snapshot(row, now=now) for row in rows]
    return now.isoformat().replace("+00:00", "Z"), [item for item in snapshots if item is not None]


TaskStatus = Literal["queued", "delivered", "accepted", "running", "succeeded", "rejected", "failed", "unknown", "cancelled"]
TASK_COLUMNS = ("task_id","operation_id","node_id","instance_id","assignment_epoch","status","delivery_attempts","created_at","updated_at","delivered_at","accepted_at","completed_at","last_error_code",)


def _read_tasks(connect: Callable[[], Any], *, node_id: UUID | None, status: str | None,
                limit: int, offset: int) -> dict[str, Any]:
    # Solo metadatos autorizados: nunca SELECT *, payload ni result_summary.
    predicates, params = [], []
    if node_id is not None:
        predicates.append("node_id = %s")
        params.append(node_id)
    if status is not None:
        predicates.append("status = %s")
        params.append(status)
    where = " WHERE " + " AND ".join(predicates) if predicates else ""
    query = ("SELECT " + ", ".join(TASK_COLUMNS) + " FROM geelark_control.agent_tasks" +
             where + " ORDER BY created_at DESC, task_id DESC LIMIT %s OFFSET %s")
    with connect() as conn:
        rows = conn.execute(query, (*params, limit + 1, offset)).fetchall()
        now = conn.execute("SELECT clock_timestamp()").fetchone()[0]
    tasks = []
    for row in rows[:limit]:
        item = dict(zip(TASK_COLUMNS, row, strict=True))
        for key in ("task_id", "operation_id", "node_id", "instance_id"):
            item[key] = str(UUID(str(item[key])))
        for key in ("created_at", "updated_at", "delivered_at", "accepted_at", "completed_at"):
            value = item[key]
            item[key] = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None
        code = item["last_error_code"]
        item["last_error_code"] = code if isinstance(code, str) and re.fullmatch(r"[A-Z0-9_]{1,64}", code) else None
        tasks.append(item)
    return {"schema_version": "1.0", "generated_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tasks": tasks, "limit": limit, "offset": offset, "has_more": len(rows) > limit}


def create_admin_app(
    *,
    connect: Callable[[], Any],
    operator_password_hash: str,
    session_db_path: str,
    secure_cookie: bool = True,
    rate_limiter: LoginRateLimiter | None = None,
    panel_path: str | Path | None = None,
    android_control: Any = None,
    diagnostics_enabled: bool = False,
) -> FastAPI:
    """Crea rutas admin con autenticación local; no inicia listener ni hace deploy."""
    if not isinstance(operator_password_hash, str) or not operator_password_hash.startswith("pbkdf2_sha256$"):
        raise ValueError("operator_password_hash debe ser un hash PBKDF2 generado localmente.")
    sessions = SessionStore(session_db_path)
    limiter = rate_limiter or LoginRateLimiter()
    @asynccontextmanager
    async def lifespan(application):
        try:
            yield
        finally:
            if android_control is not None:
                await asyncio.to_thread(android_control.close)

    app = FastAPI(title="GeeLark-IA Master Admin API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
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
            content=panel_file.read_text(encoding="utf-8").replace(
                '<!-- OPTIONAL_DIAGNOSTICS -->',
                '<a class="btn" href="/diagnostics">Diagnóstico técnico</a>' if diagnostics_enabled else ""),
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


    @app.get("/admin/v1/tasks")
    async def list_tasks(request: Request, node_id: UUID | None = None,
                         status: TaskStatus | None = None,
                         limit: int = Query(default=50, ge=1, le=100),
                         offset: int = Query(default=0, ge=0, le=10000)) -> Response:
        if not sessions.valid(request.cookies.get(SESSION_COOKIE)):
            return _security_headers(JSONResponse({"error": {"code": "AUTHENTICATION_REQUIRED"}}, status_code=401))
        payload = _read_tasks(connect, node_id=node_id, status=status, limit=limit, offset=offset)
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_RESPONSE_BYTES:
            return _security_headers(JSONResponse({"error": {"code": "RESPONSE_TOO_LARGE"}}, status_code=503))
        return _security_headers(Response(content=encoded, media_type="application/json"))

    def control_error(request, *, write=False):
        if not sessions.valid(request.cookies.get(SESSION_COOKIE)):
            return _security_headers(JSONResponse({"error": {"code": "AUTHENTICATION_REQUIRED"}}, status_code=401))
        if write and not _same_origin(request):
            return _security_headers(JSONResponse({"error": {"code": "ORIGIN_REJECTED"}}, status_code=403))
        if android_control is None:
            return _security_headers(JSONResponse({"error": {"code": "ANDROID_NOT_CONFIGURED"}}, status_code=503))
        return None

    @app.get("/admin/v1/android")
    def android_status(request: Request):
        error = control_error(request)
        if error is not None:
            return error
        return _security_headers(JSONResponse(android_control.status()))

    @app.post("/admin/v1/android/actions")
    def android_action(payload: AndroidActionPayload, request: Request):
        error = control_error(request, write=True)
        if error is not None:
            return error
        if payload.action != "recover" and payload.password is not None:
            return _security_headers(JSONResponse({"error": {"code": "INVALID_REQUEST"}}, status_code=400))
        accepted = android_control.submit(payload.action, payload.password)
        return _security_headers(JSONResponse({"accepted": accepted}, status_code=202 if accepted else 409))

    @app.get("/admin/v1/android/video")
    def android_video(request: Request, screen: str):
        error = control_error(request)
        if error is not None:
            return error
        with android_control.lock:
            current = android_control.controller.screen
            if (android_control.busy or current is None or getattr(current, "id", None) != screen
                    or current.poll() is not None or not current.claim.acquire(blocking=False)):
                return _security_headers(JSONResponse({"error": {"code": "SCREEN_UNAVAILABLE"}}, status_code=409))
        token = request.cookies.get(SESSION_COOKIE)
        def valid():
            return sessions.valid(token) and android_control.controller.screen is current
        iterator = current.frames(valid)
        def next_packet():
            return next(iterator, None)
        async def packets():
            while True:
                chunk = await anyio.to_thread.run_sync(next_packet)
                if chunk is None:
                    break
                yield chunk
        async def close_stream():
            # Liberar también si la respuesta se corta antes del primer paquete.
            try:
                await anyio.to_thread.run_sync(iterator.close)
            finally:
                try:
                    await anyio.to_thread.run_sync(current.terminate)
                finally:
                    if current.claim.locked():
                        current.claim.release()
        return _security_headers(_ClosingStream(packets(), on_close=close_stream, media_type="application/x-ndjson",
                                                   headers={"X-Accel-Buffering": "no"}))

    @app.post("/admin/v1/android/input")
    def android_input(payload: AndroidInputPayload, request: Request):
        error = control_error(request, write=True)
        if error is not None:
            return error
        with android_control.lock:
            current = android_control.controller.screen
            if android_control.busy or current is None or getattr(current, "id", None) != payload.screen:
                return _security_headers(JSONResponse({"error": {"code": "SCREEN_UNAVAILABLE"}}, status_code=409))
            try:
                current.input(payload.model_dump())
            except (ValueError, OSError):
                return _security_headers(JSONResponse({"error": {"code": "INPUT_REJECTED"}}, status_code=400))
        return _security_headers(JSONResponse({"accepted": True}))

    @app.get("/diagnostics", include_in_schema=False)
    def diagnostics_page(request: Request):
        if not diagnostics_enabled:
            return _security_headers(JSONResponse({"error": {"code": "NOT_FOUND"}}, status_code=404))
        error = control_error(request)
        if error is not None:
            return error
        page = Path(__file__).with_name("diagnostics.html")
        return HTMLResponse(page.read_text(encoding="utf-8"), headers={
            "Cache-Control": "no-store, max-age=0", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer", "Content-Security-Policy": _panel_csp(page)})

    @app.get("/admin/v1/diagnostics/android")
    def diagnostics_log(request: Request):
        if not diagnostics_enabled:
            return _security_headers(JSONResponse({"error": {"code": "NOT_FOUND"}}, status_code=404))
        error = control_error(request)
        if error is not None:
            return error
        return _security_headers(JSONResponse({"status": android_control.status(), "log": android_control.diagnostics()}))

    @app.post("/admin/v1/diagnostics/android")
    def diagnostics_run(request: Request):
        if not diagnostics_enabled:
            return _security_headers(JSONResponse({"error": {"code": "NOT_FOUND"}}, status_code=404))
        error = control_error(request, write=True)
        if error is not None:
            return error
        from .android_diagnostics import collect
        accepted = android_control.submit("diagnose", diagnostic=collect)
        return _security_headers(JSONResponse({"accepted": accepted}, status_code=202 if accepted else 409))

    @app.post("/admin/v1/diagnostics/android/clear")
    def diagnostics_clear(request: Request):
        if not diagnostics_enabled:
            return _security_headers(JSONResponse({"error": {"code": "NOT_FOUND"}}, status_code=404))
        error = control_error(request, write=True)
        if error is not None:
            return error
        accepted = android_control.clear_diagnostics()
        return _security_headers(JSONResponse({"cleared": accepted}, status_code=200 if accepted else 409))

    return app

