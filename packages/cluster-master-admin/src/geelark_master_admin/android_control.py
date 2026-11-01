"""Servicio local configurable, operaciones acotadas y estado sin secretos."""
import json
import re
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .android_process import Controller


@dataclass(frozen=True)
class AndroidConfig:
    name: str
    host: str
    user: str
    container: str
    key: Path
    port: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not 1 <= len(self.name) <= 80:
            raise ValueError("Nombre de instancia inválido")
        for value, pattern in [(self.host, r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}"),
                               (self.user, r"[a-z_][a-z0-9_-]{0,31}"),
                               (self.container, r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")]:
            if not isinstance(value, str) or not re.fullmatch(pattern, value):
                raise ValueError("Configuración Android inválida")
        if type(self.port) is not int or not 1024 <= self.port <= 65535:
            raise ValueError("Puerto local inválido")
        if not self.key.is_absolute() or not self.key.is_file():
            raise ValueError("Falta la clave privada local configurada")

    @property
    def target(self):
        return self.user + "@" + self.host

    @property
    def serial(self):
        return "127.0.0.1:" + str(self.port)


def load_control(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(data) != {"name", "host", "user", "container", "key", "port"}:
        raise ValueError("Campos de configuración Android inválidos")
    data["key"] = Path(data["key"]).expanduser()
    return AndroidControl(AndroidConfig(**data))


class AndroidControl:
    def __init__(self, config, factory=Controller):
        self.config = config
        self.lock = threading.RLock()
        self.logs = deque(maxlen=150)
        self.controller = factory(config, self.record)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="android-control")
        self.busy = False
        self.closed = False
        self.phase = "idle"
        self.message = "Listo para conectar"

    def record(self, text):
        # Registro técnico en memoria acotada; nunca forma parte del estado operativo.
        with self.lock:
            if text:
                self.logs.append(str(text)[-2000:])

    def status(self):
        with self.lock:
            screen = self.controller.screen
            return {"configured": True, "name": self.config.name, "busy": self.busy,
                    "phase": self.phase, "message": self.message,
                    "screen_open": bool(screen and screen.poll() is None)}

    def submit(self, action, password=None, diagnostic=None):
        if action not in {"open", "disconnect", "recover", "diagnose"}:
            raise ValueError("Operación inválida")
        if action == "diagnose" and diagnostic is None:
            raise ValueError("Diagnóstico deshabilitado")
        with self.lock:
            if self.busy or self.closed:
                return False
            self.busy = True
            self.phase = "working"
            self.message = {"open": "Conectando pantalla…", "disconnect": "Cerrando conexión…",
                            "recover": "Recuperando Android…", "diagnose": "Consultando diagnóstico…"}[action]
            self.executor.submit(self._work, action, password, diagnostic)
            return True

    def _work(self, action, password, diagnostic):
        try:
            if action == "open":
                self.controller.open_screen()
                message = "Pantalla iniciada"
            elif action == "disconnect":
                self.controller.close()
                message = "Conexión cerrada; Android continúa ejecutándose"
            elif action == "recover":
                self.controller.recover(password or "")
                message = "Android recuperado; puedes abrir la pantalla"
            else:
                diagnostic(self.controller, self.config)
                message = "Diagnóstico completado; consulta la vista técnica"
            with self.lock:
                self.phase, self.message = "ready", message
        except Exception as error:
            detail = str(error)
            if password:
                detail = detail.replace(password, "[oculto]")
            self.record(detail)
            with self.lock:
                self.phase = "error"
                self.message = "No se completó la operación. Revisa la conexión y el estado de Android."
        finally:
            password = None
            with self.lock:
                self.busy = False

    def diagnostics(self):
        with self.lock:
            return "\n".join(self.logs)

    def close(self):
        with self.lock:
            self.closed = True
        self.executor.shutdown(wait=True, cancel_futures=True)
        self.controller.close()
