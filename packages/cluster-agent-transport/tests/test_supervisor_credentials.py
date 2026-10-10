import os

import pytest

from cluster_agent_transport.supervisor import _read_token


def test_read_token_accepts_only_private_hexadecimal_file(tmp_path):
    token_file = tmp_path / "node-token"
    token_file.write_text("a" * 64 + "\n", encoding="ascii")
    token_file.chmod(0o600)

    assert _read_token(token_file) == "a" * 64

    token_file.chmod(0o644)
    with pytest.raises(ValueError, match="permisos privados"):
        _read_token(token_file)


def test_read_token_rejects_symlink_and_invalid_contents(tmp_path):
    target = tmp_path / "target"
    target.write_text("a" * 64, encoding="ascii")
    target.chmod(0o600)
    link = tmp_path / "node-token-link"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="enlace"):
        _read_token(link)

    target.write_text("not-a-token", encoding="ascii")
    with pytest.raises(ValueError, match="credencial hexadecimal"):
        _read_token(target)
