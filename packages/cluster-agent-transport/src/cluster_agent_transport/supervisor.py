"""Supervisor saliente de agente; telemetría únicamente, sin ejecución de tareas.

La configuración se carga explícitamente. No abre listeners, no inicia ADB/shell y
no interpreta ninguna respuesta remota como una orden de ejecución.
"""
from __future__ import annotations

import argparse
import math
import os
import signal
import stat
import threading
import time
import tomllib
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from .client import AgentHTTPSClient, AgentTransportError
from .lifecycle import AgentReceiptSyncLifecycle
from .runtime import AgentTransportRuntime


def linux_resource_snapshot(storage_path: str | Path) -> dict[str, int | float]:
    """Métricas locales aproximadas sin dependencias externas ni datos de identidad."""
    try:
        load = os.getloadavg()[0]
        cpu_percent = min(100.0, max(0.0, load / max(os.cpu_count() or 1, 1) * 100.0))
    except (AttributeError, OSError):
        cpu_percent = 0.0

    memory_total = 0
    memory_available = 0
    try:
        values: dict[str, int] = {}
        with Path("/proc/meminfo").open("r", encoding="ascii") as stream:
            for line in stream:
                key, value, *_ = line.replace(":", "").split()
                if key in {"MemTotal", "MemAvailable"}:
                    values[key] = int(value) * 1024
        memory_total = values.get("MemTotal", 0)
        memory_available = values.get("MemAvailable", 0)
    except (OSError, ValueError):
        pass

    try:
        storage_available = shutil_disk_usage(storage_path)
    except OSError:
        storage_available = 0
    return {
        "cpu_load_percent": cpu_percent,
        "memory_total_bytes": memory_total,
        "memory_available_bytes": memory_available,
        "storage_available_bytes": storage_available,
    }


def shutil_disk_usage(path: str | Path) -> int:
    # Import local para mantener explícito que no se realiza ninguna llamada de red.
    import shutil
    return shutil.disk_usage(Path(path)).free


class AgentNodeSupervisor:
    """Mantiene telemetría periódica y sincronización durable en hilos separados."""

    def __init__(
        self,
        *,
        runtime: Any,
        receipt_sync: AgentReceiptSyncLifecycle,
        agent_version: str,
        capabilities: list[str],
        heartbeat_interval_seconds: float = 30.0,
        capabilities_interval_seconds: float = 300.0,
        status_interval_seconds: float = 60.0,
        metrics_provider: Callable[[], dict[str, int | float]] | None = None,
        on_error: Callable[[str], None] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(agent_version, str) or not agent_version.strip() or len(agent_version) > 64:
            raise ValueError("agent_version debe tener entre 1 y 64 caracteres")
        if not isinstance(capabilities, list) or len(capabilities) > 128:
            raise ValueError("capabilities debe ser una lista de hasta 128 elementos")
        if any(not isinstance(item, str) or not item.strip() or len(item) > 128 for item in capabilities):
            raise ValueError("Cada capacidad debe tener entre 1 y 128 caracteres")
        if len(set(capabilities)) != len(capabilities):
            raise ValueError("No se permiten capacidades duplicadas")
        for name, value in (
            ("heartbeat_interval_seconds", heartbeat_interval_seconds),
            ("capabilities_interval_seconds", capabilities_interval_seconds),
            ("status_interval_seconds", status_interval_seconds),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 1:
                raise ValueError(f"{name} debe ser un número finito de al menos 1 segundo")
        for name in ("send_heartbeat", "publish_capabilities", "read_status"):
            if not callable(getattr(runtime, name, None)):
                raise ValueError(f"runtime debe implementar {name}()")
        if not callable(getattr(receipt_sync, "start", None)) or not callable(getattr(receipt_sync, "stop", None)):
            raise ValueError("receipt_sync debe implementar start() y stop()")
        if metrics_provider is not None and not callable(metrics_provider):
            raise ValueError("metrics_provider debe ser callable")
        if on_error is not None and not callable(on_error):
            raise ValueError("on_error debe ser callable")

        self.runtime = runtime
        self.receipt_sync = receipt_sync
        self.agent_version = agent_version.strip()
        self.capabilities = list(capabilities)
        self.heartbeat_interval_seconds = float(heartbeat_interval_seconds)
        self.capabilities_interval_seconds = float(capabilities_interval_seconds)
        self.status_interval_seconds = float(status_interval_seconds)
        self.metrics_provider = metrics_provider or (lambda: linux_resource_snapshot("."))
        self.on_error = on_error or (lambda _code: None)
        self._monotonic = monotonic
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop.is_set()

    def start(self) -> None:
        """Inicia una sola vez el sincronizador y el hilo de telemetría."""
        with self._lock:
            if self._stop.is_set() or self._thread is not None:
                raise RuntimeError("El supervisor ya se inició o se detuvo y no puede reiniciarse")
            self.receipt_sync.start()
            self._thread = threading.Thread(target=self._run, name="geelark-agent-supervisor", daemon=True)
            self._thread.start()

    def notify_reconnected(self) -> None:
        """Notificación externa del monitor de red; no sondea conectividad por sí mismo."""
        if self._stop.is_set():
            return
        self.receipt_sync.notify_reconnected()
        self._wake.set()

    def stop(self, *, timeout: float = 5.0) -> bool:
        """Apagado cooperativo; False significa que algún hilo agotó el timeout."""
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout debe ser un número finito no negativo")
        self._stop.set()
        self._wake.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=float(timeout))
            if thread.is_alive():
                return False
        return bool(self.receipt_sync.stop(timeout=float(timeout)))

    def _report(self, code: str) -> None:
        try:
            self.on_error(code)
        except Exception:
            pass

    def _metrics(self) -> dict[str, int | float]:
        values = self.metrics_provider()
        if not isinstance(values, dict):
            raise ValueError("metrics_provider debe devolver un diccionario")
        required = (
            "cpu_load_percent", "memory_total_bytes",
            "memory_available_bytes", "storage_available_bytes",
        )
        result: dict[str, int | float] = {}
        for key in required:
            value = values.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Métrica local inválida")
            result[key] = value
        if result["cpu_load_percent"] > 100:
            raise ValueError("cpu_load_percent excede 100")
        if result["memory_available_bytes"] > result["memory_total_bytes"]:
            raise ValueError("Memoria disponible supera la memoria total")
        return result

    def _call(self, code: str, callback: Callable[[], Any]) -> None:
        try:
            callback()
        except Exception:
            # No se registran excepciones, tokens, recibos ni cuerpos HTTP.
            self._report(code)

    def _heartbeat(self) -> None:
        metrics = self._metrics()
        payload = {
            "schema_version": 1,
            "agent_version": self.agent_version,
            "health_state": "healthy",
            **metrics,
        }
        self.runtime.send_heartbeat(payload)

    def _capabilities(self) -> None:
        self.runtime.publish_capabilities({
            "capabilities_version": 1,
            "capabilities": self.capabilities,
        })

    def _run(self) -> None:
        now = self._monotonic()
        next_heartbeat = now
        next_capabilities = now
        next_status = now
        while not self._stop.is_set():
            now = self._monotonic()
            if now >= next_heartbeat:
                self._call("HEARTBEAT_FAILED", self._heartbeat)
                next_heartbeat = now + self.heartbeat_interval_seconds
            if now >= next_capabilities:
                self._call("CAPABILITIES_FAILED", self._capabilities)
                next_capabilities = now + self.capabilities_interval_seconds
            if now >= next_status:
                self._call("STATUS_FAILED", self.runtime.read_status)
                next_status = now + self.status_interval_seconds
            if self._stop.is_set():
                break
            deadlines = (next_heartbeat, next_capabilities, next_status)
            wait_seconds = max(0.05, min(deadlines) - self._monotonic())
            woke = self._wake.wait(wait_seconds)
            self._wake.clear()
            if woke and not self._stop.is_set():
                # Una reconexión confirmada adelanta la telemetría sin sondeo de red.
                next_heartbeat = next_capabilities = next_status = 0.0


def _read_token(path: str | Path) -> str:
    """Lee un bearer de un archivo privado, sin seguir symlinks ni exponerlo en logs."""
    token_path = Path(path)
    if token_path.is_symlink() or not token_path.is_file():
        raise ValueError("credential_file debe ser un archivo regular, no un enlace")
    metadata = token_path.stat()
    if metadata.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError("credential_file debe tener permisos privados (sin grupo/otros)")
    if hasattr(os, "geteuid") and metadata.st_uid != os.geteuid():
        raise ValueError("credential_file debe pertenecer al usuario que ejecuta el agente")
    token = token_path.read_text(encoding="ascii").strip()
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError("credential_file no contiene una credencial hexadecimal válida")
    return token


def load_supervisor(config_path: str | Path) -> AgentNodeSupervisor:
    """Carga TOML explícito y construye el agente de telemetría sin ejecutar tareas."""
    from geelark_cluster_agent_guard import AgentJournal

    config_file = Path(config_path)
    with config_file.open("rb") as stream:
        config = tomllib.load(stream)
    required = {
        "node_id", "controller_url", "ca_cert", "journal_path",
        "credential_file", "agent_version", "capabilities",
    }
    if not isinstance(config, dict) or not required.issubset(config):
        raise ValueError("La configuración TOML no contiene todos los campos obligatorios")
    node_id = UUID(config["node_id"])
    token = _read_token(config["credential_file"])
    client = AgentHTTPSClient(
        base_url=config["controller_url"],
        ca_cert=config["ca_cert"],
        timeout_seconds=config.get("request_timeout_seconds", 5.0),
    )
    journal = AgentJournal(config["journal_path"], node_id)
    journal.initialize()
    runtime = AgentTransportRuntime(
        client=client,
        bearer_token=token,
        journal=journal,
        local_node_id=node_id,
    )
    receipt_sync = AgentReceiptSyncLifecycle(
        runtime=runtime,
        batch_size=config.get("receipt_batch_size", 100),
    )
    return AgentNodeSupervisor(
        runtime=runtime,
        receipt_sync=receipt_sync,
        agent_version=config["agent_version"],
        capabilities=config["capabilities"],
        heartbeat_interval_seconds=config.get("heartbeat_interval_seconds", 30.0),
        capabilities_interval_seconds=config.get("capabilities_interval_seconds", 300.0),
        status_interval_seconds=config.get("status_interval_seconds", 60.0),
        metrics_provider=lambda: linux_resource_snapshot(Path(config["journal_path"]).parent),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente GeeLark-IA: heartbeat y sincronización de recibos, sin ejecutar tareas")
    parser.add_argument("--config", required=True, help="Ruta al archivo TOML de configuración")
    args = parser.parse_args()
    supervisor = load_supervisor(args.config)
    shutdown = threading.Event()

    def request_shutdown(_signum: int, _frame: Any) -> None:
        shutdown.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    supervisor.start()
    try:
        shutdown.wait()
    finally:
        if not supervisor.stop(timeout=10.0):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
