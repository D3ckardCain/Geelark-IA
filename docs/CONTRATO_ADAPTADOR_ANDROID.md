# Contrato del adaptador de motor Android

**Estado:** contrato de diseño v0.1; no implica motor implementado.  
**Fecha:** 2026-10-09

## 1. Objetivo

Permitir que Geelark-IA controle más de un motor Android sin acoplar perfiles, grupos, RPA, API, logs o manuales a comandos específicos de un proveedor. El adaptador encapsula detalles del motor y expone capacidades explícitas.

## 2. Principios

- El dominio no invoca shell ni ADB directamente.
- Todo motor declara versión, capacidades, restricciones y licencias.
- Los IDs internos UUID no son IDs de proceso, contenedor ni seriales del dispositivo.
- Cada acción tiene timeout, límite de salida, error tipado y evento de auditoría redactado.
- No ejecutar comandos arbitrarios recibidos desde UI/API.
- No exponer puertos ADB en redes públicas.
- Operaciones destructivas requieren confirmación de usuario y política de retención/backup.
- Las capacidades no probadas se presentan como «no verificadas».
- Cada operación debe ser cancelable cuando el motor permita hacerlo de forma segura.

## 3. Capacidades

Cada adaptador devuelve una declaración versionada con:
- versiones Android e imágenes disponibles;
- arquitectura/ABI soportadas;
- crear, iniciar, detener, reiniciar y eliminar;
- estado de ciclo de vida;
- persistencia y exportación/importación de backup;
- captura de pantalla y resolución;
- entrada de texto, tap, swipe y teclas;
- instalación/desinstalación de APK;
- ADB autorizado;
- configuración de idioma, zona horaria, densidad, ubicación y red, campo por campo;
- proxy por instancia;
- sensores, cámara, audio y GPS;
- límites de instancias/concurrencia conocidos;
- acceso root y su estado;
- requerimientos de kernel/hipervisor/privilegios;
- funciones no soportadas o que requieren validación.

No asumir que una propiedad configurada se refleja en Android: cada setter reporta «aplicado», «no soportado», «rechazado» o «no verificable».

## 4. Operaciones abstractas

| Operación | Entrada | Resultado mínimo | Requisitos |
|---|---|---|---|
| enumerate_images | filtro opcional | imágenes, versión, ABI, checksum/fuente si existen | No descargar automáticamente |
| create_instance | UUID interno, imagen, configuración validada | ID de motor y estado inicial | Idempotencia por request ID |
| start_instance | UUID interno | estado y endpoint ADB interno | No publicar endpoint fuera de loopback/red aislada |
| stop_instance | UUID, cierre ordenado/forzado | estado final y advertencias | Intentar cierre ordenado primero |
| restart_instance | UUID | resultado de stop/start y verificación | Preservar datos |
| delete_instance | UUID, confirmación, política de backup | resultado y comprobante | Confirmación; evitar borrado ambiguo |
| get_status | UUID | estado normalizado y diagnóstico | Timeout y errores tipados |
| capture_screen | UUID | imagen, timestamp, dimensiones | Limitar tamaño; no guardar permanentemente por defecto |
| send_input | UUID, acción tipada | resultado | Lista permitida; validar coordenadas/duración |
| install_artifact | UUID, hash y ruta interna | resultado y paquete/versión si detectables | Validar origen, hash, tamaño y ABI |
| set_config_field | UUID, clave permitida, valor tipado | aplicado/no soportado/rechazado/no verificable | No aceptar claves arbitrarias |
| export_backup | UUID, destino interno | ruta/manifest/hash | Backup consistente y datos sensibles identificados |
| import_backup | UUID, artefacto validado | resultado y diferencias | No sobrescribir sin confirmación |
| health_check | ninguno | estado del motor, versión, permisos y puertos | No mostrar secretos |

## 5. Estados de instancia normalizados

- created: metadata creada, Android aún no iniciado.
- starting: arranque en curso.
- running: Android listo según una comprobación definida.
- stopping: cierre en curso.
- stopped: detenido con datos persistidos.
- error: fallo con código y diagnóstico redactado.
- deleting: eliminación confirmada en curso.
- unknown: no se puede determinar estado con seguridad.

La transición no se infiere solo de que exista un proceso: el adaptador aplica una prueba de salud con timeout.

## 6. Modelo de errores

Cada error incluye código estable, mensaje en español, detalle técnico redactado, posibilidad de reintento, efectos parciales y request/correlation ID. Códigos iniciales: ENGINE_NOT_READY, IMAGE_UNAVAILABLE, INSTANCE_NOT_FOUND, UNSUPPORTED_CAPABILITY, OPERATION_TIMEOUT, ADB_UNAUTHORIZED, RESOURCE_EXHAUSTED, BACKUP_INVALID y PERMISSION_DENIED.

No incluir contraseñas, tokens, cookies, seriales completos ni variables de entorno en errores.

## 7. Idempotencia y recuperación

- Cada operación repetible acepta request_id.
- Crear instancia repetido con la misma clave devuelve la instancia original o conflicto explícito; nunca crea duplicados silenciosamente.
- Una parada repetida debe terminar en stopped sin daño.
- Una tarea interrumpida durante instalación/restauración informa resultado parcial y requiere inspección antes de reintentar.
- No repetir acciones RPA no idempotentes automáticamente tras reiniciar backend.
- El manager reconcilia el estado persistido con el motor al iniciar.

## 8. Pruebas de conformidad por motor

1. Listar imagen válida y rechazar imagen no disponible.
2. Crear, iniciar, consultar, detener, reiniciar y eliminar.
3. Persistencia de archivos/datos tras reinicio.
4. Captura de pantalla y entrada básica.
5. Instalar APK de prueba y leer estado del paquete.
6. Aislar dos instancias.
7. Backup/restauración con checksum.
8. Interrupción durante arranque/instalación y recuperación.
9. Comprobar que ADB no es accesible desde LAN por defecto.
10. Verificar que errores/logs no contienen secretos.
11. Ejecutar funciones locales sin Internet.
12. Documentar capacidades que no superen la prueba.

## 9. Resultado

Este contrato define la interfaz interna del adaptador Android. En el alcance actual solo se prepara la implementación redroid; su conformidad debe demostrarse mediante código y pruebas, no se presume por la documentación.
