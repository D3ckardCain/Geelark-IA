# Evaluación del motor Android en preparación: redroid

**Actualizado:** 2026-10-22. **Estado:** preparación documental; bloqueado para despliegue físico por la issue #27. No aprobado para producción ni validado en WORKERS físicos.

## Alcance vigente

- PC-MASTER Windows es el panel web y coordinador central.
- Los PC-WORKERS serán equipos físicos; Debian 13 es el sistema base previsto.
- redroid es el único motor Android en preparación.
- No reabrir QEMU + Android-x86 + VNC en WSL2 ni mantener otros motores como alternativas activas.
- Agente, autenticación, transporte, persistencia, despacho y reconciliación son componentes del plano de control, no motores Android alternativos.

## Qué ofrece redroid

redroid ejecuta Android en contenedores sobre un host Linux y documenta soporte para arquitecturas amd64 y arm64 y varias instancias. La densidad y compatibilidad reales dependen del kernel, Binder/BinderFS, recursos, aplicaciones objetivo y configuración. Ninguna cifra de capacidad se considera validada para nuestro hardware.

Documentación oficial: https://github.com/remote-android/redroid-doc  
Módulos del kernel: https://github.com/remote-android/redroid-modules  
Imagen pública: https://hub.docker.com/r/redroid/redroid

## Bloqueo crítico de seguridad

La guía upstream muestra ejemplos con Docker `--privileged`. La incidencia [redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) describe una escritura de `/proc/sys/kernel/modprobe` que puede escapar al host debido a que el sysctl no está aislado por namespaces. La incidencia aparece cerrada, pero eso no prueba que una etiqueta/digest concreta tenga una corrección.

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

## Plan de pruebas después de aprobar seguridad

1. Diagnóstico de solo lectura en WORKER-01 (CPU, RAM, kernel, disco, Binder/BinderFS, red y puertos).
2. Instancia única: ciclo de vida, ADB restringido, APK autorizada, captura/entrada, archivos, persistencia y métricas.
3. Dos instancias simultáneas: independencia de datos, puertos, almacenamiento y control.
4. Reinicios y fallos: recuperación, reconciliación y ausencia de operaciones duplicadas.
5. Integración por agente autenticado con PC-MASTER Windows.
6. Medición de CPU, RAM, almacenamiento, latencia y estabilidad antes de cualquier estimación de escala.

## Capacidad y coste

El hardware de referencia inicial de cada worker es i5-11400, 32 GB de RAM, NVMe de 500 GB y sin GPU dedicada. Esto no determina cuántas instancias son viables. Medir primero una y dos; ampliar solo con datos observados.

Objetivo obligatorio: 0 USD. Verificar cada dependencia y su licencia; no depender de un servicio cloud pagado.