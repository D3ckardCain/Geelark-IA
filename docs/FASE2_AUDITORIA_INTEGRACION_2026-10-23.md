# Fase 2 — Auditoría de integración y deuda pendiente — 2026-10-23

## Resultado de inspección en vivo

Se consultaron metadatos de las PR apiladas, comparaciones de commits y Issues de aceptación. No se rebasaron ramas, no se fusionaron PR, no se cerraron Issues ni se lanzaron workflows manuales. Los workflows automáticos posteriores sí se ejecutaron por commits de corrección; los resultados se registran en la revalidación final.

### Cadena de control

| PR | Estado de merge reportado (consulta 2026-10-23) | Base → HEAD | Hallazgo |
|---|---|---|---|
| #101 | `mergeable=true` | `feat/agent-https-transport` → `043a4e23` | CI actual verde: transporte #479/#478, esquema #308 y persistencia #607. Sigue en draft. |
| #74 | `mergeable=true` | `fix/worker-module-inventory-transport-ack-v2` → `406936ec` | CI actual verde: transporte #480 y persistencia #608. Sigue en draft. |
| #52 | `mergeable=false` | `feat/master-status-snapshot-provider-v1` → `20e618aa` | Conflicto de integración; no fusionar. |
| #57 | `mergeable=true` | `feat/agent-task-inbox-v2` → `a27922c2` | Depende de #52; no integrar antes de resolver #52. |
| #67 | `mergeable=false` | `feat/agent-lifecycle-sync-inbox` → `776a3d54` | Depende de #57; requiere reconciliación tras estabilizar las bases anteriores. |
| #85 | `mergeable=true` | `feat/agent-supervisor-heartbeat-v2` → `3ef9f065` | Depende de #67; no integrar antes de validar la cadena completa. |
| #112 | `mergeable=false` | `feat/agent-task-inbox-v2` ← `406936ec` | PR de sincronización del proveedor #74 a la rama de bandeja; resolver conflictos, no fusionar a ciegas. |
| #113 | `mergeable=true` | `feat/agent-task-inbox-v2` → `21a5b491` | Corrección de lease validada: transporte #482 y persistencia #609 `success`; mantener draft hasta revisión/integración. |

Los SHA abreviados de la tabla sirven para orientación; usar SHA completos en operaciones. La propiedad `mergeable` es una observación de GitHub en el momento de la consulta y puede cambiar.

### CI exacta de #101 — estado actual

- HEAD actual consultado: `043a4e23efd063949577f758eacc326d74bb7ce5`.
- Transporte #479/#478, esquema #308 y persistencia #607 terminaron `completed/success`.
- GitHub informa `mergeable=true`. La PR sigue en draft y no se ha fusionado; revisar contrato/migración y dependencias antes de integrar.
- El SHA `b84da93881f5869e8832e5888e5dce02433e85cc` descrito en una sección histórica posterior no debe usarse como estado actual.

### Línea Windows PC-MASTER

| PR | Estado observado | Conclusión |
|---|---|---|
| #104 | abierta, draft, mergeable=true | Mantener separada; falta aceptación manual #77 y verificación local #88. |
| #103 | abierta, draft, mergeable=true | Corregir ACL/runtime y validar contra su ascendencia real antes de integrar. |
| #87 | abierta, draft, mergeable=true | Es el lanzador/configurador, no el panel web. Mantener separados los criterios de aceptación. |
| #48 | abierta, draft, mergeable=true | Transporte HTTPS base de la línea de agentes; no asumir que esté fusionada. |

No usar `mergeable=true` como sustituto de revisión, CI del HEAD exacto, integración de dependencias y aceptación manual.

### Divergencia de las PR raíz contra `main`

La revalidación de Compare API encontró tres PR raíz con ascendencia muy atrasada respecto a `main`:

| PR | Compare `main...head` | Diff visible | Acción segura |
|---|---|---|---|
| #16 contratos | `diverged`, 20 commits exclusivos de rama / 254 de main no presentes | 8 archivos nuevos de contratos y workflow; `mergeable=false` | Reconciliar la rama con main y revalidar CI antes de aceptar #28/#30 descendientes |
| #32 esquema | `diverged`, 18 commits exclusivos de rama / 242 de main no presentes | 5 archivos de migración/workflows/manual; `mergeable=false` | Reconciliar esquema/migraciones sin perder cambios y validar #34/#36/#38 descendientes |
| #40 ADR autenticación agentes | `diverged`, 2 commits exclusivos de rama / 242 de main no presentes | ADR-005 única, no integrada en main; `mergeable=false` | Conservar la decisión y reconciliar referencias con #42/#44/#47/#48 |

Los contadores de commits describen la divergencia del historial, no que todos esos commits formen parte del diff de la PR. CI en los HEAD actuales consultados: #16 run #1 `success`; #32 esquema #28 y persistencia #44 `success`; #40 no tiene workflow asociado (es documental). Estos resultados no resuelven la divergencia ni sustituyen revisar el SHA integrado. No fusionar ni cambiar bases automáticamente. Los comentarios de auditoría se añadieron en las tres PR.

## Issues: evitar cierres incorrectos

- **#29 sigue abierta correctamente:** quedan pruebas negativas de contratos, unicidad, timestamps, semántica de recursos, compatibilidad de versiones y revisión de seguridad. CI histórica de #16 no satisface estos criterios.
- **#89 sigue abierta correctamente:** la incidencia de ACL de Windows no debe cerrarse hasta integrar y probar la corrección en la pila actual; la suite completa tiene un bloqueo separado por módulos de prueba duplicados en #91.
- **#77 y #88 siguen abiertas correctamente:** la primera requiere aceptación manual del panel Windows; la segunda requiere comparar el acceso directo/artefacto realmente ejecutado en el PC con los artefactos del repositorio. No pueden resolverse solo desde GitHub.
- **#3, #4 y #6 no son duplicados exactos:** #3 coordina la Fase A; #4 fija el método y criterios de paridad; #6 contiene el catálogo detallado.
- **#10, #24 y #92 tienen puertas distintas:** inventario/medición física, caché local verificada y aprovisionamiento Debian. No instalar redroid ni tocar discos mientras falte aprobación de seguridad/procedimiento.
- **#27 continúa siendo bloqueo obligatorio:** no se ha aportado evidencia de mitigación reproducible para un digest concreto.

## Optimizaciones seguras aplicadas a la estrategia

1. No ejecutar re-runs solo para refrescar estados; ejecutar CI únicamente cuando cambie el SHA o exista una regresión concreta.
2. No cerrar ni borrar PR/Issues por antigüedad. Primero identificar cambios exclusivos y destino canónico.
3. Tratar documentación, CI, integración y aceptación física como estados separados.
4. Resolver conflictos por orden de dependencia, sin cambiar bases automáticamente.
5. Mantener redroid como único motor en preparación y coste objetivo 0 USD.

## Siguiente tarea técnica

Inspeccionar los commits que divergen en #101 respecto de la base actual y determinar el conjunto mínimo de cambios que debe preservarse. Luego resolver únicamente #101 y validar CI del nuevo HEAD. No continuar a #74 hasta que #101 tenga base reconciliada y CI relevante en verde.


## Seguimiento de resolución de PR #101 — 2026-10-23

Se realizaron tres correcciones acotadas directamente en la rama `fix/worker-module-inventory-transport-ack-v2` para reducir solapamientos con la base:
- Commit `34004599821454e05b6380ed77f6bfaf50271772`: alinea `tests/test_runtime.py` con las pruebas actuales del contrato ACK (estado/resultado esperados y ACK fail-closed).
- Commit `f3c14ff2fbfd751cb80250b3507a4752f1a788ff`: separa la explicación del fencing ACK en README para conservar el inventario de módulos y reducir conflicto de línea.
- Commit `3123cd15e08c301860389abd00900e26b4c660a2`: reconcilia el comentario del workflow con la base y mantiene una nota separada sobre el fencing.

El código `runtime.py` fue comparado en ambas ramas y su contenido actual coincide. La base tiene siete commits posteriores al ancestro común que tocan workflow, README, runtime y tests. Aunque se reconciliaron los solapamientos visibles de esos cuatro archivos, GitHub sigue informando `mergeable=false` para la PR #101. La consulta de estados y workflows del HEAD `3123cd15e08c301860389abd00900e26b4c660a2` no devolvió checks ni ejecuciones asociados. Por tanto, **no se considera resuelta** ni se ha intentado fusionar.

Siguiente paso seguro: obtener/reconciliar la base exacta y resolver el conflicto restante con una operación Git de merge/rebase que preserve los cambios únicos de la PR; validar el nuevo HEAD con CI antes de quitar el draft. No se deben tratar los checks históricos como evidencia de esta revisión.

## Resolución de la divergencia de PR #101 — 2026-10-23 (seguimiento)

Se sincronizó realmente `feat/agent-https-transport` dentro de `fix/worker-module-inventory-transport-ack-v2` mediante la PR auxiliar #110, fusionada correctamente por GitHub en el commit `32797b1cce9714e332ff1bd9020fab8db482b1d5`. La comparación de ramas posterior confirmó `ahead 30 / behind 0` respecto de `feat/agent-https-transport`; la divergencia de siete commits quedó eliminada. Se restauraron después en el README de la rama los apartados del inventario v1 y el contrato de ACK cercado, commit `043a4e23efd063949577f758eacc326d74bb7ce5`.

Estado posterior: PR #101 sigue abierta y en draft. La consulta de workflows/status para el HEAD `043a4e23efd063949577f758eacc326d74bb7ce5` aún no devuelve ejecuciones ni checks, y el indicador `mergeable` de GitHub osciló tras los últimos cambios; no se declara resuelta hasta reconsultar la mergeabilidad y obtener CI del HEAD exacto. No fusionar #101 ni desplegar a hardware físico mientras falten esas verificaciones.

## Confirmación final de sincronización — 2026-10-23

Reconsulta posterior a la restauración documental: PR #101 HEAD `043a4e23efd063949577f758eacc326d74bb7ce5`, `mergeable=true`, comparación `ahead 30 / behind 0` respecto de `feat/agent-https-transport`. GitHub ha iniciado CI para ese SHA: transporte run #40018311736, esquema #40018311703 y persistencia #40018311695; los tres figuraban `pending` al registrar este punto. Se añadió comentario de seguimiento a la PR. Mantener draft hasta obtener resultados finales de los tres workflows; no fusionar #101 antes de CI y revisión de la dependencia apilada.

## Resultado final de verificación CI — 2026-10-23

Para el HEAD exacto `043a4e23efd063949577f758eacc326d74bb7ce5`, los tres workflows terminaron `completed/success`:
- Transporte HTTPS #40018311736: transporte/seguridad y comprobación de dependencias correctos.
- Esquema PostgreSQL #40018311703: migraciones, smoke tests y restricciones correctos.
- Servicio de persistencia #40018311695: pruebas de integración/concurrencia, guard, autenticación y consistencia de dependencias correctas.

GitHub confirma `mergeable=true` y la comparación de ramas es `ahead 30 / behind 0`. La descripción de la PR #101 y su conversación se actualizaron con estos resultados. La PR permanece en draft y no se ha fusionado: los checks de CI no sustituyen la revisión final del contrato/migración ni las pruebas de aceptación en PCs físicas.

## Siguiente etapa: sincronización de proveedor de snapshots — 2026-10-23

Se fusionó la PR auxiliar #111 (solo sincronización de rama) en el merge commit `406936ecef181eb4a7a34d6e25316079ee8b29ea`, incorporando el HEAD de inventario/ACK validado `043a4e23efd063949577f758eacc326d74bb7ce5` dentro de `feat/master-status-snapshot-provider-v1`. La PR #74 conserva sus cambios propios; comparación ahora `ahead 14 / behind 0` respecto de la base #101 y GitHub indica `mergeable=true`.

CI del merge result: persistencia #40018703486 y transporte HTTPS #40018705163 estaban `in_progress` al registrar esta nota. La PR #74 sigue en draft. Antes de avanzar a la bandeja de tareas (#52), verificar ambos workflows del SHA exacto y revisar el contrato de snapshots, permisos reales de solo lectura y futura autenticación de operador. No integrar ni desplegar en hardware físico por el mero hecho de tener mergeable=true.


## Revalidación del proveedor y bloqueo de sincronización de #52 — 2026-10-23

El HEAD del proveedor de snapshots `406936ecef181eb4a7a34d6e25316079ee8b29ea` terminó con CI verde en ambos workflows disparados para esta revisión:
- Persistencia PostgreSQL [#40018703486](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40018703486): `completed/success`.
- Transporte HTTPS [#40018705163](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40018705163): `completed/success`.

Revisión estática del proveedor: consulta `SELECT` parametrizada, sin listener HTTP, y contrato/manual dejan explícitos los requisitos de rol PostgreSQL de solo lectura y autenticación/autorización humana antes de conectar el panel. No hay aceptación de producción: falta integrar autenticación humana, conectar la UI y validar permisos efectivos del entorno.

Para llevar la base verificada a la rama de bandeja se abrió PR auxiliar #112 (`feat/master-status-snapshot-provider-v1` → `feat/agent-task-inbox-v2`). La comparación muestra 34 commits exclusivos del proveedor y 23 commits exclusivos de la bandeja, con ancestro común `a8ce049458e94ae2587caeb8a42269a0b094b09a`. GitHub marca #112 `mergeable=false` y el diff toca workflows, contrato de inventario, runtime HTTPS y pruebas. Se dejó #112 en draft y se añadió comentario: no fusionar ni forzar la rama hasta reconciliar los solapamientos, preservando la lógica de #52.

La CI histórica del HEAD `20e618aaeadc1866457f637522b755540f795dfa` de #52 terminó success en los tres workflows ([persistencia #38194392804](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38194392804), [transporte #38194392823](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38194392823), [esquema #38194392801](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38194392801)), pero es evidencia histórica de ese SHA, no del merge combinado. No lanzar re-runs hasta que cambie el HEAD de la rama combinada. #74 y #52 permanecen en draft; sin despliegue ni hardware físico.


## Hallazgo de lease en bandeja de tareas — observación inicial, SHA anterior (2026-10-23)

En la revisión de #52 se detectó que `_locked_task` trataba la lease de entrega de 30 s como requisito también para tareas `accepted` y `running`. Eso puede bloquear progreso/resultado tras 30 s aun cuando la asignación siga vigente. Se abrió la PR auxiliar #113 desde `feat/agent-task-inbox-v2`:
- Código: la lease de entrega solo se exige mientras el estado es `delivered`; se mantienen propiedad, `assignment_epoch` y lease de instancia para mutaciones posteriores.
- Prueba PostgreSQL: una tarea aceptada debe poder reportar progreso tras expirar la lease de entrega; la aceptación tardía después de expirar la lease debe seguir fallando.
- HEAD de #113: `3f096d0f461e8ef47077eb02153fb615001fe465`. Comparación con base: 2 commits adelante, 0 detrás.
- Estado en esa observación inicial: #113 draft y CI aún no aparecía. Esta fotografía fue supersedida por la sección «Revalidación final de lease y cobertura PostgreSQL» al final del documento, que registra el HEAD nuevo y ambos workflows en `success`.

La divergencia entre #74 y #52 sigue siendo independiente: #112 no es mergeable y requiere reconciliar el runtime (task_id y endpoints de bandeja más ACK cercado por versión), pruebas, schema y workflows. La comparación de nombres encontró 8 rutas compartidas: `.github/workflows/cluster-agent-transport.yml`, `.github/workflows/cluster-persistence-service.yml`, `docs/MANUAL_TRANSPORTE_HTTPS_AGENTES.md`, `packages/cluster-agent-transport/README.md`, `packages/cluster-agent-transport/pyproject.toml`, `packages/cluster-agent-transport/src/cluster_agent_transport/runtime.py`, `packages/cluster-agent-transport/tests/test_domain_handlers_postgres.py` y `packages/cluster-agent-transport/tests/test_runtime.py`. No seleccionar una versión completa de `runtime.py` sobre la otra; integrar el proveedor/ACK de inventario con los endpoints de bandeja, `task_id` y sincronización de recibos. Además, conservar el ajuste de #113 a `cluster-persistence-service.yml`: el workflow debe dispararse por cambios en `packages/cluster-agent-transport/**` y ejecutar `test_task_inbox_postgres.py`; la versión de workflow en #74 no tiene esa cobertura.


## Revalidación final de lease y cobertura PostgreSQL — 2026-10-23

El HEAD inicial de #113 (`3f096d0f461e8ef47077eb02153fb615001fe465`) pasó transporte #481 (63 passed), pero la auditoría encontró que `cluster-persistence-service.yml` no se disparaba por cambios en `packages/cluster-agent-transport/**`. Se amplió el filtro `pull_request`/`push` y se añadió una ejecución explícita de `packages/cluster-agent-transport/tests/test_task_inbox_postgres.py` contra PostgreSQL 16 desechable.

HEAD actualizado de #113: `21a5b4915086959eaf7dece15b6095de333612ce`.
- Transporte #482: `success`, **63 passed**, `pip check` limpio.
- Persistencia #609: `success`; prueba PostgreSQL de bandeja **1 passed**, suites de persistencia/guard/auth **32 + 12 + 54 passed**, `pip check` limpio.

La corrección y su cobertura de CI quedan validadas en esta rama, pero #113 sigue en draft. La sincronización #112 continúa `mergeable=false`; no fusionar ni ejecutar Android hasta reconciliar las dos ramas y validar el SHA integrado.

## Corrección de estado documental de #113 — 2026-10-23

La reconsulta del HEAD actual de la rama `fix/task-delivery-lease-after-accept-v1` confirma que la PR auxiliar #113 está **3 commits adelante y 0 detrás** de `feat/agent-task-inbox-v2`. El HEAD vigente es `21a5b4915086959eaf7dece15b6095de333612ce` (no el SHA inicial `3f096d0f...`).

Los dos workflows para el HEAD vigente terminaron `completed/success`:
- Transporte HTTPS [#40030143045](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40030143045): **63 passed**, comprobación de dependencias limpia.
- Persistencia [#40030143221](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40030143221): prueba PostgreSQL de bandeja **1 passed**, además de suites de persistencia/guard/auth **32 + 12 + 54 passed** y comprobación de dependencias limpia.

La ampliación del workflow de persistencia es parte de la PR y hace que cambios bajo `packages/cluster-agent-transport/**` ejecuten también la prueba PostgreSQL de bandeja. Queda corregida la nota anterior que decía que faltaba comprobar este workflow: ya está validado en el mismo HEAD. #113 permanece en draft porque la integración combinada con #74/#52 aún requiere reconciliar runtime, ACK cercado, task_id/endpoints, esquema, pruebas y workflows. No se ha fusionado la cadena ni se ha ejecutado Android.

## Primera reconciliación combinada #115 — 2026-10-23

Se creó la rama `fix/integrate-snapshot-task-inbox-fenced-ack-v1` desde `feat/agent-task-inbox-v2` y la PR draft [#115](https://github.com/D3ckardCain/Geelark-IA/pull/115) contra esa base. HEAD inicial: `87f6e1c0f9c3e108bf99e23a658a8ee76d958a7a`; compare: 10 commits adelante, 0 detrás, 9 archivos tocados.

Cambios combinados:
- Se conserva el runtime de bandeja: `claim_next_task`, `accept_task`, `reconcile`, `task_id` y sus rutas; no se reemplazó por el runtime reducido del proveedor.
- Se integra ACK cercado con `expected_status` y `expected_result`, incluyendo el `assignment_epoch` para la API de journal que lo admite. La API antigua sin firma de ACK versionado falla cerrada.
- Se mantiene el test PostgreSQL de la bandeja y se agrega test de ACK obsoleto.
- Se integra el contrato/inventario de módulos y pruebas de snapshots, además de las comprobaciones de rol PostgreSQL de solo lectura.
- El workflow de persistencia incorpora cambios de transporte y ejecuta `test_task_inbox_postgres.py`.
- Se conserva la dependencia `geelark-cluster-agent-auth` en el `pyproject.toml` del transporte; no se copió encima el archivo de proveedor que la omitía.

Estado: #115 es solo el primer HEAD combinado y permanece draft/no mergeable mientras GitHub recalcula. Todavía no se han confirmado los CI del SHA combinado. Próximo paso: inspeccionar ambos workflows, revisar fallos en cuanto aparezcan y corregir antes de considerar cualquier fusión. No fusionar #52/#74/#112, no desplegar ni ejecutar Android.

## Resultado CI del primer HEAD combinado #115 — 2026-10-23

El HEAD `87f6e1c0f9c3e108bf99e23a658a8ee76d958a7a` terminó con ambos workflows en `completed/success`:
- Transporte HTTPS [#40040284033](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040284033).
- Persistencia/PostgreSQL [#40040284060](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040284060), incluyendo `test_task_inbox_postgres.py`.

Corrección de alcance: el workflow contiene pasos opcionales para `cluster-master-admin`, pero se omitieron en este HEAD porque el paquete no está presente en la rama base de #115. Por tanto, el CI verde **no valida** todavía la implementación ni los permisos efectivos del rol readonly de Master Admin.

Nuevo hallazgo de integración, aún abierto: `AgentTransportRuntime.sync_receipt` puede usar `task_id` si el recibo lo expone, pero el `OperationReceipt` actual del journal local solo guarda `operation_id`, `instance_id`, nodo, epoch, estado y resultado. Cuando `task_id != operation_id`, un reintento offline puede enviar a `/agent/v1/tasks/{operation_id}/...` en vez de la ruta de tarea correcta. La suite unitaria que construye un recibo artificial con `task_id` no prueba persistencia real de esa relación. Antes de cerrar #115/#52, hay que añadir y probar la persistencia durable de `task_id` desde claim/aceptación hasta los recibos/reintentos, o definir y demostrar formalmente una invariancia que garantice IDs iguales. No se presume esa invariancia.

#115 sigue en draft. No fusionar #52/#74/#112, no desplegar a PCs físicas y no ejecutar Android.

## Avance de persistencia de task_id en #115 — validación pendiente

Se corrigió el hallazgo de reintentos offline en la rama combinada:
- Se tomó como base la versión del journal que ya incluye ACK cercado y migración v1→v3, y se completó la persistencia de `task_id` en aceptación, lectura, recibos pendientes y reintentos.
- El hash semántico del comando incluye `task_id` cuando está presente; los comandos legacy sin `task_id` mantienen el hash previo.
- Se amplió `test_journal.py` con persistencia/reapertura/ACK del recibo y `test_runtime.py` con un test SQLite real que exige que `task_id != operation_id` llegue a la ruta correcta.
- El workflow de transporte fija ahora el commit de journal `8403f9d84b603b9b59c3172a75df0b3681b9bad7`, que contiene la API versionada y el campo `task_id`.

El HEAD de la PR es `167a774d14ec66b4d6e1153e8a15d9bff68e4d61`. CI del HEAD actualizado en curso: transporte run #494 y persistencia run #621. La observación previa sobre pérdida de `task_id` queda **corregida en código pero no cerrada** hasta que esos workflows pasen, en particular las pruebas de migración del journal y la ruta real con IDs distintos.

## Endurecimiento adicional de ACK por epoch — 2026-10-23

En la revisión de #115 se detectó que la comparación de ACK por `expected_status` y `expected_result` no bastaba para distinguir dos asignaciones si el resultado coincidía. Se reforzó el contrato:
- `AgentJournal.mark_receipt_synced` exige `expected_assignment_epoch` y compara el epoch persistido junto con estado/resultado.
- El runtime transmite el epoch que originó el recibo.
- Se añadió prueba que simula ACK de epoch anterior y exige que el recibo siga pendiente.
- El workflow de transporte dejó de instalar el journal desde un SHA histórico fijo; ahora instala `cluster-agent-guard` desde el mismo checkout de la PR. Se incluyó `packages/cluster-agent-guard/**` en filtros pull_request y push para no omitir cambios al journal.

Commits de esta ronda en la rama de #115: `1a81d0cc7902ac765a9c0a3f8f328d3df9e9018d` (journal), `f2e9a2aec77c1c076e0804134777f6c87e7148ab` (runtime), `d7eaf3a836fa545a485272cf90eab11655e5ee50` (prueba journal), `c90e4960e55c08f512443ae49282503eac0c3468` (workflow).

Estado: el CI del HEAD combinado anterior fue satisfactorio en transporte y persistencia; esta ronda posterior aún requiere CI nuevo. No se fusiona ni se despliega hasta que termine.

## CI final de ACK cercado y task_id en #115 — 2026-10-23

HEAD de la ronda: `c90e4960e55c08f512443ae49282503eac0c3468`. Ambos workflows terminaron en `completed/success`:
- Transporte HTTPS #499: [40040796151](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040796151).
- Persistencia/PostgreSQL #626: [40040795989](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040795989), incluyendo prueba de bandeja PostgreSQL y `pip check`.

Se verificó en el mismo HEAD: journal ACK requiere `expected_assignment_epoch` + `expected_status` + `expected_result`; runtime transmite epoch; hay prueba de ACK de epoch antiguo y se mantiene la cobertura de `task_id` distinto de `operation_id`. El workflow de transporte ya no instala el journal desde un SHA fijo antiguo.

Límite que permanece: los pasos de `cluster-master-admin` y la prueba del rol PostgreSQL readonly se omitieron porque el paquete no existe en esta rama base. No afirmar seguridad readonly de PC-MASTER validada hasta integrar ese paquete desde la rama de Master apropiada y ejecutar sus pruebas. #115 permanece draft y no se fusiona con #52/#74/#112 todavía.

## Inclusión de corrección de lease de entrega de #113 en #115 — 2026-10-23

Se detectó que el primer HEAD de #115 todavía no llevaba la corrección de lease de entrega de la PR auxiliar #113. Se incorporó explícitamente:
- `domain_handlers.py`: la lease de entrega solo se exige si la tarea permanece en estado `delivered`; después de aceptar, la operación sigue protegida por propietario, `assignment_epoch` y lease de instancia.
- `test_task_inbox_postgres.py`: prueba PostgreSQL que acepta la tarea, hace expirar la lease de entrega y verifica que el progreso sigue permitido.
- Commits de integración: `62aab2e5424c0bd23c7f3a2ad6f7ae04c5477530` (handler) y `64f4a7f344ac94f15c75313171bdc2dc9218cd8f` (test).

CI #499/#626 validó el HEAD anterior, no este nuevo HEAD. La PR #113 sigue abierta como referencia hasta que #115 pase CI actualizado y se apruebe; no cerrar aún.

## CI verde de #115 tras integrar la corrección de lease — 2026-10-23

HEAD `64f4a7f344ac94f15c75313171bdc2dc9218cd8f` validado por ambos workflows:
- Transporte HTTPS #500: [40041029911](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041029911), success.
- Persistencia/PostgreSQL #627: [40041029952](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041029952), success, incluida `test_task_inbox_postgres.py`.

Esta ronda incorpora a la rama combinada el cambio que estaba separado en #113: la lease de entrega solo restringe tareas `delivered`; después de `accepted`, la validez sigue dependiendo de propiedad, epoch y lease de instancia. La prueba PostgreSQL acepta la tarea, expira la lease de entrega y exige que progreso siga funcionando. El test de aceptación tardía tras expiración permanece intacto.

La integración combinada está verde para transporte, journal/guard, auth, persistencia y bandeja PostgreSQL. Aún no se ha probado el rol readonly de Master Admin porque el paquete no existe en la base de #115; ese límite se mantiene explícito. #115 permanece draft/no fusionada. #113 se conserva abierta hasta aprobar/fusionar la integración combinada, evitando perder la corrección auxiliar antes de tiempo.
