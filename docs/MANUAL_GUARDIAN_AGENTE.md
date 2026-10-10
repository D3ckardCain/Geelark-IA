# Manual técnico: guardián local del agente

**Estado:** prototipo offline en revisión; no ejecuta Android ni acepta conexiones de red.  
**Dependencias de ejecución:** solo biblioteca estándar de Python y SQLite.

## 1. Propósito

`packages/cluster-agent-guard` mantiene un journal local por nodo:
- `instance_fences`: último propietario local y `assignment_epoch` aceptado por instancia.
- `operation_receipts`: hash canónico, estado y resultado saneado por `operation_id`.
- `schema_migrations`: versión del esquema local.

SQLite usa WAL y sincronización FULL. En POSIX el código crea/restringe el archivo a modo 0600 y rechaza rutas simbólicas; en Windows la instalación debe aplicar ACL para que solo la cuenta del agente y administradores autorizados accedan al archivo. Debe residir en disco local persistente; no compartir el archivo activo por NFS ni usar `:memory:` para el agente real.

## 2. Aceptación de comando

Antes de llamar a `AgentJournal.accept_command`, una futura capa de transporte debe autenticar el controlador, autorizar la operación y validar el contrato Pydantic. El journal:
1. Comprueba que el comando está dirigido al UUID local del nodo.
2. Canonicaliza el payload JSON y calcula SHA-256; rechaza NaN/Infinity y payloads mayores de 1 MB.
3. Si `operation_id` ya existe con el mismo hash, devuelve el recibo previo como duplicado sin crear otra fila.
4. Si `operation_id` se reutiliza con otro payload, devuelve conflicto.
5. Rechaza comandos con lease vencida o sin fecha con zona horaria.
6. Rechaza epochs menores que el último guardado y que el mismo epoch cambie de propietario.
7. Persiste fence y recibo en una transacción `BEGIN IMMEDIATE`.

## 3. Resultados

`record_result` solo acepta un resultado cuando el propietario y epoch coinciden con el fence local actual. Un resultado atrasado se rechaza. Los resultados terminales `succeeded/failed` son inmutables: repetir el mismo resultado es idempotente; cambiarlo produce conflicto.

El journal no ejecuta el trabajo. El adaptador Android debe consultar/crear el recibo antes de cualquier efecto externo y reconciliar operaciones cuyo resultado sea incierto.

## 4. Comportamiento offline

El guardián funciona sin PostgreSQL ni conectividad una vez que el comando autenticado llega al nodo. Los recibos sobreviven al cierre/reapertura del proceso. La sincronización con la Master y el transporte de resultados pertenecen a módulos posteriores.

## 5. Límite crítico de seguridad

Un epoch local solo permite rechazar comandos viejos que llegan al mismo nodo. **No puede detener por sí solo una instancia antigua que continúa ejecutándose en otro nodo aislado de la red.** La Master no debe reasignar una instancia por la mera expiración del lease; necesita confirmar que el propietario anterior paró o aplicar un mecanismo externo de fencing probado.

Este módulo no aporta autenticación, firmas, TLS, permisos de sistema operativo, revocación ni quorum. Tampoco expone ADB/shell ni abre puertos. No desplegar en las PC físicas hasta validar todo el plano de control.


## 10. Entrega y confirmación de recibos al controlador

La versión 2 del journal añade `controller_ack_at` y una consulta acotada para reintentar recibos sin conexión.

- `list_pending_receipts(limit=100, statuses=None)` devuelve recibos sin ACK del controlador, filtrados al nodo local y ordenados por creación/ID. El límite permitido es 1-1000; el método no carga toda la base en memoria.
- `mark_receipt_delivered(operation_id, assignment_epoch)` marca un recibo como entregado solo después de recibir una respuesta HTTP 2xx autenticada del controlador. Rechaza epochs incorrectos.
- Cada nueva transición de estado vuelve a dejar el recibo pendiente; por ejemplo, si el estado `running` ya se envió y luego se obtiene `succeeded`, el resultado final debe volver a transmitirse.
- Si la red falla o el controlador devuelve un error, no marcar el recibo como entregado. Volverá a aparecer en el siguiente lote.
- Las operaciones terminales siguen siendo inmutables: el ACK de transporte no permite cambiar un resultado terminal.

Ejemplo de patrón de sincronización:

```python
for receipt in journal.list_pending_receipts(limit=50):
    response = transport.send_receipt(receipt)  # implementar con HTTPS autenticado
    if 200 <= response.status < 300:
        journal.mark_receipt_delivered(
            receipt.operation_id,
            receipt.assignment_epoch,
        )
```

El ejemplo ilustra el orden de persistencia/confirmación; `transport.send_receipt` debe implementarse con el transporte HTTPS autenticado y la clave idempotente correspondiente. Nunca marcar un recibo antes de que el controlador confirme la entrega.
