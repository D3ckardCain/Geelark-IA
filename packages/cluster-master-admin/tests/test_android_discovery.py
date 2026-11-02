"""Inventario del worker y aislamiento de operaciones entre perfiles descubiertos."""
import json
import subprocess
import threading
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from geelark_master_admin import create_admin_app, hash_operator_password
from geelark_master_admin.android_control import AndroidConfig
from geelark_master_admin.android_discovery import AndroidRegistry, parse_inventory


def client(tmp_path, registry, diagnostics=False):
    app=create_admin_app(connect=lambda:None,
        operator_password_hash=hash_operator_password('test-password-1234'),
        session_db_path=str(tmp_path/'private'/'session.sqlite3'),
        panel_path=Path(__file__).parents[1]/'src/geelark_master_admin/panel.html',
        android_control=registry,diagnostics_enabled=diagnostics)
    return TestClient(app,base_url='https://master.test')


def login(c):
    assert c.post('/admin/v1/login',json={'password':'test-password-1234'},
                  headers={'Origin':'https://master.test'}).status_code==200


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
    with patch('geelark_master_admin.android_discovery.subprocess.run',return_value=Mock(returncode=1,stderr='sudo: a password is required')):
        registry._discover(None)
    assert len(registry.entries)==1
    assert registry.status()['discovery']['phase']=='needs_auth'
    assert 'secret' not in json.dumps(registry.status())


@pytest.mark.parametrize(('code','stderr','phase'),[
    (255,'ssh: connect to host worker.local port 22: Connection timed out','offline'),
    (255,'ssh: Could not resolve hostname worker.local','offline'),
    (255,'Host key verification failed.','error'),
    (255,'Permission denied (publickey).','error'),
    (1,'sudo: 1 incorrect password attempt','needs_auth'),
    (1,'Cannot connect to the Docker daemon','error'),
])
def test_discovery_distinguishes_network_access_and_docker_failures(registry,code,stderr,phase):
    discover(registry)
    previous=dict(registry.entries)
    with patch('geelark_master_admin.android_discovery.subprocess.run',return_value=Mock(returncode=code,stderr=stderr+'\nprivate-detail')):
        registry._discover('temporary-password')
    status=registry.status()
    assert status['discovery']['phase']==phase
    assert not status['discovery']['busy']
    assert registry.entries==previous
    assert 'temporary-password' not in json.dumps(status)
    assert 'private-detail' not in json.dumps(status)
    if phase!='needs_auth':assert 'contraseña' not in status['discovery']['message']


def test_discovery_timeout_preserves_profiles_without_requesting_sudo(registry):
    discover(registry)
    previous=dict(registry.entries)
    with patch('geelark_master_admin.android_discovery.subprocess.run',side_effect=subprocess.TimeoutExpired('ssh',45)):
        registry._discover(None)
    assert registry.status()['discovery']['phase']=='offline'
    assert not registry.status()['discovery']['busy']
    assert registry.entries==previous


def test_names_match_in_inventory_selection_and_diagnostics_without_reconfiguring(tmp_path,registry):
    seed_config=registry.primary.config
    discover(registry)
    ident=registry.identity('phone-02')
    second=registry.select(ident)
    c=client(tmp_path,registry,diagnostics=True);login(c)
    inventory=c.get('/admin/v1/android').json()
    assert inventory['name']=='Android · phone-01'
    assert [p['name'] for p in inventory['profiles']]==['Android · phone-01','Android · phone-02']
    assert c.get('/admin/v1/android?profile='+ident).json()['name']=='Android · phone-02'
    assert c.get('/admin/v1/diagnostics/android?profile='+ident).json()['status']['name']=='Android · phone-02'
    assert registry.primary.config is seed_config
    assert registry.primary.config.name=='Existing phone'
    assert second.config.container=='phone-02'
    assert second.config.adb_port==5556


def test_diagnostics_link_preserves_the_owner_document(tmp_path,registry):
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.items=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':self.items.append(dict(attrs))
    c=client(tmp_path,registry,diagnostics=True);login(c)
    parser=Links();parser.feed(c.get('/').text)
    link=next(item for item in parser.items if item.get('href')=='/diagnostics')
    assert link['target']=='_blank'
    assert 'noopener' in link['rel'].split()


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
