# Control Android integrado en PC-MASTER

## Separación de operación y diagnóstico

Perfiles es la vista habitual: tabla con nombre configurado, estado de pantalla, Abrir pantalla, Cerrar conexión y Recuperar. Puede buscarse por nombre y filtrarse por pantalla abierta, cerrada o requiere atención. Estos filtros solo cambian la lista, nunca detienen ni reinician Android. Conserva el estilo oscuro del panel. No contiene terminales, registros, pruebas de memoria, rutas de claves, IP del laboratorio ni comandos técnicos.

Diagnóstico técnico es una página independiente (/diagnostics), siempre disponible en PC-MASTER desde el menú Soporte. Su módulo recolector está separado del gestor de procesos. No es una segunda consola de operación y los registros nunca se incluyen en la API operativa. Requiere la sesión del operador; recoger y limpiar requieren el mismo origen.

## Configuración local inicial

Esta primera integración administra una conexión Android explícitamente configurada. No afirma implementar adopción automática, inventario multiinstancia ni asociación con nodos PostgreSQL. No crea dispositivos ficticios cuando no existe configuración.

Crear un JSON local (no subir claves ni contraseñas a GitHub) con estos campos:

```json
{
  "name": "Mi dispositivo Android",
  "host": "worker.example",
  "user": "operador",
  "container": "android-01",
  "key": "C:/Users/OPERADOR/.ssh/clave_worker",
  "port": 15557
}
```

Sustituir los valores por los de la instalación. La clave debe existir y estar autorizada; su ruta es absoluta. Se requiere OpenSSH, ADB y scrcpy en PATH del proceso del PC-MASTER. La identidad del servidor debe estar verificada previamente en known_hosts. No se desactiva esa comprobación ni se guardan contraseñas. La conexión al puerto ADB 5555 del worker se realiza mediante un túnel loopback con puerto local configurable.

En el lanzador, seleccionar el archivo en Conexión Android (JSON). La opción es opcional: sin ella, el panel conserva inventario/tareas y muestra Android sin configurar. Para el laboratorio ya probado se incluye examples/worker-lab-android.json: puede seleccionarse directamente sin escribir comandos ni modificar JSON. Sus valores son configuración de ejemplo separada del software operativo. No existe dependencia de la utilidad Tkinter de laboratorio ni de sus archivos.

Diagnóstico técnico está siempre disponible en el menú Soporte del panel. No hay casilla de activación en el lanzador ni es necesario reiniciar para habilitarlo. PC-MASTER lo activa al arrancar, independientemente del antiguo GEELARK_ADMIN_DIAGNOSTICS. Estar disponible no ejecuta consultas automáticamente: Recoger diagnóstico se pulsa cuando sea necesario.

## Operación diaria

1. Iniciar PC-MASTER y autenticarse con la contraseña del operador habitual.
2. Entrar en Dispositivos y pulsar Abrir pantalla. PC-MASTER comprueba ADB y los servicios input/activity, además del arranque completado. La pantalla aparece dentro de Perfiles, en el panel web; no se abre una ventana independiente de scrcpy.
3. Cerrar conexión termina exclusivamente los procesos SSH/scrcpy propios. Android continúa en el worker. Se puede abrir de nuevo sin reiniciarlo.
4. Si falla Android, Recuperar dispositivo pide confirmación y contraseña del worker mediante un diálogo específico. Reinicia solo el contenedor configurado y comprueba servicios antes de anunciar recuperación. Conserva datos, pero interrumpe operaciones en curso. Nunca reinicia automáticamente ante un error.

La contraseña de recuperación se envía por HTTPS a PC-MASTER y por stdin a sudo sobre SSH. No se añade a comandos, registros, configuración, almacenamiento web ni respuestas. Existe temporalmente en memoria durante la operación. El usuario del worker necesita autorización sudo para Docker; no se modifica sudoers ni se amplían permisos.

## Diagnóstico temporal

En Soporte, abrir Diagnóstico técnico. Recoger diagnóstico consulta Debian, recursos, red, Docker y Android. sudo no interactivo puede rechazar consultas Docker y se documenta ese resultado; los controles habituales siguen disponibles. Copiar registro facilita comunicar una incidencia sin abrir PowerShell. Los registros pueden contener datos del dispositivo: revisar antes de compartir. Se conservan únicamente en memoria acotada del backend; se pierden al cerrarlo.

## Conexión, concurrencia y cierre

Solo se admite una operación a la vez; nuevas solicitudes durante ella devuelven 409 y no se encolan reinicios. Al volver a iniciar sesión se descartan respuestas antiguas. Las mutaciones requieren sesión válida y mismo origen; no hay ejecución de comandos recibidos del navegador. Inventario y tareas PostgreSQL mantienen solo lectura.

El cierre de PC-MASTER cierra sus procesos de pantalla/túnel; no apaga Debian ni el contenedor. Si hay recuperación en curso espera consultas con tiempo límite; el lanzador conserva su parada forzada del árbol como último recurso. Cerrar sesión del navegador no cancela una operación ya aceptada. No abrir simultáneamente la utilidad antigua con el mismo puerto.

Funciona en LAN sin APIs externas, tarjeta ni dependencias de pago. No consulta/controla el worker offline ni encola acciones para ejecutarlas después. Ante puerto ocupado, clave no disponible, worker desconectado o servicios incompletos, informa fallo sin matar procesos ajenos ni borrar datos.

## Validación y alcance

La recuperación, pantalla y cierre/reapertura de la utilidad de laboratorio antecedente fueron confirmados en Windows por el operador. Esta integración web es código nuevo: requiere aceptación gráfica Windows antes de declararse desplegada. Pruebas locales cubren autenticación/origen, diagnóstico opcional, configuración, concurrencia y descarte de respuestas de sesiones anteriores; no sustituyen pruebas LAN, NTFS o PostgreSQL real.

La causa original de Android offline/servicios ausentes sigue pendiente. La recuperación no se presenta como solución de causa raíz. No se cierran automáticamente las puertas de aceptación #77 ni la evaluación #27.


## Panel de operación simplificado

El menú contiene Perfiles, Workers, Tareas y Ayuda. No muestra hojas de ruta, GitHub Actions, costes objetivo, endpoints, epochs, capacidades de protocolo ni declaraciones de implementación. Workers conserva nombre, acceso, estado y última señal; Tareas conserva referencia abreviada, nombre del equipo, estado y fechas. La ausencia de nombre del equipo se indica como no disponible, sin inventarlo. El filtro de tareas permite elegir un worker por nombre.

Ayuda explica abrir/cerrar/recuperar y consultar equipos. El enlace Diagnóstico técnico aparece siempre en Soporte, como una página independiente protegida. No se elimina información de base de datos ni se alteran permisos por limpiar la interfaz.

Esta revisión presenta la conexión existente en una tabla; no crea un inventario persistente multiinstancia, grupos ficticios, nuevas imágenes ni botones sin servicio implementado. El nombre proviene del JSON ya configurado. Cerrar conexión conserva Android; Recuperar reinicia el perfil previa confirmación y contraseña efímera.

Los fallos de consulta de Workers se muestran dentro de Workers, sin sustituir el estado del perfil Android. Sin configuración Android se ofrece una indicación para configurarla y no se muestra una fila operable. Al cerrar sesión se retira la fila y se deshabilitan sus controles; una respuesta tardía no los reactiva.


## Diagnósticos separados por intento

Cada operación aceptada (abrir, cerrar conexión, recuperar o recoger diagnóstico) sustituye el registro temporal anterior e identifica el nuevo intento con fecha UTC. Una operación rechazada porque hay otra en curso no borra su evidencia. Limpiar registro elimina el registro temporal del servidor y de la vista; está bloqueado mientras haya una operación activa. Salida tardía de procesos de intentos anteriores y respuestas HTTP anteriores a la limpieza no vuelven a mezclar registros.

Se conservan como máximo 150 líneas de hasta 2000 caracteres por línea. Las salidas multilínea se separan antes de limitar, evitando perder todo el encabezado de un crash por recortar el bloque completo a sus últimos 2000 caracteres. El diagnóstico consulta el buffer crash de Android en lectura: puede contener eventos históricos con sus fechas. Limpiar esta vista no borra logcat, archivos de Android ni runtime.log. El crash histórico se distingue por su timestamp; no se presenta como nuevo por volver a consultarlo.


## Ventana de navegador administrada por el lanzador

En Windows, Iniciar panel abre una ventana propia de Edge o Chrome en modo aplicación con perfil dedicado en %LOCALAPPDATA%/GeeLark-IA/pc-master/panel-browser-local. Si esa ventana sigue ejecutándose, Iniciar panel la reutiliza; si se cerró, puede reabrirse sin levantar otro backend. Detener panel confirma primero la parada del backend y después cierra la ventana propia. Cerrar el lanzador ejecuta la misma parada.

Edge puede delegar la apertura en otro proceso y terminar el PID inicial. El lanzador consulta los procesos raíz que coinciden con el ejecutable y el argumento completo del directorio de perfil exclusivo. Solicita WM_CLOSE a sus ventanas y verifica que terminaron; si no, vuelve a comprobar esa identidad antes de aplicar el fallback limitado a ese PID y su árbol. No cierra por título, URL ni nombre global de navegador. Si no se confirma cierre, se avisa y se bloquea nuevo arranque hasta resolverlo. No se usan puertos de depuración ni se omite verificación TLS.

Se requiere Edge o Chrome instalado. La ventana usa modo invitado en un directorio dedicado, independiente del navegador personal; no inicia sesión en Edge ni sincroniza navegación. La sesión web se inicia de nuevo al abrir otra sesión de invitado. La preparación HTTPS local se explica en la sección siguiente; no se copia el perfil personal. Las pestañas abiertas por el antiguo webbrowser.open no tienen PID propio rastreado y deben cerrarse manualmente una vez; esta mejora controla las nuevas ventanas. La consulta del directorio exclusivo también permite recuperar una ventana que sobrevivió al lanzador; no se adoptan otros perfiles.


## Inicio local sin cuenta de Edge ni advertencia TLS

La captura del operador mostró que un perfil nuevo normal de Edge podía iniciar sesión automáticamente con la identidad del equipo y ofrecer sincronización. Las nuevas ventanas se abren con --guest y directorio panel-browser-local: Microsoft documenta que Guest no permite iniciar sesión ni sincronizar datos de navegación. No modifica el navegador personal ni elimina datos ya sincronizados por el perfil anterior; ese incidente se registra, no se afirma revertido.

Antes de iniciar el backend, el lanzador valida la pareja certificado/clave, vigencia, uso servidor, firma y nombres localhost/127.0.0.1 con OpenSSL. Si el certificado anterior tenía capacidad de CA o no indicaba CA:FALSE, genera otro de servidor CA:FALSE con SAN localhost/127.0.0.1, EKU serverAuth y clave privada restringida, y actualiza las rutas de configuración. Conserva los archivos originales existentes, sin crear copias de ellos. Un certificado inválido o de otro hostname se rechaza, no se confía automáticamente en él.

Se registra únicamente el certificado público validado por huella exacta en Cert:\CurrentUser\Root, nunca LocalMachine; no se registra la clave privada ni se deshabilita verificación TLS del navegador. La operación requiere OpenSSL (se detecta Git para Windows) y el paquete Master Admin ya instalado. No requiere ejecutar como administrador. La confianza afecta al usuario Windows actual, no solo a un perfil del navegador; se identifica el certificado por huella exacta y se evita duplicarlo. Windows puede presentar su confirmación del almacén si su política lo requiere. El certificado local dura 365 días; si caduca, el arranque debe indicar el error y requiere renovación, no lo ignora.

Los certificados anteriores ya confiados no se eliminan automáticamente. La preparación rechaza certificados autofirmados que no cubran localhost y 127.0.0.1. Certificados emitidos por otras autoridades requieren su cadena y una preparación distinta: esta reparación se limita al HTTPS local autofirmado de PC-MASTER. Nada de esto resuelve por sí solo el crash gráfico de Android.


## Recuperación del fallo gráfico Gralloc 2.0

En el laboratorio Android 12, scrcpy terminaba con SIGABRT y «gralloc-allocator is missing». input/activity y el arranque figuraban disponibles, pero lshal devolvía EX_TRANSACTION_FAILED/interfaceChain fails para android.hardware.graphics.allocator@2.0::IAllocator/default incluso consultando con su 0. El operador ejecutó su 0 setprop ctl.restart vendor.gralloc-2-0, abrió Android, navegó y cerró/reabrió sin repetir el comando. Tras reiniciar Debian también abrió sin reparación; no prueba una solución definitiva de causa raíz.

Recuperar mantiene confirmación y contraseña del worker. Si Android responde y lshal confirma ese fallo específico, cierra la conexión propia, restablece el transporte y reinicia solo vendor.gralloc-2-0. Verifica una fila de servicio con PID sin error de transacción y los servicios input/activity/boot antes de confirmar recuperación. Si no basta o no se puede diagnosticar, aplica el reinicio del contenedor ya autorizado por ese diálogo. Tras reiniciarlo verifica también Gralloc; no anuncia éxito con estado gráfico desconocido. La reparación es específica del laboratorio Gralloc 2.0; no equivale a soporte validado de otras versiones HAL. Requiere su dentro de redroid para la reparación selectiva; si no está disponible, no amplía permisos ni modifica SELinux.

Abrir pantalla y Diagnosticar no reinician servicios. La reparación gráfica realiza una solicitud por fase y como máximo cinco comprobaciones; no reinicia en bucle. No recrea el contenedor ni borra datos, pero puede interrumpir operaciones gráficas. Si se repite el fallo, recoger un diagnóstico nuevo y revisar su causa.

Aceptación del lanzador #153: el operador confirmó cierre de la ventana web al detener y reapertura correcta. Reinicio del worker: primer intento dejó pantalla negra y SSH sin respuesta; un segundo reinicio manual arrancó con Docker/SSH activos y Android accesible sin login Debian. El journal previo llegó a apagado ordenado; VirtualBox registró una corrección de reloj de unos 102 minutos. La causa del bloqueo sigue pendiente, no se atribuye automáticamente a Gralloc ni al reloj.


## Pantalla integrada en Perfiles

Esta revisión sustituye la ventana SDL independiente por un visor dentro del panel. Se requiere scrcpy 5.0.1 instalado con scrcpy-server junto a su ejecutable (se resuelven enlaces de WinGet), ADB y el túnel existente. No instala Node, Appium, servicios de nube ni decodificadores externos. La dependencia ya existente de scrcpy y su licencia Apache 2.0 se conserva sin redistribuir su binario.

Procedimiento: pulsar Abrir pantalla y esperar el visor bajo la tabla de Perfiles. Pulsar o arrastrar dentro de la imagen; para Atrás, Inicio y Recientes, utilizar la barra de navegación propia de Android dentro de la imagen. El panel no duplica esos tres botones debajo del visor. El visor no incluye un formulario externo para enviar texto; utilizar los controles del propio Android. Pantalla completa amplía el visor en el navegador. Cerrar conexión cierra transmisión, controles y túnel propios, conservando Android. Recuperar mantiene su confirmación y puede interrumpir operaciones gráficas.

Requisitos de navegador: contexto HTTPS local y VideoDecoder/WebCodecs con H.264, como Edge/Chrome compatibles. El panel comprueba compatibilidad y comunica el fallo si no puede decodificar; no abre una ventana externa como fallback. El vídeo se codifica en Android (720 px máximo, 15 fps, 2 Mbps objetivo, sin audio), se transporta por SSH/ADB y HTTPS local como paquetes NDJSON/base64 y se decodifica en un canvas. No se guardan grabaciones ni imágenes. Base64 aumenta aproximadamente un tercio el tamaño de los paquetes; evaluar recursos con varios perfiles antes de ampliar. El alcance sigue siendo una conexión real, no 50 perfiles validados.

El servidor admite un lector de vídeo por pantalla. Cada apertura tiene una identidad aleatoria; controles o respuestas de una pantalla anterior no afectan a una nueva. El cierre del flujo, logout/caducidad de sesión o parada del backend termina sockets y procesos propios y elimina solo el forward y JAR de esa apertura. La sesión se comprueba durante el flujo, incluido cuando el vídeo está estático mediante heartbeat. No se borran datos del contenedor ni se usa adb kill-server. El backend solo admite controles tipados y coordenadas dentro de las dimensiones recibidas; no recibe comandos shell del navegador.

No incluye audio, teclado físico completo, portapapeles sincronizado, multitáctil, grabación ni reproducción simultánea multiinstancia. Las pruebas de navegador usan un vídeo rojo H.264 generado para comprobar decodificación y controles, no representan una prueba Android real. La prueba de sockets simula el servidor Android según el protocolo. La aceptación con redroid en la laptop sigue pendiente.

Fuentes técnicas fijadas a v5.0.1 (consulta 01-11-2026): https://github.com/Genymobile/scrcpy/blob/v5.0.1/doc/develop.md ; https://github.com/Genymobile/scrcpy/blob/v5.0.1/server/src/main/java/com/genymobile/scrcpy/device/Streamer.java ; https://github.com/Genymobile/scrcpy/blob/v5.0.1/server/src/main/java/com/genymobile/scrcpy/device/DesktopConnection.java ; https://github.com/Genymobile/scrcpy/blob/v5.0.1/server/src/main/java/com/genymobile/scrcpy/control/ControlMessageReader.java . El protocolo es interno y puede cambiar entre versiones: se rechazan versiones distintas, no se asume compatibilidad.


## Diagnóstico permanente en PC-MASTER

Por solicitud del operador, se elimina la casilla del lanzador. El runtime de PC-MASTER activa siempre la vista y la enlaza directamente en el menú Soporte, junto a Ayuda. No mezcla los registros técnicos con Perfiles, Workers o Tareas. La fábrica de la API conserva su parámetro interno para pruebas aisladas; no es una opción de usuario del producto.

Para investigar una apertura fallida: entrar en Diagnóstico técnico y pulsar Copiar registro sin pulsar Recoger diagnóstico, pues cada operación nueva sustituye el intento anterior. Recoger diagnóstico inicia una consulta nueva; Limpiar registro elimina el registro temporal anterior. La habilitación permanente no altera el borrado por intento ni registra contraseñas ni realiza consultas periódicas de Docker.


## Prueba real del visor integrado — 01-11-2026

Mediante el navegador conectado del operador se verificó el redroid real: imagen en Perfiles, apertura del cajón de aplicaciones por pulsación, apertura de Configuración, desplazamiento táctil de su lista, Inicio desde la barra interna de Android y cierre/reapertura desde PC-MASTER. No se cambiaron ajustes ni datos de Android. Los botones externos duplicados ya no aparecían; Enviar texto aún estaba presente en la versión instalada y se retira en esta revisión por solicitud del operador.

Al recargar se reprodujo una conexión que permanecía ocupada después de abandonar el visor. Se añade cierre explícito de los iteradores y del servidor de pantalla al finalizar o cancelar la respuesta HTTP, con liberación del lector incluso si se corta antes del primer paquete. Se prueba desconexión ASGI 2.0 y 2.4; la corrección requiere instalarse y repetirse en la laptop antes de considerarla aceptada. No equivale a resolver la causa recurrente de Gralloc ni el bloqueo de reinicio de Debian.

## Detección del worker y varios visores — revisión actual

El JSON existente identifica el worker y mantiene la conexión inicial. Al iniciar PC-MASTER se consulta su inventario Docker por SSH. Si sudo requiere contraseña, en Perfiles pulsar Detectar Android y autorizar la consulta una vez. La contraseña solo se transmite por HTTPS y stdin de SSH/sudo; no se conserva. No se amplían permisos de Docker ni sudoers.

La consulta descubre contenedores redroid y sus puertos ADB publicados exclusivamente en loopback; no utiliza nombres ni puertos del laboratorio en el código. Cada perfil nuevo recibe su propio túnel local y servicio de control. Pulsar Abrir pantalla en ambas filas permite dos visores dentro del panel. En pantallas amplias se distribuyen en columnas; en pantallas estrechas se apilan. Cerrar conexión o recuperar afecta únicamente a la fila seleccionada. Los registros temporales siguen separados por perfil y se seleccionan en Diagnóstico técnico. Cada operación sustituye el registro anterior de ese perfil.

El límite defensivo del inventario es 50 contenedores, sin implicar capacidad probada para 50 Android. La detección actual parte del worker ya configurado: no instala Debian en equipos vacíos ni descubre/adopta otros equipos físicos. PXE, adopción de workers, selección de versiones y despliegue se desarrollarán por separado. Los perfiles descubiertos se mantienen durante la ejecución del backend; se vuelven a consultar al iniciar. No se borran contenedores ni datos durante la detección. Un contenedor que desaparece tras haberse detectado conserva su fila hasta reiniciar el panel; al intentar operarlo informa el fallo.

### Preparación comprobada de dos Android en Debian consola

El kernel del laboratorio no tiene CONFIG_ANDROID_BINDERFS. Dos redroid que usan los mismos dispositivos Binder chocaron al registrar servicios HAL. Se crearon dispositivos separados cargando binder_linux con `devices=binder,hwbinder,vndbinder,binder02,hwbinder02,vndbinder02`, persistido en `/etc/modprobe.d/geelark-binder.conf`. La regla udev `/etc/udev/rules.d/99-geelark-binder02.rules` aplica `KERNEL=="binder02|hwbinder02|vndbinder02", MODE="0666"`. Se reinició Debian limpiamente porque el módulo estaba ocupado; no se forzó su descarga.

El segundo contenedor conserva su volumen independiente `/data` y monta `/dev/binder02:/dev/binder`, `/dev/hwbinder02:/dev/hwbinder`, `/dev/vndbinder02:/dev/vndbinder`. Se verificaron números de dispositivo diferentes: primera instancia 10:266/267/268, segunda 10:269/270/271. Ambas completaron arranque, input y activity. Al detener una, la otra conservó esos servicios; se repitió en ambos sentidos. No se ha validado todavía la interacción gráfica simultánea real desde esta revisión del panel.

Ambos contenedores privilegiados comparten kernel: separar Binder y `/data` no constituye aislamiento de seguridad completo ni garantiza identidades de hardware distintas. La identidad persistente y la validación de identificadores Android siguen siendo trabajo independiente. Las pruebas no cierran la aceptación #77 ni autorizan fusiones automáticas de los borradores.

