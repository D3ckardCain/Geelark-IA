from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from cluster_agent_transport.app import create_agent_app
from cluster_agent_transport.policy import AgentPrincipal, Operation


EXPIRY = datetime.now(timezone.utc) + timedelta(hours=1)
PENDING = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "pending", "pending", EXPIRY)
ACTIVE = AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", "active", "active", EXPIRY)


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
            Operation.TASK_RESULT, Operation.RECONCILE, Operation.RECONCILE_INVENTORY,
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
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "active", "revoked", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "pending", "revoked", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "revoked", "active", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "revoked", "revoked", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "active", "expired", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "pending", "expired", EXPIRY),
        AgentPrincipal(PENDING.node_id, PENDING.credential_id, "unknown", "active", EXPIRY),
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


def test_reconcile_route_requires_active_node_and_uses_handler():
    pending_client, pending_calls = make_client(PENDING)
    body = {"schema_version": 1, "inventory": []}
    denied = pending_client.post("/agent/v1/reconcile/inventory", headers=headers(), json=body)
    assert denied.status_code == 403
    assert pending_calls == []

    active_client, active_calls = make_client(ACTIVE)
    response = active_client.post("/agent/v1/reconcile/inventory", headers=headers(), json=body)
    assert response.status_code == 200
    assert active_calls == ["reconcile_inventory"]


def test_reconcile_payload_rejects_duplicate_tasks_and_oversized_result_summary():
    client, calls = make_client(ACTIVE)
    task_id, operation_id, instance_id = str(uuid4()), str(uuid4()), str(uuid4())
    item = {
        "task_id": task_id,
        "operation_id": operation_id,
        "instance_id": instance_id,
        "assignment_epoch": 3,
        "local_state": "running",
        "result_summary": {},
    }
    duplicate = client.post(
        "/agent/v1/reconcile/inventory", headers=headers(),
        json={"schema_version": 1, "inventory": [item, item]},
    )
    assert duplicate.status_code == 422

    oversized = {**item, "task_id": str(uuid4()), "result_summary": {"data": "x" * 70_000}}
    response = client.post(
        "/agent/v1/reconcile/inventory", headers=headers(),
        json={"schema_version": 1, "inventory": [oversized]},
    )
    assert response.status_code == 422

    invalid_epoch = {**item, "task_id": str(uuid4()), "assignment_epoch": True}
    epoch_response = client.post(
        "/agent/v1/reconcile/inventory", headers=headers(),
        json={"schema_version": 1, "inventory": [invalid_epoch]},
    )
    assert epoch_response.status_code == 422

    invalid_schema = client.post(
        "/agent/v1/reconcile/inventory", headers=headers(),
        json={"schema_version": True, "inventory": []},
    )
    assert invalid_schema.status_code == 422
    assert calls == []

    # El contrato debe rechazar claves sensibles incluso en variantes camelCase
    # y cuando aparecen anidadas dentro del resumen de reconciliación.
    for sensitive_key in ("access_token", "apiKey", "password", "cookie", "privateKey"):
        sensitive = {
            **item,
            "task_id": str(uuid4()),
            "result_summary": {"nested": {sensitive_key: "must-not-be-accepted"}},
        }
        rejected = client.post(
            "/agent/v1/reconcile/inventory", headers=headers(),
            json={"schema_version": 1, "inventory": [sensitive]},
        )
        assert rejected.status_code == 422, sensitive_key
