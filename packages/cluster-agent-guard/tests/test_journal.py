from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from dataclasses import replace
import os
import stat
from uuid import UUID, uuid4

import pytest

from geelark_cluster_agent_guard import (
    AgentCommand,
    AgentGuardError,
    AgentJournal,
    AssignmentOwnerConflict,
    ExpiredAssignmentLease,
    InvalidAgentCommand,
    OperationIdConflict,
    OperationResultConflict,
    StaleAssignmentEpoch,
    StaleOperationResult,
)

LOCAL_NODE = UUID("22222222-2222-4222-8222-222222222222")
OTHER_NODE = UUID("33333333-3333-4333-8333-333333333333")
INSTANCE = UUID("66666666-6666-4666-8666-666666666666")


def command(*, epoch=1, node_id=LOCAL_NODE, operation_id=None, payload=None):
    return AgentCommand(
        operation_id=operation_id or uuid4(),
        instance_id=INSTANCE,
        node_id=node_id,
        assignment_epoch=epoch,
        lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        payload=payload if payload is not None else {"action": "start", "engine": "test-engine"},
    )


def test_acceptance_is_durable_and_duplicate_does_not_create_second_receipt(tmp_path):
    path = tmp_path / "agent-journal.sqlite3"
    journal = AgentJournal(path, LOCAL_NODE)
    journal.initialize()
    cmd = command()

    first = journal.accept_command(cmd)
    assert first.status == "accepted"
    assert first.duplicate is False

    reopened = AgentJournal(path, LOCAL_NODE)
    reopened.initialize()
    second = reopened.accept_command(cmd)
    assert second.status == "accepted"
    assert second.duplicate is True
    assert reopened.get_fence(INSTANCE) == (LOCAL_NODE, 1)


def test_reusing_operation_id_with_different_payload_is_conflict(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    operation_id = uuid4()
    journal.accept_command(command(operation_id=operation_id, payload={"action": "start"}))

    with pytest.raises(OperationIdConflict):
        journal.accept_command(command(operation_id=operation_id, payload={"action": "stop"}))


def test_older_epoch_is_rejected_after_newer_epoch_is_persisted(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    journal.accept_command(command(epoch=4))
    journal.accept_command(command(epoch=5))

    with pytest.raises(StaleAssignmentEpoch):
        journal.accept_command(command(epoch=4))


def test_same_epoch_cannot_switch_owner_between_local_node_identities(tmp_path):
    path = tmp_path / "journal.sqlite3"
    first_node = AgentJournal(path, LOCAL_NODE)
    first_node.initialize()
    first_node.accept_command(command(epoch=3, node_id=LOCAL_NODE))

    second_node = AgentJournal(path, OTHER_NODE)
    second_node.initialize()
    with pytest.raises(AssignmentOwnerConflict):
        second_node.accept_command(command(epoch=3, node_id=OTHER_NODE))


def test_old_epoch_result_cannot_modify_receipt_after_fence_advances(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    old = command(epoch=1)
    journal.accept_command(old)
    journal.accept_command(command(epoch=2))

    with pytest.raises(StaleOperationResult):
        journal.record_result(
            operation_id=old.operation_id,
            instance_id=old.instance_id,
            node_id=old.node_id,
            assignment_epoch=old.assignment_epoch,
            status="succeeded",
            result={"ok": True},
        )
    assert journal.get_receipt(old.operation_id).status == "accepted"


def test_terminal_result_is_idempotent_but_cannot_change(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    cmd = command()
    journal.accept_command(cmd)

    first = journal.record_result(
        operation_id=cmd.operation_id,
        instance_id=cmd.instance_id,
        node_id=cmd.node_id,
        assignment_epoch=cmd.assignment_epoch,
        status="succeeded",
        result={"ok": True},
    )
    assert first.status == "succeeded"
    duplicate = journal.record_result(
        operation_id=cmd.operation_id,
        instance_id=cmd.instance_id,
        node_id=cmd.node_id,
        assignment_epoch=cmd.assignment_epoch,
        status="succeeded",
        result={"ok": True},
    )
    assert duplicate.duplicate is True

    with pytest.raises(OperationResultConflict):
        journal.record_result(
            operation_id=cmd.operation_id,
            instance_id=cmd.instance_id,
            node_id=cmd.node_id,
            assignment_epoch=cmd.assignment_epoch,
            status="failed",
            result={"ok": False},
        )


def test_non_finite_json_is_rejected(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    with pytest.raises(InvalidAgentCommand):
        journal.accept_command(command(payload={"value": float("nan")}))


def test_command_for_another_node_is_rejected(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    with pytest.raises(InvalidAgentCommand):
        journal.accept_command(command(node_id=OTHER_NODE))


def test_concurrent_epoch_updates_leave_highest_epoch_as_fence(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    commands = [command(epoch=1), command(epoch=2)]

    def accept(cmd):
        try:
            return journal.accept_command(cmd).status
        except StaleAssignmentEpoch:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(accept, commands))

    assert all(result in {"accepted", "stale"} for result in results)
    assert journal.get_fence(INSTANCE) == (LOCAL_NODE, 2)


def test_expired_lease_is_rejected_before_persisting_command(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    expired = replace(
        command(),
        lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    with pytest.raises(ExpiredAssignmentLease):
        journal.accept_command(expired)
    assert journal.get_fence(INSTANCE) is None
    assert journal.get_receipt(expired.operation_id) is None


@pytest.mark.skipif(os.name == "nt", reason="permisos POSIX no aplican igual en Windows")
def test_journal_file_permissions_are_owner_only(tmp_path):
    path = tmp_path / "private-journal.sqlite3"
    journal = AgentJournal(path, LOCAL_NODE)
    journal.initialize()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="symlinks requieren permisos especiales en algunos Windows")
def test_journal_rejects_symlink_path(tmp_path):
    target = tmp_path / "target.sqlite3"
    target.write_bytes(b"")
    link = tmp_path / "linked.sqlite3"
    link.symlink_to(target)
    with pytest.raises(AgentGuardError):
        AgentJournal(link, LOCAL_NODE).initialize()



def test_pending_receipts_are_bounded_stable_and_acknowledged_versions_requeue(tmp_path):
    journal = AgentJournal(tmp_path / "journal.sqlite3", LOCAL_NODE)
    journal.initialize()
    accepted = command()
    journal.accept_command(accepted)
    running = command()
    journal.accept_command(running)
    journal.record_result(
        operation_id=running.operation_id,
        instance_id=running.instance_id,
        node_id=running.node_id,
        assignment_epoch=running.assignment_epoch,
        status="running",
        result={"progress": 25},
    )
    terminal = command()
    journal.accept_command(terminal)
    journal.record_result(
        operation_id=terminal.operation_id,
        instance_id=terminal.instance_id,
        node_id=terminal.node_id,
        assignment_epoch=terminal.assignment_epoch,
        status="succeeded",
        result={"ok": True},
    )

    pending = journal.list_pending_receipts(limit=10)
    assert {receipt.operation_id for receipt in pending} == {running.operation_id, terminal.operation_id}
    assert all(receipt.node_id == LOCAL_NODE for receipt in pending)
    assert [r.operation_id for r in journal.list_pending_receipts(limit=1)] == [
        pending[0].operation_id
    ]

    journal.mark_receipt_synced(terminal.operation_id)
    journal.mark_receipt_synced(running.operation_id)
    assert journal.list_pending_receipts(limit=10) == []

    # Una actualización posterior del mismo progreso debe volver a la cola.
    journal.record_result(
        operation_id=running.operation_id,
        instance_id=running.instance_id,
        node_id=running.node_id,
        assignment_epoch=running.assignment_epoch,
        status="running",
        result={"progress": 50},
    )
    requeued = journal.list_pending_receipts(limit=10)
    assert len(requeued) == 1
    assert requeued[0].operation_id == running.operation_id
    assert requeued[0].result == {"progress": 50}

    with pytest.raises(ValueError):
        journal.list_pending_receipts(limit=0)
    with pytest.raises(ValueError):
        journal.list_pending_receipts(limit=True)


def test_synced_receipt_ack_survives_journal_reopen(tmp_path):
    path = tmp_path / "journal.sqlite3"
    journal = AgentJournal(path, LOCAL_NODE)
    journal.initialize()
    cmd = command()
    journal.accept_command(cmd)
    journal.record_result(
        operation_id=cmd.operation_id,
        instance_id=cmd.instance_id,
        node_id=cmd.node_id,
        assignment_epoch=cmd.assignment_epoch,
        status="succeeded",
        result={"ok": True},
    )
    journal.mark_receipt_synced(cmd.operation_id)

    reopened = AgentJournal(path, LOCAL_NODE)
    reopened.initialize()
    assert reopened.list_pending_receipts(limit=100) == []
