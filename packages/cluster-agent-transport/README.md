# Transporte HTTPS privado de agentes

Paquete experimental independiente del dominio y sin listener automático.

## Política de acceso

- Un nodo `pending` con credencial `pending` solo puede enviar heartbeat, publicar capacidades y consultar su propio estado.
- Un nodo `active` con credencial `active` puede acceder a las rutas de agente configuradas.
- Combinaciones inconsistentes, estados revocados y credenciales vencidas fallan cerradas.
- La autorización se evalúa por operación; no se confía en cabeceras proxy ni en datos del cuerpo para decidir permisos.

## Controles

- La aplicación ASGI rechaza HTTP plano con 426. El listener TLS exige certificado y clave; no se inicia automáticamente.
- El listener exige IP literal privada/loopback; rechaza DNS, IP pública y `0.0.0.0`.
- El agente envía `Authorization: Bearer`, `X-Agent-Nonce` (UUID), `X-Agent-Timestamp` (ISO-8601 con zona) y `X-Request-ID` (UUID).
- Nonces persistentes en PostgreSQL, ventana temporal de ±5 minutos y rechazo de replay.
- Las escrituras requieren `Idempotency-Key` de 16-200 caracteres. El runner PostgreSQL conserva el hash del payload y el snapshot de respuesta en la misma transacción que la operación de dominio; una clave con payload distinto devuelve conflicto.
- El handler de escritura recibe `conn` y debe usar esa misma conexión para que la mutación de dominio y la respuesta idempotente sean atómicas.
- Límite de cuerpo por defecto: 1 MiB.
- Rate limit por proceso: 60 solicitudes/minuto/nodo. En despliegues multiworker no es un límite global.
- Las respuestas no incluyen tokens, SQL ni excepciones internas.
- Los handlers de dominio no configurados responden 503; el paquete no ejecuta shell/ADB ni comandos Android.

## Integración

Crear el adaptador de dominio PostgreSQL y pasar:
- `authenticate=make_database_authenticator(connect)`
- `consume_nonce` que llame a `consume_request_nonce` con una conexión gestionada.
- `idempotency_runner=make_database_idempotency_runner(connect)`
- `handlers` que usen la conexión `conn` entregada en cada escritura.

El callback de consulta de estado debe devolver solo el estado del nodo autenticado. Los callbacks de heartbeat/capacidades deben validar y persistir los datos con el mínimo privilegio.

## Validación pendiente

- CI debe pasar en el commit más reciente.
- Añadir pruebas de handshake TLS con una CA local real y confirmar validación de CA desde el agente; los tests actuales comprueban rechazo HTTP y validación de configuración, no un handshake TLS real.
- Revisar timeouts/concurrencia del servidor y decidir despliegue single-worker o limitador global.
- Completar manual de generación, rotación, respaldo y distribución de CA local.
- No conectar handlers de producción ni desplegar hasta cerrar los criterios anteriores.

Los tests de configuración TLS usan archivos ficticios para probar restricciones del listener, no para simular certificados válidos. El paquete no instala software en PCs físicas ni requiere APIs o servicios de pago.

## Pruebas locales

```sh
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```
