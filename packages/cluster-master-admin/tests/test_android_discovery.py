"""Inventario del worker y aislamiento de operaciones entre perfiles descubiertos."""
import json
import threading
from unittest.mock import Mock, patch

import pytest

from geelark_master_admin.android_control import AndroidConfig
from geelark_master_admin.android_discovery import AndroidRegistry, parse_inventory
from .test_android_control import client, login


def record(name='phone-02', port=5556, ident='b'*64, state='running'):
    return json.dumps([ident, '/'+name, state, ['/init','androidboot.hardware=redroid'], [],
                       {'5555/tcp':[{'HostIp':'127.0.0.1','HostPort':str(port)}]}])


def service(config):
    result=Mock(config=config, lock=threading.RLock(),busy=False)
    result.controller.screen=None
    result.controller.ssh.return_value=['ssh','-o','BatchMode=yes']
    result.status.return_value={'configured':True,'name':config.name,'busy':False,
                                'phase':'idle','message':'Listo','screen_open':False,'screen_id':None}
    result.submit.return_value=True
    result.diagnostics.return_value=config.container+'-log'
    result.clear_diagnostics.return_value=True
    return result


@pytest.fixture
def registry(tmp_path):
    key=tmp_path/'key';key.write_text('fixture')
    seed=service(AndroidConfig('Existing phone','worker.local','operator','phone-01',key,15557))
    result=AndroidRegistry(seed,factory=service)
    yield result
    result.close()


def discover(registry, password=None):
    output=record('phone-01',5555,'a'*64)+'\n'+record()
    with patch('geelark_master_admin.android_discovery.subprocess.run',return_value=Mock(returncode=0,stdout=output)) as run:
        registry._discover(password)
    return run


def test_discovery_preserves_existing_connection_and_assigns_independent_ports(registry):
    run=discover(registry,'one-time-fixture')
    profiles=registry.status()['profiles']
    assert len(profiles)==2
    second=registry.select(profiles[1]['profile_id'])
    assert second.config.container=='phone-02'
    assert second.config.adb_port==5556
    assert second.config.port!=registry.primary.config.port
    assert second.config.key==registry.primary.config.key
    assert run.call_args.kwargs['input']=='one-time-fixture\n'
    assert 'one-time-fixture' not in repr(run.call_args.args)
    assert 'one-time-fixture' not in json.dumps(registry.status())
    discover(registry)
    assert registry.select(profiles[1]['profile_id']) is second
    assert registry.primary is registry.select()
    assert len(registry.entries)==2


def test_failed_authorization_does_not_change_known_connections(registry):
    with patch('geelark_master_admin.android_discovery.subprocess.run',return_value=Mock(returncode=1,stderr='secret')):
        registry._discover(None)
    assert len(registry.entries)==1
    assert registry.status()['discovery']['phase']=='needs_auth'
    assert 'secret' not in json.dumps(registry.status())


@pytest.mark.parametrize('output',[
    record()+"\n"+record(),
    record()+"\n"+record('other',5556,'c'*64),
    record().replace('127.0.0.1','0.0.0.0'),
    record(port=22),
    'x'*1048577,
])
def test_inventory_rejects_ambiguous_or_unbounded_records(output):
    with pytest.raises(ValueError):parse_inventory(output)


def test_stopped_instances_and_unrelated_containers():
    assert parse_inventory(record(state='exited'))[0]['container_state']=='exited'
    unrelated=json.loads(record());unrelated[3]=['/bin/sh']
    assert parse_inventory(json.dumps(unrelated))==[]


def test_actions_and_diagnostics_are_scoped_to_selected_profile(tmp_path,registry):
    discover(registry)
    ident=registry.identity('phone-02');second=registry.select(ident)
    c=client(tmp_path,registry,diagnostics=True)
    assert c.get('/admin/v1/android').status_code==401
    login(c)
    headers={'Origin':'https://master.test'}
    assert c.post('/admin/v1/android/actions?profile='+ident,json={'action':'disconnect'},headers=headers).status_code==202
    second.submit.assert_called_once_with('disconnect',None)
    registry.primary.submit.assert_not_called()
    assert c.get('/admin/v1/diagnostics/android?profile='+ident).json()['log']=='phone-02-log'
    assert c.post('/admin/v1/diagnostics/android/clear?profile='+ident,headers=headers).status_code==200
    second.clear_diagnostics.assert_called_once()
    registry.primary.clear_diagnostics.assert_not_called()
    assert c.post('/admin/v1/android/actions?profile=unknown',json={'action':'open'},headers=headers).status_code==404
    registry.primary.submit.assert_not_called()
    second.controller.screen=Mock(id='2'*32)
    payload={'screen':'2'*32,'kind':'key','key':3}
    assert c.post('/admin/v1/android/input?profile='+ident,json=payload,headers=headers).status_code==200
    second.controller.screen.input.assert_called_once()
    assert c.post('/admin/v1/android/input',json=payload,headers=headers).status_code==409


def test_discovery_endpoint_requires_session_and_same_origin(tmp_path,registry):
    registry.discover=Mock(return_value=True)
    c=client(tmp_path,registry)
    assert c.post('/admin/v1/android/discover',json={}).status_code==401
    login(c)
    assert c.post('/admin/v1/android/discover',json={},headers={'Origin':'https://evil.test'}).status_code==403
    registry.discover.assert_not_called()
    assert c.post('/admin/v1/android/discover',json={'password':'temporary'},headers={'Origin':'https://master.test'}).status_code==202
    registry.discover.assert_called_once_with('temporary')
