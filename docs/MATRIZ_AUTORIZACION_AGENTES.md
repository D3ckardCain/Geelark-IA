# Matriz de autorización por operación de agentes

**Estado:** política de dominio en revisión mediante PR; todavía no está conectada a una API ni a un listener.
**Relacionado:** ADR-005, issues #39, #43 y #46.
**Costo:** implementación local con Python; no requiere servicios ni APIs de pago.

## Principio

Autenticación y autorización son controles distintos. El transporte futuro debe validar la credencial individual, consultar los estados actuales de nodo y credencial y después invocar la política de autorización. Este módulo no autentica tokens ni consulta la base de datos.

## Matriz inicial

| Estado administrativo del nodo | Estado de credencial | Heartbeat | Publicar capacidades | Consultar estado propio | Aceptar tarea | Progreso/resultado | Reconciliar |
|---|---|---:|---:|---:|---:|---:|---:|
| pending | pending, no vencida | Sí | Sí | Sí | No | No | No |
| active | active, no vencida | Sí | Sí | Sí | Sí | Sí | Sí |
| Cualquier otro estado | cualquiera | No | No | No | No | No | No |
| cualquiera | revoked o expired | No | No | No | No | No | No |
| cualquiera | credencial vencida por timestamp | No | No | No | No | No | No |

Los estados desconocidos y las combinaciones inconsistentes fallan cerrados. La excepción de nodo pendiente se limita a telemetría y consulta de su propio estado; no autoriza asignaciones ni mutaciones operativas.

## Operaciones enumeradas

- heartbeat
- publish_capabilities
- read_own_status
- accept_task
- report_progress
- report_result
- reconcile

Cualquier operación no enumerada —incluyendo ejecución arbitraria de shell o ADB remoto— se rechaza.

## Pruebas requeridas para integrar el transporte

- Matriz positiva/negativa para cada estado y operación.
- Revocación y expiración verificadas en cada petición.
- No confiar en node_id enviado por el cliente; usar la identidad autenticada.
- Rechazar credenciales de un nodo para actuar como otro.
- Aplicar autorización después de autenticar y antes de leer/escribir el estado operativo.
- Mantener TLS con CA local obligatorio, sin fallback HTTP ni listener activo por defecto.

## Limitaciones actuales

El paquete de autenticación cuenta con pruebas de servicio de dominio en PR #44. Este nuevo módulo agrega una política pura y sus pruebas; no implementa FastAPI, TLS, nonces, rate limiting, listener, ni integración de rutas. El PR debe permanecer en borrador hasta que CI y la revisión de seguridad terminen.
