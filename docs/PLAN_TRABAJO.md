# Plan de trabajo — Geelark-IA

Este plan es provisional. Las fases se cierran con evidencia y documentación, no solo con código.

## Fase 0 — Consolidar requisitos y evidencias
- [ ] Inventariar funciones de GeeLark y priorizarlas.
- [ ] Registrar preguntas abiertas y decisiones en GitHub.
- [ ] Inventariar hardware de cada PC.
- [ ] Definir criterios de aceptación y prueba.

**Salida:** requisitos aprobados, inventario y matriz de referencia.

## Fase 1 — Prueba de viabilidad Android
- [ ] Comparar Linux directo y Proxmox para el caso de uso.
- [ ] Probar una única instancia Android con la versión prioritaria.
- [ ] Medir CPU, RAM, almacenamiento, GPU, latencia y estabilidad.
- [ ] Documentar compatibilidad, límites, coste y pasos reproducibles.

**Salida:** informe de viabilidad y recomendación fundamentada.

## Fase 2 — Diseño de arquitectura
- [ ] Definir controlador, agentes de nodo, protocolo y almacenamiento.
- [ ] Definir identidad, roles, acceso remoto, logs y secretos.
- [ ] Definir comportamiento ante pérdida del controlador o de red.
- [ ] Diseñar estrategia de migración y respaldo.

**Salida:** arquitectura revisada y ADRs (registros de decisiones).

## Fase 3 — Módulo mínimo de gestión
- [ ] Registrar un nodo.
- [ ] Mostrar salud y capacidad del nodo.
- [ ] Registrar y consultar una instancia de prueba.
- [ ] Implementar manejo de errores y logs.
- [ ] Completar pruebas, manual y documentación técnica.

**Salida:** primer módulo terminado de extremo a extremo.

## Fase 4 — Escalado controlado
- [ ] Añadir más instancias gradualmente.
- [ ] Ejecutar pruebas de carga y estabilidad.
- [ ] Establecer capacidad por nodo con datos medidos.
- [ ] Probar desconexión/reconexión y recuperación.

**Salida:** capacidad documentada; no asumir 50 instancias hasta verificarlo.

## Fase 5 — Interfaz y acceso remoto
- [ ] Construir interfaz adaptable a PC/móvil.
- [ ] Evaluar PWA y funciones offline específicas.
- [ ] Probar acceso remoto seguro y revocación de sesiones.

## Fase 6 — Replicación modular de funciones GeeLark
Para cada módulo:
- [ ] Especificación y comparación de referencia.
- [ ] Implementación incremental.
- [ ] Pruebas funcionales, seguridad y regresión.
- [ ] Manual de usuario y guía técnica.
- [ ] Registro de diferencias y aprobación antes de avanzar.

## Flujo de trabajo obligatorio

1. Crear/actualizar una GitHub Issue.
2. Acordar criterios de aceptación antes de programar.
3. Implementar en una rama cuando corresponda.
4. Probar y registrar resultados.
5. Documentar errores y soluciones.
6. Revisar el módulo contra GeeLark.
7. Cerrar la tarea solo con evidencia.

## No comenzar todavía

No desplegar un clúster completo ni comprometerse con 50 instancias hasta que la prueba con una instancia y el inventario real de hardware respalden la decisión.
