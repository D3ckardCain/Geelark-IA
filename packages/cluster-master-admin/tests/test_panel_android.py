"""Una respuesta anterior al logout no debe reactivar los controles Android."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_android_session_race_and_recovery_payload():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node requerido')
    source = (Path(__file__).parents[1]/'src/geelark_master_admin/panel.html').read_text(encoding='utf-8')
    functions=source.split('<script>',1)[1].split('</script>',1)[0].split('el("login-form").addEventListener',1)[0]
    harness=r'''
const assert=require('node:assert/strict');const controls=new Map();
global.document={getElementById(id){if(!controls.has(id))controls.set(id,{value:'',textContent:'',innerHTML:'',disabled:false,hidden:false,close(){},focus(){},classList:{add(){},remove(){},toggle(name,value){controls.get(id).hidden=Boolean(value)}}});return controls.get(id)}};
''' + functions + r'''
(async()=>{
state.authenticated=true;
let resolveOld;fetch=()=>new Promise(r=>resolveOld=r);
const old=refreshAndroid();
state.authenticated=false;state.sessionVersion++;clearAndroid();
assert.equal(el('android-open').disabled,true);
state.authenticated=true;
fetch=async()=>({ok:true,status:200,json:async()=>({configured:true,name:'Current',busy:false,screen_open:false,phase:'ready',message:'Current state'})});
await refreshAndroid();
resolveOld({ok:true,status:200,json:async()=>({configured:true,name:'Stale',busy:false,screen_open:true,phase:'ready',message:'Old state'})});await old;
assert.equal(el('android-name').textContent,'Current');
assert.equal(el('android-profile-row').hidden,false);
el('profile-search').value='missing';filterProfiles();
assert.equal(el('android-profile-row').hidden,true);assert.equal(el('profiles-count').textContent,'0 de 1 perfil');
el('profile-search').value='cur';el('profile-state').value='open';filterProfiles();
assert.equal(el('android-profile-row').hidden,true);
el('profile-state').value='closed';filterProfiles();assert.equal(el('android-profile-row').hidden,false);
el('profile-state').value='';el('profile-search').value='';filterProfiles();
let posted;
fetch=async(url,options)=>{if(options.method==='POST'){posted=JSON.parse(options.body);return {ok:true,status:202}}return {ok:true,status:200,json:async()=>({configured:true,name:'Current',busy:true,screen_open:false,phase:'working',message:'Working'})}};
await androidAction('recover','temporary-secret');
assert.deepEqual(posted,{action:'recover',password:'temporary-secret'});
assert.equal(el('android-open').disabled,true);
state.authenticated=false;clearAndroid();
assert.equal(el('recovery-password').value,'');assert.equal(el('android-name').textContent,'Perfil Android');
assert.equal(el('android-profile-row').hidden,true);
state.authenticated=true;fetch=async()=>({ok:false,status:503});await refreshAndroid();
assert.equal(el('android-profile-row').hidden,true);assert.equal(el('android-open').disabled,true);
assert.ok(el('profiles-empty').textContent.includes('No tienes perfiles conectados'));
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    completed=subprocess.run([node,'-e',harness],capture_output=True,text=True,encoding='utf-8',timeout=10)
    assert completed.returncode==0, completed.stderr
