import queue
import socket
import struct
import threading
import time

import pytest

from cluster_agent_transport.connectivity import LinuxNetlinkConnectivityMonitor


def message(message_type, payload=b""):
    length = 16 + len(payload)
    header = struct.pack("=IHHII", length, message_type, 0, 0, 0)
    return header + payload


def new_link(flags):
    payload = struct.pack("=BBHiII", 0, 0, 1, 2, flags, 0)
    return message(16, payload)


def new_address():
    payload = struct.pack("=BBBBI", socket.AF_INET, 24, 0, 0, 2)
    return message(20, payload)


def test_parser_notifies_only_for_relevant_up_events():
    assert LinuxNetlinkConnectivityMonitor.should_notify(new_link(0x1 | 0x40))
    assert LinuxNetlinkConnectivityMonitor.should_notify(new_address())
    assert LinuxNetlinkConnectivityMonitor.should_notify(message(24, b"\x00" * 12))
    assert not LinuxNetlinkConnectivityMonitor.should_notify(new_link(0x1))
    assert not LinuxNetlinkConnectivityMonitor.should_notify(message(21, b"\x00" * 8))
    assert not LinuxNetlinkConnectivityMonitor.should_notify(b"malformed")


class FakeNetlinkSocket:
    def __init__(self):
        self.events = queue.Queue()
        self.timeout = 0.1
        self.bound = None
        self.closed = False
        self.received = 0
        self.lock = threading.Lock()

    def settimeout(self, timeout):
        self.timeout = timeout

    def bind(self, address):
        self.bound = address

    def recv(self, _size):
        if self.closed and self.events.empty():
            raise OSError("closed")
        try:
            data = self.events.get(timeout=self.timeout)
        except queue.Empty:
            raise socket.timeout()
        with self.lock:
            self.received += 1
        return data

    def emit(self, data):
        self.events.put(data)

    def close(self):
        self.closed = True
        self.events.put(b"")


def test_monitor_notifies_on_netlink_event_and_stops():
    fake_socket = FakeNetlinkSocket()
    notifications = []
    notified = threading.Event()
    monitor = LinuxNetlinkConnectivityMonitor(
        on_reconnected=lambda: (notifications.append("reconnected"), notified.set()),
        socket_factory=lambda *_args: fake_socket,
        platform_name="linux",
    )

    assert monitor.start()
    assert fake_socket.bound is not None
    fake_socket.emit(new_address())
    assert notified.wait(1)
    assert monitor.stop(timeout=1)
    assert notifications == ["reconnected"]
    assert not monitor.running


def test_monitor_debounces_event_bursts():
    fake_socket = FakeNetlinkSocket()
    notifications = []
    second_received = threading.Event()

    original_recv = fake_socket.recv

    def recv(size):
        data = original_recv(size)
        if fake_socket.received >= 2:
            second_received.set()
        return data

    fake_socket.recv = recv
    monitor = LinuxNetlinkConnectivityMonitor(
        on_reconnected=lambda: notifications.append("reconnected"),
        socket_factory=lambda *_args: fake_socket,
        platform_name="linux",
        monotonic=lambda: 10.0,
        min_event_interval_seconds=1.0,
    )
    assert monitor.start()
    fake_socket.emit(new_address())
    fake_socket.emit(message(24, b"\x00" * 12))
    deadline = time.monotonic() + 1
    while not second_received.is_set() and time.monotonic() < deadline:
        time.sleep(0.005)
    assert second_received.is_set()
    assert monitor.stop(timeout=1)
    assert notifications == ["reconnected"]


def test_monitor_reports_unavailable_without_shell_or_network_probe():
    errors = []
    created = []

    def socket_factory(*args):
        created.append(args)
        raise OSError("should not be called")

    monitor = LinuxNetlinkConnectivityMonitor(
        on_reconnected=lambda: None,
        on_error=errors.append,
        socket_factory=socket_factory,
        platform_name="darwin",
    )

    assert monitor.start() is False
    assert errors == ["CONNECTIVITY_MONITOR_UNAVAILABLE"]
    assert created == []
    assert monitor.stop(timeout=0.1)


def test_monitor_start_failure_is_sanitized():
    errors = []
    monitor = LinuxNetlinkConnectivityMonitor(
        on_reconnected=lambda: None,
        on_error=errors.append,
        socket_factory=lambda *_args: (_ for _ in ()).throw(OSError("secret details")),
        platform_name="linux",
    )

    assert monitor.start() is False
    assert errors == ["CONNECTIVITY_MONITOR_UNAVAILABLE"]
