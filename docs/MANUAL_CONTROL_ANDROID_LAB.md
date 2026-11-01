# Control práctico del laboratorio Android

Relacionado: #144. Utilidad local independiente; aún no integrada con el panel PC-MASTER.

## Requisitos

Windows con Python 3.11 o posterior y Tkinter. OpenSSH, adb y scrcpy disponibles en PATH. Worker Debian encendido, accesible en 192.168.0.11, usuario geelarkia y clave local ~/.ssh/geelark_worker_lab ya autorizada y sin frase de protección. La identidad del worker debe existir en known_hosts: no se desactiva su verificación.

No requiere instalar paquetes Python, tarjeta ni API de pago. Usa la LAN; sin conexión al worker no puede consultar Android. Los registros existentes permanecen disponibles localmente.

## Uso

1. Descargar juntos tools/ABRIR_CONTROL_ANDROID.bat y tools/control_android_lab.py, o extraer el ZIP de la rama completa.
2. Hacer doble clic en ABRIR_CONTROL_ANDROID.bat. No necesita PowerShell abierto. VirtualBox debe mantener la VM encendida; puede estar minimizado.
3. Pulsar Diagnosticar. Consulta Debian, memoria, disco, red, Docker y Android. Guarda un registro en %LOCALAPPDATA%/GeeLark-IA/worker-lab; su ruta aparece en la ventana. El registro puede contener datos del dispositivo; revisarlo antes de compartir.
4. Abrir Android comprueba ADB, boot_completed, input y activity antes de iniciar scrcpy. Si faltan servicios, muestra el error y exige diagnóstico; no reinicia ni borra Android.
5. Cerrar conexión o cerrar la ventana termina únicamente scrcpy y SSH creados por esta herramienta. Debian, Docker y los datos Android continúan. No detiene globalmente ADB ni otros túneles.

El puerto local dedicado es 15557 y escucha exclusivamente en 127.0.0.1. Si está ocupado, se muestra error y no se intenta matar su propietario. La herramienta conserva el túnel mientras está abierta y lo vuelve a crear en la siguiente operación si murió. No implementa vigilancia continua ni reparación automática.

## Diagnóstico y límites

Docker se consulta mediante sudo -n: si requiere contraseña, se registra que esa parte quedó pendiente; no se añaden permisos ni se guarda contraseña. El diagnóstico Android usa ADB mediante SSH, no necesita sudo. Tiempo límite de consultas remotas y ADB; la interfaz permanece disponible mientras trabaja. Al cerrar durante una consulta espera su tiempo límite antes de terminar procesos propios.

No modifica el contenedor, sus opciones, la red ni las claves. No soluciona aún el fallo de servicios de Android ni la pérdida de IPv4. El dispositivo fijo corresponde al laboratorio virtualizado, no a una validación de capacidad física. Para usar otro worker hay que modificar las constantes del archivo Python; configuración visual y enlace al panel quedan pendientes.

## Validación

Pruebas locales con procesos simulados: rechazo de boot_completed sin servicios, servicios obligatorios, bloqueo de scrcpy con Android incompleto, cierre limitado a procesos propios y rechazo de puerto ocupado. Validación gráfica Windows y conexión real pendientes; no se afirma que estas pruebas simulen Android/SSH reales.
