"""Integración del recibo SQLite con handlers PostgreSQL mediante la API ASGI.

La capa de red/TLS se prueba por separado en test_client.py. Aquí TestClient usa
scope HTTPS para ejecutar middleware/rutas sin abrir sockets ni tocar producción;
el adaptador simula la frontera del cliente y permite reproducir una respuesta 2xx
perdida después de que PostgreSQL haya confirmado el resultado.
"""
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from geelark_cluster_agent_guard import AgentCommand, AgentJournal
from cluster_agent_transport.app import create_agent_app
from cluster_agent_transport.client import AgentResponse, AgentTransportError
from cluster_agent_transport.domain_handlers import make_postgres_agent_handlers
from cluster_agent_transport.policy import AgentPrincipal, Operation
from cluster_agent_transport.runtime import AgentTransportRuntime


DATABASE_URL = __import__("os").environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")
TOKEN = "a" * 64


class ASGIClientAdapter:
    """Adaptador de test: no abre sockets y puede simular la pérdida del primer ACK."""

    def __init__(self, client, *, lose_first_response=False):
        self.client = client
        self.lose_first_response = lose_first_response
        self.requests = []

    def request(self, method, path, *, payload=None, headers=None):
        self.requests.append((method, path, payload, dict(headers or {})))
        response = self.client.request(method, path, json=payload, headers=headers)
        if self.lose_first_response:
            self.lose_first_response = False
            if 200 <= response.status_code < 300:
                raise AgentTransportError("respuesta de prueba perdida")
        return AgentResponse(
            status=response.status_code,
            body=response.content,
            content_type=response.headers.get("content-type"),
        )


def test_sqlite_receipt_sync_is_idempotent_when_postgres_commits_but_ack_is_lost(tmp_path):
    node_id, credential_id = uuid4(), uuid4()
    instance_id = uuid4()
    operation_id = uuid4()
    task_id = operation_id  # El runtime identifica la ruta por operation_id; el modelo actual usa el mismo UUID.
    request_id = uuid4()
    now = datetime.now(timezone.utc)
    connect = lambda: psycopg.connect(DATABASE_URL)
    principal = AgentPrincipal(str(node_id), str(credential_id), "active", "active")
    handlers = make_postgres_agent_handlers(connect)
    executions = []
    cached = {}

    def authenticate(token):
        assert token == TOKEN
        return principal

    def consume_nonce(**_kwargs):
        return None

    def idempotency_runner(*, principal, operation, key, payload, execute):
        cache_key = (principal.node_id, operation, key)
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        previous = cached.get(cache_key)
        if previous is not None:
            old_hash, result = previous
            if old_hash != payload_hash:
                raise RuntimeError("clave idempotente reutilizada con otro payload")
            return result
        with connect() as conn:
            result = execute(conn)
        executions.append((operation, key))
        cached[cache_key] = (payload_hash, result)
        return result

    app = create_agent_app(
        authenticate=authenticate,
        consume_nonce=consume_nonce,
        handlers=handlers,
        idempotency_runner=idempotency_runner,
    )
    asgi = TestClient(app, base_url="https://testserver")
    adapter = ASGIClientAdapter(asgi, lose_first_response=True)

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'active')",
                (node_id, "test-receipt-sync-" + str(node_id)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.node_credentials
                    (credential_id, node_id, token_sha256, status, created_at, expires_at, activated_at)
                VALUES (%s, %s, %s, 'active', %s, %s, %s)
                """,
                (
                    credential_id, node_id,
                    hashlib.sha256(TOKEN.encode()).hexdigest(),
                    now, now + timedelta(hours=1), now,
                ),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.instances
                    (instance_id, desired_state, observed_state, owner_node_id, assignment_epoch, lease_expires_at)
                VALUES (%s, 'running', 'reserved', %s, 3, %s)
                """,
                (instance_id, node_id, now + timedelta(minutes=5)),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.operations
                    (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type, status)
                VALUES (%s, %s, %s, %s, 3, 'assign', 'accepted')
                """,
                (operation_id, request_id, instance_id, node_id),
            )
            conn.execute(
                """
                INSERT INTO geelark_control.agent_tasks
                    (task_id, operation_id, node_id, instance_id, assignment_epoch, payload,
                     status, delivery_attempts, delivery_lease_until, delivered_at, accepted_at)
                VALUES (%s, %s, %s, %s, 3, %s, 'accepted', 1, %s, %s, %s)
                """,
                (
                    task_id, operation_id, node_id, instance_id,
                    Jsonb({"desired_state": "running"}),
                    now + timedelta(minutes=2), now, now,
                ),
            )

        journal_path = tmp_path / "agent-journal.sqlite3"
        journal = AgentJournal(journal_path, node_id)
        journal.initialize()
        journal.accept_command(
            AgentCommand(
                operation_id=operation_id,
                instance_id=instance_id,
                node_id=node_id,
                assignment_epoch=3,
                lease_expires_at=now + timedelta(minutes=4),
                payload={"desired_state": "running"},
            )
        )
        journal.record_result(
            operation_id=operation_id,
            instance_id=instance_id,
            node_id=node_id,
            assignment_epoch=3,
            status="succeeded",
            result={"exit_code": 0},
        )

        runtime = AgentTransportRuntime(
            client=adapter,
            bearer_token=TOKEN,
            journal=journal,
            local_node_id=node_id,
            clock=lambda: datetime.now(timezone.utc),
        )

        # PostgreSQL commitó el resultado, pero el agente no recibió el primer ACK.
        assert runtime.sync_pending_receipts(limit=10) == (0, 1)
        assert len(journal.list_pending_receipts(limit=10)) == 1

        # Reintento: la clave es estable, el servidor responde idempotentemente y el journal guarda ACK.
        assert runtime.sync_pending_receipts(limit=10) == (1, 1)
        assert journal.list_pending_receipts(limit=10) == []
        assert len(adapter.requests) == 2
        assert adapter.requests[0][3]["Idempotency-Key"] == adapter.requests[1][3]["Idempotency-Key"]
        assert adapter.requests[0][3]["X-Agent-Nonce"] != adapter.requests[1][3]["X-Agent-Nonce"]
        assert len(executions) == 1

        with connect() as conn:
            task_status = conn.execute(
                "SELECT status, result_summary FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            operation_status = conn.execute(
                "SELECT status, result_summary FROM geelark_control.operations WHERE operation_id = %s",
                (operation_id,),
            ).fetchone()
        assert task_status == ("succeeded", {"exit_code": 0})
        assert operation_status == ("succeeded", {"exit_code": 0})
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE task_id = %s", (task_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
