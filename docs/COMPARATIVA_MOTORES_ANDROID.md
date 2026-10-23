# Comparativa y priorización de motores Android locales

**Actualizado:** 2026-10-23. **Estado:** investigación documental; ningún motor está aprobado para producción ni validado en WORKERS físicos.

## Alcance vigente

- PC-MASTER Windows es el panel web y coordinador central.
- Los PC-WORKERS serán equipos físicos; Debian 13 es el sistema base previsto.
- AOSP Cuttlefish es el primer candidato para laboratorio, no aprobado. Android Emulator se conserva como referencia de compatibilidad. redroid está bloqueado por la issue #27 y Waydroid permanece como alternativa secundaria no validada.
- No reabrir rutas de ejecución retiradas; mantener únicamente el alcance técnico vigente.
- Agente, autenticación, transporte, persistencia, despacho y reconciliación son componentes del plano de control, no motores Android alternativos.

## Candidato prioritario: AOSP Cuttlefish

Cuttlefish es el primer candidato que se evaluará por su soporte de múltiples instancias, discos overlay por instancia, puertos ADB separados y control visual mediante WebRTC. Esto no implica que sea ligero ni adecuado para los WORKERS disponibles. Requiere validar KVM, paquetes/servicios de host, imágenes, licencias, uso de memoria/CPU y el flujo de instalación. Comenzar con un entorno de laboratorio y una instancia; medir antes de ampliar.

Fuentes oficiales: https://source.android.com/docs/devices/cuttlefish/get-started ; https://source.android.com/docs/devices/cuttlefish/multi-tenancy ; https://source.android.com/docs/setup/create/cuttlefish-ref-webrtc

## redroid: alternativa bloqueada por seguridad

redroid ejecuta Android en contenedores sobre un host Linux y documenta soporte para arquitecturas amd64 y arm64 y varias instancias. La densidad y compatibilidad reales dependen del kernel, Binder/BinderFS, recursos, aplicaciones objetivo y configuración. Ninguna cifra de capacidad se considera validada para nuestro hardware.

La documentación pública oficial consultada enumera imágenes hasta Android 16; no asumir soporte oficial de versiones superiores sin una etiqueta publicada y verificable. La frescura de una etiqueta y el digest deben comprobarse antes de seleccionarla.

Documentación oficial: https://github.com/remote-android/redroid-doc  
Módulos del kernel: https://github.com/remote-android/redroid-modules  
Imagen pública: https://hub.docker.com/r/redroid/redroid

## Bloqueo crítico de seguridad

La guía upstream muestra ejemplos con Docker `--privileged`. La incidencia [redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) describe una escritura de `/proc/sys/kernel/modprobe` que puede escapar al host debido a que el sysctl no está aislado por namespaces. La incidencia aparece cerrada como completed el 2026-08-25 y no tiene comentarios ni un parche enlazado en su hilo visible; eso no prueba que una etiqueta/digest concreta tenga una corrección. La rama upstream actual de AOSP también conserva la escritura en init.rc: https://chromium.googlesource.com/aosp/platform/system/core/+/refs/heads/upstream/rootdir/init.rc. Esta fuente confirma que la instrucción sigue presente en AOSP, no el comportamiento de cada imagen redroid concreta.

No ejecutar redroid en hardware físico hasta que la issue interna [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) contenga evidencia verificable de la mitigación sobre la imagen exacta. No basta con restaurar el valor del sysctl después del arranque. Si no se encuentra una mitigación efectiva, detener el despliegue físico.

## Lista de verificación previa

- [ ] Elegir una etiqueta fija y registrar digest; no usar `latest` en pruebas reproducibles.
- [ ] Inspeccionar init y parches de la versión exacta.
- [ ] Probar una mitigación efectiva del riesgo `kernel.modprobe`.
- [ ] Determinar privilegios, capacidades, dispositivos y montajes mínimos.
- [ ] Mantener ADB en loopback o canal administrativo explícitamente protegido.
- [ ] No exponer el socket Docker a PC-MASTER ni a la LAN.
- [ ] Verificar Binder/BinderFS y módulos requeridos en el kernel real.
- [ ] Revisar licencias y condiciones de distribución de imagen, módulos y dependencias.
- [ ] Documentar recuperación, logs redactados y reversión.
- [ ] Obtener aprobación de la puerta #27 antes de arrancar en WORKER físico.

## Compatibilidad ABI: riesgo adicional conocido

La incidencia upstream [redroid-doc #933](https://github.com/remote-android/redroid-doc/issues/933) reporta que ciertas imágenes x86_64 pueden anunciar arm64-v8a aunque la biblioteca de traducción nativa no esté disponible; una APK ARM-only podría instalarse y fallar al arrancar. El reporte está abierto y no demuestra que todas las etiquetas estén afectadas.

Por ello, la imagen se elegirá a partir de las APK objetivo y se probará por etiqueta/digest exactos. La lista ABI declarada no basta para afirmar compatibilidad. No redistribuir traductores propietarios ni extraerlos de otros productos sin revisar sus términos. Este riesgo de compatibilidad es independiente del bloqueo de seguridad #27.

## Plan de pruebas después de aprobar selección y seguridad

1. Diagnóstico de solo lectura en WORKER-01 (CPU, RAM, kernel, disco, Binder/BinderFS, red y puertos).
2. Instancia única: ciclo de vida, ADB restringido, APK autorizada, captura/entrada, archivos, persistencia y métricas.
3. Dos instancias simultáneas: independencia de datos, puertos, almacenamiento y control.
4. Reinicios y fallos: recuperación, reconciliación y ausencia de operaciones duplicadas.
5. Integración por agente autenticado con PC-MASTER Windows.
6. Medición de CPU, RAM, almacenamiento, latencia y estabilidad antes de cualquier estimación de escala.

## Capacidad y coste

El hardware de referencia inicial de cada worker es i5-11400, 32 GB de RAM, NVMe de 500 GB y sin GPU dedicada. Esto no determina cuántas instancias son viables. Medir primero una y dos; ampliar solo con datos observados.

Objetivo obligatorio: 0 USD. Verificar cada dependencia y su licencia; no depender de un servicio cloud pagado.