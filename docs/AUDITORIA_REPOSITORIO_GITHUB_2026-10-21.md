# Auditoría de higiene del repositorio GitHub — 2026-10-21

## Resumen ejecutivo

Esta auditoría revisa el estado visible del repositorio `D3ckardCain/Geelark-IA` en GitHub. El objetivo es reducir duplicados, corregir referencias envejecidas y separar trabajo terminado, candidato en rama, integrado y pendiente de aceptación.

**No confundir una PR con código integrado.** La rama predeterminada `main` contiene actualmente README y documentación; no contiene todavía paquetes de implementación, pruebas, migraciones ni workflows. La implementación técnica que se está validando vive en ramas de PR. Por tanto, el código de una PR abierta no se debe describir como integrado ni como producto aceptado.

## Inventario observado

- Rama predeterminada: `main`.
- Árbol recursivo de `main` al inicio de la auditoría: 28 archivos de texto/Markdown contando README y documentos; no aparecen `.github/workflows/`, `packages/`, `db/`, `tests/` ni `prototypes/`.
- Issues abiertos encontrados en la consulta inicial: 43; el Issue #2 se cerró como completado tras confirmar que el alcance/reglas generales están documentados. Issues abiertos restantes al cierre de esta pasada: 40 tras cerrar también la #105 como completada después de verificar la corrección de numeración ADR.
- PR abiertas encontradas antes de esta limpieza: 32.
- PR cerradas durante esta auditoría por duplicación/supersesión documentada: #25, #45, #90, #99 y #102.
- PR abiertas tras esas cinco acciones: 27, confirmado en la consulta global final.
- No se han fusionado PR, eliminado ramas, borrado archivos ni cambiado configuraciones de facturación.

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
- **Entrega de tareas y ciclo de agente:** #52 se apoya en #74; #57 se apoya en #52; #67 se apoya en #57; #85 se apoya en #67. #49 se apoya en #38.
- **Aplicación de escritorio Windows:** #87 se apoya en una rama anterior del panel local; #103 se apoya en #87. Mantener separados el envoltorio de escritorio y el panel/API web mientras se aclara su integración.
- **Documentación independiente:** #21 (inventario de hardware), #23 (manual de operación), #26 (caché de artefactos), #40 (ADR de autenticación de agentes), #70 (prototipo dashboard), #86 (actualización de evidencia GeeLark).

Este mapa sustituye la instantánea temporal de PR #45 del 2026-10-10/14; la PR #45 se cerró como supersedida sin merge. Los metadatos pueden cambiar si se actualizan las bases de las ramas.

## Duplicación parcial de artefactos del panel

- PR #70 (prototipo) y PR #74 (proveedor de snapshots) contienen los mismos blobs SHA para `docs/contracts/master-worker-status-v1.schema.json` y `docs/contracts/examples/master-worker-status-v1.example.json`; no se detectó divergencia de contenido en esos dos archivos. Al integrar, conservar una sola copia canónica del contrato.
- El manual `docs/MANUAL_USUARIO_PANEL_CONTROL_MASTER.md` de #70 es una versión anterior (7,341 bytes); #104 contiene una versión más actualizada (9,919 bytes) que declara autenticación y estado draft. No fusionar el manual antiguo encima del actualizado.
- #70 se mantiene abierta por el prototipo visual y documentación contractual; su CI del prototipo está en éxito, pero los datos de demo no representan el estado real del clúster.

## Conflicto de numeración ADR detectado

En las ramas abiertas hay dos documentos diferentes con el número **ADR-005**:
- `docs/decisiones/ADR-005-AUTENTICACION-AGENTES.md` en PR #40.
- `docs/decisiones/ADR-005-AUTENTICACION-LOCAL-PC-MASTER.md` en PR #104.

La colisión de numeración quedó corregida en la rama de PR #104 el 2026-10-22: la decisión del panel se renombró a ADR-006 y se eliminó de esa rama el archivo PC-MASTER con nombre ADR-005. La ADR-005 de agentes en #40 se conserva. Issue #105 se cerró como completada tras comprobar los archivos y los workflows del HEAD actualizado; PR #104 sigue en draft y no se ha fusionado.

## PR que deben seguir abiertas por ahora

### PR #104 — panel PC-MASTER autenticado, solo lectura y seguridad Windows

- Sigue en draft y **no está fusionada**.
- Su descripción registra CI verde en el HEAD `3b71c7979f068e5759d263dd9af13f65fc1161fd`: suite raíz 293 passed / 3 skipped, Windows ACL 50 passed / 8 skipped, y transporte HTTPS success.
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

- **#104:** workflows de transporte HTTPS y persistencia completados en `success`. El run #597 tiene tres jobs en éxito: suite raíz **293 passed, 3 skipped**; servicio PostgreSQL/persistencia con grupos de pruebas en éxito y `pip check` limpio; Windows ACL NTFS **50 passed, 8 skipped** y `pip check` limpio. El run #468 de transporte también terminó en éxito.
- **#103:** run #574 en éxito. Suite raíz **180 passed, 3 skipped**; Windows ACL **16 passed, 2 skipped**; `pip check` limpio. Esto valida el SHA actual de #103, no la aceptación de la aplicación completa #87. Su diff se solapa con #104 en `app.py`, `auth.py`, tests y workflow; la base de #103 es la app #87, mientras que #104 parte de la pila de snapshots. Reconciliar ambas líneas antes de integrar.
- **#101:** HEAD `f338d63abdf18ab2c7d833d01ff4cf085457ce0b`, transporte run #444 `success`, **58 passed**, `pip check` limpio. **#74:** HEAD `df34e00ec18eb99ef3d53e99513ef625b42d2a58`, transporte run #449 `success` (**58 passed**, `pip check` limpio) y persistencia #575 `success`. **#52:** transporte #313 `success` (**63 passed**, `pip check` limpio). **#57:** transporte #354 `success` (**83 passed**, `pip check` limpio). **#67:** transporte #344 `success` (**130 passed**, `pip check` limpio) y pruebas de persistencia exitosas. Para #85 y las demás PR listadas se encontraron workflows con `success` en los HEAD consultados; los workflows disponibles varían según filtros y no prueban integración/aceptación.
- **#48:** se encontró una ejecución anterior fallida del transporte (#295) y otra ejecución posterior en éxito (#364), además de checks de esquema/persistencia en éxito. La existencia de la falla histórica debe conservarse; revisar el estado de los checks asociados al HEAD inmediatamente antes de fusionar.
- **#87:** el único workflow encontrado para su HEAD actual terminó **cancelled** (#578). No cuenta como CI verde de la aplicación de escritorio. La PR #103 prueba una rama de correcciones basada en #87, pero no reemplaza la validación final de la aplicación completa.
- **#86, #40, #26, #23 y #21:** no se encontraron workflows asociados a sus HEADs en la consulta; son PR documentales y esto no se debe etiquetar como CI aprobada.

La consulta de logs confirmó los conteos indicados para #104 y #103. No se lanzaron workflows nuevos para evitar ejecuciones redundantes. La CI demuestra el estado de un SHA, no aceptación manual, integración en `main`, despliegue ni funcionamiento en Workers físicos.

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
- **Issue #50:** corregida la referencia obsoleta a PR #73; la línea candidata actual es #52 → #74 → #101 → #48 y #101 reemplazó a #73.
- **Issue #72:** actualizada la referencia de inventario de módulos a PR #101, sucesora de #73.
- **Issue #20:** se aclaró que las pruebas marcadas corresponden al prototipo histórico de PR #19, cerrada sin merge, y no validan automáticamente la rama actual #32.
- **Issue #58:** actualizado el estado del supervisor; PR #67 es candidata sobre #57, pero ambas siguen en draft y no están integradas.
- **Issues #89 y #91:** se registró que la CI de #104 pasa para su SHA, pero los issues siguen abiertos hasta integrar/revalidar la corrección.
- **PR #87:** se registró la superposición de archivos backend con #104 y que el workflow del HEAD actual aparece cancelado.
- **PR #86:** se conserva abierta porque tiene contenido funcional más amplio aún no integrado; requiere reconciliar fechas y el plan antiguo antes de fusionar.

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

## Límites de esta auditoría

La consulta de GitHub permite revisar el contenido del repositorio, metadatos, PR e Issues, pero no confirma el estado del PC-MASTER local, los procesos de WSL, la aceptación manual, el panel de facturación de la cuenta ni las pruebas que no tengan artefacto verificable. No se ha usado GitHub Actions para lanzar pruebas adicionales ni se ha habilitado ningún runner de pago.
