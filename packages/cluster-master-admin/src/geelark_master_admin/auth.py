"""Autenticación local de operador con PBKDF2 y sesiones revocables."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import stat
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Callable

PBKDF2_MIN_ITERATIONS = 600_000
PBKDF2_MAX_ITERATIONS = 2_000_000
PBKDF2_ITERATIONS = PBKDF2_MIN_ITERATIONS
SESSION_TTL_SECONDS = 8 * 60 * 60
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5
LOGIN_MAX_TRACKED_CLIENTS = 1024


def hash_operator_password(password: str, *, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Devuelve hash PBKDF2 versionado; nunca persiste ni devuelve la contraseña."""
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise ValueError("La contraseña debe tener entre 12 y 1024 caracteres.")
    if not PBKDF2_MIN_ITERATIONS <= iterations <= PBKDF2_MAX_ITERATIONS:
        raise ValueError("El coste PBKDF2 debe estar entre 600000 y 2000000 iteraciones.")
    salt_value = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_value, iterations)
    return "pbkdf2_sha256$" + str(iterations) + "$" + salt_value.hex() + "$" + digest.hex()


def verify_operator_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, salt_hex, digest_hex = encoded.split("$", 3)
        iterations = int(raw_iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if algorithm != "pbkdf2_sha256" or not PBKDF2_MIN_ITERATIONS <= iterations <= PBKDF2_MAX_ITERATIONS or len(salt) < 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError, UnicodeError):
        return False


class LoginRateLimiter:
    """Limitador local con ventana temporal y número máximo de direcciones rastreadas."""
    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._attempts: dict[str, deque[float]] = {}

    def _prune_expired(self, now: float) -> None:
        for key, bucket in list(self._attempts.items()):
            while bucket and now - bucket[0] >= LOGIN_WINDOW_SECONDS:
                bucket.popleft()
            if not bucket:
                self._attempts.pop(key, None)

    def allowed(self, key: str) -> bool:
        now = self._clock()
        bucket = self._attempts.get(key)
        if bucket is not None:
            while bucket and now - bucket[0] >= LOGIN_WINDOW_SECONDS:
                bucket.popleft()
            if bucket:
                return len(bucket) < LOGIN_MAX_ATTEMPTS
            self._attempts.pop(key, None)

        if len(self._attempts) >= LOGIN_MAX_TRACKED_CLIENTS:
            self._prune_expired(now)
            if len(self._attempts) >= LOGIN_MAX_TRACKED_CLIENTS:
                # Fail closed instead of allocating unbounded per-address state.
                return False

        self._attempts[key] = deque()
        return True

    def failed(self, key: str) -> None:
        bucket = self._attempts.get(key)
        if bucket is None:
            now = self._clock()
            self._prune_expired(now)
            if len(self._attempts) >= LOGIN_MAX_TRACKED_CLIENTS:
                return
            bucket = deque()
            self._attempts[key] = bucket
        bucket.append(self._clock())

    def succeeded(self, key: str) -> None:
        self._attempts.pop(key, None)



def _verify_windows_acl_no_untrusted_writers(path: Path) -> None:
    """Comprueba ACL de una ruta sin modificarla; solo usuario/SYSTEM/admin pueden escribir."""
    try:
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if not powershell.is_file():
            raise FileNotFoundError("No se encontró Windows PowerShell.")
        script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:GEELARK_ACL_TARGET
$currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$trustedSids = @(
    $currentSid,
    'S-1-5-18',
    'S-1-5-32-544',
    'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
)
$writeMask = [int]([System.Security.AccessControl.FileSystemRights]::WriteData) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::AppendData) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::WriteExtendedAttributes) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::WriteAttributes) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::Delete) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::ChangePermissions) -bor
             [int]([System.Security.AccessControl.FileSystemRights]::TakeOwnership)
$acl = Get-Acl -LiteralPath $target
$ownerSid = $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
if ($trustedSids -notcontains $ownerSid) {
    [Console]::Error.WriteLine('UNTRUSTED_OWNER')
    exit 13
}
foreach ($entry in $acl.Access) {
    if ($entry.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) { continue }
    if (($entry.PropagationFlags -band [System.Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0) { continue }
    $sid = $entry.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
    $rights = [int]$entry.FileSystemRights
    if (($trustedSids -notcontains $sid) -and (($rights -band $writeMask) -ne 0)) {
        [Console]::Error.WriteLine('UNTRUSTED_WRITE_ACE')
        exit 13
    }
}
[Console]::Out.WriteLine('OK')
"""
        env = os.environ.copy()
        env["GEELARK_ACL_TARGET"] = str(path)
        result = subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
            env=env,
        )
    except Exception:
        raise PermissionError("No se pudieron verificar las ACL NTFS de la ruta protegida.") from None
    if result.returncode != 0 or result.stdout.strip() != "OK":
        raise PermissionError(
            "Las ACL NTFS permiten escritura por identidades no confiables o no pudieron verificarse."
        )


def _restrict_windows_acl(path: Path, *, directory: bool) -> None:
    """Restringe ACL NTFS al usuario actual mediante PowerShell y verifica con icacls."""
    try:
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        icacls = system_root / "System32" / "icacls.exe"
        if not powershell.is_file() or not icacls.is_file():
            raise FileNotFoundError("No se encontraron las herramientas del sistema Windows.")
        script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:GEELARK_ACL_TARGET
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = Get-Acl -LiteralPath $target
$acl.SetAccessRuleProtection($true, $false)
foreach ($entry in @($acl.Access)) {
    [void]$acl.RemoveAccessRuleSpecific($entry)
}
$acl.SetOwner($identity)
$inheritance = [System.Security.AccessControl.InheritanceFlags]::None
if ($env:GEELARK_ACL_DIRECTORY -eq '1') {
    $inheritance = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
                   [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
}
$rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
    $identity,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    $inheritance,
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AccessControlType]::Allow
)
[void]$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $target -AclObject $acl
[Console]::Out.WriteLine([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
"""
        env = os.environ.copy()
        env["GEELARK_ACL_TARGET"] = str(path)
        env["GEELARK_ACL_DIRECTORY"] = "1" if directory else "0"
        result = subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
            env=env,
        )
        identity = result.stdout.strip()
        if not identity:
            raise PermissionError("No se pudo identificar al usuario actual para ACL NTFS.")
        verification = subprocess.run(
            [str(icacls), str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
        entries: list[tuple[str, str]] = []
        target_text = str(path)
        for line in verification.splitlines():
            if ":(" not in line:
                continue
            entry = line.strip()
            if entry.casefold().startswith(target_text.casefold()):
                entry = entry[len(target_text):].strip()
                if entry.startswith(":"):
                    entry = entry[1:].strip()
            ace_identity = entry.split(":(", 1)[0].strip()
            if ace_identity:
                entries.append((ace_identity, line))
        if (
            len(entries) != 1
            or entries[0][0].casefold() != identity.casefold()
            or "(F)" not in entries[0][1].upper()
            or "DENY" in entries[0][1].upper()
        ):
            raise PermissionError(
                "La ACL NTFS resultante no quedó limitada al usuario actual con control total."
            )
    except PermissionError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise PermissionError("No se pudieron restringir las ACL NTFS del almacén de sesiones.") from exc


class SessionStore:
    """Almacén SQLite de sesiones opacas, con revocación y expiración."""
    def __init__(self, path: str | Path, *, clock: Callable[[], float] = time.time) -> None:
        self.path = Path(path)
        self.clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            state_dir_info = self.path.parent.stat()
            if state_dir_info.st_uid != os.geteuid():
                raise PermissionError(
                    "El directorio de sesiones debe pertenecer al usuario que ejecuta PC-MASTER."
                )
            if stat.S_IMODE(state_dir_info.st_mode) & 0o077:
                raise PermissionError("El directorio de sesiones debe tener permisos privados (0700).")
            parent_info = self.path.parent.parent.stat()
            if parent_info.st_uid not in {os.geteuid(), 0}:
                raise PermissionError(
                    "El directorio superior de sesiones debe pertenecer al usuario actual o a root."
                )
            parent_mode = stat.S_IMODE(parent_info.st_mode)
            if parent_mode & 0o022 and not (
                parent_mode & stat.S_ISVTX and parent_info.st_uid == 0
            ):
                raise PermissionError(
                    "El directorio superior de sesiones no puede permitir escritura a grupo/otros, "
                    "salvo un directorio raíz con sticky bit."
                )
        elif os.name == "nt":
            _verify_windows_acl_no_untrusted_writers(self.path.parent.parent)
            _restrict_windows_acl(self.path.parent, directory=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operator_sessions (
                    token_hash TEXT PRIMARY KEY,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS operator_sessions_expiry_idx ON operator_sessions(expires_at)")
            conn.commit()
        if os.name == "posix":
            try:
                self.path.chmod(0o600)
                if self.path.stat().st_mode & 0o077:
                    raise PermissionError("El archivo SQLite no quedó privado.")
            except OSError as exc:
                raise PermissionError("No se pudieron restringir los permisos del archivo de sesiones.") from exc
        elif os.name == "nt":
            _restrict_windows_acl(self.path, directory=False)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=1.0)
        conn.execute("PRAGMA busy_timeout = 1000")
        return conn

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create(self) -> str:
        now = int(self.clock())
        token = secrets.token_urlsafe(32)
        with self._connect() as conn:
            conn.execute("DELETE FROM operator_sessions WHERE expires_at <= ?", (now,))
            conn.execute(
                "INSERT INTO operator_sessions(token_hash, created_at, expires_at) VALUES (?, ?, ?)",
                (self._token_hash(token), now, now + SESSION_TTL_SECONDS),
            )
            conn.commit()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
        return token

    def valid(self, token: str | None) -> bool:
        if not token or len(token) > 128:
            return False
        now = int(self.clock())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM operator_sessions WHERE token_hash = ? AND expires_at > ?",
                (self._token_hash(token), now),
            ).fetchone()
        return row is not None

    def revoke(self, token: str | None) -> None:
        if not token or len(token) > 128:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM operator_sessions WHERE token_hash = ?", (self._token_hash(token),))
            conn.commit()
