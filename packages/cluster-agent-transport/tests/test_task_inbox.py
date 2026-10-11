from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from cluster_agent_transport.domain_handlers import make_postgres_agent_handlers
from cluster_agent_transport.policy import AgentPrincipal, Operation


class FakeCursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        row = self.rows.pop(0) if self.rows else None
        return FakeCursor(row)


def test_claim_task_returns_durable_task_and_lease_only_for_active_node():
    node_id, credential_id = uuid4(), uuid4()
    task_id, operation_id, instance_id = uuid4(), uuid4(), uuid4()
    instance_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    delivery_lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=30)
    conn = FakeConnection([
        ("active", "active"),
        (task_id, operation_id, instance_id, 7, {"desired_state": "running"}, 2, instance_lease_expires_at),
        (delivery_lease_expires_at,),
    ])
    handlers = make_postgres_agent_handlers(lambda: conn)
    principal = AgentPrincipal(str(node_id), str(credential_id), "active", "active", datetime.now(timezone.utc) + timedelta(hours=1))

    response = handlers[Operation.TASK_FETCH](
        conn=conn, principal=principal, payload={"schema_version": 1}
    )

    assert response["task"]["task_id"] == str(task_id)
    assert response["task"]["operation_id"] == str(operation_id)
    assert response["task"]["instance_id"] == str(instance_id)
    assert response["task"]["node_id"] == str(node_id)
    assert response["task"]["assignment_epoch"] == 7
    assert response["task"]["delivery_attempt"] == 3
    assert response["task"]["lease_expires_at"] == delivery_lease_expires_at.isoformat()
    assert response["task"]["instance_lease_expires_at"] == instance_lease_expires_at.isoformat()
    assert "FOR UPDATE OF t, i, o SKIP LOCKED" in conn.calls[1][0]
    assert conn.calls[2][1] == (task_id,)


def test_pending_node_is_rejected_before_task_claim_query():
    node_id, credential_id = uuid4(), uuid4()
    conn = FakeConnection([("pending", "pending")])
    handlers = make_postgres_agent_handlers(lambda: conn)
    principal = AgentPrincipal(str(node_id), str(credential_id), "pending", "pending")

    with pytest.raises(HTTPException) as exc:
        handlers[Operation.TASK_FETCH](
            conn=conn, principal=principal, payload={"schema_version": 1}
        )

    assert exc.value.status_code == 403
    assert len(conn.calls) == 1
