# Manual de retención y mantenimiento del almacenamiento de agentes

**Estado:** propuesta implementada en una rama draft; solo validable contra PostgreSQL desechable hasta que la PR sea revisada. No ejecutar la poda en una base real sin exportación, revisión y aprobación del operador.

## Política por tipo de dato

| Dato | Vencimiento/criterio | Regla de eliminación |
|---|---|---|
| Nonces anti-replay | expires_at <= now() - 1 hour (5 min de validez + 1 h de gracia) | Elegible tras exportación confirmada |
| Snapshots idempotentes: heartbeat, capabilities, modules_report, status_read | 24 horas desde creación | Elegible tras exportación confirmada |
| Snapshots idempotentes: task_fetch, task_accept, task_progress, task_result, reconcile, reconcile_inventory | 90 días desde creación | Elegible tras exportación confirmada |
| Scopes idempotentes desconocidos | Sin vencimiento automático | Nunca se podan por esta función |
| Informes seguros: todas las decisiones son ALREADY_CONFIRMED o CONTINUE_SAME_EPOCH | 90 días o mantener los 10.000 más recientes por nodo | Elegible tras exportación confirmada |
| Informes con unknown, conflicto, discrepancia, lease hold o decisión desconocida | Se conservan al menos 365 días | No se eliminan con confirmación genérica; requieren segunda confirmación de exportación y antigüedad mayor de 365 días |
| Auditoría de mantenimiento | Una fila por preview/poda | No se elimina automáticamente |

Los scopes desconocidos se conservan para que una operación futura no herede accidentalmente una política de expiración. Cualquier decisión futura de reconciliación que no esté en la allowlist segura se trata como evidencia de revisión y se conserva.

## Límites y riesgos

- El payload de inventario tiene un máximo de 100 elementos.
- La API usa un limitador de 60 solicitudes por minuto por nodo cuando se configura PostgresRateLimiter; el limitador en memoria es solo por proceso. No se debe afirmar un límite global hasta confirmar el ensamblado de producción.
- El límite de 10.000 aplica a informes seguros por nodo. La evidencia incierta/conflictiva puede crecer más allá de ese límite si no se exporta y archiva manualmente; se conserva deliberadamente para no borrar evidencia. Supervisar el tamaño de PostgreSQL y realizar archivado revisado.
- La garantía de replay de idempotencia es de 24 horas para telemetría y 90 días para operaciones/tareas/reconciliación. Pasado ese plazo, la clave ya no garantiza el mismo snapshot; el estado durable de tarea/operación sigue siendo la fuente de verdad.
- No hay cron, servicio externo ni API de pago. La limpieza es manual y local.

## Procedimiento manual

### 1. Preparar una exportación local protegida

Conéctate con una cuenta administradora de PostgreSQL usando un archivo de contraseña privado (no incluyas contraseñas en el DSN, comandos, GitHub ni logs). En psql, exporta las tablas a una carpeta cifrada con ACL restringida. \copy escribe en el equipo cliente:

```sql
\copy (SELECT * FROM geelark_control.agent_reconciliation_reports ORDER BY created_at, report_id) TO '/ruta/privada/agent-reconciliation-reports.csv' CSV HEADER
\copy (SELECT * FROM geelark_control.idempotency_records ORDER BY created_at, scope, idempotency_key) TO '/ruta/privada/idempotency-records.csv' CSV HEADER
\copy (SELECT * FROM geelark_control.agent_request_nonces ORDER BY seen_at, node_id, nonce) TO '/ruta/privada/agent-request-nonces.csv' CSV HEADER
\copy (SELECT * FROM geelark_control.agent_storage_maintenance_runs ORDER BY started_at, run_id) TO '/ruta/privada/agent-storage-maintenance-runs.csv' CSV HEADER
```

No guardes estos archivos en el repositorio ni los subas a un servicio cloud. Protege el directorio y registra en la issue de GitHub el nombre de archivo, tamaño y SHA-256, pero no adjuntes datos sensibles.

Linux:

```sh
sha256sum /ruta/privada/*.csv
```

Windows PowerShell:

```powershell
Get-FileHash 'C:\ruta\privada\agent-reconciliation-reports.csv' -Algorithm SHA256
```

Antes de continuar, verifica que los cuatro archivos existen, tienen tamaño razonable y los hashes se han registrado en el control de cambios interno. La confirmación de exportación de la función es una declaración del operador, no una verificación criptográfica de los archivos.

### 2. Preview (no borra filas)

```sql
SELECT * FROM geelark_control.prune_agent_storage(false, false);
```

Revisa los contadores de elegibles y los motivos de retención. La función registra el preview en agent_storage_maintenance_runs.

### 3. Podar datos vencidos e informes seguros

Solo después de verificar la exportación:

```sql
SELECT * FROM geelark_control.prune_agent_storage(true, false);
```

Esto elimina nonces con más de una hora de gracia, snapshots idempotentes conocidos vencidos y solo informes seguros que superen 90 días o los últimos 10.000 por nodo. Los scopes desconocidos y los informes de revisión se conservan.

### 4. Archivar evidencia incierta/conflictiva antigua (opcional)

No ejecutes este paso automáticamente. Requiere exportación revisada, autorización explícita y que la evidencia tenga más de 365 días:

```sql
SELECT * FROM geelark_control.prune_agent_storage(true, true);
```

Este segundo parámetro permite borrar únicamente informes de revisión de más de 365 días después de confirmar la exportación. Los registros de mantenimiento conservan el rol de PostgreSQL que ejecutó el procedimiento, qué confirmaciones dio y cuántas filas se borraron. No son un registro inmutable: una cuenta propietaria con permisos suficientes puede modificarlos.

## Recuperación y respuesta a errores

- Si el preview devuelve contadores inesperados, no ejecutes la poda. Conserva el preview y abre una incidencia con los conteos y versiones, sin adjuntar credenciales ni payloads sensibles.
- Si se borran datos por error, detén nuevos intentos de limpieza. Restaura los CSV a una base de staging aislada y verifica integridad antes de decidir una recuperación. No reinsertes nonces ni snapshots idempotentes antiguos directamente en producción: podrían reabrir ventanas de replay o alterar el comportamiento de idempotencia.
- Los informes de reconciliación pueden restaurarse primero en un esquema/base de archivo de solo lectura para consulta. Cualquier recuperación a producción requiere revisión manual de IDs, epochs y estados.
- No se ha probado la restauración en una base real. La CI usa PostgreSQL 16 desechable.