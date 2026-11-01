"""Prueba Windows real: cerrar ventana administrada conserva otro navegador."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(sys.platform != 'win32', reason='Navegador nativo Windows')
def test_owned_panel_stop_preserves_another_browser(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('owned_panel_launcher', Path(__file__).parents[1]/'pc_master.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        executable = module._panel_browser_executable()
    except FileNotFoundError:
        pytest.skip('Edge/Chrome no instalado en este runner')
    monkeypatch.setattr(module, 'CONFIG_DIR', tmp_path/'master')
    app = module.PcMasterApp.__new__(module.PcMasterApp)
    app.process = None
    class Status:
        def set(self, value): pass
    app.status_var = Status()
    other = subprocess.Popen([str(executable), '--app=about:blank', f'--user-data-dir={tmp_path / "other-browser"}',
                              '--no-first-run', '--no-default-browser-check', '--disable-background-mode'],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    def cleanup(process):
        if process is not None and process.poll() is None:
            subprocess.run([str(Path(os.environ.get('SystemRoot', r'C:\Windows'))/'System32/taskkill.exe'),
                            '/PID', str(process.pid), '/T', '/F'], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                           creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            process.wait(timeout=5)
    try:
        assert app._open_panel_window(18765)
        panel = app.browser_process
        deadline = time.monotonic()+3
        while time.monotonic()<deadline and panel.poll() is None and other.poll() is None:
            time.sleep(.1)
        assert panel.poll() is None, 'El navegador no mantuvo un proceso propio para el panel'
        assert other.poll() is None
        assert app._open_panel_window(18765)
        assert app.browser_process is panel
        assert app._stop_panel()
        assert panel.poll() is not None
        assert other.poll() is None, 'Se cerró otro navegador ajeno al panel'
    finally:
        cleanup(app.__dict__.get('browser_process'))
        cleanup(other)
