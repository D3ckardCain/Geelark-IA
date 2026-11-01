import socket
import struct
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from geelark_master_admin.android_stream import EmbeddedScreen, read_packet, MAX_PACKET
from test_android_control import client, login


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
