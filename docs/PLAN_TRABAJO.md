# Plan de trabajo — Geelark-IA

**Actualizado:** 2026-10-09  
**Fase activa:** A — inventario funcional de GeeLark y viabilidad de Android virtualizado local.

El plan maestro está en [PLAN_PARIDAD_GEELARK.md](PLAN_PARIDAD_GEELARK.md). La investigación documental está en [INVESTIGACION_FUNCIONAL_GEELARK.md](INVESTIGACION_FUNCIONAL_GEELARK.md) y la matriz en [MATRIZ_PARIDAD_GEELARK.md](MATRIZ_PARIDAD_GEELARK.md).

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
