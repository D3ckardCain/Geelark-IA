# Manual de usuario: reconciliación de inventario del agente

## Estado

El endpoint de reconciliación está en revisión en la rama apilada feat/agent-reconciliation. No se debe considerar listo para producción hasta que CI y revisión de seguridad terminen. No se ha probado en PCs físicas.

## Propósito

Después de iniciar o recuperar conectividad, el agente puede enviar una instantánea de inventario local para que el controlador compare:
- identidad de tarea, operación e instancia;
- propietario actual del nodo;
- assignment_epoch;
- leases;
- estado y resumen de resultado en el agente y el controlador.

La reconciliación **no cambia automáticamente** el estado de tareas ni de instancias. Su única escritura de dominio es un informe de auditoría que contiene hash del inventario y decisiones conservadoras. El controlador nunca convierte un estado unknown en éxito o fallo por falta de heartbeat.

## Cómo se usa desde el agente

1. Construir una lista de hasta 100 elementos de inventario local.
2. Cada elemento debe incluir task_id, operation_id, instance_id, assignment_epoch, local_state y result_summary.
3. local_state solo puede ser accepted, running, succeeded, failed o unknown.
4. Enviar la lista con AgentTransportRuntime.reconcile_inventory(). El cliente usa HTTPS, nonce, timestamp y request ID. Cada intento de reconciliación tiene un UUID propio (`reconciliation_id`): el supervisor conserva ese UUID al reintentar una solicitud cuyo ACK se perdió y genera otro UUID para una reconciliación nueva, aunque el inventario no haya cambiado.
5. Revisar el resultado devuelto y actuar solo mediante endpoints autorizados (accept/progress/result) o revisión manual. No ejecutar una acción solo porque la respuesta sugiera que hay una divergencia.
6. Si la solicitud falla, conservar el inventario y el mismo `reconciliation_id` al reintentar; el servidor devuelve el snapshot idempotente. Una reconciliación posterior debe usar un UUID nuevo para no recibir decisiones antiguas.
7. Tras recuperar conectividad, AgentSupervisor puede llamar al proveedor de inventario y entregar la respuesta a on_reconciliation. Ese callback debe ser rápido y no registrar secretos.

## Decisiones posibles

| Decisión | Significado | Acción segura |
|---|---|---|
| CONTINUE_SAME_EPOCH | El estado local y servidor coinciden y la asignación sigue vigente | Continuar bajo el mismo epoch |
| RESEND_PROGRESS | El agente conoce progreso que el servidor aún no confirmó | Reenviar progreso por el endpoint normal e idempotente |
| RESEND_TERMINAL_RESULT | El agente conserva un resultado terminal que el servidor no confirmó | Reenviar resultado por el endpoint normal e idempotente |
| ALREADY_CONFIRMED | Estado terminal y resumen coinciden | No repetir efectos; conservar evidencia local hasta ACK |
| SERVER_AHEAD_HOLD | El servidor conoce un estado posterior al journal local | No retroceder el servidor ni reasignar; revisar recibos |
| STALE_ASSIGNMENT_EPOCH | El epoch o propietario ya no coincide | No ejecutar ni reenviar efectos con el epoch obsoleto |
| LEASE_EXPIRED_HOLD / INSTANCE_LEASE_EXPIRED_HOLD | La asignación o instancia ya no tiene lease vigente | No renovar automáticamente ni reasignar solo por timeout |
| SERVER_TASK_MISSING_FROM_LOCAL_INVENTORY | El controlador mantiene una tarea activa que no aparece localmente | No marcarla fallida ni reasignarla; investigar el journal/disco |
| SERVER_TASK_OPERATION_STATE_MISMATCH | La tarea y la operación no coinciden en estado/resumen | Revisión manual y corrección transaccional explícita |
| TERMINAL_CONFLICT_MANUAL_REVIEW | El resultado local contradice el terminal del servidor | Preservar ambas evidencias; no sobrescribir |
| MANUAL_REVIEW_REQUIRED | Hay incertidumbre, incluyendo unknown | Bloquear acciones externas hasta reconciliar manualmente |
| UNKNOWN_TASK / IDENTITY_MISMATCH / TASK_NOT_OWNED_BY_NODE | La identidad no corresponde a una asignación autorizada | No actuar; revisar identidad, credenciales y auditoría |

Las decisiones son recomendaciones del protocolo, no autorización para ejecutar una operación. Todos los elementos incluyen automatic_mutation=false.

## Seguridad

- Solo nodos active/active pueden llamar a reconciliación; nodos pending siguen limitados a heartbeat, capacidades y consulta de estado.
- La carga está limitada a 1 MiB en HTTP, 100 elementos y 64 KiB por result_summary.
- Se rechazan task_id duplicados y JSON no válido.
- El informe guarda un hash del inventario y las decisiones, no el token bearer.
- La clave idempotente evita crear informes duplicados por reintentos con el mismo inventario.
- El handler bloquea las filas relevantes para comparar una vista consistente, pero no actualiza task.status, operation.status ni instance.owner/epoch.

## Offline y recuperación

La reconciliación necesita conexión HTTPS con el controlador. Mientras no hay red, el journal local conserva los recibos. Al recuperar conectividad, primero se despierta el sincronizador durable; la reconciliación es de solo comparación y puede ejecutarse en paralelo porque no aplica mutaciones de estado. Si se detecta una divergencia, se conserva el informe y no se infiere éxito/fallo.

## Pendientes

- [x] CI del commit ejecutable `5186c5700b5eb346485d4dd7f0880437dca54021` aprobado: 107 pruebas, migraciones PostgreSQL y `pip check` correctos; queda una advertencia deprecatoria de Starlette/httpx.
- [ ] Revisión de concurrencia e idempotencia del informe.
- [ ] Integración con el supervisor y proveedor de inventario real del journal.
- [ ] Manual técnico y estados revisados por seguridad.
- [ ] Aprobación antes de cualquier prueba en hardware físico.
