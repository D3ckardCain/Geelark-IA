import threading
import time

import pytest

from cluster_agent_transport.lifecycle import AgentReceiptSyncLifecycle


class FakeRuntime:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.called = threading.Event()

    def sync_pending_receipts(self, *, limit):
        self.calls.append(limit)
        self.called.set()
        item = self.responses.pop(0) if self.responses else (0, 0)
        if isinstance(item, Exception):
            raise item
        return item


def test_start_syncs_immediately_in_bounded_batch_and_stop_is_clean():
    runtime = FakeRuntime([(1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(runtime=runtime, batch_size=2)
    lifecycle.start()
    assert runtime.called.wait(1)
    assert lifecycle.stop(timeout=1)
    assert runtime.calls == [2]
    assert not lifecycle.running


def test_failed_sync_retries_with_bounded_jitter_and_sanitized_error():
    runtime = FakeRuntime([OSError("no debe filtrarse"), (1, 1)])
    errors = []
    lifecycle = AgentReceiptSyncLifecycle(
        runtime=runtime,
        batch_size=5,
        initial_backoff_seconds=0.01,
        max_backoff_seconds=0.02,
        random_value=lambda: 1.0,
        on_error=errors.append,
    )
    lifecycle.start()
    deadline = time.monotonic() + 1
    while len(runtime.calls) < 2 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert runtime.calls[:2] == [5, 5]
    assert errors == ["RECEIPT_SYNC_FAILED"]
    assert lifecycle.stop(timeout=1)


def test_reconnect_wakes_idle_sync_worker():
    runtime = FakeRuntime([(0, 0), (1, 1)])
    lifecycle = AgentReceiptSyncLifecycle(runtime=runtime)
    lifecycle.start()
    assert runtime.called.wait(1)
    deadline = time.monotonic() + 1
    while len(runtime.calls) < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    lifecycle.notify_reconnected()
    deadline = time.monotonic() + 1
    while len(runtime.calls) < 2 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert len(runtime.calls) >= 2
    assert lifecycle.stop(timeout=1)


@pytest.mark.parametrize("kwargs", [
    {"batch_size": 0},
    {"batch_size": 1001},
    {"initial_backoff_seconds": 0},
    {"initial_backoff_seconds": 2, "max_backoff_seconds": 1},
])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        AgentReceiptSyncLifecycle(runtime=FakeRuntime([]), **kwargs)


def test_stop_before_start_is_safe():
    lifecycle = AgentReceiptSyncLifecycle(runtime=FakeRuntime([]))
    assert lifecycle.stop()
    with pytest.raises(RuntimeError):
        lifecycle.start()
