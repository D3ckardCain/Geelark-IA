"""API de agente con permisos por ruta, nonces y límites defensivos.

La fábrica no abre puertos. El despliegue debe configurar explícitamente
TLS con certificado/clave y distribuir la CA local de confianza al agente.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, ValidationError

from .limits import InMemoryRateLimiter
from .policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation
from .replay import ReplayRejected


class HeartbeatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: int = Field(ge=1, le=1)
    agent_version: str = Field(min_length=1, max_length=64)
    health_state: str = Field(pattern="^(healthy|degraded|unknown)$")
    cpu_load_percent: FiniteFloat = Field(ge=0, le=100)
    memory_total_bytes: int = Field(ge=0, le=2**63 - 1)
    memory_available_bytes: int = Field(ge=0, le=2**63 - 1)
    storage_available_bytes: int = Field(ge=0, le=2**63 - 1)


class CapabilitiesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capabilities_version: int = Field(ge=1, le=2**31 - 1)
    capabilities: list[str] = Field(max_length=128)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "CapabilitiesPayload":
        parsed = super().model_validate(obj, *args, **kwargs)
        if any(not isinstance(item, str) or not item.strip() or len(item) > 128 for item in parsed.capabilities):
            raise ValueError("Cada capacidad debe tener entre 1 y 128 caracteres.")
        if len(set(parsed.capabilities)) != len(parsed.capabilities):
            raise ValueError("No se permiten capacidades duplicadas.")
        return parsed


class TaskMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=1, le=1)
    state: str = Field(min_length=1, max_length=32)
    details: dict[str, Any] = Field(default_factory=dict)


class BodyLimitMiddleware:
    """Limita el cuerpo incluso si la petición no declara Content-Length."""

    def __init__(self, app: Any, max_bytes: int = 1_048_576) -> None:
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
                    await self._too_large(scope, receive, send)
                    return
            except ValueError:
                await self._bad_request(scope, receive, send)
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
                await self._too_large(scope, receive, send)
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
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _too_large(scope: dict[str, Any], receive: Any, send: Any) -> None:
        from starlette.responses import JSONResponse
        await JSONResponse({"error": {"code": "BODY_TOO_LARGE", "message": "El cuerpo excede 1 MiB."}}, status_code=413)(scope, receive, send)

    @staticmethod
    async def _bad_request(scope: dict[str, Any], receive: Any, send: Any) -> None:
        from starlette.responses import JSONResponse
        await JSONResponse({"error": {"code": "INVALID_CONTENT_LENGTH", "message": "Content-Length inválido."}}, status_code=400)(scope, receive, send)


def create_agent_app(
    *,
    authenticate: Callable[[str], AgentPrincipal],
    consume_nonce: Callable[..., None],
    handlers: dict[Operation, Callable[..., Any]],
    rate_limiter: InMemoryRateLimiter | None = None,
    max_body_bytes: int = 1_048_576,
) -> FastAPI:
    """Crea la API sin listener; callbacks de dominio son obligatorios para actuar."""
    limiter = rate_limiter or InMemoryRateLimiter()
    app = FastAPI(
        title="GeeLark-IA Agent API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(BodyLimitMiddleware, max_bytes=max_body_bytes)

    def authorize(
        operation: Operation,
        authorization: str | None,
        x_agent_nonce: str | None,
        x_agent_timestamp: str | None,
        x_request_id: str | None,
    ) -> AgentPrincipal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
        secret = authorization[7:]
        try:
            principal = authenticate(secret)
        except Exception as exc:
            # No incluir mensajes de autenticación/SQL en la respuesta.
            from .db_auth import InvalidAgentCredential
            if isinstance(exc, InvalidAgentCredential):
                raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_FAILED"}) from None
            raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"}) from None

        if not limiter.allow(principal.node_id):
            raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED"})
        try:
            authorize_operation(principal, operation)
        except PermissionDenied:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"}) from None

        try:
            nonce = UUID(x_agent_nonce or "")
            request_id = UUID(x_request_id or "")
            timestamp = datetime.fromisoformat((x_agent_timestamp or "").replace("Z", "+00:00"))
            consume_nonce(
                node_id=UUID(principal.node_id),
                credential_id=UUID(principal.credential_id),
                nonce=nonce,
                request_id=request_id,
                timestamp=timestamp,
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
            # El adaptador debe registrar request_id de forma saneada; no exponer excepción.
            raise HTTPException(status_code=500, detail={"code": "OPERATION_FAILED"}) from None

    @app.post("/agent/v1/heartbeat")
    def heartbeat(
        payload: HeartbeatPayload,
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ) -> Any:
        principal = authorize(Operation.HEARTBEAT, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        if payload.memory_available_bytes > payload.memory_total_bytes:
            raise HTTPException(status_code=422, detail={"code": "INVALID_MEMORY_METRICS"})
        return invoke(Operation.HEARTBEAT, principal, payload.model_dump())

    @app.put("/agent/v1/capabilities")
    def capabilities(
        payload: CapabilitiesPayload,
        authorization: str | None = Header(default=None),
        x_agent_nonce: str | None = Header(default=None),
        x_agent_timestamp: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ) -> Any:
        principal = authorize(Operation.CAPABILITIES, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        return invoke(Operation.CAPABILITIES, principal, payload.model_dump())

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
        ) -> Any:
            principal = authorize(operation, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
            return invoke(operation, principal, {"task_id": str(task_id), **payload.model_dump()})
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
    ) -> Any:
        principal = authorize(Operation.RECONCILE, authorization, x_agent_nonce, x_agent_timestamp, x_request_id)
        return invoke(Operation.RECONCILE, principal, payload.model_dump())

    return app
