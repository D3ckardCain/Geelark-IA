"""Respuestas de snapshots de sesiones anteriores no deben repoblar el panel."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_snapshot_responses_are_discarded_after_session_change():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Se requiere Node.js para comprobar JavaScript")
    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    functions = source.split("<script>", 1)[1].split("</script>", 1)[0].split('el("login-form").addEventListener', 1)[0]
    harness = r"""
const assert=require("node:assert/strict");
const controls=new Map();
global.document={getElementById(id){
  if(!controls.has(id))controls.set(id,{value:"",innerHTML:"",textContent:"",disabled:false,
    classList:{toggle(){},add(){},remove(){}},focus(){}});
  return controls.get(id);
}};
""" + functions + r"""
(async()=>{
let notices=0;updateNotice=()=>{notices++};
const snapshot={node:{node_id:"worker-1",display_name:"WORKER-1",authorization_state:"active",
  health_state:"healthy",capabilities:[],modules:[]},freshness:{state:"fresh",age_seconds:0}};
const payload={schema_version:"1.0",snapshots:[snapshot]};
const ok=()=>({ok:true,status:200,headers:{get:()=>"application/json"},json:async()=>payload});
state.authenticated=true;
let finishOld;
fetch=()=>new Promise(resolve=>{finishOld=resolve});
const old=refresh();
state.authenticated=false;showLogin("Sesión cerrada.");render();
finishOld(ok());await old;
assert.deepEqual(state.snapshots,[]);assert.equal(state.connected,false);
assert.equal(state.lastRefresh,null);assert.equal(notices,0);
// Pérdida de sesión mientras ya se está leyendo el JSON.
state.authenticated=true;
let finishJson;
fetch=async()=>({...ok(),json:()=>new Promise(resolve=>{finishJson=resolve})});
const decoding=refresh();await Promise.resolve();
assert.equal(typeof finishJson,"function");
state.authenticated=false;showLogin("Sesión cerrada.");
// Una nueva sesión inicia su propia consulta antes de que termine la anterior.
state.authenticated=true;
let finishNew;
fetch=()=>new Promise(resolve=>{finishNew=resolve});
const fresh=refresh();
finishJson(payload);await decoding;
assert.equal(state.busy,true);assert.deepEqual(state.snapshots,[]);
finishNew(ok());await fresh;
assert.deepEqual(state.snapshots,[snapshot]);assert.equal(state.busy,false);
assert.equal(state.connected,true);assert.equal(notices,1);
// Un error tardío tampoco debe reemplazar los datos de la nueva sesión.
let rejectOld;
fetch=()=>new Promise((resolve,reject)=>{rejectOld=reject});
const failing=refresh();
state.authenticated=false;showLogin("Sesión cerrada.");
state.authenticated=true;fetch=async()=>ok();await refresh();
rejectOld(new Error("error de sesión anterior"));await failing;
assert.deepEqual(state.snapshots,[snapshot]);assert.equal(state.connected,true);
assert.equal(state.error,null);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result = subprocess.run([node, "-e", harness], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
