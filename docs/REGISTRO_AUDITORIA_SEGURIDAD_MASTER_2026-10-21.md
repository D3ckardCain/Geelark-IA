# Registro de auditoría de seguridad — PC-MASTER y transporte Worker

**Fecha:** 2026-10-21  
**Repositorio:** `D3ckardCain/Geelark-IA`  
**Rama:** `feat/master-control-readonly-api-local-auth-v2`  
**Issue de seguimiento:** [#93 — auditoría del panel y evolución](https://github.com/D3ckardCain/Geelark-IA/issues/93)  
**PR principal:** [#84 — API local autenticada y panel GitHub Dark](https://github.com/D3ckardCain/Geelark-IA/pull/84)

## Alcance y límites

Esta iteración refuerza la validación del panel PC-MASTER, la conexión PostgreSQL de solo lectura, el almacenamiento de credenciales, el limitador de login y el transporte HTTPS de Workers. No se fusionó ninguna PR, no se desplegó la aplicación y no se conectó ningún Worker físico ni base de datos de producción. El lanzador Windows y el hardware permanecen sin cambios.

No se añadieron servicios de pago, APIs de pago ni dependencias de infraestructura obligatorias. El objetivo de coste operativo continúa siendo **$0 USD**.

## Correcciones implementadas

### Panel y contrato de snapshots
- Validación defensiva de estructura, campos exactos, UUID, fechas válidas de calendario, enumeraciones, capacidades, módulos, límites de tamaño y coherencia de salud/frescura.
- Pruebas que mantienen las enumeraciones del panel sincronizadas con `docs/contracts/master-worker-status-v1.schema.json`.
- El panel no cambia automáticamente a datos ficticios cuando falla la API; el ejemplo debe solicitarse explícitamente.
- Se mantienen ausentes los controles de shell, ADB, ejecución de tareas y reconciliación.

### Conexión PostgreSQL de PC-MASTER
- Correspondencia posicional y cardinalidad validada entre `host` y `hostaddr`; se rechazan IP inválidas y pares remotos/loopback ambiguos.
- Se exige destino y base de datos explícitos; se rechazan perfiles libpq externos y parámetros críticos heredados de variables de entorno.
- Para destinos remotos se exige `sslmode=verify-full` y una CA explícita. En POSIX se valida propietario y permisos de la CA y de su directorio; en Windows se comprueba propietario y ACL NTFS.
- Se fuerza `gssencmode=disable` para impedir que libpq prefiera GSSAPI en lugar de TLS verificado.
- Se rechazan contraseñas en el DSN, `PGPASSWORD` y el registro de claves TLS mediante `sslkeylogfile`; se bloquea también preventivamente la variable ambiental no documentada `PGSSLKEYLOGFILE`.
- `PGPASSFILE` debe pertenecer al usuario del proceso, ser legible solo por él (por ejemplo, modo `0600` o `0400`) y estar en un directorio protegido.
- Cada conexión fija `default_transaction_read_only=on`, `statement_timeout=1500ms`, `lock_timeout=500ms` e `idle_in_transaction_session_timeout=5000ms`.
- El verificador SQL comprueba los valores por defecto reales del rol antes de iniciar `BEGIN READ ONLY`. CI debilita cada ajuste individualmente y verifica que el script falle cerrado.

### Sesiones y autenticación local
- La carpeta SQLite de sesiones en POSIX debe pertenecer al usuario del proceso, tener modo privado `0700` y no depender de un directorio superior reemplazable; se admite un directorio raíz con sticky bit como `/tmp`.
- En Windows se restringen las ACL del archivo privado y se verifican las ACL/propietarios del directorio contenedor mediante PowerShell; el proceso falla cerrado si no puede comprobarlas.
- El limitador de login conserva la ventana de cinco fallos por 15 minutos, elimina ventanas expiradas y limita a 1024 las direcciones rastreadas. Si se llena con ventanas activas, las nuevas direcciones se rechazan temporalmente en vez de asignar memoria sin límite.

### Transporte HTTPS de Workers
- El cliente carga la ruta canónica de la CA y en POSIX valida propietario y permisos del archivo y su directorio.
- El listener valida en POSIX la propiedad y los permisos de la clave TLS, y usa rutas canónicas verificadas.
- El cuerpo JSON del cliente se limita a 16 KiB, alineado con el límite del servidor.
- Se rechazan redirects, URL absolutas, caracteres de control, backslashes y traversal, incluso cuando los controles están codificados en varias capas.
- Se mantienen validación de certificados/SAN, TLS moderno, timeout, límite de respuesta y ausencia de fallback HTTP.

## Validación CI registrada

La última validación completa del HEAD `88970dd03fb7850c44526f4773b37d6b3b06ab96` terminó correctamente:

- [Cluster persistence service #39604502755](https://github.com/D3ckardCain/Geelark-IA/actions/runs/39604502755): Master Admin **67 passed**; persistencia **33 passed**; guard **12 passed**; autorización **54 passed**; verificación PostgreSQL de solo lectura y `pip check` correctos.
- [Cluster agent HTTPS transport #39604503308](https://github.com/D3ckardCain/Geelark-IA/actions/runs/39604503308): **125 passed in 2.69 s**; `pip check` correcto.

Los workflows se ejecutaron con Python 3.11 y PostgreSQL desechable. No prueban la conectividad ni los permisos de una base real.

## Puerta pendiente antes de desplegar

La nueva lógica de ACL NTFS tiene pruebas unitarias que simulan PowerShell en CI Linux, pero **no se ha ejecutado todavía contra ACL reales en un host Windows**. La validación Windows anterior registrada en la issue #77 es anterior a estos cambios y no debe interpretarse como integración de esta nueva lógica. Se añadió un job de integración NTFS en `windows-latest`, opt-in mediante la etiqueta `enhancement` del PR para no consumir minutos Windows en cada push. El runner hospedado es Windows Server, no el escritorio Windows 11 de PC-MASTER; la prueba valida APIs NTFS/PowerShell compatibles, pero no sustituye toda la aceptación local.

Antes de habilitar esta ruta en producción, queda pendiente una prueba de aceptación Windows de la carpeta de sesiones, el archivo `PGPASSFILE`, el archivo de hash del operador y, si se usa PostgreSQL remoto, la CA TLS. Hasta entonces, PR #84 permanece en borrador y sin fusionar.

## Trazabilidad

Los commits, resultados CI, errores detectados durante las iteraciones y sus correcciones están registrados en el historial de esta rama y en los comentarios de la [issue #93](https://github.com/D3ckardCain/Geelark-IA/issues/93). Este documento consolida el estado de auditoría; no sustituye el historial de commits ni los logs de Actions.


## Incidencia detectada en la primera ejecución Windows real — 2026-10-21

La validación con `windows-latest` detectó que las variantes compactas de `icacls` no eran aceptadas por ese runner. La alternativa de modificar la DACL mediante `Set-Acl` se descartó después de que una prueba real excediera el timeout. El código vuelve a usar `icacls`, pasando el nivel de herencia como argumentos separados (`/inheritancelevel`, `r`), conserva la verificación de propietario/ACE mediante PowerShell y prepara explícitamente `PSModulePath`. También se corrigieron las rutas CA de pruebas para que sean portables en Windows. La aceptación final de NTFS queda pendiente de una nueva ejecución Windows sobre el HEAD sincronizado con la PR; no se declara aprobada hasta entonces.


## Corrección del ciclo CI Windows — 2026-10-21

- El job Windows estaba condicionado a un evento de etiquetado, por lo que quedaba omitido al actualizar la PR aunque la etiqueta estuviera presente. Se cambió a ejecutarse en cada evento `pull_request` de esta familia de cambios.
- Se corrigió la doble codificación de las rutas CA en DSN URI de prueba. En DSN keyword/value, las rutas se entrecomillan como valores, no se codifican como URL.
- La estrategia ACL elegida ejecuta por separado `icacls /reset`, `icacls /inheritance:r` y `icacls /grant:r`, falla ante cualquier código distinto de cero y comprueba después que solo queda la ACE de control total del usuario actual.
- No aceptar la corrección hasta que el job Windows de la PR #98 termine en verde y el resto de CI de ese HEAD finalice.
