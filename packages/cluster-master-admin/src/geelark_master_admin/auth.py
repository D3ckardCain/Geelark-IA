"""Autenticación local de operador con PBKDF2 y sesiones revocables."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import subprocess
import time
from collections import defaultdict, deque
from getpass import getuser
from pathlib import Path
from typing import Callable

PBKDF2_ITERATIONS = 600_000
SESSION_TTL_SECONDS = 8 * 60 * 60
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5


def hash_operator_password(password: str, *, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Devuelve hash PBKDF2 versionado; nunca persiste ni devuelve la contraseña."""
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise ValueError("La contraseña debe tener entre 12 y 1024 caracteres.")
    if iterations < 600_000:
        raise ValueError("El coste PBKDF2 no puede ser inferior a 600000 iteraciones.")
    salt_value = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_value, iterations)
    return "pbkdf2_sha256$" + str(iterations) + "$" + salt_value.hex() + "$" + digest.hex()


def verify_operator_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, salt_hex, digest_hex = encoded.split("$", 3)
        iterations = int(raw_iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if algorithm != "pbkdf2_sha256" or iterations < 600_000 or len(salt) < 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError, UnicodeError):
        return False


class LoginRateLimiter:
    """Limitador en memoria por dirección; pensado para un proceso local único."""
    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, key: str) -> bool:
        now = self._clock()
        bucket = self._attempts[key]
        while bucket and now - bucket[0] >= LOGIN_WINDOW_SECONDS:
            bucket.popleft()
        return len(bucket) < LOGIN_MAX_ATTEMPTS

    def failed(self, key: str) -> None:
        self._attempts[key].append(self._clock())

    def succeeded(self, key: str) -> None:
        self._attempts.pop(key, None)


def _restrict_windows_acl(path: Path, *, directory: bool) -> None:
    """Restringe ACL NTFS al usuario actual; falla cerrado si icacls no funciona."""
    try:
        identity = subprocess.run(
            ["whoami"], check=True, capture_output=True, text=True, timeout=3
        ).stdout.strip()
        grant = f"{identity}:(OI)(CI)F" if directory else f"{identity}:F"
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", grant],
            check=True, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PermissionError("No se pudieron restringir las ACL NTFS del almacén de sesiones.") from exc


class SessionStore:
    """Almacén SQLite de sesiones opacas, con revocación y expiración."""
    def __init__(self, path: str | Path, *, clock: Callable[[], float] = time.time) -> None:
        self.path = Path(path)
        self.clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            if self.path.parent.stat().st_mode & 0o077:
                raise PermissionError("El directorio de sesiones debe tener permisos privados (0700).")
        elif os.name == "nt":
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
        return hashlib.sha256(token.encode("ascii")).hexdigest()

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
