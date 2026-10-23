# Auditoría de continuidad GitHub — 2026-10-22

**Estado:** hallazgos registrados; no implica fusión ni aceptación de implementación.  
**Coste:** auditoría documental mediante APIs de GitHub; no se lanzaron workflows.  
**Regla de seguridad:** no borrar ramas divergentes ni cerrar tareas sin verificar dependencias y evidencia.

## Decisiones vigentes

- Se descarta la vía experimental QEMU + Android-x86 + VNC. No continuar diagnóstico de pantalla negra ni latencia de puntero en esa vía.
- No se selecciona automáticamente un motor sustituto. La selección Android local continúa pendiente de evidencia.
- PC-MASTER sigue siendo la aplicación/panel local sobre Windows. Su aceptación real no se sustituye por CI.
- El objetivo operativo continúa siendo 0 USD. No repetir CI solo para reconstruir resultados ya documentados.

## Comparaciones reproducibles de ramas

| Referencia | Base | Delante | Detrás | Resultado | Acción segura |
|---|---|---:|---:|---|---|
| PR #86 / docs/geelark-source-refresh-2026-10-12 | main | 36 | 78 | diverged | No fusionar tal cual; reconciliar los cinco documentos modificados sobre main actual. |
| docs/android-engine-evaluation | main | 8 | 80 | diverged | Conservar como fuente de documentos únicos; actualizar la evaluación para reflejar el descarte de QEMU y revisar los documentos antes de migrarlos. |
| docs/cluster-os-poc-decision | main | 14 | 80 | diverged | Conservar la matriz Debian/Proxmox y el plan de POC; reconciliar con decisiones posteriores antes de integrar. |
| docs/audit-open-work-2026-10-10 | main | 83 | 80 | diverged | No fusionar la rama completa: contiene una edición amplia de ESTADO_PROYECTO.md que requiere reconciliación. |
| PR #87 / feat/pc-master-windows-desktop-v0.1 | feat/master-control-readonly-api-local-auth | 23 | 0 | ahead | La comparación no muestra retraso respecto a la base declarada; revisar archivos compartidos y CI del HEAD antes de integrar. |
| PR #101 / fix/worker-module-inventory-transport-ack-v2 | feat/agent-https-transport | 17 | 7 | diverged | Reconciliar la base y el contrato de ACK antes de integrar. |

Las cifras corresponden a la comparación de commits consultada el 2026-10-22. Pueden cambiar con nuevos commits.

## PR apiladas y bloqueos

- PR #103 depende de PR #87; no integrarla por separado de su base.
- PR #104 permanece en draft y sin merge. Las issues #77, #89 y #91 documentan respectivamente la aceptación manual Windows pendiente, la corrección de ACL y la suite integral.
- Issue #77 exige comprobar en el PC-MASTER real ACL, TLS, bind loopback, autenticación, permisos de solo lectura y apagado limpio. No conectar Workers físicos ni exponer el servicio a la LAN para adelantar esa aceptación.
- PR #70 (prototipo visual) y #104 siguen siendo propuestas no integradas; no describir el panel como desplegado/operativo.
- PR #86 está muy retrasada y divergida. No cerrarla como duplicada ni fusionarla a ciegas.

## Evidencia CI

Se consultó el endpoint de estado combinado para los HEAD de #86, #87, #101 y #104. El resultado no devolvió checks para esos SHA. Esto no significa éxito ni fallo. Las ejecuciones históricas citadas en las issues solo pueden reutilizarse si coinciden exactamente con el commit evaluado.

No se lanzaron workflows nuevos durante esta auditoría para evitar gasto redundante. Lanzar CI únicamente tras cambios relevantes o cuando una integración necesite validación.

## Limpieza de documentación Android

La rama docs/android-engine-evaluation contiene, entre otros, estos documentos propios:
- docs/ACTUALIZACION_SEGURIDAD_REDROID_2026-10-09.md
- docs/CONTRATO_ADAPTADOR_RUNTIME_ANDROID.md
- docs/EVALUACION_PRELIMINAR_MOTOR_ANDROID_CLUSTER.md
- docs/PLAN_PRUEBA_NO_DESTRUCTIVA_WORKER_01.md
- docs/REVISION_DISPONIBILIDAD_IMAGENES_ANDROID_2026-10-09.md

La evaluación preliminar todavía presenta Android-x86/Bliss OS en QEMU/KVM como alternativa si redroid falla. Esa recomendación ya no está vigente tras la decisión del usuario. Debe conservarse como registro histórico, pero añadirse una nota visible de retirada o reemplazarse por un estado histórico en una actualización documental revisada. No borrar el análisis de seguridad de redroid ni la evidencia técnica que pueda seguir siendo útil.

## Siguientes pasos seguros

1. Reconciliar selectivamente los cinco documentos de PR #86 con main y verificar fuentes oficiales actuales.
2. Preparar una actualización documental que marque QEMU/Android-x86/VNC como vía descartada, sin borrar el análisis histórico.
3. Revisar divergencias y archivos compartidos en la cadena #87/#103/#104 y en #48/#101/#74/#52/#57/#67/#85.
4. Confirmar CI del HEAD exacto cuando haya cambios; evitar reejecuciones redundantes.
5. Completar la aceptación manual del PC-MASTER real antes de cerrar #77 o declarar el panel operativo.
6. Cerrar issues solo tras comprobar que su entregable se integró, se probó y se documentó.

## Alcance de esta auditoría

No se fusionaron PR, no se borraron ramas, no se modificaron los binarios ni se ejecutaron pruebas en los equipos físicos. Se publicaron comentarios de continuidad en las issues #88, #91 y #93 y se registraron las decisiones de retirada de QEMU en #8 y #24.


## Hallazgo adicional — documentación histórica de motores Android

La rama `docs/android-engine-evaluation` contiene documentación útil, pero no debe confundirse con una decisión vigente:

- `docs/ACTUALIZACION_SEGURIDAD_REDROID_2026-10-09.md` registra un riesgo de redroid privilegiado y propone QEMU/Bliss OS como alternativa si no se demuestra una mitigación.
- `docs/EVALUACION_PRELIMINAR_MOTOR_ANDROID_CLUSTER.md` todavía presenta redroid como candidato prioritario y QEMU/KVM como plan alternativo.
- Esa recomendación de QEMU/Android-x86/Bliss OS está **obsoleta y descartada por decisión del usuario**. No ejecutar ni reactivar ese plan, ni convertir el descarte en una selección automática de redroid u otro motor.
- La información de seguridad histórica de redroid y los requisitos de aislamiento siguen siendo referencias documentales, pero cualquier evaluación futura debe partir de una nueva decisión explícita y evidencia actualizada. Hasta entonces, el motor Android queda **sin seleccionar**.
- No se ha copiado esta rama completa a `main`: sigue divergida y contiene documentos únicos. La reconciliación debe ser selectiva y preservar las evidencias no obsoletas.

## Próxima unidad de auditoría

Priorizar una reconciliación documental selectiva de la PR #86 por archivo, sin fusionar su rama divergida completa; después clasificar los documentos únicos de `docs/android-engine-evaluation` y `docs/cluster-os-poc-decision` como vigentes, históricos o pendientes. La limpieza de ramas solo se hará después de verificar que no queda contenido único sin migrar.


## Revalidación posterior — 22-oct-2026 (HEADs exactos)

Esta sección actualiza el estado CI de la instantánea anterior; las notas previas se conservan como evidencia histórica de lo observado en aquel momento.

- **PR #70** HEAD `fd0365d579a815d2a39f1213ed11af891dfe91d6`: workflow de prototipo #44 (`39872433379`) completado con `success`. GitHub sigue indicando `mergeable=false`; no fusionar hasta reconciliar base/diff.
- **PR #104** HEAD `75764c435f488f617a07c0003ce088829e6dbd41`: transporte #473 y persistencia #602 completados con `success`. Logs de persistencia: suite raíz **293 passed/3 skipped**; asignaciones **33**, guard/journal **12**, integración de transporte **54**, autenticación **70 passed/2 skipped**; Windows ACL **50 passed/8 skipped**; `pip check` limpio en los tres jobs. Esto no sustituye la aceptación manual de #77.
- **PR #101** HEAD actual `b84da93881f5869e8832e5888e5dce02433e85cc`: no se encontraron workflows asociados a ese SHA y GitHub marca `mergeable=false`. La CI previa de 58 pruebas pertenece al HEAD anterior `f338d63abdf18ab2c7d833d01ff4cf085457ce0b`; no atribuirla al HEAD actual.
- **PR #48** HEAD `f2301e9b1673c57b74a9d625f3f4788f603a83ed`: transporte #471 `success` (**54 passed, 1 warning**, `pip check` limpio); esquema #303 y persistencia #600 también `success`.
- **PR #87** conserva un workflow cancelado para su HEAD actual; la CI verde de #103 valida una rama descendiente de correcciones, no la app completa ni la aceptación manual.
- Recuento del repositorio por API: **23 PR abiertas** (todas en draft), **40 Issues abiertas** y **8 Issues cerradas**. Issues #64, #105 y #107 se cerraron con alcance limitado y evidencia documentada; no se fusionó ninguna PR.
- La numeración ADR final en ramas candidatas es #40 ADR-005 (autenticación agentes), #70 ADR-006 (lectura de estado Master/Worker), #104 ADR-007 (autenticación PC-MASTER). Issue #107 quedó cerrada tras confirmar referencias, manuales separados y CI actual de #70/#104.



## Reconciliación de documentos históricos Android — 22-oct-2026

Se añadieron avisos de vigencia sin borrar el análisis original, únicamente en la rama `docs/android-engine-evaluation`, a cinco archivos: `ACTUALIZACION_SEGURIDAD_REDROID_2026-10-09.md`, `EVALUACION_PRELIMINAR_MOTOR_ANDROID_CLUSTER.md`, `PLAN_PRUEBA_NO_DESTRUCTIVA_WORKER_01.md`, `CONTRATO_ADAPTADOR_RUNTIME_ANDROID.md` y `REVISION_DISPONIBILIDAD_IMAGENES_ANDROID_2026-10-09.md`. Los avisos prohíben tratar como vigente la recomendación QEMU/KVM + Bliss OS y aclaran el estado actual de los candidatos. No se fusionó la rama ni se ejecutó CI; no hubo cambios de código ni instalaciones.


## Revalidación de la rama histórica `docs/cluster-os-poc-decision` — 22-oct-2026

Se añadieron avisos de revalidación, sin borrar el contenido original, a `EVALUACION_SO_BASE_CLUSTER_0USD.md`, `MATRIZ_DECISION_SO_CLUSTER.md`, `HOJA_EJECUCION_POC_HOST_CLUSTER.md` y `POC_DEBIAN13_PRIMER_NODO.md`. Los avisos distinguen Debian 13 como base prevista de una autorización de instalación y recuerdan el retiro de QEMU/Android-x86/VNC, el bloqueo de redroid y que Cuttlefish no está aprobado. La rama sigue divergida; no se fusionó ni se ejecutó CI.
