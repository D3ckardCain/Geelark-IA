from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from cluster_agent_transport.app import create_agent_app
from cluster_agent_transport.policy import AgentPrincipal, Operation


PENDING = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "pending", "pending")
ACTIVE = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "active", "active")


def make_client(principal, *, base_url="https://testserver"):
    calls = []

    def authenticate(secret):
        assert secret == "a" * 64
        return principal

    def nonce_guard(**kwargs):
        assert kwargs["node_id"].int != 0
        assert kwargs["timestamp"].tzinfo is not None

    handlers = {
        op: (lambda *, principal, payload=None, op=op: calls.append(op.value) or {"ok": True})
        for op in Operation
    }
    app = create_agent_app(authenticate=authenticate, consume_nonce=nonce_guard, handlers=handlers)
    return TestClient(app, base_url=base_url), calls


def headers():
    return {
        "Authorization": "Bearer " + "a" * 64,
        "X-Agent-Nonce": str(uuid4()),
        "X-Agent-Timestamp": datetime.now(timezone.utc).isoformat(),
        "X-Request-ID": str(uuid4()),
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
    response = client.post(
        f"/agent/v1/tasks/{uuid4()}/accept", headers=headers(),
        json={"schema_version": 1, "state": "accepted", "details": {}},
    )
    assert response.status_code == 403
    assert calls == ["heartbeat", "status_read"]


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
