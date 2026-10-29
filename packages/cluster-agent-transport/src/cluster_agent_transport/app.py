"""API de agente con permisos por ruta, nonces y límites defensivos.

La fábrica no abre puertos. HTTPS se impone también a nivel ASGI para impedir
que un despliegue accidental detrás de HTTP acepte credenciales bearer.
"""
from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Callable
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

from .limits import InMemoryRateLimiter
from .policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation
from .replay import ReplayRejected


class HeartbeatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: int = Field(ge=1, le=1)
    agent_version: str = Field(min_length=1, max_length=64)
    health_state: str = Field(pattern="^(healthy|degraded|unhealthy|unknown)$", description="Declaración reportada por el Worker; no es una salud autoritativa del controlador.")
    cpu_load_percent: FiniteFloat = Field(ge=0, le=100)
    memory_total_bytes: int = Field(ge=0, le=2**63 - 1)
    memory_available_bytes: int = Field(ge=0, le=2**63 - 1)
    storage_available_bytes: int = Field(ge=0, le=2**63 - 1)


class CapabilitiesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capabilities_version: int = Field(ge=1, le=2**31 - 1)
    capabilities: list[str] = Field(max_length=128)

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 128 for item in value):
            raise ValueError("Cada capacidad debe tener entre 1 y 128 caracteres.")
        if len(set(value)) != len(value):
            raise ValueError("No se permiten capacidades duplicadas.")
        return value


class TaskMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=1, le=1)
    state: str = Field(min_length=1, max_length=32)
    details: dict[str, Any] = Field(default_factory=dict)


class RequireHTTPSMiddleware:
    """Falla cerrada si el servidor ASGI recibe una solicitud HTTP sin TLS."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and scope.get("scheme") != "https":
            from starlette.responses import JSONResponse
            response = JSONResponse({"error": {"code": "HTTPS_REQUIRED"}}, status_code=426)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class BodyLimitMiddleware:
    """Limita el cuerpo incluso si la petición no declara Content-Length."""

    def __init__(self, app: Any, max_bytes: int = 1_048_576) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes debe ser positivo.")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length")
        if length is not None:
            try:
                if int(length) > self.max_bytes:
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
            # Tras repetir el cuerpo, conservar el canal ASGI original:
            # Starlette necesita recibir http.disconnect y no requests vacías infinitas.
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _respond(scope: dict[str, Any], receive: Any, send: Any, status: int, code: str) -> None:
        from starlette.responses import JSONResponse
        await JSONResponse({"error": {"code": code}}, status_code=status)(scope, receive, send)


def create_agent_app(
    *,
    authenticate: Callable[[str], AgentPrincipal],
    consume_nonce: Callable[..., None],
    handlers: dict[Operation, Callable[..., Any]],
    idempotency_runner: Callable[..., Any] | None = None,
    rate_limiter: InMemoryRateLimiter | None = None,
    max_body_bytes: int = 1_048_576,
) -> FastAPI:
    """Crea la API sin listener; las acciones de dominio requieren callbacks."""
    limiter = rate_limiter or InMemoryRateLimiter()
    app = FastAPI(title="GeeLark-IA Agent API", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(BodyLimitMiddleware, max_bytes=max_body_bytes)
    app.add_middleware(RequireHTTPSMiddleware)

    def authorize(
        operation: Operation,
        authorization: str | None,
        x_agent_nonce: str | None,
        x_agent_timestamp: str | None,
        x_request_id: str | None,
    ) -> AgentPrincipal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
        try:
            principal = authenticate(authorization[7:])
        except Exception as exc:
            from .db_auth import InvalidAgentCredential
            if isinstance(exc, InvalidAgentCredential):
                raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_FAILED"}) from None
            raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"}) from None

        try:
            authorize_operation(principal, operation)
        except PermissionDenied:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"}) from None

        try:
            allowed = limiter.allow(principal.node_id)
        except Exception:
            raise HTTPException(status_code=503, detail={"code": "RATE_LIMITER_UNAVAILABLE"}) from None
        if not allowed:
            raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED"})

        try:
            nonce = UUID(x_agent_nonce or "")
            request_id = UUID(x_request_id or "")
            timestamp = datetime.fromisoformat((x_agent_timestamp or "").replace("Z", "+00:00"))
            consume_nonce(
                node_id=UUID(principal.node_id), credential_id=UUID(principal.credential_id),
                nonce=nonce, request_id=request_id, timestamp=timestamp,
            )
        except ReplayRejected:
            raise HTTPException(status_code=409, detail={"code": "REPLAY_REJECTED"}) from None
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail={"code": "INVALID_SECURITY_HEADERS"}) from None
        except Exception:
            raise HTTPException(status_code=503, detail={"code": "REPLAY_GUARD_UNAVAILABLE"}) from None
        return principal

    def invoke(operation: Operation, principal: AgentPrincipal, payload: Any = None) -> Any:
        handler = handlers.get(operation)
        if handler is None:
            raise HTTPException(status_code=503, detail={"code": "OPERATION_NOT_CONFIGURED"})
        try:
            return handler(principal=principal, payload=payload)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail={"code": "OPERATION_FAILED"}) from None

    def invoke_write(operation: Operation, principal: AgentPrincipal, payload: Any, idempotency_key: str | None) -> Any:
        if not idempotency_key or not re.fullmatch(r"[A-Za-z0-9._:-]{16,200}", idempotency_key):
            raise HTTPException(status_code=400, detail={"code": "INVALID_IDEMPOTENCY_KEY"})
        if idempotency_runner is None:
            raise HTTPException(status_code=503, detail={"code": "IDEMPOTENCY_NOT_CONFIGURED"})
        handler = handlers.get(operation)
        if handler is None:
            raise HTTPException(status_code=503, detail={"code": "OPERATION_NOT_CONFIGURED"})
        from .idempotency import IdempotencyConflict, IdempotencyInProgress
        try:
            return idempotency_runner(
                principal=principal, operation=operation.value, key=idempotency_key, payload=payload,
                execute=lambda conn: handler(conn=conn, principal=principal, payload=payload),
            )
        except IdempotencyConflict:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from None
        except IdempotencyInProgress:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_IN_PROGRESS"}) from None
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail={"code": "OPERATION_FAILED"}) from None

    @app.post("/agent/v1/heartbeat")
    def heartbeat(
        payload: HeartbeatPayload,
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Any:
        principal = authorize(Operation.HEARTBEAT, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        if payload.memory_available_bytes > payload.memory_total_bytes:
            raise HTTPException(status_code=422, detail={"code": "INVALID_MEMORY_METRICS"})
        return invoke_write(Operation.HEARTBEAT, principal, payload.model_dump(), idempotency_key)

    @app.put("/agent/v1/capabilities")
    def capabilities(
        payload: CapabilitiesPayload,
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Any:
        principal = authorize(Operation.CAPABILITIES, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        return invoke_write(Operation.CAPABILITIES, principal, payload.model_dump(), idempotency_key)

    @app.get("/agent/v1/status")
    def status(
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ) -> Any:
        principal = authorize(Operation.STATUS_READ, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        return invoke(Operation.STATUS_READ, principal)

    def task_route(operation: Operation) -> Callable[..., Any]:
        def endpoint(
            task_id: UUID,
            payload: TaskMessage,
            authorization: str | None = Header(default=None),
            x_agent_nonce: str | None = Header(default=None),
            x_agent_timestamp: str | None = Header(default=None),
            x_request_id: str | None = Header(default=None),
            idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        ) -> Any:
            principal = authorize(operation, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
            return invoke_write(operation, principal, {"task_id": str(task_id), **payload.model_dump()}, idempotency_key)
        endpoint.__name__ = f"task_{operation.value}"
        return endpoint

    app.add_api_route("/agent/v1/tasks/{task_id}/accept", task_route(Operation.TASK_ACCEPT), methods=["POST"])
    app.add_api_route("/agent/v1/tasks/{task_id}/progress", task_route(Operation.TASK_PROGRESS), methods=["POST"])
    app.add_api_route("/agent/v1/tasks/{task_id}/result", task_route(Operation.TASK_RESULT), methods=["POST"])

    @app.post("/agent/v1/reconcile")
    def reconcile(
        payload: TaskMessage,
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Any:
        principal = authorize(Operation.RECONCILE, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        return invoke_write(Operation.RECONCILE, principal, payload.model_dump(), idempotency_key)

    return app
