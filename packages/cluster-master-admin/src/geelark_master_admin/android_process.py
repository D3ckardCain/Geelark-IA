"""Procesos locales de pantalla Android. Sin valores de laboratorio ni UI de diagnóstico."""
import os
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def healthy(output):
    lines = [line.strip() for line in output.splitlines()]
    return "1" in lines and "Service input: found" in lines and "Service activity: found" in lines


class Controller:
    def __init__(self, config, emit):
        self.config = config
        self.emit = emit
        self.tunnel = None
        self.screen = None
        self.adb_owned = False

    def run(self, args, timeout=20):
        result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
                                timeout=timeout, creationflags=FLAGS)
        self.emit(result.stdout.strip())
        if result.returncode:
            raise RuntimeError(f"{Path(args[0]).name}: código {result.returncode}. Revisa el registro.")
        return result.stdout

    def ssh(self):
        if not self.config.key.is_file():
            raise RuntimeError(f"Falta la clave: {self.config.key}")
        return [self.require("ssh"), "-i", str(self.config.key), "-o", "IdentitiesOnly=yes",
                "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=10",
                "-o", "ServerAliveCountMax=2"]

    @staticmethod
    def require(name):
        path = shutil.which(name)
        if not path:
            raise RuntimeError(f"No se encuentra {name} en PATH.")
        return path

    def start_tunnel(self):
        if self.tunnel and self.tunnel.poll() is None:
            return
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", self.config.port))
            except OSError:
                raise RuntimeError(f"Puerto {self.config.port} ocupado. No se modificó el proceso que lo usa.")
        args = self.ssh() + ["-o", "ExitOnForwardFailure=yes", "-N", "-L",
                             f"127.0.0.1:{self.config.port}:127.0.0.1:5555", self.config.target]
        self.tunnel = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE, creationflags=FLAGS)
        # Drenar stderr para evitar bloqueo del proceso por llenar la tubería.
        emit = self.emit
        def errors(proc):
            for line in iter(proc.stderr.readline, b""):
                emit(line.decode("utf-8", "replace").strip())
            proc.stderr.close()
        threading.Thread(target=errors, args=(self.tunnel,), daemon=True).start()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if self.tunnel.poll() is not None:
                raise RuntimeError("No se pudo abrir el túnel SSH.")
            try:
                with socket.create_connection(("127.0.0.1", self.config.port), timeout=.3):
                    return
            except OSError:
                time.sleep(.15)
        raise RuntimeError("El túnel no respondió dentro del tiempo previsto.")

    def android_status(self):
        self.start_tunnel()
        adb = self.require("adb")
        self.adb_owned = True
        for attempt in range(2):
            try:
                self.run([adb, "connect", self.config.serial])
                self.run([adb, "-s", self.config.serial, "wait-for-device"], timeout=8)
                state = self.run([adb, "-s", self.config.serial, "get-state"])
                if state.strip() != "device":
                    raise RuntimeError("ADB no está disponible para este dispositivo.")
                break
            except (RuntimeError, subprocess.TimeoutExpired):
                if attempt:
                    raise
                self.emit("Reconectando únicamente el transporte ADB de este dispositivo…")
                self.run([adb, "disconnect", self.config.serial], timeout=5)
        return self.run([adb, "-s", self.config.serial, "shell",
                         "getprop sys.boot_completed; service check input; service check activity"])

    def open_screen(self):
        if self.screen and self.screen.poll() is None:
            self.emit("La pantalla ya está abierta.")
            return
        if not healthy(self.android_status()):
            raise RuntimeError("Android no está operativo. Pulsa Diagnosticar; no se reiniciará automáticamente.")
        self.screen = subprocess.Popen([self.require("scrcpy"), "-s", self.config.serial, "--no-audio",
                                        "--max-size=720", "--max-fps=15"],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, creationflags=FLAGS)
        emit = self.emit
        def monitor(proc):
            for line in iter(proc.stdout.readline, b""):
                emit(line.decode("utf-8", "replace").strip())
            proc.stdout.close()
            emit(f"Pantalla cerrada (código {proc.wait()}).")
        threading.Thread(target=monitor, args=(self.screen,), daemon=True).start()
        self.emit("Pantalla iniciada.")

    def recover(self, password):
        # Solo una recuperación solicitada puede reiniciar el servicio gráfico.
        # Abrir pantalla y diagnosticar siguen siendo operaciones sin reparación.
        try:
            if healthy(self.android_status()) and self.allocator_status() == "failed":
                self.close()
                self.android_status()
                if self.repair_allocator():
                    self.emit("Servicio gráfico recuperado. Ya puedes abrir la pantalla.")
                    return
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            self.emit("No se confirmó la reparación gráfica; se aplicará la recuperación completa solicitada.")
        self.close()
        self.emit("Reiniciando la instancia seleccionada. No se borra ni recrea el contenedor.")
        result = subprocess.run(self.ssh() + [self.config.target, "sudo -S -p '' docker restart " + self.config.container],
                                input=password + "\n", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace", timeout=60, creationflags=FLAGS)
        # Nunca registrar la entrada enviada a sudo.
        self.emit(result.stdout.replace(password, "[oculto]") if password else result.stdout)
        if result.returncode:
            raise RuntimeError("No se pudo reiniciar Android. Comprueba el mensaje de sudo.")
        deadline = time.monotonic() + 90
        allocator_repair_attempted = False
        while time.monotonic() < deadline:
            try:
                if healthy(self.android_status()):
                    allocator = self.allocator_status()
                    if allocator == "failed":
                        if allocator_repair_attempted:
                            raise RuntimeError("El servicio gráfico sigue fallando tras la recuperación.")
                        allocator_repair_attempted = True
                        if not self.repair_allocator():
                            raise RuntimeError("El servicio gráfico sigue fallando tras la recuperación.")
                    if allocator == "unknown":
                        raise RuntimeError("No se pudo verificar el servicio gráfico tras la recuperación.")
                    self.emit("Android recuperado. Ya puedes pulsar Abrir Android.")
                    return
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                self.emit(str(error))
            time.sleep(3)
        raise RuntimeError("Android no recuperó sus servicios. Pulsa Diagnosticar; no se repetirá el reinicio.")

    def allocator_status(self):
        interface = "android.hardware.graphics.allocator@2.0::IAllocator/default"
        output = self.run([self.require("adb"), "-s", self.config.serial, "shell",
                           "su 0 lshal 2>&1 | grep -F '" + interface + "'"], timeout=15)
        lines = output.splitlines()
        if any(interface in line and ("EX_TRANSACTION_FAILED" in line or "interfaceChain fails" in line)
               for line in lines):
            return "failed"
        # Exigir una fila del servicio publicado con PID, no solo su declaración.
        for line in lines:
            fields = line.split()
            if interface in fields and fields.index(interface) >= 2:
                tail = fields[fields.index(interface)+1:]
                if fields[0] != "X" and any(re.fullmatch(r"[1-9][0-9]*", field) for field in tail):
                    return "ready"
        return "unknown"

    def repair_allocator(self):
        self.emit("Reiniciando únicamente el servicio gráfico de Android; se conservan sus datos.")
        self.run([self.require("adb"), "-s", self.config.serial, "shell",
                  "su 0 setprop ctl.restart vendor.gralloc-2-0"], timeout=10)
        for _ in range(5):
            time.sleep(2)
            try:
                if self.allocator_status() == "ready" and healthy(self.android_status()):
                    return True
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
        return False

    def close(self):
        # Solo procesos creados por esta ventana; no adb kill-server ni taskkill global.
        for proc in (self.screen, self.tunnel):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
        self.screen = self.tunnel = None
        # ADB conserva transports offline al cerrar el túnel. Desregistrar solo
        # nuestro serial evita reutilizarlo en la siguiente apertura.
        if self.adb_owned:
            try:
                self.run([self.require("adb"), "disconnect", self.config.serial], timeout=5)
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                self.emit(f"No se confirmó la desconexión ADB: {error}")
            self.adb_owned = False
        self.emit("Conexiones propias cerradas. Debian y Android continúan ejecutándose.")

