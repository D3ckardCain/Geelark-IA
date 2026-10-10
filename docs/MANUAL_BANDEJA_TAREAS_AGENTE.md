# Manual técnico — bandeja durable de tareas del agente

**Estado:** implementación en borrador en PR #51. No activar en producción hasta que CI, revisión de seguridad y reconciliación estén completos.

## Objetivo y límites

La bandeja entrega asignaciones tipadas a agentes mediante HTTPS saliente. No abre conexiones entrantes hacia los nodos y no reutiliza `outbox_events`, que sigue siendo una cola interna del controlador.

La entrega no ejecuta la asignación. No se implementan shell arbitrario, ADB remoto ni ejecución Android.

## Flujo

1. El servicio transaccional valida la solicitud de asignación y reserva recursos.
2. En una sola transacción escribe la operación, reserva, evento outbox y fila `agent_tasks`.
3. El agente activo solicita una tarea con `POST /agent/v1/tasks/claim`, nonce nuevo y clave idempotente.
4. El controlador reclama una sola tarea mediante `FOR UPDATE SKIP LOCKED`, registra una lease de entrega de 30 segundos y devuelve un payload versionado.
5. El agente acepta la tarea con `POST /agent/v1/tasks/{task_id}/accept`.
6. El agente informa progreso por `/progress` y resultado tipado por `/result`.
7. Cada transición vuelve a comprobar identidad, estado de credencial, propietario, epoch y lease de la instancia.

## Estados

- `queued`: tarea creada y disponible.
- `delivered`: entregada al agente; puede volver a ofrecerse cuando vence la lease de entrega si no se aceptó.
- `accepted`: agente confirma recepción; no significa que Android esté listo.
- `running`: el adaptador reporta trabajo en curso.
- `succeeded`, `rejected`, `failed`: resultado terminal tipado.
- `unknown`: estado incierto; no se interpreta como éxito ni fallo y requiere reconciliación.
- `cancelled`: cancelada por un flujo de control autorizado futuro.

## Idempotencia y concurrencia

- La misma clave de claim devuelve el snapshot de respuesta original.
- Las claves nuevas no vuelven a reclamar una tarea cuya lease de entrega sigue vigente.
- La consulta de claim bloquea la fila con `SKIP LOCKED` para impedir que dos workers entreguen la misma fila a la vez.
- Las escrituras de aceptación/progreso/resultado usan la transacción idempotente y bloquean la tarea, instancia y operación.
- Un propietario o epoch distinto, lease vencida, resultado terminal contradictorio o tarea ajena se rechazan.
- La lease de entrega (30 segundos) es distinta de la lease de asignación de la instancia. La expiración de cualquiera no autoriza por sí sola a iniciar la instancia en otro nodo.

## Estados pending y active

- Un nodo `pending` puede enviar heartbeat, capacidades y consultar su propio estado.
- Solo el par `active/active` puede reclamar tareas, aceptar, reportar progreso o resultado.
- Revocación o cambio de epoch impide nuevas mutaciones.
- La bandeja no activa listener por sí sola; la configuración del servidor HTTPS debe revisarse por separado.

## Offline

- El claim, aceptación y reportes necesitan conexión con el controlador.
- El journal local puede conservar recibos de resultados; la integración automática con el journal y la reconciliación siguen pendientes.
- Si se pierde la respuesta de claim, se usa la misma clave idempotente para recuperar el snapshot. Una reclamación nueva solo podrá volver a ofrecer una tarea cuando la lease de entrega haya expirado.
- Si se pierde la conexión tras ejecutar una operación, no asumir éxito ni fallo: registrar incertidumbre y reconciliar antes de reasignar.

## Validación requerida antes de integración

- CI PostgreSQL 16 para todas las migraciones y constraints.
- Concurrencia de doble claim y recuperación tras expiración de lease.
- Revocación durante la petición y cambio de epoch.
- Idempotencia de claim/accept/progress/result y conflicto de resultado terminal.
- Aislamiento entre nodos y denegación de `pending`.
- Integración con journal local y reconciliación tras reconexión.
- Revisión de manual de usuario y manual técnico.
