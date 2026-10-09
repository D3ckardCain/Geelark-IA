# Plan de trabajo — Geelark-IA

**Actualizado:** 2026-10-09  
**Fase activa:** A — inventario funcional de GeeLark y viabilidad de Android virtualizado local.

El plan maestro está en [PLAN_PARIDAD_GEELARK.md](PLAN_PARIDAD_GEELARK.md). La investigación documental está en [INVESTIGACION_FUNCIONAL_GEELARK.md](INVESTIGACION_FUNCIONAL_GEELARK.md), la matriz en [MATRIZ_PARIDAD_GEELARK.md](MATRIZ_PARIDAD_GEELARK.md) y la comparativa de motores en [COMPARATIVA_MOTORES_ANDROID.md](COMPARATIVA_MOTORES_ANDROID.md).

## Objetivo confirmado

Replicar las funciones de GeeLark aplicables a Android, con Android virtualizado/emulado en hardware anfitrión local. El hardware físico es el equipo que ejecuta las instancias; no se presupone el uso de teléfonos físicos. iOS queda fuera del alcance. El sistema debe evitar dependencia obligatoria de servicios cloud y mantener un coste operativo obligatorio de software/servicios de **0 USD**.

La equivalencia se comprobará función por función. No se afirmará paridad total antes de completar inventario, implementación y pruebas.

## Fases

1. **Inventario funcional de GeeLark:** inspeccionar documentación, menús, opciones, flujos, restricciones, errores y notas de versión; mantener matriz de paridad con fuentes.
2. **Viabilidad de Android virtualizado:** investigar motores, imágenes, compatibilidad de CPU/ABI, aceleración, sensores, gráficos, ADB, licencias y límites.
3. **Auditoría del equipo anfitrión:** recopilar SO, CPU, RAM, GPU, almacenamiento, virtualización por hardware y red.
4. **Prueba técnica mínima:** crear una instancia Android local, iniciarla/detenerla, instalar/ejecutar una app de prueba, capturar pantalla, enviar entradas, transferir archivos y comprobar persistencia.
5. **Arquitectura:** elegir tecnologías solo tras pruebas, comprobando licencias, costes, límites, seguridad y migrabilidad.
6. **Núcleo de instancias/perfiles:** ciclo de vida, grupos, configuración, estado y control visual.
7. **Operaciones Android:** aplicaciones, archivos, biblioteca local, conectividad y proxies configurables.
8. **Automatización:** RPA visual, plantillas, sincronizador entre instancias, colas, programación y recuperación.
9. **Integración y trazabilidad:** API local, CLI, eventos, logs, historial y analítica.
10. **Funciones avanzadas:** usuarios/permisos, recursos y alternativas de IA local según hardware/licencias.
11. **Offline y mantenimiento:** caché, colas locales, instalación, backups, actualización y rollback.
12. **Validación integral:** pruebas de regresión, matriz de paridad final, manuales y lista explícita de funciones no equivalentes/no viables.

## Reglas de avance

- Una fase cada vez; no pasar a la siguiente sin entregables, pruebas, documentación y aceptación de la fase actual.
- Cada módulo tendrá issue de GitHub, criterios de aceptación, registro de problemas/soluciones y manual de usuario completo.
- Todo registro, manual, issue y decisión se redactará en español.
- Objetivo de coste operativo: 0 USD para software y servicios obligatorios. Los costes físicos indirectos —electricidad, hardware y conectividad— se documentarán por separado.
- Priorizar software libre, local, autoalojado y migrable; revisar licencias y límites reales.
- Offline donde sea técnicamente viable, sin afirmar que las apps online funcionan sin Internet.
- No declarar una función como implementada o probada sin evidencia.
- No copiar código, marca, contenido privado ni activos propietarios de GeeLark; implementar independientemente a partir de requisitos observables.

## Estado actual

La investigación pública inicial confirma que GeeLark integra perfiles Android cloud, proxies, Library, AIGC, Analytics, Applications, Automaton, Synchronizer, API/ADB, recursos, grupos, miembros y logs. Véanse las fuentes y las incertidumbres en los documentos vinculados arriba.

**No hay módulos de producto declarados terminados.** La siguiente prioridad es completar el inventario y determinar qué tecnología permite ejecutar Android virtual localmente con la mayor compatibilidad posible, antes de fijar el stack.


## Auditoría funcional ampliada (actualización 2026-10-09)

Se añade como entregable obligatorio el [catálogo funcional detallado](CATALOGO_FUNCIONAL_GEELARK.md), que complementa la investigación y matriz existentes. Las notas oficiales recientes muestran que el inventario debe cubrir cambios por versión, incluyendo clonado y configuración de red de perfiles, inspector de UI/árbol de elementos, exportación/importación de RPA, carga masiva de archivos en Synchronizer, etiquetas y vistas de Library, informes de tareas y operaciones masivas de aplicaciones.

La issue activa para este trabajo es [#6 — Completar el catálogo de perfiles, RPA, Synchronizer, Library y API](https://github.com/D3ckardCain/Geelark-IA/issues/6).

**Orden inmediato de trabajo:**
1. Completar el desglose de campos y flujos de perfiles y proxies.
2. Extraer del manual RPA cada bloque, parámetros, selectores, variables, condiciones, errores y formato de exportación.
3. Enumerar operaciones API/CLI/ADB documentadas y especificar contratos locales equivalentes.
4. Completar Library, aplicaciones, grupos, miembros, logs, analytics, cámara y sensores.
5. Actualizar matriz con criterios de aceptación y diferencias explícitas.
6. Solo después, continuar selección de motor mediante prueba reproducible en el hardware anfitrión.

No se inicia implementación de producto ni se selecciona stack definitivo durante esta auditoría.


## Comparativa documental de motores (2026-10-09)

Se completó una primera comparación documental de redroid, Android Emulator oficial, Waydroid y Android-x86/derivados. La revisión detecta que no basta con comparar funciones: las condiciones de licencia de SDK/imágenes, las funciones del kernel Linux, el aislamiento entre instancias y los privilegios/puertos ADB son criterios de bloqueo.

La issue [#8 — Comparar y validar motores Android locales](https://github.com/D3ckardCain/Geelark-IA/issues/8) controla los siguientes entregables. redroid queda como primer candidato a probar si el anfitrión resulta ser Linux compatible; no es aún el motor aprobado. La selección permanece bloqueada hasta obtener las especificaciones del anfitrión y completar una prueba reproducible.


## Actualización del orden de auditoría — 2026-10-09

La revisión directa de guías oficiales permitió concretar criterios de aceptación preliminares para perfiles, proxies, aplicaciones, grupos, RPA, Synchronizer, API/CLI, webhooks, logs y operación offline. Estos criterios están en la sección 2.5 de la matriz y no significan que exista implementación.

Orden de trabajo vigente:
1. Completar los bloques RPA y sus contratos de flujo.
2. Enumerar los endpoints API públicos con sus esquemas y errores; definir contratos locales propios.
3. Completar Library, Members, Logs, Analytics, cámara, sensores, GPS y conectividad.
4. Completar criterios de aceptación de cada fila de la matriz.
5. Ejecutar la prueba del motor en el anfitrión real una vez disponibles sus especificaciones.


## Actualización — revisión de notas v4.5.1/v4.5.2

La auditoría añadió evidencia concreta para carga masiva de archivos en Synchronizer, árbol UI y análisis de layout, etiquetas/vistas de Library, parámetros de tareas publicados y seguimiento de AIGC. Estas capacidades se reflejan en el catálogo y la matriz; no se consideran implementadas.

La siguiente línea de investigación es completar el inventario de bloques RPA y especificar contratos de API/CLI local; los detalles que no aparecen en documentación pública se marcarán como desconocidos en lugar de inferirlos.


## Requisito transversal añadido — seguridad (2026-10-09)

El documento [MODELO_AMENAZAS_SEGURIDAD.md](MODELO_AMENAZAS_SEGURIDAD.md) y la [issue #9](https://github.com/D3ckardCain/Geelark-IA/issues/9) establecen requisitos de seguridad para API local, ADB/shell, aislamiento, archivos, RPA, secretos, importación, backups y operación offline. Estos controles deberán integrarse en las pruebas de cada módulo; el documento no significa que estén implementados.


## Inventario del anfitrión pendiente

Antes de ejecutar la prueba del motor, obtener los datos del equipo siguiendo [GUIA_INVENTARIO_EQUIPO.md](GUIA_INVENTARIO_EQUIPO.md). La tarea se controla en la [issue #10](https://github.com/D3ckardCain/Geelark-IA/issues/10). La guía usa comandos de lectura y evita solicitar números de serie o secretos.
