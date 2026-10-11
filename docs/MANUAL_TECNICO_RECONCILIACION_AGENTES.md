# Manual técnico: protocolo de reconciliación del agente

## Contrato de entrada

POST /agent/v1/reconcile/inventory usa el transporte HTTPS autenticado y requiere:
- Bearer token vigente;
- nonce, timestamp y request ID anti-replay;
- Idempotency-Key;
- principal active/active (pending se rechaza por política);
- schema_version=1 e inventory con hasta 100 elementos.

Cada elemento contiene task_id, operation_id, instance_id, assignment_epoch, local_state y result_summary. local_state solo acepta accepted, running, succeeded, failed o unknown. El resultado es JSON finito de hasta 64 KiB por elemento. El middleware limita el cuerpo HTTP a 1 MiB.

## Decisiones

El handler bloquea las filas de tarea/instancia/operación relevantes, comprueba identidad, propietario, epoch, leases y coherencia entre el estado de agent_tasks y operations. No actualiza estados de dominio; solo inserta una fila de auditoría en agent_reconciliation_reports.

Decisiones principales:
- CONTINUE_SAME_EPOCH: estados y resumen coinciden.
- RESEND_PROGRESS / RESEND_TERMINAL_RESULT: el estado local parece ir por delante; usar el endpoint normal e idempotente, no mutar directamente la base de datos.
- ALREADY_CONFIRMED: terminal y resumen coinciden.
- STALE_ASSIGNMENT_EPOCH, INSTANCE_LEASE_EXPIRED_HOLD, DELIVERY_LEASE_EXPIRED_HOLD: no ejecutar ni reasignar automáticamente.
- MANUAL_REVIEW_REQUIRED / TERMINAL_CONFLICT_MANUAL_REVIEW / SERVER_TASK_OPERATION_STATE_MISMATCH: preservar evidencia y bloquear automatismos.
- SERVER_TASK_MISSING_FROM_LOCAL_INVENTORY: la tarea activa existe en servidor, pero el agente no la reporta; no marcarla fallida ni reasignarla por timeout.
- UNKNOWN_TASK / IDENTITY_MISMATCH / TASK_NOT_OWNED_BY_NODE: rechazar cualquier acción basada en esa entrada.

Todos los elementos llevan automatic_mutation=false. Los estados unknown nunca se convierten automáticamente en éxito/fallo.

## Persistencia e idempotencia

Migration 0006 crea agent_reconciliation_reports:
- report_id UUID;
- node_id;
- inventory_sha256;
- inventory_count;
- decisions JSONB;
- created_at.

La ruta usa execute_idempotent con una clave derivada del nodo y del hash canónico del inventario. Un reintento idéntico devuelve el snapshot previo; no inserta un segundo informe. Cambiar el inventario genera una clave distinta.

El handler no cambia task.status, operation.status, instance.owner_node_id, assignment_epoch ni leases. También compara nodo, instancia y epoch de la fila operation con los de agent_tasks; la divergencia se informa como SERVER_TASK_OPERATION_IDENTITY_MISMATCH. El informe de auditoría es la única escritura de dominio. La lectura se hace con FOR UPDATE para comparar un conjunto consistente durante la transacción.

## Cliente y supervisor

AgentTransportRuntime.reconcile_inventory(inventory) envía el payload con HTTPS y clave idempotente estable. AgentNodeSupervisor acepta un proveedor de inventario opcional y ejecuta la reconciliación en un worker separado, sin bloquear heartbeat/capacidades. Lo invoca tras el primer heartbeat exitoso y al recuperar conectividad, entrega el AgentResponse a on_reconciliation y aplica una espera de reintento si falla. Conserva el UUID por intento y lo renueva para una solicitud posterior. El callback debe interpretar las decisiones, no ejecutar shell/ADB ni convertir estados automáticamente.

La fábrica build_agent_components permite inyectar el proveedor y el callback. El proceso instalable todavía debe construir el inventario desde el journal real y configurar el callback de manera segura.

## Límites de validación

La prueba de integración existente cubre TLS real en loopback, journal SQLite, resultados PostgreSQL y pérdida de ACK. La reconciliación se incorpora a esa misma prueba para verificar ALREADY_CONFIRMED y que el reintento con el mismo reconciliation_id no crea un segundo informe. CI PostgreSQL cubre decisiones conservadoras y auditoría. Esto no prueba todavía reinicio del servicio real, inventario de un motor Android, recuperación manual ni despliegue físico.
