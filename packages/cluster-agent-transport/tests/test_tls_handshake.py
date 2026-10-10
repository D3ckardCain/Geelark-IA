import http.client
import shutil
import socket
import ssl
import subprocess
import threading
import time

import pytest
from fastapi import FastAPI

from cluster_agent_transport.server import make_uvicorn_config


@pytest.mark.skipif(shutil.which("openssl") is None, reason="requiere OpenSSL para generar una CA temporal de prueba")
def test_real_tls_handshake_trusts_local_ca_and_rejects_untrusted_ca(tmp_path):
    ca_key = tmp_path / "ca.key"
    ca_cert = tmp_path / "ca.crt"
    server_key = tmp_path / "server.key"
    server_csr = tmp_path / "server.csr"
    server_cert = tmp_path / "server.crt"
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

    config = make_uvicorn_config(
        app, host="127.0.0.1", port=port,
        certfile=str(server_cert), keyfile=str(server_key),
    )
    import uvicorn
    server = uvicorn.Server(config)
    thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
    thread.start()

    try:
        deadline = time.monotonic() + 5
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started, "Uvicorn HTTPS no llegó a iniciar en el socket local de prueba"

        trusted = ssl.create_default_context(cafile=str(ca_cert))
        connection = http.client.HTTPSConnection("127.0.0.1", port, context=trusted, timeout=3)
        connection.request("GET", "/healthz")
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == b'{"ok":true}'
        connection.close()

        untrusted = ssl.create_default_context()
        connection = http.client.HTTPSConnection("127.0.0.1", port, context=untrusted, timeout=3)
        with pytest.raises(ssl.SSLCertVerificationError):
            connection.request("GET", "/healthz")
        connection.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
        assert not thread.is_alive(), "El servidor TLS temporal no terminó"
