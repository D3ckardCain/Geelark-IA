import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from geelark_master_admin.android_process import Controller


def controller():
    c = Controller(SimpleNamespace(serial='127.0.0.1:15557'), Mock())
    c.start_tunnel = Mock()
    c.require = Mock(return_value='adb')
    return c


def test_offline_transport_reconnects_once_without_restart():
    c = controller()
    c.run = Mock(side_effect=['already connected', subprocess.TimeoutExpired('adb',8),
                             'disconnected', 'connected', '', 'device\n',
                             '1\nService input: found\nService activity: found'])
    assert 'Service input: found' in c.android_status()
    commands = [call.args[0] for call in c.run.call_args_list]
    assert commands.count(['adb','disconnect',c.config.serial]) == 1
    assert commands.count(['adb','connect',c.config.serial]) == 2
    assert all('kill-server' not in cmd and 'restart' not in cmd for cmd in commands)


def test_repeated_failure_stops_after_one_retry():
    c = controller()
    c.run = Mock(side_effect=['connected', RuntimeError('offline'), 'disconnected',
                             'connected', RuntimeError('offline')])
    with pytest.raises(RuntimeError, match='offline'):
        c.android_status()
    assert c.run.call_count == 5


def test_close_unregisters_only_own_serial():
    c = controller()
    c.adb_owned = True
    c.run = Mock()
    c.close()
    c.run.assert_called_once_with(['adb','disconnect','127.0.0.1:15557'],timeout=5)


def test_disconnect_failure_does_not_prevent_process_cleanup():
    c = controller()
    proc=Mock()
    proc.poll.return_value=None
    c.tunnel=proc
    c.adb_owned = True
    c.run=Mock(side_effect=RuntimeError('offline'))
    c.close()
    proc.terminate.assert_called_once()
    assert c.tunnel is None


def test_close_without_owned_transport_does_not_disconnect_other_clients():
    c=controller()
    c.run=Mock()
    c.close()
    c.run.assert_not_called()


def test_recovery_after_close_does_not_disconnect_absent_serial(monkeypatch):
    c=controller()
    c.config.target='operator@worker.local'
    c.config.container='android-01'
    c.ssh=Mock(return_value=['ssh'])
    c.run=Mock(side_effect=AssertionError('No debe desconectar de nuevo'))
    c.android_status=Mock(return_value='1\nService input: found\nService activity: found')
    monkeypatch.setattr(subprocess,'run',Mock(return_value=SimpleNamespace(returncode=0,stdout='android-01')))
    c.recover('test-secret')
    c.android_status.assert_called_once()
    c.run.assert_not_called()
