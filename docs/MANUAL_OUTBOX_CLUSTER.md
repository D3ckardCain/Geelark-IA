# Manual técnico: dispatcher recuperable del outbox

**Estado:** implementación local en revisión; no envía mensajes por red.  
**Dependencia:** PR #34 (persistencia transaccional) y el esquema de PR #32.

## 1. Objetivo

El outbox guarda la intención de asignación en la misma transacción que propietario, epoch, reserva y operación. El dispatcher reclama eventos con leases para que un proceso pueda reiniciarse y otro trabajador recupere el trabajo abandonado.

## 2. Estados

- `pending`: listo cuando `available_at <= now()`.
- `inflight`: reclamado por un worker con `claimed_by` y `claim_until`.
- `delivered`: el transporte futuro confirmó la entrega; no significa que Android haya terminado la operación.
- `dead`: alcanzó el máximo de intentos y requiere diagnóstico/revisión; no se elimina silenciosamente.

Un evento `inflight` con claim expirado puede volver a reclamarse. Cada claim incrementa `attempt_count`.

## 3. API local del paquete

- `claim_outbox_batch(conn, worker_id, batch_size=20, lease_seconds=30)`: reclama un lote con `FOR UPDATE SKIP LOCKED`; el claim se confirma antes de devolverlo.
- `mark_outbox_delivered(conn, event_id, worker_id)`: solo confirma si el worker sigue siendo dueño del claim y el lease continúa vigente. Devuelve `False` si perdió autoridad.
- `retry_outbox_event(..., error_code, delay_seconds=5, max_attempts=8)`: reprograma o marca `dead`. Solo actúa sobre un claim vigente del worker; devuelve `None` si el claim se perdió.

Los códigos de error se limitan a identificadores saneados (A-Z, 0-9 y guion bajo); no guardar trazas ni secretos.

## 4. Garantías y límites

- La reclamación es concurrente segura entre workers de PostgreSQL.
- El lease evita que un worker viejo confirme o reprograme después de que otro haya reclamado el evento.
- El envío futuro será **al menos una vez**, no exactamente una vez. Un worker puede enviar y caer antes de marcar delivered; por eso el agente deberá deduplicar por operación/evento y validar `assignment_epoch`.
- Este paquete todavía no abre sockets, no envía solicitudes HTTP y no ejecuta comandos en nodos.
- No reemplaza autenticación, autorización, TLS, fencing del agente ni reconciliación.
- No hay failover automático ni despliegue en las PC físicas.

## 5. Pruebas

La CI usa PostgreSQL 16 desechable para comprobar:
- dos workers no reclaman el mismo evento;
- un claim expirado se recupera y aumenta el contador;
- el worker anterior no puede confirmar/reprogramar;
- el backoff aplaza la próxima entrega;
- al alcanzar el límite, el evento pasa a `dead`.

Antes de habilitar el transporte real se debe definir un contrato de ACK del agente, deduplicación durable, límites de tamaño de payload, autenticación de nodos, retención y procedimiento para inspeccionar/reprocesar eventos `dead`.
