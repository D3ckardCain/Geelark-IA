from __future__ import annotations

import json
import os
import ssl
from pathlib import Path
from urllib.error import URLError

import pytest

from cluster_agent_transport.client import AgentHTTPSClient, AgentTransportError
from cluster_agent_transport.network import is_private_lan_address


def ca_bundle() -> str:
    candidate = ssl.get_default_verify_paths().cafile
    if candidate and Path(candidate).is_file():
        return candidate
    pytest.skip("El runner no expone un bundle CA PEM en una ruta de archivo.")


def client(tmp_path: Path, **kwargs: object) -> AgentHTTPSClient:
    return AgentHTTPSClient(
        base_url="https://127.0.0.1:8765",
        ca_cert=ca_bundle(),
        **kwargs,
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8765",
        "https://controller.local:8765",
        "https://8.8.8.8:8765",
        "https://user@127.0.0.1:8765",
        "https://user:secret@127.0.0.1:8765",
        "https://127.0.0.1:8765/api",
        "https://127.0.0.1:8765/?token=x",
        "https://127.0.0.1:8765/#fragment",
        "https://0.0.0.0:8765",
    ],
)
def test_client_rejects_unsafe_base_urls(tmp_path: Path, url: str) -> None:
    with pytest.raises(ValueError):
        AgentHTTPSClient(base_url=url, ca_cert=ca_bundle())


def test_client_requires_existing_ca_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="certificado público"):
        AgentHTTPSClient(
            base_url="https://127.0.0.1:8765",
            ca_cert=str(tmp_path / "missing.pem"),
        )


@pytest.mark.parametrize("timeout", [0, -1, 60.1, float("nan"), float("inf"), True, "5"])
def test_client_rejects_invalid_timeouts(tmp_path: Path, timeout: object) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        client(tmp_path, timeout_seconds=timeout)


@pytest.mark.parametrize("limit", [0, -1, 16 * 1024 * 1024 + 1, True, 1.5])
def test_client_rejects_invalid_response_limits(tmp_path: Path, limit: object) -> None:
    with pytest.raises(ValueError, match="max_response_bytes"):
        client(tmp_path, max_response_bytes=limit)


def test_client_requires_private_ip_and_verified_tls(tmp_path: Path) -> None:
    instance = client(tmp_path)
    assert instance.ssl_context.verify_mode == ssl.CERT_REQUIRED
    assert instance.ssl_context.check_hostname is True
    assert instance.ssl_context.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert instance.base_url == "https://127.0.0.1:8765"


@pytest.mark.parametrize(
    "address,expected",
    [
        ("127.0.0.1", True),
        ("10.1.2.3", True),
        ("172.16.0.1", True),
        ("172.31.255.254", True),
        ("192.168.1.10", True),
        ("fc00::1", True),
        ("::1", True),
        ("172.32.0.1", False),
        ("100.64.0.1", False),
        ("169.254.1.1", False),
        ("2001:4860:4860::8888", False),
        ("::ffff:192.168.1.1", False),
    ],
)
def test_private_lan_classifier_is_explicit(address: str, expected: bool) -> None:
    import ipaddress

    assert is_private_lan_address(ipaddress.ip_address(address)) is expected


@pytest.mark.parametrize(
    "path",
    [
        "https://evil.example/path",
        "//evil.example/path",
        "/../admin",
        "/a/../admin",
        "/%2e%2e/admin",
        "/a/%2E%2E/admin",
        "/%252e%252e/admin",
        "/a/%255c..%255cadmin",
        "/admin#fragment",
        "relative/path",
    ],
)
def test_request_rejects_unsafe_paths_before_network(
    tmp_path: Path, path: str
) -> None:
    instance = client(tmp_path)
    with pytest.raises(ValueError, match="ruta debe ser local"):
        instance.request("GET", path)


def test_request_rejects_unsupported_methods(tmp_path: Path) -> None:
    instance = client(tmp_path)
    with pytest.raises(ValueError, match="Método HTTP"):
        instance.request("DELETE", "/admin/v1/status")


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Test": "ok\r\nInjected: yes"},
        {"Host": "evil.example"},
        {"content-length": "0"},
        {"Connection": "close"},
        {"Transfer-Encoding": "chunked"},
    ],
)
def test_request_rejects_unsafe_headers(
    tmp_path: Path, headers: dict[str, str]
) -> None:
    instance = client(tmp_path)
    with pytest.raises(ValueError, match="Cabecera HTTP|sobrescribir"):
        instance.request("GET", "/status", headers=headers)


def test_request_rejects_non_finite_json_and_large_body(tmp_path: Path) -> None:
    instance = client(tmp_path)
    with pytest.raises(ValueError):
        instance.request("POST", "/status", payload={"value": float("nan")})
    with pytest.raises(ValueError, match="excede 1 MiB"):
        instance.request("POST", "/status", payload={"value": "x" * (1024 * 1024)})


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json"):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return self.body[:size]

    def close(self) -> None:
        self.closed = True


class FakeOpener:
    def __init__(self, response: FakeResponse | Exception):
        self.response = response
        self.request = None

    def open(self, request, timeout: float):
        self.request = request
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_request_returns_bounded_response_and_closes_stream(tmp_path: Path) -> None:
    instance = client(tmp_path, max_response_bytes=32)
    response = FakeResponse(b'{"ok":true}')
    opener = FakeOpener(response)
    instance._opener = opener
    result = instance.request("GET", "/admin/v1/status")
    assert result.status == 200
    assert result.body == b'{"ok":true}'
    assert result.content_type == "application/json"
    assert response.closed is True
    assert opener.request.get_method() == "GET"


def test_request_rejects_oversized_response_and_closes_stream(tmp_path: Path) -> None:
    instance = client(tmp_path, max_response_bytes=4)
    response = FakeResponse(b"12345")
    instance._opener = FakeOpener(response)
    with pytest.raises(AgentTransportError, match="excede el límite"):
        instance.request("GET", "/status")
    assert response.closed is True


def test_request_never_follows_redirects(tmp_path: Path) -> None:
    instance = client(tmp_path)
    response = FakeResponse(b"", status=302)
    instance._opener = FakeOpener(response)
    with pytest.raises(AgentTransportError, match="redirigir"):
        instance.request("GET", "/status")
    assert response.closed is True


def test_transport_errors_do_not_leak_underlying_details(tmp_path: Path) -> None:
    instance = client(tmp_path)
    instance._opener = FakeOpener(URLError("private network detail"))
    with pytest.raises(AgentTransportError, match="Falló la conexión HTTPS verificada") as exc:
        instance.request("GET", "/status")
    assert "private network detail" not in str(exc.value)


def test_request_encodes_json_without_nonstandard_values(tmp_path: Path) -> None:
    instance = client(tmp_path)
    response = FakeResponse(b"{}", content_type="application/json")
    opener = FakeOpener(response)
    instance._opener = opener
    result = instance.request("POST", "/admin/v1/status", payload={"name": "worker"})
    assert result.status == 200
    assert opener.request.get_header("Content-type") == "application/json"
    assert json.loads(opener.request.data.decode("utf-8")) == {"name": "worker"}


@pytest.mark.skipif(os.name != "posix", reason="La prueba de modos POSIX no aplica en Windows.")
@pytest.mark.parametrize("unsafe_target", ["file", "directory"])
def test_client_rejects_mutable_ca_trust_path(
    tmp_path: Path, unsafe_target: str
) -> None:
    ca_dir = tmp_path / "ca-store"
    ca_dir.mkdir()
    ca_file = ca_dir / "root.crt"
    ca_file.write_text("not a certificate; permissions must be checked first", encoding="utf-8")
    ca_file.chmod(0o644)
    if unsafe_target == "file":
        ca_file.chmod(0o666)
    else:
        ca_dir.chmod(0o777)
    with pytest.raises(ValueError, match="archivo CA|directorio contenedor"):
        AgentHTTPSClient(
            base_url="https://127.0.0.1:8765",
            ca_cert=str(ca_file),
        )
