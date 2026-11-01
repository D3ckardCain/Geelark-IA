import threading
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from geelark_master_admin import create_admin_app, hash_operator_password
from geelark_master_admin.android_control import AndroidConfig, AndroidControl
from geelark_master_admin.android_process import healthy


def client(tmp_path, service=None, diagnostics=False):
    app = create_admin_app(connect=lambda: None,
        operator_password_hash=hash_operator_password("test-password-1234"),
        session_db_path=str(tmp_path / "private" / "session.sqlite3"),
        panel_path=Path(__file__).parents[1]/"src/geelark_master_admin/panel.html",
        android_control=service, diagnostics_enabled=diagnostics)
    return TestClient(app, base_url="https://master.test")


def login(c):
    assert c.post('/admin/v1/login', json={'password':'test-password-1234'},
                  headers={'Origin':'https://master.test'}).status_code == 200


def test_control_authentication_origin_and_fixed_actions(tmp_path):
    service = Mock()
    service.status.return_value = {'configured': True}
    service.submit.return_value = True
    c = client(tmp_path, service)
    assert c.get('/admin/v1/android').status_code == 401
    assert c.post('/admin/v1/android/actions', json={'action':'open'}).status_code == 401
    login(c)
    assert c.post('/admin/v1/android/actions', json={'action':'open'},headers={'Origin':'https://evil.test'}).status_code == 403
    assert c.post('/admin/v1/android/actions', json={'action':'shell','password':'sensitive-test'},headers={'Origin':'https://master.test'}).status_code == 400
    service.submit.assert_not_called()
    r = c.post('/admin/v1/android/actions', json={'action':'open'},headers={'Origin':'https://master.test'})
    assert r.status_code == 202
    service.submit.assert_called_once_with('open', None)
    assert r.headers['cache-control'].startswith('no-store')


def test_diagnostics_optional_and_separate_from_status(tmp_path):
    service = Mock()
    service.status.return_value = {'configured': True, 'message':'OK'}
    service.diagnostics.return_value = 'technical-log'
    c = client(tmp_path, service)
    login(c)
    assert c.get('/diagnostics').status_code == 404
    assert c.get('/admin/v1/diagnostics/android').status_code == 404
    assert c.post('/admin/v1/diagnostics/android',headers={'Origin':'https://master.test'}).status_code == 404
    assert 'technical-log' not in c.get('/admin/v1/android').text
    assert 'href="/diagnostics"' not in c.get('/').text


def test_diagnostics_require_session_and_origin(tmp_path):
    service = Mock()
    service.status.return_value = {'busy':False}
    service.diagnostics.return_value = 'trace'
    service.submit.return_value = True
    c = client(tmp_path, service, diagnostics=True)
    assert c.get('/diagnostics').status_code == 401
    login(c)
    assert c.get('/diagnostics').status_code == 200
    assert 'href="/diagnostics"' in c.get('/').text
    assert c.post('/admin/v1/diagnostics/android',headers={'Origin':'https://evil.test'}).status_code == 403
    assert c.post('/admin/v1/diagnostics/android',headers={'Origin':'https://master.test'}).status_code == 202


def test_without_config_no_operations(tmp_path):
    c = client(tmp_path)
    login(c)
    assert c.get('/admin/v1/android').status_code == 503
    assert c.post('/admin/v1/android/actions', json={'action':'open'},headers={'Origin':'https://master.test'}).status_code == 503


def test_clear_diagnostics_is_opt_in_authenticated_and_same_origin(tmp_path):
    service = Mock()
    service.clear_diagnostics.return_value = True
    c = client(tmp_path, service)
    assert c.post('/admin/v1/diagnostics/android/clear').status_code == 404
    c = client(tmp_path, service, diagnostics=True)
    assert c.post('/admin/v1/diagnostics/android/clear').status_code == 401
    login(c)
    assert c.post('/admin/v1/diagnostics/android/clear', headers={'Origin':'https://evil.test'}).status_code == 403
    service.clear_diagnostics.assert_not_called()
    assert c.post('/admin/v1/diagnostics/android/clear', headers={'Origin':'https://master.test'}).json() == {'cleared':True}
    service.clear_diagnostics.return_value = False
    assert c.post('/admin/v1/diagnostics/android/clear', headers={'Origin':'https://master.test'}).status_code == 409


def test_records_preserve_crash_header_and_reject_old_attempt_emitters(tmp_path):
    key = tmp_path/'key'
    key.write_text('fixture')
    controller = Mock(screen=None)
    service = AndroidControl(AndroidConfig('Device','worker.local','operator','device',key,15557), factory=lambda *_:controller)
    emitters = []
    def collect(*_):
        emitters.append(controller.emit)
        controller.emit('CURRENT-HEADER\n'+'\n'.join('crash-frame-'+str(i)+'-'*40 for i in range(100)))
    try:
        service.record('OLD-DIAGNOSIS')
        assert service.submit('diagnose', diagnostic=collect)
        service.executor.submit(lambda: None).result(timeout=2)
        assert 'OLD-DIAGNOSIS' not in service.diagnostics()
        assert 'CURRENT-HEADER' in service.diagnostics()
        assert 'crash-frame-99' in service.diagnostics()
        assert service.clear_diagnostics()
        emitters[0]('STALE-SCREEN-OUTPUT')
        assert service.diagnostics() == ''
        service.busy = True
        service.record('ACTIVE-OPERATION')
        assert not service.clear_diagnostics()
        assert 'ACTIVE-OPERATION' in service.diagnostics()
        service.busy = False
        service.record('BETWEEN-ATTEMPTS')
        assert service.submit('diagnose', diagnostic=collect)
        service.executor.submit(lambda: None).result(timeout=2)
        assert 'BETWEEN-ATTEMPTS' not in service.diagnostics()
        emitters[0]('FIRST-ATTEMPT-LATE-OUTPUT')
        assert 'FIRST-ATTEMPT-LATE-OUTPUT' not in service.diagnostics()
    finally:
        service.close()


def test_recovery_password_not_returned_or_accepted_for_open(tmp_path):
    service = Mock()
    service.submit.return_value = True
    c = client(tmp_path, service)
    login(c)
    r = c.post('/admin/v1/android/actions',json={'action':'recover','password':'ephemeral-test'},headers={'Origin':'https://master.test'})
    assert r.status_code == 202 and 'ephemeral-test' not in r.text
    service.submit.assert_called_once_with('recover','ephemeral-test')
    assert c.post('/admin/v1/android/actions',json={'action':'open','password':'ephemeral-test'},headers={'Origin':'https://master.test'}).status_code == 400


@pytest.mark.parametrize('field,value', [('host','-oProxyCommand=anything'),('container','name; touch anything'),('user','root;whoami'),('port',True)])
def test_config_rejects_shell_and_option_injection(tmp_path, field, value):
    key=tmp_path/'key'
    key.write_text('fixture')
    data=dict(name='Device',host='worker.local',user='operator',container='device',key=key,port=15557)
    data[field]=value
    with pytest.raises(ValueError):
        AndroidConfig(**data)


def test_one_operation_at_a_time_and_shutdown_owned_controller(tmp_path):
    key=tmp_path/'key'
    key.write_text('fixture')
    controller=Mock(screen=None)
    entered=threading.Event()
    release=threading.Event()
    def open_screen():
        entered.set()
        release.wait(2)
    controller.open_screen.side_effect=open_screen
    service=AndroidControl(AndroidConfig('Device','worker.local','operator','device',key,15557),factory=lambda *_:controller)
    try:
        assert service.submit('open')
        assert entered.wait(1)
        assert not service.submit('recover','secret')
        assert service.status()['busy']
    finally:
        release.set()
        service.close()
    controller.close.assert_called_once()
    assert not service.submit('open')


def test_android_boot_flag_without_services_is_rejected():
    assert not healthy('1\nService input: not found\nService activity: not found')
    assert healthy('1\nService input: found\nService activity: found')


def test_exited_scrcpy_does_not_report_success(tmp_path):
    key=tmp_path/'key'
    key.write_text('fixture')
    controller=Mock()
    controller.screen.poll.return_value=1
    service=AndroidControl(AndroidConfig('Device','worker.local','operator','device',key,15557),factory=lambda *_:controller)
    try:
        service.action='open'
        service.phase='ready'
        service.message='Pantalla iniciada'
        status=service.status()
        assert not status['screen_open'] and status['phase']=='error'
        assert 'Pantalla iniciada' not in status['message']
    finally:
        service.close()
