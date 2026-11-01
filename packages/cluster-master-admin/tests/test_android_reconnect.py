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
    c.allocator_status=Mock(return_value='ready')
    monkeypatch.setattr(subprocess,'run',Mock(return_value=SimpleNamespace(returncode=0,stdout='android-01')))
    c.recover('test-secret')
    assert c.android_status.call_count == 2
    c.run.assert_not_called()


def test_recovery_repairs_confirmed_gralloc_fault_without_container_restart(monkeypatch):
    c=controller()
    c.android_status=Mock(return_value='1\nService input: found\nService activity: found')
    c.allocator_status=Mock(return_value='failed')
    c.repair_allocator=Mock(return_value=True)
    c.close=Mock()
    restart=Mock(side_effect=AssertionError('No debe reiniciar el contenedor'))
    monkeypatch.setattr(subprocess,'run',restart)
    c.recover('test-secret')
    c.repair_allocator.assert_called_once()
    restart.assert_not_called()


def test_unconfirmed_graphic_repair_falls_back_to_requested_container_restart(monkeypatch):
    c=controller()
    c.config.target='operator@worker.local'
    c.config.container='android-01'
    c.ssh=Mock(return_value=['ssh'])
    c.close=Mock()
    c.android_status=Mock(return_value='1\nService input: found\nService activity: found')
    c.allocator_status=Mock(side_effect=['failed','ready'])
    c.repair_allocator=Mock(return_value=False)
    restart=Mock(return_value=SimpleNamespace(returncode=0,stdout='android-01'))
    monkeypatch.setattr(subprocess,'run',restart)
    c.recover('test-secret')
    c.repair_allocator.assert_called_once()
    restart.assert_called_once()
    assert restart.call_args.args[0][-1] == "sudo -S -p '' docker restart android-01"
    assert all('test-secret' not in str(call) for call in c.emit.call_args_list)


@pytest.mark.parametrize('output,expected', [
    ("Warning: Skipping android.hardware.graphics.allocator@2.0::IAllocator/default: interfaceChain fails: Status(EX_TRANSACTION_FAILED)", 'failed'),
    ('DM,FC Y android.hardware.graphics.allocator@2.0::IAllocator/default N/A 78 78', 'ready'),
    ('DM,FC ? android.hardware.graphics.allocator@2.0::IAllocator/default N/A N/A', 'unknown'),
    ('X ? android.hardware.graphics.allocator@2.0::IAllocator/default N/A 78', 'unknown'),
])
def test_allocator_requires_live_service_and_checks_transaction_failure(output, expected):
    c=controller()
    c.run=Mock(return_value=output)
    assert c.allocator_status() == expected


def test_repair_checks_service_and_android_before_success(monkeypatch):
    c=controller()
    c.run=Mock()
    c.allocator_status=Mock(side_effect=['failed','ready'])
    c.android_status=Mock(return_value='1\nService input: found\nService activity: found')
    monkeypatch.setattr('geelark_master_admin.android_process.time.sleep',lambda _:None)
    assert c.repair_allocator()
    c.run.assert_called_once_with(['adb','-s',c.config.serial,'shell',
                                  'su 0 setprop ctl.restart vendor.gralloc-2-0'],timeout=10)


def test_failed_repair_is_bounded_and_not_reported_as_success(monkeypatch):
    c=controller()
    c.run=Mock()
    c.allocator_status=Mock(return_value='failed')
    c.android_status=Mock()
    monkeypatch.setattr('geelark_master_admin.android_process.time.sleep',lambda _:None)
    assert not c.repair_allocator()
    assert c.allocator_status.call_count == 5
    c.android_status.assert_not_called()
