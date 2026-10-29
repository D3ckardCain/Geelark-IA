import logging
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
    {"heartbeat_interval_seconds": -1},
    {"heartbeat_interval_seconds": True},
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



def test_default_diagnostics_log_only_generic_error_codes(caplog):
    class BrokenRuntime(FakeRuntime):
        def send_heartbeat(self, payload):
            raise RuntimeError("bearer=super-secret response-body")

    runtime = BrokenRuntime()
    supervisor, _, _ = make_supervisor(runtime=runtime)
    with caplog.at_level(logging.WARNING, logger="geelark_agent"):
        supervisor.start()
        assert wait_for(runtime, "capabilities")
        assert supervisor.stop(timeout=1)

    assert "HEARTBEAT_FAILED" in caplog.text
    assert "super-secret" not in caplog.text
    assert "response-body" not in caplog.text


def test_capabilities_failure_does_not_stop_heartbeat_or_status():
    class BrokenCapabilitiesRuntime(FakeRuntime):
        def publish_capabilities(self, payload):
            raise RuntimeError("sensitive response body")

    runtime = BrokenCapabilitiesRuntime()
    errors = []
    supervisor, _, _ = make_supervisor(runtime=runtime, on_error=errors.append)
    supervisor.start()
    assert wait_for(runtime, "heartbeat")
    assert wait_for(runtime, "status")
    assert "CAPABILITIES_FAILED" in errors
    assert supervisor.stop(timeout=1)


def test_error_callback_can_request_shutdown_without_self_join():
    callback_called = threading.Event()
    stop_results = []
    supervisor = None

    class BrokenHeartbeatRuntime(FakeRuntime):
        def send_heartbeat(self, payload):
            raise RuntimeError("secret")

    def on_error(code):
        if code == "HEARTBEAT_FAILED":
            stop_results.append(supervisor.stop(timeout=1))
            callback_called.set()

    supervisor, _, sync = make_supervisor(
        runtime=BrokenHeartbeatRuntime(),
        on_error=on_error,
    )
    supervisor.start()
    assert callback_called.wait(1)
    assert stop_results == [False]
    thread = supervisor._thread
    assert thread is not None
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert sync.stopped == 1


def test_receipt_sync_wake_failure_is_reported_and_telemetry_still_wakes():
    supervisor, runtime, sync = make_supervisor()
    errors = []

    def fail_wake():
        raise RuntimeError("private receipt detail")

    sync.notify_reconnected = fail_wake
    supervisor.on_error = errors.append
    supervisor.start()
    assert wait_for(runtime, "heartbeat")
    with runtime.lock:
        before = sum(kind == "heartbeat" for kind, _ in runtime.calls)
    supervisor.notify_reconnected()
    assert "RECEIPT_SYNC_WAKE_FAILED" in errors
    assert wait_for(runtime, "status")
    deadline = time.monotonic() + 1
    after = before
    while time.monotonic() < deadline:
        with runtime.lock:
            after = sum(kind == "heartbeat" for kind, _ in runtime.calls)
        if after > before:
            break
        time.sleep(0.005)
    assert after > before
    assert supervisor.stop(timeout=1)


def test_raising_error_observer_does_not_terminate_telemetry_thread():
    class BrokenHeartbeatRuntime(FakeRuntime):
        def send_heartbeat(self, payload):
            raise RuntimeError("sensitive token data")

    supervisor, runtime, _ = make_supervisor(
        runtime=BrokenHeartbeatRuntime(),
        on_error=lambda _code: (_ for _ in ()).throw(RuntimeError("observer failed")),
    )
    supervisor.start()
    assert wait_for(runtime, "capabilities")
    assert wait_for(runtime, "status")
    assert supervisor.stop(timeout=1)


def test_start_is_single_use_and_stop_before_start_is_final():
    supervisor, runtime, sync = make_supervisor()
    supervisor.start()
    assert wait_for(runtime, "heartbeat")
    with pytest.raises(RuntimeError, match="ya se inició o se detuvo"):
        supervisor.start()
    assert supervisor.stop(timeout=1)
    assert sync.started == 1
    assert sync.stopped == 1

    fresh, _, fresh_sync = make_supervisor()
    assert fresh.stop(timeout=1)
    with pytest.raises(RuntimeError, match="ya se inició o se detuvo"):
        fresh.start()
    assert fresh_sync.started == 0


@pytest.mark.parametrize(
    ("reported_metrics", "expected_health"),
    [
        ({"memory_total_bytes": 0, "memory_available_bytes": 0}, "unknown"),
        ({"memory_available_bytes": 0}, "degraded"),
        ({"storage_available_bytes": 0}, "degraded"),
        ({}, "healthy"),
    ],
)
def test_heartbeat_never_reports_healthy_with_unknown_or_exhausted_critical_resources(
    reported_metrics, expected_health,
):
    # Un Worker con métricas ausentes puede estar conectado, pero no debe
    # anunciar salud sana y habilitar el claim de tareas.
    supervisor, runtime, _sync = make_supervisor()
    snapshot = {**metrics(), **reported_metrics}
    supervisor.metrics_provider = lambda: snapshot
    supervisor._heartbeat()
    with runtime.lock:
        sent = [payload for kind, payload in runtime.calls if kind == "heartbeat"]
    assert len(sent) == 1
    assert sent[0]["health_state"] == expected_health
    assert sent[0]["memory_total_bytes"] == snapshot["memory_total_bytes"]
    assert sent[0]["storage_available_bytes"] == snapshot["storage_available_bytes"]


def test_unreadable_linux_memory_and_storage_do_not_produce_false_healthy(monkeypatch, tmp_path):
    import cluster_agent_transport.supervisor as module

    actual_open = module.Path.open

    def deny_meminfo(path, *args, **kwargs):
        if str(path) == "/proc/meminfo":
            raise OSError("unavailable")
        return actual_open(path, *args, **kwargs)

    def deny_disk(_path):
        raise OSError("unavailable")

    monkeypatch.setattr(module.Path, "open", deny_meminfo)
    monkeypatch.setattr(module, "shutil_disk_usage", deny_disk)

    fallback_snapshot = module.linux_resource_snapshot(tmp_path)
    assert fallback_snapshot["memory_total_bytes"] == 0
    assert fallback_snapshot["storage_available_bytes"] == 0

    supervisor, runtime, _sync = make_supervisor()
    supervisor.metrics_provider = lambda: fallback_snapshot
    supervisor._heartbeat()
    with runtime.lock:
        sent = [payload for kind, payload in runtime.calls if kind == "heartbeat"]
    assert len(sent) == 1
    assert sent[0]["health_state"] == "unknown"
