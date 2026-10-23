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

- PBKDF2-HMAC-SHA256 con salt aleatorio y 600.000 iteraciones. Se rechazan hashes con coste superior a 2.000.000 iteraciones para evitar bloqueos por configuración manipulada.
- Token aleatorio opaco; SQLite almacena únicamente SHA-256 del token. Expiración en 8 horas y revocación en logout.
- Cookie `__Host-geelark_master_session`: HttpOnly, Secure, SameSite=Strict, Path=/.
- HTTPS obligatorio en Uvicorn; sin confiar en cabeceras de proxy.
- POST exige Origin del mismo origen. El limitador admite cinco intentos fallidos por IP en 15 minutos; es en memoria y presupone un solo proceso.
- Respuestas sin caché, errores genéricos y sin OpenAPI expuesto.
- PostgreSQL exige el rol `geelark_master_reader`; transacciones read-only y límites de conexión, sentencia y bloqueo.
- El verificador SQL también rechaza privilegios efectivos sobre otras tablas/secuencias, grants a nivel de columna, `CREATE` fuera del alcance permitido y propiedad de objetos/esquemas. La CI incluye pruebas negativas para SELECT por columna en una tabla ajena y UPDATE por columna en `geelark_control.nodes`.
- El verificador también rechaza `EXECUTE` efectivo sobre rutinas de esquemas de aplicación (incluidas funciones expuestas por `PUBLIC`); la allowlist de rutinas está vacía hasta revisión explícita. La prueba negativa crea una función `SECURITY DEFINER` ficticia y exige su rechazo. Estas ampliaciones están validadas en la CI de la PR #84: [ejecución #38272945485](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38272945485), con 30 pruebas Master Admin, 33 de persistencia/snapshot, 12 de guardia, 54 de autorización, probes negativos del rol lector y `pip check` correcto. La CI usa PostgreSQL desechable; no sustituye la validación física de Windows.
- PostgreSQL remoto exige `host=` explícito y `sslmode=verify-full`, verifica la cadena de confianza y el nombre del servidor, y detecta destinos remotos indicados mediante `hostaddr`; no se aceptan perfiles `service=` porque pueden ocultar la configuración efectiva.
- La migración existente `0003_agent_rate_limit.sql` añade `reported_health_state` y separa la declaración del Worker de `health_state`, que deriva el controlador. La API lee ambos conceptos por separado; los módulos se leen de `module_reports`.
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

### 5. Preparar el esquema PostgreSQL local

Si usas una base PostgreSQL local nueva, primero aplica las migraciones en orden, una sola vez y con una cuenta administradora. Hazlo únicamente sobre la base destinada a GeeLark-IA; no apuntes a una base con datos importantes sin revisar antes cada migración.

Linux/macOS, desde la raíz del repositorio:
```sh
for migration in db/migrations/0001_cluster_control.sql db/migrations/0002_agent_auth.sql db/migrations/0003_agent_rate_limit.sql db/migrations/0004_worker_module_inventory.sql; do
  psql "$ADMIN_DSN" -v ON_ERROR_STOP=1 -f "$migration" || exit 1
done
```

Windows PowerShell:
```powershell
$Migrations = @(
  "db/migrations/0001_cluster_control.sql",
  "db/migrations/0002_agent_auth.sql",
  "db/migrations/0003_agent_rate_limit.sql",
  "db/migrations/0004_worker_module_inventory.sql"
)
foreach ($Migration in $Migrations) {
  psql $env:ADMIN_DSN -v ON_ERROR_STOP=1 -f $Migration
  if ($LASTEXITCODE -ne 0) { throw "Falló la migración $Migration; detén la instalación y revisa el error." }
}
```

No repitas estas migraciones sobre una base ya inicializada sin consultar el historial y las instrucciones de migración.

### 6. Crear y verificar el rol PostgreSQL

El script `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` crea/configura el rol dedicado y concede únicamente `USAGE` en el esquema y `SELECT` en `geelark_control.nodes`. Ejecútalo con una cuenta administradora, nunca con el usuario que usará el panel:

```sh
psql "$ADMIN_DSN" -v ON_ERROR_STOP=1 -f packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql
psql "$ADMIN_DSN"
```

En el prompt interactivo de psql ejecuta `\password geelark_master_reader` y establece una contraseña fuerte. No la pongas en el script SQL, GitHub, argumentos de comandos ni logs.

Después, conecta como `geelark_master_reader` y ejecuta `packages/cluster-master-admin/sql/verify_readonly_role.sql`. La prueba debe terminar sin excepción. Verifica además que el rol no pertenezca a otros roles ni tenga privilegios de escritura concedidos por otros mecanismos. No se han verificado grants reales: el proyecto Supabase vinculado aparece INACTIVE y no se restauró. Hasta que el usuario decida entre reactivarlo tras confirmar que seguirá en $0 o configurar PostgreSQL local, el control de permisos de base de datos sigue pendiente.

### 7. Configurar el entorno sin guardar secretos en Git

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

Equivalente en Windows PowerShell. El directorio `$StateDir` debe haberse creado y protegido en el paso 2. Este bloque crea `pgpass` sin sobrescribir uno existente, pide la contraseña sin mostrarla, no la incluye en argumentos ni logs y restringe la ACL antes de iniciar el servicio:

```powershell
$StateDir = "$env:LOCALAPPDATA\GeeLark-IA\master-admin"
$env:GEELARK_ADMIN_OPERATOR_AUTH_FILE = Join-Path $StateDir "operator-auth.json"
$env:GEELARK_ADMIN_STATE_DIR = $StateDir
$env:GEELARK_ADMIN_DATABASE_URL = "postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable"
$env:GEELARK_ADMIN_TLS_CERT = Join-Path $StateDir "master-local.crt"
$env:GEELARK_ADMIN_TLS_KEY = Join-Path $StateDir "master-local.key"
$env:PGPASSFILE = Join-Path $StateDir "pgpass"

if (Test-Path -LiteralPath $env:PGPASSFILE) {
  throw "PGPASSFILE ya existe; no se sobrescribirá. Revisa la configuración manualmente."
}
$credential = Get-Credential -UserName "geelark_master_reader" -Message "Introduce la contraseña del rol PostgreSQL; no se mostrará en pantalla."
$bstr = [IntPtr]::Zero
$file = $null
try {
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($credential.Password)
  $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  if ($plain.Contains("`r") -or $plain.Contains("`n")) {
    throw "La contraseña no puede contener saltos de línea para el formato pgpass."
  }
  $escaped = $plain.Replace('\', '\\').Replace(':', '\:')
  $line = "localhost:5432:geelark:geelark_master_reader:$escaped"
  $bytes = [Text.UTF8Encoding]::new($false).GetBytes($line + "`n")
  $file = [IO.File]::Open($env:PGPASSFILE, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
  $file.Write($bytes, 0, $bytes.Length)
} finally {
  if ($null -ne $file) { $file.Dispose() }
  if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
  $plain = $null; $escaped = $null; $line = $null; $bytes = $null; $credential = $null
}

icacls $env:PGPASSFILE /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):F"
if ($LASTEXITCODE -ne 0) {
  Remove-Item -LiteralPath $env:PGPASSFILE -Force -ErrorAction SilentlyContinue
  throw "No se pudo restringir la ACL de PGPASSFILE; no inicies el servicio."
}
$acl = icacls $env:PGPASSFILE
if ($LASTEXITCODE -ne 0 -or ($acl -join "`n") -notmatch [regex]::Escape("$($env:USERDOMAIN)\$($env:USERNAME)")) {
  throw "No se pudo verificar la ACL de PGPASSFILE; no inicies el servicio."
}
python -m geelark_master_admin.runtime
```

Para PostgreSQL local, usa `localhost` o socket local. Para una base remota, exige `sslmode=verify-full` y almacena la contraseña en un archivo `PGPASSFILE` privado o en el gestor de secretos del sistema. No pegues DSN con contraseña en GitHub ni en el chat. La base remota requiere conectividad y puede tener límites del proveedor; el coste $0 no está garantizado por proveedores externos. PostgreSQL local es la opción con menor dependencia externa.

### 8. Iniciar y comprobar

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

- Histórico: la primera versión del código pasó [CI #38190869235](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38190869235). La rama limpia actual PR #84 tiene evidencia más reciente en [CI #38272945485](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38272945485).
- Pasaron 33 pruebas de persistencia, 12 de guardia, 54 de autenticación de agentes y 26 pruebas administrativas; la verificación del rol lector en PostgreSQL desechable, las pruebas negativas de privilegios y `pip check` también pasaron.
- Las pruebas usan `httpx2` para el cliente Starlette; la advertencia deprecatoria anterior desapareció.
- El repositorio es público y se usa el workflow de integración existente, sin crear un workflow paralelo. No se añadieron APIs de pago, SaaS ni runners especiales.
- Los commits posteriores al HEAD validado actualizan únicamente documentación; no modifican el código cubierto por la ejecución indicada.
- La CI desechable no valida las ACL NTFS/TLS del Windows real ni los grants de la base de datos objetivo. No se ha instalado ni ejecutado en PC-MASTER. La aceptación física está registrada en [issue #77](https://github.com/D3ckardCain/Geelark-IA/issues/77). La PR #84 continúa en borrador y no debe fusionarse ni desplegarse hasta completar esa puerta de validación.
- El objetivo operativo sigue siendo $0 USD; una base remota puede introducir límites o costes, por lo que se prefiere PostgreSQL local.

## Límites conocidos

- No es un servicio de alta disponibilidad; un proceso único.
- El rate limiter vive en memoria; reiniciar el proceso reinicia la ventana.
- SQLite guarda sesiones localmente; una pérdida del archivo cierra sesiones.
- No hay rutas para tareas, ADB, shell, reconciliación ni cambios de estado.
- Consulta real requiere PostgreSQL disponible; si es remoto, requiere Internet.
- No se ha instalado ni ejecutado en el PC-MASTER real, ni se ha validado el certificado/ACL de la máquina del usuario.


## Revalidación de privilegios y CI — 2026-10-12

La verificación SQL del rol lector se ejecutó en PostgreSQL 16 desechable en [run #38193499261](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38193499261): success para las pruebas negativas de `EXECUTE` de rutinas, grants de columna, tablas ajenas y esquema. La suite completa de esta rama limpia terminó success en [run #38194249930](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38194249930): 33 pruebas de persistencia, 12 de guard, 54 de autorización y 28 del paquete Master Admin; el verificador SQL y `pip check` también pasaron. La comprobación simulada de ACL NTFS pasó; la ACL efectiva, certificado y bind loopback aún requieren validación física en Windows conforme a issue #77.
