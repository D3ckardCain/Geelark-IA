# Proveedor interno de snapshots Master/Worker v1

**Estado:** implementación interna en revisión; no expone HTTP y no está conectada al panel.  
**Coste:** no añade servicios externos ni dependencias de pago.

## Propósito

`PostgresStatusSnapshotProvider` implementa el puerto `StatusSnapshotProvider` para leer un único nodo desde la tabla autoritativa `geelark_control.nodes` y convertirlo al contrato `master-worker-status-v1`. No consulta directamente a los Workers, no modifica asignaciones y no escribe en PostgreSQL.

## Uso interno

El consumidor debe autenticar y autorizar al operador antes de invocar el proveedor. La conexión debe usar un rol PostgreSQL de solo lectura; el código del adaptador ejecuta únicamente una consulta `SELECT`. No se añade endpoint HTTP, listener ni acceso público en esta fase.

La llamada `get_node_snapshot(UUID)` devuelve el snapshot con los campos de contrato v1 o `None` si el nodo no existe. El adaptador no concede permisos: `pending` no se convierte en `active`, y estados administrativos que no caben en el contrato se representan como `unknown`.

## Reglas de seguridad y frescura

- El Master genera `snapshot_id` y `generated_at`; el timestamp del Worker no se usa para calcular la frescura del nodo.
- Umbral de heartbeat: 90 segundos. Sin heartbeat: `missing/offline`; heartbeat caducado: `stale/offline`; timestamp futuro más allá de la tolerancia: `unknown`.
- La salud autoritativa se deriva de la declaración reportada y la frescura. `reported_health_state` permanece como evidencia no autoritativa.
- Los módulos sin reporte, con timestamp inválido, caducados o asociados a un nodo obsoleto se devuelven como `unknown`, con un código de error normalizado.
- Capacidades desconocidas se omiten. Los nombres de nodo incompatibles con el contrato se sustituyen por un identificador estable basado en el UUID, sin exponer texto inesperado en el panel.
- El proveedor no incluye credenciales, secretos, logs libres, tareas ni comandos.

## Offline

Este adaptador es una lectura en vivo de PostgreSQL y requiere conectividad con la base de datos de PC-MASTER. La caché offline no está implementada aquí; deberá ser un adaptador separado que marque `source=master-cache` y preserve la marca de frescura original. La UI no debe mostrar un snapshot cacheado como actual.

## Validación

Las pruebas cubren snapshots frescos, heartbeat ausente/obsoleto, reloj futuro, estado de autorización conservador, saneamiento de capacidades/módulos y el contrato de solo lectura del adaptador. Son pruebas unitarias con conexión simulada; no prueban todavía permisos PostgreSQL reales, autenticación humana ni hardware físico.

## Fuera de alcance

- No hay endpoint administrativo ni autenticación de operador implementados.
- No hay conexión desde el prototipo HTML.
- No se despliega ni modifica ninguna PC física.
- No se habilitan shell, ADB, ejecución de tareas ni reconciliación.
