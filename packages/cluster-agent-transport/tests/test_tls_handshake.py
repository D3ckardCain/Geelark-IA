import shutil
import socket
import subprocess
import threading
import time

import pytest
from fastapi import FastAPI

from cluster_agent_transport.client import AgentHTTPSClient, AgentTransportError
from cluster_agent_transport.server import make_uvicorn_config


@pytest.mark.skipif(shutil.which("openssl") is None, reason="requiere OpenSSL para generar CA temporales de prueba")
def test_real_tls_handshake_trusts_local_ca_and_rejects_untrusted_ca(tmp_path):
    ca_key, ca_cert = tmp_path / "ca.key", tmp_path / "ca.crt"
    other_ca_key, other_ca_cert = tmp_path / "other-ca.key", tmp_path / "other-ca.crt"
    server_key, server_csr, server_cert = tmp_path / "server.key", tmp_path / "server.csr", tmp_path / "server.crt"
    extensions = tmp_path / "server.ext"
    extensions.write_text(
        "basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n"
        "subjectAltName=IP:127.0.0.1\n"
    )

    commands = [
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(ca_key)],
        ["openssl", "req", "-x509", "-new", "-sha256", "-days", "1", "-key", str(ca_key),
         "-out", str(ca_cert), "-subj", "/CN=GeeLark-IA Test CA",
         "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign"],
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(other_ca_key)],
        ["openssl", "req", "-x509", "-new", "-sha256", "-days", "1", "-key", str(other_ca_key),
         "-out", str(other_ca_cert), "-subj", "/CN=GeeLark-IA Untrusted Test CA",
         "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign"],
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(server_key)],
        ["openssl", "req", "-new", "-sha256", "-key", str(server_key), "-out", str(server_csr),
         "-subj", "/CN=GeeLark-IA Test Server"],
        ["openssl", "x509", "-req", "-sha256", "-days", "1", "-in", str(server_csr),
         "-CA", str(ca_cert), "-CAkey", str(ca_key), "-CAcreateserial", "-out", str(server_cert),
         "-extfile", str(extensions)],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, text=True)

    app = FastAPI()

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    config = make_uvicorn_config(app, host="127.0.0.1", port=port, certfile=str(server_cert), keyfile=str(server_key))

    import uvicorn
    server = uvicorn.Server(config)
    thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
    thread.start()

    try:
        deadline = time.monotonic() + 5
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started, "Uvicorn HTTPS no llegó a iniciar en el socket local de prueba"

        trusted = AgentHTTPSClient(base_url=f"https://127.0.0.1:{port}", ca_cert=str(ca_cert))
        response = trusted.request("GET", "/healthz")
        assert response.status == 200
        assert response.body == b'{"ok":true}'

        untrusted = AgentHTTPSClient(base_url=f"https://127.0.0.1:{port}", ca_cert=str(other_ca_cert))
        with pytest.raises(AgentTransportError):
            untrusted.request("GET", "/healthz")
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
        assert not thread.is_alive(), "El servidor TLS temporal no terminó"


def test_client_rejects_http_and_non_private_controller_urls():
    with pytest.raises(ValueError):
        AgentHTTPSClient(base_url="http://127.0.0.1:8443", ca_cert="/missing/ca.crt")
    for address in ("8.8.8.8", "192.0.2.5", "169.254.1.1", "100.64.0.1", "2001:db8::1"):
        url_host = f"[{address}]" if ":" in address else address
        with pytest.raises(ValueError):
            AgentHTTPSClient(base_url=f"https://{url_host}:8443", ca_cert="/missing/ca.crt")
