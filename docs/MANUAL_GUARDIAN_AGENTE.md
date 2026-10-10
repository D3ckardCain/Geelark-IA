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

`record_result` solo acepta un resultado cuando el propietario y epoch coinciden con el fence local actual. Un resultado atrasado se rechaza. Los resultados terminales `succeeded/rejected/failed` son inmutables: repetir el mismo resultado es idempotente; cambiarlo produce conflicto. La versión 2 del journal migra el CHECK de SQLite y conserva los recibos y ACK de la versión 1.

El journal no ejecuta el trabajo. El adaptador Android debe consultar/crear el recibo antes de cualquier efecto externo y reconciliar operaciones cuyo resultado sea incierto.

## 4. Comportamiento offline

El guardián funciona sin PostgreSQL ni conectividad una vez que el comando autenticado llega al nodo. Los recibos sobreviven al cierre/reapertura del proceso. La sincronización con la Master se realiza a través del adaptador de transporte: `list_pending_receipts(limit=...)` enumera un lote ordenado y acotado, y `mark_receipt_synced()` guarda el ACK terminal después de una respuesta 2xx. Los recibos `rejected` también se conservan hasta el ACK. El bucle principal del agente aún debe invocar el sincronizador al iniciar y recuperar conexión.

## 5. Límite crítico de seguridad

Un epoch local solo permite rechazar comandos viejos que llegan al mismo nodo. **No puede detener por sí solo una instancia antigua que continúa ejecutándose en otro nodo aislado de la red.** La Master no debe reasignar una instancia por la mera expiración del lease; necesita confirmar que el propietario anterior paró o aplicar un mecanismo externo de fencing probado.

Este módulo no aporta autenticación, firmas, TLS, permisos de sistema operativo, revocación ni quorum. Tampoco expone ADB/shell ni abre puertos. No desplegar en las PC físicas hasta validar todo el plano de control.
