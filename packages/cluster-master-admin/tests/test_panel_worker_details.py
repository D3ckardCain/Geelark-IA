"""Pruebas de comportamiento del JavaScript empaquetado, sin servidor ni navegador."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def test_worker_filters_details_escape_and_session_cleanup():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Se requiere Node.js para ejecutar el JavaScript del panel")
    panel = Path(__file__).parents[1] / "src" / "geelark_master_admin" / "panel.html"
    source = panel.read_text(encoding="utf-8")
    script = source.split("<script>", 1)[1].split("</script>", 1)[0]
    # Carga las funciones reales antes del registro de eventos y del arranque HTTP.
    functions = script.split('el("login-form").addEventListener', 1)[0]
    harness = r"""
const assert=require("node:assert/strict");
const controls=new Map();
global.document={getElementById(id){
  if(!controls.has(id))controls.set(id,{value:"",innerHTML:"",textContent:"",hidden:false,
    classList:{toggle(name,value){controls.get(id).hidden=Boolean(value)}}});
  return controls.get(id);
}};
""" + functions + r"""
const modules=Array.from({length:12},(_,i)=>({module_id:"module-"+i,state:"unknown",version:"1",
  checked_at:null,source:"master-check",error_code:"REPORT_STALE"}));
const snapshot={generated_at:"2026-10-29T12:00:00Z",
  freshness:{state:"stale",age_seconds:120},
  node:{node_id:"worker-1",display_name:"WORKER-UNO",authorization_state:"active",
    health_state:"offline",reported_health_state:"healthy",agent_version:"1.2",
    last_heartbeat_at:"2026-10-29T11:58:00Z",capabilities:["heartbeat-v1"],modules}};
const pending={...snapshot,node:{...snapshot.node,node_id:"worker-2",display_name:"WORKER-DOS",
  authorization_state:"pending",health_state:"unknown"}};
state.snapshots=[snapshot,pending];
assert.equal(filterNodes().length,2);
el("node-search").value="UNO";assert.deepEqual(filterNodes(),[snapshot]);
el("node-authorization").value="pending";assert.equal(filterNodes().length,0);
el("node-search").value="";assert.deepEqual(filterNodes(),[pending]);
el("node-authorization").value="";el("node-health").value="offline";
assert.deepEqual(filterNodes(),[snapshot]);
const detail=nodeDetails(snapshot);
assert.ok(detail.includes("module-11"));assert.ok(detail.includes("REPORT_STALE"));
assert.ok(detail.includes("heartbeat-v1"));assert.ok(detail.includes("120 s"));
const hostile={...snapshot,node:{...snapshot.node,node_id:'"><img src=x onerror=alert(1)>',
  capabilities:["<script>alert(1)</script>"],modules:[{module_id:"<svg/onload=alert(1)>",
  state:"unknown",version:'"><img src=x>',source:"<iframe>",error_code:"<bad>"}]}};
const escaped=nodeDetails(hostile)+nodeRow(hostile);
assert.ok(!escaped.includes("<script>"));assert.ok(!escaped.includes("<img"));
assert.ok(!escaped.includes("<svg"));assert.ok(!escaped.includes("<iframe"));
assert.ok(escaped.includes("&lt;script&gt;"));
state.authenticated=true;state.selectedNodeId="worker-1";renderNodeDetails();
assert.equal(el("node-detail").hidden,false);assert.ok(el("node-detail-body").innerHTML.includes("module-11"));
state.snapshots=[];renderNodeDetails();
assert.equal(el("node-detail").hidden,true);assert.equal(el("node-detail-body").innerHTML,"");
assert.equal(state.selectedNodeId,null);
state.snapshots=[snapshot];state.selectedNodeId="worker-1";state.authenticated=false;renderNodeDetails();
assert.equal(el("node-detail-body").innerHTML,"");assert.equal(state.selectedNodeId,null);
"""
    completed = subprocess.run([node, "-e", harness], capture_output=True, text=True, timeout=15)
    assert completed.returncode == 0, completed.stderr
