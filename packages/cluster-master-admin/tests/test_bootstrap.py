from __future__ import annotations

import json
import os
import sys

import pytest
from pathlib import Path

from geelark_master_admin import bootstrap


def test_windows_bootstrap_verifies_parent_acl_before_restricting_output(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "private" / "operator-auth.json"
    calls: list[tuple[str, Path, bool | None]] = []

    class WindowsOsProxy:
        name = "nt"
        O_WRONLY = os.O_WRONLY
        O_CREAT = os.O_CREAT
        O_EXCL = os.O_EXCL
        open = staticmethod(os.open)
        fdopen = staticmethod(os.fdopen)

    monkeypatch.setattr(bootstrap, "os", WindowsOsProxy)
    monkeypatch.setattr(bootstrap, "getpass", lambda _prompt: "a-long-test-password")
    monkeypatch.setattr(bootstrap, "hash_operator_password", lambda _password: "test-only-hash")
    monkeypatch.setattr(
        bootstrap,
        "_verify_windows_acl_no_untrusted_writers",
        lambda path: calls.append(("verify", path, None)),
    )
    monkeypatch.setattr(
        bootstrap,
        "_restrict_windows_acl",
        lambda path, *, directory: calls.append(("restrict", path, directory)),
    )
    monkeypatch.setattr(sys, "argv", ["geelark-master-admin-bootstrap", "--output", str(target)])

    assert bootstrap.main() == 0

    assert calls == [
        ("verify", target.parent.parent, None),
        ("restrict", target.parent, True),
        ("restrict", target, False),
    ]
    assert json.loads(target.read_text(encoding="utf-8")) == {"password_hash": "test-only-hash"}


def test_windows_bootstrap_fails_closed_when_parent_acl_is_untrusted(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "private" / "operator-auth.json"
    restricted: list[Path] = []

    class WindowsOsProxy:
        name = "nt"
        O_WRONLY = os.O_WRONLY
        O_CREAT = os.O_CREAT
        O_EXCL = os.O_EXCL
        open = staticmethod(os.open)
        fdopen = staticmethod(os.fdopen)

    def reject_parent(_path: Path) -> None:
        raise PermissionError("ACL superior no confiable")

    monkeypatch.setattr(bootstrap, "os", WindowsOsProxy)
    monkeypatch.setattr(bootstrap, "getpass", lambda _prompt: "a-long-test-password")
    monkeypatch.setattr(bootstrap, "hash_operator_password", lambda _password: "test-only-hash")
    monkeypatch.setattr(bootstrap, "_verify_windows_acl_no_untrusted_writers", reject_parent)
    monkeypatch.setattr(
        bootstrap,
        "_restrict_windows_acl",
        lambda path, *, directory: restricted.append(path),
    )
    monkeypatch.setattr(sys, "argv", ["geelark-master-admin-bootstrap", "--output", str(target)])

    with pytest.raises(SystemExit) as error:
        bootstrap.main()

    assert error.value.code == 2
    assert restricted == []
    assert not target.exists()


@pytest.mark.skipif(os.name != "posix", reason="La comprobación POSIX no aplica en Windows.")
def test_posix_bootstrap_rejects_writable_parent_directory(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "private" / "operator-auth.json"
    tmp_path.chmod(0o777)
    monkeypatch.setattr(bootstrap, "getpass", lambda _prompt: "a-long-test-password")
    monkeypatch.setattr(bootstrap, "hash_operator_password", lambda _password: "test-only-hash")
    monkeypatch.setattr(sys, "argv", ["geelark-master-admin-bootstrap", "--output", str(target)])

    with pytest.raises(SystemExit) as error:
        bootstrap.main()

    assert error.value.code == 2
    assert not target.exists()
