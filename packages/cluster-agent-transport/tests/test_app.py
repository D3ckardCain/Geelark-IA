from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from cluster_agent_transport.app import create_agent_app
from cluster_agent_transport.policy import AgentPrincipal, Operation


AUTH_NOW = datetime.now(timezone.utc)
EXPIRY = AUTH_NOW + timedelta(hours=1)
PENDING = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "pending", "pending", EXPIRY, AUTH_NOW)
ACTIVE = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "active", "active", EXPIRY, AUTH_NOW)


def make_client(principal, *, base_url="https://testserver", configure_task_handlers=True):
    calls = []

    def authenticate(secret):
        assert secret == "a" * 64
        return principal

    def nonce_guard(**kwargs):
        assert kwargs["node_id"].int != 0
        assert kwargs["timestamp"].tzinfo is not None

    configured_operations = set(Operation)
    if not configure_task_handlers:
        configured_operations -= {
            Operation.TASK_ACCEPT, Operation.TASK_PROGRESS,
            Operation.TASK_RESULT, Operation.RECONCILE,
        }
    handlers = {
        op: (lambda *, principal, payload=None, conn=None, op=op: calls.append(op.value) or {"ok": True})
        for op in configured_operations
    }
    def idempotency_runner(*, principal, operation, key, payload, execute):
        assert len(key) >= 16
        return execute(None)
    app = create_agent_app(
        authenticate=authenticate, consume_nonce=nonce_guard,
        handlers=handlers, idempotency_runner=idempotency_runner,
    )
    return TestClient(app, base_url=base_url), calls


def headers():
    return {
        "Authorization": "Bearer " + "a" * 64,
        "X-Agent-Nonce": str(uuid4()),
        "X-Agent-Timestamp": datetime.now(timezone.utc).isoformat(),
        "X-Request-ID": str(uuid4()),
        "Idempotency-Key": "request-" + str(uuid4()),
    }


def test_pending_can_send_heartbeat_and_read_status_but_not_accept_task():
    client, calls = make_client(PENDING)
    heartbeat = {
        "schema_version": 1, "agent_version": "0.1.0", "health_state": "healthy",
        "cpu_load_percent": 10, "memory_total_bytes": 100, "memory_available_bytes": 50,
        "storage_available_bytes": 200,
    }
    assert client.post("/agent/v1/heartbeat", headers=headers(), json=heartbeat).status_code == 200
    assert client.get("/agent/v1/status", headers=headers()).status_code == 200
    capabilities = {"capabilities_version": 1, "capabilities": ["heartbeat", "status"]}
    assert client.put("/agent/v1/capabilities", headers=headers(), json=capabilities).status_code == 200
    modules = {"schema_version": 1, "modules": [{"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0"}]}
    assert client.put("/agent/v1/modules", headers=headers(), json=modules).status_code == 403
    response = client.post(
        f"/agent/v1/tasks/{uuid4()}/accept", headers=headers(),
        json={"schema_version": 1, "state": "accepted", "details": {}},
    )
    assert response.status_code == 403
    assert calls == ["heartbeat", "status_read", "capabilities"]


def test_active_node_can_report_modules_and_unknown_module_is_rejected():
    client, calls = make_client(ACTIVE)
    valid = {"schema_version": 1, "modules": [{"module_id": "agent-supervisor", "state": "operational", "version": "0.1.0"}]}
    assert client.put("/agent/v1/modules", headers=headers(), json=valid).status_code == 200
    assert calls == ["modules_report"]
    invalid = {"schema_version": 1, "modules": [{"module_id": "unlisted-module", "state": "operational"}]}
    assert client.put("/agent/v1/modules", headers=headers(), json=invalid).status_code == 422


def test_duplicate_module_ids_are_rejected():
    client, calls = make_client(ACTIVE)
    duplicate = {"schema_version": 1, "modules": [
        {"module_id": "agent-supervisor", "state": "operational"},
        {"module_id": "agent-supervisor", "state": "degraded"},
    ]}
    assert client.put("/agent/v1/modules", headers=headers(), json=duplicate).status_code == 422
    assert calls == []


def test_pending_is_denied_all_task_and_reconciliation_routes_without_handler_calls():
    client, calls = make_client(PENDING)
    payload = {"schema_version": 1, "state": "accepted", "details": {}}
    responses = [
        client.post(f"/agent/v1/tasks/{uuid4()}/accept", headers=headers(), json=payload),
        client.post(f"/agent/v1/tasks/{uuid4()}/progress", headers=headers(), json=payload),
        client.post(f"/agent/v1/tasks/{uuid4()}/result", headers=headers(), json=payload),
        client.post("/agent/v1/reconcile", headers=headers(), json={"schema_version": 1, "assignments": []}),
    ]
    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert calls == []


def test_active_node_with_unconfigured_task_handlers_gets_503_without_mutation():
    client, calls = make_client(ACTIVE, configure_task_handlers=False)
    payload = {"schema_version": 1, "state": "accepted", "details": {}}
    responses = [
        client.post(f"/agent/v1/tasks/{uuid4()}/accept", headers=headers(), json=payload),
        client.post(f"/agent/v1/tasks/{uuid4()}/progress", headers=headers(), json=payload),
        client.post(f"/agent/v1/tasks/{uuid4()}/result", headers=headers(), json=payload),
        client.post("/agent/v1/reconcile", headers=headers(), json={"schema_version": 1, "assignments": []}),
    ]
    assert [response.status_code for response in responses] == [503, 503, 503, 503]
    assert calls == []


def test_pending_cannot_claim_tasks_and_active_can_claim():
    pending_client, pending_calls = make_client(PENDING)
    denied = pending_client.post(
        "/agent/v1/tasks/claim", headers=headers(), json={"schema_version": 1}
    )
    assert denied.status_code == 403
    assert pending_calls == []

    active_client, active_calls = make_client(ACTIVE)
    accepted = active_client.post(
        "/agent/v1/tasks/claim", headers=headers(), json={"schema_version": 1}
    )
    assert accepted.status_code == 200
    assert active_calls == ["task_fetch"]

def test_active_node_can_reach_task_handler():
    client, calls = make_client(ACTIVE)
    response = client.post(
        f"/agent/v1/tasks/{uuid4()}/accept", headers=headers(),
        json={"schema_version": 1, "state": "accepted", "details": {}},
    )
    assert response.status_code == 200
    assert calls == ["task_accept"]


def test_missing_security_headers_fail_closed():
    client, _ = make_client(PENDING)
    response = client.get("/agent/v1/status", headers={"Authorization": "Bearer " + "a" * 64})
    assert response.status_code == 400


def test_oversized_body_rejected():
    client, _ = make_client(ACTIVE)
    response = client.post(
        "/agent/v1/heartbeat", headers=headers(),
        content=b"x" * (1_048_577),
    )
    assert response.status_code == 413


def test_plain_http_is_rejected_before_authentication():
    client, _ = make_client(PENDING, base_url="http://testserver")
    response = client.get("/agent/v1/status", headers={"Authorization": "Bearer " + "a" * 64})
    assert response.status_code == 426


def test_inconsistent_revoked_and_expired_principal_states_never_reach_handlers():
    denied = (
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "active", "revoked", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "pending", "revoked", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "revoked", "active", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "revoked", "revoked", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "active", "expired", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "pending", "expired", EXPIRY, AUTH_NOW),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "unknown", "active", EXPIRY, AUTH_NOW),
    )
    for principal in denied:
        client, calls = make_client(principal)
        response = client.post(
            "/agent/v1/heartbeat",
            headers=headers(),
            json={
                "schema_version": 1, "agent_version": "0.1.0",
                "health_state": "healthy", "cpu_load_percent": 10,
                "memory_total_bytes": 100, "memory_available_bytes": 50,
                "storage_available_bytes": 200,
            },
        )
        assert response.status_code == 403
        assert calls == []


def test_body_limit_middleware_propagates_disconnect_after_replaying_body():
    import asyncio

    from cluster_agent_transport.app import BodyLimitMiddleware

    incoming = [
        {"type": "http.request", "body": b"hello", "more_body": False},
        {"type": "http.disconnect"},
    ]
    received_by_app = []
    sent = []

    async def receive():
        if incoming:
            return incoming.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    async def inner_app(scope, receive_from_middleware, send_to_client):
        received_by_app.append(await receive_from_middleware())
        received_by_app.append(await receive_from_middleware())
        await send_to_client({"type": "http.response.start", "status": 200, "headers": []})
        await send_to_client({"type": "http.response.body", "body": b"ok"})

    middleware = BodyLimitMiddleware(inner_app, max_bytes=16)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"content-length", b"5")],
        "server": ("testserver", 443),
        "client": ("testclient", 12345),
    }

    asyncio.run(middleware(scope, receive, send))

    assert received_by_app[0] == {
        "type": "http.request",
        "body": b"hello",
        "more_body": False,
    }
    assert received_by_app[1] == {"type": "http.disconnect"}
    assert sent[0]["status"] == 200
