# Estado del proyecto GeeLark-IA

**Actualizado:** 2026-10-23  
**Alcance vigente:** PC-MASTER Windows + PC-WORKERS Debian 13 previsto + adaptador Android agnóstico + agregados del plano de control.  
**Estado:** preparación y auditoría; redroid bloqueado para despliegue físico por la issue #27. No declarar producción ni capacidad validada.

## Objetivo

Construir una plataforma local que administre instancias Android ejecutadas en PCs WORKER físicos desde el panel web PC-MASTER Windows. GeeLark es la referencia funcional pública; la implementación será independiente. iOS queda fuera del alcance. El objetivo obligatorio de coste de software/servicios es 0 USD.

## Decisiones vigentes

1. PC-MASTER significa el panel web central, no su lanzador/configurador de escritorio.
2. El contrato del motor Android es agnóstico; redroid es el primer candidato a evaluar, todavía bloqueado por seguridad #27 y no aprobado para ejecución física.
3. Debian 13 es el sistema base previsto para los workers; no se ha instalado ni aprobado aún mediante este registro.
4. La ruta manual QEMU + Android-x86 + VNC en WSL2 está retirada. redroid es la prioridad de evaluación, pero no se ejecuta en Workers físicos hasta resolver #27. Android Emulator queda como referencia de compatibilidad y Cuttlefish como contingencia.
5. Se conservan agente, enrolamiento, autenticación/autorización, HTTPS privado, heartbeat, capacidades, estado, persistencia, despacho durable, auditoría, reconciliación, captura/entrada y automatización.
6. Los nodos pendientes pueden enviar telemetría y consultar estado limitado; no reciben ni ejecutan tareas hasta ser autorizados.
7. No arrancar ningún motor Android en hardware físico hasta aprobar la selección, licencias, seguridad y plan de pruebas; #27 sigue bloqueando específicamente redroid.
8. No estimar densidad de instancias sin pruebas medidas en el hardware real.
9. Coste obligatorio objetivo: 0 USD; mantener alternativas locales y evitar servicios críticos de pago.

## Estado comprobable

- El plan de aprovisionamiento Debian 13 está en [PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md](PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md). La preparación base del worker y el diagnóstico de solo lectura son independientes del motor; las guías específicas de redroid no autorizan instalarlo.
- La limpieza de alcance/documentación se integró mediante la PR #109.
- El bloqueo de seguridad sigue abierto: [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27).
- No se ha instalado redroid en los workers físicos ni se han modificado sus discos durante esta preparación.
- La limpieza local del experimento QEMU retirado está preparada en `docs/RETIRADA_EXPERIMENTO_QEMU_WSL.md` y registrada en la [Issue #114](https://github.com/D3ckardCain/Geelark-IA/issues/114); no se ha ejecutado desde GitHub y requiere comprobación manual del proceso/paquetes antes de borrar o desinstalar.
- Las PR abiertas no equivalen a cambios integrados; revisar dependencia, CI del HEAD actual y aceptación manual antes de cerrar módulos.

## Recuento de auditoría GitHub — 2026-10-23

La última reconsulta registra **39 Issues abiertas, 10 cerradas y 22 PR abiertas**, todas las PR abiertas en draft al 2026-10-23. Las cifras anteriores (40/7/27 y 39/10/23) se conservan como fotografías previas al cierre sin merge de #112 y #113; estos conteos son dinámicos, no un criterio de aceptación. La auditoría documental más reciente está en [AUDITORIA_CONTINUIDAD_GITHUB_2026-10-23.md](AUDITORIA_CONTINUIDAD_GITHUB_2026-10-23.md); la auditoría base del 21-oct se conserva en [AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md](AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md). No se han fusionado las PR de la cadena del agente/panel; no confundir CI de ramas con integración o aceptación en hardware.

## Bloqueos de integración comprobados — 2026-10-23

- La cadena de agentes/control está apilada en orden #101 → #74 → #52 → #57 → #67 → #85. #101 HEAD `043a4e23efd063949577f758eacc326d74bb7ce5` tiene transporte #479/#478, esquema #308 y persistencia #607 en `success`, y figura `mergeable=true`. #74 HEAD `406936ecef181eb4a7a34d6e25316079ee8b29ea` tiene transporte #480 y persistencia #608 `success`, `mergeable=true`. #52 y #67 siguen `mergeable=false`; #112, sincronización proveedor→bandeja, también está en conflicto.
- Las PR raíz #16 (contratos), #32 (esquema) y #40 (ADR agentes) también están `mergeable=false` y divergidas de `main` según Compare API (20/254, 18/242 y 2/242 commits exclusivos/ausentes). Sus descendientes requieren reconciliación de historial antes de integración; no usar CI histórica como validación de SHA nuevos.
- PR #112 se cerró sin merge como supersedida por #115 tras inspeccionar sus 10 archivos. #115 conserva claim/accept/reconcile, `task_id`, ACK cercado, inventario y pruebas de salud; HEAD `f17bd3651b710ce2baee64cc98c0825c7bc96546`, transporte #502 y persistencia #629 `success`, `mergeable=true`, aún draft. Revisar su diff/seguridad y la cobertura de Master Admin en la línea #104 antes de integrar. PR #113 se cerró sin merge como supersedida por #115 tras verificar que `domain_handlers.py` y `test_task_inbox_postgres.py` son idénticos y que el workflow de #115 conserva los filtros y la prueba PostgreSQL. #115 HEAD `f17bd3651b710ce2baee64cc98c0825c7bc96546` pasó transporte #502 (66 passed) y persistencia #629 (33 + 20 + 54 + 1 passed; `pip check` limpio). #52/#57/#67/#85 siguen sin integración/aceptación manual; validar dependencias en orden.
- La línea Windows (#87/#103/#104) sigue separada; #87/#103 parten de una rama vinculada a la PR #76 cerrada sin merge. Reconciliar la ascendencia sin cambiar bases automáticamente.
- #104 tiene transporte y persistencia en success en el HEAD consultado, pero sigue draft; aceptación manual Windows #77 y comprobación del artefacto local #88 continúan pendientes.
- La documentación funcional de GeeLark mantiene corte de fuentes del 2026-10-09; se añadieron avisos de frescura, pero no se ha completado una nueva auditoría exhaustiva de las funciones públicas.

## Próximas etapas

1. Revisar la integración de #115 (sustituta de #112) y el stack de control en orden base → descendiente; después reconciliar la línea Windows (#87/#103/#104).
2. Evaluar redroid primero: seguridad de la imagen/digest, requisitos kernel/Binder, licencia, compatibilidad de APK, operación multiinstancia y recursos. Cuttlefish solo si redroid se descarta.
3. Mantener #27 abierta mientras redroid no tenga mitigación verificable para la imagen exacta.
4. Aprobar el procedimiento de aprovisionamiento Debian 13 para WORKER-01.
5. Ejecutar diagnóstico de solo lectura cuando el worker esté preparado.
6. Probar una instancia y después dos, solo tras aprobar el motor elegido.
7. Integrar el agente autenticado con PC-MASTER y validar enrolamiento, heartbeat, despacho y reconciliación.
8. Medir capacidad y actualizar manuales y registro de problemas/soluciones.

## Documentos principales

- [Alcance PC-MASTER + redroid](ALCANCE_PC_MASTER_REDROID.md)
- [Evaluación de redroid](COMPARATIVA_MOTORES_ANDROID.md)
- [Contrato del adaptador Android](CONTRATO_ADAPTADOR_ANDROID.md)
- [Arquitectura del clúster físico](ARQUITECTURA_CLUSTER_HETEROGENEO.md)
- [Modelo de amenazas](MODELO_AMENAZAS_SEGURIDAD.md)
- [Inventario de licencias y costes](INVENTARIO_LICENCIAS_COSTE.md)
- [Plan de trabajo](PLAN_TRABAJO.md)

---

## Revalidación del estado — 2026-10-28

Esta sección sustituye las fotografías históricas anteriores cuando exista contradicción. Los apartados fechados en 2026-10-23 se conservan como historial, no como estado operativo actual.

### PC-MASTER Windows

- La línea de interfaz actual está propuesta en la cadena apilada [PR #136](https://github.com/D3ckardCain/Geelark-IA/pull/136) → [PR #138](https://github.com/D3ckardCain/Geelark-IA/pull/138) → [PR #139](https://github.com/D3ckardCain/Geelark-IA/pull/139). La CI reportada para los HEAD revisados fue verde en Linux/Windows e integración PostgreSQL; esto no equivale a integración en `main` ni a aceptación manual.
- La aceptación manual permanece pendiente en [Issue #77](https://github.com/D3ckardCain/Geelark-IA/issues/77). No afirmar que el panel fue aceptado en el equipo físico.
- La PR #141 propone refrescar el plan de trabajo; sigue siendo propuesta hasta fusionarse.

### Adopción de workers Linux

- [Issue #118](https://github.com/D3ckardCain/Geelark-IA/issues/118) continúa bloqueada para implementación/despliegue real por la aceptación #77 y la necesidad de reconciliar el stack existente.
- [PR #142](https://github.com/D3ckardCain/Geelark-IA/pull/142) propone el diseño documental de adopción segura. No instala ni despliega agente, no genera credenciales reales, no abre puertos y no toca workers físicos.
- Hallazgo de integración que debe resolverse antes de programar: el contrato de #40/#46 describe telemetría limitada para nodos `pending`, mientras el servicio de dominio descrito en #44 autentica credenciales activas de nodos aprobados. No resolver con bypass ni API paralela. Decidir dentro del servicio existente y añadir pruebas negativas por estado/operación y carrera con revocación.
- Los nodos pendientes nunca pueden recibir, reclamar ni ejecutar tareas; conectividad y salud reportada deben mantenerse separadas.

### Redroid y coste

- [Issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27) continúa abierta como puerta obligatoria de seguridad. [PR #122](https://github.com/D3ckardCain/Geelark-IA/pull/122) es investigación documental; no se ha descargado ni iniciado una imagen como parte de esta preparación.
- No ejecutar Redroid en PC-MASTER ni en workers físicos hasta fijar un digest concreto, revisar el init/patches y demostrar mitigación efectiva y reproducible para el riesgo de `kernel.modprobe`.
- Objetivo de operación: 0 USD. No introducir servicios, APIs o almacenamiento de pago como dependencia crítica; verificar límites y licencias antes de adoptar herramientas.

### Próximo orden de trabajo

1. Revisar la ascendencia, bases y diff de las cadenas de autenticación/transporte existentes; no crear implementación duplicada.
2. Resolver la discrepancia `pending` frente a autenticación activa con contrato y pruebas negativas.
3. Mantener las PR de PC-MASTER sin fusionar hasta la aceptación manual #77.
4. Mantener Redroid bloqueado por #27 y workers físicos sin despliegue.
5. Registrar en GitHub decisiones, evidencias de CI asociadas al SHA exacto y limitaciones de validación.

**Límites de esta revalidación:** estado derivado de PRs, Issues y resultados de CI reportados en GitHub. No constituye prueba física, prueba de seguridad completa ni confirmación de que las PR estén fusionadas.
