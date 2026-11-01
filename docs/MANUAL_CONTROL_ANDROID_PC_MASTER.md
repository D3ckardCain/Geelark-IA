# Control Android integrado en PC-MASTER

## Separación de operación y diagnóstico

Perfiles es la vista habitual: tabla con nombre configurado, estado de pantalla, Abrir pantalla, Cerrar conexión y Recuperar. Puede buscarse por nombre y filtrarse por pantalla abierta, cerrada o requiere atención. Estos filtros solo cambian la lista, nunca detienen ni reinician Android. Conserva el estilo oscuro del panel. No contiene terminales, registros, pruebas de memoria, rutas de claves, IP del laboratorio ni comandos técnicos.

Diagnóstico técnico es una página independiente (/diagnostics), desactivada por defecto. Su módulo recolector está separado del gestor de procesos. Desactivarla no afecta abrir, cerrar ni recuperar. No es una segunda consola de operación. La página y sus API responden 404 cuando está desactivada; los registros nunca se incluyen en la API operativa.

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

Para una sesión de soporte, marcar Habilitar diagnóstico técnico solo en esta sesión en el lanzador antes de iniciar el panel (equivale a GEELARK_ADMIN_DIAGNOSTICS=1). La casilla no se guarda en la configuración. El enlace Diagnóstico técnico aparece en Sistema; requiere sesión válida. Desmarcar la casilla y reiniciar PC-MASTER elimina la vista y sus API. Las rutas del diagnóstico y el marcador de navegación no contienen controles operativos permanentes.

## Operación diaria

1. Iniciar PC-MASTER y autenticarse con la contraseña del operador habitual.
2. Entrar en Dispositivos y pulsar Abrir pantalla. PC-MASTER comprueba ADB y los servicios input/activity, además del arranque completado. La ventana scrcpy se abre localmente en Windows; no es un streaming dentro del navegador.
3. Cerrar conexión termina exclusivamente los procesos SSH/scrcpy propios. Android continúa en el worker. Se puede abrir de nuevo sin reiniciarlo.
4. Si falla Android, Recuperar dispositivo pide confirmación y contraseña del worker mediante un diálogo específico. Reinicia solo el contenedor configurado y comprueba servicios antes de anunciar recuperación. Conserva datos, pero interrumpe operaciones en curso. Nunca reinicia automáticamente ante un error.

La contraseña de recuperación se envía por HTTPS a PC-MASTER y por stdin a sudo sobre SSH. No se añade a comandos, registros, configuración, almacenamiento web ni respuestas. Existe temporalmente en memoria durante la operación. El usuario del worker necesita autorización sudo para Docker; no se modifica sudoers ni se amplían permisos.

## Diagnóstico temporal

En Sistema, abrir Diagnóstico técnico cuando esté habilitado. Recoger diagnóstico consulta Debian, recursos, red, Docker y Android. sudo no interactivo puede rechazar consultas Docker y se documenta ese resultado; los controles habituales siguen disponibles. Copiar registro facilita comunicar una incidencia sin abrir PowerShell. Los registros pueden contener datos del dispositivo: revisar antes de compartir. Se conservan únicamente en memoria acotada del backend; se pierden al cerrarlo.

## Conexión, concurrencia y cierre

Solo se admite una operación a la vez; nuevas solicitudes durante ella devuelven 409 y no se encolan reinicios. Al volver a iniciar sesión se descartan respuestas antiguas. Las mutaciones requieren sesión válida y mismo origen; no hay ejecución de comandos recibidos del navegador. Inventario y tareas PostgreSQL mantienen solo lectura.

El cierre de PC-MASTER cierra sus procesos de pantalla/túnel; no apaga Debian ni el contenedor. Si hay recuperación en curso espera consultas con tiempo límite; el lanzador conserva su parada forzada del árbol como último recurso. Cerrar sesión del navegador no cancela una operación ya aceptada. No abrir simultáneamente la utilidad antigua con el mismo puerto.

Funciona en LAN sin APIs externas, tarjeta ni dependencias de pago. No consulta/controla el worker offline ni encola acciones para ejecutarlas después. Ante puerto ocupado, clave no disponible, worker desconectado o servicios incompletos, informa fallo sin matar procesos ajenos ni borrar datos.

## Validación y alcance

La recuperación, pantalla y cierre/reapertura de la utilidad de laboratorio antecedente fueron confirmados en Windows por el operador. Esta integración web es código nuevo: requiere aceptación gráfica Windows antes de declararse desplegada. Pruebas locales cubren autenticación/origen, diagnóstico opcional, configuración, concurrencia y descarte de respuestas de sesiones anteriores; no sustituyen pruebas LAN, NTFS o PostgreSQL real.

La causa original de Android offline/servicios ausentes sigue pendiente. La recuperación no se presenta como solución de causa raíz. No se cierran automáticamente las puertas de aceptación #77 ni la evaluación #27.


## Panel de operación simplificado

El menú contiene Perfiles, Workers, Tareas y Ayuda. No muestra hojas de ruta, GitHub Actions, costes objetivo, endpoints, epochs, capacidades de protocolo ni declaraciones de implementación. Workers conserva nombre, acceso, estado y última señal; Tareas conserva referencia abreviada, nombre del equipo, estado y fechas. La ausencia de nombre del equipo se indica como no disponible, sin inventarlo. El filtro de tareas permite elegir un worker por nombre.

Ayuda explica abrir/cerrar/recuperar y consultar equipos. El enlace Diagnóstico técnico solo aparece si fue habilitado en el lanzador para esa sesión; sigue siendo otra página protegida. No se elimina información de base de datos ni se alteran permisos por limpiar la interfaz.

Esta revisión presenta la conexión existente en una tabla; no crea un inventario persistente multiinstancia, grupos ficticios, nuevas imágenes ni botones sin servicio implementado. El nombre proviene del JSON ya configurado. Cerrar conexión conserva Android; Recuperar reinicia el perfil previa confirmación y contraseña efímera.

Los fallos de consulta de Workers se muestran dentro de Workers, sin sustituir el estado del perfil Android. Sin configuración Android se ofrece una indicación para configurarla y no se muestra una fila operable. Al cerrar sesión se retira la fila y se deshabilitan sus controles; una respuesta tardía no los reactiva.


## Diagnósticos separados por intento

Cada operación aceptada (abrir, cerrar conexión, recuperar o recoger diagnóstico) sustituye el registro temporal anterior e identifica el nuevo intento con fecha UTC. Una operación rechazada porque hay otra en curso no borra su evidencia. Limpiar registro elimina el registro temporal del servidor y de la vista; está bloqueado mientras haya una operación activa. Salida tardía de procesos de intentos anteriores y respuestas HTTP anteriores a la limpieza no vuelven a mezclar registros.

Se conservan como máximo 150 líneas de hasta 2000 caracteres por línea. Las salidas multilínea se separan antes de limitar, evitando perder todo el encabezado de un crash por recortar el bloque completo a sus últimos 2000 caracteres. El diagnóstico consulta el buffer crash de Android en lectura: puede contener eventos históricos con sus fechas. Limpiar esta vista no borra logcat, archivos de Android ni runtime.log. El crash histórico se distingue por su timestamp; no se presenta como nuevo por volver a consultarlo.
