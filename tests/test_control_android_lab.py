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

    def test_recovery_targets_only_lab_and_redacts_password(self):
        emit = Mock()
        c = control.Controller(emit)
        result = Mock(returncode=0, stdout='android-lab-01\n')
        with patch.object(c, 'ssh', return_value=['ssh']), patch.object(c, 'run'), patch.object(c, 'require', return_value='adb'), patch.object(c, 'android_status', return_value='1\nService input: found\nService activity: found'), patch.object(control.subprocess, 'run', return_value=result) as run:
            c.recover('secret-test')
            args, kwargs = run.call_args
            self.assertEqual(args[0][-1], "sudo -S -p '' docker restart android-lab-01")
            self.assertEqual(kwargs['input'], 'secret-test\n')
            self.assertNotIn('secret-test', str(emit.call_args_list))

    def test_rejected_sudo_does_not_retry_restart(self):
        c = control.Controller(Mock())
        with patch.object(c, 'ssh', return_value=['ssh']), patch.object(control.subprocess, 'run', return_value=Mock(returncode=1, stdout='rechazado')) as run:
            with self.assertRaisesRegex(RuntimeError, 'No se pudo reiniciar'):
                c.recover('secret-test')
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
