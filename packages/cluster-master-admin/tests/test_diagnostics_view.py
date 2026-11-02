"""Limpiar en servidor/vista y descartar lecturas anteriores a la limpieza."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_clear_does_not_restore_a_late_old_read():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node requerido')
    source = (Path(__file__).parents[1]/'src/geelark_master_admin/diagnostics.html').read_text(encoding='utf-8')
    functions = source.split('<script>', 1)[1].split('run.addEventListener', 1)[0]
    harness = r'''
const assert=require('node:assert/strict');const elements=new Map();
global.document={getElementById(id){if(!elements.has(id))elements.set(id,{textContent:'',disabled:false});return elements.get(id)}};
''' + functions + r'''
(async()=>{
let resolveOld;fetch=()=>new Promise(r=>resolveOld=r);
const old=update();
let posted;
fetch=async(url,options)=>{if(options?.method==='POST'){posted=url;return {ok:true,status:200}}return {ok:true,json:async()=>({log:'',status:{busy:false,message:'Last operation'}})}};
await mutate('clear');
assert.equal(posted,'/admin/v1/diagnostics/android/clear');
assert.equal(log.textContent,'');assert.equal(copy.disabled,true);
resolveOld({ok:true,json:async()=>({log:'OLD DIAGNOSIS',status:{busy:false,message:'Old'}})});await old;
assert.equal(log.textContent,'');
fetch=async(url,options)=>options?.method==='POST'?{ok:true,status:202}:{ok:true,json:async()=>({log:'CURRENT DIAGNOSIS',status:{busy:false,message:'Finished'}})};
await mutate('run');assert.equal(log.textContent,'CURRENT DIAGNOSIS');
assert.equal(copy.disabled,false);
busy=true;let called=false;fetch=()=>{called=true};await mutate('clear');assert.equal(called,false);
busy=false;profileId='c'.repeat(32);const scoped=[];
fetch=async(url,options)=>{scoped.push(url);return options?.method==='POST'?{ok:true,status:202}:{ok:true,json:async()=>({log:'SECOND PROFILE',status:{name:'Android · second',busy:false,message:'Finished'}})}};
await update();await mutate('run');await mutate('clear');
assert.ok(scoped.length>=5);
assert.ok(scoped.every(url=>url.endsWith('?profile='+profileId)));
assert.ok(scoped.includes('/admin/v1/diagnostics/android/clear?profile='+profileId));
assert.equal(document.getElementById('diagnostic-name').textContent,'Android · second');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    r = subprocess.run([node, '-e', harness], capture_output=True, text=True, timeout=10)
    assert r.returncode == 0, r.stderr
