"""GeeLark-IA PC-MASTER: lanzador de escritorio local para Windows.

Solo usa la biblioteca estándar de Python. No instala servicios, no abre puertos
remotos y no persiste secretos. La API debe instalarse por separado desde el repo.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "GeeLark-IA · PC-MASTER"
PORT_DEFAULT = "8765"
CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GeeLark-IA" / "pc-master"
CONFIG_FILE = CONFIG_DIR / "settings.json"


def _safe_dsn(value: str) -> bool:
    """Reject passwords embedded in PostgreSQL URLs or keyword DSNs."""
    value = value.strip()
    if not value:
        return False
    if re.search(r"postgres(?:ql)?://[^\s/@:]+:[^\s/@]+@", value, re.IGNORECASE):
        return False
    if re.search(r"(?:^|\s)password\s*=", value, re.IGNORECASE):
        return False
    return True


def validate_settings(settings: dict[str, str]) -> list[str]:
    errors: list[str] = []
    required = {
        "operator_auth_file": "Archivo de autenticación del operador",
        "state_dir": "Directorio privado de estado",
        "database_url": "DSN PostgreSQL",
        "tls_cert": "Certificado TLS",
        "tls_key": "Clave privada TLS",
        "pgpassfile": "Archivo PGPASSFILE",
    }
    for key, label in required.items():
        if not settings.get(key, "").strip():
            errors.append(f"Falta: {label}.")
    if settings.get("database_url") and not _safe_dsn(settings["database_url"]):
        errors.append("El DSN contiene una contraseña. Usa PGPASSFILE; no guardamos contraseñas en la configuración.")
    try:
        port = int(settings.get("port", PORT_DEFAULT))
        if not 1024 <= port <= 65535:
            raise ValueError
    except ValueError:
        errors.append("El puerto debe ser un número entre 1024 y 65535.")
    for key, label in (("operator_auth_file", "archivo de autenticación"), ("tls_cert", "certificado TLS"), ("tls_key", "clave TLS"), ("pgpassfile", "PGPASSFILE")):
        raw = settings.get(key, "").strip()
        if raw and not Path(raw).expanduser().is_file():
            errors.append(f"No existe el {label} indicado.")
    raw_dir = settings.get("state_dir", "").strip()
    if raw_dir and not Path(raw_dir).expanduser().is_dir():
        errors.append("El directorio de estado no existe. Créalo y restringe sus permisos NTFS antes de continuar.")
    if importlib.util.find_spec("geelark_master_admin") is None:
        errors.append("No se encuentra la API. Instala los paquetes del proyecto en este mismo Python (consulta el manual).")
    return errors


class PcMasterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("960x720")
        self.minsize(820, 620)
        self.configure(bg="#101827")
        self.process: subprocess.Popen | None = None
        self.settings = self._load_settings()
        self.vars: dict[str, tk.StringVar] = {}
        self._style()
        self._build_ui()
        self._refresh_runtime_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#101827")
        style.configure("Panel.TFrame", background="#192437")
        style.configure("TLabel", background="#101827", foreground="#e5edf7", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), foreground="#ffffff")
        style.configure("Sub.TLabel", foreground="#9fb0c7")
        style.configure("Panel.TLabel", background="#192437", foreground="#e5edf7")
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=(12, 8))
        style.configure("Primary.TButton", background="#3b82f6", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#2563eb")])
        style.configure("TEntry", fieldbackground="#f8fafc", foreground="#111827", padding=6)
        style.configure("Status.TLabel", font=("Segoe UI Semibold", 10), foreground="#93c5fd")

    def _load_settings(self) -> dict[str, str]:
        defaults = {"operator_auth_file": "", "state_dir": str(CONFIG_DIR / "state"), "database_url": "postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable", "tls_cert": "", "tls_key": "", "pgpassfile": "", "port": PORT_DEFAULT}
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for key in defaults:
                    if isinstance(data.get(key), str):
                        defaults[key] = data[key]
        except (OSError, json.JSONDecodeError):
            pass
        return defaults

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="GeeLark-IA", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="PC-MASTER · escritorio Windows · versión inicial de pruebas", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        status = ttk.Frame(outer, style="Panel.TFrame", padding=16)
        status.pack(fill="x", pady=(0, 14))
        ttk.Label(status, text="ESTADO DEL PANEL", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Sin iniciar")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=1, sticky="e", padx=(12, 0))
        status.columnconfigure(0, weight=1)
        ttk.Label(status, text="Confinado a este equipo: 127.0.0.1 · sin acceso LAN", style="Panel.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        form = ttk.Frame(outer, style="Panel.TFrame", padding=16)
        form.pack(fill="both", expand=True)
        ttk.Label(form, text="Configuración local", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        fields = [
            ("operator_auth_file", "Archivo hash operador (JSON)", True),
            ("state_dir", "Directorio privado de estado", True),
            ("database_url", "DSN PostgreSQL (sin contraseña)", False),
            ("tls_cert", "Certificado TLS (.crt/.pem)", True),
            ("tls_key", "Clave privada TLS (.key/.pem)", True),
            ("pgpassfile", "Archivo PGPASSFILE privado", True),
            ("port", "Puerto local", False),
        ]
        for row, (key, label, browse) in enumerate(fields, start=1):
            ttk.Label(form, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            var = tk.StringVar(value=self.settings.get(key, ""))
            self.vars[key] = var
            show = "•" if key == "tls_key" else ""
            ttk.Entry(form, textvariable=var, show=show, width=68).grid(row=row, column=1, sticky="ew", pady=5)
            if browse:
                ttk.Button(form, text="Examinar…", command=lambda k=key: self._browse(k)).grid(row=row, column=2, padx=(8, 0), pady=5)
        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(14, 8))
        ttk.Button(buttons, text="Guardar configuración", command=self._save_settings).pack(side="left")
        ttk.Button(buttons, text="Diagnosticar", command=self._diagnose).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Iniciar panel", style="Primary.TButton", command=self._start_panel).pack(side="right")
        ttk.Button(buttons, text="Detener panel", command=self._stop_panel).pack(side="right", padx=(0, 8))

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(8, 0))
        ttk.Label(footer, text="La configuración guarda rutas y parámetros, nunca contraseñas. No se conecta a dispositivos ni ejecuta comandos remotos.", style="Sub.TLabel", wraplength=880).pack(anchor="w")
        ttk.Label(footer, text="Manual: apps/pc-master-windows/README.md", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

    def _browse(self, key: str) -> None:
        selected = filedialog.askdirectory(title="Selecciona el directorio privado de estado") if key == "state_dir" else filedialog.askopenfilename(title="Selecciona un archivo local")
        if selected:
            self.vars[key].set(selected)

    def _current_settings(self) -> dict[str, str]:
        return {key: var.get().strip() for key, var in self.vars.items()}

    def _save_settings(self, quiet: bool = False) -> bool:
        settings = self._current_settings()
        if settings.get("database_url") and not _safe_dsn(settings["database_url"]):
            messagebox.showerror("Contraseña en DSN", "No incluyas contraseñas en el DSN. Usa el archivo PGPASSFILE privado.", parent=self)
            return False
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            # El JSON contiene rutas/configuración, nunca credenciales; el ACL del perfil
            # Windows sigue siendo responsabilidad del usuario y se comprueba en manual.
            CONFIG_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.settings = settings
        except OSError as exc:
            messagebox.showerror("No se pudo guardar", f"No fue posible guardar la configuración local: {exc}", parent=self)
            return False
        if not quiet:
            messagebox.showinfo("Configuración guardada", f"Se guardaron los parámetros locales en:\n{CONFIG_FILE}", parent=self)
        return True

    def _diagnose(self) -> None:
        settings = self._current_settings()
        errors = validate_settings(settings)
        python_ok = sys.version_info >= (3, 11)
        lines = [f"Python: {sys.version.split()[0]} ({'OK' if python_ok else 'requiere 3.11+'})", f"Sistema: {sys.platform}", f"API instalada en este Python: {'sí' if importlib.util.find_spec('geelark_master_admin') else 'no'}", f"Configuración: {'válida' if not errors else 'requiere atención'}"]
        if not python_ok:
            errors.insert(0, "Se requiere Python 3.11 o posterior.")
        lines += ["", *(["Problemas detectados:", *[f"• {e}" for e in errors]] if errors else ["No se detectaron problemas básicos. Aún faltan pruebas reales de TLS, ACL NTFS y permisos PostgreSQL."])]
        messagebox.showinfo("Diagnóstico PC-MASTER", "\n".join(lines), parent=self)

    def _start_panel(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Panel ya iniciado", "El proceso del panel ya está ejecutándose.", parent=self)
            return
        settings = self._current_settings()
        errors = validate_settings(settings)
        if sys.version_info < (3, 11):
            errors.insert(0, "Se requiere Python 3.11 o posterior.")
        if errors:
            messagebox.showerror("No se puede iniciar", "Corrige estos puntos antes de iniciar:\n\n" + "\n".join(f"• {e}" for e in errors), parent=self)
            return
        if not self._save_settings(quiet=True):
            return
        env = os.environ.copy()
        env.update({
            "GEELARK_ADMIN_OPERATOR_AUTH_FILE": settings["operator_auth_file"],
            "GEELARK_ADMIN_STATE_DIR": settings["state_dir"],
            "GEELARK_ADMIN_DATABASE_URL": settings["database_url"],
            "GEELARK_ADMIN_TLS_CERT": settings["tls_cert"],
            "GEELARK_ADMIN_TLS_KEY": settings["tls_key"],
            "GEELARK_ADMIN_BIND_HOST": "127.0.0.1",
            "GEELARK_ADMIN_PORT": settings.get("port", PORT_DEFAULT),
        })
        env.pop("GEELARK_ADMIN_ALLOW_REMOTE", None)
        env["PGPASSFILE"] = settings["pgpassfile"]
        try:
            self.process = subprocess.Popen([sys.executable, "-m", "geelark_master_admin.runtime"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as exc:
            messagebox.showerror("Error de inicio", f"No se pudo iniciar la API con este Python: {exc}", parent=self)
            return
        self.status_var.set("Iniciando…")
        threading.Thread(target=self._wait_for_server, args=(int(settings.get("port", PORT_DEFAULT)), self.process), daemon=True).start()

    def _wait_for_server(self, port: int, process: subprocess.Popen) -> None:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.after(0, lambda: self.status_var.set("No inició · revisa configuración/dependencias"))
                return
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                    self.after(0, lambda: self._server_ready(port, process))
                    return
            except OSError:
                time.sleep(0.25)
        self.after(0, lambda: self.status_var.set("Sin respuesta · revisar diagnóstico"))

    def _server_ready(self, port: int, process: subprocess.Popen) -> None:
        if self.process is process and process.poll() is None:
            self.status_var.set(f"Activo · https://localhost:{port}/")
            webbrowser.open(f"https://localhost:{port}/")

    def _stop_panel(self) -> None:
        process = self.process
        if not process or process.poll() is not None:
            self.status_var.set("Sin iniciar")
            self.process = None
            return
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        self.process = None
        self.status_var.set("Detenido")

    def _refresh_runtime_status(self) -> None:
        if self.process and self.process.poll() is None:
            self.status_var.set("Proceso activo")

    def _on_close(self) -> None:
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno("Cerrar PC-MASTER", "El panel sigue activo. ¿Detenerlo y cerrar?", parent=self):
                return
            self._stop_panel()
        self.destroy()


def main() -> None:
    app = PcMasterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
