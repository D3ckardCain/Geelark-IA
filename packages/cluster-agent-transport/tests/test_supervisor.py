import threading
import time

import pytest

from cluster_agent_transport.supervisor import AgentNodeSupervisor


class FakeRuntime:
    def __init__(self):
        self.calls = []
        self.called = threading.Event()
        self.lock = threading.Lock()

    def send_heartbeat(self, payload):
        with self.lock:
            self.calls.append(("heartbeat", payload))
        self.called.set()
        return object()

    def publish_capabilities(self, payload):
        with self.lock:
            self.calls.append(("capabilities", payload))
        self.called.set()
        return object()

    def read_status(self):
        with self.lock:
            self.calls.append(("status", None))
        self.called.set()
        return object()


class FakeReceiptSync:
    def __init__(self):
        self.started = 0
        self.stopped = 0
        self.reconnected = 0

    def start(self):
        self.started += 1

    def stop(self, *, timeout):
        self.stopped += 1
        return True

    def notify_reconnected(self):
        self.reconnected += 1


def metrics():
    return {
        "cpu_load_percent": 12.5,
        "memory_total_bytes": 1000,
        "memory_available_bytes": 400,
        "storage_available_bytes": 5000,
    }


def wait_for(runtime, kind, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with runtime.lock:
            if any(item[0] == kind for item in runtime.calls):
                return True
        time.sleep(0.005)
    return False


def make_supervisor(runtime=None, sync=None, **kwargs):
    runtime = runtime or FakeRuntime()
    sync = sync or FakeReceiptSync()
    supervisor = AgentNodeSupervisor(
        runtime=runtime,
        receipt_sync=sync,
        agent_version="0.1.0",
        capabilities=["heartbeat", "capabilities", "status", "receipt_sync"],
        heartbeat_interval_seconds=30,
        capabilities_interval_seconds=300,
        status_interval_seconds=60,
        metrics_provider=metrics,
        **kwargs,
    )
    return supervisor, runtime, sync


def test_start_reports_only_telemetry_and_stops_cooperatively():
    supervisor, runtime, sync = make_supervisor()
    supervisor.start()
    assert wait_for(runtime, "heartbeat")
    assert wait_for(runtime, "capabilities")
    assert wait_for(runtime, "status")
    assert supervisor.stop(timeout=1)
    assert sync.started == 1
    assert sync.stopped == 1
    with runtime.lock:
        heartbeat = next(payload for kind, payload in runtime.calls if kind == "heartbeat")
        caps = next(payload for kind, payload in runtime.calls if kind == "capabilities")
        assert heartbeat == {
            "schema_version": 1,
            "agent_version": "0.1.0",
            "health_state": "healthy",
            **metrics(),
        }
        assert caps["capabilities"] == ["heartbeat", "capabilities", "status", "receipt_sync"]
        assert all(kind in {"heartbeat", "capabilities", "status"} for kind, _ in runtime.calls)


def test_reconnect_notifies_receipt_sync_and_wakes_telemetry():
    supervisor, runtime, sync = make_supervisor()
    supervisor.start()
    assert wait_for(runtime, "heartbeat")
    with runtime.lock:
        before = sum(kind == "heartbeat" for kind, _ in runtime.calls)
    supervisor.notify_reconnected()
    assert sync.reconnected == 1
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        with runtime.lock:
            after = sum(kind == "heartbeat" for kind, _ in runtime.calls)
        if after > before:
            break
        time.sleep(0.005)
    assert after > before
    assert supervisor.stop(timeout=1)


def test_failure_reports_only_generic_code_and_does_not_crash_thread():
    class BrokenRuntime(FakeRuntime):
        def send_heartbeat(self, payload):
            raise RuntimeError("token=super-secret HTTP body")

    errors = []
    runtime = BrokenRuntime()
    supervisor, _, _ = make_supervisor(runtime=runtime, on_error=errors.append)
    supervisor.start()
    assert wait_for(runtime, "capabilities")
    assert "HEARTBEAT_FAILED" in errors
    assert all("super-secret" not in error for error in errors)
    assert supervisor.stop(timeout=1)


@pytest.mark.parametrize("kwargs", [
    {"heartbeat_interval_seconds": 0},
    {"capabilities_interval_seconds": float("nan")},
    {"status_interval_seconds": float("inf")},
    {"agent_version": ""},
    {"capabilities": ["status", "status"]},
])
def test_invalid_supervisor_configuration_is_rejected(kwargs):
    runtime = FakeRuntime()
    sync = FakeReceiptSync()
    base = {
        "runtime": runtime,
        "receipt_sync": sync,
        "agent_version": "0.1.0",
        "capabilities": ["status"],
    }
    base.update(kwargs)
    with pytest.raises(ValueError):
        AgentNodeSupervisor(**base, metrics_provider=metrics)
