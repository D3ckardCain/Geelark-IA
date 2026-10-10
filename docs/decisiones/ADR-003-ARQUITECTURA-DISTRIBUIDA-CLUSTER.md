# ADR-003 — Arquitectura distribuida para clúster heterogéneo

- **Fecha:** 2026-10-09
- **Estado:** aceptado como requisito de diseño; tecnologías de infraestructura pendientes de prueba.
- **Contexto:** Geelark-IA debe aprovechar múltiples PC físicas heterogéneas para ejecutar instancias Android virtualizadas. Una PC Master centraliza administración y el usuario podrá administrar remotamente desde PC/teléfono autenticado.
- **Decisión:** la arquitectura de producto se diseñará desde el inicio para un plano de control y varios nodos de ejecución. La aplicación de escritorio y la API local siguen siendo componentes válidos, pero no pueden asumir que todas las instancias viven en un único equipo. Cada nodo tendrá un agente autenticado, capacidades declaradas y comunicación restringida. Un planificador asignará instancias/tareas por compatibilidad y recursos disponibles.
- **Infraestructura aún no decidida:** Proxmox VE y Linux directo son candidatos. No se declara elegido el hipervisor, sistema operativo definitivo ni motor Android hasta ejecutar una prueba de concepto con dos nodos heterogéneos.
- **Resiliencia:** no hacer de la interfaz Master un punto de fallo que detenga por sí solo instancias ya ejecutándose cuando el diseño técnico lo permita. No prometer alta disponibilidad, failover automático o migración en vivo sin pruebas. Se deben evitar asignaciones duplicadas y reintentos inseguros.
- **Datos:** metadatos de control separados de discos de instancias y artefactos. Para el MVP se prefiere almacenamiento local por nodo y backups explícitos; almacenamiento compartido es opcional y requiere pruebas.
- **Seguridad:** red privada, autenticación de nodos, mínimo privilegio, auditoría redactada. No exponer ADB, shell ni consolas de hipervisor a Internet.
- **Coste:** software y servicios obligatorios con objetivo de 0 USD; revisar condiciones y licencias reales. Hardware, electricidad y conectividad son costes indirectos.
- **Consecuencias:** se requiere diseñar contrato del agente, modelo de recursos, scheduler, política de asignación/recuperación, instalación y actualización de nodos, y pruebas de desconexión. La implementación será portable entre infraestructuras para reducir vendor lock-in.
- **Referencia detallada:** [Arquitectura de clúster heterogéneo](../ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- **Seguimiento:** issue dedicada para integrar el clúster en la arquitectura, probar Proxmox VE frente a Linux directo y validar dos nodos.

## Regla de alta y ejecución de nodos

Un nodo en estado `pending_enrollment` no es elegible para tareas ni operaciones. Hasta la aprobación administrativa registrada, solo puede enviar heartbeat, capacidades/inventario no sensible y consultar su estado de inscripción. El plano de control debe aplicar esta denegación del lado servidor en cada ruta de asignación/aceptación; la interfaz y el agente no son fronteras de seguridad suficientes.

La transición a ejecutor exige credencial individual válida, aprobación registrada, compatibilidad de versión y reconciliación del estado real. Los estados ausentes, revocados, desconocidos o inconsistentes se deniegan por defecto. Tras una desconexión no se habilita automáticamente un nodo pendiente.

**Prueba de aceptación obligatoria:** intentar enviar una tarea desde un nodo pendiente debe producir rechazo auditable y cero efectos secundarios (sin asignación, instancia ni operación iniciada). La regla detallada está en [Contrato del agente y planificador](../CONTRATO_AGENTE_NODO_PLANIFICADOR.md#13-puerta-de-ejecucion-para-nodos-pendientes).
