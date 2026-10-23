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


## Hallazgo de lease en bandeja de tareas — 2026-10-23

En la revisión de #52 se detectó que `_locked_task` trataba la lease de entrega de 30 s como requisito también para tareas `accepted` y `running`. Eso puede bloquear progreso/resultado tras 30 s aun cuando la asignación siga vigente. Se abrió la PR auxiliar #113 desde `feat/agent-task-inbox-v2`:
- Código: la lease de entrega solo se exige mientras el estado es `delivered`; se mantienen propiedad, `assignment_epoch` y lease de instancia para mutaciones posteriores.
- Prueba PostgreSQL: una tarea aceptada debe poder reportar progreso tras expirar la lease de entrega; la aceptación tardía después de expirar la lease debe seguir fallando.
- HEAD de #113: `3f096d0f461e8ef47077eb02153fb615001fe465`. Comparación con base: 2 commits adelante, 0 detrás.
- Estado: #113 draft; CI aún no aparece en los resultados al registrar esta nota. No se ha fusionado ni desplegado. Revalidar CI antes de incorporar el fix a #52 y antes de reconciliar la pila con el proveedor de snapshots.

La divergencia entre #74 y #52 sigue siendo independiente: #112 no es mergeable y requiere reconciliar el runtime (task_id y endpoints de bandeja más ACK cercado por versión), pruebas, schema y workflows. No seleccionar una versión completa de `runtime.py` sobre la otra.


## Revalidación final de lease y cobertura PostgreSQL — 2026-10-23

El HEAD inicial de #113 (`3f096d0f461e8ef47077eb02153fb615001fe465`) pasó transporte #481 (63 passed), pero la auditoría encontró que `cluster-persistence-service.yml` no se disparaba por cambios en `packages/cluster-agent-transport/**`. Se amplió el filtro `pull_request`/`push` y se añadió una ejecución explícita de `packages/cluster-agent-transport/tests/test_task_inbox_postgres.py` contra PostgreSQL 16 desechable.

HEAD actualizado de #113: `21a5b4915086959eaf7dece15b6095de333612ce`.
- Transporte #482: `success`, **63 passed**, `pip check` limpio.
- Persistencia #609: `success`; prueba PostgreSQL de bandeja **1 passed**, suites de persistencia/guard/auth **32 + 12 + 54 passed**, `pip check` limpio.

La corrección y su cobertura de CI quedan validadas en esta rama, pero #113 sigue en draft. La sincronización #112 continúa `mergeable=false`; no fusionar ni ejecutar Android hasta reconciliar las dos ramas y validar el SHA integrado.
