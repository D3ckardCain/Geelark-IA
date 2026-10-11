# API local de administración PC-MASTER

## Estado

Implementación inicial de la API de snapshots autenticada. La fábrica ASGI no abre un listener ni despliega servicios. Aún falta montarla en el proceso anfitrión real de PC-MASTER, cargar configuración desde rutas privadas, crear el rol PostgreSQL de solo lectura y conectar el formulario de acceso de la interfaz.

## Rutas

- `GET /admin/v1/session`: consulta si la cookie actual tiene una sesión válida.
- `POST /admin/v1/login`: valida contraseña local y emite una cookie opaca.
- `POST /admin/v1/logout`: revoca la sesión en SQLite y elimina la cookie.
- `GET /admin/v1/status/snapshots`: requiere sesión y devuelve hasta 500 snapshots v1.

Solo la ruta de snapshots lee el estado del clúster. No existen rutas administrativas de mutación.

## Seguridad

- Contraseña derivada con PBKDF2-HMAC-SHA256, 600.000 iteraciones y salt aleatorio de 16 bytes.
- Las sesiones usan tokens aleatorios; SQLite almacena únicamente SHA-256 del token, con expiración a 8 horas y revocación explícita.
- Cookie `__Host-geelark_master_session`, HttpOnly, Secure (predeterminado), SameSite=Strict, Path=/.
- HTTPS obligatorio en middleware; rutas de login/logout rechazan solicitudes sin Origin del mismo origen.
- Límite de cinco intentos fallidos por dirección en 15 minutos (en memoria, para un solo proceso).
- Respuestas sin caché; errores genéricos; sin docs/OpenAPI en ejecución.
- Consulta PostgreSQL limitada por `LIMIT 500`, solo columnas de estado conocidas. No consulta tareas, payloads, logs libres ni secretos.
- Tamaño máximo de respuesta: 1 MiB.
- No se confía en la UI para autorizar acceso.

## Inicializar contraseña local

Instala el paquete en el entorno privado de PC-MASTER y ejecuta:

```sh
python -m geelark_master_admin.bootstrap --output /etc/geelark/master-admin/operator-auth.json
```

El comando solicita la contraseña dos veces y escribe solo el hash en un archivo nuevo con permisos restrictivos. No sobrescribe un archivo existente. La contraseña y el hash no deben almacenarse en GitHub.

## Conexión PostgreSQL

El callback `connect` debe crear conexiones con timeout y `statement_timeout` configurados en el DSN/opciones de PostgreSQL y utilizar un rol dedicado con permisos SELECT estrictos sobre las columnas necesarias. No se debe usar el usuario propietario ni una credencial de escritura. La comprobación de grants reales queda pendiente.

## Offline y coste

Autenticación y sesión funcionan localmente sin APIs ni SaaS. Consultar snapshots reales requiere que el proceso y PostgreSQL local estén disponibles. No hay coste obligatorio de servicio externo; cualquier despliegue en infraestructura externa queda fuera del alcance y no se recomienda para esta fase.
