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
- Las respuestas no incluyen tokens, SQL ni excepciones internas.
- Los handlers de dominio no configurados responden 503; el paquete no ejecuta shell/ADB ni comandos Android.

## Integración

Para el primer tramo de telemetría, usar:
- `authenticate=make_database_authenticator(connect)`
- `consume_nonce=make_database_nonce_consumer(connect)`
- `idempotency_runner=make_database_idempotency_runner(connect)`
- `rate_limiter=PostgresRateLimiter(connect)` para despliegues reales/multiworker.
- `handlers=make_postgres_agent_handlers(connect)`

Los handlers incluidos vuelven a comprobar estado/credencial bajo bloqueo de fila antes de mutar; guardan heartbeat/capacidades y consultan únicamente el nodo autenticado. Los handlers de tareas/reconciliación siguen sin configurarse y devuelven 503; no deben conectarse a operaciones reales hasta integrar el servicio de dominio/outbox y revisarlo.

## Validación pendiente

- CI debe pasar en el commit más reciente.
- Añadir pruebas de handshake TLS con una CA local real y confirmar validación de CA desde el agente; los tests actuales comprueban rechazo HTTP y validación de configuración, no un handshake TLS real.
- Definir timeouts/concurrencia del servidor y cuotas apropiadas para el tamaño real de la LAN. El limitador global PostgreSQL ya está implementado y probado.
- Completar manual de generación, rotación, respaldo y distribución de CA local.
- No conectar handlers de producción ni desplegar hasta cerrar los criterios anteriores.

Los tests de configuración TLS usan archivos ficticios para probar restricciones del listener, no para simular certificados válidos. El paquete no instala software en PCs físicas ni requiere APIs o servicios de pago.

## Pruebas locales

```sh
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```
