# Transporte HTTPS privado de agentes

Paquete experimental independiente del dominio y sin listener automático.

## Política de acceso

- Un nodo `pending` con credencial `pending` solo puede enviar heartbeat, publicar capacidades y consultar su propio estado.
- Un nodo `active` con credencial `active` puede acceder a las rutas de agente configuradas.
- Estados revocados, inconsistentes, credenciales vencidas o combinaciones no reconocidas fallan cerradas.
- La autorización se evalúa por operación; no se confía en cabeceras proxy ni en datos del cuerpo para decidir permisos.

## Controles

- HTTPS requiere certificado y clave TLS; el helper no arranca Uvicorn ni abre puertos.
- El listener exige IP literal privada/loopback; rechaza DNS, IP pública y `0.0.0.0`.
- El agente envía `Authorization: Bearer`, `X-Agent-Nonce` (UUID), `X-Agent-Timestamp` (ISO-8601 con zona) y `X-Request-ID` (UUID).
- Los nonces se consumen en PostgreSQL y su clave única impide repetición concurrente entre procesos.
- Ventana de timestamp por defecto: ±5 minutos.
- Límite de cuerpo por defecto: 1 MiB.
- Rate limit por proceso: 60 solicitudes/minuto/nodo. En despliegues multiworker no es un límite global.
- Las respuestas no incluyen tokens, SQL ni excepciones internas.
- Las rutas de tareas llaman callbacks explícitos; sin callback responden 503 y no ejecutan acciones.

## Integración pendiente

Crear el adaptador de dominio PostgreSQL y pasar `authenticate=make_database_authenticator(connect)`; el callback `consume_nonce` debe invocar `consume_request_nonce` con una conexión cerrada correctamente. Los handlers deben conectarse a servicios de dominio/outbox revisados. No arrancar el listener hasta revisar la CA local, idempotencia, autorización y pruebas de integración.

Los tests de configuración TLS usan archivos ficticios para probar la restricción de host, no para simular un certificado válido. El paquete no instala software en PC físicas ni requiere APIs o servicios de pago.

## Pruebas locales

```sh
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```
