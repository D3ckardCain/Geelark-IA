"""Consulta administrativa de tareas: sesión, filtros, metadatos y permisos reales."""
from contextlib import AbstractContextManager
from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from geelark_master_admin import create_admin_app, hash_operator_password
from geelark_master_admin.app import TASK_COLUMNS


def task_row():
    now = datetime.now(timezone.utc)
    return (uuid4(), uuid4(), uuid4(), uuid4(), 3, "failed", 2,
            now, now, now, now, now, "ENGINE_UNAVAILABLE")


class TaskConnection(AbstractContextManager):
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, query, params=()):
        self.calls.append((query, params))
        assert query.lstrip().upper().startswith("SELECT")
        assert "*" not in query
        assert "payload" not in query and "result_summary" not in query
        return self
    def fetchall(self):
        return self.rows
    def fetchone(self):
        return (datetime.now(timezone.utc),)


def client_for(tmp_path, rows=()):
    connection = TaskConnection(rows)
    app = create_admin_app(connect=lambda: connection,
        operator_password_hash=hash_operator_password("Correct Horse Battery 2030!"),
        session_db_path=str(tmp_path / "private" / "sessions.sqlite3"))
    return TestClient(app, base_url="https://master.test"), connection


def login(client):
    assert client.post("/admin/v1/login",
        json={"password": "Correct Horse Battery 2030!"},
        headers={"Origin": "https://master.test"}).status_code == 200


def test_tasks_require_session_and_logout_revokes_access(tmp_path):
    client, connection = client_for(tmp_path)
    assert client.get("/admin/v1/tasks").status_code == 401
    assert connection.calls == []
    login(client)
    response = client.get("/admin/v1/tasks")
    assert response.status_code == 200
    assert response.json()["tasks"] == []
    assert response.headers["cache-control"] == "no-store, max-age=0"
    connection.calls.clear()
    client.post("/admin/v1/logout", headers={"Origin": "https://master.test"})
    assert client.get("/admin/v1/tasks").status_code == 401
    assert connection.calls == []
    assert client.post("/admin/v1/tasks").status_code == 405


def test_task_filters_pagination_and_metadata_only(tmp_path):
    row = task_row()
    client, connection = client_for(tmp_path, [row, row])
    login(client)
    response = client.get("/admin/v1/tasks", params={
        "node_id": str(row[2]), "status": "failed", "limit": 1, "offset": 50})
    assert response.status_code == 200
    payload = response.json()
    assert payload["has_more"] is True
    assert payload["offset"] == 50
    assert len(payload["tasks"]) == 1
    assert set(payload["tasks"][0]) == set(TASK_COLUMNS)
    assert payload["tasks"][0]["last_error_code"] == "ENGINE_UNAVAILABLE"
    query, params = connection.calls[0]
    assert "node_id = %s" in query and "status = %s" in query
    assert params == (row[2], "failed", 2, 50)
    assert "ORDER BY created_at DESC, task_id DESC" in query


@pytest.mark.parametrize("params", [
    {"node_id": "invalid"}, {"status": "failed' OR true --"},
    {"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 10001}])
def test_invalid_task_filters_never_query_database(tmp_path, params):
    client, connection = client_for(tmp_path)
    login(client)
    response = client.get("/admin/v1/tasks", params=params)
    assert response.status_code == 400
    assert response.json() == {"error": {"code": "INVALID_REQUEST"}}
    assert connection.calls == []


def test_task_error_code_does_not_reflect_arbitrary_text(tmp_path):
    row = list(task_row())
    row[-1] = "password=do-not-return"
    client, _ = client_for(tmp_path, [tuple(row)])
    login(client)
    response = client.get("/admin/v1/tasks")
    assert response.json()["tasks"][0]["last_error_code"] is None
    assert "do-not-return" not in response.text


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requiere PostgreSQL desechable")
def test_task_metadata_role_and_api_with_real_postgres():
    import psycopg
    from psycopg import sql
    from geelark_master_admin.app import _read_tasks

    dsn = os.environ["TEST_DATABASE_URL"]
    role = "task_reader_" + uuid4().hex
    password = uuid4().hex
    node_id, instance_id, operation_id, task_id = (uuid4() for _ in range(4))
    package = Path(__file__).parents[1]
    role_script = (package / "sql" / "MASTER_ADMIN_READONLY_ROLE.sql").read_text()
    verify_script = (package / "sql" / "verify_readonly_role.sql").read_text()
    with psycopg.connect(dsn, autocommit=True) as admin:
        try:
            admin.execute(role_script.replace("geelark_master_reader", role))
            admin.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
            admin.execute("INSERT INTO geelark_control.nodes(node_id, display_name) VALUES (%s, %s)",
                          (node_id, "TASK-" + node_id.hex[:12]))
            admin.execute("INSERT INTO geelark_control.instances(instance_id) VALUES (%s)", (instance_id,))
            admin.execute("""INSERT INTO geelark_control.operations
                (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type)
                VALUES (%s, %s, %s, %s, 1, 'assign')""", (operation_id, uuid4(), instance_id, node_id))
            admin.execute("""INSERT INTO geelark_control.agent_tasks
                (task_id, operation_id, node_id, instance_id, assignment_epoch, payload, result_summary)
                VALUES (%s, %s, %s, %s, 1, '{"password":"hidden-payload"}', '{"token":"hidden-result"}')""",
                (task_id, operation_id, node_id, instance_id))
            reader_dsn = psycopg.conninfo.make_conninfo(dsn, user=role, password=password)
            result = _read_tasks(lambda: psycopg.connect(reader_dsn),
                node_id=node_id, status="queued", limit=50, offset=0)
            assert [item["task_id"] for item in result["tasks"]] == [str(task_id)]
            assert "hidden" not in str(result)
            with psycopg.connect(reader_dsn, autocommit=True) as reader:
                reader.execute(verify_script)
                for query in ("SELECT payload FROM geelark_control.agent_tasks",
                              "SELECT result_summary FROM geelark_control.agent_tasks",
                              "SELECT * FROM geelark_control.agent_tasks"):
                    with pytest.raises(psycopg.errors.InsufficientPrivilege):
                        reader.execute(query)
                with pytest.raises((psycopg.errors.InsufficientPrivilege, psycopg.errors.ReadOnlySqlTransaction)):
                    reader.execute("UPDATE geelark_control.agent_tasks SET status='failed' WHERE false")
            # El verificador debe detectar incluso un grant de una sola columna sensible.
            admin.execute(sql.SQL("GRANT SELECT(payload) ON geelark_control.agent_tasks TO {}").format(sql.Identifier(role)))
            with psycopg.connect(reader_dsn, autocommit=True) as reader:
                with pytest.raises(psycopg.errors.RaiseException, match="Columnas no permitidas"):
                    reader.execute(verify_script)
                reader.execute("ROLLBACK")
        finally:
            admin.execute("DELETE FROM geelark_control.agent_tasks WHERE task_id=%s", (task_id,))
            admin.execute("DELETE FROM geelark_control.operations WHERE operation_id=%s", (operation_id,))
            admin.execute("DELETE FROM geelark_control.instances WHERE instance_id=%s", (instance_id,))
            admin.execute("DELETE FROM geelark_control.nodes WHERE node_id=%s", (node_id,))
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
