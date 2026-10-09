# Modelo de amenazas y requisitos de seguridad — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** requisitos de diseño; no representa una auditoría de código ni una implementación existente.  
**Alcance:** aplicación local, instancias Android virtuales, ADB/shell, RPA, proxies, archivos, importación opcional desde Android físico y API/CLI local.

## 1. Objetivos de seguridad

1. Mantener control del propietario sobre las instancias y los datos.
2. No exponer ADB, shell ni API de administración a redes no confiables.
3. Evitar que contraseñas, tokens, cookies, claves 2FA, archivos privados o datos de aplicaciones aparezcan en logs, exportaciones o respaldos sin cifrado.
4. Limitar las operaciones destructivas y privilegiadas mediante confirmación, permisos y auditoría.
5. No modificar el Android físico de origen durante la inspección/importación.
6. Permitir que la administración local básica funcione sin Internet.
7. Evitar dependencias obligatorias de servicios cloud, telemetría o APIs de pago.
8. Documentar límites de aislamiento y no presentar contenedores como una frontera de seguridad perfecta.

## 2. Activos que proteger

- Perfiles, configuración e identidad sintética de cada instancia.
- Datos persistentes del Android virtual y archivos de usuario.
- Credenciales de proxy y datos de autenticación del API local.
- Archivos multimedia y APK aportados por el usuario.
- Flujos RPA, parámetros de tareas, historial y capturas de pantalla.
- Datos obtenidos de un Android físico conectado por ADB.
- Copias de seguridad, exportaciones y claves de cifrado.
- Integridad de la base de datos y del registro de auditoría.

## 3. Límites de confianza

1. **Interfaz local → API local:** validar todas las entradas aunque el servidor escuche solo en localhost.
2. **API → motor Android:** tratar comandos y respuestas del motor como datos no confiables; aplicar timeout y límites de salida.
3. **Motor/instancia → otras instancias:** aislamiento obligatorio de directorios, datos, puertos y credenciales.
4. **Android físico → importador:** lectura explícita, mínima y de solo lectura; no confiar en nombres o propiedades devueltas por el dispositivo.
5. **Archivos importados → parser/instalador:** validar tipo, tamaño, nombre, contenido y rutas; evitar traversal, enlaces simbólicos y descompresión insegura.
6. **RPA → aplicaciones/sistema:** cada bloque tiene permisos y límites; el flujo no puede ejecutar comandos arbitrarios sin una autorización elevada.
7. **Integraciones externas → aplicación:** opcionales, configurables y desactivables; no deben ser necesarias para iniciar la aplicación local.

## 4. Amenazas y controles

| Amenaza | Control requerido | Prueba de aceptación |
|---|---|---|
| ADB expuesto en LAN/Internet | Enlace a loopback/red interna aislada por defecto; firewall; no publicar puertos; documentación visible | Escaneo desde otra máquina no alcanza ADB ni API de administración por defecto |
| API local sin autenticación | Token local o sesión protegida, permisos mínimos y protección CSRF cuando aplique | Petición sin credenciales se rechaza; sesión revocada no vuelve a funcionar |
| Robo de credenciales de proxy | Cifrado en reposo cuando sea viable; secretos separados de metadatos; no incluirlos en logs | Buscar patrones de contraseña en logs, informes, exportaciones y mensajes de error |
| Exposición de token/cookie/clave 2FA | Redacción de secretos, permisos de lectura, confirmación antes de exportar | Exportación por defecto no contiene secretos; prueba automatizada de redacción |
| RPA malicioso o accidental | Permisos por bloque, límites de tiempo/iteraciones, confirmación para acciones destructivas, botón de parada | Flujo infinito se detiene por límite; cancelar interrumpe en tiempo razonable |
| Comando shell peligroso | Shell deshabilitado para roles no autorizados; lista de operaciones permitidas; timeout y registro redactado | Rol sin permiso no ejecuta shell; comando bloqueado queda auditado sin datos secretos |
| Archivo malicioso o ruta manipulada | Validación de tamaño/extensión/contenido, almacenamiento aislado y rutas normalizadas | Rechazar traversal, archivo sobredimensionado y formato no permitido |
| Contaminación entre instancias | Directorios/volúmenes y puertos separados; identificadores únicos; evitar clonar datos privados por defecto | Dos instancias no leen/escriben el almacenamiento de la otra |
| Importación accidental de datos personales | Lista de campos permitidos, vista previa y exclusión sensible por defecto | Cancelación no guarda nada; origen no cambia; cuentas/tokens no se importan |
| SSRF en webhooks o URLs de proxy | Validación de esquema/destino, bloqueo de loopback/link-local/metadata en webhooks externos, timeouts | URL a servicios internos es rechazada en configuración de webhook |
| Pérdida/corrupción de datos | Copias de seguridad, migraciones versionadas, escritura atómica y recuperación probada | Restaurar backup en instalación limpia y comparar hashes/resultados |
| Actualización comprometida | Fuentes oficiales, verificación de checksums/firma cuando existan, registro de versiones y rollback | Reproducir instalación con versión fija y comprobar integridad |
| Telemetría externa inesperada | Sin telemetría obligatoria; conexiones externas documentadas y desactivables | Modo sin Internet no realiza llamadas externas para operaciones locales |
| Escalada de privilegios por contenedor | Evitar el modo privilegiado si el motor lo permite; justificar excepciones; ejecutar con usuario mínimo; limitar capacidades | Revisión de configuración y prueba de permisos efectivos |
| Acceso a datos mediante logs/capturas | Retención configurable, permisos de lectura y redacción; no guardar capturas sensibles por defecto | Usuario sin permiso no consulta logs/capturas ajenos |

## 5. Requisitos de importación desde Android físico

- Detección de dispositivos y lectura solo después de que el usuario autorice la conexión.
- El prototipo inicial solo inspecciona datos técnicos no sensibles y no modifica el dispositivo.
- Vista previa campo por campo, con origen, sensibilidad, compatibilidad y motivo de exclusión.
- Cuentas, contraseñas, tokens, mensajes, contactos, archivos privados y datos de aplicaciones excluidos por defecto.
- Identificadores protegidos, claves de hardware y señales de integridad no se intentarán extraer ni falsificar.
- Cada importación tendrá ID único, fecha, campos seleccionados, resultado por campo y acción de borrado.
- No guardar número de serie completo si no es necesario; usar representación enmascarada o hash local con sal cuando proceda.
- Cancelar antes de aplicar debe dejar el perfil destino sin cambios.

## 6. Operación offline y secretos

- Los datos y secretos permanecen locales por defecto.
- La aplicación debe indicar qué funciones intentan acceder a Internet y por qué.
- No incluir secretos en logs, errores, eventos, informes, capturas de diagnóstico ni datos de prueba.
- Los respaldos que incluyan datos de instancias deben permitir cifrado y verificación de integridad.
- La recuperación de contraseña local no puede depender obligatoriamente de correo o proveedor cloud; el mecanismo elegido se especificará antes de implementar autenticación multiusuario.

## 7. Seguridad del modelo de despliegue

La elección de motor Android queda condicionada a su modelo de permisos. La documentación de redroid muestra ejemplos con el modo privilegiado y advierte expresamente que ADB no debe exponerse en una red pública. Por tanto, cualquier uso de redroid requiere revisar privilegios, binder, puertos, persistencia y aislamiento antes de aprobarlo.

Fuente de referencia: https://github.com/remote-android/redroid-doc

La aplicación no se considerará segura solo porque se ejecute en local. Los puertos, procesos, archivos, permisos del anfitrión y secretos necesitan configuración segura.

## 8. Pruebas de seguridad mínimas antes de cada versión

1. Escaneo de puertos y revisión de enlaces de escucha.
2. Pruebas de autorización por rol/instancia/grupo.
3. Pruebas de redacción de secretos en todos los tipos de logs.
4. Pruebas de traversal y límites de tamaño de archivos.
5. Prueba de cancelación y límites de RPA.
6. Prueba de aislamiento de datos entre dos instancias.
7. Prueba de importación de solo lectura y cancelación sin cambios.
8. Restauración de backup y verificación de integridad.
9. Arranque offline y verificación de ausencia de dependencias externas obligatorias.
10. Revisión de licencias y puertos/privilegios del motor Android.

## 9. Criterio de aprobación

No se publicará una versión como lista para uso real hasta completar las pruebas críticas, documentar riesgos residuales y proporcionar una guía de configuración segura. Este documento es un plan de controles: no afirma que el producto actual implemente dichos controles.
