# Contrato de autenticación local y API Master Admin v1

**Estado:** implementación inicial de la fábrica ASGI; integración y despliegue siguen pendientes.

## Decisión confirmada

La autenticación del panel es local y gestionada por PC-MASTER. No depende de Supabase Auth, Cloudflare Access, OAuth externo ni APIs de pago.

## API

- `GET /admin/v1/session`: 200 con `{"authenticated": true|false}`.
- `POST /admin/v1/login`: acepta únicamente `{"password": "..."}`; exige HTTPS y `Origin` del mismo origen. Responde 200 y emite cookie o 401/403/429.
- `POST /admin/v1/logout`: revoca sesión local y borra cookie; exige HTTPS y mismo origen.
- `GET /admin/v1/status/snapshots`: requiere sesión vigente y devuelve `schema_version`, `generated_at` y máximo 500 snapshots. Respuestas de error no se reemplazan por datos ficticios.

## Controles

- Hash PBKDF2-HMAC-SHA256 con salt aleatorio, mínimo 600.000 iteraciones.
- Token de sesión aleatorio opaco; SQLite guarda solo su SHA-256. Expira en 8 horas y logout revoca la sesión.
- Cookie HttpOnly, Secure por defecto, SameSite=Strict y prefijo `__Host-`.
- HTTPS obligatorio, Origin estricto para operaciones POST, limitador de intentos fallidos, headers anti-cache y errores genéricos.
- SQL de snapshots: una consulta SELECT, ORDER BY estable, LIMIT 500. La conexión debe usar timeouts y un rol de PostgreSQL solo lectura.
- Tamaño máximo de respuesta 1 MiB. Se omiten tareas, secretos, payloads y logs libres.

## Límites y pendientes

- El limitador actual está en memoria y presupone un único proceso; debe sustituirse o hacerse compartido antes de ejecutar múltiples workers.
- La API todavía no está montada en el servicio anfitrión de PC-MASTER; no se ha abierto ningún puerto ni desplegado nada.
- Pendiente verificar grants reales PostgreSQL, configurar timeouts de conexión, integrar el formulario de login en el panel y probar con PostgreSQL desechable bajo CI.
- No usar en producción hasta completar esas puertas. No fusionar automáticamente.
