> **Documento histórico no ejecutable — actualizado 2026-10-22:** La priorización original de redroid y el plan alternativo QEMU/KVM + Bliss OS que aparecen más abajo ya no representan la decisión vigente. No instalar ni probar siguiendo esta evaluación antigua. QEMU + Android-x86 + VNC en WSL2 está retirado; redroid permanece bloqueado por #27; Cuttlefish es solo candidato de laboratorio pendiente de licencias/seguridad; no hay motor aprobado. Se conserva el análisis como evidencia histórica y debe reconciliarse antes de reutilizarlo.

# Evaluación preliminar del motor Android para el clúster GeeLark-IA

**Estado:** propuesta de arquitectura; no instalada ni probada en el hardware del usuario.  
**Objetivo:** MVP de instancias Android gestionadas desde GeeLark-IA, con coste operativo obligatorio de 0 USD, cuatro PCs dedicadas y conectividad WAN de 10/10 Mbps.

## 1. Inventario de trabajo

| Equipo | CPU recordada (no verificada) | RAM | Disco |
|---|---|---:|---:|
| PC-MASTER | Intel Core i7 (modelo exacto pendiente de confirmar; el usuario recuerda i7-11700) | 16 GB | 500 GB |
| WORKER-01 | Intel Core i5-11400 (confirmado por el usuario) | 32 GB | NVMe M.2 de 500 GB |
| WORKER-02 | Intel Core i5-11400 (confirmado por el usuario) | 32 GB | NVMe M.2 de 500 GB |
| WORKER-03 | Intel Core i5-11400 (confirmado por el usuario) | 32 GB | NVMe M.2 de 500 GB |

No hay tarjetas gráficas dedicadas en ninguno de los equipos. Esto no confirma ni descarta la presencia de gráficos integrados en la CPU; las capacidades de la iGPU y su soporte en Linux deben comprobarse. LAN Gigabit. Los equipos pueden estar encendidos todo el día. La suma declarada es 112 GB de RAM física entre cuatro nodos, no una memoria unificada. El almacenamiento conocido suma 2 TB entre los cuatro equipos.

## 2. Opciones evaluadas

### A. redroid — candidato prioritario para un prototipo

- Proyecto: https://github.com/remote-android/redroid-doc
- El proyecto describe Android en contenedores Linux, con arquitecturas amd64/arm64 y posibilidad de ejecutar múltiples instancias en un host. Como no hay GPU dedicada, hay que comprobar si el motor y la imagen elegida funcionan con gráficos integrados o renderizado por software.
- Puede encajar mejor que una VM completa por instancia para investigar densidad de dispositivos, pero el renderizado por software podría elevar mucho el consumo de CPU. No se debe prometer cuántas instancias caben por worker antes de medir RAM, CPU, gráficos, almacenamiento y compatibilidad de aplicaciones.
- Requiere características/módulos del kernel y permisos elevados en el host; el ejemplo de despliegue usa modo privilegiado. Eso aumenta el impacto potencial de una vulnerabilidad y obliga a aislar los workers, limitar la administración y no publicar ADB en Internet. Además, la documentación pública registra un reporte reciente (julio de 2026) donde el init de Android en un contenedor privilegiado modificó `/proc/sys/kernel/modprobe` del host, un ajuste no aislado por namespace. Antes de cualquier prueba hay que verificar la incidencia y mitigación en la versión elegida; hasta entonces, no ejecutar redroid en un host que también aloje servicios críticos.
- La licencia del proyecto principal es Apache-2.0, pero el propio proyecto advierte que hay componentes de terceros cuyas licencias deben revisarse. Google Mobile Services/Play Store, imágenes propietarias y traducción de aplicaciones ARM no se deben dar por incluidos ni legalmente redistribuibles.
- **Veredicto:** candidato para laboratorio, no seleccionado para producción. Su densidad potencial debe sopesarse contra el riesgo del modo privilegiado y la dependencia del kernel compartido. La prueba requiere un worker aislado, acceso físico/recuperación disponible, firewall restrictivo y revisión de la incidencia de seguridad antes de ejecutar.

### B. Android Emulator oficial — útil como referencia de prueba

- Documentación: https://developer.android.com/studio/run/emulator-acceleration
- En Linux, la aceleración depende de KVM y de que VT-x/Intel 64/XD estén disponibles y habilitados. La disponibilidad de aceleración gráfica también debe medirse; sin GPU dedicada, el rendimiento de gráficos puede convertirse en un límite.
- Está orientado al desarrollo y pruebas de Android. Puede servir para una prueba comparativa de compatibilidad, pero aún no se ha validado como motor de operación continua de muchas instancias gestionadas remotamente en este clúster.
- Deben evaluarse tamaño de imágenes, descargas del SDK, uso de RAM/GPU y condiciones de uso antes de elegirlo.
- **Veredicto:** referencia secundaria de pruebas, no decisión de producción por ahora.

### C. Android x86 / Bliss OS en QEMU/KVM — alternativa para aislar cada instancia

- Documentación: https://docs.blissos.org/installation/install-in-a-virtual-machine/install-in-qemu/
- QEMU/KVM permite asignar CPU, RAM, disco y red a cada VM; la documentación de Bliss OS advierte que ciertos modos/ versiones pueden tener limitaciones gráficas o de compatibilidad.
- Una VM completa ofrece un límite de aislamiento más claro que compartir el kernel del host, pero normalmente consume más recursos por instancia y requiere validar cuidadosamente arranque, gráficos, entrada y compatibilidad con aplicaciones. La falta de GPU dedicada hace especialmente importante probar la aceleración disponible y el coste del renderizado por software.
- **Veredicto:** plan alternativo si redroid falla con las aplicaciones objetivo o si la compatibilidad/aislamiento pesa más que la densidad.

## 3. Propuesta inicial de arquitectura

- **PC-MASTER:** panel/API de control de GeeLark-IA, registro de nodos y tareas, cola de operaciones, inventario de capacidad y caché de artefactos en LAN. No asumir que el panel web existente ya hace todo esto; integrar por fases.
- **WORKER-01/02/03:** Linux Server sin entorno gráfico innecesario, agente de nodo con identidad propia, runtime de Android validado, límites de recursos y métricas. El agente debe autenticar las órdenes y reportar resultados; la base de datos no debe confiar en un nombre de nodo declarado sin autenticación.
- **Red interna:** comunicación de gestión restringida a la LAN; no exponer ADB ni puertos administrativos a Internet. Separar credenciales de agentes, rotarlas y permitir revocación.
- **Planificador:** asignar instancias considerando RAM/CPU/disk disponible, límites por nodo y estado de salud. La capacidad por worker se establecerá mediante pruebas de carga, no por estimación.
- **Persistencia:** mantener la lógica de asignación transaccional/idempotente del prototipo bajo revisión; todavía no equivale a un clúster operativo y no se harán cambios de Supabase durante esta fase.
- **Recuperación:** si un worker se desconecta, marcar sus instancias como no disponibles, conservar operaciones idempotentes y reconciliar estado al reconectar. No reubicar automáticamente una instancia con estado local no replicado como si fuera una copia idéntica.

## 4. Caché local para WAN de 10/10 Mbps

PC-MASTER puede alojar una caché HTTP interna para artefactos aprobados, si el hardware y el sistema operativo elegidos lo permiten. Separar tres categorías:

1. Paquetes del sistema operativo y actualizaciones de seguridad.
2. Imágenes del sistema Android, contenedores y herramientas del runtime.
3. Instaladores/actualizaciones de aplicaciones, solo cuando sus términos permitan almacenarlos y distribuirlos de esa manera.

Cada artefacto tendrá un manifiesto con nombre, versión, arquitectura, URL de origen, fecha de descarga, licencia, tamaño, SHA-256, estado (pendiente/aprobado/revocado) y nodos destino. Flujo: descargar una vez → verificar hash y firma cuando exista → registrar procedencia/licencia → probar en un worker de laboratorio → aprobar explícitamente → distribuir por LAN → registrar resultado. Mantener versiones anteriores para rollback, salvo que una licencia o requisito de seguridad obligue a retirarlas.

No se debe copiar ni redistribuir automáticamente todo lo que se descargue. La caché no elimina las condiciones de licencia del proveedor. Las actualizaciones de aplicaciones pueden tener restricciones distintas de los paquetes Linux.

## 5. Sistema operativo: criterio, no decisión definitiva

La primera candidata para evaluar es una distribución Linux Server con soporte vigente, paquetes disponibles sin suscripción obligatoria y soporte documentado de KVM/contenedores. Ubuntu Server LTS y Debian Stable son candidatos razonables para comparar; no se ha elegido aún una versión definitiva porque primero hay que validar los requisitos del kernel de redroid, controladores gráficos y soporte de seguridad. No instalar hasta cerrar esta matriz de compatibilidad.

## 6. Puerta de seguridad específica para redroid

La documentación de redroid recomienda no exponer ADB en una red pública y usa `--privileged` en el ejemplo de arranque. Adicionalmente, el issue público #932 del proyecto reportó en julio de 2026 que el init de Android dentro de un contenedor privilegiado puede escribir en `/proc/sys/kernel/modprobe` del host y deshabilitar la carga automática de módulos del kernel; el reporte figura cerrado, pero el cierre por sí solo no demuestra que la versión concreta que usemos esté protegida.

Antes de una prueba:
1. Leer el issue #932 y su solución/discusión para la versión exacta de imagen y kernel.
2. No ejecutar el primer experimento en PC-MASTER ni en un worker que aloje datos/servicios irremplazables.
3. Usar un worker de laboratorio sin secretos, limitar ADB a loopback o a una VLAN/LAN de administración restringida, y bloquear cualquier publicación hacia Internet.
4. Definir un procedimiento de recuperación por consola local/Live USB y una copia de seguridad previa de cualquier dato necesario.
5. Si no puede demostrarse una mitigación aceptable, detener redroid y comparar una VM completa QEMU/KVM u otra alternativa; no relajar seguridad para conseguir que arranque.

Fuentes relevantes:
- Guía y advertencia ADB de redroid: https://github.com/remote-android/redroid-doc
- Reporte de seguridad/impacto de host (issue #932): https://github.com/remote-android/redroid-doc/issues/932
- Requisitos de kernel de redroid: https://github.com/remote-android/redroid-doc/blob/master/deploy/README.md

## 7. Pruebas obligatorias antes de desplegar

1. Confirmar modelo exacto del i7 de PC-MASTER; los tres i5-11400 de los workers están confirmados por el usuario. Inventariar la iGPU disponible, RAM, disco y soporte VT-x en cada PC; comprobar VT-x habilitado en BIOS/UEFI.
2. Arrancar un entorno Live USB sin instalar ni modificar discos para inventariar hardware, cuando el usuario esté listo.
3. Instalar solo en un worker de prueba después de revisar y aprobar el plan de recuperación.
4. Validar arranque/parada, persistencia de datos, ADB restringido a LAN, streaming/visualización remota y recuperación tras reinicio.
5. Probar las aplicaciones reales requeridas: arquitectura ABI, servicios Google si son necesarios, notificaciones, red, cámara/sensores si aplican y comportamiento de autenticación. No asumir que las aplicaciones bancarias, DRM o apps con detección de emulador funcionarán.
6. Medir memoria, CPU y carga gráfica en reposo y bajo carga, latencia, estabilidad durante 24 horas y densidad máxima sostenible con margen de seguridad. Comparar aceleración integrada y renderizado por software cuando ambas opciones existan.
7. Probar fallo de red, reinicio de worker, actualización fallida, rollback y restauración de caché.
8. Revisar licencias y seguridad antes de permitir uso continuo.

## 8. Costos y límites conocidos

- No se propone ningún servicio de pago obligatorio ni una API de pago.
- El software de base seleccionado debe ser libre/gratuito y no requerir tarjeta o periodo de prueba.
- El objetivo de 0 USD no elimina costos indirectos de electricidad, desgaste, conexión a Internet o tiempo de mantenimiento.
- GitHub Actions y otros servicios con cuotas no deben ser una dependencia crítica de ejecución; las pruebas esenciales deben poder correr localmente.
- No se promete paridad funcional con GeeLark. Cada módulo deberá tener manual, pruebas y matriz de brechas contra la referencia.

## 9. Decisión provisional

**Mantener redroid como candidato de laboratorio condicionado a superar la puerta de seguridad**, con Android Emulator como comparación de pruebas y Bliss OS/QEMU-KVM como alternativa de aislamiento. Si el riesgo del contenedor privilegiado no queda resuelto de forma verificable, no usar redroid y priorizar la evaluación de una VM completa. Esta es una recomendación de investigación, no una aprobación para instalar. El siguiente bloqueo técnico es confirmar el modelo exacto del i7 de PC-MASTER, identificar las capacidades gráficas integradas y listar las aplicaciones/funciones que deben funcionar en cada teléfono virtual.

## Fuentes oficiales

- redroid: https://github.com/remote-android/redroid-doc
- Reporte sobre `kernel.modprobe` en contenedor privilegiado (issue #932): https://github.com/remote-android/redroid-doc/issues/932
- Requisitos de kernel de redroid: https://github.com/remote-android/redroid-doc/blob/master/deploy/README.md
- Aceleración de Android Emulator: https://developer.android.com/studio/run/emulator-acceleration
- Bliss OS en QEMU: https://docs.blissos.org/installation/install-in-a-virtual-machine/install-in-qemu/
- Documentación de Bliss OS: https://docs.blissos.org/
