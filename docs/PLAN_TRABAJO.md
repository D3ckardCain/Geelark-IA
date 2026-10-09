# Plan de trabajo — Geelark-IA

El plan detallado de paridad funcional está en [PLAN_PARIDAD_GEELARK.md](PLAN_PARIDAD_GEELARK.md). Este archivo resume el orden operativo y las reglas de ejecución.

## Objetivo confirmado por el usuario

Replicar desde cero las funciones de GeeLark aplicables a Android, usando hardware físico/local y herramientas gratuitas, sin depender de dispositivos en la nube ni servicios de pago obligatorios. iOS queda fuera. La equivalencia se verificará por función; no se dará por garantizada de antemano.

## Fases

1. **Inventario funcional de GeeLark:** revisar documentación y flujos; crear matriz de funciones, requisitos, dependencias, pruebas y diferencias.
2. **Auditoría de hardware:** confirmar PC, sistema operativo, CPU, RAM, almacenamiento, GPU, teléfonos Android, cables, red y capacidad esperada.
3. **Prueba técnica:** controlar un teléfono Android real localmente y medir conexión, pantalla, entrada, archivos, reconexión y rendimiento.
4. **Arquitectura:** elegir tecnologías solo después de las pruebas, comprobando licencias, costos, límites, seguridad y migrabilidad.
5. **Núcleo local:** inventario/perfiles, conexión y control de dispositivos.
6. **Operaciones Android:** aplicaciones, archivos, red/proxy y biblioteca local.
7. **Automatización:** RPA visual, ejecución programada, colas, sincronizador multi-dispositivo y plantillas.
8. **Integración:** API local/CLI, logs, historial, analítica y, si se aprueba, usuarios/permisos.
9. **Funciones avanzadas:** IA local condicionada al hardware; recursos/marketplace local.
10. **Offline y mantenimiento:** caché, colas, recuperación, instalación, copias de seguridad y actualizaciones.
11. **Validación integral:** matriz de paridad, pruebas, manuales y lista explícita de funciones no equivalentes/no viables.

## Reglas de avance

- Una fase cada vez; no pasar a la siguiente hasta completar pruebas, documentación y aceptación de la fase actual.
- Cada módulo tiene una issue de GitHub y criterios de aceptación.
- Cada módulo debe incluir manual de usuario completo y documentación técnica.
- Costo operativo objetivo: 0 USD; no tarjeta, pruebas temporales ni APIs de pago obligatorias.
- Registrar decisiones, problemas, soluciones, resultados y cambios en GitHub.
- No afirmar paridad sin evidencia ni asumir hardware o tecnologías aún no confirmados.

## Primera tarea

Completar el inventario funcional inicial y recopilar especificaciones reales del hardware disponible. No iniciar implementación de gran escala ni fijar el stack antes de la prueba técnica.
