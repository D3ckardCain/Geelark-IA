import threading
import time

import pytest

from cluster_agent_transport.supervisor import AgentSupervisor


class FakeLifecycle:
    def __init__(self):
        self.starts = 0
        self.reconnections = 0
        self.fail_reconnections = False
        self.stops = []
        self.started = threading.Event()

    def start(self):
        self.starts += 1
        self.started.set()

    def notify_reconnected(self):
        self.reconnections += 1
        if self.fail_reconnections:
            raise RuntimeError("sincronizador detenido")

    def stop(self, *, timeout=5):
        self.stops.append(timeout)
        return True


class FakeRuntime:
    def __init__(self, heartbeat=None, capabilities=None, reconcile_responses=None):
        self.heartbeat = list(heartbeat or [])
        self.capabilities = list(capabilities or [])
        self.reconcile_responses = list(reconcile_responses or [])
        self.heartbeat_calls = []
        self.capability_calls = []
        self.reconcile_calls = []
        self.lock = threading.Lock()
        self.called = threading.Event()

    def send_heartbeat(self, payload):
        with self.lock:
            self.heartbeat_calls.append(payload)
            item = self.heartbeat.pop(0) if self.heartbeat else None
        self.called.set()
        if isinstance(item, Exception):
            raise item
        return object()

    def publish_capabilities(self, payload):
        with self.lock:
            self.capability_calls.append(payload)
            item = self.capabilities.pop(0) if self.capabilities else None
        self.called.set()
        if isinstance(item, Exception):
            raise item
        return object()

    def reconcile_inventory(self, inventory):
        with self.lock:
            self.reconcile_calls.append(inventory)
            item = self.reconcile_responses.pop(0) if self.reconcile_responses else {"ok": True}
        self.called.set()
        if isinstance(item, Exception):
            raise item
        return item


def wait_for(predicate, timeout=1):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def test_start_runs_heartbeat_and_capabilities_and_stops_both_cycles():
    runtime = FakeRuntime()
    lifecycle = FakeLifecycle()
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {"health_state": "healthy"},
        capabilities_payload=lambda: {"capabilities_version": 1, "capabilities": ["heartbeat"]},
        heartbeat_interval_seconds=0.2,
    )

    supervisor.start()
    assert runtime.called.wait(1)
    assert wait_for(lambda: len(runtime.capability_calls) >= 1)
    assert runtime.heartbeat_calls[0] == {"health_state": "healthy"}
    assert runtime.capability_calls[0]["capabilities_version"] == 1
    assert lifecycle.starts == 1
    assert supervisor.stop(timeout=1)
    assert lifecycle.stops
    assert not supervisor.running


def test_heartbeat_recovery_notifies_receipt_lifecycle():
    runtime = FakeRuntime(heartbeat=[OSError("offline"), None])
    lifecycle = FakeLifecycle()
    errors = []
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {"health_state": "healthy"},
        capabilities_payload=lambda: {"capabilities_version": 1, "capabilities": []},
        heartbeat_interval_seconds=0.5,
        on_error=errors.append,
    )

    supervisor.start()
    assert wait_for(lambda: errors == ["HEARTBEAT_FAILED"])
    supervisor.notify_reconnected()
    assert wait_for(lambda: len(runtime.heartbeat_calls) >= 2)
    assert wait_for(lambda: lifecycle.reconnections >= 2)
    assert supervisor.stop(timeout=1)


def test_callback_exception_does_not_terminate_supervisor():
    runtime = FakeRuntime(heartbeat=[OSError("offline"), None])
    lifecycle = FakeLifecycle()
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
        heartbeat_interval_seconds=0.1,
        on_error=lambda _code: (_ for _ in ()).throw(RuntimeError("telemetry")),
    )
    supervisor.start()
    assert wait_for(lambda: len(runtime.heartbeat_calls) >= 1)
    supervisor.notify_reconnected()
    assert wait_for(lambda: len(runtime.heartbeat_calls) >= 2)
    assert supervisor.stop(timeout=1)


@pytest.mark.parametrize("interval", [0, 0.05, 3601, float("nan"), float("inf"), True])
def test_invalid_heartbeat_interval_is_rejected(interval):
    with pytest.raises(ValueError):
        AgentSupervisor(
            runtime=FakeRuntime(),
            receipt_lifecycle=FakeLifecycle(),
            heartbeat_payload=lambda: {},
            capabilities_payload=lambda: {},
            heartbeat_interval_seconds=interval,
        )


def test_start_is_idempotent_and_stop_before_start_is_final():
    runtime = FakeRuntime()
    lifecycle = FakeLifecycle()
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
        heartbeat_interval_seconds=0.2,
    )
    supervisor.start()
    supervisor.start()
    assert wait_for(lambda: len(runtime.heartbeat_calls) >= 1)
    assert lifecycle.starts == 1
    assert supervisor.stop(timeout=1)

    stopped = AgentSupervisor(
        runtime=FakeRuntime(),
        receipt_lifecycle=FakeLifecycle(),
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
    )
    assert stopped.stop(timeout=1)
    with pytest.raises(RuntimeError):
        stopped.start()



def test_sync_wake_failure_is_not_misreported_as_heartbeat_failure():
    runtime = FakeRuntime(heartbeat=[OSError("offline"), None])
    lifecycle = FakeLifecycle()
    lifecycle.fail_reconnections = True
    errors = []
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
        heartbeat_interval_seconds=0.5,
        on_error=errors.append,
    )
    supervisor.start()
    assert wait_for(lambda: "HEARTBEAT_FAILED" in errors)
    supervisor.notify_reconnected()
    assert wait_for(lambda: errors.count("RECEIPT_SYNC_WAKE_FAILED") >= 2)
    assert errors.count("HEARTBEAT_FAILED") == 1
    assert supervisor.stop(timeout=1)



def test_capabilities_failure_does_not_stop_heartbeat_loop():
    runtime = FakeRuntime(capabilities=[OSError("offline"), None])
    lifecycle = FakeLifecycle()
    errors = []
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {"health_state": "healthy"},
        capabilities_payload=lambda: {"capabilities_version": 1, "capabilities": []},
        heartbeat_interval_seconds=0.1,
        on_error=errors.append,
    )
    supervisor.start()
    assert wait_for(lambda: "CAPABILITIES_FAILED" in errors)
    assert wait_for(lambda: len(runtime.heartbeat_calls) >= 2)
    assert errors.count("CAPABILITIES_FAILED") == 1
    assert supervisor.stop(timeout=1)



def test_stop_from_error_callback_requests_shutdown_without_self_join():
    runtime = FakeRuntime(heartbeat=[OSError("offline")])
    lifecycle = FakeLifecycle()
    stop_results = []
    callback_called = threading.Event()
    supervisor = None

    def on_error(_code):
        stop_results.append(supervisor.stop(timeout=1))
        callback_called.set()

    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
        heartbeat_interval_seconds=0.1,
        on_error=on_error,
    )
    supervisor.start()
    assert callback_called.wait(1)
    assert stop_results == [False]  # El hilo actual aún no puede afirmar que terminó.
    supervisor._thread.join(timeout=1)
    assert not supervisor._thread.is_alive()
    assert lifecycle.stops



def test_reconciliation_runs_on_start_and_explicit_reconnect():
    runtime = FakeRuntime(reconcile_responses=[{"report_id": "r1"}, {"report_id": "r2"}])
    lifecycle = FakeLifecycle()
    reports = []
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {"health_state": "healthy"},
        capabilities_payload=lambda: {"capabilities_version": 1, "capabilities": []},
        reconcile_inventory=lambda: [{"task_id": "local-task"}],
        on_reconciliation=reports.append,
        heartbeat_interval_seconds=0.5,
    )
    supervisor.start()
    assert wait_for(lambda: len(runtime.reconcile_calls) == 1)
    supervisor.notify_reconnected()
    assert wait_for(lambda: len(runtime.reconcile_calls) == 2)
    assert wait_for(lambda: len(reports) == 2)
    assert reports == [{"report_id": "r1"}, {"report_id": "r2"}]
    assert runtime.reconcile_calls == [
        [{"task_id": "local-task"}],
        [{"task_id": "local-task"}],
    ]
    assert supervisor.stop(timeout=1)


def test_reconciliation_failure_is_sanitized_and_retried_after_backoff():
    runtime = FakeRuntime(reconcile_responses=[OSError("do not log"), {"ok": True}])
    lifecycle = FakeLifecycle()
    errors = []
    supervisor = AgentSupervisor(
        runtime=runtime,
        receipt_lifecycle=lifecycle,
        heartbeat_payload=lambda: {},
        capabilities_payload=lambda: {},
        reconcile_inventory=lambda: [],
        reconciliation_retry_interval_seconds=1,
        heartbeat_interval_seconds=0.1,
        on_error=errors.append,
    )
    supervisor.start()
    assert wait_for(lambda: errors == ["RECONCILIATION_FAILED"])
    time.sleep(0.1)
    assert len(runtime.reconcile_calls) == 1
    assert supervisor.stop(timeout=1)
