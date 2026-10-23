# Auditoría de higiene del repositorio GitHub — actualización 2026-10-23

## Objetivo

Mantener el repositorio GeeLark-IA alineado con el alcance vigente: PC-MASTER Windows, PC-WORKERS físicos con Debian 13 previsto, un adaptador Android agnóstico y selección de motor basada en evidencia. El objetivo operativo obligatorio es 0 USD.

## Estado y reglas

- No confundir una PR abierta con código integrado o aceptado.
- No cerrar un bloqueo de seguridad por tener documentación escrita; exigir evidencia reproducible.
- No borrar ramas o historial de commits para ocultar decisiones anteriores. La documentación operativa sí debe reflejar el alcance actual.
- Las tareas de autenticación, enrolamiento, transporte, persistencia, despacho, reconciliación, observabilidad y automatización permanecen porque son componentes necesarios del plano de control.
- La estrategia de motor se reabrió a nivel de investigación tras retirar el experimento manual QEMU + Android-x86 + VNC en WSL2. AOSP Cuttlefish es el primer candidato de laboratorio, no aprobado; Android Emulator es referencia de compatibilidad; redroid sigue bloqueado por #27. El contrato permanece agnóstico y no se permite instalación física hasta revisar licencias, seguridad y plan de pruebas.
- No se han instalado paquetes ni modificado discos de los WORKERS durante esta limpieza documental.

## Cambios realizados en la rama de limpieza

- README actualizado con el alcance y los enlaces vigentes.
- ADR-001 y ADR-002 alineados con PC-MASTER Windows, Debian 13 previsto y motor Android intercambiable; ADR-002 retira la ruta QEMU + Android-x86 + VNC en WSL2.
- Arquitectura tecnológica y de clúster actualizadas.
- Plan de trabajo actualizado con fases y puertas de aceptación.
- Evaluación de redroid conservada como bloqueo de seguridad independiente; investigación/comparativa priorizan evaluar Cuttlefish antes de aprobar cualquier motor.
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
- Recuento consultado el 2026-10-23: **38 Issues abiertas, 10 cerradas, 22 PR abiertas**. El recuento cambia con nuevas acciones; no es criterio de aceptación.
- La cadena de PR de clúster sigue mayormente en draft. La CI de una rama no acredita que el stack esté integrado, aceptado manualmente ni probado en hardware.
- #24 se limita a caché local de artefactos; #92 a aprovisionamiento Debian 13. Se añadieron comentarios para evitar duplicación. #27 sigue bloqueando la ejecución física de redroid.
- La auditoría de origen PC-MASTER (#88) sigue pendiente de comparar el archivo/acceso directo local; GitHub identifica la rama candidata, pero no prueba qué ejecutable se inició en Windows.
- Revalidación de CI en ramas apiladas: #104 HEAD `75764c435f488f617a07c0003ce088829e6dbd41` pasó transporte (#473, 125 pruebas) y persistencia/suite raíz (#602: 293 passed/3 skipped; Windows ACL 50/8 skipped; `pip check` limpio). Esto no sustituye aceptación manual (#77).
- #101 HEAD `b84da93881f5866e8832e5888e5dce02433e85cc` no devolvió workflows asociados en la consulta; no declarar CI verde. #87 HEAD `386da22f1dca3f2a1f489e2d9a898d30350d3eb0` solo devolvió persistencia cancelada (#578). #103 HEAD `31ec5abceae6e38279d6be1e19e94683e0ea00ea` devolvió persistencia exitosa (#574), pero no transporte en esa consulta. Las tres PR siguen en draft.
- #87/#103 heredan una base vinculada a la PR #76 cerrada sin merge; reconciliar la ascendencia con #104 antes de integrar. No retargetear automáticamente sin comparar diffs.

## Registro

Esta actualización reemplaza recuentos históricos de Issues/PR que podrían haber cambiado. El historial de GitHub conserva las decisiones anteriores; los documentos operativos actuales deben seguir esta actualización.

## Continuación de auditoría — 2026-10-23

### Conteo actual y alcance

- Consulta global de GitHub: **22 PR abiertas, todas en draft**. La cifra previa de 27 y la consulta intermedia de 23 quedan supersedidas por este recuento.
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
- **#86 — cerrada sin merge:** su rama contiene documentación histórica de investigación funcional/RPA que no debe borrarse del historial. Sus documentos exclusivos no se consideran integrados por defecto. Reconciliar el catálogo, investigación funcional, matriz de paridad y especificación RPA con el alcance vigente PC-MASTER Windows + Debian 13 + motor intercambiable; Cuttlefish es candidato no aprobado y redroid permanece bloqueado por #27.

### Duplicados, prototipos y ramas apiladas

- **#70 no es una copia exacta de #104:** #70 contiene una maqueta HTML ficticia autocontenida, contrato v1, ADR-006 de lectura de estado y pruebas de navegación; #104 implementa el backend/panel autenticado local y corrige Windows. Hay solapamiento documental en manual/contrato, pero los propósitos y archivos principales difieren. Mantener #70 en draft; antes de integrarlo, reconciliar contrato/manual y ADR-006 de estado con ADR-007 de autenticación de PC-MASTER. No conectarlo a datos reales.
- **#87 → #103** conserva el lanzador Windows y correcciones específicas, pero su ascendencia usa la rama antigua de #76 cerrada sin merge. Reconciliar con #104 antes de integrar para no reintroducir backend antiguo. No cambiar la base automáticamente.
- Cadena de implementación de agentes/control registrada en #50: #38 → #42 → #44 → #47 → #48 → #101 → #74 → #52 → #57 → #67 → #85. No integrar fuera de orden; checks verdes por SHA no resuelven por sí solos conflictos/topología.
- Los prototipos históricos (#19 y #70) deben seguir diferenciados de los servicios operativos; las pruebas de un prototipo no son aceptación de producción.

### Evidencia reciente que permanece vigente

- PR #48 HEAD `f2301e9b1673c57b74a9d625f3f4788f603a83ed`: transporte HTTPS **54 passed, 1 warning**, `pip check` limpio; workflow #471 success.
- PR #104 HEAD `75764c435f488f617a07c0003ce088829e6dbd41`: persistencia **293 passed / 3 skipped**, Windows ACL **50 passed / 8 skipped**, asignaciones **33 passed**, guard/journal **12 passed**, auth **70 passed / 2 skipped**, transporte **125 passed**; `pip check` limpio. Sigue en draft y sin merge.
- La rama de #104 incluye ADR-007 de autenticación local; #70 usa ADR-006 para el contrato/lectura de estado. La antigua colisión ADR-005 se corrigió en #104 y el Issue #105 está cerrado.
- Ninguno de estos resultados acredita instalación en hardware, acceso remoto seguro ya desplegado, ni ejecución real de instancias Android.


### Corrección de estrategia Android — 2026-10-23

- Se actualizaron Issues #3, #10, #11, #12, #24 y #92 para retirar afirmaciones envejecidas que nombraban redroid como motor único/seleccionado. Ahora reflejan que Cuttlefish es candidato de laboratorio, no aprobado, y que el contrato del adaptador es agnóstico.
- #24 mantiene únicamente la caché local de artefactos verificados; #92 mantiene únicamente el aprovisionamiento Debian 13. No ejecutar instalación de runtime hasta superar las puertas de licencia, seguridad y aceptación.
- #27 permanece abierta como bloqueo específico de redroid; no se cierra porque la estrategia haya cambiado, ya que sigue siendo evidencia de riesgo relevante si se reconsidera ese motor.
- Se cerró #64 como decisión resuelta (Windows en PC-MASTER, Debian 13 previsto en WORKERS). No se cerró ninguna tarea de implementación física por inferencia.
