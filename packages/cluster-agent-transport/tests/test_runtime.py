from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from cluster_agent_transport.client import AgentResponse, AgentTransportError
from cluster_agent_transport.runtime import AgentTransportRuntime


class FakeClient:
    def __init__(self, *, response=None, error=None, events=None):
        self.response = response or AgentResponse(200, b'{"ok":true}', "application/json")
        self.error = error
        self.events = events if events is not None else []
        self.requests = []

    def request(self, method, path, *, payload=None, headers=None):
        self.events.append("network")
        self.requests.append((method, path, payload, dict(headers or {})))
        if self.error:
            raise self.error
        return self.response


class FakeJournal:
    def __init__(self, events=None):
        self.events = events if events is not None else []
        self.calls = []
        self.pending = []
        self.synced = []

    def list_pending_receipts(self, *, limit=100):
        return self.pending[:limit]

    def mark_receipt_synced(self, operation_id):
        self.synced.append(operation_id)

    def record_result(self, **kwargs):
        self.events.append("journal")
        self.calls.append(kwargs)
        return SimpleNamespace(**kwargs)


def make_runtime(client, journal, node_id):
    return AgentTransportRuntime(
        client=client,
        bearer_token="a" * 64,
        journal=journal,
        local_node_id=node_id,
        clock=lambda: datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc),
    )


def test_terminal_result_is_journaled_before_send_and_retry_key_is_stable():
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    events = []
    client, journal = FakeClient(events=events), FakeJournal(events=events)
    runtime = make_runtime(client, journal, node_id)
    receipt = SimpleNamespace(
        node_id=node_id, instance_id=instance_id, operation_id=operation_id,
        assignment_epoch=3, status="succeeded", result={"exit_code": 0},
    )

    runtime.report_result(
        operation_id=operation_id, instance_id=instance_id, assignment_epoch=3,
        status="succeeded", result={"exit_code": 0},
    )
    first_key = client.requests[0][3]["Idempotency-Key"]
    assert events == ["journal", "network"]
    assert client.requests[0][1] == f"/agent/v1/tasks/{operation_id}/result"
    assert client.requests[0][3]["Authorization"] == "Bearer " + "a" * 64

    runtime.sync_receipt(receipt)
    second_key = client.requests[1][3]["Idempotency-Key"]
    assert first_key == second_key
    assert client.requests[1][3]["X-Agent-Nonce"] != client.requests[0][3]["X-Agent-Nonce"]
    # El reintento transmite el recibo durable existente; no crea otro registro local.
    assert len(journal.calls) == 1
    assert events == ["journal", "network", "network"]


def test_result_remains_durable_when_network_is_offline():
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    events = []
    client = FakeClient(error=AgentTransportError("offline"), events=events)
    journal = FakeJournal(events=events)
    runtime = make_runtime(client, journal, node_id)

    with pytest.raises(AgentTransportError):
        runtime.report_result(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=1,
            status="failed", result={"error_code": "WORKER_FAILED"},
        )
    assert events == ["journal", "network"]
    assert journal.calls[0]["status"] == "failed"
    assert journal.calls[0]["result"] == {"error_code": "WORKER_FAILED"}


def test_pending_receipt_is_not_sent_as_a_task_result():
    node_id = uuid4()
    client, journal = FakeClient(), FakeJournal()
    runtime = make_runtime(client, journal, node_id)
    receipt = SimpleNamespace(
        node_id=node_id, instance_id=uuid4(), operation_id=uuid4(),
        assignment_epoch=1, status="accepted", result=None,
    )
    assert runtime.sync_receipt(receipt) is None
    assert client.requests == []
    assert journal.calls == []


def test_non_success_http_response_is_reported_without_response_body():
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    client = FakeClient(response=AgentResponse(403, b'{"secret":"must-not-leak"}', "application/json"))
    runtime = make_runtime(client, FakeJournal(), node_id)
    with pytest.raises(AgentTransportError) as exc:
        runtime.report_result(
            operation_id=operation_id, instance_id=instance_id, assignment_epoch=1,
            status="succeeded", result={"ok": True},
        )
    assert "must-not-leak" not in str(exc.value)
    assert "403" in str(exc.value)



def test_sync_pending_receipts_marks_terminal_ack_and_stops_when_offline():
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    journal = FakeJournal()
    journal.pending = [
        SimpleNamespace(
            node_id=node_id, instance_id=instance_id, operation_id=operation_id,
            assignment_epoch=4, status="succeeded", result={"ok": True},
        ),
        SimpleNamespace(
            node_id=node_id, instance_id=uuid4(), operation_id=uuid4(),
            assignment_epoch=4, status="failed", result={"error_code": "X"},
        ),
    ]
    client = FakeClient()
    runtime = make_runtime(client, journal, node_id)
    confirmed, attempted = runtime.sync_pending_receipts(limit=10)
    assert (confirmed, attempted) == (2, 2)
    assert journal.synced == [operation_id, journal.pending[1].operation_id]

    offline_journal = FakeJournal()
    offline_journal.pending = journal.pending
    offline_client = FakeClient(error=AgentTransportError("offline"))
    offline_runtime = make_runtime(offline_client, offline_journal, node_id)
    confirmed, attempted = offline_runtime.sync_pending_receipts(limit=10)
    assert (confirmed, attempted) == (0, 1)
    assert offline_journal.synced == []



def test_runtime_syncs_real_sqlite_journal_and_persists_terminal_ack(tmp_path):
    guard = pytest.importorskip("geelark_cluster_agent_guard")
    if not callable(getattr(guard.AgentJournal, "list_pending_receipts", None)) or not callable(
        getattr(guard.AgentJournal, "mark_receipt_synced", None)
    ):
        pytest.skip("la rama base aún no incluye la API de recibos del PR #38")
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    journal = guard.AgentJournal(tmp_path / "journal.sqlite3", node_id)
    journal.initialize()
    command = guard.AgentCommand(
        operation_id=operation_id,
        instance_id=instance_id,
        node_id=node_id,
        assignment_epoch=1,
        lease_expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        payload={"kind": "test-only"},
    )
    journal.accept_command(command)
    journal.record_result(
        operation_id=operation_id,
        instance_id=instance_id,
        node_id=node_id,
        assignment_epoch=1,
        status="succeeded",
        result={"test": True},
    )

    runtime = make_runtime(FakeClient(), journal, node_id)
    assert len(journal.list_pending_receipts(limit=10)) == 1
    confirmed, attempted = runtime.sync_pending_receipts(limit=10)
    assert (confirmed, attempted) == (1, 1)
    assert journal.list_pending_receipts(limit=10) == []

    reopened = guard.AgentJournal(tmp_path / "journal.sqlite3", node_id)
    reopened.initialize()
    assert reopened.list_pending_receipts(limit=10) == []



def test_running_progress_ack_is_persisted_and_does_not_block_later_receipts():
    node_id, instance_id, operation_id = uuid4(), uuid4(), uuid4()
    journal = FakeJournal()
    journal.pending = [
        SimpleNamespace(
            node_id=node_id, instance_id=instance_id, operation_id=operation_id,
            assignment_epoch=1, status="running", result={"progress": 25},
        ),
        SimpleNamespace(
            node_id=node_id, instance_id=uuid4(), operation_id=uuid4(),
            assignment_epoch=1, status="succeeded", result={"ok": True},
        ),
    ]
    runtime = make_runtime(FakeClient(), journal, node_id)
    confirmed, attempted = runtime.sync_pending_receipts(limit=2)
    assert (confirmed, attempted) == (2, 2)
    assert journal.synced == [operation_id, journal.pending[1].operation_id]
