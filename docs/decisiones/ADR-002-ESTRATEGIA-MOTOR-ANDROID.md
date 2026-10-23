# ADR-002: Motor Android en preparación — redroid

- **Estado:** decisión de alcance para evaluación; no aprobado para producción.
- **Actualizado:** 2026-10-22.
- **Alcance:** PC-MASTER Windows y redroid en PC-WORKERS físicos con Debian 13 como sistema base previsto.
- **Coste obligatorio objetivo:** 0 USD.

## Contexto

GeeLark-IA necesita un panel web central PC-MASTER en Windows y un plano de ejecución distribuido en PCs WORKER. El motor debe permitir instancias Android independientes, ciclo de vida, persistencia, acceso visual y automatización. La referencia funcional es GeeLark, pero no se copiará código ni se dependerá de sus servicios cloud.

## Decisión de alcance

1. redroid es el único motor Android que se prepara en este ciclo.
2. No se mantendrán alternativas activas ni comparativas de otros motores Android en la documentación operativa.
3. Se retira definitivamente como ruta de producto el experimento QEMU + Android-x86 + VNC en WSL2.
4. PC-MASTER significa el panel web central; su lanzador/configurador de Windows es un componente separado.
5. Se conservan los agregados imprescindibles: agente de worker, enrolamiento, autenticación/autorización, transporte HTTPS privado, heartbeat, inventario de capacidades, persistencia transaccional, despacho durable, límites de recursos, auditoría, reconciliación, captura/entrada remota y automatización.
6. Un nodo pendiente solo puede informar telemetría y consultar estado limitado; no puede aceptar ni ejecutar tareas.
7. Debian 13 es el sistema base previsto para workers. La elección no autoriza a instalar o cambiar particiones en hardware físico hasta que exista procedimiento aprobado.
8. Coste obligatorio de software y servicios: 0 USD. Verificar licencias, condiciones de redistribución, límites y dependencias antes de adoptar cada componente.

## Bloqueo de seguridad

La documentación oficial de redroid muestra ejemplos con Docker `--privileged`. La incidencia upstream [redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) reportó que el init de Android puede escribir en `/proc/sys/kernel/modprobe` desde un contenedor privilegiado y afectar al host. Aunque la incidencia figure cerrada, el cierre no acredita que la imagen exacta que usaríamos contenga una corrección.

**No iniciar redroid en un worker físico** hasta que la issue interna [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) registre evidencia verificable de:
- versión, etiqueta y digest exactos;
- revisión del código/init de esa versión;
- mitigación probada que impida la escritura peligrosa o limite sus efectos de forma demostrable;
- privilegios, capacidades, dispositivos y montajes mínimos necesarios;
- ADB no expuesto y límites de red;
- aislamiento entre instancias y plan de recuperación.

Restaurar `kernel.modprobe` después de arrancar no es suficiente si el host ya pudo quedar afectado. Si no se consigue una mitigación demostrable, el bloqueo permanece abierto y no se despliega.

## Secuencia de validación

1. Auditoría de imagen, dependencias, licencias y seguridad.
2. Diagnóstico de solo lectura del worker: CPU, RAM, disco, kernel, Binder/BinderFS, red y puertos.
3. Instalación aprobada de Debian 13 en WORKER-01; no ejecutar esta etapa antes de cerrar la puerta de seguridad.
4. Una instancia: inicio/parada/reinicio, ADB restringido, APK autorizada, captura/entrada, red, archivos, persistencia y métricas.
5. Dos instancias: separación de datos, puertos, ADB y operación independiente.
6. Integración con PC-MASTER por agente autenticado, sin publicar Docker ni ADB como API administrativa.
7. Medición real de CPU, RAM, disco, arranque, latencia y estabilidad antes de estimar densidad.

## Fuentes

- Documentación oficial redroid: https://github.com/remote-android/redroid-doc
- Módulos de kernel redroid: https://github.com/remote-android/redroid-modules
- Incidencia upstream #932: https://github.com/remote-android/redroid-doc/issues/932
- Bloqueo interno #27: https://github.com/D3ckardCain/Geelark-IA/issues/27

## Registro de cambios

- 2026-10-22: se limita el alcance documental a PC-MASTER Windows, redroid y agregados requeridos; se retiran motores alternativos como opciones activas.
- 2026-10-22: se mantiene el bloqueo físico hasta demostrar mitigación de seguridad en la imagen exacta.