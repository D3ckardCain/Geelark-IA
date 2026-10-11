# Transporte HTTPS privado de agentes

Paquete experimental independiente del dominio y sin listener automático.

## Política de acceso

- Un nodo `pending` con credencial `pending` solo puede enviar heartbeat, publicar capacidades y consultar su propio estado.
- Un nodo `active` con credencial `active` puede acceder a las rutas de agente configuradas.
- Combinaciones inconsistentes, estados revocados y credenciales vencidas fallan cerradas.
- La autorización se evalúa por operación; no se confía en cabeceras proxy ni en datos del cuerpo para decidir permisos.

## Controles

- La aplicación ASGI rechaza HTTP plano con 426. El listener TLS exige certificado y clave; no se inicia automáticamente.
- Listener y cliente solo aceptan RFC1918 IPv4, IPv6 ULA o loopback; rechazan DNS, IP pública, rangos de documentación, link-local y CGNAT.
- El agente envía `Authorization: Bearer`, `X-Agent-Nonce` (UUID), `X-Agent-Timestamp` (ISO-8601 con zona) y `X-Request-ID` (UUID).
- Nonces persistentes en PostgreSQL, ventana temporal de ±5 minutos y rechazo de replay.
- Las escrituras requieren `Idempotency-Key` de 16-200 caracteres. El runner PostgreSQL conserva el hash del payload y el snapshot de respuesta en la misma transacción que la operación de dominio; una clave con payload distinto devuelve conflicto.
- El handler de escritura recibe `conn` y debe usar esa misma conexión para que la mutación de dominio y la respuesta idempotente sean atómicas.
- Límite de cuerpo por defecto: 1 MiB.
- `InMemoryRateLimiter` limita a 60 solicitudes/minuto/nodo por proceso y solo es apropiado para pruebas o un único worker.
- `PostgresRateLimiter` usa un UPDATE atómico en la fila del nodo y aplica el límite global entre workers/procesos. Requiere la migración `db/migrations/0003_agent_rate_limit.sql`; el contador se satura para evitar desbordamiento.
- El cliente `AgentHTTPSClient` usa la CA explícita, verifica cadena y hostname/IP, exige TLS 1.2+, no sigue redirects, rechaza path traversal y limita timeout, cuerpos y respuestas.
- `AgentTransportRuntime` conecta el cliente con un journal compatible: persiste progreso/resultados antes de enviarlos y ofrece `sync_pending_receipts(limit=100)` para recorrer un lote acotado. El journal debe exponer `list_pending_receipts(limit=...)` y `mark_receipt_synced(operation_id)`; el ACK terminal solo se registra tras una respuesta HTTP 2xx. Los estados `accepted` no se envían como resultados. No ejecuta tareas ni inicia polling por sí solo.
- Las respuestas no incluyen tokens, SQL ni excepciones internas.
- Los handlers de dominio no configurados responden 503; el paquete no ejecuta shell/ADB ni comandos Android.

## Integración

Para el primer tramo de telemetría, usar:
- `authenticate=make_database_authenticator(connect)`
- `consume_nonce=make_database_nonce_consumer(connect)`
- `idempotency_runner=make_database_idempotency_runner(connect)`
- `rate_limiter=PostgresRateLimiter(connect)` para despliegues reales/multiworker.
- `handlers=make_postgres_agent_handlers(connect)`
- `AgentTransportRuntime(client=https_client, bearer_token=token, journal=agent_journal, local_node_id=node_id)` para integrar el cliente con el journal local del agente.

Los handlers incluidos vuelven a comprobar estado/credencial bajo bloqueo de fila antes de mutar; guardan heartbeat/capacidades y consultan únicamente el nodo autenticado. Los handlers de tareas/reconciliación siguen sin configurarse y devuelven 503; no deben conectarse a operaciones reales hasta integrar el servicio de dominio/outbox y revisarlo.

## Validación pendiente

- CI de transporte #38015892590 pasó con **31 pruebas**, `pip check` correcto y una prueba cruzada omitida explícitamente porque la rama base aún no incluye la API de recibos del PR #38.
- Los workflows de persistencia #38015892688 y esquema #38015892600 pasaron. La integración real SQLite→HTTPS se mantiene como dependencia pendiente; no se declara validada hasta apilar la API del journal.
- La suite prueba handshake TLS real con CA local y rechaza una CA desconocida. Sigue pendiente integrar el cliente HTTPS en el bucle principal del agente y completar la reconciliación.
- Definir timeouts/concurrencia del servidor y cuotas apropiadas para el tamaño real de la LAN. El limitador global PostgreSQL ya está implementado y probado.
- Completar manual de generación, rotación, respaldo y distribución de CA local.
- No conectar handlers de producción ni desplegar hasta cerrar los criterios anteriores.

Los tests de configuración TLS usan archivos ficticios para probar restricciones del listener, no para simular certificados válidos. El paquete no instala software en PCs físicas ni requiere APIs o servicios de pago.

## Pruebas locales

```sh
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```


## Inventario de módulos (v1, en revisión)

- `PUT /agent/v1/modules` acepta IDs de una lista cerrada: `agent-supervisor`, `agent-transport`, `agent-guard`, `task-journal` y `android-engine`.
- Solo un nodo `active` puede publicar estados de módulos. Un nodo `pending` recibe 403 y conserva exclusivamente heartbeat, capacidades y consulta de su propio estado.
- El Master fija `checked_at`; no confía en el reloj del Worker.
- Si el heartbeat supera 90 segundos o el reporte supera 5 minutos, el estado leído pasa a `unknown`, con origen `master-check` y código seguro (`NODE_STALE` o `REPORT_STALE`).
- Migración requerida: `db/migrations/0004_worker_module_inventory.sql`. No está desplegado ni conectado a PCs físicas.

- Esquema normativo del payload: [worker-module-inventory-v1.schema.json](../../docs/contracts/worker-module-inventory-v1.schema.json); [ejemplo](../../docs/contracts/examples/worker-module-inventory-v1.example.json).
