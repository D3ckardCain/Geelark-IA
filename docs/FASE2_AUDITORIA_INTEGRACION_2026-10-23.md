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
| #112 | cerrada sin merge, supersedida | `feat/agent-task-inbox-v2` ← `406936ec` | El intento conflictivo se reemplazó por #115, que reconcilia proveedor, bandeja y ACK cercado; conservar historial, no reabrir salvo regresión. |
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

## Conflictos de sincronización #112 — inspección por archivo (2026-10-23)

Se compararon las versiones de los 10 archivos tocados por la PR auxiliar #112 entre la rama de proveedor (#74) y la rama de bandeja (#52). Se identificaron cambios exclusivos que deben conservarse:

| Archivo | Cambios que deben coexistir |
|---|---|
| `.github/workflows/cluster-agent-transport.yml` | Pin del journal compatible con ACK condicional y pruebas reproducibles; verificar contrato de API del SHA pinneado. |
| `.github/workflows/cluster-persistence-service.yml` | Triggers y tests del paquete Master Admin/rol de solo lectura + suite de persistencia/bandeja de tareas. |
| `docs/MANUAL_TRANSPORTE_HTTPS_AGENTES.md` | Advertencias de enrolamiento no operativo + documentación de ACK durable. |
| `docs/contracts/worker-module-inventory-v1.schema.json` | Restricciones de unicidad `maxContains` para módulos de inventario. |
| `packages/cluster-agent-transport/README.md` | Contratos de bandeja claim/accept/progress/result + ACK fail-closed del journal. |
| `packages/cluster-agent-transport/pyproject.toml` | Dependencia explícita de auth + cliente HTTP compatible con Starlette TestClient. |
| `packages/cluster-agent-transport/src/cluster_agent_transport/runtime.py` | Métodos de bandeja claim/accept + transmisión de recibos durables sin reescribir el journal durante reintentos. |
| `packages/cluster-agent-transport/tests/test_domain_handlers_postgres.py` | Pruebas de persistencia de salud reportada separada de salud derivada. |
| `packages/cluster-agent-transport/tests/test_runtime.py` | Pruebas de bandeja + ACK condicional `expected_status/expected_result`, ACK negativo y retry sin mutación local. |
| `packages/cluster-persistence/tests/test_status_snapshot.py` | Pruebas de separación entre salud reportada por Worker y salud derivada por Master. |

**Decisión aplicada:** no se intentó arreglar #112 mediante reemplazo total de archivos. Se cerró sin merge como supersedida por #115, que conserva la bandeja, el ACK cercado, el inventario y las pruebas de salud. HEAD #115 `f17bd3651b710ce2baee64cc98c0825c7bc96546`: transporte #502 **66 passed**, persistencia #629 **33 + 20 + 54 + 1 passed**, ambos `pip check` limpios y `mergeable=true`. #115 sigue en draft y requiere revisión final; la cobertura de Master Admin en la línea de bandeja es condicional porque ese paquete no existe en esa base. No se ejecutaron workflows manuales ni se fusionó ninguna PR.

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

Nota histórica anterior a la creación de #115: la divergencia entre #74 y #52 requería reconciliar runtime (`task_id`/endpoints de bandeja y ACK cercado), pruebas, schema y workflows. Esa reconciliación se realizó en la rama #115 y su HEAD final está registrado más abajo. La comparación de nombres encontró 8 rutas compartidas: `.github/workflows/cluster-agent-transport.yml`, `.github/workflows/cluster-persistence-service.yml`, `docs/MANUAL_TRANSPORTE_HTTPS_AGENTES.md`, `packages/cluster-agent-transport/README.md`, `packages/cluster-agent-transport/pyproject.toml`, `packages/cluster-agent-transport/src/cluster_agent_transport/runtime.py`, `packages/cluster-agent-transport/tests/test_domain_handlers_postgres.py` y `packages/cluster-agent-transport/tests/test_runtime.py`. No seleccionar una versión completa de `runtime.py` sobre la otra; integrar el proveedor/ACK de inventario con los endpoints de bandeja, `task_id` y sincronización de recibos. Además, conservar el ajuste de #113 a `cluster-persistence-service.yml`: el workflow debe dispararse por cambios en `packages/cluster-agent-transport/**` y ejecutar `test_task_inbox_postgres.py`; la versión de workflow en #74 no tiene esa cobertura.


## Revalidación final de lease y cobertura PostgreSQL — 2026-10-23

El HEAD inicial de #113 (`3f096d0f461e8ef47077eb02153fb615001fe465`) pasó transporte #481 (63 passed), pero la auditoría encontró que `cluster-persistence-service.yml` no se disparaba por cambios en `packages/cluster-agent-transport/**`. Se amplió el filtro `pull_request`/`push` y se añadió una ejecución explícita de `packages/cluster-agent-transport/tests/test_task_inbox_postgres.py` contra PostgreSQL 16 desechable.

HEAD actualizado de #113: `21a5b4915086959eaf7dece15b6095de333612ce`.
- Transporte #482: `success`, **63 passed**, `pip check` limpio.
- Persistencia #609: `success`; prueba PostgreSQL de bandeja **1 passed**, suites de persistencia/guard/auth **32 + 12 + 54 passed**, `pip check` limpio.

Nota histórica anterior a #115: #113 tenía su corrección validada de forma aislada, pero la integración con #74/#52 seguía pendiente. #115 incorporó posteriormente la corrección y pasó CI; véanse las secciones finales. No ejecutar Android: la puerta de seguridad #27 sigue vigente.

## Corrección de estado documental de #113 — 2026-10-23

La reconsulta del HEAD actual de la rama `fix/task-delivery-lease-after-accept-v1` confirma que la PR auxiliar #113 está **3 commits adelante y 0 detrás** de `feat/agent-task-inbox-v2`. El HEAD vigente es `21a5b4915086959eaf7dece15b6095de333612ce` (no el SHA inicial `3f096d0f...`).

Los dos workflows para el HEAD vigente terminaron `completed/success`:
- Transporte HTTPS [#40030143045](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40030143045): **63 passed**, comprobación de dependencias limpia.
- Persistencia [#40030143221](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40030143221): prueba PostgreSQL de bandeja **1 passed**, además de suites de persistencia/guard/auth **32 + 12 + 54 passed** y comprobación de dependencias limpia.

La ampliación del workflow de persistencia es parte de la PR y hace que cambios bajo `packages/cluster-agent-transport/**` ejecuten también la prueba PostgreSQL de bandeja. Queda corregida la nota anterior que decía que faltaba comprobar este workflow: fue validado en el mismo HEAD. #113 permaneció en draft en esa observación; luego se cerró sin merge como supersedida por #115, que incluye ese cambio. No se ha fusionado la cadena ni se ha ejecutado Android.

## Primera reconciliación combinada #115 — 2026-10-23

Se creó la rama `fix/integrate-snapshot-task-inbox-fenced-ack-v1` desde `feat/agent-task-inbox-v2` y la PR draft [#115](https://github.com/D3ckardCain/Geelark-IA/pull/115) contra esa base. HEAD inicial: `87f6e1c0f9c3e108bf99e23a658a8ee76d958a7a`; compare: 10 commits adelante, 0 detrás, 9 archivos tocados.

Cambios combinados:
- Se conserva el runtime de bandeja: `claim_next_task`, `accept_task`, `reconcile`, `task_id` y sus rutas; no se reemplazó por el runtime reducido del proveedor.
- Se integra ACK cercado con `expected_status` y `expected_result`, incluyendo el `assignment_epoch` para la API de journal que lo admite. La API antigua sin firma de ACK versionado falla cerrada.
- Se mantiene el test PostgreSQL de la bandeja y se agrega test de ACK obsoleto.
- Se integra el contrato/inventario de módulos y pruebas de snapshots, además de las comprobaciones de rol PostgreSQL de solo lectura.
- El workflow de persistencia incorpora cambios de transporte y ejecuta `test_task_inbox_postgres.py`.
- Se conserva la dependencia `geelark-cluster-agent-auth` en el `pyproject.toml` del transporte; no se copió encima el archivo de proveedor que la omitía.

Estado de esa observación inicial: #115 era el primer HEAD combinado y CI aún estaba pendiente. Esta fotografía quedó supersedida por las secciones finales, que registran el HEAD `f17bd365...`, ambos workflows en success y #112 cerrada sin merge como supersedida. #115 sigue en draft; no desplegar ni ejecutar Android.

## Resultado CI del primer HEAD combinado #115 — 2026-10-23

El HEAD `87f6e1c0f9c3e108bf99e23a658a8ee76d958a7a` terminó con ambos workflows en `completed/success`:
- Transporte HTTPS [#40040284033](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040284033).
- Persistencia/PostgreSQL [#40040284060](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40040284060), incluyendo `test_task_inbox_postgres.py`.

Corrección de alcance: el workflow contiene pasos opcionales para `cluster-master-admin`, pero se omitieron en este HEAD porque el paquete no está presente en la rama base de #115. Por tanto, el CI verde **no valida** todavía la implementación ni los permisos efectivos del rol readonly de Master Admin.

Nuevo hallazgo de integración, aún abierto: `AgentTransportRuntime.sync_receipt` puede usar `task_id` si el recibo lo expone, pero el `OperationReceipt` actual del journal local solo guarda `operation_id`, `instance_id`, nodo, epoch, estado y resultado. Cuando `task_id != operation_id`, un reintento offline puede enviar a `/agent/v1/tasks/{operation_id}/...` en vez de la ruta de tarea correcta. La suite unitaria que construye un recibo artificial con `task_id` no prueba persistencia real de esa relación. Antes de cerrar #115/#52, hay que añadir y probar la persistencia durable de `task_id` desde claim/aceptación hasta los recibos/reintentos, o definir y demostrar formalmente una invariancia que garantice IDs iguales. No se presume esa invariancia.

Nota histórica de la primera revisión combinada: #115 seguía en draft. #112 fue cerrada después sin merge como supersedida por #115. La integración funcional sigue sin fusionarse; no desplegar a PCs físicas ni ejecutar Android.

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

Límite que permanece: los pasos de `cluster-master-admin` y la prueba del rol PostgreSQL readonly se omitieron porque el paquete no existe en esta rama base. No afirmar seguridad readonly de PC-MASTER validada hasta integrar ese paquete desde la rama Master apropiada y ejecutar sus pruebas. #115 permanece draft y no se ha fusionado con #52/#74; #112 quedó cerrada sin merge como supersedida.

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

La integración combinada está verde para transporte, journal/guard, auth, persistencia y bandeja PostgreSQL. Aún no se ha probado el rol readonly de Master Admin porque el paquete no existe en la base de #115; ese límite se mantiene explícito. #115 permanece draft/no fusionada. #113 se conservó abierta en ese momento para no perder la corrección; posteriormente se cerró sin merge como supersedida por #115 después de verificar equivalencia del handler/test y CI verde.

## Documentación de transporte alineada con el ACK/lease final — 2026-10-23

Se corrigió `packages/cluster-agent-transport/README.md`, que aún describía la API antigua `mark_receipt_synced(operation_id)` y no precisaba la frontera de la lease. Ahora documenta los argumentos obligatorios `expected_assignment_epoch`, `expected_status` y `expected_result`, el fallo cerrado de APIs antiguas, y que la lease de entrega solo bloquea aceptación mientras el estado sea `delivered`. Commit: `f510356c9796e67270a23c763018c6a1de84dbbd`. Este cambio vuelve a disparar CI de transporte y debe validarse en el HEAD documental nuevo.

## CI del HEAD final con documentación alineada — 2026-10-23

Tras actualizar el README para describir correctamente el ACK versionado y la frontera de la lease, el HEAD `f510356c9796e67270a23c763018c6a1de84dbbd` pasó de nuevo ambos workflows:
- Transporte HTTPS #501: [40041192926](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041192926), success.
- Persistencia/PostgreSQL #628: [40041193006](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041193006), success.

La documentación ya no recomienda la API antigua de ACK. Se actualizó la descripción de #115 a estos checks. La PR sigue draft y no fusionada; el rol readonly de Master Admin sigue fuera de esta rama y no se declara validado.

## Uso autoritativo de task_id en reportes inmediatos — 2026-10-23

Se cerró otro borde del runtime: antes, los reintentos offline recuperaban `task_id` del journal, pero `report_progress`/`report_result` podían usar `operation_id` si el llamador omitía el argumento opcional. Ahora el runtime deriva `task_id` del recibo durable cuando está disponible y rechaza un ID explícito que no coincida con el guardado. Pruebas nuevas cubren progreso/resultado inmediatos con `task_id != operation_id` y el rechazo de discrepancia.
- Runtime: `991302171d95d6eddcd5b23bc177e13233516cd8`.
- Pruebas: `f17bd3651b710ce2baee64cc98c0825c7bc96546`.

Este cambio crea un HEAD nuevo después de CI #501/#628; no declararlo validado hasta que los dos workflows terminen de nuevo.

## CI final de task_id autoritativo en reportes en vivo — 2026-10-23

HEAD `f17bd3651b710ce2baee64cc98c0825c7bc96546` pasó los dos workflows:
- Transporte HTTPS #502: [40041315719](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041315719), success.
- Persistencia/PostgreSQL #629: [40041315731](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40041315731), success, incluida la prueba de bandeja PostgreSQL.

Se confirma que el runtime usa el `task_id` del recibo durable en reportes inmediatos si se omite el argumento, y rechaza discrepancias explícitas; los tests de progreso/resultado con `task_id != operation_id` pasaron. La documentación, la corrección de lease de entrega y el ACK cercado por epoch/estado/resultado también están incluidos en este HEAD. #115 permanece draft y no fusionada. Los pasos de Master Admin readonly siguen omitidos porque ese paquete no existe en esta rama base.


## Cierre de PR auxiliares #112/#113 — 2026-10-23

- #112 se cerró sin merge como supersedida por #115 tras inspeccionar sus 10 archivos de solapamiento.
- #113 se cerró sin merge como supersedida por #115 después de comparar `domain_handlers.py` y `test_task_inbox_postgres.py` (contenido idéntico en ambas ramas) y verificar que el workflow de #115 conserva los filtros y la prueba PostgreSQL.
- La PR activa de integración es #115, HEAD `f17bd3651b710ce2baee64cc98c0825c7bc96546`, mergeable=true, transporte #502 (**66 passed**) y persistencia #629 (**33 + 20 + 54 + 1 passed**), `pip check` limpio. Sigue en draft y no fusionada.
- La seguridad de Master Admin/rol PostgreSQL readonly no queda validada por esta línea porque el paquete no está presente en su base; debe comprobarse en la línea #104. La issue #27 sigue bloqueando la ejecución física de redroid.


## Revalidación de la línea Windows #87/#103/#104 — 2026-10-23

La comparación de los cinco archivos compartidos entre #103 y #104 confirma divergencia funcional, no duplicación exacta:
- `auth.py`: #103 usa `whoami.exe` + `icacls.exe` con timeout de 30 s; #104 usa PowerShell para aplicar ACL secuenciales/verificadas, timeout de 8 s y comprobación posterior con `icacls`. No portar el método antiguo sobre #104.
- `app.py`: #103 usa `health_state AS reported_health_state`; #104 consulta la columna `reported_health_state` explícita, evitando confundir salud derivada y reportada.
- `tests/test_app.py` / `tests/test_auth.py`: los fixtures de #103 corresponden a la estrategia antigua; #104 contiene pruebas más amplias de ACL PowerShell y seguridad de solo lectura.
- Workflow: #103 añade un job Windows específico; #104 mantiene pruebas adicionales del rol PostgreSQL readonly. Reconciliar cobertura al integrar.

La #87 aporta el lanzador/configurador Windows; #104 aporta el panel web/API autenticado. #103 no se cierra como duplicada: se mantiene como corrección apilada pendiente de reconciliación. El objetivo es conservar el lanzador sin reintroducir la implementación antigua del backend/ACL. No se cambió ninguna base ni se fusionaron ramas.

## Revisión adicional de divergencia de ramas — 2026-10-23

### Evidencia comprobada

- PR #104: head `fix/windows-ca-test-fixture-v1`, commit `75764c435f488f617a07c0003ce088829e6dbd41`, base `feat/master-status-snapshot-provider-v1`.
- PR #115: head `fix/integrate-snapshot-task-inbox-fenced-ack-v1`, commit `f17bd3651b710ce2baee64cc98c0825c7bc96546`, base `feat/agent-task-inbox-v2`.
- La comparación directa de ambos heads devuelve `diverged`, con 57 commits exclusivos de la rama de tareas y 130 commits exclusivos de la rama PC-MASTER en la comparación de GitHub; merge base `a8ce049458e94ae2587caeb8a42269a0b094b09a`.
- El diff directo incluye 27 rutas, entre ellas workflows, migración y smoke SQL de bandeja, journal SQLite, handlers/runtime, contratos y pruebas PostgreSQL. Por tanto no es correcto resolver la integración cambiando únicamente la base de la PR.
- PR auxiliar #116 fue cerrada sin merge porque GitHub informó `mergeable=false`; era un registro de integración, no una resolución de código.

### Decisiones de seguridad

1. No fusionar #104 ni #115 por separado como si la otra línea no existiera.
2. Preservar los archivos exclusivos de PC-MASTER: panel web, autenticación local, TLS, ACL NTFS y pruebas negativas del rol PostgreSQL de solo lectura.
3. Preservar la bandeja durable: migración `0005_agent_task_inbox.sql`, smoke SQL, journal con `task_id`, fencing del ACK por epoch/estado/resultado, y operaciones claim/accept/progress/result.
4. Resolver semánticamente al menos `domain_handlers.py`, `runtime.py`, `journal.py`, `cluster-agent-transport.yml`, `cluster-persistence-service.yml` y `MANUAL_TRANSPORTE_HTTPS_AGENTES.md`.
5. La suite de persistencia combinada debe mantener los jobs Windows ACL, suite raíz y verificaciones negativas del rol lector; además debe ejecutar las pruebas PostgreSQL de la bandeja. No reducir silenciosamente los controles existentes.
6. La CI verde de cada head separado no demuestra que el head combinado compile ni que pase las pruebas.
7. No iniciar listeners, despliegues ni pruebas en hardware físico. La aceptación manual de PC-MASTER (issue #77) sigue siendo un bloqueo separado.

### Próximos pasos verificables

- Crear un merge real de Git con ambos heads como padres y una única resolución de árbol, conservando todo el contenido exclusivo de PC-MASTER.
- Ejecutar CI en ese head combinado y revisar los logs de cada job; no reutilizar checks de commits anteriores como prueba de integración.
- Mantener la PR de integración en draft hasta que el diff y la CI del head combinado estén validados.
- Registrar el resultado manual del panel en la issue #77 antes de aceptar el módulo.

**Estado al cierre de esta revisión:** integración no resuelta; no se ha fusionado ni desplegado ningún cambio.

## Reconciliación combinada ejecutada y CI — actualización 2026-10-23 (UTC 2026-10-24)

### PR de integración

Se creó la [PR #117](https://github.com/D3ckardCain/Geelark-IA/pull/117), rama `feat/pc-master-task-inbox-reconciliation-v1`, en draft y sin merge. Su historial contiene un merge real de PC-MASTER (#104) y la bandeja/snapshot/ACK (#115), seguido de la incorporación del head actual del proveedor (#74).

- HEAD combinado: `d443a4b59a7fcdb29b13d9d9e113a10edf686024`.
- GitHub informa `mergeable=true`; la comparación contra la base actual `406936ecef181eb4a7a34d6e25316079ee8b29ea` muestra 180 commits por delante y 0 por detrás.
- Diff: 48 archivos añadidos/modificados; **ningún archivo eliminado**.
- Se preservaron el paquete `cluster-master-admin`, panel, autenticación local, TLS, ACL Windows y probes negativos del rol PostgreSQL lector.
- Se incorporaron migración y smoke SQL de la bandeja, journal con `task_id`, handlers/runtime de tareas y pruebas PostgreSQL.
- El workflow de persistencia conserva Windows ACL y suite raíz, ejecuta el test PostgreSQL de bandeja y activa suite raíz para esta rama. El workflow HTTPS valida el código actual sin fijar un checkout histórico del journal.

### CI del HEAD combinado

Los tres workflows terminaron en `success` sobre el mismo HEAD `d443a4b59a7fcdb29b13d9d9e113a10edf686024`:

- [Transporte HTTPS #40056081545](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40056081545): **133 passed**, `pip check` limpio.
- [Migraciones/invariantes PostgreSQL #40056081543](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40056081543): success.
- [Persistencia + Windows ACL + suite raíz #40056081523](https://github.com/D3ckardCain/Geelark-IA/actions/runs/40056081523):
  - Suite raíz: **310 passed, 2 skipped**, `pip check` limpio.
  - Windows ACL: **50 passed, 8 skipped**, `pip check` limpio.
  - Persistencia: **33 passed**; guard: **20 passed**; autenticación: **54 passed**; Master Admin: **70 passed, 2 skipped**; prueba PostgreSQL de bandeja: **1 passed**; `pip check` limpio.
- Los mensajes PostgreSQL de error que aparecen en logs corresponden a pruebas negativas/inyección de fallos esperadas; todos los jobs finalizaron en éxito.

### Qué sigue pendiente

1. Revisión humana del diff y de los contratos de tareas/ACK.
2. Aceptación manual de PC-MASTER en el Windows real según issue #77. CI no demuestra ACL/TLS/configuración efectiva del equipo del usuario.
3. Resolver el orden de la pila: #117 sigue basada en la rama del proveedor snapshot (#74), mientras #52 y las PR descendientes #57/#67/#85 siguen abiertas. No fusionar fuera de orden ni asumir que sus ramas descendientes ya contienen el nuevo HEAD combinado.
4. Mantener #117 en draft hasta completar la revisión humana y resolver la estrategia de la pila. No desplegar, no conectar bases productivas y no ejecutar Android/ADB/shell en hardware físico.

**Estado actualizado:** integración de código entre PC-MASTER, snapshots y bandeja validada por CI en un único HEAD; aceptación del panel y orden de integración de la pila siguen pendientes.

## Auditoría de la siguiente pila de agente — después de #117

La siguiente línea funcional no forma parte de la PR #117 y no debe darse por integrada:

- #57 — ciclo de vida y sincronización durable (`feat/agent-lifecycle-sync-inbox`), base #52; 9 rutas en su diff directo con #117, incluida la nueva implementación `lifecycle.py` y pruebas de sincronización.
- #67 — supervisor/heartbeat (`feat/agent-supervisor-heartbeat-v2`), base #57; GitHub lo marca `mergeable=false` en su propia pila actual. Añade bootstrap, conectividad, credenciales, supervisor y pruebas asociadas.
- #85 — reconciliación, retención y guard de frescura (`feat/agent-reconciliation-retention-clean-v2`), base #67; añade migraciones `0006_agent_reconciliation_reports.sql` y `0007_agent_storage_retention.sql`, handlers/pruebas de reconciliación y retención.

La comparación de cada rama descendiente contra #117 indica divergencia de historial y muestra 9/30/50 rutas cambiadas, respectivamente. Eso no demuestra que las funcionalidades sean incompatibles, pero sí que sus CI históricas no validan el árbol combinado actual. En particular, #85 modifica `journal.py`, `runtime.py`, `test_task_inbox_postgres.py` y workflows; se requiere merge semántico para conservar el ACK cercado y `task_id` durable de #117 junto con las nuevas funciones de ciclo de vida/supervisor/reconciliación.

**Acción segura:** no fusionar ni cerrar #57/#67/#85 por ahora. Mantenerlas draft, revisar el diff y sus dependencias después de completar la aceptación manual de PC-MASTER en #77. No crear otra PR combinada grande antes de aceptar el módulo actual.

