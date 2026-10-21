from __future__ import annotations

import os
from pathlib import Path

import pytest

from geelark_master_admin.auth import (
    SESSION_TTL_SECONDS,
    SessionStore,
    _restrict_windows_acl,
    hash_operator_password,
    verify_operator_password,
)


def test_password_hash_uses_random_salt_and_verifies() -> None:
    password = "Correct Horse Battery 2030!"
    first = hash_operator_password(password)
    second = hash_operator_password(password)
    assert first != second
    assert verify_operator_password(password, first)
    assert not verify_operator_password("wrong password", first)


def test_password_policy_and_malformed_hash_fail_closed() -> None:
    with pytest.raises(ValueError):
        hash_operator_password("short")
    with pytest.raises(ValueError):
        hash_operator_password("long-enough-password", iterations=1000)
    assert not verify_operator_password("password", "plaintext")
    assert not verify_operator_password("password", "pbkdf2_sha256$1$00$00")
    with pytest.raises(ValueError, match="entre 600000 y 2000000"):
        hash_operator_password("long-enough-password", iterations=2_000_001)
    oversized_cost_hash = "pbkdf2_sha256$2000001$" + ("00" * 16) + "$" + ("00" * 32)
    assert not verify_operator_password("password", oversized_cost_hash)


def test_sessions_are_hashed_revocable_and_expire(tmp_path: Path) -> None:
    if os.name == "nt":
        _restrict_windows_acl(tmp_path, directory=True)
    now = [1_000_000.0]
    store = SessionStore(tmp_path / "private" / "sessions.sqlite3", clock=lambda: now[0])
    token = store.create()
    assert token
    assert not store.valid("cookie-☃-no-ascii")
    store.revoke("cookie-☃-no-ascii")
    assert store.valid(token)
    with store._connect() as conn:
        row = conn.execute("SELECT token_hash FROM operator_sessions").fetchone()
    assert row[0] != token
    store.revoke(token)
    assert not store.valid(token)

    second = store.create()
    assert store.valid(second)
    now[0] += SESSION_TTL_SECONDS + 1
    assert not store.valid(second)


def test_session_database_permissions_are_restricted(tmp_path: Path) -> None:
    if os.name == "nt":
        _restrict_windows_acl(tmp_path, directory=True)
    path = tmp_path / "private" / "sessions.sqlite3"
    SessionStore(path)
    assert path.exists()
    if os.name == "posix":
        assert path.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("directory", [False, True])
def test_windows_acl_resets_old_explicit_entries_before_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, directory: bool
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    calls: list[list[str]] = []
    target = tmp_path / ("sessions" if directory else "sessions.sqlite3")

    def fake_is_file(path: Path) -> bool:
        return path.name.lower() in {"whoami.exe", "icacls.exe"}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        if command[0].lower().endswith("whoami.exe"):
            return SimpleNamespace(stdout=r"PC-MASTER\operator")
        if len(calls) == 2:
            return SimpleNamespace(stdout="ACL updated")
        flags = "(OI)(CI)(F)" if directory else "(F)"
        return SimpleNamespace(stdout=f"{target} PC-MASTER\\operator:{flags}\n")

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subprocess, "run", fake_run)

    auth_module._restrict_windows_acl(target, directory=directory)

    expected_grant = r"PC-MASTER\operator:(OI)(CI)F" if directory else r"PC-MASTER\operator:F"
    assert len(calls) == 3
    assert calls[1][0].lower().endswith("icacls.exe")
    assert calls[1][2:] == [
        "/reset",
        "/inheritancelevel:r",
        "/grant:r",
        expected_grant,
    ]
    assert calls[2] == [calls[1][0], str(target)]


def test_windows_acl_verification_rejects_unexpected_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    target = tmp_path / "sessions.sqlite3"

    def fake_is_file(path: Path) -> bool:
        return path.name.lower() in {"whoami.exe", "icacls.exe"}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        if command[0].lower().endswith("whoami.exe"):
            return SimpleNamespace(stdout=r"PC-MASTER\operator")
        if "/grant:r" in command:
            return SimpleNamespace(stdout="ACL updated")
        return SimpleNamespace(
            stdout=(
                f"{target} PC-MASTER\\operator:(F)\n"
                "             BUILTIN\\Users:(R)\n"
            )
        )

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PermissionError, match="ACL NTFS resultante"):
        auth_module._restrict_windows_acl(target, directory=False)


def test_windows_acl_verification_rejects_empty_acl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    target = tmp_path / "sessions.sqlite3"

    def fake_is_file(path: Path) -> bool:
        return path.name.lower() in {"whoami.exe", "icacls.exe"}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        if command[0].lower().endswith("whoami.exe"):
            return SimpleNamespace(stdout=r"PC-MASTER\operator")
        if "/grant:r" in command:
            return SimpleNamespace(stdout="ACL updated")
        return SimpleNamespace(stdout=f"{target}\n")

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PermissionError, match="ACL NTFS resultante"):
        auth_module._restrict_windows_acl(target, directory=False)


def test_windows_acl_failure_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    def fake_is_file(path: Path) -> bool:
        return path.name.lower() in {"whoami.exe", "icacls.exe"}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PermissionError, match="ACL NTFS"):
        auth_module._restrict_windows_acl(tmp_path / "sessions.sqlite3", directory=False)


def test_login_rate_limiter_enforces_window_and_success_resets() -> None:
    from geelark_master_admin.auth import (
        LOGIN_MAX_ATTEMPTS,
        LOGIN_WINDOW_SECONDS,
        LoginRateLimiter,
    )

    now = [100.0]
    limiter = LoginRateLimiter(clock=lambda: now[0])
    key = "127.0.0.1"
    for _ in range(LOGIN_MAX_ATTEMPTS):
        assert limiter.allowed(key)
        limiter.failed(key)
    assert not limiter.allowed(key)
    now[0] += LOGIN_WINDOW_SECONDS
    assert limiter.allowed(key)
    limiter.succeeded(key)
    assert limiter.allowed(key)


def test_login_rate_limiter_caps_tracked_addresses_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geelark_master_admin import auth as auth_module

    monkeypatch.setattr(auth_module, "LOGIN_MAX_TRACKED_CLIENTS", 2)
    now = [100.0]
    limiter = auth_module.LoginRateLimiter(clock=lambda: now[0])
    for key in ("client-a", "client-b"):
        assert limiter.allowed(key)
        limiter.failed(key)
    assert len(limiter._attempts) == 2
    assert not limiter.allowed("client-c")
    assert len(limiter._attempts) == 2

    now[0] += auth_module.LOGIN_WINDOW_SECONDS
    assert limiter.allowed("client-c")
    assert len(limiter._attempts) == 1


@pytest.mark.skipif(os.name != "posix", reason="La propiedad POSIX no aplica en Windows.")
def test_session_directory_must_belong_to_process_user(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    path = tmp_path / "private" / "sessions.sqlite3"
    path.parent.mkdir(mode=0o700)
    original_stat = Path.stat

    def fake_stat(target: Path, *args: object, **kwargs: object):
        result = original_stat(target, *args, **kwargs)
        if target == path.parent:
            return SimpleNamespace(st_uid=os.geteuid() + 1, st_mode=result.st_mode)
        return result

    monkeypatch.setattr(Path, "stat", fake_stat)
    with pytest.raises(PermissionError, match="pertenecer al usuario"):
        SessionStore(path)


@pytest.mark.skipif(os.name != "posix", reason="Los permisos POSIX no aplican en Windows.")
def test_session_directory_rejects_replaceable_parent(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o777)
    state_dir = shared / "private"
    state_dir.mkdir(mode=0o700)
    with pytest.raises(PermissionError, match="directorio superior de sesiones"):
        SessionStore(state_dir / "sessions.sqlite3")


def test_windows_parent_acl_verifier_accepts_trusted_acl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    system_root = tmp_path / "windows"
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    powershell.parent.mkdir(parents=True)
    powershell.write_text("test placeholder", encoding="utf-8")
    target = tmp_path / "private"
    target.mkdir()
    monkeypatch.setenv("SystemRoot", str(system_root))
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        assert kwargs["env"]["GEELARK_ACL_TARGET"] == str(target)
        assert "Get-Acl" in command[-1]
        assert "GetOwner" in command[-1]
        assert "UNTRUSTED_OWNER" in command[-1]
        return SimpleNamespace(returncode=0, stdout="OK\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    auth_module._verify_windows_acl_no_untrusted_writers(target)
    assert len(calls) == 1


def test_windows_parent_acl_verifier_fails_closed_on_untrusted_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from geelark_master_admin import auth as auth_module

    system_root = tmp_path / "windows"
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    powershell.parent.mkdir(parents=True)
    powershell.write_text("test placeholder", encoding="utf-8")
    target = tmp_path / "private"
    target.mkdir()
    monkeypatch.setenv("SystemRoot", str(system_root))
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=13, stdout="", stderr="UNTRUSTED_WRITE_ACE"),
    )
    with pytest.raises(PermissionError, match="ACL NTFS"):
        auth_module._verify_windows_acl_no_untrusted_writers(target)


@pytest.mark.skipif(os.name != "nt", reason="Prueba de integración exclusiva de Windows.")
def test_windows_acl_verifier_accepts_private_directory_on_real_ntfs(tmp_path: Path) -> None:
    from geelark_master_admin import auth as auth_module

    target = tmp_path / "private-accepted"
    target.mkdir()
    auth_module._restrict_windows_acl(target, directory=True)
    auth_module._verify_windows_acl_no_untrusted_writers(target)


@pytest.mark.skipif(os.name != "nt", reason="Prueba de integración exclusiva de Windows.")
def test_windows_acl_verifier_rejects_users_group_write_on_real_ntfs(tmp_path: Path) -> None:
    import subprocess

    from geelark_master_admin import auth as auth_module

    target = tmp_path / "private-rejected"
    target.mkdir()
    auth_module._restrict_windows_acl(target, directory=True)
    subprocess.run(
        ["icacls", str(target), "/grant", "*S-1-5-32-545:(OI)(CI)(M)"],
        check=True,
        capture_output=True,
        text=True,
    )
    with pytest.raises(PermissionError, match="ACL NTFS"):
        auth_module._verify_windows_acl_no_untrusted_writers(target)
