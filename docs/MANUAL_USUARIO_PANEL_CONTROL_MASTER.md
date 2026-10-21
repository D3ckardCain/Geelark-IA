# Manual de usuario — Panel de control PC-MASTER

**Estado:** panel y autenticación implementados en la PR borrador #84. La CI de la rama pasó en la ejecución [#38272945485](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38272945485), incluidas las pruebas del paquete Master Admin y los probes negativos del rol PostgreSQL. La validación de Windows de la issue #77 ya se realizó y superó en la sesión de trabajo del proyecto; no se debe repetir como tarea pendiente sin una regresión o un cambio técnico que la justifique. La PR continúa en draft y no está fusionada.

## 1. Acceso inicial

1. Instala el paquete local y configura TLS, hash de operador, directorio privado y DSN PostgreSQL siguiendo [la guía de instalación](../packages/cluster-master-admin/README.md).
2. Inicia manualmente `python -m geelark_master_admin.runtime`.
3. Abre `https://localhost:8765/` en el mismo PC-MASTER. No abras el HTML como archivo local para acceder a datos reales.
4. Verifica que el certificado corresponda a `localhost` y esté confiado por el sistema. No ignores advertencias TLS sin verificar la huella y procedencia del certificado.
5. Escribe la contraseña local del operador. No hay cuenta externa ni recuperación remota; conserva la contraseña de forma segura.
6. Al entrar, el panel consulta snapshots por GET y solo muestra datos que devuelve el servicio.

## 2. Cerrar sesión

Pulsa **Cerrar sesión** en la cabecera. El servidor revoca la sesión en SQLite y elimina la cookie. Si no se recibe confirmación, el panel no afirma que la sesión se haya cerrado; comprueba la conexión e inténtalo de nuevo. La sesión también caduca tras ocho horas.

## 3. Navegación

La interfaz usa un tema oscuro inspirado en GitHub Dark: fondo carbón, paneles discretos, bordes grises, texto claro y acento azul. La barra lateral agrupa las áreas del producto para que la navegación pueda ampliarse sin rehacer el panel.

Secciones disponibles en esta versión:
- **Resumen:** contadores y últimos snapshots.
- **PC Workers:** búsqueda por nombre o identificador, estado de autorización, salud derivada, heartbeat, versión y capacidades.
- **Aplicaciones y módulos:** estado de módulos reportados y frescura del reporte.
- **Auditoría y CI:** estado de integración y enlaces a las ejecuciones de GitHub. Consultar GitHub requiere Internet.

Secciones visibles pero todavía deshabilitadas:
- **Instancias Android**
- **Automatizaciones**
- **Tareas y colas**
- **Red y conectividad**
- **Almacenamiento**
- **Usuarios y permisos**
- **Configuración**

Los accesos deshabilitados son marcadores de navegación futura, no funciones implementadas. No permiten operaciones y no deben interpretarse como evidencia de que esas capacidades ya estén disponibles.

## 4. Estados

- **Saludable:** estado derivado por el Master con evidencia fresca.
- **Degradado:** el reporte de salud indica degradación o problema.
- **Desconectado:** el heartbeat está obsoleto.
- **Pendiente:** el nodo no está autorizado para aceptar tareas.
- **Revocado:** autorización revocada.
- **Desconocido:** evidencia ausente, obsoleta o inconsistente.
- **Fresco / obsoleto / ausente:** frescura del heartbeat, no salud por sí sola.

Autorización y salud son señales distintas. La API no ejecuta tareas ni modifica nodos.

## 5. Ejemplo ficticio

El botón **Ver ejemplo ficticio** permite probar navegación sin iniciar sesión. Los datos son generados localmente y no representan equipos reales. El ejemplo no crea una sesión ni concede acceso al backend. Para volver a datos reales, el panel exige comprobar la sesión local.

## 6. Errores y solución

- **No se puede iniciar sesión:** revisa la contraseña local; tras cinco intentos fallidos en 15 minutos se limita el acceso.
- **401:** inicia sesión; la sesión no existe, expiró o fue revocada.
- **403:** el origen de la solicitud no coincide con el origen del panel.
- **429:** espera a que pase la ventana del limitador.
- **503:** servicio o base de datos no disponible, o respuesta demasiado grande. Revisa logs locales sin registrar contraseñas, cookies, DSN ni tokens.
- **No hay nodos:** puede ser una tabla vacía o ausencia de snapshots; no se interpreta como clúster saludable.
- **Error de certificado:** confirma el certificado y su SAN; no desactives TLS.

## 7. Seguridad

- Autenticación local gestionada por PC-MASTER; no se envían contraseñas a proveedores externos.
- Cookie HttpOnly, Secure, SameSite=Strict y Path=/; el navegador no puede leerla desde JavaScript.
- La API exige HTTPS y comprueba Origin para login/logout.
- El backend usa el rol PostgreSQL `geelark_master_reader`, con transacciones read-only, `statement_timeout=1500ms`, `lock_timeout=500ms`, `idle_in_transaction_session_timeout=5000ms` y una consulta SELECT limitada. El runtime fija esos tres timeouts y el modo read-only en cada conexión, además de los valores por defecto del rol. Las conexiones PostgreSQL remotas requieren `sslmode=verify-full` y una ruta `sslrootcert` explícita a un archivo CA existente; el runtime normaliza y fija esa ruta antes de conectar, sin recurrir a la CA predeterminada de libpq. En POSIX, el archivo CA y su directorio contenedor deben pertenecer al usuario actual o a root y no pueden ser modificables por grupo/otros; en Windows, el runtime verifica las ACL NTFS del archivo CA y de su directorio, y falla cerrado si una identidad no confiable puede modificarlos. El runtime rechaza contraseñas embebidas en `GEELARK_ADMIN_DATABASE_URL` y `PGPASSWORD`, y rechaza la opción `sslkeylogfile` en el DSN, que puede registrar claves de sesión TLS. También bloquea preventivamente una variable de entorno llamada `PGSSLKEYLOGFILE`; esa variable no es un equivalente documentado de libpq. Debe configurarse `PGPASSFILE` con la ruta explícita a un archivo existente; en POSIX se exige un archivo legible solo por el usuario (modo `0600` o `0400`), propiedad del usuario del proceso, y un directorio contenedor no escribible por grupo/otros; en Windows se restringe la ACL NTFS del archivo y se verifica que su directorio no permita a otras identidades sustituirlo. No se permite depender del archivo de contraseñas predeterminado de libpq, declarar `passfile` dentro del DSN ni usar un `PGPASSFILE` que sea enlace simbólico; el proceso normaliza la ruta al archivo privado validado antes de conectar.
- No hay controles de mutación, ejecución shell, ADB, tareas, ni reconciliación.
- No se persisten credenciales ni snapshots en almacenamiento del navegador.
- La interfaz sirve desde el mismo origen que la API, evitando tener que habilitar CORS.
- El servidor escucha en loopback por defecto; no lo expongas a la LAN sin revisión de seguridad específica.

## 8. Validación de snapshots

Antes de renderizar datos reales, el navegador valida el sobre de respuesta y cada snapshot frente a las restricciones del contrato v1: estructura y campos exactos, UUID, fechas, enumeraciones permitidas, capacidades y módulos admitidos, límites de tamaño, tipos y coherencia entre frescura y salud. Si la respuesta no cumple, se rechaza y el panel muestra el error; no cambia automáticamente al ejemplo ficticio. Esta validación del cliente es defensiva y complementa —no sustituye— la validación y construcción del snapshot en el backend.

## 9. Funciones offline

| Función | ¿Funciona sin conexión? |
|---|---|
| Abrir la página empaquetada en el servidor local | Sí, mientras PC-MASTER esté ejecutándose |
| Navegar por la interfaz | Sí |
| Ejemplo ficticio | Sí |
| Iniciar sesión | Requiere el servicio local |
| Consultar snapshots | Requiere PostgreSQL disponible |
| Consultar GitHub Actions | Requiere Internet |
| Ejecutar operaciones en Workers | No implementado |

Si PostgreSQL está alojado remotamente, consultar datos reales requiere Internet y depende de la disponibilidad/límites del proveedor. Para mayor autonomía y coste controlado, PostgreSQL local es preferible.

## 10. Limitaciones conocidas

- Una sola instancia de servidor; el limitador de login es en memoria y limita a 1024 direcciones rastreadas. Si se llena con intentos aún vigentes, las direcciones nuevas se rechazan temporalmente hasta que expire alguna ventana de 15 minutos; no se asigna memoria sin límite por IP.
- La sesión se guarda en SQLite local y expira en ocho horas. En POSIX, el directorio de sesiones debe pertenecer al usuario del proceso, tener modo privado `0700` y no depender de un directorio superior sustituible; se permite un directorio raíz con sticky bit como `/tmp`.
- CI verifica los permisos del rol y sus valores de sesión (`default_transaction_read_only`, `statement_timeout`, `lock_timeout`, `idle_in_transaction_session_timeout`) en PostgreSQL desechable, incluidas pruebas negativas que alteran cada valor y comprueban que el verificador falla. Los permisos efectivos de la instancia real deben verificarse ejecutando `packages/cluster-master-admin/sql/verify_readonly_role.sql` como el usuario lector.
- La CI aprobada incluye pruebas de la API y verificación de grants en una base PostgreSQL desechable; no sustituye la validación de credenciales, permisos ni conectividad en la instancia real de PC-MASTER ni la revisión manual de seguridad.
- La validación controlada de Windows ya está completada según el registro de trabajo; no equivale a un despliegue en Workers físicos ni habilita sus operaciones. La PR #84 sigue en draft y no está fusionada. Las PR #76 y #79 quedaron supersedidas y cerradas sin merge.
