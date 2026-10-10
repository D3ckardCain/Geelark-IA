"""Integración real SQLite → HTTPS/TLS → API → PostgreSQL con pérdida de ACK."""

import hashlib
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from geelark_cluster_agent_guard import AgentCommand, AgentJournal
from cluster_agent_transport import (
    AgentHTTPSClient,
    AgentTransportError,
    AgentTransportRuntime,
    PostgresRateLimiter,
    create_agent_app,
    make_database_authenticator,
    make_database_idempotency_runner,
    make_database_nonce_consumer,
    make_postgres_agent_handlers,
)
from cluster_agent_transport.server import make_uvicorn_config


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


class LoseFirstAckClient:
    """Usa HTTPS real y simula que se pierde la primera respuesta 2xx."""

    def __init__(self, client):
        self.client = client
        self.drop_next_success = True
        self.requests = []

    def request(self, method, path, *, payload=None, headers=None):
        self.requests.append((method, path, payload, dict(headers or {})))
        response = self.client.request(method, path, payload=payload, headers=headers)
        if self.drop_next_success and 200 <= response.status < 300:
            self.drop_next_success = False
            raise AgentTransportError("respuesta de prueba perdida")
        return response


def create_local_tls_identity(tmp_path):
    ca_key, ca_cert = tmp_path / "ca.key", tmp_path / "ca.crt"
    server_key, server_csr, server_cert = (
        tmp_path / "server.key",
        tmp_path / "server.csr",
        tmp_path / "server.crt",
    )
    extensions = tmp_path / "server.ext"
    extensions.write_text(
        "basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n"
        "subjectAltName=IP:127.0.0.1\n",
        encoding="utf-8",
    )
    commands = [
        [
            "openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
            "-out", str(ca_key),
        ],
        [
            "openssl", "req", "-x509", "-new", "-sha256", "-days", "1",
            "-key", str(ca_key), "-out", str(ca_cert), "-subj", "/CN=GeeLark-IA Integration CA",
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign",
        ],
        [
            "openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
            "-out", str(server_key),
        ],
        [
            "openssl", "req", "-new", "-sha256", "-key", str(server_key), "-out", str(server_csr),
            "-subj", "/CN=GeeLark-IA Integration Server",
        ],
        [
            "openssl", "x509", "-req", "-sha256", "-days", "1", "-in", str(server_csr),
            "-CA", str(ca_cert), "-CAkey", str(ca_key), "-CAcreateserial",
            "-out", str(server_cert), "-extfile", str(extensions),
        ],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, text=True)
    return ca_cert, server_cert, server_key


@pytest.mark.skipif(shutil.which("openssl") is None, reason="requiere OpenSSL para la CA temporal")
def test_sqlite_receipt_reaches_postgres_over_real_https_and_recovers_lost_ack(tmp_path):
    node_id, credential_id = uuid4(), uuid4()
    instance_id, operation_id = uuid4(), uuid4()
    task_id = operation_id  # El contrato actual construye la ruta de resultado con operation_id.
    request_id = uuid4()
    token = secrets.token_hex(32)
    now = datetime.now(timezone.utc)
    connect = lambda: psycopg.connect(DATABASE_URL)

    ca_cert, server_cert, server_key = create_local_tls_identity(tmp_path)
    app = create_agent_app(
        authenticate=make_database_authenticator(connect),
        consume_nonce=make_database_nonce_consumer(connect),
        idempotency_runner=make_database_idempotency_runner(connect),
        rate_limiter=PostgresRateLimiter(connect, max_requests=60, window_seconds=60),
        handlers=make_postgres_agent_handlers(connect),
    )

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    config = make_uvicorn_config(
        app, host="127.0.0.1", port=port,
        certfile=str(server_cert), keyfile=str(server_key),
    )

    import uvicorn

    server = uvicorn.Server(config)
    thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
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
                    credential_id, node_id, hashlib.sha256(token.encode("ascii")).hexdigest(),
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
                    psycopg.types.json.Jsonb({"desired_state": "running"}),
                    now + timedelta(minutes=2), now, now,
                ),
            )

        thread.start()
        deadline = time.monotonic() + 8
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started, "El servidor HTTPS de integración no llegó a iniciar"

        https = AgentHTTPSClient(
            base_url=f"https://127.0.0.1:{port}",
            ca_cert=str(ca_cert),
            timeout_seconds=5,
        )
        client = LoseFirstAckClient(https)
        journal = AgentJournal(tmp_path / "agent-journal.sqlite3", node_id)
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
            client=client,
            bearer_token=token,
            journal=journal,
            local_node_id=node_id,
        )

        # El controlador confirma en PostgreSQL; se pierde la respuesta en el enlace HTTPS.
        assert runtime.sync_pending_receipts(limit=10) == (0, 1)
        assert len(journal.list_pending_receipts(limit=10)) == 1

        # El reintento reutiliza la clave idempotente; PostgreSQL devuelve el snapshot previo.
        assert runtime.sync_pending_receipts(limit=10) == (1, 1)
        assert journal.list_pending_receipts(limit=10) == []
        assert len(client.requests) == 2
        assert client.requests[0][3]["Idempotency-Key"] == client.requests[1][3]["Idempotency-Key"]
        assert client.requests[0][3]["X-Agent-Nonce"] != client.requests[1][3]["X-Agent-Nonce"]

        with connect() as conn:
            task = conn.execute(
                "SELECT status, result_summary FROM geelark_control.agent_tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            operation = conn.execute(
                "SELECT status, result_summary FROM geelark_control.operations WHERE operation_id = %s",
                (operation_id,),
            ).fetchone()
        assert task == ("succeeded", {"exit_code": 0})
        assert operation == ("succeeded", {"exit_code": 0})
    finally:
        server.should_exit = True
        if thread.is_alive():
            thread.join(timeout=8)
        listener.close()
        with connect() as conn:
            conn.execute(
                "DELETE FROM geelark_control.idempotency_records WHERE scope LIKE %s",
                (f"agent:{node_id}:%",),
            )
            conn.execute("DELETE FROM geelark_control.agent_request_nonces WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.agent_tasks WHERE task_id = %s", (task_id,))
            conn.execute("DELETE FROM geelark_control.operations WHERE operation_id = %s", (operation_id,))
            conn.execute("DELETE FROM geelark_control.instances WHERE instance_id = %s", (instance_id,))
            conn.execute("DELETE FROM geelark_control.node_credentials WHERE node_id = %s", (node_id,))
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
        assert not thread.is_alive(), "El servidor HTTPS temporal no terminó"
