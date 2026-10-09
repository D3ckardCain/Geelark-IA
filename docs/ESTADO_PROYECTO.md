# Estado del proyecto Geelark-IA

**Actualizado:** 2026-10-09  
**Fase:** 0 — consolidación de requisitos y evaluación de viabilidad  
**Estado de implementación:** no se ha confirmado en esta documentación ningún módulo funcional terminado.

## Resumen ejecutivo

Geelark-IA busca construir, por módulos, una plataforma de administración de instancias Android tomando GeeLark como referencia funcional. La prioridad es lograr un sistema útil para uso personal, con arquitectura distribuida, administración remota, documentación completa y costo operativo objetivo de 0 USD.

## Requisitos confirmados

1. Objetivo de costo operativo: 0 USD, sin tarjeta obligatoria, pruebas temporales, cargos automáticos ni APIs de pago.
2. Preferencia por software libre, local o autoalojado y arquitectura migrable.
3. Android de distintas versiones; meta inicial de hasta 50 instancias, ampliable.
4. Evaluar PC maestro/controlador y varios nodos trabajadores.
5. Proxmox es una opción preferida por la experiencia previa del usuario, pero falta validar la compatibilidad técnica.
6. Administración desde PC y móvil, incluso fuera de la red local, con acceso remoto seguro.
7. Investigar cómo mantener trabajos ya iniciados en los nodos si el controlador deja de estar disponible.
8. Operación offline/conectividad limitada donde resulte técnicamente viable.
9. Completar y probar cada módulo antes de comenzar el siguiente.
10. Para cada módulo: manual de usuario completo, documentación técnica, pruebas y comparación funcional con GeeLark.
11. Registrar tareas, problemas, soluciones, decisiones y avances en GitHub.
12. Los materiales de un proyecto anterior de postventa solo podrán servir de referencia contextual para ideas pertinentes; no se debe fusionar ese proyecto con Geelark-IA.

## Recursos conocidos

- PCs actuales mencionados: Intel Core i5 de 10.ª y 11.ª generación.
- RAM indicada: 32 GB por PC actual; planificación futura con equipos de al menos 16 GB.
- SSD de ejemplo: 500 GB NVMe.
- Número de máquinas flexible y ampliable.
- Windows y conexión a Internet forman parte del entorno conocido; también se evalúa Linux directo o Proxmox.

## Decisiones todavía no cerradas

- Hipervisor/sistema operativo definitivo.
- Método de virtualización/emulación Android por versión y sus requisitos de aceleración.
- Arquitectura del controlador, agentes de nodo, base de datos y mensajería.
- Stack de frontend/backend y mecanismo de acceso remoto.
- Seguridad, copias de respaldo, actualización, monitoreo y recuperación ante fallos.
- Viabilidad de 50 instancias simultáneas y recursos por instancia.
- Lista exacta de funciones de GeeLark a replicar, ordenadas por prioridad y comprobadas con evidencias.

## Riesgos y validaciones necesarias

- La cantidad de instancias depende de RAM, CPU, GPU, almacenamiento, versión Android y carga de las aplicaciones; no debe prometerse hasta completar pruebas.
- Proxmox no garantiza por sí solo que la virtualización Android sea compatible o eficiente.
- La conectividad remota pública requiere un diseño seguro; no exponer servicios administrativos directamente a Internet sin protección.
- Cada servicio candidato debe revisarse por límites, tarjeta requerida, condiciones comerciales, cuotas, suspensión y posibilidad de operar sin pago.
- Las funciones offline requieren especificación por módulo; no toda función puede operar sin Internet.

## Próximos pasos

1. Inventariar hardware real de cada PC (CPU exacta, RAM, disco libre, GPU, red y sistema actual).
2. Crear una matriz de funciones observables de GeeLark y definir criterios de aceptación.
3. Hacer una prueba técnica pequeña con una sola instancia Android y medir compatibilidad, rendimiento y estabilidad.
4. Comparar Linux directo y Proxmox con criterios explícitos, sin desplegar el clúster completo aún.
5. Aprobar la arquitectura solo después de registrar resultados y confirmar que cumple el objetivo de costo.
6. Convertir cada decisión y tarea en GitHub Issues y registrar soluciones en las incidencias correspondientes.

## Registro de actualización

- 2026-10-09: consolidación inicial de los requisitos compartidos en las conversaciones del proyecto. Este documento resume requisitos conocidos; no implica que se hayan realizado pruebas o implementaciones.
