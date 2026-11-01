import socket
import struct
import threading
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from geelark_master_admin.android_stream import EmbeddedScreen, read_packet, MAX_PACKET
from fastapi.testclient import TestClient
from geelark_master_admin import create_admin_app, hash_operator_password


def client(tmp_path, service):
    app=create_admin_app(connect=lambda:None,
        operator_password_hash=hash_operator_password('test-password-1234'),
        session_db_path=str(tmp_path/'private'/'session.sqlite3'),
        panel_path=Path(__file__).parents[1]/'src/geelark_master_admin/panel.html',
        android_control=service)
    return TestClient(app,base_url='https://master.test')


def login(c):
    assert c.post('/admin/v1/login',json={'password':'test-password-1234'},
                  headers={'Origin':'https://master.test'}).status_code==200


def test_packets_survive_fragmented_socket_reads_and_rotation():
    a,b=socket.socketpair()
    session=struct.pack('>III',0x80000000,416,720)
    frame=struct.pack('>QI',1<<61|123,4)+b'data'
    def send():
        for byte in session+frame:
            b.sendall(bytes([byte]))
        b.close()
    worker=threading.Thread(target=send);worker.start()
    try:
        assert read_packet(a)==session
        assert read_packet(a)==frame
        with pytest.raises(RuntimeError):read_packet(a)
    finally:a.close();worker.join()


def test_video_packet_limit_is_checked_before_payload_read():
    sock=Mock();sock.recv.return_value=struct.pack('>QI',0,MAX_PACKET+1)
    with pytest.raises(ValueError):read_packet(sock)
    sock.recv.assert_called_once_with(12)


def screen():
    current=EmbeddedScreen(Mock())
    current.proc=Mock();current.proc.poll.return_value=None
    current.control=Mock();current.width=416;current.height=720
    return current


def test_touch_matches_scrcpy_501_binary_protocol_and_rejects_stale_screen():
    current=screen()
    current.input(dict(screen=current.id,kind='touch',action=0,x=20,y=30))
    assert current.control.sendall.call_args.args[0]==struct.pack('>BBQiiHHHII',2,0,0,20,30,416,720,65535,0,0)
    with pytest.raises(ValueError):current.input(dict(screen='old',kind='key',key=3))
    with pytest.raises(ValueError):current.input(dict(screen=current.id,kind='touch',action=0,x=416,y=20))


def test_unicode_text_limit_applies_to_utf8_bytes():
    current=screen()
    with pytest.raises(ValueError):current.input(dict(screen=current.id,kind='text',text='界'*101))
    current.control.sendall.assert_not_called()


def test_stream_and_input_require_session_and_scoped_screen(tmp_path):
    current=screen()
    service=SimpleNamespace(lock=threading.RLock(),busy=False,controller=SimpleNamespace(screen=current))
    c=client(tmp_path,service)
    assert c.get('/admin/v1/android/video',params={'screen':current.id}).status_code==401
    login(c)
    assert c.get('/admin/v1/android/video',params={'screen':'old'}).status_code==409
    payload=dict(screen=current.id,kind='key',key=3)
    assert c.post('/admin/v1/android/input',json=payload).status_code==403
    assert c.post('/admin/v1/android/input',json=payload,headers={'Origin':'https://master.test'}).status_code==200
    payload['key']=123
    assert c.post('/admin/v1/android/input',json=payload,headers={'Origin':'https://master.test'}).status_code==400


def test_second_viewer_is_rejected_without_closing_first(tmp_path):
    current=screen();current.claim.acquire()
    service=SimpleNamespace(lock=threading.RLock(),busy=False,controller=SimpleNamespace(screen=current))
    c=client(tmp_path,service);login(c)
    assert c.get('/admin/v1/android/video',params={'screen':current.id}).status_code==409
    assert not current.cleaned
    current.claim.release()


def test_expired_session_cleans_stream_before_reading():
    current=screen();current.claim.acquire();current.terminate=Mock()
    assert list(current.frames(lambda:False))==[]
    current.terminate.assert_called_once()
    assert current.claim.acquire(blocking=False)
    current.claim.release()


def test_server_handshake_video_control_and_cleanup_over_real_sockets(tmp_path,monkeypatch):
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(2)
    executable=tmp_path/'scrcpy.exe';executable.touch();(tmp_path/'scrcpy-server').touch()
    proc=Mock();proc.stdout=io.BytesIO();proc.poll.return_value=None
    proc.terminate.side_effect=lambda:setattr(proc.poll,'return_value',0)
    c=Mock();c.config.serial='127.0.0.1:15557'
    c.require.side_effect=lambda name:str(executable) if name=='scrcpy' else 'adb'
    def run(args,**kwargs):
        if '--version' in args:return 'scrcpy 5.0.1 <https://github.com/Genymobile/scrcpy>'
        if 'tcp:0' in args:return str(listener.getsockname()[1])
        return ''
    c.run.side_effect=run
    received=[];errors=[]
    def server():
        try:
            video,_=listener.accept();video.settimeout(5);video.sendall(b'\0')
            control,_=listener.accept();control.settimeout(5)
            with video,control:
                video.sendall(b'h264'+struct.pack('>III',0x80000000,32,64))
                received.append(control.recv(14))
        except Exception as error:errors.append(error)
    worker=threading.Thread(target=server);worker.start()
    monkeypatch.setattr('geelark_master_admin.android_stream.subprocess.Popen',Mock(return_value=proc))
    current=EmbeddedScreen(c)
    try:
        current.start();assert read_packet(current.video)==struct.pack('>III',0x80000000,32,64)
        current.input(dict(screen=current.id,kind='key',key=3))
        worker.join(timeout=5);assert not worker.is_alive();assert not errors
        assert received[0].startswith(struct.pack('>BBiii',0,0,3,0,0))
        current.terminate();current.terminate()
        removals=[call for call in c.run.call_args_list if '--remove' in call.args[0]]
        assert len(removals)==1
        assert removals[0].args[0][-1]==f'tcp:{current.port}'
        assert all('--remove-all' not in call.args[0] for call in c.run.call_args_list)
    finally:
        listener.close();current.terminate();worker.join(timeout=5)
