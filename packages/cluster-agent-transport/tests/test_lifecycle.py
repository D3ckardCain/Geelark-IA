import threading
import time

import pytest

from cluster_agent_transport.lifecycle import AgentReceiptSyncLifecycle


class FakeRuntime:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.called = threading.Event()
        self.lock = threading.Lock()

    def sync_pending_receipts(self, *, limit):
        with self.lock:
            self.calls.append(limit)
            item = self.responses.pop(0) if self.responses else (0, 0)
        self.called.set()
        if isinstance(item, Exception):
            raise item
        return item


def wait_for_calls(runtime, count, timeout=1):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with runtime.lock:
            if len(runtime.calls) >= count:
                return True
        time.sleep(0.005)
    return False


def test_start_syncs_immediately_in_bounded_batch_and_stop_is_clean():
    runtime = FakeRuntime([(1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(runtime=runtime, batch_size=2)
    lifecycle.start()
    assert runtime.called.wait(1)
    assert lifecycle.stop(timeout=1)
    with runtime.lock:
        assert runtime.calls == [2]
    assert not lifecycle.running


def test_failed_sync_retries_with_bounded_jitter_and_sanitized_error():
    runtime = FakeRuntime([OSError("no debe filtrarse"), (1, 1)])
    errors = []
    lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime, batch_size=5, initial_backoff_seconds=0.01,
        max_backoff_seconds=0.02, random_value=lambda: 1.0, on_error=errors.append,
    )
    lifecycle.start()
    assert wait_for_calls(runtime, 2)
    assert errors == ["RECEIPT_SYNC_FAILED"]
    assert lifecycle.stop(timeout=1)


def test_error_callback_failure_does_not_kill_retry_worker():
    runtime = FakeRuntime([OSError("red"), (1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime, initial_backoff_seconds=0.01,
        on_error=lambda _code: (_ for _ in ()).throw(RuntimeError("telemetría")),
    )
    lifecycle.start()
    assert wait_for_calls(runtime, 2)
    assert lifecycle.stop(timeout=1)


def test_full_batch_is_drained_without_waiting_for_reconnection():
    runtime = FakeRuntime([(2, 2), (1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(runtime=runtime, batch_size=2)
    lifecycle.start()
    assert wait_for_calls(runtime, 2)
    assert lifecycle.stop(timeout=1)
    with runtime.lock:
        assert runtime.calls == [2, 2]


def test_reconnect_wakes_idle_sync_worker():
    runtime = FakeRuntime([(0, 0), (1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(runtime=runtime)
    lifecycle.start()
    assert runtime.called.wait(1)
    assert wait_for_calls(runtime, 1)
    lifecycle.notify_reconnected()
    assert wait_for_calls(runtime, 2)
    assert lifecycle.stop(timeout=1)


@pytest.mark.parametrize("kwargs", [
    {"batch_size": 0},
    {"batch_size": 1001},
    {"initial_backoff_seconds": 0},
    {"initial_backoff_seconds": float("nan")},
    {"max_backoff_seconds": float("inf")},
    {"initial_backoff_seconds": 2, "max_backoff_seconds": 1},
])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        AgentReceiptSyncLifecycle(runtime=FakeRuntime([]), **kwargs)


@pytest.mark.parametrize("response", [(True, 1), (0, True), (-1, 0), (0, 1001), (2, 1), None])
def test_invalid_runtime_counters_are_reported_and_retried(response):
    runtime = FakeRuntime([response, (0, 0)])
    errors = []
    lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime, initial_backoff_seconds=0.01, on_error=errors.append,
    )
    lifecycle.start()
    assert wait_for_calls(runtime, 2)
    assert errors == ["RECEIPT_SYNC_FAILED"]
    assert lifecycle.stop(timeout=1)


def test_stop_before_start_is_safe_and_timeout_is_validated():
    lifecycle = AgentReceiptSyncLifecycle(runtime=FakeRuntime([]))
    assert lifecycle.stop()
    with pytest.raises(ValueError):
        lifecycle.stop(timeout=float("nan"))
    with pytest.raises(RuntimeError):
        lifecycle.start()


def test_error_callback_can_stop_lifecycle_without_self_join():
    callback_called = threading.Event()
    stop_results = []

    class BrokenRuntime(FakeRuntime):
        def sync_pending_receipts(self, *, limit):
            with self.lock:
                self.calls.append(limit)
            self.called.set()
            raise OSError("sensitive database/network detail")

    runtime = BrokenRuntime([])
    lifecycle = None

    def on_error(_code):
        stop_results.append(lifecycle.stop(timeout=1))
        callback_called.set()

    lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime,
        initial_backoff_seconds=0.01,
        on_error=on_error,
    )
    lifecycle.start()
    assert callback_called.wait(1)
    assert stop_results == [False]
    thread = lifecycle._thread
    assert thread is not None
    thread.join(timeout=1)
    assert not thread.is_alive()
