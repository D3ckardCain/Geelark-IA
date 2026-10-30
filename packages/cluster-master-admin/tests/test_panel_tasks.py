"""JavaScript de tareas: consulta, filtros, escape y descarte de respuestas tardías."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_tasks_ui_reads_filters_and_discards_late_responses():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Se requiere Node.js para comprobar el JavaScript del panel")
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
const task={task_id:"task-1",node_id:"node-1",status:"failed",last_error_code:"ENGINE_ERROR",delivery_attempts:2};
state.authenticated=true;state.tasksOffset=50;
el("tasks-node").value="node-1";el("tasks-status").value="failed";
let requested;
global.fetch=async(url,options)=>{requested={url,options};return {status:200,ok:true,
  json:async()=>({schema_version:"1.0",generated_at:"2026-10-29T12:00:00Z",tasks:[task],has_more:true})}};
await refreshTasks();
assert.ok(requested.url.includes("node_id=node-1"));assert.ok(requested.url.includes("status=failed"));
assert.ok(requested.url.includes("offset=50"));assert.equal(requested.options.cache,"no-store");
assert.equal(requested.options.credentials,"same-origin");
assert.equal(requested.options.method,undefined); // fetch usa GET por defecto
assert.deepEqual(state.tasks,[task]);assert.equal(state.tasksHasMore,true);
state.selectedTaskId="task-1";renderTasks();assert.ok(el("task-detail-body").innerHTML.includes("ENGINE_ERROR"));
const hostile=taskDetails({...task,task_id:"<script>alert(1)</script>",node_id:'<img src=x onerror=alert(1)>'});
assert.ok(!hostile.includes("<script>"));assert.ok(!hostile.includes("<img"));
assert.ok(hostile.includes("&lt;script&gt;"));
let resolveResponse;
global.fetch=()=>new Promise(resolve=>{resolveResponse=resolve});
const pending=refreshTasks();
state.authenticated=false;state.sessionVersion++;clearTasks();renderTasks();
resolveResponse({ok:true,status:200,json:async()=>({schema_version:"1.0",tasks:[task],has_more:false})});
await pending;
assert.deepEqual(state.tasks,[]);assert.equal(el("task-detail-body").innerHTML,"");
state.authenticated=true;global.fetch=async()=>({ok:false,status:401});
await refreshTasks();
assert.equal(state.authenticated,false);assert.deepEqual(state.tasks,[]);
assert.ok(el("login-error").textContent.includes("Sesión requerida"));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result = subprocess.run([node, "-e", harness], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
