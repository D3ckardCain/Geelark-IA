# Requisitos iniciales — Geelark-IA

Este documento separa las reglas confirmadas de las características que todavía requieren definición. Los objetivos técnicos no se consideran implementados hasta verificarlos.

## REQ-001 — Objetivo de costo operativo de 0 USD

**Prioridad:** crítica.

Evitar dependencias que requieran pagos obligatorios, tarjeta bancaria, pruebas temporales, cargos automáticos o APIs de pago.

**Criterio de aceptación:** antes de adoptar cada servicio, registrar precio, requisito de tarjeta, límites, cuotas, condiciones de uso, almacenamiento, ancho de banda, ejecución y riesgo de suspensión. Las funciones críticas deben tener una alternativa sostenible sin pagos obligatorios.

## REQ-002 — Desarrollo incremental

Construir el sistema por pasos pequeños, con explicación y comprobación antes de avanzar.

**Criterio de aceptación:** cada tarea tiene objetivo, pasos, resultado esperado, pruebas y estado documentado. No se inicia el siguiente módulo dependiente antes de cerrar el actual.

## REQ-003 — Trazabilidad en GitHub

Registrar requisitos, decisiones, tareas, incidencias, soluciones, pruebas y cambios.

**Criterio de aceptación:** las tareas relevantes se vinculan a Issues, commits o PRs según corresponda. Las incidencias registran reproducción, resultado esperado y real, causa conocida o hipótesis, solución y verificación.

## REQ-004 — Documentación completa por módulo

Cada módulo requiere manual de usuario y documentación técnica.

**Criterio de aceptación:** documentar propósito, requisitos, instalación, configuración, opciones, procedimientos, errores frecuentes, seguridad, pruebas, limitaciones y resolución de problemas.

## REQ-005 — Comparación funcional con GeeLark

GeeLark es la referencia funcional para las características seleccionadas.

**Criterio de aceptación:** documentar el comportamiento de referencia, configuración, resultado esperado, resultado probado en Geelark-IA, evidencias y diferencias. No afirmar paridad sin prueba.

## REQ-006 — Operación offline cuando sea viable

Diseñar funcionamiento offline o con conectividad limitada para las operaciones que lo permitan.

**Criterio de aceptación:** cada módulo identifica qué funciona offline, qué requiere red, cómo se guardan las operaciones pendientes, cómo se reintentan y cómo se resuelven conflictos cuando corresponda.

## REQ-007 — Seguridad y secretos

**Criterio de aceptación:** no almacenar secretos en el repositorio, commits, logs ni incidencias; usar permisos mínimos y documentar los controles de seguridad aplicables.

## Por definir con el usuario

- Problema principal y objetivo de la primera versión.
- Funciones prioritarias.
- Inventario real de hardware.
- Versiones Android necesarias y capacidad objetivo.
- Acceso local/remoto y roles de usuario.
- Arquitectura y tecnologías.
- Requisitos concretos de rendimiento, disponibilidad y respaldo.

Estos elementos no deben tratarse como decisiones aprobadas hasta acordarlos.
