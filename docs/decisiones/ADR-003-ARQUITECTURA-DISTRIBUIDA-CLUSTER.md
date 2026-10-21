# ADR-003 — Arquitectura distribuida para clúster heterogéneo

- **Fecha:** 2026-10-09
- **Estado:** decisión de arquitectura confirmada; aprovisionamiento y runtime Android pendientes de validación física.
- **Contexto:** Geelark-IA debe aprovechar múltiples PC físicas heterogéneas para ejecutar instancias Android virtualizadas. Una PC Master centraliza administración y el usuario podrá administrar remotamente desde PC/teléfono autenticado.
- **Decisión:** la arquitectura de producto se diseñará desde el inicio para un plano de control y varios nodos de ejecución. La aplicación de escritorio y la API local siguen siendo componentes válidos, pero no pueden asumir que todas las instancias viven en un único equipo. Cada nodo tendrá un agente autenticado, capacidades declaradas y comunicación restringida. Un planificador asignará instancias/tareas por compatibilidad y recursos disponibles.
- **Decisión de infraestructura:** PC-MASTER permanece como aplicación Windows; los PC WORKER físicos utilizarán Debian 13 directamente como sistema base previsto. GeeLark-IA será responsable del descubrimiento, la adopción aprobada, el despliegue del agente y la administración de las herramientas locales de virtualización Android. El arranque por red desde equipos vacíos se validará según las capacidades de firmware y LAN.
- **Resiliencia:** no hacer de la interfaz Master un punto de fallo que detenga por sí solo instancias ya ejecutándose cuando el diseño técnico lo permita. No prometer alta disponibilidad, failover automático o migración en vivo sin pruebas. Se deben evitar asignaciones duplicadas y reintentos inseguros.
- **Datos:** metadatos de control separados de discos de instancias y artefactos. Para el MVP se prefiere almacenamiento local por nodo y backups explícitos; almacenamiento compartido es opcional y requiere pruebas.
- **Seguridad:** red privada, autenticación de nodos, mínimo privilegio, auditoría redactada. No exponer ADB, shell ni interfaces administrativas de los nodos a Internet.
- **Coste:** software y servicios obligatorios con objetivo de 0 USD; revisar condiciones y licencias reales. Hardware, electricidad y conectividad son costes indirectos.
- **Consecuencias:** se requiere diseñar contrato del agente, modelo de recursos, scheduler, política de asignación/recuperación, instalación y actualización de nodos, y pruebas de desconexión. La implementación será portable entre infraestructuras para reducir vendor lock-in.
- **Referencia detallada:** [Arquitectura de clúster heterogéneo](../ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- **Seguimiento:** validar el aprovisionamiento de extremo a extremo en dos nodos físicos, incluida la instalación por red, la autorización del agente y el inicio de Android.
