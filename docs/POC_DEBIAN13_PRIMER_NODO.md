# POC inicial: Debian 13 Stable en un nodo GeeLark-IA

**Estado:** preparación documental; no ejecutada.  
**Objetivo:** validar un solo nodo antes de incorporar workers al clúster.  
**Coste obligatorio:** 0 USD. No usar pruebas temporales, suscripciones ni APIs de pago.  
**Proxmox VE:** se conserva como alternativa para una fase posterior; este documento no lo descarta.  
**Límite de autorización:** leer este documento no autoriza instalar Debian, borrar discos, modificar BIOS/UEFI ni alterar hardware.

## 1. Alcance de esta primera prueba

La primera POC valida un único equipo y no habilita la ejecución distribuida de tareas. Hasta superar las pruebas de seguridad, el nodo debe operar en modo restringido:

- Puede anunciar heartbeat, capacidades y consultar su estado.
- No puede aceptar tareas ni ejecutar operaciones de automatización.
- No puede abrir ADB en la LAN general ni en Internet.
- La desconexión no puede provocar duplicación de instancias o repetición de operaciones de resultado incierto.
- El control y los registros del proyecto deben seguir siendo portables y no depender de APIs de Proxmox.

No migrar los cuatro equipos simultáneamente. El resto de las PCs debe permanecer sin cambios durante esta primera POC.

## 2. Puerta de autorización

Antes de una instalación, deben constar en la issue asociada:

1. Alias exacto del equipo de prueba y confirmación física del modelo.
2. Confirmación de que el usuario autoriza instalar Debian 13 en ese equipo concreto.
3. Confirmación explícita de si se permite borrar el disco; no asumirlo.
4. Copia de seguridad verificada si existe cualquier dato que conservar.
5. Método de recuperación probado o procedimiento de reinstalación aceptado.
6. Acceso a otro equipo para descargar/verificar artefactos y crear el medio de instalación.
7. ISO obtenida de la fuente oficial, versión exacta registrada y firma/checksum verificado.
8. Licencias revisadas para el SO, motor Android, imagen, aplicaciones y artefactos.
9. Plan de red aislada y control de acceso local.
10. Criterios de éxito y procedimiento de abortar la prueba.

Si falta cualquiera de los puntos aplicables, la instalación permanece bloqueada.

## 3. Inventario previo de solo lectura

Usar primero la [guía de inventario del equipo](GUIA_INVENTARIO_EQUIPO.md) y la [hoja de ejecución de la POC](HOJA_EJECUCION_POC_HOST_CLUSTER.md). Registrar como mínimo:

- CPU exacta y arquitectura.
- RAM total.
- Modelo, tipo y capacidad de disco.
- GPU integrada, controlador y soporte gráfico observado.
- Firmware/BIOS y disponibilidad de VT-x/VT-d si aplica.
- Interfaces de red y velocidad negociada.
- Estado del equipo, periféricos y método de acceso físico.
- Qué datos o instalaciones se perderían si se autorizara borrar el disco.

No publicar números de serie, UUID de discos, direcciones MAC, IP pública, claves, tokens ni nombres de usuario.

## 4. Instalación propuesta (no ejecutar hasta autorización)

Cuando exista autorización específica:

1. Descargar Debian 13 Stable únicamente desde el sitio oficial de Debian.
2. Verificar la firma criptográfica del artefacto usando la documentación oficial; registrar el archivo, versión, hash y resultado. No basta con que la descarga termine sin error.
3. Preparar un medio de instalación con un procedimiento documentado y revisar dos veces el dispositivo destino para evitar escribir sobre un disco equivocado.
4. Confirmar por última vez el equipo y el alcance autorizado antes de particionar o instalar.
5. Instalar una configuración mínima, sin entorno o servicios que no hagan falta para la POC.
6. Configurar un usuario administrativo seguro, actualizaciones de seguridad desde repositorios oficiales y acceso de red limitado.
7. No abrir ADB ni la API de control a redes no confiables.
8. Registrar versiones y configuración sin secretos.
9. Antes de instalar el motor Android, verificar la compatibilidad del kernel con binder/binderfs y los requisitos exactos del motor seleccionado.
10. Crear una referencia reproducible de la configuración y un plan de restauración antes de ejecutar cargas.

No fijar ahora un esquema de particiones, cifrado o arranque definitivo sin conocer el equipo, el método de recuperación y la autorización. No ejecutar comandos de instalación o borrado desde esta guía.

## 5. Selección del motor Android

La selección del motor es una puerta independiente. Comparar al menos la compatibilidad y las condiciones de uso de:

- Android Emulator oficial como referencia de compatibilidad.
- redroid como candidato para ejecución multiinstancia en Linux, condicionado a verificar kernel, binder/binderfs, privilegios, aceleración gráfica y licencias de todos los componentes.

No asumir que una imagen de Android incluye derechos para redistribuir Google Mobile Services, aplicaciones comerciales u otros componentes propietarios. Usar una APK de prueba autorizada y no subir imágenes/APK sin permiso.

No ejecutar contenedores privilegiados sin una evaluación de riesgo documentada. Si el modelo de seguridad del motor exige privilegios excesivos, detener la prueba y documentar la alternativa.

## 6. Red, ADB y comportamiento del agente

- Mantener el control administrativo en una interfaz local o red de gestión aislada.
- ADB solo debe escuchar en loopback o en una interfaz de prueba expresamente aislada.
- Probar desde otro equipo no autorizado que ADB no sea accesible.
- No exponer la API administrativa a Internet.
- Aplicar lista permitida de operaciones en el agente.
- Un nodo pendiente puede enviar heartbeat, capacidades y consultar estado; no aceptar tareas ni ejecutar operaciones.
- Ante pérdida de conexión, conservar el estado de las ejecuciones y reconciliarlo antes de reanudar. No repetir automáticamente acciones cuyo resultado sea incierto.
- Registrar eventos de forma local y sincronizarlos cuando vuelva la conectividad, con identificadores únicos e idempotencia.

## 7. Pruebas de aceptación

La POC no se considera aprobada solo porque el sistema arranque.

- [ ] Arranque reproducible tras tres reinicios.
- [ ] Actualización de seguridad documentada y sin suscripción obligatoria.
- [ ] Motor Android compatible con la versión exacta del kernel.
- [ ] Captura de pantalla y acciones de prueba autorizadas.
- [ ] CPU/RAM medidas en reposo y bajo carga.
- [ ] GPU y renderer identificados; no asumir aceleración.
- [ ] ADB inaccesible desde interfaces no autorizadas.
- [ ] Sin acceso cruzado entre instancias/datos.
- [ ] Persistencia comprobada tras reinicio.
- [ ] Backup y restauración probados.
- [ ] Arranque y funciones locales probadas sin WAN.
- [ ] Heartbeat/capacidades/estado funcionan en modo restringido.
- [ ] No se aceptan tareas ni ejecutan operaciones mientras el nodo siga pendiente.
- [ ] Desconexión/reconexión no duplica tareas ni efectos.
- [ ] Coste obligatorio real: 0 USD.
- [ ] Incidentes, comandos, versiones y resultados registrados en GitHub.

Los umbrales de rendimiento deben definirse según el objetivo funcional confirmado; no inventar capacidad de instancias antes de medir.

## 8. Plan de reversión

Antes de la prueba, registrar:
- Método para volver al estado previo.
- Medio de instalación y controladores necesarios, obtenidos de fuentes oficiales.
- Copia de datos si corresponde.
- Procedimiento para recuperar acceso local y red.
- Criterios de parada inmediata (pérdida de acceso, datos inesperados, exposición de ADB, coste obligatorio o incompatibilidad crítica).
- Responsable y confirmación de que la reversión es viable.

La restauración debe probarse antes de usar el nodo con datos o cargas relevantes.

## 9. Registro de resultados

Vincular esta POC a una issue de GitHub y registrar cada intento con fecha, alias del host, versión exacta, comandos, logs redactados, métricas, hashes, incidentes, solución y repetición. No guardar credenciales ni datos personales en issues o commits.

## 10. Fase posterior: Proxmox VE

Proxmox queda pendiente deliberadamente. Cuando el usuario solicite esa fase, crear una prueba separada y comparable con VM Linux dedicada. Medir recursos consumidos por el hipervisor/VM, rendimiento del motor, acceso a iGPU, aislamiento, backup/restore y política de actualizaciones sin suscripción obligatoria. No convertir los equipos en un clúster Proxmox ni modificar los otros nodos sin autorización específica.
