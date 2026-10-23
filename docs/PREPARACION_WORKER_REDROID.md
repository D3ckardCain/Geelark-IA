# Preparación del primer worker GeeLark-IA con redroid

**Fecha de revisión:** 2026-10-22  
**Estado:** preparación documental; NO instalado, NO probado en hardware físico y NO aprobado para producción.  
**Objetivo de coste:** 0 USD en licencias y servicios obligatorios.  
**Control central:** PC-MASTER Windows existente.  
**Primer nodo previsto:** WORKER-01, Intel Core i5-11400, 32 GB RAM, NVMe de 500 GB, sin GPU dedicada.  
**Sistema base previsto:** Debian 13 instalado directamente en el worker.

> **Bloqueo obligatorio:** no ejecutar redroid en un host físico hasta resolver la issue interna [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27). La documentación oficial de redroid usa `--privileged`; el riesgo no queda resuelto por el mero hecho de que la issue upstream esté cerrada.

## 1. Decisión de alcance

- PC-MASTER Windows permanece como panel y coordinador central.
- redroid se evalúa únicamente como motor Android local en los WORKERS.
- Debian 13 es el sistema base previsto para el worker. Se busca empaquetar y automatizar la instalación para que el usuario no tenga que administrar manualmente cada capa.
- No se reinstalará ni modificará PC-MASTER para esta prueba.
- No se reabre la ruta retirada QEMU + Android-x86 + VNC en WSL2.
- El adaptador Android de GeeLark-IA debe seguir siendo independiente del motor para no bloquear una futura sustitución.
- No se instalará software en los equipos físicos ni se cambiarán particiones/BIOS como parte de esta preparación documental.

## 2. Hallazgo de seguridad que bloquea la instalación

La guía oficial de redroid documenta una ejecución Docker con `--privileged` y advierte que ADB no debe exponerse a redes públicas. La issue upstream [remote-android/redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932) describe que el init de Android puede escribir en `/proc/sys/kernel/modprobe` desde el contenedor privilegiado, afectando al host porque ese sysctl no está aislado por namespaces. El reporte incluye redroid 14 y redroid 16.

La issue upstream aparece cerrada por quien la abrió como “completed”, pero la página consultada no documenta un commit, parche publicado ni versión corregida. Además, la fuente oficial de AOSP `platform/system/core` para `android16-qpr2-release` sigue conteniendo la escritura `write /proc/sys/kernel/modprobe \\n` en `rootdir/init.rc` (fuente: https://android.googlesource.com/platform/system/core/+/android16-qpr2-release/rootdir/init.rc). Esto confirma que la instrucción sigue presente en esa rama Android 16 consultada; no demuestra por sí solo el comportamiento de cada digest de redroid, que debe comprobarse por separado. Por tanto, **no interpretamos ese cierre como prueba de mitigación**.

### Puerta de seguridad previa a cualquier prueba

- [ ] Identificar la etiqueta, digest de imagen y versión exactos que se pretenden evaluar.
- [ ] Revisar el código AOSP/redroid de esa versión y confirmar si la escritura de `/proc/sys/kernel/modprobe` continúa presente.
- [ ] Identificar una mitigación reproducible y verificable; no depender solo de un temporizador que restaure el sysctl después de que el host ya haya sido afectado.
- [ ] Determinar qué capacidades, dispositivos, montajes y accesos necesita realmente el contenedor. No asumir que `--cap-drop` o eliminar una opción Docker por intuición bastará.
- [ ] Verificar que ADB no escucha en una interfaz pública ni queda accesible sin autenticación desde la LAN.
- [ ] Revisar aislamiento entre instancias, datos, puertos, dispositivos Binder y recursos.
- [ ] Documentar recuperación local y reversión.
- [ ] Si no puede demostrarse una mitigación aceptable, detener el despliegue físico y mantener el bloqueo abierto. No activar otra ruta técnica automáticamente.

Un laboratorio temporal dentro de una VM desechable puede considerarse para estudiar el comportamiento con una frontera de kernel separada, pero no se considera prueba de despliegue bare-metal ni sustituye la puerta de seguridad para producción.

## 3. Requisitos que debe confirmar WORKER-01

Lectura primero; no instalar paquetes hasta aprobar la puerta de seguridad.

- [ ] Modelo de CPU, núcleos/hilos y arquitectura.
- [ ] Virtualización y características de CPU relevantes.
- [ ] Versión exacta de Debian 13 y kernel.
- [ ] Disponibilidad de `binder_linux` y soporte `binderfs` en el kernel elegido.
- [ ] Compatibilidad del kernel con los módulos requeridos; no asumir que hace falta `ashmem_linux` en kernels modernos.
- [ ] Dispositivos y controlador de GPU integrada disponibles; el inventario solo confirma que no hay GPU dedicada.
- [ ] RAM libre y espacio real de NVMe.
- [ ] Reglas de firewall y dirección de escucha del servicio.
- [ ] Compatibilidad de las aplicaciones objetivo, arquitectura ABI, servicios de Google y requisitos de certificación/dispositivo.

No registrar números de serie, claves, tokens ni credenciales en logs o GitHub.

## 4. Plan de instalación reproducible (pendiente de aprobación)

1. Seleccionar y documentar una imagen de Debian 13 y un kernel compatible; registrar versión y hashes.
2. Instalar Debian directamente en WORKER-01 mediante el procedimiento de aprovisionamiento aprobado.
3. Aplicar actualizaciones de seguridad disponibles y fijar la configuración del sistema.
4. Instalar el runtime de contenedores desde una fuente oficial y documentar versión, licencia y paquetes.
5. Confirmar Binder/BinderFS y demás requisitos con pruebas de solo lectura antes de arrancar redroid.
6. Descargar una imagen redroid con etiqueta fija; verificar digest, procedencia, licencia y dependencias. No usar `latest` ni `--pull always` para una prueba reproducible.
7. No arrancar el contenedor hasta que la puerta de seguridad esté cerrada con evidencia.
8. Mantener la persistencia de Android en un directorio/volumen separado por instancia, con permisos y límites explícitos.
9. No publicar el puerto ADB en la LAN. La primera prueba deberá usar acceso local restringido; PC-MASTER hablará con el agente autenticado del worker, no con un puerto ADB abierto indiscriminadamente.
10. Registrar comandos exactos, versiones, hashes, cambios, logs redactados y resultados.
11. Repetir el procedimiento desde cero en un segundo intento para demostrar reproducibilidad.

## 5. Política de red e integración con PC-MASTER

- El worker inicia en modo pendiente/no adoptado.
- Antes de la adopción, solo puede informar heartbeat y capacidades de solo lectura; no recibe tareas Android.
- La adopción requiere autorización desde PC-MASTER.
- El agente del worker valida autenticación, autorización, esquema, límites, timeout e idempotencia.
- La API de control no ejecuta shell arbitrario ni expone el socket Docker al panel.
- ADB queda limitado a loopback o a un canal administrativo explícitamente protegido; nunca se publica a Internet.
- La pérdida de PC-MASTER no debe provocar borrado, reinicio destructivo ni duplicación de instancias.
- Cada instancia tiene ID estable, directorio persistente separado, puertos internos asignados por el agente y estado reconciliable.
- Todas las operaciones quedan registradas con resultado, actor lógico, tiempo y error redactado.

## 6. Primera prueba funcional después de aprobar seguridad

No empezar con una flota ni prometer densidad.

### Fase 1: una instancia

- [ ] Crear una instancia Android con etiqueta/digest fijados.
- [ ] Confirmar estado de arranque y recoger logs.
- [ ] Verificar que ADB solo es accesible por el canal permitido.
- [ ] Consultar versión Android, ABI y propiedades relevantes.
- [ ] Instalar una APK de prueba autorizada y no sensible.
- [ ] Abrirla, capturar pantalla y enviar entrada.
- [ ] Reiniciar la instancia y confirmar persistencia.
- [ ] Detenerla y confirmar que los recursos se liberan.
- [ ] Verificar que el host conserva el valor esperado de `kernel.modprobe` y que la carga de módulos del host sigue funcionando.
- [ ] Revisar puertos abiertos y registros de seguridad.

### Fase 2: dos instancias

Solo si Fase 1 pasa:

- [ ] Datos, IDs, puertos y estado separados.
- [ ] Detener/reiniciar una instancia sin afectar a la otra.
- [ ] ADB y captura/control independientes.
- [ ] Persistencia independiente tras reinicio.
- [ ] Prueba de presión de recursos y estabilidad.
- [ ] Registro de CPU, RAM, disco, tiempo de arranque, latencia y errores.

### Fase 3: integración

- [ ] El worker se registra y reporta capacidades a PC-MASTER.
- [ ] Un worker pendiente no acepta tareas.
- [ ] PC-MASTER solicita una operación tipada y el worker la valida.
- [ ] Estado, errores y eventos regresan al panel.
- [ ] Desconexión/reconexión sin duplicar tareas ni instancias.

## 7. Medición y criterios de aprobación

No se estimará el número máximo de instancias sin medirlo en el i5-11400 con 32 GB de RAM y sin GPU dedicada.

Registrar para 1 y luego 2 instancias:
- uso de CPU medio/pico;
- RAM del host y por instancia;
- almacenamiento consumido y crecimiento;
- tiempo hasta Android listo;
- latencia de captura/entrada;
- estabilidad y reinicios;
- compatibilidad con las APK objetivo;
- estado de seguridad del kernel y puertos.

Aprobación de la prueba solo si:
1. La puerta de seguridad tiene evidencia verificable.
2. No hay ADB expuesto indebidamente.
3. El host mantiene su funcionamiento normal.
4. Las instancias se aíslan y persisten de forma independiente.
5. Las operaciones básicas funcionan de forma repetible.
6. El coste obligatorio continúa en 0 USD.
7. Los resultados y fallos quedan documentados.

## 8. Distribución local y coste

La conexión a Internet disponible es 10/10 Mbps. Para evitar descargar repetidamente imágenes grandes:
- descargar una vez por versión;
- validar digest y licencia;
- almacenar en una caché local controlada;
- distribuir por LAN a los workers;
- mantener manifiesto de versiones, hashes y fecha;
- no redistribuir imágenes o APK sin verificar sus términos;
- no actualizar automáticamente a `latest`.

## 9. Fuentes primarias consultadas

- Documentación oficial y ejecución de redroid: https://github.com/remote-android/redroid-doc
- Despliegue en Debian: https://github.com/remote-android/redroid-doc/blob/master/deploy/debian.md
- Incidencia upstream sobre `kernel.modprobe`: https://github.com/remote-android/redroid-doc/issues/932
- Módulos de kernel redroid y requisitos: https://github.com/remote-android/redroid-modules
- Bloqueo interno: https://github.com/D3ckardCain/Geelark-IA/issues/27
- Selección de motores: https://github.com/D3ckardCain/Geelark-IA/issues/8
- Contrato agnóstico del motor: https://github.com/D3ckardCain/Geelark-IA/issues/12
- Inventario y aprovisionamiento de workers: https://github.com/D3ckardCain/Geelark-IA/issues/24

## 10. Registro de estado

- Documentación preparada en rama de trabajo; no fusionada.
- No se ha instalado redroid ni software en los equipos físicos.
- No se ha modificado PC-MASTER, BIOS, particiones, Supabase ni los discos de los workers.
- No se declara redroid aprobado ni se declara resuelta la issue #27.
- Próximo paso: completar evidencia de la puerta de seguridad y preparar la matriz de comandos de solo lectura para Debian 13; solo después decidir si se autoriza el primer despliegue.
