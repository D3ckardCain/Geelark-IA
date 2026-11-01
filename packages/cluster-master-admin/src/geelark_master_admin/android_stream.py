"""Puente local del protocolo scrcpy 5.0.1; sin ventanas SDL ni servicios externos."""
import base64
import json
import secrets
import select
import socket
import struct
import subprocess
import threading
import time
from pathlib import Path

VERSION = "5.0.1"
MAX_PACKET = 4 * 1024 * 1024


class StreamClosed(RuntimeError):
    """ADB puede aceptar y cerrar el forward antes de que escuche el servidor."""


def exact(sock, size):
    result = bytearray()
    while len(result) < size:
        block = sock.recv(size - len(result))
        if not block:
            raise StreamClosed("Se cerró la transmisión Android.")
        result.extend(block)
    return bytes(result)


def read_packet(sock):
    header = exact(sock, 12)
    flags, size = struct.unpack(">QI", header)
    if flags & (1 << 63):
        width, height = struct.unpack(">II", header[4:])
        if not 1 <= width <= 8192 or not 1 <= height <= 8192:
            raise ValueError("Dimensiones de vídeo inválidas")
        return header
    if not 0 < size <= MAX_PACKET:
        raise ValueError("Paquete de vídeo inválido")
    return header + exact(sock, size)


class EmbeddedScreen:
    def __init__(self, controller):
        self.controller = controller
        self.id = secrets.token_hex(16)
        self.scid = secrets.randbelow(0x7ffffffe) + 1
        self.remote = f"/data/local/tmp/geelark-{self.id}.jar"
        self.proc = self.video = self.control = None
        self.port = None
        self.width = self.height = 0
        self.code = None
        self.claim = threading.Lock()
        self.control_lock = threading.Lock()
        self.cleanup_lock = threading.Lock()
        self.cleaned = False
        self.emit = controller.emit

    def adb(self, *args):
        return [self.controller.require("adb"), "-s", self.controller.config.serial, *args]

    def start(self):
        c = self.controller
        executable = Path(c.require("scrcpy")).resolve()
        version = c.run([str(executable), "--version"])
        if version.splitlines()[0].split()[:2] != ["scrcpy", VERSION]:
            raise RuntimeError("La pantalla integrada requiere scrcpy 5.0.1.")
        server = executable.parent / "scrcpy-server"
        if not server.is_file():
            raise RuntimeError("No se encuentra scrcpy-server junto a scrcpy.")
        try:
            c.run(self.adb("push", str(server), self.remote))
            port = c.run(self.adb("forward", "--no-rebind", "tcp:0", f"localabstract:scrcpy_{self.scid:08x}"))
            self.port = int(port.strip())
            if not 1024 <= self.port <= 65535:
                raise RuntimeError("Puerto de vídeo inválido")
            command = f"CLASSPATH={self.remote} app_process / com.genymobile.scrcpy.Server {VERSION} scid={self.scid:08x} audio=false video_codec=h264 max_size=720 max_fps=15 video_bit_rate=2000000 tunnel_forward=true send_device_meta=false clipboard_autosync=false"
            self.proc = subprocess.Popen(self.adb("shell", command), stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            def logs():
                for line in iter(self.proc.stdout.readline, b""):
                    self.emit(line.decode("utf-8", "replace").strip())
                self.proc.stdout.close()
            threading.Thread(target=logs, daemon=True).start()
            deadline = time.monotonic() + 12
            waiting = False
            while time.monotonic() < deadline:
                try:
                    self.video = socket.create_connection(("127.0.0.1", self.port), timeout=1)
                    if exact(self.video, 1) != b"\0":
                        raise RuntimeError("Respuesta de vídeo inválida")
                    break
                except (OSError, StreamClosed):
                    if self.video:
                        self.video.close()
                    self.video = None
                    if self.proc.poll() is not None:
                        raise RuntimeError("El servidor de pantalla no pudo arrancar.")
                    if not waiting:
                        self.emit("Esperando al servidor de pantalla Android antes de completar la conexión…")
                        waiting = True
                    time.sleep(.1)
            if self.video is None:
                raise RuntimeError("La pantalla Android no respondió.")
            self.control = socket.create_connection(("127.0.0.1", self.port), timeout=5)
            self.video.settimeout(5)
            if exact(self.video, 4) != b"h264":
                raise RuntimeError("El dispositivo no ofrece vídeo H.264.")
            # Drenar respuestas del canal de control para no bloquear Android.
            self.control.settimeout(2)
            def drain():
                try:
                    while not self.cleaned:
                        try:
                            if not self.control.recv(4096):
                                return
                        except socket.timeout:
                            continue
                except OSError:
                    pass
            threading.Thread(target=drain, daemon=True).start()
        except Exception:
            self.terminate()
            raise

    def poll(self):
        if self.code is not None:
            return self.code
        return self.proc.poll() if self.proc else 1

    def frames(self, valid):
        try:
            while valid() and self.poll() is None:
                if not select.select([self.video], [], [], 1)[0]:
                    yield b"\n"
                    continue
                packet = read_packet(self.video)
                if packet[0] & 128:
                    self.width, self.height = struct.unpack(">II", packet[4:12])
                yield (json.dumps({"packet": base64.b64encode(packet).decode("ascii")})+"\n").encode()
        except (OSError, RuntimeError, ValueError) as error:
            if not self.cleaned:
                self.code = 1
                self.emit(str(error))
        finally:
            self.terminate()
            self.claim.release()

    def input(self, payload):
        if self.poll() is not None or payload["screen"] != self.id:
            raise ValueError("Pantalla no disponible")
        kind = payload["kind"]
        if kind == "key":
            key = payload["key"]
            if key not in (3, 4, 187):
                raise ValueError("Tecla no permitida")
            data = b"".join(struct.pack(">BBiii", 0, action, key, 0, 0) for action in (0, 1))
        elif kind == "text":
            text = payload["text"].encode("utf-8")
            if not 1 <= len(text) <= 300:
                raise ValueError("Texto demasiado largo")
            data = struct.pack(">BI", 1, len(text)) + text
        elif kind == "touch":
            x, y, action = payload["x"], payload["y"], payload["action"]
            if action not in (0, 1, 2) or not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError("Coordenadas inválidas")
            data = struct.pack(">BBQiiHHHII", 2, action, 0, x, y, self.width, self.height,
                               0 if action == 1 else 65535, 0, 0)
        else:
            raise ValueError("Control no permitido")
        with self.control_lock:
            self.control.sendall(data)

    def terminate(self):
        with self.cleanup_lock:
            if self.cleaned:
                return
            self.cleaned = True
        if self.code is None:
            self.code = self.proc.poll() if self.proc and self.proc.poll() is not None else 0
        for sock in (self.video, self.control):
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        for args in (["forward", "--remove", f"tcp:{self.port}"] if self.port else None,
                     ["shell", "rm", "-f", self.remote]):
            if args:
                try:
                    self.controller.run(self.adb(*args), timeout=5)
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    pass

    def wait(self, timeout=None):
        return self.code if self.code is not None else self.proc.wait(timeout=timeout)

    kill = terminate
