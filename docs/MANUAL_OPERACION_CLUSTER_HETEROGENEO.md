# Manual de operación del clúster heterogéneo — borrador de ingeniería

**Versión del documento:** 0.1  
**Estado del módulo:** prototipo de persistencia; NO apto para producción ni para controlar PC físicas.  
**Alcance:** Master local, registro de nodos, reservas, asignaciones, resultados con epoch y primitivas SQL del outbox.  
**Referencia funcional del producto:** GeeLark sigue siendo la referencia para la experiencia de gestión de instancias Android. Este manual cubre únicamente el subsistema de coordinación distribuida; no afirma paridad funcional con GeeLark ni que el motor Android esté integrado.

## 1. Qué existe y qué no

### Validado en CI
- Esquema PostgreSQL 16 de prototipo.
- Asignación atómica de propietario, epoch, reserva, operación, auditoría, idempotencia y outbox.
- Repetición idempotente y conflicto por reutilizar la clave con otro hash.
- Rechazo de asignaciones que exceden la capacidad utilizable registrada.
- Rechazo de resultados con epoch antiguo o de un nodo no propietario.
- Primitivas SQL de claim, reintento y marca de entrega del outbox.
- Pruebas de concurrencia que verifican un solo ganador al asignar una misma instancia.

### Todavía no existe
- Servicio HTTP/FastAPI desplegable ni API de administración conectada a estas funciones.
- Autenticación real de los agentes, enrolamiento, certificados ni revocación de credenciales.
- Agente instalado en Windows/Linux o transporte real de órdenes a Workers.
- Compatibilidad verificada con motores Android, imágenes, ABI o perfiles de GeeLark.
- Dispatcher de larga duración que envíe eventos de outbox a los agentes.
- Reconciliación automática, backup/restauración ensayados ni failover de Master.
- Instalador, actualizador, interfaz de usuario o manual de usuario final del módulo.

**Regla de seguridad:** no conectar este prototipo a la base de producción ni a Supabase y no permitir que un nodo físico ejecute SQL directo.

## 2. Arquitectura de referencia

- **Master/controlador:** autoridad del MVP; mantiene estado durable y toma decisiones.
- **PostgreSQL local:** base autoritativa del plano de control.
- **Workers/agentes:** en el futuro, publicarán heartbeat/capacidad y ejecutarán solo órdenes autenticadas y vigentes.
- **Outbox:** persiste órdenes junto con la asignación para que una caída después del commit no pierda la intención.
- **Epoch:** contador monotónico de asignación; un resultado con epoch viejo no puede cambiar el estado actual.
- **Reconciliación:** cuando el resultado de una operación sea incierto, se conserva el propietario y se investiga antes de reasignar.

No se permite una segunda Master activa ni failover automático hasta diseñar y probar liderazgo y fencing.

## 3. Ejecutar la validación automatizada

La forma recomendada es revisar el workflow **Cluster persistence prototype** en GitHub Actions, que crea PostgreSQL 16 temporal, aplica el esquema y ejecuta las pruebas.

Para una ejecución local:
1. Crear una base PostgreSQL desechable y vacía.
2. Configurar las variables estándar de conexión de psql para esa base.
3. Ejecutar en este orden:
   - packages/cluster-persistence/prototype/001_schema.sql
   - packages/cluster-persistence/prototype/002_assign_instance.sql
   - packages/cluster-persistence/prototype/003_apply_agent_result.sql
   - packages/cluster-persistence/prototype/004_outbox_dispatch.sql
   - test_constraints.sql
   - test_assignment_function.sql
   - test_agent_result.sql
   - test_outbox_dispatch.sql
   - test_concurrency.sh
   - test_concurrent_assignments.sh
4. Confirmar que todos los comandos terminan con código 0 y las pruebas imprimen PASS.
5. Destruir la base desechable después de terminar.

Los scripts de concurrencia dejan datos de prueba confirmados; para repetir la suite completa hay que recrear la base. No usar credenciales reales ni incluirlas en logs.

## 4. Flujo de asignación (prototipo)

La función SQL cluster_control.assign_instance recibe IDs creados por la capa de aplicación, una clave de idempotencia, el SHA-256 del payload canónico y cantidades de RAM, disco y CPU.

1. Registra o encuentra la clave idempotente.
2. Si la clave existe con el mismo hash, devuelve la operación y epoch originales.
3. Si la clave existe con otro hash, rechaza la solicitud con IDEMPOTENCY_CONFLICT.
4. Bloquea la instancia, el nodo y la capacidad en un orden determinista.
5. Comprueba que la instancia no tenga propietario vigente, que el nodo esté activo/sano y que su telemetría/capacidad no esté vencida.
6. Comprueba la capacidad restante incluyendo reservas held y uncertain.
7. Incrementa el epoch, registra propietario, reserva, operación, auditoría y outbox en una transacción.
8. Devuelve el ID de operación, epoch y si fue un reintento.

El controlador real todavía debe autenticar al usuario, autorizar la operación, validar el motor Android y generar un hash canónico del payload.

## 5. Aplicar resultados de un agente (primitiva SQL)

cluster_control.apply_agent_result acepta un resultado solo si coinciden:
- nodo autenticado suministrado por una capa de servicio confiable;
- instancia y propietario actuales;
- epoch vigente;
- operación asociada a esa instancia, nodo y epoch;
- transición de estado permitida.

Los resultados con epoch antiguo o de otro nodo se rechazan. Repetir un resultado terminal idéntico no duplica el evento de auditoría.

La función SQL NO autentica al agente. No se debe aceptar p_authenticated_node_id desde el cuerpo de una petición sin verificar su identidad en el servicio.

## 6. Outbox: claim, reintento y entrega

Las funciones del prototipo son:
- claim_outbox: reclama un lote pendiente con FOR UPDATE SKIP LOCKED y un lease de claim.
- mark_outbox_delivered: marca un evento como entregado si el worker aún conserva el claim; repetir la marca después de entregar es idempotente.
- release_outbox_failure: registra un código de error y difiere el siguiente intento.

La entrega puede ser **al menos una vez**. Por ello, un futuro agente debe deduplicar por ID de operación/evento y comprobar el epoch antes de ejecutar. Un worker que pierde su claim no puede marcar la entrega ni liberar el claim de otro worker.

Estas funciones no envían tráfico de red por sí solas; el proceso dispatcher y el transporte autenticado siguen pendientes.

## 7. Estados y respuesta ante fallos

| Situación | Respuesta segura | No hacer |
|---|---|---|
| Heartbeat vencido | Marcar salud como incierta y reconciliar | Asumir que el proceso Android se detuvo |
| Lease de instancia vencido | Conservar propietario hasta tener evidencia | Liberar automáticamente y asignar a otro nodo |
| Resultado con epoch antiguo | Rechazar y registrar el motivo | Aplicar el estado recibido |
| Nodo no propietario envía resultado | Rechazar | Permitirle liberar reservas |
| Capacidad insuficiente | Rechazar o buscar otro candidato | Sobreasignar RAM/disco por una lectura vieja |
| Outbox sin claim vigente | Permitir reclamación por otro worker | Confiar en un worker que perdió el claim |
| Error de transporte tras commit | Reintentar de forma idempotente | Crear una segunda operación nueva |
| Estado remoto desconocido | Mantener unknown/reconciliación | Lanzar la misma instancia en otro nodo |

## 8. Códigos de error iniciales del prototipo

- INSTANCE_NOT_FOUND, NODE_NOT_FOUND
- INSTANCE_ALREADY_ASSIGNED_OR_UNCERTAIN
- NODE_NOT_ELIGIBLE_OR_TELEMETRY_STALE
- NODE_CAPACITY_MISSING_OR_STALE, NODE_CAPACITY_EXCEEDED
- IDEMPOTENCY_CONFLICT, IDEMPOTENCY_RECORD_INCOMPLETE
- STALE_ASSIGNMENT_EPOCH, RESULT_FROM_NON_OWNER
- OPERATION_OWNERSHIP_MISMATCH, INVALID_STATE_TRANSITION
- OUTBOX_CLAIM_LOST, OUTBOX_EVENT_NOT_FOUND

Son códigos internos de la función SQL experimental. El servicio API deberá mapearlos a errores tipados y redactados.

## 9. Seguridad y coste

- PostgreSQL puede ejecutarse localmente sin tarifa de licencia ni suscripción.
- La prueba de CI usa una base efímera y credenciales de prueba, no la base del usuario.
- Las funciones revocan EXECUTE a PUBLIC; todavía hay que crear roles dedicados y conceder permisos mínimos al servicio.
- No exponer PostgreSQL, API de control ni agente directamente a Internet.
- No registrar tokens, claves privadas, payloads de perfiles ni datos privados.
- El coste operativo objetivo del software es 0 USD, pero el hardware, la electricidad, el almacenamiento y la red tienen costes indirectos.

## 10. Criterios para pasar de prototipo a MVP operativo

1. Revisar SQL y privilegios mínimos.
2. Implementar un servicio de dominio con autenticación y autorización.
3. Implementar el dispatcher y transporte con TLS, credenciales individuales y revocación.
4. Implementar agente de nodo con deduplicación y fencing.
5. Probar caídas antes/después del envío, reintentos y reconexión.
6. Probar reconciliación y restauración desde backup.
7. Inventariar las PC reales y verificar motor/virtualización Android.
8. Comparar cada flujo de gestión de instancias con la referencia GeeLark y documentar diferencias.
9. Publicar manual de usuario final cuando la interfaz y los flujos estén implementados.

**No marcar el módulo como terminado hasta que estos criterios tengan evidencia reproducible.**
