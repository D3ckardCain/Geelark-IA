import os

import pytest

from cluster_agent_transport.credentials import (
    CredentialProviderError,
    SystemdCredentialProvider,
)


TOKEN = "a" * 64


def secure_file(path, content=TOKEN.encode("ascii") + b"\n", mode=0o400):
    path.write_bytes(content)
    path.chmod(mode)
    return path


def test_reads_token_from_systemd_credentials_directory(tmp_path, monkeypatch):
    secure_file(tmp_path / "geelark-agent-token")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path))
    provider = SystemdCredentialProvider()
    assert provider.load_bearer_token() == TOKEN


def test_explicit_credentials_directory_takes_precedence(tmp_path, monkeypatch):
    directory = tmp_path / "credentials"
    directory.mkdir(mode=0o700)
    secure_file(directory / "custom-token", b"b" * 64, mode=0o400)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path / "wrong"))
    provider = SystemdCredentialProvider(
        credential_name="custom-token",
        credentials_directory=directory,
    )
    assert provider.load_bearer_token() == "b" * 64


def test_missing_or_invalid_systemd_directory_is_reported_without_secret(monkeypatch):
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    with pytest.raises(CredentialProviderError, match="SYSTEMD_CREDENTIALS_DIRECTORY_UNAVAILABLE"):
        SystemdCredentialProvider().load_bearer_token()


def test_insecure_directory_or_file_permissions_are_rejected(tmp_path):
    credential = secure_file(tmp_path / "geelark-agent-token")
    tmp_path.chmod(0o755)
    with pytest.raises(CredentialProviderError, match="DIRECTORY_PERMISSIONS_INVALID"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()

    tmp_path.chmod(0o700)
    credential.chmod(0o644)
    with pytest.raises(CredentialProviderError, match="FILE_PERMISSIONS_INVALID"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()


def test_symlink_credential_is_rejected(tmp_path):
    target = secure_file(tmp_path / "real-token")
    (tmp_path / "geelark-agent-token").symlink_to(target.name)
    with pytest.raises(CredentialProviderError, match="SYSTEMD_CREDENTIAL_UNAVAILABLE"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()


@pytest.mark.parametrize("content", [
    b"",
    b"short",
    b"a" * 63 + b" ",
    b"non-ascii-" + b"\xff" * 32,
])
def test_invalid_token_contents_are_rejected(tmp_path, content):
    secure_file(tmp_path / "geelark-agent-token", content, mode=0o400)
    with pytest.raises(CredentialProviderError, match="SYSTEMD_CREDENTIAL_FORMAT_INVALID"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()


def test_oversized_credential_is_rejected(tmp_path):
    secure_file(tmp_path / "geelark-agent-token", b"a" * 4097, mode=0o400)
    with pytest.raises(CredentialProviderError, match="SYSTEMD_CREDENTIAL_TOO_LARGE"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()


@pytest.mark.parametrize("name", ["", "../token", "a/b", ".", "..", "token name"])
def test_credential_name_must_be_a_simple_filename(name):
    with pytest.raises(ValueError):
        SystemdCredentialProvider(credential_name=name)


def test_non_regular_credential_file_is_rejected(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO solo está disponible en POSIX")
    fifo = tmp_path / "geelark-agent-token"
    os.mkfifo(fifo, 0o400)
    with pytest.raises(CredentialProviderError, match="SYSTEMD_CREDENTIAL_FILE_INVALID"):
        SystemdCredentialProvider(credentials_directory=tmp_path).load_bearer_token()
