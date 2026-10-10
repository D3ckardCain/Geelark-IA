import pytest

from cluster_agent_transport.limits import InMemoryRateLimiter
from cluster_agent_transport.server import TransportConfigurationError, validate_https_listener


def test_rate_limiter_rejects_after_configured_window_quota():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)
    assert limiter.allow("node-a", now=1)
    assert limiter.allow("node-a", now=2)
    assert not limiter.allow("node-a", now=3)
    assert limiter.allow("node-a", now=12)
    assert limiter.allow("node-b", now=3)


@pytest.mark.parametrize("host", ["0.0.0.0", "192.0.2.5", "example.invalid", "::"])
def test_listener_rejects_unspecified_public_or_nonliteral_hosts(host, tmp_path):
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert.write_text("cert")
    key.write_text("key")
    with pytest.raises(TransportConfigurationError):
        validate_https_listener(host=host, port=8443, certfile=str(cert), keyfile=str(key))


def test_listener_requires_tls_files_and_private_ip(tmp_path):
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert.write_text("cert")
    key.write_text("key")
    validate_https_listener(host="127.0.0.1", port=8443, certfile=str(cert), keyfile=str(key))
    with pytest.raises(TransportConfigurationError):
        validate_https_listener(host="127.0.0.1", port=80, certfile=str(cert), keyfile=str(tmp_path / "missing.pem"))
