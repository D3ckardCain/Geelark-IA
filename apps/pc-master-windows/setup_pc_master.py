"""Preparación inicial Windows desde la descarga GitHub, sin consola manual."""
import base64
import ctypes
import hashlib
import hmac
import json
import os
import queue
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PRIVATE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GeeLark-IA" / "pc-master"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ARTIFACTS = ("operator-auth.json", "master-local.crt", "master-local.key", "pgpass.conf", "settings.json", "state")


def require_normal_user():
    if os.name != "nt":
        raise RuntimeError("Este asistente prepara PC-MASTER en Windows.")
    if ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError("Cierra y abre PREPARAR_PC_MASTER.bat con doble clic normal, sin Ejecutar como administrador.")


def existing_installation(directory):
    settings = directory / "settings.json"
    if not settings.exists():
        if any((directory / name).exists() for name in ARTIFACTS):
            raise RuntimeError("Hay una preparación incompleta. No se sobrescribieron archivos privados.")
        return False
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
        complete = all(isinstance(data.get(key), str) and Path(data[key]).is_file() for key in
                       ("operator_auth_file", "tls_cert", "tls_key", "pgpassfile"))
        if not complete or not Path(data.get("state_dir", "__missing__")).is_dir():
            raise ValueError
    except (OSError, ValueError, TypeError):
        raise RuntimeError("La configuración existente requiere revisión; no se sobrescribió.")
    return True


def bootstrap():
    require_normal_user()
    if sys.version_info < (3, 11):
        raise RuntimeError("Se necesita Python 3.11 o posterior.")
    for name in ("cluster-persistence", "cluster-master-admin"):
        if not (PROJECT / "packages" / name / "pyproject.toml").is_file():
            raise RuntimeError("Extrae la descarga completa de GitHub antes de preparar PC-MASTER.")
    python = PROJECT / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(PROJECT / ".venv")], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(PROJECT / "packages/cluster-persistence"),
                    "-e", str(PROJECT / "packages/cluster-master-admin")], check=True)
    subprocess.run([str(python), "-c", "import tkinter, geelark_master_admin.android_control"], check=True)
    subprocess.Popen([str(python.with_name("pythonw.exe")), str(Path(__file__).resolve()), "--wizard"], cwd=PROJECT)


def locate_openssl():
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    openssl = shutil.which("openssl")
    if not openssl:
        candidate = program_files / "Git/usr/bin/openssl.exe"
        if candidate.is_file():
            openssl = str(candidate)
    if not openssl:
        raise RuntimeError("Falta OpenSSL. El incluido con Git para Windows es compatible; no se descargará software automáticamente.")
    return openssl


def pgpass_escape(value):
    return value.replace("\\", "\\\\").replace(":", "\\:")


def scram_verifier(password):
    # La contraseña del lector se genera como ASCII aleatorio, sin normalización SASL pendiente.
    password.encode("ascii")
    salt = secrets.token_bytes(16)
    salted = hashlib.pbkdf2_hmac("sha256", password.encode("ascii"), salt, 4096)
    client = hmac.digest(salted, b"Client Key", "sha256")
    stored = hashlib.sha256(client).digest()
    server = hmac.digest(salted, b"Server Key", "sha256")
    b64 = lambda value: base64.b64encode(value).decode("ascii")
    return f"SCRAM-SHA-256$4096:{b64(salt)}${b64(stored)}:{b64(server)}"


def write_private(path, text):
    from geelark_master_admin.auth import _restrict_windows_acl
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    _restrict_windows_acl(path, directory=False)


def prepare_database(passfile, reader_password, report):
    import psycopg
    from psycopg import sql
    connect = dict(host="localhost", port=5432, user="postgres", passfile=str(passfile), connect_timeout=8, autocommit=True)
    with psycopg.connect(dbname="postgres", **connect) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname='geelark'").fetchone():
            conn.execute("CREATE DATABASE geelark")
    with psycopg.connect(dbname="geelark", **connect) as conn:
        present = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='geelark_control'").fetchone()[0]
        if present == 0:
            report("Preparando las cinco migraciones…")
            for path in sorted((PROJECT / "db/migrations").glob("*.sql")):
                conn.execute(path.read_text(encoding="utf-8"), prepare=False)
        else:
            required = ("nodes", "node_credentials", "agent_request_nonces", "agent_tasks", "schema_migrations")
            found = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='geelark_control'").fetchall()
            columns = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='geelark_control' AND table_name='nodes'").fetchall()
            if not set(required).issubset({r[0] for r in found}) or not {"module_reports", "reported_health_state", "agent_rate_window_count"}.issubset({r[0] for r in columns}):
                raise RuntimeError("La base geelark existente tiene un esquema incompleto. No se aplicarán migraciones a ciegas.")
        role_script = PROJECT / "packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql"
        conn.execute(role_script.read_text(encoding="utf-8"), prepare=False)
        conn.execute(sql.SQL("ALTER ROLE geelark_master_reader PASSWORD {}").format(sql.Literal(scram_verifier(reader_password))))
    reader_pass = passfile.with_name("reader.pgpass")
    try:
        write_private(reader_pass, "localhost:5432:geelark:geelark_master_reader:" + reader_password + "\n")
        with psycopg.connect(dbname="geelark", host="localhost", port=5432, user="geelark_master_reader", passfile=str(reader_pass), connect_timeout=8) as conn:
            if conn.execute("SHOW transaction_read_only").fetchone()[0] != "on":
                raise RuntimeError("El lector no quedó en modo de solo lectura.")
            conn.execute("SELECT node_id FROM geelark_control.nodes LIMIT 1").fetchall()
    finally:
        reader_pass.unlink(missing_ok=True)
    report("Base de datos y lector verificados.")


def provision(admin_password, operator_password, android_config, report, directory=PRIVATE):
    require_normal_user()
    if existing_installation(directory):
        report("Se conserva la configuración existente. No se cambiaron contraseñas ni certificados.")
        return
    if len(operator_password) < 12:
        raise ValueError("La contraseña del panel debe tener al menos 12 caracteres.")
    if "\n" in admin_password or "\r" in admin_password:
        raise ValueError("La contraseña PostgreSQL no puede contener saltos de línea.")
    openssl = locate_openssl()
    from geelark_master_admin.auth import _restrict_windows_acl, hash_operator_password
    directory.mkdir(parents=True, exist_ok=True)
    _restrict_windows_acl(directory, directory=True)
    lock = directory / "preparation.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError("Ya existe un bloqueo de preparación. Comprueba si otro asistente sigue abierto; no se modificaron archivos.")
    os.close(fd)
    committed = []
    try:
        # Los temporales nuevos se borran al terminar; no son copias de datos existentes.
        with tempfile.TemporaryDirectory(prefix="preparation-", dir=directory) as stage_name:
            stage = Path(stage_name)
            _restrict_windows_acl(stage, directory=True)
            admin_pass = stage / "admin.pgpass"
            reader_password = secrets.token_urlsafe(32)
            try:
                write_private(admin_pass, "localhost:5432:*:postgres:" + pgpass_escape(admin_password) + "\n")
                prepare_database(admin_pass, reader_password, report)
            finally:
                admin_pass.unlink(missing_ok=True)
                admin_password = None
            report("Creando credencial del panel y certificado HTTPS local…")
            write_private(stage / "operator-auth.json", json.dumps({"password_hash": hash_operator_password(operator_password)}) + "\n")
            operator_password = None
            subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-sha256", "-days", "365", "-nodes",
                            "-keyout", str(stage / "master-local.key"), "-out", str(stage / "master-local.crt"),
                            "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, creationflags=FLAGS)
            for name in ("master-local.key", "master-local.crt"):
                _restrict_windows_acl(stage / name, directory=False)
            write_private(stage / "pgpass.conf", "localhost:5432:geelark:geelark_master_reader:" + reader_password + "\n")
            reader_password = None
            (stage / "state").mkdir()
            _restrict_windows_acl(stage / "state", directory=True)
            settings = {"operator_auth_file": str(directory / "operator-auth.json"), "state_dir": str(directory / "state"),
                        "database_url": "postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable",
                        "tls_cert": str(directory / "master-local.crt"), "tls_key": str(directory / "master-local.key"),
                        "pgpassfile": str(directory / "pgpass.conf"), "port": "8765", "android_config_file": android_config}
            write_private(stage / "settings.json", json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
            for name in ARTIFACTS:
                if name == "settings.json":
                    continue
                os.rename(stage / name, directory / name)
                committed.append(directory / name)
            os.rename(stage / "settings.json", directory / "settings.json")
            committed.append(directory / "settings.json")
        report("Preparación completa. El certificado es local; su confianza en Windows se verifica por separado.")
    except Exception:
        for path in reversed(committed):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink(missing_ok=True)
        raise
    finally:
        lock.unlink(missing_ok=True)


def wizard():
    import tkinter as tk
    from tkinter import ttk, simpledialog, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
    require_normal_user()
    root = tk.Tk()
    root.title("GeeLark-IA · Preparar PC-MASTER")
    root.geometry("680x430")
    ttk.Label(root, text="Preparación inicial", font=("Segoe UI", 18)).pack(anchor="w", padx=20, pady=15)
    ttk.Label(root, text="Configura PostgreSQL local, acceso al panel, HTTPS y rutas.\nUna instalación completa existente se conserva.").pack(anchor="w", padx=20)
    area = ScrolledText(root, height=10, state="disabled")
    area.pack(fill="both", expand=True, padx=20, pady=12)
    events = queue.Queue()
    running = False
    ready = False

    def open_launcher():
        subprocess.Popen([sys.executable, str(PROJECT / "apps/pc-master-windows/pc_master.py")], creationflags=FLAGS)
        root.destroy()

    def start():
        nonlocal running
        if running:
            return
        admin = operator = ""
        config = ""
        try:
            existing = existing_installation(PRIVATE)
            if not existing:
                locate_openssl()
                admin = simpledialog.askstring("PostgreSQL local", "Contraseña del administrador postgres:", show="*", parent=root)
                if admin is None:
                    return
                operator = simpledialog.askstring("Acceso al panel", "Nueva contraseña del panel (mínimo 12 caracteres):", show="*", parent=root)
                if operator is None:
                    return
                confirm = simpledialog.askstring("Confirmar acceso", "Repite la contraseña del panel:", show="*", parent=root)
                if operator != confirm or len(operator) < 12:
                    raise ValueError("Las contraseñas deben coincidir y tener al menos 12 caracteres.")
                if messagebox.askyesno("Conexión Android", "¿Seleccionar un JSON de conexión Android existente? Es opcional.", parent=root):
                    config = filedialog.askopenfilename(parent=root, title="Conexión Android", filetypes=[("JSON", "*.json")])
            running = True
            prepare.config(state="disabled")
            def work(admin, operator, config):
                try:
                    provision(admin, operator, config, events.put)
                    events.put(True)
                except Exception as error:
                    detail = str(error)
                    for secret in (admin, operator):
                        if secret:
                            detail = detail.replace(secret, "[oculto]")
                    events.put("ERROR: " + detail)
                    events.put(False)
                finally:
                    admin = operator = None
            threading.Thread(target=work, args=(admin, operator, config), daemon=True).start()
        except Exception as error:
            messagebox.showerror("Preparación", str(error), parent=root)

    bar = ttk.Frame(root)
    bar.pack(fill="x", padx=20, pady=(0, 15))
    prepare = ttk.Button(bar, text="Preparar PC-MASTER", command=start)
    prepare.pack(side="left")
    launch = ttk.Button(bar, text="Abrir lanzador", command=open_launcher, state="disabled")
    launch.pack(side="right")

    def poll():
        nonlocal running, ready
        while not events.empty():
            item = events.get_nowait()
            if type(item) is bool:
                running = False
                ready = item
                prepare.config(state="disabled" if ready else "normal")
                launch.config(state="normal" if ready else "disabled")
            else:
                area.config(state="normal")
                area.insert("end", item + "\n")
                area.see("end")
                area.config(state="disabled")
        root.after(150, poll)

    def close():
        if running:
            messagebox.showinfo("Preparación en curso", "Espera a que termine la operación actual.", parent=root)
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    root.mainloop()


if __name__ == "__main__":
    try:
        wizard() if "--wizard" in sys.argv else bootstrap()
    except Exception as error:
        if "--wizard" in sys.argv:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Preparar PC-MASTER", str(error))
        else:
            print("No se completó la preparación:", error)
        raise SystemExit(1)
