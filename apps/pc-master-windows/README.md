# PC-MASTER para Windows — versión inicial v0.1

## Objetivo de esta entrega

Una aplicación de escritorio Windows para configurar, diagnosticar, iniciar y detener el panel local GeeLark-IA PC-MASTER. Usa Python/Tkinter, incluido con la distribución estándar de Python; no requiere un servicio de pago, una cuenta externa ni conexión a Internet para abrir la interfaz. La API necesita que sus paquetes estén instalados; PostgreSQL puede ser local y no se requiere conectividad externa si todo se aloja en el mismo PC.

**Esta es una primera versión de pruebas**, no un instalador final. Nota de estado: esta frase describe el estado anterior a las pruebas locales documentadas el 2026-10-14. Esas pruebas cubrieron la suite indicada, la respuesta HTTPS local y el cierre del proceso; no completan la aceptación de seguridad ni la integración real con PostgreSQL. La UI y la validación estática deben probarse primero; ACL NTFS, certificado, conexión PostgreSQL y la sesión real requieren pruebas en Windows.

## Requisitos

- Windows 10/11 de 64 bits.
- Python 3.11 o posterior, instalado desde python.org con `py` Launcher.
- Checkout local del repositorio GeeLark-IA.
- API `cluster-master-admin` y persistencia instaladas en el mismo intérprete de Python usado por el lanzador.
- PostgreSQL preparado con el esquema de GeeLark-IA y rol lector restringido.
- Archivo hash del operador, certificado TLS local y archivo PGPASSFILE con ACL NTFS privada.

## Arranque de la aplicación

1. Descarga/clona el repositorio desde GitHub y cambia a la rama de esta entrega.
2. Abre PowerShell en la raíz del repositorio.
3. Instala los paquetes en un entorno virtual:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e packages/cluster-persistence -e packages/cluster-master-admin
   ```

4. Abre la carpeta `apps\pc-master-windows` y ejecuta `run_pc_master.bat`, o desde la raíz ejecuta:

   ```powershell
   .\.venv\Scripts\python.exe apps\pc-master-windows\pc_master.py
   ```

   Usa el mismo Python para instalar los paquetes y ejecutar la app. Si utilizaste otro intérprete, el botón Diagnosticar indicará que no encuentra la API.

## Preparación segura previa al inicio del panel

No rellenes rutas inventadas. Deben existir los archivos indicados y la base debe estar preparada. Consulta `packages/cluster-master-admin/README.md` para generar el hash de operador, crear certificado SAN `localhost`/`127.0.0.1`, preparar PostgreSQL y ejecutar los scripts SQL de rol lector.

1. Crea un directorio privado en `%LOCALAPPDATA%\GeeLark-IA\master-admin`.
2. Restringe sus ACL NTFS al usuario que operará PC-MASTER. No continúes si `icacls` muestra acceso para usuarios/grupos generales.
3. Configura `operator-auth.json`, `master-local.crt`, `master-local.key` y `pgpass` según el manual del módulo backend.
4. En la app indica las rutas completas. El DSN de ejemplo apunta a PostgreSQL local y no contiene contraseña. Si tu base usa otro nombre/puerto, cámbialo sin introducir contraseña.
5. Pulsa **Diagnosticar**. Corrige todos los problemas antes de iniciar.
6. Pulsa **Guardar configuración**. El archivo de configuración de la app contiene rutas y parámetros, no contraseñas. Se guarda en `%LOCALAPPDATA%\GeeLark-IA\pc-master\settings.json`.
7. Pulsa **Iniciar panel**. La app fuerza el bind `127.0.0.1`, elimina `GEELARK_ADMIN_ALLOW_REMOTE` del entorno hijo y abre `https://localhost:8765/` (o el puerto configurado) cuando detecta el socket local.
8. Si el navegador advierte del certificado, no lo ignores a ciegas: comprueba el certificado y establece confianza local de acuerdo con el manual. No desactives validación TLS.
9. Al terminar, pulsa **Detener panel** o cierra la app y confirma que el proceso se detuvo.

## Qué incluye y qué no

Incluye:
- Interfaz Windows de escritorio.
- Guardado local de parámetros no secretos.
- Diagnóstico de versión Python, disponibilidad del paquete, rutas y configuración.
- Inicio/detención del backend local y apertura del panel en navegador.
- El panel queda limitado a loopback; esta app no expone acceso a la LAN.

No incluye todavía:
- Instalador `.exe` firmado ni actualización automática.
- Configuración automática de PostgreSQL, certificados o ACL NTFS.
- Control de dispositivos Android, ADB, shell, ejecución remota o mutación de nodos.
- Operación completa offline del backend: la interfaz abre offline, pero las consultas reales requieren PostgreSQL disponible.
- Validación física en PC-MASTER del usuario.

## Privacidad, seguridad y coste

- Solo biblioteca estándar en la interfaz.
- No se guardan contraseñas de PostgreSQL ni de operador en la configuración de esta app.
- El DSN con contraseña embebida se rechaza; usa PGPASSFILE con ACL NTFS restringida.
- No se abren puertos remotos y no se habilita `GEELARK_ADMIN_ALLOW_REMOTE`.
- No requiere APIs de pago ni servicios externos obligatorios. La descarga inicial de Python/dependencias requiere Internet. El uso de un proveedor PostgreSQL remoto puede tener costes; para respetar $0, se prefiere PostgreSQL local.

## Prueba inicial que debe hacer el usuario

1. Ejecutar `run_pc_master.bat`.
2. Confirmar que abre la ventana sin errores.
3. Pulsar **Diagnosticar** y compartir el texto del resultado (sin compartir contraseñas ni contenido de `pgpass`).
4. Si indica que falta la API, seguir el paso de instalación de paquetes y repetir.
5. Cuando el diagnóstico esté limpio, configurar las rutas y hacer una prueba de inicio/detención solo con PostgreSQL local de pruebas.
6. Reportar captura o texto de errores; ocultar nombres de usuario/rutas personales si lo desea.

## Limitaciones conocidas v0.1

- El proceso hijo redirige salida estándar y errores para evitar que mensajes inesperados expongan datos. Si no inicia, el estado de UI es genérico; en la siguiente iteración se añadirá un diagnóstico local redactado sin secretos.
- El JSON de ajustes contiene rutas. Windows debe proteger el perfil de usuario; la versión inicial no modifica automáticamente ACL del perfil ni del archivo de ajustes.
- No se debe considerar operativa hasta completar las pruebas Windows documentadas en la issue #77.

## Validacion local de PC-MASTER — 2026-10-14

Esta seccion actualiza el estado de las pruebas locales realizadas el 14 de octubre de 2026. No elimina las limitaciones de seguridad ni sustituye la aceptacion funcional completa.

### Resultados comprobados

- La suite `pytest packages\cluster-master-admin\tests apps\pc-master-windows\tests\test_pc_master.py -q` termino con 39 pruebas aprobadas.
- `git diff --check` termino sin errores de formato. Los avisos de finales de linea LF/CRLF no fueron errores.
- El backend respondio por HTTPS en `127.0.0.1:8765`; una solicitud de comprobacion de sesion obtuvo HTTP 200.
- Se comprobo el cierre de la aplicacion: no quedaron procesos identificados como PC-MASTER/backend y el puerto 8765 quedo libre.
- El backend escribe su salida estandar y errores en `%LOCALAPPDATA%\GeeLark-IA\pc-master\runtime.log`, en modo de adicion.
- El cierre solicita primero una parada coordinada mediante la entrada privada del proceso. En Windows, `taskkill /T /F` queda como alternativa de emergencia si no se confirma la salida.

### Como revisar el registro

1. Abre PowerShell con la cuenta que ejecuta PC-MASTER.
2. Ejecuta `Get-Content -LiteralPath (Join-Path $env:LOCALAPPDATA 'GeeLark-IA\pc-master\runtime.log') -Tail 100`.
3. Antes de compartir resultados, revisa que no contengan secretos, rutas privadas ni informacion sensible.
4. No interpretes errores historicos del registro como fallos nuevos sin comparar la hora de cada entrada.

### Pendiente de aceptacion completa

- Repetir inicio y cierre desde la interfaz tras cualquier cambio posterior.
- Verificar la confianza del certificado TLS en el navegador y comprobar que no se desactiva la validacion TLS del navegador.
- Confirmar login, logout y lectura real de snapshots con la base de datos prevista.
- Verificar las ACL NTFS y los privilegios efectivos del rol PostgreSQL en la instancia objetivo.
- Completar la revision de seguridad y la lista de aceptacion asociada a la issue #77.

La comprobacion HTTPS interna de disponibilidad de la aplicacion no valida la identidad del certificado: el navegador debe efectuar su propia validacion TLS. Los resultados de estas pruebas no autorizan exponer el servicio a la LAN.

## Estado documental actualizado — 2026-10-20

La suite completa del repositorio se ejecutó localmente con Python 3.15.0: 133 pruebas aprobadas, 39 omitidas y 0 fallidas (11,29 segundos). Esta ejecución es posterior a las comprobaciones específicas documentadas anteriormente; no reemplaza sus resultados históricos.

Las pruebas específicas de `apps/pc-master-windows/tests/test_pc_master.py` y `packages/cluster-master-admin/tests/test_runtime.py` terminaron con 24 aprobadas en conjunto. `git diff --check` no detectó errores en la revisión anterior. La aceptación integral de producción sigue pendiente, incluida la validación de TLS en el navegador, las ACL NTFS y las pruebas completas de autenticación y permisos de PostgreSQL. Mantener el servicio limitado a loopback.
