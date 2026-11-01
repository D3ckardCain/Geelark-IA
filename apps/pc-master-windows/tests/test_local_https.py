"""Validación del certificado local antes de confiarlo al usuario Windows."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock

import pytest
import geelark_master_admin.auth as auth


def load():
    spec = importlib.util.spec_from_file_location('https_launcher', Path(__file__).parents[1]/'pc_master.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def certificate(module, folder, ca='FALSE', host='localhost'):
    executable = shutil.which('openssl')
    if not executable:
        candidate = Path(module.os.environ.get('ProgramFiles', r'C:\Program Files'))/'Git/usr/bin/openssl.exe'
        if not candidate.is_file():
            pytest.skip('OpenSSL no instalado')
        executable = str(candidate)
    cert, key = folder/'cert.crt', folder/'cert.key'
    subprocess.run([executable, 'req', '-x509', '-newkey', 'rsa:2048', '-sha256', '-days', '1', '-nodes',
                    '-subj', '/CN='+host, '-addext', f'subjectAltName=DNS:{host},IP:127.0.0.1',
                    '-addext', 'basicConstraints=critical,CA:'+ca, '-addext', 'extendedKeyUsage=serverAuth',
                    '-keyout', str(key), '-out', str(cert)], check=True, capture_output=True,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return {'tls_cert':str(cert), 'tls_key':str(key)}


def test_server_certificate_is_preserved_and_validated_before_trust(tmp_path, monkeypatch):
    module = load()
    settings = certificate(module, tmp_path)
    before = Path(settings['tls_cert']).read_bytes()
    trust = Mock()
    monkeypatch.setattr(module, '_local_certificate_trust', trust)
    result = module._prepare_panel_https(settings)
    assert result == settings
    assert Path(result['tls_cert']).read_bytes() == before
    trust.assert_called_once_with(Path(settings['tls_cert']))


def test_wrong_hostname_is_never_trusted(tmp_path, monkeypatch):
    module = load()
    settings = certificate(module, tmp_path, host='other.invalid')
    trust = Mock()
    monkeypatch.setattr(module, '_local_certificate_trust', trust)
    with pytest.raises(subprocess.CalledProcessError):
        module._prepare_panel_https(settings)
    trust.assert_not_called()


def test_old_ca_is_replaced_by_a_server_only_certificate(tmp_path, monkeypatch):
    module = load()
    settings = certificate(module, tmp_path, ca='TRUE')
    original = Path(settings['tls_cert']).read_bytes()
    monkeypatch.setattr(module, 'CONFIG_DIR', tmp_path/'private')
    monkeypatch.setattr(auth, '_restrict_windows_acl', lambda *_args, **_kwargs: None)
    trusted = Mock()
    monkeypatch.setattr(module, '_local_certificate_trust', trusted)
    result = module._prepare_panel_https(settings)
    assert result != settings
    assert Path(settings['tls_cert']).read_bytes() == original
    assert Path(result['tls_key']).is_file()
    trusted.assert_called_once_with(Path(result['tls_cert']))
    # Segundo arranque valida y reutiliza el certificado generado.
    assert module._prepare_panel_https(result) == result


@pytest.mark.skipif(__import__('sys').platform != 'win32', reason='Almacén TLS Windows')
def test_windows_trust_and_real_https_without_browser_bypass(tmp_path, monkeypatch):
    import hashlib
    import http.server
    import os
    import socket
    import ssl
    import threading
    import ctypes
    from ctypes import wintypes

    module = load()
    settings = certificate(module, tmp_path)
    thumbprint = hashlib.sha1(ssl.PEM_cert_to_DER_cert(Path(settings['tls_cert']).read_text())).hexdigest().upper()
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    server = None
    browser = None
    # La importación de Root pide confirmación nativa. Aceptar en esta prueba
    # solo el diálogo del PowerShell creado aquí y con la huella de su certificado.
    owned_powershell = set()
    original_popen = subprocess.Popen
    def tracked_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        command = args[0] if args else kwargs.get('args', [])
        if command and str(command[0]).lower() == str(powershell).lower() and kwargs.get('env', {}).get('GEELARK_LOCAL_CERT_THUMBPRINT') == thumbprint:
            owned_powershell.add(process.pid)
        return process
    monkeypatch.setattr(subprocess, 'Popen', tracked_popen)
    done = threading.Event()
    approved = []
    def confirm_fixture():
        user32 = ctypes.windll.user32
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows.argtypes = [callback, wintypes.LPARAM]
        user32.EnumChildWindows.argtypes = [wintypes.HWND, callback, wintypes.LPARAM]
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetDlgItem.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetDlgItem.restype = wintypes.HWND
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        @callback
        def inspect(window, _):
            owner = wintypes.DWORD()
            user32.GetWindowThreadProcessId(window, ctypes.byref(owner))
            if owner.value not in owned_powershell:
                return True
            text = []
            @callback
            def child(handle, _):
                length = user32.GetWindowTextLengthW(handle)
                value = ctypes.create_unicode_buffer(length+1)
                user32.GetWindowTextW(handle, value, length+1)
                text.append(value.value)
                return True
            user32.EnumChildWindows(window, child, 0)
            import re
            normalized = re.sub('[^0-9A-F]', '', ' '.join(text).upper())
            if thumbprint in normalized:
                yes = user32.GetDlgItem(window, 6)  # IDYES
                if yes:
                    approved.append(thumbprint)
                    user32.PostMessageW(yes, 0x00F5, 0, 0)  # BM_CLICK
            return True
        while not done.wait(.1):
            user32.EnumWindows(inspect, 0)
    confirmer = threading.Thread(target=confirm_fixture, daemon=True)
    confirmer.start()
    try:
        assert module._prepare_panel_https(settings) == settings
        assert module._prepare_panel_https(settings) == settings
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<html><body>PCMASTER_TLS_OK</body></html>')
            def log_message(self, *_args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(settings['tls_cert'], settings['tls_key'])
        server.socket = context.wrap_socket(server.socket, server_side=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        with socket.create_connection(('127.0.0.1', port), timeout=5) as plain:
            with ssl.create_default_context().wrap_socket(plain, server_hostname='localhost') as secured:
                assert secured.getpeercert()['subjectAltName']
        executable = module._panel_browser_executable()
        browser = subprocess.Popen([str(executable), '--headless=new', '--disable-gpu', '--guest',
                                    '--no-first-run', f'--user-data-dir={tmp_path / "tls-browser"}',
                                    '--dump-dom', f'https://localhost:{port}/'],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        output, _ = browser.communicate(timeout=25)
        assert b'PCMASTER_TLS_OK' in output, output[-1500:]
    finally:
        done.set()
        confirmer.join(timeout=2)
        if server:
            server.shutdown()
            server.server_close()
        if browser is not None and browser.poll() is None:
            subprocess.run([str(Path(os.environ.get('SystemRoot', r'C:\Windows'))/'System32/taskkill.exe'),
                            '/PID', str(browser.pid), '/T', '/F'], capture_output=True, timeout=10,
                           creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        # Retirar solo el certificado generado para esta prueba.
        subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-Command',
                        f"Remove-Item -LiteralPath 'Cert:\\CurrentUser\\Root\\{thumbprint}' -ErrorAction SilentlyContinue"],
                       capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
