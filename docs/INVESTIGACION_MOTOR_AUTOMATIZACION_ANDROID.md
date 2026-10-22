# Investigación ampliada: plataforma Android y automatización para GeeLark-IA

**Fecha de revisión:** 2026-10-21  
**Estado:** investigación documental; no se ha instalado ni validado ningún candidato en WORKERS físicos.  
**Objetivo del producto:** construir una alternativa local, administrable y automatizable inspirada en las funciones públicas de GeeLark, empezando por instancias Android independientes, su ciclo de vida y automatización.  
**Restricción obligatoria:** 0 USD en licencias/servicios obligatorios; sin tarjeta, pruebas temporales, cargos automáticos ni servicios cloud pagados como dependencia crítica.

## 1. Decisión de alcance: vía anterior retirada

Se descarta como ruta de producto el prototipo manual **QEMU + Android-x86 9.0-r2 + VNC** probado en WSL2. No se continuará depurando su pantalla negra ni se construirá la arquitectura de GeeLark-IA sobre esa ISO.

Razones documentadas:
- Android-x86 9.0-r2 es una imagen antigua; el éxito de arranque no demuestra mantenimiento, compatibilidad con apps actuales, aislamiento, automatización o escalabilidad.
- La experiencia gráfica VNC no fue estable y consumió tiempo sin validar el requisito central de una plataforma multiinstancia administrable.
- WSL2 es un entorno auxiliar, no el host de producción Debian 13 de los WORKERS.
- El prototipo no demuestra paridad funcional con GeeLark ni una vía fiable para aprovisionamiento, operación desatendida o automatización.

Esta retirada es una decisión de proyecto; no significa que se haya borrado software de la distribución Debian13 de WSL. No se harán limpiezas destructivas del entorno local como parte de esta investigación documental.

## 2. Qué debemos reproducir de GeeLark

Las páginas públicas de GeeLark describen, entre otras, estas capacidades:
- Perfiles de teléfonos Android independientes, creación, inicio/parada, actualización, clonación y agrupación.
- Acceso remoto a la pantalla y controles del dispositivo.
- Aplicaciones, archivos, Library y operaciones por lotes.
- Automatización por plantillas; constructor visual RPA con acciones, condiciones, bucles, variables y parámetros.
- Synchronizer: repetir/multiplicar acciones en vivo hacia dispositivos seleccionados.
- API programática, ADB en entornos compatibles, consulta de tareas, cancelación/reintento y Webhooks.
- Registros y estado de operaciones, usuarios/permisos y configuración de proxies.

Fuentes oficiales de GeeLark:
- https://www.geelark.com/product/cloud-phone/
- https://www.geelark.com/features/automation/
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/features/api/
- https://github.com/GeeLark/geelark-openapi

La edición gratuita de GeeLark no es una alternativa para cumplir el coste total del proyecto: la página oficial limita perfiles/minutos y el uso de teléfonos cloud cuesta por minuto; la automatización/API y otras capacidades dependen del plan. Se usa solo como referencia funcional, no como infraestructura.

## 3. Candidatos de motor Android

### A. AOSP Cuttlefish — primera prueba recomendada

**Tipo:** plataforma oficial AOSP para dispositivos Android virtuales en hosts Linux.  
**Multiinstancia:** documentada expresamente; `cvd create --num_instances=N` lanza varios dispositivos desde una imagen, con discos overlay copy-on-write por instancia y puertos ADB diferentes. La documentación indica que el paquete base configura por defecto recursos host para instancias 1–10, ampliables con configuración del host.  
**Acceso/control:** ofrece transmisión WebRTC desde navegador, con control remoto y ADB en navegador; la documentación afirma que la codificación es más eficiente que VNC.  
**Ventajas:** Android virtual real, ciclo de vida por herramientas propias, multiinstancia documentada, separación de datos por overlay, integración ADB y camino para control remoto sin desarrollar el visor primero.  
**Riesgos y pruebas pendientes:** requiere host Linux compatible, KVM, imágenes de dispositivo Cuttlefish compatibles y dependencias específicas. No asumir Google Play/Play Services, ABI ARM, cámara/sensores equivalentes ni compatibilidad universal de apps. Validar la versión exacta, licencias de imagen y forma de distribución.  
**Licencia:** repositorio principal Apache-2.0, pero revisar las licencias de componentes, artefactos e imágenes que se vayan a usar; el nombre de una licencia del repositorio no concede automáticamente derechos sobre todo el contenido distribuido.

Fuentes:
- https://source.android.com/docs/devices/cuttlefish
- https://source.android.com/docs/devices/cuttlefish/multi-tenancy
- https://source.android.com/docs/devices/cuttlefish/get-started
- https://source.android.com/docs/devices/cuttlefish/on-premises (solo para distinguir la vía Orchestrator; no se asume como dependencia local)
- https://source.android.com/docs/setup/create/cuttlefish-ref-webrtc
- https://github.com/google/android-cuttlefish
- https://github.com/google/android-cuttlefish/blob/main/LICENSE

**Coste de instalación/operación técnica:** la guía oficial no es simplemente instalar una app de escritorio: requiere preparar paquetes Debian del host (compilarlos o instalarlos desde el repositorio oficial), pertenencia a grupos KVM/red/render, módulos/reglas del sistema y reinicio del host. Las imágenes de dispositivo se descargan por separado desde Android Continuous Integration. Esto es gratuito en software, pero añade mantenimiento y debe automatizarse con cuidado en el aprovisionamiento. No se requiere usar Google Cloud/Cloud Orchestrator para la prueba local por WORKER; la guía de servidor on-premise que usa Orchestrator es una vía distinta y no será una dependencia obligatoria.

La documentación oficial también advierte que los recursos dependen del perfil y la carga: su ejemplo de 40 instancias con 4 CPU y 8 GB RAM por instancia requiere 160 núcleos y 320 GB RAM. Es un ejemplo de configuración, no un mínimo universal, pero deja claro que no debemos inferir densidad por el mero soporte multiinstancia. En nuestros WORKERS de 6 núcleos/32 GB, habrá que medir perfiles mucho más modestos y comprobar si las aplicaciones objetivo funcionan con ellos.

**Evaluación:** primera opción para una prueba controlada de una y dos instancias, porque ya documenta multiinstancia y control web. No es todavía el motor aprobado.

### B. redroid — posible alta densidad, bloqueado por seguridad

**Tipo:** Android en contenedores Linux, orientado a instancias remotas y aceleración gráfica.  
**Ventajas:** arquitectura potencialmente ligera; imágenes multi-arquitectura y distintas versiones; ADB y control de pantalla con herramientas externas como scrcpy.  
**Requisitos:** funciones de kernel como binderfs, ashmem/memfd, IPv6, DMA-BUF/ION o heaps equivalentes y tamaño de página de 4 KB, según la documentación de despliegue. La compatibilidad debe verificarse en el kernel exacto de Debian 13.  
**Riesgo bloqueante:** el ejemplo oficial usa `--privileged`, publica ADB y advierte que ADB no debe exponerse en redes públicas. El proyecto interno mantiene abierta la issue #27 por una investigación de seguridad upstream relacionada con la modificación de `/proc/sys/kernel/modprobe` desde un contenedor privilegiado. No ejecutar en PC-MASTER ni en un host productivo mientras no se confirme mitigación para la versión exacta y un modelo de aislamiento aceptable.  
**Licencia:** redroid declara Apache-2.0 para el proyecto y GPL-2.0 para sus módulos de kernel, pero señala que hay que revisar componentes de terceros e imágenes.

Fuentes:
- https://github.com/remote-android/redroid-doc
- https://github.com/remote-android/redroid-doc/blob/master/deploy/README.md
- https://github.com/remote-android/redroid-modules
- https://github.com/remote-android/redroid-doc/issues/932
- Bloqueo interno: https://github.com/D3ckardCain/Geelark-IA/issues/27

**Evaluación:** mantener como candidato de investigación; no hacer prueba física hasta resolver la issue #27 y diseñar aislamiento/puertos con privilegios mínimos.

### C. Android Emulator oficial — referencia de compatibilidad, no decisión de producto

**Tipo:** emulador oficial del SDK Android; AVD, CLI, ADB y aceleración KVM en Linux. Algunas imágenes incluyen Google Play.  
**Ventajas:** herramientas maduras para arrancar dispositivos, instalar APK, probar versiones Android y automatizar UI. Es un buen punto de comparación para compatibilidad y depuración.  
**Limitaciones:** consume recursos por AVD y está orientado principalmente a desarrollo/pruebas; no se debe asumir densidad ni equivalencia con GeeLark. El SDK, los binarios, las imágenes y las imágenes Google Play tienen términos distintos que deben revisarse antes de redistribuirlos o integrarlos en un producto.

La variante oficial en contenedores es una opción técnica separada que merece un experimento documental: el repositorio proporciona contenedores con `/dev/kvm`, ADB por puerto, gRPC/WebRTC y una demo React para control desde navegador. Algunas imágenes son publicadas en Google Artifact Registry, pero depender de ese registro no es lo mismo que tener una solución completamente local/offline; se debe fijar versión, revisar condiciones de SDK y avisos de imagen, comprobar telemetría y preparar caché/redistribución local solo si la licencia lo permite. El proyecto declara explícitamente que esta función en contenedores es experimental. Docker Desktop en Windows no sirve para esta aceleración; el destino previsto es Debian físico.  
**Licencia/coste:** no tratar “descarga gratuita” como permiso ilimitado para redistribuir imágenes o incluirlo en un producto. Revisar los términos exactos para el uso planeado; no usar servicios de pago ni suscripciones.

Fuentes:
- https://developer.android.com/studio/run/emulator-commandline
- https://developer.android.com/studio/run/emulator-acceleration
- https://developer.android.com/studio/terms
- https://github.com/google/android-emulator-container-scripts

**Evaluación:** conservar como referencia separada para pruebas de compatibilidad, no volver al prototipo manual QEMU + Android-x86. La variante en contenedores es experimental y no debe ser la base inicial del producto.

### D. Waydroid — alternativa secundaria de contenedor

**Tipo:** Android integrado en escritorio Linux/Wayland mediante contenedores y funciones del kernel.  
**Ventajas:** software libre y buen encaje para aplicaciones Android en un escritorio Linux; puede ser útil para explorar compatibilidad y control.  
**Limitaciones:** su orientación es integración de escritorio, no un clúster de muchos dispositivos independientes headless. No hay evidencia suficiente de multiinstancia independiente, asignación por recursos y control remoto por instancia para nuestros requisitos.  
**Evaluación:** mantener como opción secundaria; no empezar por aquí.

Fuentes:
- https://waydro.id/
- https://docs.waydro.id/
- https://github.com/waydroid/waydroid

### E. Android-x86 / Bliss OS con QEMU manual — retirado

No se considera candidato para el producto ni se invertirá más tiempo en el prototipo Android-x86 9.0-r2/VNC. No se usará para comparar densidad ni para diseñar la automatización. Cualquier reentrada requeriría una nueva decisión explícita y evidencia que justifique reabrir la vía; no forma parte del plan actual.

### F. Genymotion Desktop gratuito — descartado por condiciones

La modalidad gratuita de escritorio es para uso personal, excluye el uso profesional/comercial y prohíbe instalar en servidores o usar automatización/no-manual testing bajo esa modalidad. Las opciones profesionales requieren licencia pagada. No satisface el requisito del proyecto.

Fuentes:
- https://www.genymotion.com/legal-terms-and-conditions/
- https://www.genymotion.com/pricing/

### G. Anbox clásico — descartado por mantenimiento

El repositorio original está archivado; no iniciar una nueva integración basándose en él.
Fuente: https://github.com/anbox/anbox

## 4. Comparación ejecutiva

| Candidato | Multiinstancia documentada | Control remoto | Android/ADB | Riesgo principal | Prioridad |
|---|---|---|---|---|---|
| Cuttlefish | Sí, explícita | WebRTC en navegador | ADB por instancia | Host/imagen/licencia y compatibilidad de apps | 1 |
| redroid | Sí, objetivo del proyecto | ADB + scrcpy u otra capa | Sí | Contenedor privilegiado, kernel y aislamiento | 2, bloqueado |
| Android Emulator oficial | AVD independientes | Herramientas de emulador; contenedor WebRTC experimental | Sí | Condiciones de SDK/imágenes y densidad | Referencia |
| Waydroid | No demostrada para nuestra topología | Integración de escritorio; remoto por diseñar | Depende de configuración | Multiinstancia/headless | 3 |
| Android-x86 + QEMU manual | Una VM por instancia es posible | El prototipo VNC falló | Parcial | Mantenimiento/UX y ruta no validada | Retirado |
| Genymotion Desktop gratis | No apto para uso profesional/servidor automatizado | Variable | Sí | Licencia/coste | Descartado |
| Anbox clásico | No se recomienda | — | — | Repositorio archivado | Descartado |

Las capacidades anteriores provienen de documentación pública, no de pruebas en nuestro hardware. “Multiinstancia documentada” no significa que 50 instancias quepan en tres WORKERS.

## 5. Automatización: qué componentes necesitamos

GeeLark combina plantillas, RPA visual, Synchronizer y API/Webhooks. No existe una única herramienta libre que replique automáticamente todo ese producto. La estrategia viable es construir una capa propia encima de un motor Android intercambiable.

### A. Ejecución y control de UI

- **ADB/platform-tools:** ciclo de vida de conexión, instalación de APK, archivos, capturas y comandos permitidos; solo mediante un adaptador interno con lista permitida, timeouts, límites y auditoría. No publicar ADB en Internet ni ofrecer una consola shell arbitraria.
- **Appium + UiAutomator2:** candidato para automatización estructurada de apps Android mediante selectores/UI y protocolo WebDriver. Licencia del driver UiAutomator2: Apache-2.0. Requiere probar versión de Appium/driver y compatibilidad con la imagen Android elegida.
- **UI Automator oficial:** API de Android para pruebas e interacción con apps/sistema; buena referencia para acciones y árbol semántico, pero la integración como servicio multiinstancia necesita desarrollo propio.
- **scrcpy:** visor/controlador libre de pantalla mediante ADB, multiplataforma, sin cuenta ni servicio cloud; útil para una consola de operador y depuración, no crea instancias ni es el motor RPA completo.
- **Maestro:** framework abierto de automatización UI declarativa mediante YAML. Evaluar como herramienta auxiliar para pruebas y flujos; verificar licencia exacta, compatibilidad, concurrencia y capacidades antes de integrarlo en el producto.
- **DeviceFarmer STF:** proyecto de gestión de una granja de dispositivos Android con acceso por navegador. Puede servir como referencia de consola/dispositivo, pero no crea por sí solo instancias Android virtuales; la documentación del contenedor advierte que el proyecto tiene carga de hardware alta y carencias de seguridad/aislamiento entre usuarios. No adoptarlo como plano de control de GeeLark-IA sin una auditoría y endurecimiento; en principio no cubre nuestro requisito principal de motor de emulación.

Fuentes:
- https://developer.android.com/tools/adb
- https://developer.android.com/training/testing/other-components/ui-automator
- https://github.com/appium/appium-uiautomator2-driver
- https://github.com/Genymobile/scrcpy
- https://docs.maestro.dev/get-started/what-is-maestro
- https://github.com/DeviceFarmer/stf (referencia de gestión de dispositivos, no motor de emulación; revisar seguridad y estado actual)

### B. Componentes propios que replican el producto

1. **Instance Manager:** adaptador por motor para crear/iniciar/detener/reiniciar/eliminar; consultar estado; instalar app; obtener captura; gestionar archivos y persistencia.
2. **Profile Manager:** metadatos, grupos, configuración de instancia, versión de Android, imagen, red/proxy, aplicaciones y permisos; los datos de perfil deben separarse de los datos internos de Android.
3. **RPA Builder:** editor visual propio de pasos tipados: lanzar app, esperar, buscar elemento, tocar, escribir, deslizar, condición, bucle acotado, variable, captura, transferencia de archivo, resultado y manejo de error.
4. **RPA Runner:** cola persistente, máquina de estados por tarea/paso, timeouts, cancelación, pausa/reanudación donde sea seguro, límite de iteraciones, reintentos solo para acciones idempotentes y resultado por instancia.
5. **Synchronizer:** no replicar ciegamente coordenadas. Capturar eventos de alto nivel en la instancia maestra y traducirlos a cada destino; validar resolución, orientación, app/versión y presencia del elemento; mostrar errores parciales por destino. Coordenadas brutas solo como modo explícito con límites.
6. **API local + Webhooks/eventos:** operaciones tipadas, autenticación, autorización, idempotencia, límites de tasa y resultados consultables; eventos locales para UI y agente de nodo.
7. **Plantillas y Library:** flujos versionados, importación/exportación JSON validada, APK/archivos con checksum y límites de tamaño.
8. **Logs/auditoría:** registrar quién, qué perfil/instancia, tarea, paso, resultado, tiempos y error saneado; nunca secretos, tokens o datos personales por defecto.
9. **Control de recursos:** cada motor anuncia capacidades y coste medido de RAM/CPU/disco; el planificador asigna instancias a WORKERS según recursos reales y evita sobreasignación.
10. **Offline:** edición de perfiles/flujos, historial local y cola de operaciones pueden funcionar sin Internet; iniciar Android requiere el motor local; descargar imágenes/APK remotos, proxies externos y callbacks remotos requieren conectividad. Reintentos y sincronización deben ser idempotentes.

## 6. Arquitectura objetivo recomendada

- **PC-MASTER Windows:** UI existente y plano de control; no moverlo a Linux ni reconstruirlo durante esta investigación.
- **WORKERS físicos Debian 13:** runtime Android elegido, adaptador de motor y agente de nodo.
- **Capa de dominio independiente del motor:** contrato común de instancia/capacidades/errores/tareas; ningún módulo de perfiles/RPA depende de comandos de Cuttlefish, redroid o AVD.
- **ADB restringido:** loopback o red de administración autenticada y aislada; no accesible desde redes públicas.
- **Distribución por LAN:** caché de imágenes y APK aprobados, checksum/firma cuando existan, versiones fijadas y descarga única; no depender de registro remoto para operación cotidiana.
- **Automatización desacoplada:** RPA Runner y Synchronizer consumen el contrato del adaptador, no un motor concreto.
- **Coste:** solo herramientas de código abierto/gratuitas con condiciones compatibles; revisar licencias de cada imagen, binario y componente. No depender de APIs de pago, teléfonos cloud ni cuotas de prueba.

## 7. Protocolo de validación

### Puerta 0: documentación/licencia/seguridad
No instalar hasta fijar versiones, licencias de motor e imagen, dependencias, permisos, puertos y mecanismo de actualización. redroid queda bloqueado por la issue #27.

### Puerta 1: una instancia en Debian físico de laboratorio
- Inicio/parada/reinicio repetibles.
- Captura real de pantalla, entrada táctil/teclado y control remoto.
- ADB, instalación/ejecución/desinstalación de APK legítima.
- Persistencia de datos después de reinicio.
- Prueba de red y archivos.
- Medición de CPU/RAM/disco/tiempo de arranque.

### Puerta 2: dos instancias simultáneas
- Datos y archivos aislados.
- ADB/capturas/acciones no cruzadas.
- Operación independiente: parar/reiniciar una no altera la otra.
- RPA en ambas con resultados separados.
- Prueba de saturación y estabilidad.

### Puerta 3: automatización y control
- Flujo RPA con acciones, selectores, condición, bucle limitado, timeout, cancelación y resultado.
- Synchronizer con dos instancias y discrepancias controladas.
- Reinicio del motor o caída de red en mitad de una tarea; comprobar recuperación sin duplicar acciones no idempotentes.
- API local autenticada, autorización, logs redactados y ADB no expuesto.

### Puerta 4: escalado medido
Probar progresivamente 4, 6 y más instancias en un WORKER solo si las métricas lo permiten. No extrapolar a 50 por aritmética simple. Medir RAM/CPU, latencia, disco, temperatura/estabilidad y calidad de la interacción.

### Puerta 5: integración del clúster
PC-MASTER detecta WORKERS, el usuario aprueba adopción y el agente prepara automáticamente el runtime y las imágenes. Nodos pendientes no aceptan tareas. La instalación por red requiere compatibilidad PXE/UEFI y una red controlada; no sobrescribir discos sin aprobación.

## 8. Próximas tareas en GitHub

1. Actualizar issue #8 con esta comparación, la retirada de QEMU/Android-x86 y las puertas de validación.
2. Actualizar ADR-002 para que no recomiende redroid sin resolver la issue #27 y priorice la prueba documental de Cuttlefish.
3. Implementar/validar el contrato agnóstico del motor (issue #12) antes de integrar un motor.
4. Resolver la seguridad de redroid en issue #27 por separado.
5. Mantener el inventario funcional de GeeLark en issue #3, especialmente RPA, Synchronizer, API/Webhooks, perfiles y logs.
6. No instalar en PCs físicos ni declarar motor elegido hasta que la puerta 0 pase y exista autorización para la prueba física.

## 9. Fuentes principales

### GeeLark: producto y automatización
- https://www.geelark.com/product/cloud-phone/
- https://www.geelark.com/features/automation/
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/features/api/
- https://www.geelark.com/pricing/
- https://github.com/GeeLark/geelark-openapi

### Motores
- https://source.android.com/docs/devices/cuttlefish
- https://source.android.com/docs/devices/cuttlefish/multi-tenancy
- https://source.android.com/docs/setup/create/cuttlefish-ref-webrtc
- https://github.com/google/android-cuttlefish
- https://github.com/remote-android/redroid-doc
- https://github.com/remote-android/redroid-modules
- https://github.com/remote-android/redroid-doc/issues/932
- https://developer.android.com/studio/run/emulator-commandline
- https://developer.android.com/studio/run/emulator-acceleration
- https://developer.android.com/studio/terms
- https://github.com/google/android-emulator-container-scripts
- https://waydro.id/
- https://github.com/waydroid/waydroid
- https://www.genymotion.com/legal-terms-and-conditions/
- https://github.com/anbox/anbox

### Automatización
- https://developer.android.com/tools/adb
- https://developer.android.com/training/testing/other-components/ui-automator
- https://github.com/appium/appium-uiautomator2-driver
- https://github.com/Genymobile/scrcpy
- https://docs.maestro.dev/get-started/what-is-maestro

## 10. Registro de cambios

- 2026-10-21: retirada del prototipo manual QEMU + Android-x86 9.0-r2 + VNC como ruta de producto.
- 2026-10-21: Cuttlefish pasa a primera opción documental para una prueba local por su soporte explícito de multiinstancia y WebRTC.
- 2026-10-21: redroid permanece bloqueado por revisión de seguridad; Android Emulator se conserva como referencia de compatibilidad; Waydroid queda secundario.
- 2026-10-21: se amplía el análisis de paridad de GeeLark a RPA Builder, Runner, Synchronizer, API/Webhooks, perfiles, Library y logs.
- 2026-10-21: no hay motor elegido ni pruebas físicas completadas.
