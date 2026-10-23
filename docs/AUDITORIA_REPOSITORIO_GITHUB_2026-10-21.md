# Auditoría de higiene del repositorio GitHub — 21–22 de octubre de 2026

## Resumen ejecutivo

Esta auditoría revisa el estado visible del repositorio `D3ckardCain/Geelark-IA` en GitHub. El objetivo es reducir duplicados, corregir referencias envejecidas y separar trabajo terminado, candidato en rama, integrado y pendiente de aceptación.

**No confundir una PR con código integrado.** La rama predeterminada `main` contiene actualmente README y documentación; no contiene todavía paquetes de implementación, pruebas, migraciones ni workflows. La implementación técnica que se está validando vive en ramas de PR. Por tanto, el código de una PR abierta no se debe describir como integrado ni como producto aceptado.

## Inventario observado

- Rama predeterminada: `main`.
- Árbol recursivo de `main` al inicio de la auditoría: 28 archivos de texto/Markdown contando README y documentos; no aparecen `.github/workflows/`, `packages/`, `db/`, `tests/` ni `prototypes/`.
- Issues abiertos encontrados en la consulta inicial: 43; el Issue #2 se cerró como completado tras confirmar que el alcance/reglas generales están documentados. Issues abiertos: 40 en la última consulta global (2026-10-22); #105 se cerró tras resolver su colisión inicial, #64 se cerró como decisión resuelta y #107 se cerró después de confirmar CI y separar los manuales.
- PR abiertas encontradas antes de esta limpieza: 32.
- PR cerradas durante esta auditoría por duplicación/supersesión documentada: #25, #45, #49, #90, #99 y #102.
- PR abiertas en la última consulta global del 2026-10-22: 23. Este número puede cambiar cuando se actualicen PRs; no se han fusionado PR durante esta continuación.
- La PR #106 (auditoría de continuidad documental) sí se fusionó en `main` el 2026-10-22; fue una PR documental explícita y su contenido es esta auditoría. No se fusionaron otras PR de implementación, no se eliminaron ramas ni se cambiaron configuraciones de facturación. La PR #49 se cerró como supersedida por #38 después de confirmar que el journal actual ya cubre su función con un ACK más seguro. Se renumeraron documentos solo en ramas de PR: #70 ahora propone ADR-006 para lectura de estado y separa su manual como `MANUAL_PROTOTIPO_PANEL_CONTROL_MASTER.md`; #104 propone ADR-007 para autenticación PC-MASTER. No se perdió contenido ni se fusionó ninguna rama.

## Acciones realizadas

### PR #102 — cerrada como supersedida

- Era la versión v2 de la corrección de ACL NTFS/ciclo ASGI para la rama PC-MASTER Windows.
- La PR #103 conserva la misma línea de trabajo en v3.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/102

### PR #90 — cerrada como supersedida

- Era la versión inicial de la misma corrección de ACL NTFS/suite integral.
- La PR #103 es la versión posterior.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/90

### PR #99 — cerrada como supersedida

- Era una rama anterior de endurecimiento del panel administrativo basada en el proveedor de snapshots.
- La PR #104 continúa esa línea con correcciones posteriores, pruebas y CI documentada para el HEAD actual.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/99

Los cierres conservan el historial de GitHub; no se borró el trabajo histórico.

### PR #25 — evaluación preliminar del motor Android, cerrada como supersedida

- La propuesta del 2026-10-09 se quedó obsoleta frente a la investigación y comparativa ampliadas, el ADR-002 y el Issue #8.
- La vía QEMU + Android-x86 + VNC está retirada; redroid sigue bloqueado por #27 y Cuttlefish es solo candidato de laboratorio.
- No se fusionó ni se borró la rama histórica.

## Mapa de dependencias de PR observado el 2026-10-21

Las PR abiertas no son una lista plana: varias se apilan unas sobre otras. El orden de base observado en los metadatos de GitHub es:

- **Contratos:** #16 (base `main`) → #30; #28 también se apoya en la rama de contratos #16.
- **Persistencia/outbox/journal:** #32 (base `main`) → #34 → #36 → #38 → #42 → #44 → #47 → #48 → #101 → #74 → #104. Esta cadena se debe revisar como conjunto y no fusionar fuera de orden.
- **Entrega de tareas y ciclo de agente:** #52 se apoya en #74; #57 se apoya en #52; #67 se apoya en #57; #85 se apoya en #67. La PR #49, que se apoyaba en #38, se cerró como supersedida después de confirmar que el journal de #38 ya ofrece ACK durable versionado más seguro.
- **Aplicación de escritorio Windows:** #87 se apoya en una rama anterior del panel local; #103 se apoya en #87. Mantener separados el envoltorio de escritorio y el panel/API web mientras se aclara su integración.
- **Documentación independiente:** #21 (inventario de hardware), #23 (manual de operación), #26 (caché de artefactos), #40 (ADR de autenticación de agentes), #70 (prototipo dashboard), #86 (actualización de evidencia GeeLark).

Este mapa sustituye la instantánea temporal de PR #45 del 2026-10-10/14; la PR #45 se cerró como supersedida sin merge. Los metadatos pueden cambiar si se actualizan las bases de las ramas.

## PR #49 — cerrada como supersedida por #38

- La PR #49 (`feat/agent-journal-delivery-ack`) está basada en `feat/cluster-agent-guard` (#38); la PR #48 (`feat/agent-https-transport`) parte de `feat/agent-operation-authorization`, y #101 parte de #48. La cadena descrita en Issue #50 no incluye #49.
- #49 modifica el journal local y su entrega de recibos. Debe compararse con el contrato `mark_receipt_delivered` y el ACK esperado por #48/#101 para decidir si es dependencia faltante o implementación reemplazada.
- La comparación posterior confirmó que #38 ya incluye el ACK versionado que necesitaba el transporte; #49 se cerró como supersedida, sin merge, conservando su historial. La dependencia de #48 queda resuelta por el pin compatible y la prueba del HEAD actual, aunque la integración del grafo sigue pendiente.

## Nueva colisión ADR y solapamiento del panel (#107)

- Orden propuesto y documentado en comentarios: ADR-005 autenticación de agentes (#40), ADR-006 lectura de estado Master/Worker (#70), ADR-007 autenticación local PC-MASTER (#104).
- En #70 se renombró `ADR-005-LECTURA-ESTADO-CLUSTER.md` a `ADR-006-LECTURA-ESTADO-CLUSTER.md`, se actualizó la referencia del módulo, se separó el manual y se eliminó un filtro redundante de workflow. La CI #44 pasó en el HEAD final. En #104 se renombró la decisión PC-MASTER de ADR-006 a ADR-007; CI #473/#602 pasó. Los cambios están en ramas draft, sin merge.
- Se separó el manual del prototipo de #70 en `docs/MANUAL_PROTOTIPO_PANEL_CONTROL_MASTER.md`; #104 conserva `docs/MANUAL_USUARIO_PANEL_CONTROL_MASTER.md` para la aplicación autenticada. El schema/example v1 compartido entre #70 y #74 tiene los mismos blobs, así que no hay divergencia de contenido en esos archivos.
- CI final: PR #70 HEAD `fd0365d579a815d2a39f1213ed11af891dfe91d6`, workflow prototipo #44 `success` tras quitar un filtro redundante de ruta manual; PR #104 HEAD `75764c435f488f617a07c0003ce088829e6dbd41`, transporte #473 `success` y persistencia #602 `success`. Issue #107 quedó cerrada como completada; ambas PR siguen en draft.

## Dependencia heredada de la aplicación de escritorio Windows

- La PR #87 tiene base `feat/master-control-readonly-api-local-auth`, que es la rama de la PR #76 cerrada sin merge. La PR #104 es la línea más reciente del panel/API autenticado y tiene como base `feat/master-status-snapshot-provider-v1`.
- La PR #103 se apila sobre #87. No se cerraron #87/#103 porque aportan el lanzador de escritorio y correcciones específicas de Windows; sin embargo, deben reconciliar la ascendencia antes de integrar para no reintroducir la versión anterior del backend ni producir una base de integración incompleta.
- Se dejaron comentarios en ambas PR. No se cambió la base automáticamente, porque un retarget/rebase sin comparar el diff podría perder cambios exclusivos.

## Duplicación parcial de artefactos del panel

- PR #70 (prototipo) y PR #74 (proveedor de snapshots) contienen los mismos blobs SHA para `docs/contracts/master-worker-status-v1.schema.json` y `docs/contracts/examples/master-worker-status-v1.example.json`; no se detectó divergencia de contenido en esos dos archivos. Al integrar, conservar una sola copia canónica del contrato.
- El manual de #70 se separó y renombró como `docs/MANUAL_PROTOTIPO_PANEL_CONTROL_MASTER.md` para documentar la maqueta offline/demo; #104 conserva `docs/MANUAL_USUARIO_PANEL_CONTROL_MASTER.md` para la app autenticada. Se evita el conflicto de ruta y se preserva el contenido específico de ambas.
- #70 se mantiene abierta por el prototipo visual y documentación contractual; su CI del prototipo está en éxito, pero los datos de demo no representan el estado real del clúster.

## Conflictos de numeración ADR detectados y corregidos en ramas candidatas

La colisión inicial entre #40 y #104 se resolvió primero al renombrar autenticación PC-MASTER a ADR-006; la auditoría posterior detectó que #70 también asignaba ADR-005 a lectura de estado. El orden final propuesto y aplicado en ramas es ADR-005 (#40 agentes), ADR-006 (#70 estado Master/Worker) y ADR-007 (#104 autenticación PC-MASTER). Los cambios se han aplicado en sus respectivas ramas; no se fusionaron PR. Las Issues #105 y #107 están cerradas con alcance limitado a las colisiones/solapamientos revisados.

## PR que deben seguir abiertas por ahora

### PR #104 — panel PC-MASTER autenticado, solo lectura y seguridad Windows

- Sigue en draft y **no está fusionada**.
- HEAD actual tras renumerar ADR: `75764c435f488f617a07c0003ce088829e6dbd41`. Transporte HTTPS run #473 y persistencia run #602 terminaron `success`. Logs del HEAD actual: suite raíz **293 passed / 3 skipped**; asignaciones **33 passed**, guard/journal **12 passed**, integración de transporte **54 passed**, autenticación **70 passed / 2 skipped**; Windows ACL **50 passed / 8 skipped**; `pip check` limpio en los tres jobs. Estos checks validan este SHA, no la aceptación manual ni la integración.
- La propia PR declara pendientes revisión final de diffs y aceptación manual en el PC-MASTER real: TLS/certificados, login/logout y permisos efectivos contra PostgreSQL local desechable.
- Issue de aceptación manual: #77.
- No marcar el módulo como aceptado solo por CI.

### PR #103 — corrección Windows v3

- Sigue abierta como draft y es la línea actual de corrección de ACL NTFS/ciclo ASGI sobre la aplicación de escritorio Windows (#87).
- Las versiones v1/v2 (#90/#102) se cerraron como supersedidas.
- Mantener #103 abierta hasta verificar su CI/relación final con la rama PC-MASTER; no fusionar automáticamente.

### Otras PR abiertas

Las ramas de transporte, autenticación, persistencia, journal, supervisor y planificador están apiladas entre sí. No se cerraron automáticamente por antigüedad: varias declaran dependencias explícitas y cerrar una podría descartar trabajo que no está integrado en `main`. Se requiere una auditoría de grafo PR por PR, comparando bases, HEAD, archivos y referencias de supersesión antes de consolidarlas.

## Auditoría de CI por HEAD de las PR abiertas

Se consultaron los workflows asociados a los SHA actuales de las PR, sin lanzar ejecuciones nuevas:

- **#104:** el HEAD renumerado `75764c435f488f617a07c0003ce088829e6dbd41` tiene transporte HTTPS #473 y persistencia #602 en `success`. Los logs del HEAD actual confirman suite raíz **293 passed/3 skipped**, asignaciones **33**, guard/journal **12**, integración de transporte **54**, autenticación **70 passed/2 skipped**, Windows ACL **50 passed/8 skipped** y `pip check` limpio en los tres jobs.
- **#103:** run #574 en éxito. Suite raíz **180 passed, 3 skipped**; Windows ACL **16 passed, 2 skipped**; `pip check` limpio. Esto valida el SHA actual de #103, no la aceptación de la aplicación completa #87. Su diff se solapa con #104 en `app.py`, `auth.py`, tests y workflow; la base de #103 es la app #87, mientras que #104 parte de la pila de snapshots. Reconciliar ambas líneas antes de integrar.
- **#101:** el HEAD anterior `f338d63abdf18ab2c7d833d01ff4cf085457ce0b` pasó transporte run #444 (**58 passed**, `pip check` limpio). El HEAD actual consultado `b84da93881f5869e8832e5888e5dce02433e85cc` no tiene workflows asociados y GitHub marca `mergeable=false`; los 58 tests son evidencia histórica, no CI del HEAD actual. **#74:** HEAD `df34e00ec18eb99ef3d53e99513ef625b42d2a58`, transporte run #449 `success` (**58 passed**, `pip check` limpio) y persistencia #575 `success`. **#52:** transporte #313 `success` (**63 passed**, `pip check` limpio). **#57:** transporte #354 `success` (**83 passed**, `pip check` limpio). **#67:** transporte #344 `success` (**130 passed**, `pip check` limpio) y pruebas de persistencia exitosas. Para #85 y las demás PR listadas se encontraron workflows con `success` en los HEAD consultados; los workflows disponibles varían según filtros y no prueban integración/aceptación.
- **#48:** la ejecución histórica #295 falló por una API de journal incompatible. Se corrigió el pin al journal versionado y el test double de ACK; HEAD actual `f2301e9b1673c57b74a9d625f3f4788f603a83ed` pasó transporte en run #471 (**54 passed, 1 warning**) y `pip check` limpio; esquema #303 y persistencia #600 también `success`. La falla histórica se conserva; la PR sigue abierta por integración ordenada, revisión de seguridad y aceptación del stack.
- **#87:** el único workflow encontrado para su HEAD actual terminó **cancelled** (#578). No cuenta como CI verde de la aplicación de escritorio. La PR #103 prueba una rama de correcciones basada en #87, pero no reemplaza la validación final de la aplicación completa.
- **#86, #40, #26, #23 y #21:** no se encontraron workflows asociados a sus HEADs en la consulta; son PR documentales y esto no se debe etiquetar como CI aprobada.

La consulta de logs confirmó los conteos del HEAD actual de #104 (#473/#602), los conteos de #103 y el run #471 de #48. No se iniciaron workflows manualmente durante la auditoría inicial; las correcciones de código posteriores activaron CI automáticamente en las PR #48 y #104. La CI demuestra el estado de un SHA, no aceptación manual, integración en `main`, despliegue ni funcionamiento en Workers físicos.

## Issues: criterio de limpieza

### Issues #18 y #22 — cerradas como duplicadas

- **#18** se cerró como duplicada de #29. Los criterios únicos de #18 (diferenciar sobre administrativo/protocolo privado y probar mensajes duplicados, epoch antiguo y telemetría caducada) se trasladaron a #29 antes del cierre.
- **#22** se cerró como duplicada de #33. La Issue #33 es la referencia detallada para la capa transaccional de asignación, idempotencia, fencing, capacidad y concurrencia sobre el esquema de la PR #32.



### Issue #2 — cerrado como completado

El acuerdo inicial (desarrollo desde cero, coste obligatorio $0, local/offline cuando sea viable, documentación/manuales, aceptación por módulo y registro en GitHub) ya está documentado en README, requisitos, estado y plan. Las tareas concretas de inventario/paridad siguen en #3, #4 y #6; se cerró únicamente el issue general de arranque.

No se cerró ninguna Issue únicamente por tener casillas marcadas, antigüedad o una prueba verde en una rama sin fusionar.

- #77 debe permanecer abierta: la aceptación manual del panel en el PC-MASTER real sigue pendiente.
- #89 y #91 describen defectos de ACL/ciclo ASGI y de suite pytest. Hay evidencia de corrección candidata y CI verde en #104, pero el cambio no está integrado; revisar de nuevo tras resolver las PR candidatas.
- #20 tiene pruebas de DDL marcadas, pero mantiene casillas abiertas para autenticación/roles y otros pasos; no está completa.
- #8 y #12 permanecen activas: motor Android y contrato agnóstico todavía no están validados en hardware.
- #27 permanece como bloqueo de seguridad para redroid.
- #6 mantiene la auditoría de paridad funcional pendiente; no declarar terminado el catálogo sin contrastar fuentes y registrar evidencias.

## Registros envejecidos corregidos durante la auditoría

- **Issue #11:** actualizada la combinación tecnológica a decisiones vigentes: PC-MASTER Windows, WORKERS físicos Debian 13, Cuttlefish candidato de laboratorio, redroid bloqueado por #27, Android Emulator como referencia y Waydroid secundario. Tauri permanece sin aprobación.
- **Issue #50:** corregida la referencia obsoleta a PR #73; la cadena de dependencias, en dirección base → descendiente, es #48 → #101 → #74 → #52 → #57 → #67 → #85. #101 reemplaza a #73. Se añadieron conteos de CI de los HEADs consultados el 22-oct; la revisión manual de seguridad sigue pendiente.
- **Issue #72:** actualizada la referencia de inventario de módulos a PR #101, sucesora de #73.
- **Issue #20:** se aclaró que las pruebas marcadas corresponden al prototipo histórico de PR #19, cerrada sin merge, y no validan automáticamente la rama actual #32.
- **Issue #58:** actualizado el estado del supervisor; PR #67 es candidata sobre #57, pero ambas siguen en draft y no están integradas.
- **Issues #89 y #91:** se registró que la CI de #104 pasa para su SHA, pero los issues siguen abiertos hasta integrar/revalidar la corrección.
- **PR #87:** se registró la superposición de archivos backend con #104 y que el workflow del HEAD actual aparece cancelado.
- **Issue #88:** documentada la evidencia de GitHub: `main` no contiene la aplicación PC-MASTER; la candidata de escritorio está en #87, basada en la rama de la PR #76 cerrada sin merge, y el panel/API actual está en #104. La procedencia exacta del acceso directo local no puede confirmarse sin comparar el archivo ejecutado en el PC-MASTER; la issue permanece abierta.
- **Issue #64:** se verificó que la decisión de sistema base y separación de roles está cerrada como decisión resuelta; el texto distingue expresamente que Debian/PXE, aprovisionamiento y runtime Android aún no están implementados ni probados.
- **Issues #10 y #24:** corregido el inventario para distinguir PC-MASTER (laptop Windows, Core i7 de 11.ª generación con modelo exacto pendiente) de los tres WORKER sin sistema operativo instalado. Se retiró de #24 la instrucción obsoleta de priorizar redroid/QEMU Android-x86; Cuttlefish es candidato de laboratorio, redroid está bloqueado por #27 y no hay motor aprobado ni benchmark físico.
- **PR #86:** se conserva abierta porque tiene contenido funcional más amplio aún no integrado. En su rama se actualizaron `INVESTIGACION_FUNCIONAL_GEELARK.md` y `MATRIZ_PARIDAD_GEELARK.md` con el estado actual de motores; `PLAN_TRABAJO.md` se reconcilió con el contenido actual de `main` y conserva las cuatro secciones únicas de auditoría RPA/API. Por la ascendencia antigua, el diff aún requiere revisión/refresco antes de integrar.

## Documentación envejecida detectada

- `docs/ESTADO_PROYECTO.md` y `docs/PLAN_TRABAJO.md` tenían encabezado de actualización del 2026-10-09 aunque había decisiones y pruebas posteriores hasta 2026-10-21; ambos se actualizaron.
- `docs/CATALOGO_FUNCIONAL_GEELARK.md`, `docs/INVESTIGACION_FUNCIONAL_GEELARK.md` y `docs/MATRIZ_PARIDAD_GEELARK.md` en `main` siguen fechados 2026-10-09. La PR #86 contiene versiones más extensas fechadas 2026-10-12 (por ejemplo, el catálogo pasa de ~63 KB a ~79 KB), por lo que no se debe cerrar como duplicada; debe reconciliarse con el estado actual y revisarse antes de integrar.
- `docs/PLAN_PARIDAD_GEELARK.md` se revisó el 2026-10-21 para registrar el retiro de QEMU/Android-x86/VNC y el estado actual de candidatos sin declarar ningún motor aprobado. `docs/INVENTARIO_LICENCIAS_COSTE.md` se revisó el 2026-10-21: Tauri quedó como alternativa no seleccionada, redroid bloqueado por #27, Cuttlefish como candidato prioritario sin aprobación y licencias exactas de imágenes pendientes de confirmar. `docs/ARQUITECTURA_TECNOLOGICA_PROPUESTA.md` se revisó el 2026-10-21 para aclarar que Tauri no está aprobado, PC-MASTER sigue en Windows y la candidata actual de escritorio es Python/Tkinter en PR #87.
- Los documentos centrales deben distinguir explícitamente:
  1. contenido presente en `main`;
  2. implementación en PR abierta;
  3. CI verificada para un SHA concreto;
  4. aceptación manual del usuario;
  5. despliegue en hardware físico.
- La vía manual QEMU + Android-x86 + VNC está retirada como estrategia de producto. La limpieza local de WSL sigue pendiente de ejecución manual del usuario; GitHub no puede confirmar que se hayan borrado procesos, ISO o paquetes del equipo.
- Cuttlefish es candidato de investigación, no motor aprobado. redroid sigue bloqueado por #27.

## Siguiente cola de auditoría

1. Revisar todas las PR abiertas en grupos de dependencia (PC-MASTER, snapshots, autenticación/transporte, bandeja/outbox/journal/supervisor, contratos/persistencia, documentos).
2. Cerrar PR adicionales solo cuando la descripción, los comentarios y los diffs demuestren inequívocamente que otra PR las sustituye o que no contienen cambios exclusivos.
3. Revisar Issues abiertos en relación con PR/CI: cerrar únicamente defectos corregidos e integrados; mantener bloqueos manuales y decisiones no resueltas.
4. Comparar documentos de main entre sí para localizar secciones repetidas, fechas contradictorias, nombres de contrato/ADR y enlaces rotos; fusionar contenido solo cuando no se pierda contexto.
5. Actualizar fechas de encabezado solo cuando el contenido se haya revisado realmente, no para ocultar antigüedad.
6. Confirmar al final el recuento de PR/Issues, las acciones realizadas y los pendientes que requieren al usuario.

## Comprobaciones de documentación realizadas

- Se comprobaron los enlaces Markdown relativos de los 29 archivos que había en `main` al completar esta pasada: **no se encontraron rutas internas rotas** hacia archivos inexistentes en el árbol de `main`. Esto no verifica la disponibilidad de enlaces externos ni todos los fragmentos/anchors.
- Se revisaron encabezados en `ESTADO_PROYECTO.md`, `PLAN_TRABAJO.md`, `ARQUITECTURA_TECNOLOGICA_PROPUESTA.md`, `MODELO_AMENAZAS_SEGURIDAD.md`, `CONTRATO_API_CLUSTER.md` y `CONTRATO_MENSAJES_AGENTE_CLUSTER.md`; no se encontraron encabezados Markdown idénticos repetidos en esos documentos.
- Los nombres de archivos del árbol principal son diferenciados por función. Las similitudes entre catálogo/investigación/matriz o entre contratos de API/mensajes son complementarias y no se borraron como duplicados sin evidencia de contenido redundante.

## Continuación de auditoría — transporte HTTPS (#48), 2026-10-22

- Inspeccionado el log del run de transporte #295 (ID `38193127429`): fallaron exactamente dos pruebas de `test_runtime.py` relacionadas con la sincronización/ACK real del journal. El workflow instalaba el SHA histórico `e37e5aaef72837c19837eb5b648c29f05ae9b3c3`, cuya firma `mark_receipt_synced(operation_id)` no implementa los argumentos versionados `expected_status` y `expected_result`.
- La PR #38 en su HEAD `5815bc6e8f4146099e5fff028008fdf9f0ede5d6` sí contiene el método versionado. Corregí el pin en `.github/workflows/cluster-agent-transport.yml` dentro de la rama de la PR #48; commit `cbede919af6242c9d874a6eead3596e0144d81ec`.
- La CI del commit de pin `cbede919af6242c9d874a6eead3596e0144d81ec` (#469) eliminó las dos fallas anteriores del journal real, pero expuso una falla adicional del test double `FencedJournal.mark_receipt_delivered`. Ajusté el fixture y la aserción en commit `f2301e9b1673c57b74a9d625f3f4788f603a83ed`. La CI del HEAD final `f2301e9b1673c57b74a9d625f3f4788f603a83ed` pasó en run #471: **54 passed, 1 warning**, `pip check` limpio; los workflows de esquema (#303) y persistencia (#600) también terminaron `success`. La PR #48 sigue abierta por su posición en la cadena de dependencias y la integración real del journal, no por esa suite de transporte.
- **Límite de la corrección:** el pin permite que la prueba cruzada instale la API compatible, pero no cambia la base de #48 ni integra la historia de #38. La topología de ramas y las migraciones siguen requiriendo integración ordenada; no hacer merge por el mero hecho de que el workflow pase.

## Revisión final de Issues abiertas — 22-oct-2026

- Se consultaron las 40 Issues abiertas directamente por la API del repositorio. Tener todas las casillas marcadas, o no tener checklist, no basta por sí solo para cerrar: los issues #24, #11, #10 y #4 siguen teniendo criterios explícitos pendientes de medición, prueba física o contraste funcional; #20 conserva cuatro tareas sin completar; #63 conserva pendiente confirmar el costo real de GitHub Actions, dato que no está disponible desde esta auditoría.
- Se mantienen abiertas las tareas que requieren intervención local del usuario (#77 aceptación Windows, #88 confirmar el archivo/acceso directo local), pruebas en hardware físico (#8/#10/#12/#24) o revisión de seguridad (#9/#27/#65). No se cerraron por antigüedad ni por CI verde en ramas no integradas.

## Límites de esta auditoría

La consulta de GitHub permite revisar el contenido del repositorio, metadatos, PR e Issues, pero no confirma el estado del PC-MASTER local, los procesos de WSL, la aceptación manual, el panel de facturación de la cuenta ni las pruebas que no tengan artefacto verificable. No se iniciaron ejecuciones manuales de GitHub Actions ni se habilitó ningún runner de pago; los commits de corrección sí dispararon las validaciones automáticas configuradas para las PR.


## Estado de mergeabilidad de las ramas apiladas — 22-oct-2026

Consulta de metadatos actual de GitHub (la mergeabilidad puede cambiar con cada push):
- Revalidación de metadatos 2026-10-22: GitHub marca `mergeable=false` en #101 (ACK/inventario), #52 (bandeja durable), #67 (supervisor) y #86 (documentación funcional); #70 (prototipo del panel) ahora aparece `mergeable=true`. #101 tiene HEAD `b84da93881f5869e8832e5888e5dce02433e85cc` sin workflows asociados; los 58 tests previos pertenecen al HEAD anterior. #52 y #67 tienen CI success en sus SHA actuales, pero siguen con conflicto de integración. No asumir que CI verde equivale a que el diff pueda integrarse; reconciliar conflictos/base y volver a revisar el HEAD antes de cualquier merge.
- #87, #103 y #104 aparecen `mergeable=true` en la consulta, pero siguen en draft y tienen dependencias/aceptación pendientes. En particular, #87/#103 heredan una base de #76 cerrada sin merge; la mergeabilidad técnica no elimina ese problema de ascendencia.
- No cambié bases ni forcé resoluciones de conflicto porque podrían descartar cambios exclusivos.

## Continuación — panel y recuento verificado (22-oct-2026)

- Recuento mediante API GitHub al 22-oct: **23 PR abiertas**, todas en draft; **40 Issues abiertas** y 8 cerradas. El recuento previo de 27 PR estaba desactualizado y se corrige aquí.
- PR #70: HEAD `fd0365d579a815d2a39f1213ed11af891dfe91d6`, workflow de prototipo #44 (`39872433379`) completado con `success`. Mantener draft: es el prototipo visual y los contratos de estado, no el panel autenticado de producción.
- PR #104: HEAD `75764c435f488f617a07c0003ce088829e6dbd41`; transporte #473 y persistencia #602 `success`. Persistencia: suite raíz **293 passed / 3 skipped**; asignaciones **33**, guard/journal **12**, integración de transporte **54**, autenticación **70 passed / 2 skipped**; Windows ACL **50 passed / 8 skipped**; `pip check` limpio en los tres jobs.
- La colisión documental queda resuelta: #40 usa ADR-005 (autenticación de agentes), #70 ADR-006 (lectura de estado Master/Worker), #104 ADR-007 (autenticación local PC-MASTER). El prototipo conserva `MANUAL_PROTOTIPO_PANEL_CONTROL_MASTER.md`; el panel autenticado conserva `MANUAL_USUARIO_PANEL_CONTROL_MASTER.md`. Issue #107 cerrada tras verificar CI de los HEAD actuales.
- Issue #93 es una issue paraguas de evolución visual e integración del panel; no es duplicada de #77 (aceptación de seguridad Windows), #71 (semántica de salud), #72 (inventario persistido) ni #69 (diseño del módulo central). Mantener cada una abierta hasta sus propios criterios de aceptación.
- PR #86 contiene ampliaciones funcionales no presentes en `main` y no se cierra como duplicada. Debe reconciliarse con las decisiones motor Android del 21–22 oct y no sobrescribir el plan actual con su copia antigua.
- No se cerraron otras Issues solo por CI verde: muchas representan trabajo pendiente de integración, pruebas físicas, seguridad o aceptación manual. No se fusionaron PR ni se eliminaron ramas.


## Rama histórica `docs/android-engine-evaluation` — actualización 22-oct-2026

Se añadieron avisos de vigencia, preservando el análisis original, a cinco documentos de esta rama: actualización de seguridad redroid, evaluación preliminar de motor, plan de prueba Worker-01, contrato de adaptador runtime histórico y revisión de disponibilidad de imágenes. Los avisos declaran no ejecutable la recomendación antigua QEMU/KVM + Bliss OS, mantienen redroid bloqueado por #27 y aclaran que Cuttlefish no está aprobado. La rama continúa divergida y no se fusionó; estos commits documentales no alteran `main` ni ejecutan CI.


## Rama histórica `docs/cluster-os-poc-decision` — avisos de revalidación (22-oct-2026)

Se añadieron avisos, sin eliminar el análisis original, a cuatro documentos de esa rama divergida: evaluación de sistema base, matriz de decisión, hoja de ejecución de POC y POC Debian 13 primer nodo. Los avisos prohíben ejecutarlos como si fueran un plan aprobado: Debian 13 es base prevista pero la instalación requiere autorización específica; QEMU + Android-x86 + VNC está retirado, redroid bloqueado por #27 y Cuttlefish no aprobado. No se fusionó la rama ni se ejecutó CI.


## Corrección de decisiones envejecidas en `main` — 22-oct-2026

- `docs/ARQUITECTURA_CLUSTER_HETEROGENEO.md` ya no presenta Tauri/React como interfaz seleccionada: aclara PC-MASTER Windows, candidata Python/Tkinter #87 y panel autenticado #104, ambos sin integrar.
- `docs/decisiones/ADR-001-STACK-PRINCIPAL.md` conserva la propuesta original del 9-oct como historial, pero añade nota visible de que Tauri/React y SQLite inicial no deben tratarse como decisiones vigentes frente a la candidata Windows y la persistencia PostgreSQL local que se está validando.
- `docs/ESTADO_PROYECTO.md` etiqueta como históricas/supersedidas las recomendaciones iniciales de redroid y Tauri para evitar que contradigan el estado actual: Cuttlefish candidato no aprobado, redroid bloqueado por #27 y motor sin seleccionar.
