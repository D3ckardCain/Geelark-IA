from __future__ import annotations

import copy
import json
import shutil
import subprocess
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from geelark_master_admin import create_admin_app, hash_operator_password
from geelark_master_admin.app import SESSION_COOKIE, _panel_csp


class FakeConnection(AbstractContextManager):
    def __init__(self, rows):
        self.rows = rows
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
        assert params == (500,)
        return self

    def fetchall(self):
        return self.rows


def make_row(reported_health_state="healthy"):
    return (
        uuid4(),
        "WORKER-01",
        "active",
        reported_health_state,
        "1.0.0",
        datetime.now(timezone.utc),
        {"items": ["heartbeat-v1", "self-status-v1"]},
        [],
        None,
    )


def make_client(tmp_path: Path, rows=None):
    connections = []

    def connect():
        conn = FakeConnection(rows if rows is not None else [make_row()])
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
    query = connections[0].statements[0][0]
    assert query.lstrip().upper().startswith("SELECT")
    assert "reported_health_state" in query
    assert "health_state AS reported_health_state" not in query

    logout = client.post("/admin/v1/logout", headers={"Origin": "https://master.test"})
    assert logout.status_code == 200
    assert client.get("/admin/v1/status/snapshots").status_code == 401


def test_panel_preserves_reported_health_separately_from_derived_health(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path, rows=[make_row(reported_health_state="unhealthy")])
    login = client.post(
        "/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://master.test"},
    )
    assert login.status_code == 200
    response = client.get("/admin/v1/status/snapshots")
    assert response.status_code == 200
    node = response.json()["snapshots"][0]["node"]
    assert node["reported_health_state"] == "unhealthy"
    assert node["health_state"] == "degraded"


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


def test_panel_payload_validator_covers_contract_constraints() -> None:
    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    validator = source.split("function validatePayload(data){", 1)[1].split("\nfunction currentSnapshots()", 1)[0]
    # Contract guardrails: IDs/dates, enums, bounded arrays, exact object keys, and cross-field safety rules.
    for marker in (
        "snapshot_id", "uuid(s.snapshot_id)", "dt(s.generated_at)",
        "authorization_state", "authStates", "healthStates", "freshnessStates",
        "caps", "n.capabilities.length>32", "n.modules.length>128",
        "threshold_seconds>86400", "Object.keys(v)",
        "un snapshot sin frescura", "un nodo sin heartbeat",
    ):
        assert marker in validator, f"Falta una validación del contrato en el panel: {marker}"


def test_panel_payload_validator_rejects_malformed_payloads() -> None:
    node = shutil.which("node")
    if node is None:
        import pytest

        pytest.skip("Node.js no está disponible; la CI de GitHub sí lo proporciona.")

    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    start = source.index("function validatePayload(data){")
    end = source.index("\nfunction currentSnapshots()", start)
    validator = source[start:end]

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    valid = {
        "schema_version": "1.0",
        "generated_at": now,
        "snapshots": [
            {
                "schema_version": "1.0",
                "snapshot_id": str(uuid4()),
                "generated_at": now,
                "source": "master-live",
                "node": {
                    "node_id": str(uuid4()),
                    "display_name": "WORKER-TEST-01",
                    "authorization_state": "active",
                    "health_state": "healthy",
                    "last_heartbeat_at": now,
                    "agent_version": "1.0.0",
                    "capabilities": ["heartbeat-v1"],
                    "modules": [
                        {
                            "module_id": "agent-supervisor",
                            "state": "operational",
                            "version": "1.0.0",
                            "checked_at": now,
                            "source": "agent-report",
                            "error_code": None,
                        }
                    ],
                    "reported_health_state": "healthy",
                },
                "freshness": {
                    "state": "fresh",
                    "age_seconds": 0,
                    "threshold_seconds": 90,
                    "observed_at": now,
                },
            }
        ],
    }

    script = (
        validator
        + "\nconst data=JSON.parse(process.argv[1]);"
        + "\ntry { const result=validatePayload(data);"
        + " process.stdout.write(JSON.stringify({ok:true,count:result.length}));"
        + " } catch (error) { process.stdout.write(JSON.stringify({ok:false}));"
        + " process.exitCode=1; }"
    )

    def run(payload: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [node, "-e", script, json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    accepted = run(valid)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout) == {"ok": True, "count": 1}

    malformed = []
    bad_uuid = copy.deepcopy(valid)
    bad_uuid["snapshots"][0]["snapshot_id"] = "not-a-uuid"
    malformed.append(bad_uuid)

    bad_enum = copy.deepcopy(valid)
    bad_enum["snapshots"][0]["node"]["authorization_state"] = "root"
    malformed.append(bad_enum)

    bad_capability = copy.deepcopy(valid)
    bad_capability["snapshots"][0]["node"]["capabilities"].append("shell-v1")
    malformed.append(bad_capability)

    extra_field = copy.deepcopy(valid)
    extra_field["snapshots"][0]["node"]["untrusted"] = True
    malformed.append(extra_field)

    stale_but_healthy = copy.deepcopy(valid)
    stale_but_healthy["snapshots"][0]["freshness"]["state"] = "stale"
    malformed.append(stale_but_healthy)

    bad_module_state = copy.deepcopy(valid)
    bad_module_state["snapshots"][0]["node"]["modules"][0]["state"] = "running"
    malformed.append(bad_module_state)

    bad_date = copy.deepcopy(valid)
    bad_date["generated_at"] = "not-a-date"
    malformed.append(bad_date)

    duplicate_capability = copy.deepcopy(valid)
    duplicate_capability["snapshots"][0]["node"]["capabilities"].append("heartbeat-v1")
    malformed.append(duplicate_capability)

    too_many = copy.deepcopy(valid)
    too_many["snapshots"] = too_many["snapshots"] * 501
    malformed.append(too_many)

    for payload in malformed:
        rejected = run(payload)
        assert rejected.returncode == 1
        assert json.loads(rejected.stdout) == {"ok": False}
