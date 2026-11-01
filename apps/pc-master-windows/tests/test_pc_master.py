import importlib.util
import sys
import unittest
from unittest import mock
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "pc_master.py"
spec = importlib.util.spec_from_file_location("pc_master", APP)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DsnSafetyTests(unittest.TestCase):
    def test_accepts_passwordless_local_dsn(self):
        self.assertTrue(module._safe_dsn("postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable"))

    def test_rejects_password_in_uri(self):
        self.assertFalse(module._safe_dsn("postgresql://reader:secret@localhost:5432/geelark"))

    def test_rejects_password_keyword(self):
        self.assertFalse(module._safe_dsn("host=localhost user=reader password=secret dbname=geelark"))

    def test_rejects_empty_dsn(self):
        self.assertFalse(module._safe_dsn("   "))




# PC_MASTER_REGRESSION_TESTS_20261014
import tempfile


class _FakeStatus:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class _FakeStdin:
    def __init__(self):
        self.data = []
        self.closed = False

    def write(self, value):
        self.data.append(value)

    def flush(self):
        pass

    def close(self):
        self.closed = True


class _FakeProcess:
    def __init__(self):
        self.pid = 45678
        self.terminated = False
        self.killed = False
        self.returncode = None
        self.stdin = _FakeStdin()
        self.wait_behaviors = []

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.wait_behaviors:
            behavior = self.wait_behaviors.pop(0)
            if isinstance(behavior, BaseException):
                raise behavior
        self.returncode = 0
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.killed = True
        self.returncode = -9


def _bare_app(process):
    app = module.PcMasterApp.__new__(module.PcMasterApp)
    app.process = process
    app.status_var = _FakeStatus()
    return app


class PcMasterStopRegressionTests(unittest.TestCase):
    @mock.patch.object(module.sys, "platform", "win32")
    @mock.patch.object(module.subprocess, "run")
    @mock.patch.object(module.messagebox, "showwarning")
    def test_windows_stop_success_is_graceful(self, showwarning, run):
        process = _FakeProcess()
        app = _bare_app(process)

        self.assertTrue(app._stop_panel())

        self.assertIsNone(app.process)
        self.assertEqual(app.status_var.value, "Detenido")
        self.assertEqual(process.stdin.data, ["STOP\n"])
        self.assertTrue(process.stdin.closed)
        run.assert_not_called()
        showwarning.assert_not_called()

    @mock.patch.object(module.sys, "platform", "win32")
    @mock.patch.object(module.subprocess, "run")
    @mock.patch.object(module.messagebox, "showwarning")
    def test_windows_taskkill_failure_preserves_process(
        self, showwarning, run
    ):
        process = _FakeProcess()
        process.wait_behaviors = [
            module.subprocess.TimeoutExpired("runtime", 8),
            module.subprocess.TimeoutExpired("runtime", 5),
        ]
        app = _bare_app(process)
        run.return_value = mock.Mock(returncode=1)

        self.assertFalse(app._stop_panel())

        self.assertIs(app.process, process)
        self.assertEqual(
            app.status_var.value, "Parada no confirmada; comprueba el puerto"
        )
        showwarning.assert_called_once()
        args = run.call_args.args[0]
        self.assertIn("/T", args)
        self.assertIn("/F", args)

    @mock.patch.object(module.sys, "platform", "win32")
    @mock.patch.object(module.subprocess, "run")
    @mock.patch.object(module.messagebox, "showerror")
    def test_windows_taskkill_os_error_preserves_process(
        self, showerror, run
    ):
        process = _FakeProcess()
        process.wait_behaviors = [
            module.subprocess.TimeoutExpired("runtime", 8)
        ]
        app = _bare_app(process)
        run.side_effect = OSError("simulated failure")

        self.assertFalse(app._stop_panel())

        self.assertIs(app.process, process)
        self.assertEqual(
            app.status_var.value, "Error al detener; comprueba el puerto"
        )
        showerror.assert_called_once()

    @mock.patch.object(module.sys, "platform", "linux")
    @mock.patch.object(module.subprocess, "run")
    def test_non_windows_stop_uses_control_pipe(self, run):
        process = _FakeProcess()
        app = _bare_app(process)

        self.assertTrue(app._stop_panel())

        self.assertEqual(process.stdin.data, ["STOP\n"])
        self.assertTrue(process.stdin.closed)
        self.assertFalse(process.terminated)
        self.assertFalse(process.killed)
        self.assertIsNone(app.process)
        self.assertEqual(app.status_var.value, "Detenido")
        run.assert_not_called()


class PcMasterCloseRegressionTests(unittest.TestCase):
    @mock.patch.object(module.PcMasterApp, "destroy")
    @mock.patch.object(module.messagebox, "askyesno", return_value=True)
    def test_window_stays_open_when_stop_is_not_confirmed(
        self, askyesno, destroy
    ):
        process = _FakeProcess()
        app = _bare_app(process)
        app._stop_panel = mock.Mock(return_value=False)

        app._on_close()

        askyesno.assert_called_once()
        app._stop_panel.assert_called_once()
        destroy.assert_not_called()


class PcMasterRuntimeLogRegressionTests(unittest.TestCase):
    @mock.patch.object(module.sys, "platform", "win32")
    @mock.patch.object(module.sys, "executable", str(Path("/runtime/pythonw.exe")))
    def test_start_appends_runtime_log_and_redirects_backend_output(self):
        process = _FakeProcess()
        settings = {
            "operator_auth_file": "operator-auth.json",
            "state_dir": "state",
            "database_url": "postgresql://reader@localhost/geelark",
            "tls_cert": "server.crt",
            "tls_key": "server.key",
            "pgpassfile": "pgpass.conf",
            "port": "18765",
        }
        app = _bare_app(None)
        app._current_settings = mock.Mock(return_value=settings)
        app._save_settings = mock.Mock(return_value=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            log_path = config_dir / "runtime.log"
            log_path.write_text("REGISTRO ANTERIOR\n", encoding="utf-8")

            with (
                mock.patch.object(module, "CONFIG_DIR", config_dir),
                mock.patch.object(module, "validate_settings", return_value=[]),
                mock.patch.object(
                    module.subprocess, "Popen", return_value=process
                ) as popen,
                mock.patch.object(module.threading, "Thread") as thread,
            ):
                app._start_panel()

            contents = log_path.read_text(encoding="utf-8")
            self.assertIn("REGISTRO ANTERIOR", contents)
            self.assertIn(
                "===== INICIO PC-MASTER BACKEND =====", contents
            )

            self.assertEqual(popen.call_args.args[0], [str(Path(module.sys.executable).with_name("python.exe")), "-m", "geelark_master_admin.runtime"])
            self.assertIn("creationflags", popen.call_args.kwargs)
            kwargs = popen.call_args.kwargs
            self.assertEqual(kwargs["stdout"].name, str(log_path))
            self.assertIs(kwargs["stderr"], module.subprocess.STDOUT)
            self.assertEqual(
                kwargs["env"]["GEELARK_ADMIN_BIND_HOST"], "127.0.0.1"
            )
            self.assertEqual(
                kwargs["env"]["GEELARK_ADMIN_PORT"], "18765"
            )
            self.assertEqual(kwargs["env"]["PGPASSFILE"], "pgpass.conf")
            thread.return_value.start.assert_called_once()
            self.assertIs(app.process, process)


class PcMasterSingleInstanceTests(unittest.TestCase):
    @mock.patch.object(module.sys, "platform", "linux")
    def test_non_windows_does_not_create_global_mutex(self):
        self.assertIsNone(module._acquire_single_instance_mutex())

    @mock.patch.object(module.sys, "platform", "win32")
    def test_windows_acquires_named_mutex(self):
        import ctypes

        kernel32 = mock.Mock()
        kernel32.CreateMutexW.return_value = 123
        kernel32.GetLastError.return_value = 0
        with mock.patch.object(ctypes, "windll", mock.Mock(kernel32=kernel32), create=True):
            lock = module._acquire_single_instance_mutex()
        self.assertEqual(lock, (kernel32, 123))
        kernel32.CreateMutexW.assert_called_once_with(
            None, True, "Local\\GeeLarkIA_PC_MASTER_SINGLE_INSTANCE"
        )

    @mock.patch.object(module.sys, "platform", "win32")
    def test_windows_duplicate_closes_new_handle_and_refuses_second_instance(self):
        import ctypes

        kernel32 = mock.Mock()
        kernel32.CreateMutexW.return_value = 456
        kernel32.GetLastError.return_value = 183
        with mock.patch.object(ctypes, "windll", mock.Mock(kernel32=kernel32), create=True):
            with self.assertRaisesRegex(RuntimeError, "ya está abierto"):
                module._acquire_single_instance_mutex()
        kernel32.CloseHandle.assert_called_once_with(456)

    def test_release_mutex_releases_ownership_and_handle(self):
        kernel32 = mock.Mock()
        module._release_single_instance_mutex((kernel32, 789))
        kernel32.ReleaseMutex.assert_called_once_with(789)
        kernel32.CloseHandle.assert_called_once_with(789)


class PanelWindowTests(unittest.TestCase):
    @mock.patch.object(module.sys, "platform", "win32")
    @mock.patch.object(module, "_panel_window_action")
    @mock.patch.object(module, "_panel_browser_executable", return_value=Path("browser.exe"))
    @mock.patch.object(module.subprocess, "Popen")
    def test_open_reuses_owned_process_and_separates_personal_profile(self, popen, executable, window_action):
        app = _bare_app(None)
        browser = _FakeProcess()
        popen.return_value = browser
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(module, "CONFIG_DIR", Path(folder)):
            self.assertTrue(app._open_panel_window(8765))
            self.assertTrue(app._open_panel_window(8765))
            popen.assert_called_once()
            args = popen.call_args.args[0]
            self.assertIn("--app=https://localhost:8765/", args)
            self.assertIn("--user-data-dir="+str(Path(folder)/"panel-browser"), args)
            self.assertFalse(any("ignore-certificate" in arg or "remote-debugging" in arg for arg in args))
            window_action.assert_called_once_with(browser.pid, close=False)

    @mock.patch.object(module, "_panel_window_action")
    @mock.patch.object(module.subprocess, "run")
    def test_confirmed_stop_closes_only_tracked_browser(self, run, window_action):
        app = _bare_app(None)
        app.browser_process = browser = _FakeProcess()
        self.assertTrue(app._stop_panel())
        window_action.assert_called_once_with(browser.pid, close=True)
        run.assert_not_called()
        self.assertIsNone(app.browser_process)

    def test_failed_backend_stop_does_not_close_browser(self):
        app = _bare_app(None)
        app._stop_backend = mock.Mock(return_value=False)
        app._close_panel_window = mock.Mock()
        self.assertFalse(app._stop_panel())
        app._close_panel_window.assert_not_called()

    @mock.patch.object(module, "_panel_window_action")
    @mock.patch.object(module.subprocess, "run")
    def test_browser_fallback_is_pid_scoped(self, run, window_action):
        app = _bare_app(None)
        app.browser_process = browser = _FakeProcess()
        browser.wait_behaviors = [module.subprocess.TimeoutExpired("browser", 4)]
        self.assertTrue(app._close_panel_window())
        args = run.call_args.args[0]
        self.assertEqual(args[1:], ["/PID", str(browser.pid), "/T", "/F"])
        self.assertNotIn("/IM", args)

    @mock.patch.object(module, "_panel_window_action")
    @mock.patch.object(module.subprocess, "run")
    def test_untracked_browser_is_never_closed(self, run, window_action):
        self.assertTrue(_bare_app(None)._close_panel_window())
        run.assert_not_called()
        window_action.assert_not_called()


if __name__ == "__main__":
    unittest.main()

