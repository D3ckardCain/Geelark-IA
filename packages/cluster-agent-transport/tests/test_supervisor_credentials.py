import os
import sys
import types
from uuid import uuid4

import cluster_agent_transport.supervisor as supervisor

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



def test_read_token_rejects_group_or_world_writable_parent_directory(tmp_path):
    unsafe_dir = tmp_path / "unsafe"
    unsafe_dir.mkdir()
    unsafe_dir.chmod(0o777)
    token_file = unsafe_dir / "node-token"
    token_file.write_text("b" * 64, encoding="ascii")
    token_file.chmod(0o600)

    with pytest.raises(ValueError, match="directorio padre"):
        _read_token(token_file)


def test_read_token_rejects_symlinked_parent_directory(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    real_dir.chmod(0o700)
    token_file = real_dir / "node-token"
    token_file.write_text("c" * 64, encoding="ascii")
    token_file.chmod(0o600)
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="directorios padre"):
        _read_token(linked_dir / "node-token")


def test_load_supervisor_supports_systemd_credentials_without_credential_file(monkeypatch, tmp_path):
    token = "d" * 64
    provider_instances = []

    class FakeSystemdProvider:
        def __init__(self, *, credential_name, credentials_directory=None):
            self.credential_name = credential_name
            self.credentials_directory = credentials_directory
            provider_instances.append(self)

        def load_bearer_token(self):
            return token

    class FakeClient:
        def __init__(self, *, base_url, ca_cert, timeout_seconds):
            self.base_url = base_url
            self.ca_cert = ca_cert
            self.timeout_seconds = timeout_seconds

    class FakeJournal:
        def __init__(self, path, node_id):
            self.path = path
            self.node_id = node_id

        def initialize(self):
            pass

        def record_result(self, **_kwargs):
            pass

        def record_result(self, **_kwargs):
            pass

    guard_module = types.ModuleType("geelark_cluster_agent_guard")
    guard_module.AgentJournal = FakeJournal
    monkeypatch.setitem(sys.modules, "geelark_cluster_agent_guard", guard_module)
    monkeypatch.setattr(supervisor, "AgentHTTPSClient", FakeClient)
    monkeypatch.setattr(supervisor, "SystemdCredentialProvider", FakeSystemdProvider)

    ca_file = tmp_path / "ca.pem"
    ca_file.write_text("test CA")
    config = tmp_path / "agent.toml"
    config.write_text(
        f'node_id = "{uuid4()}"\n'
        f'controller_url = "https://127.0.0.1:8443"\n'
        f'ca_cert = "{ca_file}"\n'
        f'journal_path = "{tmp_path / "journal.sqlite"}"\n'
        'agent_version = "0.1.0"\n'
        'capabilities = ["heartbeat", "status"]\n'
        'credential_provider = "systemd"\n'
        'systemd_credential_name = "test-agent-token"\n',
        encoding="utf-8",
    )

    instance = supervisor.load_supervisor(config)
    assert provider_instances[0].credential_name == "test-agent-token"
    assert provider_instances[0].credentials_directory is None
    assert instance.runtime._bearer_token == token
    assert instance._thread is None
