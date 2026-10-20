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


if __name__ == "__main__":
    unittest.main()
