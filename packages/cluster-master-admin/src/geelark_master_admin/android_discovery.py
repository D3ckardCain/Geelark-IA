"""Descubrimiento de redroid en el worker ya configurado. Sin nombres de laboratorio."""
import hashlib
import json
import re
import shlex
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from .android_control import AndroidControl

INSPECT = ('[{{json .Id}},{{json .Name}},{{json .State.Status}},'
           '{{json .Config.Entrypoint}},{{json .Config.Cmd}},{{json .HostConfig.PortBindings}}]')
SCRIPT = "set -eu\nids=$(docker ps -aq --no-trunc)\nif [ -n \"$ids\" ]; then docker inspect --format " + shlex.quote(INSPECT) + " $ids; fi"


def parse_inventory(output):
    if len(output.encode('utf-8')) > 1048576:
        raise ValueError('Inventario demasiado grande')
    records=[]
    seen_ids=set()
    for line in output.splitlines():
        if not line.strip():continue
        ident,name,state,entry,args,ports=json.loads(line)
        if not re.fullmatch(r'[0-9a-f]{64}',ident) or not isinstance(name,str):
            raise ValueError('Inventario inválido')
        if not isinstance(entry,list) or 'androidboot.hardware=redroid' not in entry:
            continue
        if ident in seen_ids or state not in {'created','running','paused','restarting','removing','exited','dead'}:
            raise ValueError('Identidad o estado duplicado o inválido')
        seen_ids.add(ident)
        bindings=(ports or {}).get('5555/tcp') or []
        candidates=[int(b['HostPort']) for b in bindings if b.get('HostIp')=='127.0.0.1' and str(b.get('HostPort','')).isdigit()]
        if len(set(candidates))!=1 or not 1024<=candidates[0]<=65535:
            raise ValueError('Un Android no tiene un puerto ADB loopback inequívoco')
        container=name.removeprefix('/')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',container):
            raise ValueError('Nombre de contenedor inválido')
        records.append({'container':container,'adb_port':candidates[0],'container_state':state})
    if len(records)>50 or len({r['container'] for r in records})!=len(records):
        raise ValueError('Inventario duplicado o fuera del límite')
    if len({r['adb_port'] for r in records})!=len(records):
        raise ValueError('Puertos ADB duplicados')
    return records


class AndroidRegistry:
    def __init__(self, primary, factory=AndroidControl):
        self.primary=primary
        self.factory=factory
        self.registry_lock=threading.RLock()
        self.entries={self.identity(primary.config.container):primary}
        self.states={}
        self.discovery={'busy':False,'phase':'idle','message':'Preparado para detectar Android del worker'}
        self.discovery_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='android-discovery')
        self.shutting_down=False

    def __getattr__(self,name):
        return getattr(self.primary,name)

    def identity(self,container):
        return hashlib.sha256((self.primary.config.target+'\0'+container).encode()).hexdigest()[:32]

    def select(self,ident=None):
        with self.registry_lock:
            return self.primary if ident is None else self.entries.get(ident)

    def status(self):
        result=self.primary.status()
        with self.registry_lock:
            result['profiles']=[dict(service.status(),profile_id=ident,primary=service is self.primary,
                                     container_state=self.states.get(ident,'unknown')) for ident,service in self.entries.items()]
            result['discovery']=dict(self.discovery)
        return result

    def discover(self,password=None):
        with self.registry_lock:
            if self.discovery['busy'] or self.shutting_down:return False
            self.discovery={'busy':True,'phase':'working','message':'Detectando Android en el worker…'}
            self.discovery_pool.submit(self._discover,password)
            return True

    def _discover(self,password):
        try:
            c=self.primary.controller
            sudo="sudo -S -p '' " if password is not None else 'sudo -n '
            command=sudo+'sh -c '+shlex.quote(SCRIPT)
            result=subprocess.run(c.ssh()+[self.primary.config.target,command],
                                  input=password+'\n' if password is not None else None,
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',errors='replace',
                                  timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:
                with self.registry_lock:
                    self.discovery={'busy':False,'phase':'needs_auth','message':'Autoriza la consulta del worker para detectar sus Android'}
                return
            records=parse_inventory(result.stdout)
            with self.registry_lock:
                if self.shutting_down:return
                for record in records:
                    existing=self.entries.get(self.identity(record['container']))
                    if existing and existing.config.adb_port!=record['adb_port']:
                        raise ValueError('Cambió el puerto de un perfil ya registrado')
                used={s.config.port for s in self.entries.values()}
                additions={}
                for record in records:
                    ident=self.identity(record['container'])
                    existing=self.entries.get(ident)
                    if existing:
                        continue
                    with socket.socket() as probe:
                        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
                    while port in used:
                        with socket.socket() as probe:
                            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
                    used.add(port)
                    config=replace(self.primary.config,name=record['container'],container=record['container'],
                                   port=port,adb_port=record['adb_port'])
                    additions[ident]=self.factory(config)
                self.entries.update(additions)
                self.states={self.identity(r['container']):r['container_state'] for r in records}
                self.discovery={'busy':False,'phase':'ready','message':f'{len(records)} Android detectados en el worker'}
        except Exception:
            with self.registry_lock:
                self.discovery={'busy':False,'phase':'error','message':'No se pudo completar la detección. Comprueba el acceso al worker.'}
        finally:
            password=None

    def close(self):
        with self.registry_lock:self.shutting_down=True
        self.discovery_pool.shutdown(wait=True,cancel_futures=True)
        for service in list(self.entries.values()):service.close()
