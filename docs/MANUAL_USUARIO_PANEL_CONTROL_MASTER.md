# Manual de usuario — Panel PC-MASTER

## Estado y alcance vigente
Panel web local para Windows, estilo GitHub Dark. Rama de desarrollo: `fix/pc-master-session-acl-hardening`, PR #139. Workers previstos: Debian 13 y redroid.
Las funciones descritas están en la rama; la aceptación manual Windows sigue pendiente en #77. Redroid continúa bloqueado por #27. No se declara validación de hardware.

## Acceso
Inicia el panel desde el lanzador Windows y abre la URL HTTPS local configurada (por defecto https://localhost:8765/). Verifica el certificado y usa la contraseña local del operador. La sesión usa cookie segura y caduca a las ocho horas.
Cerrar sesión revoca la sesión en el servidor. Un error de red no se presenta como cierre confirmado.

## Navegación
La barra lateral ofrece Nodos, Tareas y Sistema. En pantallas estrechas aparece sobre el contenido.

### Nodos
- Actualizar estado consulta el Master autenticado. No se generan workers de ejemplo.
- Busca por nombre o identificador. Combina la búsqueda con filtros de autorización y salud; todos deben coincidir.
- Los contadores generales corresponden al inventario recibido; el contador de la tabla indica cuántos nodos coinciden.
- Pulsa el nombre de un worker para abrir su ficha. El nombre es un botón accesible con teclado.
- La ficha muestra ID, versión del agente, último heartbeat, fecha del snapshot, autorización, salud derivada, salud reportada y frescura.
- Capacidades: lista completa de lo reportado. Un listado vacío significa ausencia de evidencia.
- Módulos: inventario completo del worker, con estado, versión, fecha, fuente y código de error. El resumen general solo muestra los ocho primeros; la ficha no tiene ese recorte.
- Cerrar ficha vuelve el foco a la búsqueda.
- Al actualizar, la ficha toma los datos del nuevo snapshot. Si desaparece el nodo, falla la consulta o se cierra la sesión, se elimina el detalle anterior.
- La antigüedad se calcula en PostgreSQL cuando se genera el snapshot; no es un contador en vivo. Pulsa Actualizar estado para renovarla.
- La API devuelve como máximo 500 nodos por consulta. No hay paginación en esta versión.

### Tareas
Pantalla informativa. Aunque la bandeja durable existe en el backend del agente, esta versión administrativa no consulta ni ejecuta tareas. No ofrece órdenes remotas, shell ni ADB.

### Sistema
Muestra la conexión con la API y enlaces a GitHub/Actions. Las descripciones de configuración son el diseño previsto; no sustituyen la verificación efectiva de TLS, ACL y loopback del equipo.

## Estados
Autorización y salud son señales distintas. Un nodo pendiente no queda autorizado porque reporte salud.
- Saludable: evidencia fresca y reporte saludable.
- Degradado: reporte de salud degradado o no saludable.
- Desconectado: heartbeat antiguo o ausente.
- Desconocido: evidencia insuficiente o incoherente.
Los módulos ausentes o desconocidos no se consideran instalados.

## Errores
401/403: comprobar sesión y origen local. 429: límite de intentos, esperar la ventana indicada. 503 o fallo de conexión: actualizar de nuevo cuando el servicio y PostgreSQL estén disponibles. No se conservan datos antiguos como si fueran actuales.
No ignores errores del certificado. No compartas contraseña, cookies, pgpass ni claves TLS.

## Operación sin Internet
El panel y sus consultas funcionan sin Internet mientras el servicio local y PostgreSQL sean accesibles. GitHub y Actions requieren Internet. No hay caché persistente ni modo PWA; con el servicio detenido no se garantiza abrir la página. No se almacenan snapshots ni credenciales en localStorage/IndexedDB.

## Validación
Las pruebas automáticas verifican API, ACL, lanzador, PostgreSQL y comportamiento JavaScript de filtros/ficha, incluido escape de texto y eliminación de datos sin sesión.
La revisión visual y de teclado en Windows real sigue pendiente en #77. Las cifras de CI pertenecen a cada SHA y se registran en #139; no sustituyen esa aceptación.

## Historial de validación local (conservado)

Los registros siguientes son históricos. Sus referencias a PR y estados locales corresponden a aquellas fechas; para el funcionamiento vigente usa las secciones anteriores.

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
