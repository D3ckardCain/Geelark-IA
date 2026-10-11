# API y panel local de administración PC-MASTER

## Estado

La PR implementa una API FastAPI, formulario de acceso en el panel del mismo origen, sesiones locales y una consulta de snapshots. El proceso de arranque exige TLS y configuración explícita. No se ha iniciado en el PC-MASTER del usuario ni se ha desplegado. El proyecto Supabase vinculado aparece actualmente como INACTIVE en el plan Free; no se restauró ni modificó para evitar cualquier riesgo de coste. Por ello no se pudieron verificar grants ni conectividad reales.

## Rutas

- `GET /`: sirve el panel local empaquetado.
- `GET /admin/v1/session`: consulta si la cookie actual tiene una sesión válida.
- `POST /admin/v1/login`: valida contraseña local y emite cookie opaca.
- `POST /admin/v1/logout`: revoca la sesión local.
- `GET /admin/v1/status/snapshots`: requiere sesión, ejecuta SELECT limitado a 500 filas y devuelve contrato v1.

No existen rutas administrativas de mutación.

## Seguridad implementada

- PBKDF2-HMAC-SHA256 con salt aleatorio y 600.000 iteraciones.
- Token aleatorio opaco; SQLite almacena únicamente SHA-256 del token. Expiración en 8 horas y revocación en logout.
- Cookie `__Host-geelark_master_session`: HttpOnly, Secure, SameSite=Strict, Path=/.
- HTTPS obligatorio en Uvicorn; sin confiar en cabeceras de proxy.
- POST exige Origin del mismo origen. El limitador admite cinco intentos fallidos por IP en 15 minutos; es en memoria y presupone un solo proceso.
- Respuestas sin caché, errores genéricos y sin OpenAPI expuesto.
- PostgreSQL exige el rol `geelark_master_reader`; transacciones read-only y límites de conexión, sentencia y bloqueo.
- PostgreSQL remoto exige `sslmode=verify-full` o `verify-ca`.
- La consulta usa `health_state AS reported_health_state`, que coincide con el esquema actual; módulos se leen de `module_reports`.
- La UI no almacena contraseña, token ni snapshots en localStorage/sessionStorage. El ejemplo ficticio es explícito y no concede sesión.
- El arranque por defecto escucha únicamente en `127.0.0.1:8765`. TLS y el hash de operador son obligatorios.

## Instalación local en PC-MASTER (no ejecutada por ChatGPT)

### 1. Preparar Python y los paquetes

Usa Python 3.11 o posterior. Desde la raíz de un checkout local:

```sh
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e packages/cluster-persistence -e packages/cluster-master-admin
```

Estos componentes son software libre/open source. No necesitan OAuth externo ni APIs de pago. Instalar paquetes requiere Internet una vez; operar la API después de instalarlos es local salvo que PostgreSQL esté alojado externamente.

### 2. Crear directorios privados

Linux:
```sh
install -d -m 700 "$HOME/.config/geelark/master-admin" "$HOME/.local/state/geelark/master-admin"
```

Windows PowerShell (elige rutas locales privadas y ejecuta como el usuario que operará PC-MASTER):
```powershell
$StateDir = "$env:LOCALAPPDATA\GeeLark-IA\master-admin"
New-Item -ItemType Directory -Force $StateDir | Out-Null
icacls $StateDir /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):(OI)(CI)F"
```

En Windows, las ACL NTFS deben limitar las rutas privadas al usuario del servicio; los bits POSIX no sirven para demostrarlo.

### 3. Crear contraseña de operador

Ejecuta una sola vez y usa una contraseña larga y única. El comando pide la contraseña dos veces y guarda solo el hash, nunca la contraseña:

```sh
python -m geelark_master_admin.bootstrap --output "$HOME/.config/geelark/master-admin/operator-auth.json"
```

En Windows sustituye la ruta por una dentro de tu directorio privado. Después restringe el archivo a permisos 0600 en Linux o a la ACL NTFS del usuario de PC-MASTER en Windows. El comando no sobrescribe el archivo existente.

### 4. Configurar TLS local

Necesitas OpenSSL instalado (herramienta gratuita) y certificado con SAN para `localhost` y `127.0.0.1`. Ejemplo para crear un certificado autofirmado local:

```sh
openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 365 \
  -keyout "$HOME/.config/geelark/master-admin/master-local.key" \
  -out "$HOME/.config/geelark/master-admin/master-local.crt" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 "$HOME/.config/geelark/master-admin/master-local.key"
```

En Windows PowerShell, usando el directorio `$StateDir` creado arriba:
```powershell
openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 365 -keyout "$StateDir\master-local.key" -out "$StateDir\master-local.crt" -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
icacls "$StateDir\master-local.key" /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):F"
```

Guarda ambos archivos fuera de Git y protege la clave privada. Para evitar avisos del navegador, instala el certificado local como certificado de confianza en el equipo operador. No desactives la validación TLS. No uses este certificado autofirmado para publicar el servicio en Internet ni en una LAN.

### 5. Crear y verificar el rol PostgreSQL

El script `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` crea/configura el rol dedicado y concede únicamente `USAGE` en el esquema y `SELECT` en `geelark_control.nodes`. Ejecútalo con una cuenta administradora, nunca con el usuario que usará el panel:

```sh
psql "$ADMIN_DSN" -v ON_ERROR_STOP=1 -f packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql
psql "$ADMIN_DSN"
```

En el prompt interactivo de psql ejecuta `\password geelark_master_reader` y establece una contraseña fuerte. No la pongas en el script SQL, GitHub, argumentos de comandos ni logs.

Después, conecta como `geelark_master_reader` y ejecuta `packages/cluster-master-admin/sql/verify_readonly_role.sql`. La prueba debe terminar sin excepción. Verifica además que el rol no pertenezca a otros roles ni tenga privilegios de escritura concedidos por otros mecanismos. No se han verificado grants reales: el proyecto Supabase vinculado aparece INACTIVE y no se restauró. Hasta que el usuario decida entre reactivarlo tras confirmar que seguirá en $0 o configurar PostgreSQL local, el control de permisos de base de datos sigue pendiente.

### 6. Configurar el entorno sin guardar secretos en Git

Variables obligatorias:
- `GEELARK_ADMIN_OPERATOR_AUTH_FILE`: ruta del JSON privado del hash.
- `GEELARK_ADMIN_STATE_DIR`: directorio privado para SQLite.
- `GEELARK_ADMIN_DATABASE_URL`: DSN PostgreSQL usando exactamente `geelark_master_reader`.
- `GEELARK_ADMIN_TLS_CERT` y `GEELARK_ADMIN_TLS_KEY`: certificado y clave TLS.
- Opcionales: `GEELARK_ADMIN_BIND_HOST` (por defecto `127.0.0.1`) y `GEELARK_ADMIN_PORT` (por defecto `8765`).

Ejemplo de configuración en Linux/macOS, después de crear el hash, el certificado y el archivo de contraseña PostgreSQL:
```sh
export GEELARK_ADMIN_OPERATOR_AUTH_FILE="$HOME/.config/geelark/master-admin/operator-auth.json"
export GEELARK_ADMIN_STATE_DIR="$HOME/.local/state/geelark/master-admin"
export GEELARK_ADMIN_DATABASE_URL="postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable"
export GEELARK_ADMIN_TLS_CERT="$HOME/.config/geelark/master-admin/master-local.crt"
export GEELARK_ADMIN_TLS_KEY="$HOME/.config/geelark/master-admin/master-local.key"
export PGPASSFILE="$HOME/.config/geelark/master-admin/pgpass"
chmod 600 "$PGPASSFILE"
python -m geelark_master_admin.runtime
```
El archivo `pgpass` contiene una línea con formato `host:port:database:username:password`, por ejemplo los cuatro primeros campos deben coincidir con el DSN. No pongas la contraseña en el DSN ni en el repositorio.

Equivalente en Windows PowerShell (usa un `PGPASSFILE` con ACL limitada al usuario actual):
```powershell
$StateDir = "$env:LOCALAPPDATA\GeeLark-IA\master-admin"
$env:GEELARK_ADMIN_OPERATOR_AUTH_FILE = Join-Path $StateDir "operator-auth.json"
$env:GEELARK_ADMIN_STATE_DIR = $StateDir
$env:GEELARK_ADMIN_DATABASE_URL = "postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable"
$env:GEELARK_ADMIN_TLS_CERT = Join-Path $StateDir "master-local.crt"
$env:GEELARK_ADMIN_TLS_KEY = Join-Path $StateDir "master-local.key"
$env:PGPASSFILE = Join-Path $StateDir "pgpass"
icacls $env:PGPASSFILE /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):F"
python -m geelark_master_admin.runtime
```

Para PostgreSQL local, usa `localhost` o socket local. Para una base remota, exige `sslmode=verify-full` y almacena la contraseña en un archivo `PGPASSFILE` privado o en el gestor de secretos del sistema. No pegues DSN con contraseña en GitHub ni en el chat. La base remota requiere conectividad y puede tener límites del proveedor; el coste $0 no está garantizado por proveedores externos. PostgreSQL local es la opción con menor dependencia externa.

### 7. Iniciar y comprobar

Solo después de configurar lo anterior, inicia manualmente desde el entorno virtual:

```sh
python -m geelark_master_admin.runtime
```

Abre `https://localhost:8765/`, acepta el certificado solo después de instalar/verificar su confianza y entra con la contraseña local. Confirma:
1. Sin iniciar sesión, `GET /admin/v1/status/snapshots` devuelve 401.
2. La contraseña incorrecta devuelve 401; después de cinco fallos devuelve 429.
3. El login correcto muestra la sesión y snapshots reales.
4. Logout revoca la cookie; el endpoint vuelve a devolver 401.
5. La consulta solo lee `geelark_control.nodes` y el rol no puede actualizar filas.
6. El panel muestra errores y no inventa datos reales cuando PostgreSQL está inaccesible.

No se recomienda exponerlo a la LAN. El arranque rechaza un bind no-loopback salvo que se configure explícitamente `GEELARK_ADMIN_ALLOW_REMOTE=1`; no configures esa variable para el uso local. Para acceso remoto se requiere certificado con SAN para el hostname/IP real, firewall restringido, revisión de CSRF/Origin y pruebas de seguridad.

## CI y coste

El workflow `.github/workflows/cluster-master-admin.yml` se ejecuta manualmente para evitar consumo automático de minutos en un repositorio privado. La última ejecución de este paquete validó 10 pruebas en el commit anterior a los cambios recientes; los nuevos tests aún requieren validación. Una ejecución del workflow general de esquema falló porque la prueba específica de grants se encontraba temporalmente en `db/tests` y se ejecutó como superusuario; se movió a `packages/cluster-master-admin/sql/verify_readonly_role.sql`, fuera del filtro de CI general. Ese fallo no verifica los grants reales y no debe interpretarse como prueba de producción. No ejecutar Actions sin comprobar la cuota disponible y confirmar que no se producirán cargos. Objetivo operativo obligatorio: $0 USD.

## Límites conocidos

- No es un servicio de alta disponibilidad; un proceso único.
- El rate limiter vive en memoria; reiniciar el proceso reinicia la ventana.
- SQLite guarda sesiones localmente; una pérdida del archivo cierra sesiones.
- No hay rutas para tareas, ADB, shell, reconciliación ni cambios de estado.
- Consulta real requiere PostgreSQL disponible; si es remoto, requiere Internet.
- No se ha instalado ni ejecutado en el PC-MASTER real, ni se ha validado el certificado/ACL de la máquina del usuario.
