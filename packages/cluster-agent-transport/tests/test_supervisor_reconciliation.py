import threading
import time
from uuid import UUID

import pytest

from cluster_agent_transport.supervisor import AgentNodeSupervisor


class FakeReceiptSync:
    def __init__(self):
        self.started = 0
        self.stopped = 0
        self.reconnected = 0

    def start(self):
        self.started += 1

    def notify_reconnected(self):
        self.reconnected += 1

    def stop(self, *, timeout):
        self.stopped += 1
        return True


class FakeRuntime:
    def __init__(self, reconciliation_results=None, *, block_reconciliation=False):
        self.calls = []
        self.reconciliation_results = list(reconciliation_results or [])
        self.block_reconciliation = block_reconciliation
        self.reconciliation_started = threading.Event()
        self.release_reconciliation = threading.Event()
        self.lock = threading.Lock()

    def send_heartbeat(self, payload):
        with self.lock:
            self.calls.append(("heartbeat", payload))
        return object()

    def publish_capabilities(self, payload):
        with self.lock:
            self.calls.append(("capabilities", payload))
        return object()

    def read_status(self):
        with self.lock:
            self.calls.append(("status", None))
        return object()

    def reconcile_inventory(self, inventory, *, reconciliation_id=None):
        with self.lock:
            self.calls.append(("reconcile", (inventory, reconciliation_id)))
            result = self.reconciliation_results.pop(0) if self.reconciliation_results else {"ok": True}
        self.reconciliation_started.set()
        if self.block_reconciliation:
            self.release_reconciliation.wait(3)
        if isinstance(result, Exception):
            raise result
        return result


def metrics():
    return {
        "cpu_load_percent": 10.0,
        "memory_total_bytes": 1000,
        "memory_available_bytes": 500,
        "storage_available_bytes": 2000,
    }


def wait_for(predicate, timeout=2.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def make_supervisor(runtime, inventory_provider, *, errors=None, on_reconciliation=None, retry=1.0):
    sync = FakeReceiptSync()
    supervisor = AgentNodeSupervisor(
        runtime=runtime,
        receipt_sync=sync,
        agent_version="0.1.0",
        capabilities=["heartbeat", "status", "receipt_sync"],
        heartbeat_interval_seconds=1.0,
        capabilities_interval_seconds=1.0,
        status_interval_seconds=1.0,
        metrics_provider=metrics,
        reconcile_inventory=inventory_provider,
        on_reconciliation=on_reconciliation,
        reconciliation_retry_interval_seconds=retry,
        on_error=(errors.append if errors is not None else None),
    )
    return supervisor, sync


def test_reconciliation_runs_in_separate_worker_without_blocking_telemetry():
    runtime = FakeRuntime(block_reconciliation=True)
    supervisor, sync = make_supervisor(runtime, lambda: [{"task_id": "local-1"}])
    supervisor.start()
    assert runtime.reconciliation_started.wait(1)
    with runtime.lock:
        before = sum(kind == "heartbeat" for kind, _ in runtime.calls)
    assert wait_for(lambda: sum(kind == "heartbeat" for kind, _ in runtime.calls) > before, timeout=1.8)
    runtime.release_reconciliation.set()
    assert supervisor.stop(timeout=2)
    assert sync.started == 1 and sync.stopped == 1


def test_failed_reconciliation_reuses_id_and_snapshot_until_acknowledged():
    runtime = FakeRuntime([OSError("network unavailable"), {"ok": True}])
    errors = []
    provider_calls = []
    inventory = [{"task_id": "local-1", "local_state": "unknown"}]

    def provider():
        provider_calls.append(1)
        return inventory

    supervisor, _ = make_supervisor(runtime, provider, errors=errors, retry=1.0)
    supervisor.start()
    assert wait_for(lambda: len([x for x in runtime.calls if x[0] == "reconcile"]) >= 2, timeout=3.5)
    with runtime.lock:
        calls = [payload for kind, payload in runtime.calls if kind == "reconcile"]
    assert calls[0][0] == calls[1][0] == inventory
    assert calls[0][1] == calls[1][1]
    assert isinstance(calls[0][1], UUID)
    assert provider_calls == [1]
    assert "RECONCILIATION_FAILED" in errors
    assert supervisor.stop(timeout=2)


def test_reconnect_starts_a_new_reconciliation_attempt():
    runtime = FakeRuntime()
    provider_calls = []

    def provider():
        provider_calls.append(len(provider_calls) + 1)
        return [{"task_id": f"local-{provider_calls[-1]}"}]

    supervisor, sync = make_supervisor(runtime, provider)
    supervisor.start()
    assert wait_for(lambda: len([x for x in runtime.calls if x[0] == "reconcile"]) == 1)
    supervisor.notify_reconnected()
    assert wait_for(lambda: len([x for x in runtime.calls if x[0] == "reconcile"]) == 2)
    with runtime.lock:
        calls = [payload for kind, payload in runtime.calls if kind == "reconcile"]
    assert calls[0][1] != calls[1][1]
    assert calls[0][0] != calls[1][0]
    assert len(provider_calls) == 2
    assert sync.reconnected == 1
    assert supervisor.stop(timeout=2)


@pytest.mark.parametrize("retry", [0, 0.5, 3601, float("nan"), float("inf"), True])
def test_invalid_reconciliation_retry_interval_is_rejected(retry):
    with pytest.raises(ValueError, match="reconciliation_retry_interval_seconds"):
        make_supervisor(FakeRuntime(), lambda: [], retry=retry)
