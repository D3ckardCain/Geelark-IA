"""Control local de laboratorio. Python 3.11+, Tk y OpenSSH/ADB/scrcpy."""
import os
import queue
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

WORKER = "geelarkia@192.168.0.11"
KEY = Path.home() / ".ssh" / "geelark_worker_lab"
SERIAL = "127.0.0.1:15557"
PORT = 15557
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
REMOTE = "hostname; uptime; free -m; df -h /; ip -br a; systemctl is-active docker; sudo -n docker ps -a; sudo -n docker inspect --format '{{.State.Status}} OOM={{.State.OOMKilled}} Exit={{.State.ExitCode}}' android-lab-01"


def healthy(output):
    lines = [line.strip() for line in output.splitlines()]
    return "1" in lines and "Service input: found" in lines and "Service activity: found" in lines


class Controller:
    def __init__(self, emit):
        self.emit = emit
        self.tunnel = None
        self.screen = None

    def run(self, args, timeout=20):
        result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
                                timeout=timeout, creationflags=FLAGS)
        self.emit(result.stdout.strip())
        if result.returncode:
            raise RuntimeError(f"{Path(args[0]).name}: código {result.returncode}. Revisa el registro.")
        return result.stdout

    def ssh(self):
        if not KEY.is_file():
            raise RuntimeError(f"Falta la clave: {KEY}")
        return [self.require("ssh"), "-i", str(KEY), "-o", "IdentitiesOnly=yes",
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
                probe.bind(("127.0.0.1", PORT))
            except OSError:
                raise RuntimeError(f"Puerto {PORT} ocupado. No se modificó el proceso que lo usa.")
        args = self.ssh() + ["-o", "ExitOnForwardFailure=yes", "-N", "-L",
                             f"127.0.0.1:{PORT}:127.0.0.1:5555", WORKER]
        self.tunnel = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE, creationflags=FLAGS)
        # Drenar stderr para evitar bloqueo del proceso por llenar la tubería.
        def errors(proc):
            for line in iter(proc.stderr.readline, b""):
                self.emit(line.decode("utf-8", "replace").strip())
            proc.stderr.close()
        threading.Thread(target=errors, args=(self.tunnel,), daemon=True).start()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if self.tunnel.poll() is not None:
                raise RuntimeError("No se pudo abrir el túnel SSH.")
            try:
                with socket.create_connection(("127.0.0.1", PORT), timeout=.3):
                    return
            except OSError:
                time.sleep(.15)
        raise RuntimeError("El túnel no respondió dentro del tiempo previsto.")

    def android_status(self):
        self.start_tunnel()
        adb = self.require("adb")
        self.run([adb, "connect", SERIAL])
        self.run([adb, "-s", SERIAL, "get-state"])
        return self.run([adb, "-s", SERIAL, "shell",
                         "getprop sys.boot_completed; service check input; service check activity"])

    def diagnose(self):
        self.emit("DIAGNÓSTICO: Debian / Docker / Android")
        try:
            self.run(self.ssh() + [WORKER, REMOTE], timeout=30)
        except Exception as error:
            self.emit(str(error))
            self.emit("Si sudo requiere contraseña, los datos Docker quedan pendientes; no se cambian permisos.")
        state = self.android_status()
        adb = self.require("adb")
        self.run([adb, "-s", SERIAL, "shell",
                  "pidof system_server; getprop init.svc.zygote; getprop init.svc.servicemanager"])
        self.run([adb, "-s", SERIAL, "logcat", "-b", "crash", "-d", "-t", "100"])
        self.emit("Android operativo." if healthy(state) else
                  "Android incompleto: faltan servicios principales. Abrir pantalla queda bloqueado.")

    def open_screen(self):
        if self.screen and self.screen.poll() is None:
            self.emit("La pantalla ya está abierta.")
            return
        if not healthy(self.android_status()):
            raise RuntimeError("Android no está operativo. Pulsa Diagnosticar; no se reiniciará automáticamente.")
        self.screen = subprocess.Popen([self.require("scrcpy"), "-s", SERIAL, "--no-audio",
                                        "--max-size=720", "--max-fps=15"],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, creationflags=FLAGS)
        def monitor(proc):
            for line in iter(proc.stdout.readline, b""):
                self.emit(line.decode("utf-8", "replace").strip())
            proc.stdout.close()
            self.emit(f"Pantalla cerrada (código {proc.wait()}).")
        threading.Thread(target=monitor, args=(self.screen,), daemon=True).start()
        self.emit("Pantalla iniciada.")

    def recover(self, password):
        self.close()
        self.emit("Reiniciando únicamente android-lab-01. No se borra ni recrea el contenedor.")
        result = subprocess.run(self.ssh() + [WORKER, "sudo -S -p '' docker restart android-lab-01"],
                                input=password + "\n", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace", timeout=60, creationflags=FLAGS)
        # Nunca registrar la entrada enviada a sudo.
        self.emit(result.stdout.replace(password, "[oculto]") if password else result.stdout)
        if result.returncode:
            raise RuntimeError("No se pudo reiniciar Android. Comprueba el mensaje de sudo.")
        adb = self.require("adb")
        self.run([adb, "disconnect", SERIAL])
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if healthy(self.android_status()):
                    self.emit("Android recuperado. Ya puedes pulsar Abrir Android.")
                    return
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                self.emit(str(error))
            time.sleep(3)
        raise RuntimeError("Android no recuperó sus servicios. Pulsa Diagnosticar; no se repetirá el reinicio.")

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
        self.emit("Conexiones propias cerradas. Debian y Android continúan ejecutándose.")


def main():
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText
    from tkinter import messagebox, simpledialog
    root = tk.Tk()
    root.title("GeeLark-IA · Control del laboratorio")
    root.geometry("850x560")
    messages = queue.Queue()
    logdir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GeeLark-IA" / "worker-lab"
    logdir.mkdir(parents=True, exist_ok=True)
    logfile = logdir / (time.strftime("diagnostico-%Y%m%d-%H%M%S") + ".log")
    controller = Controller(messages.put)
    tk.Label(root, text=f"{WORKER} · android-lab-01", pady=8).pack()
    tk.Label(root, text="Debian debe estar encendido. No necesitas abrir consolas ni túneles.").pack()
    bar = tk.Frame(root)
    bar.pack(pady=10)
    output = ScrolledText(root, wrap="word", state="disabled")
    output.pack(fill="both", expand=True, padx=10, pady=5)
    tk.Label(root, text=f"Registro: {logfile}", wraplength=810).pack(pady=5)
    busy = False
    closing = False
    buttons = []

    def action(fn):
        nonlocal busy
        if busy:
            return
        busy = True
        for button in buttons:
            button.config(state="disabled")
        def work():
            try:
                fn()
            except Exception as error:
                messages.put(f"ERROR: {error}")
            finally:
                messages.put(None)
        threading.Thread(target=work, daemon=True).start()

    for label, fn in [("Diagnosticar", controller.diagnose), ("Abrir Android", controller.open_screen),
                      ("Cerrar conexión", controller.close)]:
        button = tk.Button(bar, text=label, command=lambda f=fn: action(f), padx=15)
        button.pack(side="left", padx=5)
        buttons.append(button)

    def request_recovery():
        if busy:
            return
        if not messagebox.askyesno("Recuperar Android", "Se reiniciará solo android-lab-01 y se cerrará su pantalla. Las operaciones en curso se interrumpirán. ¿Continuar?"):
            return
        password = simpledialog.askstring("Contraseña Debian", "Contraseña de geelarkia (no se guardará):", show="*")
        if password is not None:
            action(lambda: controller.recover(password))
    recovery = tk.Button(bar, text="Recuperar Android", command=request_recovery, padx=15)
    recovery.pack(side="left", padx=5)
    buttons.append(recovery)

    def finish_close():
        controller.close()
        root.destroy()

    def request_close():
        nonlocal closing
        if busy:
            closing = True
            messages.put("Cerrando al terminar la operación actual (tiene tiempo límite).")
        else:
            finish_close()

    def poll():
        nonlocal busy
        while not messages.empty():
            message = messages.get_nowait()
            if message is None:
                busy = False
                if closing:
                    finish_close()
                    return
                for button in buttons:
                    button.config(state="normal")
                continue
            if message:
                output.config(state="normal")
                output.insert("end", message + "\n")
                output.see("end")
                output.config(state="disabled")
                try:
                    with logfile.open("a", encoding="utf-8") as stream:
                        stream.write(message + "\n")
                except OSError as error:
                    messagebox.showerror("Registro no disponible", str(error))
        root.after(150, poll)
    root.protocol("WM_DELETE_WINDOW", request_close)
    messages.put("Preparado. Pulsa Diagnosticar para investigar el fallo actual de Android.")
    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
