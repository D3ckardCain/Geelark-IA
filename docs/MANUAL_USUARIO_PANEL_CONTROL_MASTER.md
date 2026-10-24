# Manual de usuario — Panel de control PC-MASTER

**Estado actualizado al 2026-10-19:** se han completado comprobaciones operativas adicionales en el PC-MASTER local, documentadas al final de este manual. La aceptación integral de producción y varias pruebas de seguridad siguen pendientes. La CI de la PR #84 está aprobada para su HEAD publicado, pero eso no valida los cambios locales sin publicar.

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

- **Resumen:** contadores y últimos snapshots.
- **Nodos Worker:** búsqueda por nombre o identificador, estado de autorización, salud, heartbeat, versión y capacidades.
- **Módulos:** estado de los módulos reportados y frescura del reporte.
- **Auditoría y CI:** enlaces a las ejecuciones de GitHub. Consultar GitHub requiere Internet.

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
- El backend usa el rol PostgreSQL `geelark_master_reader`, con transacciones read-only, timeouts y una consulta SELECT limitada.
- No hay controles de mutación, ejecución shell, ADB, tareas, ni reconciliación.
- No se persisten credenciales ni snapshots en almacenamiento del navegador.
- La interfaz sirve desde el mismo origen que la API, evitando tener que habilitar CORS.
- El servidor escucha en loopback por defecto; no lo expongas a la LAN sin revisión de seguridad específica.

## 8. Funciones offline

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

## 9. Limitaciones conocidas

- Una sola instancia de servidor; el limitador de login es en memoria.
- La sesión se guarda en SQLite local y expira en ocho horas.
- CI verifica los permisos del rol en PostgreSQL desechable. Los permisos efectivos de la instancia real deben verificarse ejecutando `packages/cluster-master-admin/sql/verify_readonly_role.sql` como el usuario lector.
- La CI aprobada incluye pruebas de la API y verificación de grants en una base PostgreSQL desechable; no sustituye la validación de credenciales, permisos ni conectividad en la instancia real de PC-MASTER ni la revisión manual de seguridad.
- Las pruebas locales no equivalen a una aceptación completa en producción. La PR #76 se cerró sin fusionarse; la PR de reemplazo es la #84, que permanece en borrador y sin fusionar. Completar la lista de aceptación de la issue #77 antes de declarar operativo el módulo.

## 10. Inicio, diagnostico y cierre desde PC-MASTER para Windows

Esta seccion documenta las comprobaciones locales realizadas el 14 de octubre de 2026. Hay dos modos de inicio: el procedimiento manual con Python descrito al principio del manual, o la aplicacion de escritorio Windows descrita aqui. Usa solo uno de los dos modos a la vez. Si inicias desde la aplicacion, no ejecutes tambien el comando manual de Python; el lanzador administra el proceso hijo.

1. Abre PC-MASTER desde el repositorio y ejecuta la comprobación de diagnóstico que ofrezca la interfaz, si está disponible.
2. Pulsa **Iniciar panel**. La aplicacion espera una respuesta HTTPS local antes de abrir el navegador.
3. Comprueba que el navegador llega a `https://localhost:8765/` o al puerto configurado. No omitas ni desactives la validacion TLS del navegador para ocultar un error de certificado.
4. Para detener el backend, pulsa **Detener panel**. Tambien puedes cerrar la ventana y confirmar la parada.
5. Si la aplicacion indica que la parada no esta confirmada, no intentes iniciar otra instancia a ciegas. Comprueba los procesos y el puerto antes de volver a iniciar.
6. Para consultar diagnosticos del proceso, revisa `%LOCALAPPDATA%\GeeLark-IA\pc-master\runtime.log`. No compartas contrasenas, cookies, tokens ni el contenido de `pgpass`.

### Evidencia y limites

En las pruebas locales del 14 de octubre, el backend respondio HTTP 200 por HTTPS y el cierre posterior dejo el puerto 8765 libre. La suite de regresion de la aplicacion Windows y del backend administrativo paso con 39 pruebas aprobadas.

Estas pruebas no sustituyen la validacion del certificado en el navegador, la comprobacion de ACL NTFS y permisos reales de PostgreSQL, ni la prueba completa de login, logout y snapshots contra la base objetivo. La comprobacion de disponibilidad del lanzador no autentica el certificado TLS.

## Actualización de validación local — 2026-10-19

### Comprobaciones locales realizadas

- Se accedió al panel local mediante HTTPS y se confirmó su respuesta HTTP 200.
- El endpoint de snapshots respondió HTTP 401 al solicitarlo sin sesión.
- Se confirmó visualmente que el panel muestra los nodos.
- La base SQLite de sesiones se pudo abrir después de corregir sus permisos de acceso.
- Se comprobó la lectura de nodos en PostgreSQL local con el usuario de lectura previsto.
- Las pruebas del panel Windows registraron 10 aprobadas y las pruebas del runtime de administración, 14 aprobadas, según las ejecuciones documentadas previamente.
- La prueba específica de heartbeat ausente o antiguo terminó con 1 aprobada.
- El usuario confirmó que la acción «Diagnosticar» funcionó correctamente.

### Qué no debe darse por validado

- No se ha demostrado mediante esta prueba que un worker físico se desconectara realmente; se validó el comportamiento del heartbeat mediante una prueba automatizada.
- La respuesta 401 sin sesión no sustituye la prueba integral de contraseña incorrecta, limitación de intentos, inicio de sesión válido, cierre de sesión y revocación de sesión.
- La comprobación de acceso a SQLite no equivale a auditar todas las ACL de los archivos privados y de la clave TLS.
- La lectura de nodos en PostgreSQL no sustituye las pruebas negativas de UPDATE, INSERT, DELETE, DDL y acceso a tablas ajenas en la instancia objetivo.
- Debe comprobarse que el servicio escucha exclusivamente en loopback y que no expone interfaces LAN o IPv6 globales.
- La CI aprobada de la PR #84 corresponde al commit publicado `3b5692467b9442e0e009856224de9eebf0970f5d`. La rama local actual es distinta y contiene cambios sin confirmar; no se debe atribuir esa CI a los cambios locales.
- La aceptación completa de producción sigue pendiente. Mantener la PR #84 en borrador y no habilitar acceso remoto ni fusionar hasta completar las comprobaciones correspondientes de la issue #77.

### Conservación del proyecto

Las comprobaciones anteriores no autorizan a descartar cambios locales ni a fusionar ramas. Los archivos modificados existentes deben conservarse y revisarse por separado antes de cualquier publicación.

## Registro adicional de validación — 2026-10-20

La suite completa del repositorio terminó con 133 pruebas aprobadas, 39 omitidas y 0 fallidas en 11,29 segundos. Las pruebas específicas del panel Windows y del runtime administrativo terminaron con 24 aprobadas. Estas cifras corresponden a ejecuciones posteriores a las descritas en la actualización del 19 de octubre; las cifras anteriores se conservan como historial.

Las pruebas automatizadas no sustituyen la aceptación integral de producción. Siguen pendientes las comprobaciones de seguridad e integración real enumeradas en este manual. La PR #84 no debe considerarse fusionada ni la CI de su HEAD publicado debe atribuirse a cambios locales sin publicar.
