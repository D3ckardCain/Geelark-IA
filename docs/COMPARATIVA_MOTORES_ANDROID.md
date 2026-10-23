# Motor Android seleccionado para evaluación: redroid

**Actualizado:** 2026-10-22. **Estado:** preparación documental; bloqueado para despliegue físico por la issue #27. No aprobado para producción ni validado en workers físicos.

## Alcance
- PC-MASTER Windows permanece como panel y coordinador central.
- Los PC-WORKERS serán equipos físicos con Debian 13 como sistema base previsto.
- redroid es el único motor Android de este ciclo.
- No reabrir la vía manual QEMU + Android-x86 + VNC en WSL2.
- Agente, transporte autenticado, persistencia y reconciliación son agregados necesarios para que PC-MASTER controle los workers.

## Motor
redroid ejecuta Android en contenedores sobre un host Linux y está diseñado para varias instancias. El rendimiento real depende del kernel, los módulos/dispositivos disponibles y las aplicaciones objetivo.

Repositorio oficial: https://github.com/remote-android/redroid-doc

## Bloqueo de seguridad
La documentación oficial muestra un contenedor privilegiado y advierte contra exponer ADB públicamente. La incidencia upstream [redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) describe una escritura de `/proc/sys/kernel/modprobe` que puede afectar al host. El cierre upstream no demuestra por sí solo que exista una imagen corregida.

Antes de la prueba física:
1. Fijar etiqueta y digest concretos.
2. Inspeccionar el init de la imagen exacta y las instrucciones de kernel relevantes.
3. Identificar una mitigación efectiva y reproducible; no basta con restaurar el sysctl después.
4. Determinar capacidades, dispositivos y montajes mínimos.
5. Restringir ADB y no publicar el socket Docker al panel.
6. Verificar aislamiento y persistencia por instancia.
7. Registrar evidencia en la issue interna #27.

Mientras la puerta no esté cerrada con evidencia, no arrancar redroid en workers físicos.

## Preparación
1. Instalar Debian 13 en WORKER-01 mediante el procedimiento aprobado.
2. Ejecutar el diagnóstico de solo lectura para CPU, RAM, kernel, Binder/BinderFS, disco, red y puertos.
3. Verificar licencias y procedencia de imágenes, paquetes y APK.
4. Fijar versiones y digests; no usar `latest`.
5. Aprobar seguridad antes de iniciar el contenedor.
6. Probar una instancia: arranque, ADB restringido, APK autorizada, captura, entrada, persistencia y parada.
7. Probar dos instancias independientes y medir CPU, RAM, disco, latencia y estabilidad.
8. Integrar agente autenticado con PC-MASTER: adopción, heartbeat, capacidades, órdenes tipadas, errores y reconciliación.

## Coste y capacidad
Objetivo de coste obligatorio: 0 USD. Confirmar licencias, redistribución y dependencias. No estimar capacidad máxima hasta medirla en hardware real.

## Fuentes
- https://github.com/remote-android/redroid-doc
- https://github.com/remote-android/redroid-doc/issues/932
- https://github.com/remote-android/redroid-modules
- https://github.com/D3ckardCain/Geelark-IA/issues/27
- https://github.com/D3ckardCain/Geelark-IA/issues/24
