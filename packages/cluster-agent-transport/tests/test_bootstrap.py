from uuid import uuid4

import pytest

import cluster_agent_transport.bootstrap as bootstrap
from cluster_agent_transport.bootstrap import build_agent_components


TOKEN = "c" * 64


class FakeCredentialProvider:
    def __init__(self, token=TOKEN):
        self.token = token
        self.calls = 0

    def load_bearer_token(self):
        self.calls += 1
        return self.token


class FakeJournal:
    def record_result(self, **_kwargs):
        pass


class FakeHTTPSClient:
    def __init__(self, *, base_url, ca_cert, timeout_seconds):
        self.base_url = base_url
        self.ca_cert = ca_cert
        self.timeout_seconds = timeout_seconds


def metrics():
    return {
        "cpu_load_percent": 12.5,
        "memory_total_bytes": 1000,
        "memory_available_bytes": 400,
        "storage_available_bytes": 5000,
    }


def test_factory_wires_tls_runtime_receipt_lifecycle_and_supervisor_without_starting(monkeypatch):
    monkeypatch.setattr(bootstrap, "AgentHTTPSClient", FakeHTTPSClient)
    provider = FakeCredentialProvider()
    node_id = uuid4()

    components = build_agent_components(
        base_url="https://127.0.0.1:8443",
        ca_cert="/tmp/test-ca.crt",
        credential_provider=provider,
        journal=FakeJournal(),
        local_node_id=node_id,
        agent_version="0.1.0",
        capabilities=["heartbeat", "status"],
        request_timeout_seconds=2,
        receipt_batch_size=7,
        heartbeat_interval_seconds=1.5,
        capabilities_interval_seconds=2.0,
        status_interval_seconds=3.0,
        metrics_provider=metrics,
    )

    assert provider.calls == 1
    assert components.client.base_url == "https://127.0.0.1:8443"
    assert components.client.ca_cert == "/tmp/test-ca.crt"
    assert components.client.timeout_seconds == 2
    assert components.runtime.client is components.client
    assert components.runtime.local_node_id == node_id
    assert components.receipt_lifecycle.runtime is components.runtime
    assert components.receipt_lifecycle.batch_size == 7
    assert components.supervisor.runtime is components.runtime
    assert components.supervisor.receipt_sync is components.receipt_lifecycle
    assert components.supervisor._thread is None
    assert not components.receipt_lifecycle.running


def test_factory_rejects_invalid_bearer_token_without_logging_it(monkeypatch):
    monkeypatch.setattr(bootstrap, "AgentHTTPSClient", FakeHTTPSClient)
    provider = FakeCredentialProvider("secret-not-valid")
    with pytest.raises(ValueError, match="credencial bearer"):
        build_agent_components(
            base_url="https://127.0.0.1:8443",
            ca_cert="/tmp/test-ca.crt",
            credential_provider=provider,
            journal=FakeJournal(),
            local_node_id=uuid4(),
            agent_version="0.1.0",
            capabilities=["heartbeat"],
        )
    assert provider.calls == 1


def test_factory_requires_credential_provider_contract(monkeypatch):
    monkeypatch.setattr(bootstrap, "AgentHTTPSClient", FakeHTTPSClient)
    with pytest.raises(ValueError, match="credential_provider"):
        build_agent_components(
            base_url="https://127.0.0.1:8443",
            ca_cert="/tmp/test-ca.crt",
            credential_provider=object(),
            journal=FakeJournal(),
            local_node_id=uuid4(),
            agent_version="0.1.0",
            capabilities=["heartbeat"],
        )
