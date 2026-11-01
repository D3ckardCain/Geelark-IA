# Preparación inicial de PC-MASTER Windows

## Entrada única desde GitHub

Extraer la descarga completa y hacer doble clic normal en PREPARAR_PC_MASTER.bat, situado junto a apps, packages y examples. No ejecutar como administrador. El código y los cambios siguen en GitHub; esta carpeta es la instalación de ejecución.

Se requiere Python 3.11+ con Tkinter y el lanzador py, PostgreSQL local accesible en localhost:5432 y OpenSSL (se detecta el incluido con Git para Windows). El asistente no instala servicios del sistema ni descarga instaladores externos. Si falta un requisito, lo indica. La primera instalación de paquetes Python requiere acceso a sus registros públicos; no requiere tarjeta, API de pago ni prueba temporal.

El preparador crea/reutiliza .venv en la carpeta descargada, instala los paquetes locales de persistencia y Master Admin y abre un asistente gráfico. Las rutas se derivan de la ubicación del script; no dependen de dónde se abra PowerShell. No se activa ningún servicio de PC-MASTER automáticamente.

## Asistente de instalación nueva

Pulsar Preparar PC-MASTER. Solicita la contraseña del administrador PostgreSQL y una nueva contraseña del operador, con confirmación y mínimo 12 caracteres. Puede seleccionarse un JSON de conexión Android existente; es opcional. Los cuadros de contraseña están ocultos.

La preparación automatiza:

1. Creación de geelark si no existe, aplicación de migraciones a un esquema vacío y detección de un esquema existente incompleto. No intenta modificar parcialmente un esquema desconocido.
2. Configuración del rol geelark_master_reader y generación aleatoria de su contraseña, guardada únicamente en pgpass.conf privado. En una preparación nueva puede actualizar la contraseña de ese rol local; no hacerlo si otro sistema depende del mismo rol.
3. Verificación de acceso del lector y modo de solo lectura.
4. Hash PBKDF2 de acceso al panel, certificado/clave HTTPS local, directorio de sesiones privado y settings.json con las rutas completas.
5. Presentación del botón Abrir lanzador una vez completado.

La configuración privada se guarda en %LOCALAPPDATA%/GeeLark-IA/pc-master. Las contraseñas no se incluyen en el repositorio, argumentos de procesos ni registros. La conexión administrativa usa un passfile temporal privado que se elimina al terminar; la prueba del lector usa otro passfile temporal. El secreto del operador queda como hash y la contraseña del lector permanece en el archivo privado requerido por PostgreSQL. El verificador SCRAM del lector se genera a partir de una contraseña ASCII aleatoria.

El certificado es autofirmado para localhost/127.0.0.1. La preparación no lo incorpora automáticamente al almacén de confianza de Windows. Esa aceptación debe verificarse por separado. El panel sigue en loopback.

## Instalación ya preparada

Si existe settings.json y todos sus archivos requeridos, el asistente conserva contraseñas, certificados, estado, configuración Android y base de datos; permite abrir el lanzador. La instalación de paquetes sí se actualiza desde esta descarga. No obtiene la última rama automáticamente ni cambia el código de otras instalaciones.

Si encuentra archivos privados parciales o configuración incompleta, se detiene sin sobrescribirlos. No fabrica copias de seguridad ni elimina datos existentes. La preparación usa un bloqueo para evitar dos asistentes simultáneos. Al fallar una preparación nueva limpia sus archivos temporales y los archivos nuevos publicados por ese intento; los cambios ya confirmados en PostgreSQL pueden permanecer. No se borra la base ni se eliminan tablas para reintentar.

## Lanzador en pantallas pequeñas

El formulario de rutas tiene desplazamiento vertical mediante barra, rueda y navegación por Tab. Los botones Guardar configuración, Diagnosticar, Iniciar panel y Detener panel permanecen en una barra fija; no es necesario maximizar para acceder a ellos. El tamaño inicial se adapta a la pantalla. El diagnóstico continúa siendo opcional por sesión y no se mezcla con los controles permanentes del panel.

## Límites y aceptación

No instala Debian/redroid, no crea workers ni claves SSH, no cambia redes y no proporciona adopción automática. Esta mejora prepara PC-MASTER y su base local; PostgreSQL, Python y OpenSSL deben estar disponibles. La selección Android sigue requiriendo una conexión válida.

Las pruebas incluyen preservación de configuración, rechazo de archivos parciales y ejecución elevada, autenticación SCRAM contra PostgreSQL desechable cuando está disponible, y geometría real Tk en Windows para ventanas 800×600 y 960×720. Validar visualmente en la laptop antes de sustituir su lanzador operativo. No volver a inicializar la instalación ya validada del operador.
