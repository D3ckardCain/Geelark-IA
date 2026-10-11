"""Monitor Linux netlink basado en eventos; no sondea la conectividad por red.

Se suscribe a cambios de enlace, direcciones y rutas. Un evento de enlace activo,
nueva dirección o nueva ruta despierta al supervisor para que vuelva a consultar
el controlador. Esto es una señal local, no una garantía de que el controlador ya
sea alcanzable; los timeouts HTTPS y el heartbeat periódico siguen siendo necesarios.
"""
from __future__ import annotations

import logging
import math
import socket
import struct
import sys
import threading
import time
from collections.abc import Callable
from typing import Any

_LOGGER = logging.getLogger("geelark_agent")

# Grupos de multicast de NETLINK_ROUTE (Linux UAPI).
_RTMGRP_LINK = 1
_RTMGRP_IPV4_IFADDR = 0x10
_RTMGRP_IPV4_ROUTE = 0x40
_RTMGRP_IPV6_IFADDR = 0x100
_RTMGRP_IPV6_ROUTE = 0x400

_RTM_NEWLINK = 16
_RTM_NEWADDR = 20
_RTM_NEWROUTE = 24
_IFF_UP = 0x1
_IFF_RUNNING = 0x40
_NLMSG_HEADER_SIZE = 16


class LinuxNetlinkConnectivityMonitor:
    """Despierta el agente ante eventos de red Linux, sin conexión de prueba propia."""

    def __init__(
        self,
        *,
        on_reconnected: Callable[[], None],
        on_error: Callable[[str], None] | None = None,
        socket_factory: Callable[..., Any] | None = None,
        platform_name: str | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        min_event_interval_seconds: float = 1.0,
    ) -> None:
        if not callable(on_reconnected):
            raise ValueError("on_reconnected debe ser callable")
        if on_error is not None and not callable(on_error):
            raise ValueError("on_error debe ser callable")
        if not callable(monotonic):
            raise ValueError("monotonic debe ser callable")
        if (
            isinstance(min_event_interval_seconds, bool)
            or not isinstance(min_event_interval_seconds, (int, float))
            or not math.isfinite(min_event_interval_seconds)
            or min_event_interval_seconds < 0
        ):
            raise ValueError("min_event_interval_seconds debe ser finito y no negativo")

        self.on_reconnected = on_reconnected
        self.on_error = on_error or (lambda code: _LOGGER.warning("%s", code))
        self.socket_factory = socket_factory or socket.socket
        self.platform_name = platform_name or sys.platform
        self.monotonic = monotonic
        self.min_event_interval_seconds = float(min_event_interval_seconds)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket: Any = None
        self._lock = threading.Lock()
        self._last_notify_at: float | None = None
        self._started = False

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop.is_set()

    def start(self) -> bool:
        """Se suscribe a eventos locales; devuelve False si no está disponible."""
        with self._lock:
            if self._started:
                raise RuntimeError("El monitor ya se inició y no puede reiniciarse")
            self._started = True
            if not self.platform_name.startswith("linux"):
                self._report("CONNECTIVITY_MONITOR_UNAVAILABLE")
                return False
            try:
                sock = self.socket_factory(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
                sock.settimeout(1.0)
                groups = (
                    _RTMGRP_LINK | _RTMGRP_IPV4_IFADDR | _RTMGRP_IPV6_IFADDR
                    | _RTMGRP_IPV4_ROUTE | _RTMGRP_IPV6_ROUTE
                )
                sock.bind((0, groups))
            except (AttributeError, OSError):
                try:
                    sock.close()
                except (UnboundLocalError, AttributeError, OSError):
                    pass
                self._report("CONNECTIVITY_MONITOR_UNAVAILABLE")
                return False
            self._socket = sock
            self._thread = threading.Thread(
                target=self._run, name="geelark-netlink-monitor", daemon=True
            )
            self._thread.start()
            return True

    def stop(self, *, timeout: float = 2.0) -> bool:
        """Detiene el hilo; False indica que no terminó dentro del timeout."""
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout < 0
        ):
            raise ValueError("timeout debe ser finito y no negativo")
        deadline = time.monotonic() + float(timeout)
        self._stop.set()
        sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=max(0.0, deadline - time.monotonic()))
        return not thread.is_alive()

    def _report(self, code: str) -> None:
        try:
            self.on_error(code)
        except Exception:
            pass

    @staticmethod
    def should_notify(data: bytes) -> bool:
        """Analiza mensajes netlink y reconoce solo eventos que pueden restaurar red."""
        offset = 0
        while offset + _NLMSG_HEADER_SIZE <= len(data):
            try:
                length, message_type, _flags, _sequence, _pid = struct.unpack_from("=IHHII", data, offset)
            except struct.error:
                return False
            if length < _NLMSG_HEADER_SIZE or offset + length > len(data):
                return False
            payload_offset = offset + _NLMSG_HEADER_SIZE
            if message_type in {_RTM_NEWADDR, _RTM_NEWROUTE}:
                return True
            if message_type == _RTM_NEWLINK and length >= _NLMSG_HEADER_SIZE + 16:
                interface_flags = struct.unpack_from("=I", data, payload_offset + 8)[0]
                if interface_flags & _IFF_UP and interface_flags & _IFF_RUNNING:
                    return True
            offset += (length + 3) & ~3
        return False

    def _run(self) -> None:
        sock = self._socket
        while not self._stop.is_set() and sock is not None:
            try:
                data = sock.recv(65535)
            except socket.timeout:
                # Timeout solo permite revisar la señal de apagado; no hace probes de red.
                continue
            except OSError:
                if not self._stop.is_set():
                    self._report("CONNECTIVITY_MONITOR_FAILED")
                return
            if not self.should_notify(data):
                continue
            now = self.monotonic()
            if (
                self._last_notify_at is not None
                and now - self._last_notify_at < self.min_event_interval_seconds
            ):
                continue
            self._last_notify_at = now
            try:
                self.on_reconnected()
            except Exception:
                self._report("CONNECTIVITY_NOTIFY_FAILED")
