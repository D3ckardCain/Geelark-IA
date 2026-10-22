# Plan de trabajo — Geelark-IA

**Actualizado:** 2026-10-22  
**Fase activa:** A — inventario funcional de GeeLark y viabilidad de Android virtualizado local.

El plan maestro está en [PLAN_PARIDAD_GEELARK.md](PLAN_PARIDAD_GEELARK.md). La investigación documental está en [INVESTIGACION_FUNCIONAL_GEELARK.md](INVESTIGACION_FUNCIONAL_GEELARK.md), la matriz en [MATRIZ_PARIDAD_GEELARK.md](MATRIZ_PARIDAD_GEELARK.md) y la comparativa de motores en [COMPARATIVA_MOTORES_ANDROID.md](COMPARATIVA_MOTORES_ANDROID.md).

## Higiene y estado de integración — 2026-10-22

Antes de avanzar en nuevas funciones, revisar la [auditoría de higiene del repositorio](AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md). La rama `main` conserva requisitos y documentación; el código que se está validando sigue en PR abiertas. Las PR #90 y #102 se cerraron en favor de #103, la PR #99 se cerró en favor de #104 y la evaluación preliminar obsoleta #25 se cerró en favor de la investigación actual y la instantánea de auditoría #45 se cerró en favor del informe actualizado. El Issue #2 de alcance inicial quedó completado; los Issues #18 y #22 se cerraron como duplicados tras trasladar sus criterios únicos a #29 y #33. Los Issues #3/#4/#6 siguen cubriendo inventario y paridad. No fusionar ni declarar aceptado un módulo hasta revisar dependencias, CI del HEAD actual y criterios de aceptación manual. La PR #48 pasó transporte HTTPS (54 passed, 1 warning; `pip check` limpio) en su HEAD `f2301e9b1673c57b74a9d625f3f4788f603a83ed`; esto no sustituye integrar el journal #38 ni validar el grafo de ramas. Bloqueos de auditoría vigentes: PR #49 (journal ACK) parece quedar fuera de la cadena #48→#101 y debe reconciliarse con su contrato antes de integrar. La colisión ADR se renumeró en ramas: #40 ADR-005, #70 ADR-006 y #104 ADR-007. La Issue #107 sigue abierta hasta confirmar CI en los HEAD finales y revisar dependencias. La PR #87/#103 hereda una base de la PR #76 cerrada sin merge; la CI de #87 está cancelada y su ascendencia debe reconciliarse con #104 antes de integrar. La PR #104 sigue en draft y requiere aceptación manual antes de integrar. Además, #87/#103 se apoyan en la rama de #76 cerrada sin merge; su ascendencia debe reconciliarse con #104 antes de integrar.

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

Se amplió la investigación documental de redroid, Android Emulator, Waydroid, Cuttlefish y automatización. La vía manual QEMU + Android-x86 9.0-r2 + VNC en WSL2 se retiró como ruta de producto. La prioridad actual de evaluación es Cuttlefish por su multiinstancia y control WebRTC documentados; redroid queda bloqueado por seguridad en issue #27; Android Emulator es referencia de compatibilidad y Waydroid una alternativa secundaria.

La issue [#8 — Seleccionar y validar motores Android locales y automatización](https://github.com/D3ckardCain/Geelark-IA/issues/8) controla los entregables. No hay motor aprobado: la selección requiere revisión de licencias/seguridad y pruebas reproducibles en Debian físico.


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


## Nueva línea de trabajo — arquitectura tecnológica

La [propuesta de arquitectura](ARQUITECTURA_TECNOLOGICA_PROPUESTA.md) se creó para seleccionar software sin esperar especificaciones de hardware. La [issue #11](https://github.com/D3ckardCain/Geelark-IA/issues/11) controla su validación. Se puede diseñar la UI, API, datos, adaptadores y pruebas de manera agnóstica; las pruebas de rendimiento/compatibilidad del motor se ejecutarán después en hardware de referencia.


## Documentos de decisión y licencias

- [ADR-001 — Stack principal](decisiones/ADR-001-STACK-PRINCIPAL.md)
- [Inventario de licencias y coste](INVENTARIO_LICENCIAS_COSTE.md)

Antes de empaquetar o redistribuir se generará un SBOM, un inventario de licencias transitivas y una verificación de licencias de imágenes Android y APK.


## Contratos previos a implementación

- [Contrato del adaptador Android](CONTRATO_ADAPTADOR_ANDROID.md)
- [Especificación del motor RPA](ESPECIFICACION_MOTOR_RPA.md)

La implementación deberá convertir estos contratos en modelos, código y pruebas de conformidad antes de habilitar los módulos en la interfaz.


- [ADR-002 — Estrategia de selección del motor Android](decisiones/ADR-002-ESTRATEGIA-MOTOR-ANDROID.md): criterios de comparación y bloqueos de seguridad/licencia.


## Actualización de arquitectura distribuida — 2026-10-09

La arquitectura de clúster heterogéneo queda incorporada como línea prioritaria; no se tratará como ampliación futura.

Documentos nuevos:
- [Arquitectura de clúster heterogéneo](ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- [Contrato del agente de nodo y planificador distribuido](CONTRATO_AGENTE_NODO_PLANIFICADOR.md).
- [Arquitectura de clúster físico heterogéneo](ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- [ADR-003 — Arquitectura distribuida](decisiones/ADR-003-ARQUITECTURA-DISTRIBUIDA-CLUSTER.md).
- [Issue #14 — Integrar clúster y planificador](https://github.com/D3ckardCain/Geelark-IA/issues/14).

Orden de trabajo actualizado:
1. Cerrar el contrato del agente de nodo, alta/autorización, heartbeat, capacidades, tareas, leases, seguridad y reconciliación.
2. Diseñar el modelo de recursos y la asignación explicable para CPU, RAM, disco, ABI, motor Android y salud.
3. Mantener Debian 13 como sistema base previsto de los WORKER y validar la compatibilidad de virtualización Android, licencias, seguridad y rendimiento.
4. Definir una prueba reproducible de dos nodos heterogéneos y un workload Android común.
5. Solo después de la prueba, decidir infraestructura y motor; luego implementar el núcleo distribuido con pruebas y manual en español.

La especificación de agente/planificador ya está documentada, pero no implementada ni probada. No se afirmará alta disponibilidad, failover, migración en vivo ni densidad de instancias sin evidencia.


## Actualización — planificador y prueba de concepto (2026-10-09)

Se añadieron dos documentos para convertir el diseño del clúster en criterios comprobables:

- [Especificación del planificador de recursos](ESPECIFICACION_PLANIFICADOR_RECURSOS.md): filtros de elegibilidad, reservas, puntuación explicable, leases/epochs, reconciliación, seguridad y pruebas de aceptación.
- [Plan de prueba de concepto del aprovisionamiento](PLAN_PRUEBA_CONCEPTO_CLUSTER.md): protocolo para validar descubrimiento, adopción aprobada, instalación desatendida de Debian por red, despliegue del agente y preparación del entorno Android.

Orden inmediato:
1. Revisar la persistencia autoritativa y las garantías de consistencia del plano de control antes de implementar asignaciones distribuidas.
2. Definir y probar los esquemas del protocolo de agente y scheduler.
3. Ejecutar la prueba de concepto con los equipos disponibles y registrar mediciones reales.
4. Elegir infraestructura solo con resultados y revisión de licencias.
5. Implementar el núcleo distribuido, pruebas automatizadas y manual de usuario antes de pasar al siguiente módulo.

Los documentos son especificaciones y planes; no hay planificador, agente ni clúster implementados, y la prueba de concepto sigue pendiente.


## Decisión previa necesaria — persistencia del clúster (2026-10-09)

Se documentó [ADR-004 — Persistencia y consistencia del plano de control](decisiones/ADR-004-PERSISTENCIA-CONSISTENCIA-CLUSTER.md). La propuesta para el MVP es PostgreSQL local en la Master con un único controlador activo y sin failover automático: si la Master cae, se pausan nuevas asignaciones mientras las instancias existentes continúan cuando sea seguro. Esto prioriza no duplicar instancias sobre una promesa de alta disponibilidad no probada.

La propuesta queda condicionada a revisión de licencias y a la prueba de concepto. Antes de implementar el scheduler se deben validar transacciones, epochs, idempotencia, fencing, backup/restauración y reconciliación. No se considera decisión final hasta completar esas verificaciones.


## Contrato de mensajes del agente (2026-10-09)

Se añadió [CONTRATO_MENSAJES_AGENTE_CLUSTER.md](CONTRATO_MENSAJES_AGENTE_CLUSTER.md), con ejemplos de alta de nodo, heartbeat, telemetría, asignación, resultado, errores tipados y transiciones de estado. Define reglas de idempotencia, epochs, frescura de telemetría y rechazo de mensajes incompatibles. El documento sigue siendo especificación, no una API o agente implementado.

Siguiente secuencia técnica:
1. Convertir el contrato a modelos Pydantic estrictos y fixtures JSON sintéticos.
2. Crear pruebas automatizadas de validación y transiciones.
3. Añadir pruebas de concurrencia e idempotencia para la persistencia.
4. Probar desconexión/reinicio/reconciliación.
5. Solo después comenzar el agente y scheduler ejecutables.


## Implementación inicial del contrato (PR en borrador)

El [PR #16](https://github.com/D3ckardCain/Geelark-IA/pull/16) contiene los primeros modelos Pydantic y una máquina de estados pura. Próximo gate: ejecutar el checkout exacto del branch en entorno limpio, confirmar instalación local y suite completa, revisar modelos/estados y luego integrar. Después implementar persistencia transaccional e idempotencia durable en una rama separada; no simular coordinación distribuida con memoria de proceso.


### Revisión del contrato y estados

El PR #16 incorpora validación cruzada de resultados para impedir combinaciones contradictorias de estado. La copia de trabajo local pasó 33 casos. Gate pendiente: ejecutar instalación y pruebas contra el checkout exacto del branch en un entorno limpio antes de integrar; después abordar persistencia transaccional e idempotencia durable.


## Persistencia segura de asignaciones

Se añadió [ESPECIFICACION_PERSISTENCIA_ASIGNACIONES.md](ESPECIFICACION_PERSISTENCIA_ASIGNACIONES.md), que define invariantes de propiedad/epoch, reservas transaccionales, claves idempotentes, auditoría y outbox para recuperación de órdenes. Es una especificación, no una migración ni un repositorio implementado. El siguiente gate es revisar el diseño junto con ADR-004 y traducirlo a DDL/pruebas locales solo después de verificar el contrato inicial.


### Próxima tarea técnica registrada

La issue [#17 — persistencia transaccional de asignaciones y outbox](https://github.com/D3ckardCain/Geelark-IA/issues/17) queda preparada con criterios de aceptación para exclusión de doble propietario, idempotencia durable, epoch, reservas, outbox, recuperación y backups. No se empezará esa implementación hasta cerrar la revisión de contratos del PR #16.


## Actualización del plan de motores — 2026-10-21

La ruta manual QEMU + Android-x86 9.0-r2 + VNC queda retirada. La investigación ampliada está en [INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md](INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md).

Nuevo orden:
1. Revisar licencias, imágenes, host y seguridad de Cuttlefish; después realizar una prueba de una instancia y otra de dos en Debian físico de laboratorio.
2. Mantener redroid bloqueado hasta resolver issue #27 y demostrar aislamiento con privilegios mínimos.
3. Usar Android Emulator oficial como referencia de compatibilidad únicamente después de revisar los términos del SDK/imágenes.
4. Mantener Waydroid como alternativa secundaria.
5. Diseñar RPA Builder/Runner, Synchronizer, API/eventos y control de instancias detrás de un contrato agnóstico del motor.
6. Medir recursos y escalar progresivamente; no prometer 50 instancias sin resultados.

Estas decisiones documentales no autorizan todavía instalación en WORKERS físicos ni demuestran rendimiento.
