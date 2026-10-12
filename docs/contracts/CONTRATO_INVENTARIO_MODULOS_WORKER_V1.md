# Contrato de inventario de módulos Worker v1

**Versión:** 1  
**Estado:** en revisión; aún no integrado en PC-MASTER.  
**Ruta:** `PUT /agent/v1/modules`

## Autorización

Solo nodos `active` con credencial activa pueden publicar el inventario. Un nodo `pending` recibe `403 PERMISSION_DENIED` y conserva únicamente heartbeat, capacidades y consulta de su propio estado. Este endpoint no acepta tareas ni cambia la autorización del nodo.

## Payload y validación

- JSON Schema: [worker-module-inventory-v1.schema.json](worker-module-inventory-v1.schema.json).
- Ejemplo ficticio: [worker-module-inventory-v1.example.json](examples/worker-module-inventory-v1.example.json).
- `schema_version` debe ser `1`; máximo 32 entradas; no se permiten IDs duplicados ni propiedades desconocidas.
- IDs permitidos: `agent-supervisor`, `agent-transport`, `agent-guard`, `task-journal`, `android-engine`. Añadir otro exige actualizar registro, esquema y pruebas en el mismo cambio.
- Estados declarables: `operational`, `degraded`, `not-installed`, `unknown`.
- `version` y `error_code` son opcionales. Los códigos son acotados, sin mensajes arbitrarios.

El servidor genera `checked_at` con su reloj y `source=agent-report`; no confía en timestamps del Worker. No se admiten logs, trazas, rutas privadas, tokens, comandos ni payloads de tareas.

## Frescura y lectura

- Si el último heartbeat del nodo tiene más de 90 segundos, los estados de módulos se presentan como `unknown` con `NODE_STALE`.
- Si el informe de módulo tiene más de cinco minutos, se presenta como `unknown` con `REPORT_STALE`.
- La derivación usa el reloj del Master. Un estado `operational` reportado no demuestra por sí solo que el módulo esté realmente sano.
- La persistencia usa la columna `module_reports` de PostgreSQL añadida por `0004_worker_module_inventory.sql`.

## Límite de integración

Este contrato cubre el reporte de agente y su consulta de estado propio. Todavía no existe una ruta administrativa de snapshot v1 conectada al panel PC-MASTER; esa integración sigue bloqueada hasta confirmar la fuente de verdad y la autenticación/autorización del operador. No se ha desplegado en PCs físicas.
