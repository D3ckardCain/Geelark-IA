from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timedelta, timezone
import os

import pytest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from geelark_master_admin import create_admin_app, hash_operator_password
from geelark_master_admin.app import SESSION_COOKIE, _panel_csp


class FakeConnection(AbstractContextManager):
    def __init__(self, rows, database_now=None):
        self.rows = rows
        self.database_now = database_now if database_now is not None else datetime.now(timezone.utc)
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=()):
        self.statements.append((statement, params))
        assert statement.lstrip().upper().startswith("SELECT")
        assert "INSERT " not in statement.upper()
        assert "UPDATE " not in statement.upper()
        assert "DELETE " not in statement.upper()
        if 'FROM geelark_control.nodes' in statement:
            assert params == (500,)
            assert 'health_state AS reported_health_state' not in statement
            assert 'admin_state, reported_health_state,' in statement
        else:
            assert statement.strip().lower() == 'select clock_timestamp()'
            assert params == ()
        return self

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return (self.database_now,)


def make_row():
    return (
        uuid4(),
        "WORKER-01",
        "active",
        "healthy",
        "1.0.0",
        datetime.now(timezone.utc),
        {"items": ["heartbeat-v1", "self-status-v1"]},
        [],
        None,
    )


def make_client(tmp_path: Path, rows=None, database_now=None):
    connections = []

    def connect():
        conn = FakeConnection(rows if rows is not None else [make_row()], database_now=database_now)
        connections.append(conn)
        return conn

    app = create_admin_app(
        connect=connect,
        operator_password_hash=hash_operator_password("Correct Horse Battery 2030!"),
        session_db_path=str(tmp_path / "private" / "sessions.sqlite3"),
    )
    return TestClient(app, base_url="https://master.test"), connections


def test_packaged_panel_has_local_login_and_strict_script_csp() -> None:
    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    assert 'id="login-form"' in source
    assert '"/admin/v1/login"' in source
    assert '"/admin/v1/logout"' in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source
    csp = _panel_csp(panel)
    assert "script-src 'self' 'sha256-" in csp
    assert "script-src 'self' 'unsafe-inline'" not in csp


def test_root_serves_login_panel_same_origin(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.html"
    panel_path.write_text("<!doctype html><html lang='es'><body id='local-panel'>PC-MASTER</body></html>", encoding="utf-8")
    app = create_admin_app(
        connect=lambda: FakeConnection([]),
        operator_password_hash=hash_operator_password("Correct Horse Battery 2030!"),
        session_db_path=str(tmp_path / "private" / "sessions.sqlite3"),
        panel_path=panel_path,
    )
    client = TestClient(app, base_url="https://master.test")
    response = client.get("/")
    assert response.status_code == 200
    assert "PC-MASTER" in response.text
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert "connect-src 'self'" in response.headers["content-security-policy"]


def test_snapshots_require_auth_and_never_cache(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    response = client.get("/admin/v1/status/snapshots")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_login_requires_same_origin_and_valid_password(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    rejected = client.post(
        "/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://evil.test"},
    )
    assert rejected.status_code == 403
    invalid = client.post(
        "/admin/v1/login",
        json={"password": "incorrect"},
        headers={"Origin": "https://master.test"},
    )
    assert invalid.status_code == 401
    assert "set-cookie" not in invalid.headers


def test_login_get_snapshots_and_logout_revoke_session(tmp_path: Path) -> None:
    client, connections = make_client(tmp_path)
    login = client.post(
        "/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://master.test"},
    )
    assert login.status_code == 200
    assert login.json() == {"authenticated": True}
    cookie = login.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=strict" in cookie
    assert SESSION_COOKIE.lower() in cookie

    status = client.get("/admin/v1/session")
    assert status.json() == {"authenticated": True}
    response = client.get("/admin/v1/status/snapshots")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert len(body["snapshots"]) == 1
    assert body["snapshots"][0]["node"]["display_name"] == "WORKER-01"
    assert len(connections) == 1
    assert connections[0].statements[0][0].lstrip().upper().startswith("SELECT")

    logout = client.post("/admin/v1/logout", headers={"Origin": "https://master.test"})
    assert logout.status_code == 200
    assert client.get("/admin/v1/status/snapshots").status_code == 401


def test_validation_error_never_reflects_submitted_password(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    oversized_secret = "S" * 1025
    response = client.post(
        "/admin/v1/login",
        json={"password": oversized_secret},
        headers={"Origin": "https://master.test"},
    )
    assert response.status_code == 400
    assert response.json() == {"error": {"code": "INVALID_REQUEST"}}
    assert oversized_secret not in response.text


def test_login_rate_limit_and_https_required(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    for _ in range(5):
        response = client.post(
            "/admin/v1/login",
            json={"password": "wrong"},
            headers={"Origin": "https://master.test"},
        )
        assert response.status_code == 401
    limited = client.post(
        "/admin/v1/login",
        json={"password": "wrong"},
        headers={"Origin": "https://master.test"},
    )
    assert limited.status_code == 429

    http_client = TestClient(client.app, base_url="http://master.test")
    response = http_client.get("/admin/v1/session")
    assert response.status_code == 426


def test_empty_node_list_is_valid(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path, rows=[])
    client.post(
        "/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://master.test"},
    )
    response = client.get("/admin/v1/status/snapshots")
    assert response.status_code == 200
    assert response.json()["snapshots"] == []


def test_oversized_request_body_is_rejected_without_reflecting_content(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    oversized = b'{"password":"' + b"A" * 20_000 + b'"}'
    response = client.post(
        "/admin/v1/login",
        content=oversized,
        headers={
            "Origin": "https://master.test",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 413
    assert response.json() == {"error": {"code": "BODY_TOO_LARGE"}}
    assert "A" * 100 not in response.text


def test_panel_matches_preview_tabs_without_fabricating_real_workers() -> None:
    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    assert 'data-page="nodes"' in source
    assert 'data-page="tasks"' in source
    assert 'data-page="system"' in source
    assert "GeeLark-IA" in source and "PC-MASTER" in source
    assert "Redroid" in source and "Planificado" in source
    assert "No se mostrarán datos ficticios" in source
    assert "WORKER-DEMO-01" not in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source


def test_body_limit_middleware_propagates_disconnect_after_replaying_body() -> None:
    import asyncio

    from geelark_master_admin.app import BodyLimitMiddleware

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


def test_panel_node_search_visible_accessible_and_wired() -> None:
    from html.parser import HTMLParser

    source = (
        Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    ).read_text(encoding="utf-8")

    class ControlParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.inputs = []
            self.labels = []

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == "input" and attributes.get("id") == "node-search":
                self.inputs.append(attributes)
            if tag == "label" and attributes.get("for") == "node-search":
                self.labels.append(attributes)

    controls = ControlParser()
    controls.feed(source)
    assert len(controls.inputs) == 1
    assert controls.inputs[0]["type"] == "search"
    assert controls.labels and controls.labels[0]["class"] == "sr-only"
    assert 'el("node-search")?.addEventListener("input",render)' in source
    assert "const visibleNodes=filterNodes()" in source
    assert "Sin nodos que coincidan con la búsqueda." in source


@pytest.mark.parametrize("database_offset", [-3600, 3600])
def test_snapshots_use_database_clock_for_stale_heartbeat(tmp_path, database_offset):
    database_now = datetime.now(timezone.utc) + timedelta(seconds=database_offset)
    row = list(make_row())
    row[5] = database_now - timedelta(seconds=90)
    client, connections = make_client(tmp_path, rows=[tuple(row)], database_now=database_now)
    client.post(
        "/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://master.test"},
    )
    response = client.get("/admin/v1/status/snapshots")
    assert response.status_code == 200
    payload = response.json()
    snapshot = payload["snapshots"][0]
    expected = database_now.isoformat().replace("+00:00", "Z")
    assert payload["generated_at"] == snapshot["generated_at"] == expected
    assert snapshot["freshness"]["age_seconds"] == 90
    assert snapshot["freshness"]["state"] == "stale"
    assert snapshot["node"]["health_state"] == "offline"
    assert snapshot["node"]["reported_health_state"] == "healthy"
    assert len(connections[0].statements) == 2


def test_empty_snapshots_still_use_database_clock():
    from geelark_master_admin.app import _read_snapshots

    database_now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    generated_at, snapshots = _read_snapshots(
        lambda: FakeConnection([], database_now=database_now)
    )
    assert generated_at == "2020-01-01T00:00:00Z"
    assert snapshots == []


def test_snapshot_clock_failure_does_not_fall_back_to_local_time():
    from geelark_master_admin.app import _read_snapshots

    class UnavailableClock(FakeConnection):
        def execute(self, statement, params=()):
            if statement.strip().lower() == "select clock_timestamp()":
                raise RuntimeError("database clock unavailable")
            return super().execute(statement, params)

    with pytest.raises(RuntimeError, match="database clock unavailable"):
        _read_snapshots(lambda: UnavailableClock([]))


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requiere PostgreSQL desechable")
def test_admin_snapshots_read_reported_health_and_database_clock_in_postgres():
    import psycopg
    from geelark_master_admin.app import _read_snapshots

    dsn = os.environ["TEST_DATABASE_URL"]
    node_id = uuid4()
    with psycopg.connect(dsn, autocommit=True) as admin:
        try:
            admin.execute(
                """
                INSERT INTO geelark_control.nodes
                    (node_id, display_name, admin_state, health_state,
                     reported_health_state, last_seen_at)
                VALUES (%s, %s, 'active', 'healthy', 'unhealthy', clock_timestamp())
                """,
                (node_id, "SNAPSHOT-" + node_id.hex[:12]),
            )
            before = admin.execute("SELECT clock_timestamp()").fetchone()[0]
            generated_at, snapshots = _read_snapshots(lambda: psycopg.connect(dsn))
            after = admin.execute("SELECT clock_timestamp()").fetchone()[0]
            snapshot = next(item for item in snapshots if item["node"]["node_id"] == str(node_id))
            assert snapshot["node"]["reported_health_state"] == "unhealthy"
            assert snapshot["node"]["health_state"] == "degraded"
            assert snapshot["freshness"]["state"] == "fresh"
            assert snapshot["generated_at"] == generated_at
            observed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            assert before <= observed <= after
        finally:
            admin.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
