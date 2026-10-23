## Revalidación final de PRs y CI — 2026-10-23

Consulta en vivo de GitHub:
- **38 Issues abiertas, 10 cerradas y 23 PR abiertas** en la consulta más reciente del 2026-10-23; todas las PR abiertas están en draft.
- **#101 (observación histórica, 2026-10-23 temprano):** HEAD `b84da93881f5869e8832e5888e5dce02433e85cc` no tenía workflows asociados en esa consulta. Fue reemplazado por HEAD `043a4e23efd063949577f758eacc326d74bb7ce5`, que posteriormente pasó transporte #479/#478, esquema #308 y persistencia #607.
- **#74** HEAD `df34e00ec18eb99ef3d53e99513ef625b42d2a58`, base #101: GitHub la muestra mergeable, pero no integrar mientras #101 siga en conflicto.
- **#52** HEAD `20e618aaeadc1866457f637522b755540f795dfa`: `mergeable=false`; resultados CI anteriores exitosos no eliminan el conflicto.
- **#57** HEAD `a27922c2e773b3e3b01f368931e14b389490c2f6`: mergeable en metadatos, pero depende de #52 y no debe integrarse antes de resolver la cadena.
- **#67** HEAD `776a3d54fb28af269b405658541a13f57d3c2537`: `mergeable=false`; CI anterior exitosa no valida la integración con la base actual.
- **#85** HEAD `3ef9f065c6228e337c9509e43be5484b3de11c76`: mergeable en metadatos, pero depende de #67.
- **#104** HEAD `75764c435f488f617a07c0003ce088829e6dbd41`: transporte HTTPS run #473 y persistencia run #602 en `success`; sigue en draft y requiere aceptación manual #77 y reconciliación del stack.
- **#103** HEAD `31ec5abceae6e38279d6be1e19e94683e0ea00ea`: persistencia run #574 en `success`; no se observó workflow de transporte para ese SHA en la consulta.
- **#87** HEAD `386da22f1dca3f2a1f489e2d9a898d30350d3eb0`: persistencia run #578 cancelada. Su ascendencia continúa basada en la rama de #76 cerrada sin merge; reconciliar con #104 sin retarget automático.
- **#48** HEAD `f2301e9b1673c57b74a9d625f3f4788f603a83ed`: transporte #471 pasó 54 pruebas, 1 warning y `pip check` limpio. La rama sigue draft por el orden de integración y revisión de seguridad, no por ese workflow.

**Decisión de auditoría:** no cerrar ni fusionar las PR apiladas únicamente por CI verde. La acción de mayor valor es resolver el conflicto de #101 primero, volver a validar su nuevo SHA y continuar base → descendiente (#101 → #74 → #52 → #57 → #67 → #85). Mantener aparte la línea Windows (#87/#103/#104) hasta reconciliar su ascendencia. La prioridad de runtime permanece redroid; #27 continúa como bloqueo de seguridad físico.

## Corrección de prioridad de motor Android — 2026-10-23

La prioridad acordada es redroid primero. La documentación que nombraba AOSP Cuttlefish como primer candidato fue corregida en `docs/COMPARATIVA_MOTORES_ANDROID.md`, `docs/decisiones/ADR-002-ESTRATEGIA-MOTOR-ANDROID.md`, `docs/ARQUITECTURA_TECNOLOGICA_PROPUESTA.md`, `docs/ESTADO_PROYECTO.md`, `docs/PLAN_TRABAJO.md` y `README.md`. También se corrigió la Issue #11 y se aclaró #27: redroid es prioritario, pero continúa bloqueado para ejecución física hasta demostrar mitigación en la imagen/digest exactos. Cuttlefish queda como contingencia, no como prioridad. No se instaló ni ejecutó ningún motor.

# Auditoría de higiene del repositorio GitHub — actualización 2026-10-23

## Objetivo

Mantener el repositorio GeeLark-IA alineado con el alcance vigente: PC-MASTER Windows, PC-WORKERS físicos con Debian 13 previsto, un adaptador Android agnóstico y selección de motor basada en evidencia. El objetivo operativo obligatorio es 0 USD.

## Estado y reglas

- No confundir una PR abierta con código integrado o aceptado.
- No cerrar un bloqueo de seguridad por tener documentación escrita; exigir evidencia reproducible.
- No borrar ramas o historial de commits para ocultar decisiones anteriores. La documentación operativa sí debe reflejar el alcance actual.
- Las tareas de autenticación, enrolamiento, transporte, persistencia, despacho, reconciliación, observabilidad y automatización permanecen porque son componentes necesarios del plano de control.
- La estrategia vigente es redroid primero y como único motor Android en preparación. La ruta manual QEMU + Android-x86 + VNC en WSL2 está retirada; Android Emulator es referencia de compatibilidad y Cuttlefish queda como contingencia, no como candidato activo. El contrato permanece agnóstico y no se permite instalación física de redroid hasta resolver #27 con mitigación verificable para la imagen/digest exactos.
- No se han instalado paquetes ni modificado discos de los WORKERS durante esta limpieza documental.

## Cambios realizados en la rama de limpieza

- README actualizado con el alcance y los enlaces vigentes.
- ADR-001 y ADR-002 alineados con PC-MASTER Windows, Debian 13 previsto y motor Android intercambiable; ADR-002 retira la ruta QEMU + Android-x86 + VNC en WSL2.
- Arquitectura tecnológica y de clúster actualizadas.
- Plan de trabajo actualizado con fases y puertas de aceptación.
- Evaluación de redroid conservada como prioridad y bloqueo de seguridad independiente; Cuttlefish queda solo como contingencia futura y no como candidato activo.
- Catálogo funcional y matriz de paridad conservados como documentación de funciones públicas de GeeLark, no como selección de motores.
- Issue #8 cerrada como decisión de alcance completada; la issue #27 permanece abierta.
- PR #108 integró la preparación del worker y el diagnóstico de solo lectura; PR #109 integró la limpieza de alcance.

## Criterios antes de integrar

1. Revisar que todos los enlaces internos resuelvan en el árbol final de main.
2. Revisar diff completo para asegurar que no se han eliminado contratos, tareas o documentación necesaria del plano de control.
3. Ejecutar comprobaciones de formato/enlaces localmente cuando el árbol esté disponible; no lanzar workflows solo para reconstruir resultados ya registrados.
4. Revisar CI del HEAD exacto y dependencias de PR apiladas.
5. Mantener la issue #27 abierta hasta que exista evidencia de mitigación sobre la imagen redroid exacta.
6. No declarar redroid instalado, seguro, probado en hardware físico ni escalable hasta que esas pruebas se ejecuten y documenten.

## Revalidación de continuidad — 2026-10-23

- PR #106 (auditoría de continuidad), #108 (preparación segura de WORKER-01) y #109 (consolidación del alcance PC-MASTER/redroid) están fusionadas en `main`.
- PR #86 se cerró sin merge por cambio de alcance; su documentación histórica se conserva, pero no es fuente operativa vigente. Su valor funcional debe recuperarse solo si el alcance de producto vuelve a exigirlo.
- Issue #64 se cerró como decisión resuelta: Windows en PC-MASTER y Debian 13 previsto para WORKERS. No significa que PXE, instalación o pruebas físicas estén implementadas.
- Recuento consultado el 2026-10-23 por la mañana: **38 Issues abiertas, 10 cerradas, 21 PR abiertas**. La revalidación posterior encontró 23 PR abiertas tras crear #112 y #113; el recuento cambia con nuevas acciones y no es criterio de aceptación.
- La cadena de PR de clúster sigue mayormente en draft. La CI de una rama no acredita que el stack esté integrado, aceptado manualmente ni probado en hardware.
- #24 se limita a caché local de artefactos; #92 a aprovisionamiento Debian 13. Se añadieron comentarios para evitar duplicación. #27 sigue bloqueando la ejecución física de redroid.
- La auditoría de origen PC-MASTER (#88) sigue pendiente de comparar el archivo/acceso directo local; GitHub identifica la rama candidata, pero no prueba qué ejecutable se inició en Windows.
- Revalidación de CI en ramas apiladas: #104 HEAD `75764c435f488f617a07c0003ce088829e6dbd41` pasó transporte (#473, 125 pruebas) y persistencia/suite raíz (#602: 293 passed/3 skipped; Windows ACL 50/8 skipped; `pip check` limpio). Esto no sustituye aceptación manual (#77).
- Observación histórica de HEADs consultados el 2026-10-23 temprano: #101 `b84da93881f5866e8832e5888e5dce02433e85cc` no tenía workflows; #87 `386da22f1dca3f2a1f489e2d9a898d30350d3eb0` solo devolvió persistencia cancelada (#578); #103 `31ec5abceae6e38279d6be1e19e94683e0ea00ea` devolvió persistencia exitosa (#574) pero no transporte en esa consulta. No extrapolar esos resultados a HEADs posteriores.
- #87/#103 heredan una base vinculada a la PR #76 cerrada sin merge; reconciliar la ascendencia con #104 antes de integrar. No retargetear automáticamente sin comparar diffs.

## Registro

Esta actualización reemplaza recuentos históricos de Issues/PR que podrían haber cambiado. El historial de GitHub conserva las decisiones anteriores; los documentos operativos actuales deben seguir esta actualización.

## Continuación de auditoría — 2026-10-23

### Conteo actual y alcance

- Consulta global de GitHub más reciente del 2026-10-23: **23 PR abiertas, todas en draft**. Los recuentos anteriores de 21 y 27 corresponden a consultas previas.
- Issues abiertas: **38**. Issues cerradas consultadas: **10**.
- No se fusionó ni eliminó ninguna PR durante esta continuación; no se borraron ramas. No se lanzaron workflows manuales.
- PR #108 y #109 ya están fusionadas en `main`; PR #106 también aparece registrada como fusionada en la auditoría previa. No tratarlas como pendientes.
- La implementación candidata de PC-MASTER sigue fuera de `main` (#87/#103/#104).

### Issues revisadas y criterio de cierre

- **#39 — ya cerrada en GitHub:** sus requisitos siguen siendo criterios de seguridad para PR #40/#42/#44/#48; cerrar la fase de diseño no significa que todo el transporte esté integrado ni que haya pruebas físicas.
- **#64 — cerrada en esta auditoría:** decisión de Windows PC-MASTER + Debian 13 WORKERS registrada. No implica que PXE, aprovisionamiento automático o motor Android estén implementados.
- **#20 — permanece abierta correctamente:** nueve pruebas del prototipo histórico están marcadas completas, pero autenticación real, dispatcher, recuperación/reconciliación y evaluación de migración oficial continúan sin completar. No confundir el prototipo PR #19 con el esquema actual #32.
- **#29, #31, #33, #41, #46, #55, #62, #65, #69 y #71 — permanecen abiertas:** describen trabajo de contratos, persistencia, transporte, sincronización, retención, autorización o salud derivada que no se demuestra terminado/integrado.
- **#63 — permanece abierta:** las herramientas del repositorio no permiten verificar el saldo/facturación de la cuenta. No se iniciaron workflows manuales ni configuraron runners de pago. El propietario debe revisar el panel de uso si necesita certificar el coste real de Actions.
- **#88 — permanece abierta:** GitHub identifica las ramas/PR candidatas, pero no demuestra qué acceso directo/archivo ejecutó el equipo Windows. La comparación local sigue pendiente; no instalar ni iniciar el panel desde esta issue.
- **#89/#91 — permanecen abiertas:** la corrección candidata de Windows/suite está verde en el HEAD de #104, pero no está integrada en la rama base; #77 conserva la aceptación manual.
- **#77 — permanece abierta:** aceptación manual en el PC-MASTER real pendiente; CI no sustituye la inspección de ACL/certificados/rutas del equipo.
- **#86 — cerrada sin merge:** su rama contiene documentación histórica de investigación funcional/RPA que no debe borrarse del historial. Sus documentos exclusivos no se consideran integrados por defecto. Reconciliar el catálogo, investigación funcional, matriz de paridad y especificación RPA con el alcance vigente PC-MASTER Windows + Debian 13 + motor intercambiable; redroid es el primer motor en preparación y permanece bloqueado por #27; Cuttlefish solo queda como contingencia futura.

### Duplicados, prototipos y ramas apiladas

- **#70 se cerró como supersedida el 2026-10-23, sin merge.** Su maqueta HTML ficticia y contrato se solapan con la línea activa: #74 contiene proveedor/schema/ejemplo y #104 contiene panel autenticado/API. No se integró el manual antiguo ni el prototipo; la rama permanece como referencia recuperable. Esto no acepta el panel, que sigue pendiente de #77 y #88.
- **#87 → #103** conserva el lanzador Windows y correcciones específicas, pero su ascendencia usa la rama antigua de #76 cerrada sin merge. Reconciliar con #104 antes de integrar para no reintroducir backend antiguo. No cambiar la base automáticamente.
- Cadena de implementación de agentes/control registrada en #50: #38 → #42 → #44 → #47 → #48 → #101 → #74 → #52 → #57 → #67 → #85. No integrar fuera de orden; checks verdes por SHA no resuelven por sí solos conflictos/topología.
- Los prototipos históricos (#19 y #70) deben seguir diferenciados de los servicios operativos; #70 se cerró sin merge como supersedida y las pruebas de un prototipo no son aceptación de producción.

### Evidencia reciente que permanece vigente

- PR #48 HEAD `f2301e9b1673c57b74a9d625f3f4788f603a83ed`: transporte HTTPS **54 passed, 1 warning**, `pip check` limpio; workflow #471 success.
- PR #104 HEAD `75764c435f488f617a07c0003ce088829e6dbd41`: persistencia **293 passed / 3 skipped**, Windows ACL **50 passed / 8 skipped**, asignaciones **33 passed**, guard/journal **12 passed**, auth **70 passed / 2 skipped**, transporte **125 passed**; `pip check` limpio. Sigue en draft y sin merge.
- La rama de #104 incluye ADR-007 de autenticación local; #70 conserva su ADR-006 únicamente en la rama histórica cerrada sin merge. La antigua colisión ADR-005 se corrigió en #104 y el Issue #105 está cerrado.
- Ninguno de estos resultados acredita instalación en hardware, acceso remoto seguro ya desplegado, ni ejecución real de instancias Android.


### Corrección de estrategia Android — 2026-10-23

- Se actualizaron Issues #3, #10, #11, #12, #24 y #92 para corregir textos envejecidos que ponían a Cuttlefish por delante de redroid. La decisión vigente es **redroid primero y único motor Android en preparación**; el adaptador permanece agnóstico.
- #24 mantiene únicamente la caché local de artefactos verificados; #92 mantiene únicamente el aprovisionamiento Debian 13. No ejecutar instalación de runtime hasta superar las puertas de licencia, seguridad y aceptación.
- #27 permanece abierta como bloqueo obligatorio de redroid. La prioridad no implica aprobación de seguridad ni autoriza instalación física; la puerta solo se levanta con evidencia reproducible sobre la imagen/digest exactos.
- Se cerró #64 como decisión resuelta (Windows en PC-MASTER, Debian 13 previsto en WORKERS). No se cerró ninguna tarea de implementación física por inferencia.


**Documento complementario:** [Auditoría de continuidad GitHub — 2026-10-22](AUDITORIA_GITHUB_CONTINUIDAD_2026-10-22.md) resume decisiones de alcance y continuidad; este archivo conserva el registro detallado de higiene, issues, PRs, conflictos y CI.


## Higiene de documentación funcional — 2026-10-23

- Los documentos `CATALOGO_FUNCIONAL_GEELARK.md`, `INVESTIGACION_FUNCIONAL_GEELARK.md` y `MATRIZ_PARIDAD_GEELARK.md` conservaban un corte de fuentes del 2026-10-09. Se añadieron avisos visibles de frescura: el alcance de motor fue revalidado el 23-oct (redroid primero; #27 bloqueante), pero la investigación funcional no se declara actualizada ni exhaustiva. No se alteraron las conclusiones históricas ni se marcó paridad sin pruebas.
- Issues #3 y #6 se mantienen separadas: #3 controla la Fase A y aceptación de la matriz; #6 detalla el catálogo de funciones. Se documentó la distinción en ambas issues; no son duplicados exactos.
- Los informes `AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md` y `AUDITORIA_GITHUB_CONTINUIDAD_2026-10-22.md` se conservan como documentos complementarios (detalle de higiene/CI frente a resumen de continuidad), con enlaces cruzados; no se borró historial.
- No se cerraron issues de implementación pendientes por inferencia. Se cerró #64 porque el texto declaraba la decisión de sistema base/roles como resuelta; no significa que Debian, PXE o redroid estén instalados.

## Revalidación del stack de tareas — 2026-10-23
- PR #101 y #74 cambiaron de HEAD tras la auditoría anterior. Se verificó CI actual: #101 HEAD `043a4e23efd063949577f758eacc326d74bb7ce5` con transporte #479/#478, esquema #308 y persistencia #607 en `success`; #74 HEAD `406936ecef181eb4a7a34d6e25316079ee8b29ea` con transporte #480 y persistencia #608 en `success`.
- PR #112 intenta sincronizar el proveedor de snapshots a la rama de bandeja; la API de GitHub informa `mergeable=false`. No fusionar hasta resolver conflictos y revisar el diff completo.
- PR #113 corrige el uso de lease de entrega tras aceptación. HEAD `21a5b4915086959eaf7dece15b6095de333612ce`: transporte #482 `success` (**63 passed**, `pip check` limpio); persistencia #609 `success` (prueba PostgreSQL de bandeja **1 passed**, suites persistencia/guard/auth **32 + 12 + 54 passed**, `pip check` limpio). Se amplió el filtro del workflow para que los cambios de `cluster-agent-transport` ejecuten esta prueba PostgreSQL.
- La cadena no se considera integrada: mantener #52/#57/#67/#85 y #112/#113 en draft hasta resolver dependencias, CI completa y aceptación manual. No se despliega ni se ejecuta Android.
