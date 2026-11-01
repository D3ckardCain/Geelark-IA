import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('control', Path(__file__).parents[1] / 'tools/control_android_lab.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class Checks(unittest.TestCase):
    def test_boot_flag_alone_is_not_health(self):
        self.assertFalse(control.healthy('1\nService input: not found\nService activity: not found'))

    def test_both_services_required(self):
        self.assertFalse(control.healthy('1\nService input: found'))
        self.assertTrue(control.healthy('1\r\nService input: found\r\nService activity: found\r\n'))

    def test_unhealthy_android_does_not_start_scrcpy(self):
        c = control.Controller(Mock())
        with patch.object(c, 'android_status', return_value='1'), patch.object(control.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError, 'no está operativo'):
                c.open_screen()
            popen.assert_not_called()

    def test_close_only_owned_processes(self):
        c = control.Controller(Mock())
        own = Mock()
        own.poll.return_value = None
        c.tunnel = own
        with patch.object(control.subprocess, 'run') as run:
            c.close()
            own.terminate.assert_called_once()
            run.assert_not_called()

    def test_busy_port_does_not_launch_ssh(self):
        c = control.Controller(Mock())
        with patch.object(control.socket, 'socket') as sock, patch.object(control.subprocess, 'Popen') as popen:
            sock.return_value.__enter__.return_value.bind.side_effect = OSError('ocupado')
            with self.assertRaisesRegex(RuntimeError, 'ocupado'):
                c.start_tunnel()
            popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
