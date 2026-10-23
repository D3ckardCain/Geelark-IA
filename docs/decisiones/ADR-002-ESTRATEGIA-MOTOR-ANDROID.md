# ADR-002: Estrategia de selección del motor Android local

- **Estado:** decisión de alcance para evaluación; no aprobado para producción.
- **Actualizado:** 2026-10-23.
- **Alcance:** PC-MASTER Windows, PC-WORKERS físicos con Debian 13 previsto y adaptador Android agnóstico.
- **Coste obligatorio objetivo:** 0 USD.

## Contexto

GeeLark-IA necesita un panel web central PC-MASTER en Windows y un plano de ejecución distribuido en PCs WORKER. El motor debe permitir instancias Android independientes, ciclo de vida, persistencia, acceso visual y automatización. La referencia funcional es GeeLark, pero no se copiará código ni se dependerá de sus servicios cloud.

## Decisión de alcance

1. El contrato del motor Android permanece agnóstico.
2. redroid es el primer candidato a evaluar; todavía no está aprobado para ejecución física.
3. Android Emulator sirve como referencia de compatibilidad; revisar licencias y condiciones de imágenes antes de uso.
4. La issue #27 bloquea cualquier instalación física de redroid hasta demostrar mitigación sobre la imagen/digest exactos.
5. La ruta manual QEMU + Android-x86 + VNC en WSL2 queda retirada y no debe retomarse.
4. PC-MASTER significa el panel web central; su lanzador/configurador de Windows es un componente separado.
5. Se conservan los agregados imprescindibles: agente de worker, enrolamiento, autenticación/autorización, transporte HTTPS privado, heartbeat, inventario de capacidades, persistencia transaccional, despacho durable, límites de recursos, auditoría, reconciliación, captura/entrada remota y automatización.
6. Un nodo pendiente solo puede informar telemetría y consultar estado limitado; no puede aceptar ni ejecutar tareas.
7. Debian 13 es el sistema base previsto para workers. La elección no autoriza a instalar o cambiar particiones en hardware físico hasta que exista procedimiento aprobado.
8. Coste obligatorio de software y servicios: 0 USD. Verificar licencias, condiciones de redistribución, límites y dependencias antes de adoptar cada componente.

## Bloqueo de seguridad

La documentación oficial de redroid muestra ejemplos con Docker `--privileged`. La incidencia upstream [redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) reportó que el init de Android puede escribir en `/proc/sys/kernel/modprobe` desde un contenedor privilegiado y afectar al host. La incidencia figura cerrada como completed el 2026-08-25, sin comentarios ni parche enlazado en el hilo visible; el cierre no acredita que la imagen exacta que usaríamos contenga una corrección. La rama upstream actual de AOSP mantiene la escritura en init.rc (https://chromium.googlesource.com/aosp/platform/system/core/+/refs/heads/upstream/rootdir/init.rc); esto refuerza la necesidad de revisar el digest exacto, pero no prueba por sí solo cómo se comporta cada imagen redroid.

**No iniciar ningún motor Android en un worker físico sin aprobar su selección y puerta de seguridad. Aunque redroid es la prioridad de evaluación, no iniciarlo** hasta que la issue interna [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) registre evidencia verificable de:
- versión, etiqueta y digest exactos;
- revisión del código/init de esa versión;
- mitigación probada que impida la escritura peligrosa o limite sus efectos de forma demostrable;
- privilegios, capacidades, dispositivos y montajes mínimos necesarios;
- ADB no expuesto y límites de red;
- aislamiento entre instancias y plan de recuperación.

Restaurar `kernel.modprobe` después de arrancar no es suficiente si el host ya pudo quedar afectado. Si no se consigue una mitigación demostrable, el bloqueo permanece abierto y no se despliega.

## Secuencia de validación

1. Evaluar redroid primero: requisitos Debian/kernel/Binder, imagen/digest, privilegios, licencia, control visual, compatibilidad y densidad; resolver #27 antes de ejecutarlo en Workers físicos.
2. Diagnóstico de solo lectura del worker: CPU, RAM, disco, kernel, virtualización, red y puertos.
3. Aprobar instalación Debian 13 en WORKER-01; no modificar discos antes de aprobar el procedimiento.
4. Probar una instancia en laboratorio solo tras aprobar la puerta de seguridad y licencia del candidato.
5. Probar dos instancias y validar separación de datos, puertos, ADB y operación independiente.
6. Integrar con PC-MASTER por agente autenticado, sin publicar ADB ni interfaces privilegiadas como API administrativa.
7. Medir CPU, RAM, disco, arranque, latencia y estabilidad antes de estimar densidad.

## Fuentes

- Documentación oficial redroid: https://github.com/remote-android/redroid-doc
- Módulos de kernel redroid: https://github.com/remote-android/redroid-modules
- Incidencia upstream #932: https://github.com/remote-android/redroid-doc/issues/932
- Bloqueo interno #27: https://github.com/D3ckardCain/Geelark-IA/issues/27

## Registro de cambios

- 2026-10-22: se limita el alcance documental a PC-MASTER Windows, redroid y agregados requeridos; se retiran motores alternativos como opciones activas.
- 2026-10-22: se mantiene el bloqueo físico hasta demostrar mitigación de seguridad en la imagen exacta.