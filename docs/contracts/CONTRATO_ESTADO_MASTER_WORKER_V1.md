# Contrato de estado Master/Worker v1

**Estado:** contrato propuesto y versionado; todavía no está conectado a una API operativa.  
**Versión:** `1.0`  
**Coste:** sin dependencias ni servicios externos obligatorios.

## Propósito

Definir la representación de solo lectura que PC-MASTER podrá presentar para un Worker y sus módulos. El contrato separa autorización, salud y frescura, evita secretos/logs arbitrarios y no transporta tareas ni comandos.

- Esquema JSON: `docs/contracts/master-worker-status-v1.schema.json`
- Ejemplo ficticio: `docs/contracts/examples/master-worker-status-v1.example.json`
- El ejemplo sirve para pruebas; no describe el estado real de ningún equipo.

## Semántica normativa

- **Autoridad:** `authorization_state` es asignado por el Master/controlador, nunca por el Worker. Un valor `unknown` no concede permisos.
- **Autorización:** `pending` puede informar heartbeat, capacidades no sensibles y consultar su propio estado; no puede aceptar tareas ni ejecutar operaciones.
- **Salud:** `reported_health_state` conserva la declaración no autoritativa del Worker; `health_state` es derivado por el Master de forma independiente. `unknown` no se convierte en éxito ni fallo y no habilita reintentos, reasignaciones o reconciliación automática.
- **Frescura:** `freshness.observed_at` y `age_seconds` se calculan usando el reloj del Master al recibir/observar la evidencia. No confiar únicamente en el reloj del Worker. El esquema rechaza `healthy` si la frescura es `stale`, `missing` o `unknown`; si no hay heartbeat, tampoco permite salud `healthy` ni frescura `fresh`.
- **Caché/offline:** `source=master-cache` indica que el snapshot se leyó de la caché local; `state=stale`/ `missing`/ `unknown` debe mostrarse como tal, nunca como saludable por defecto.
- **Capacidades:** lista cerrada de identificadores no sensibles. No incluye shell, ADB, ejecución de tareas ni capacidades arbitrarias.
- **Módulos:** cada estado incluye origen, versión/fecha si se conocen y un código de error acotado. No incluir trazas, cuerpos HTTP, rutas privadas, tokens ni logs sin redactar.
- **Extensibilidad:** cambios incompatibles requieren una nueva versión de contrato. En v1 se rechazan propiedades desconocidas para fallar de forma visible y evitar que productores/consumidores interpreten campos de forma diferente.

## Campos y límites

| Campo | Semántica |
|---|---|
| `schema_version` | Versión del contrato; en este esquema es `1.0`. |
| `snapshot_id` | UUID único del snapshot. |
| `generated_at` | Instante UTC de generación por el Master. |
| `source` | `master-live` o `master-cache`. |
| `node.authorization_state` | Estado autoritativo `pending/active/revoked/unknown`. |
| `node.reported_health_state` | Declaración del Worker (`healthy/degraded/unhealthy/unknown` o `null`), no autoritativa. |
| `node.health_state` | Estado derivado por el Master (`healthy/degraded/offline/unknown`), separado de autorización y del reporte del Worker. |
| `node.capabilities` | Solo capacidades explícitamente permitidas por el esquema. |
| `node.modules[].state` | `operational/degraded/not-installed/unknown`. |
| `freshness` | Estado, edad, umbral y hora de observación del lado Master. |

## Qué no forma parte de v1

- Credenciales, tokens, secretos o datos de usuarios.
- Tareas, comandos, argumentos, payloads de ejecución, shell o ADB.
- Resolución de estados terminales `unknown`.
- Acciones de control o mutaciones desde la UI.
- Logs arbitrarios o mensajes de error sin normalizar.

La discrepancia del stack de agentes que motiva esta separación está registrada en [issue #71](https://github.com/D3ckardCain/Geelark-IA/issues/71). La integración real debe esperar a que ese campo quede separado en la fuente de verdad.

## Validación

Las pruebas usan la biblioteca estándar de Python para comprobar que el JSON Schema y el ejemplo son JSON válido, que el ejemplo cumple las reglas declaradas y que se rechazan propiedades/capacidades no permitidas. El validador de pruebas cubre el subconjunto usado por este esquema; no se presenta como una implementación completa de JSON Schema Draft 2020-12.

Antes de integrar el contrato en un servicio real hacen falta revisión de seguridad, pruebas de compatibilidad y una política versionada de transición. No desplegar en PCs físicas como parte de esta fase.
