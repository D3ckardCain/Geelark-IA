# Evaluación del sistema operativo base del clúster GeeLark-IA

**Fecha de revisión:** 2026-10-10  
**Estado:** recomendación técnica preliminar; no aprobada para instalación física.  
**Restricción:** coste operativo obligatorio de software/servicios de 0 USD, sin tarjeta ni suscripción obligatoria.

## Resumen ejecutivo

**Estado: sin candidato ganador.** Ubuntu 26.04 LTS directo, Debian 13 Stable directo y Proxmox VE con una VM Linux dedicada permanecen como candidatos documentales. Linux directo probablemente tenga menos capas para la primera prueba del motor Android, pero no hay evidencia suficiente para preferir Ubuntu frente a Debian ni para descartar Proxmox. No se instalará nada hasta la autorización expresa del usuario.

Motivos:
- Debian Stable es una distribución libre sin suscripción obligatoria, con una base conservadora y un ciclo de soporte documentado.
- Linux directo reduce capas y complejidad mientras se valida el motor Android, los módulos de kernel, la GPU integrada y el rendimiento real.
- Proxmox VE es software libre y puede instalarse sin una suscripción, pero su documentación indica que el repositorio no-subscription es para pruebas/no producción y no lo recomienda para servidores de producción; el repositorio Enterprise y soporte forman parte de sus planes de suscripción. Esto entra en tensión con la regla de coste $0 para producción.
- No hay resultados de rendimiento todavía. La recomendación no demuestra que una imagen Android específica vaya a funcionar.

No instalar ningún sistema operativo hasta que se apruebe expresamente el plan de prueba de concepto y se comprueben las licencias de cada componente.

## Comparativa preliminar

Esta primera tabla resume únicamente Linux directo frente a Proxmox; no sustituye la comparación de tres candidatos incluida más abajo.

| Criterio | Linux directo (Ubuntu 26.04 LTS o Debian 13) | Proxmox VE sin suscripción |
|---|---|---|
| Coste obligatorio del SO | 0 USD | 0 USD para descargar/usar; suscripción opcional |
| Repositorio de actualizaciones | Repositorios oficiales de la distribución elegida | Repositorio no-subscription disponible sin clave |
| Adecuación de actualizaciones gratuitas a producción | Depende de la política de soporte de Ubuntu 26.04 LTS o Debian 13 y de los paquetes usados; verificar la cobertura aplicable | Proxmox declara que no-subscription es para pruebas/no producción y no lo recomienda para producción |
| Complejidad inicial | Menos capas: Linux, motor Android y agente | Más capas: Proxmox, VM/CT, red/almacenamiento y motor Android |
| Aislamiento | Depende de contenedores, usuarios, cgroups, namespaces y política local | Puede aportar aislamiento/gestión de VM; la configuración sigue requiriendo auditoría |
| Gestión centralizada de nodos | La implementa GeeLark-IA | Proxmox aporta su propia administración de infraestructura, con requisitos de quorum/cluster |
| Rendimiento Android | Debe medirse; evita una capa de hipervisor | Debe medirse; VM/CT, passthrough y aceleración añaden variables |
| Riesgo de bloqueo tecnológico | Menor si el agente usa interfaces Linux estándar y backends abstractos | Mayor si la automatización depende de APIs específicas de Proxmox |
| Estado actual | Candidato documental; sin preferencia entre Ubuntu y Debian hasta revisar requisitos y probar | Candidato comparativo; su política de actualizaciones gratuitas plantea un riesgo para producción con $0 estricto |

## Requisitos de Android que deben verificarse

El proyecto redroid documenta soporte para hosts Linux x86_64/amd64 y arm64, pero requiere características del kernel y módulos como binder; algunas configuraciones históricas también requieren ashmem. Sus ejemplos usan contenedores privilegiados y advierten expresamente que ADB no debe exponerse a redes públicas.

Antes de seleccionar un motor:
1. Verificar licencia del código y de cada módulo de terceros.
2. Separar la licencia del motor de la licencia de la imagen Android, aplicaciones Google, servicios propietarios y APK de terceros.
3. Confirmar compatibilidad con la CPU/ABI y versión del kernel.
4. Probar si la GPU integrada disponible ofrece aceleración útil; no asumirlo por el nombre de CPU.
5. No exponer el puerto ADB a la LAN general ni a Internet. En la POC debe quedar en loopback/red aislada y ser accesible solo por el adaptador local autorizado.
6. No usar una etiqueta de imagen mutable como versión reproducible; registrar digest, versión, origen y licencia.

redroid declara que su propio código está bajo Apache 2.0 y sus módulos de kernel bajo GPL v2, pero también advierte que incluye componentes de terceros cuyas licencias deben revisarse. Esto no equivale a autorización automática para redistribuir Google Mobile Services ni cualquier APK.

## Propuesta de POC reversible

### Fase 0 — solo inventario, sin instalar

- Registrar modelo exacto de cada PC, CPU completa (incluido sufijo), RAM, disco, firmware/BIOS, soporte VT-x/VT-d, NIC y GPU integrada/dedicada.
- Verificar que no hay información que deba conservarse y confirmar el consentimiento para borrar el disco del equipo de prueba.
- Descargar ISO desde fuente oficial y verificar firma/checksum desde otra máquina.
- Elegir dos equipos distintos para medir heterogeneidad.
- Crear una incidencia GitHub por cada instalación, comando, resultado y fallo; redactar secretos.

### Fase 1 — Linux directo en un solo equipo desechable

Elegir Ubuntu 26.04 LTS o Debian 13 solo después de completar la puerta documental y confirmar que el usuario autoriza expresamente borrar/reinstalar el equipo designado. La matriz de decisión define cómo compararlos sin favorecer uno de antemano.

1. Instalar Debian 13 Stable con particiones simples y cifrado de disco si el equipo admite recuperación de clave documentada.
2. Aplicar actualizaciones de seguridad y deshabilitar servicios/puertos innecesarios.
3. Instalar solo las herramientas de contenedor necesarias, evitando Docker Desktop y cualquier producto que requiera licencia comercial.
4. Probar el motor Android con una imagen y APK de prueba autorizadas.
5. Medir arranque, RAM, CPU, almacenamiento, estabilidad, captura de pantalla y entrada.
6. Confirmar que ADB solo escucha en loopback o en una interfaz aislada y que no es accesible desde redes no autorizadas.
7. Repetir al menos tres veces y registrar fallos.

### Fase 2 — segundo nodo y red aislada

- Repetir en un segundo PC con capacidades diferentes.
- Registrar ambos agentes y validar heartbeat/capacidades.
- Ejecutar una carga compatible y otra incompatible para comprobar la política de colocación.
- Desconectar/reconectar un nodo; verificar que el controlador no duplica instancias ni repite acciones externas de resultado incierto.
- Probar restauración de un respaldo en un nodo compatible, no migración en vivo.

### Fase 3 — evaluar Proxmox solo si existe una razón medible

Proxmox se prueba únicamente si Debian directo no ofrece el aislamiento/operación necesarios. La comparación debe usar la misma carga, imagen, reserva de RAM y protocolo de medición. No activar suscripciones ni repositorios de pago. Documentar claramente el riesgo de usar el repositorio no-subscription en producción; si el coste cero impide una política de actualización aceptable, descartar Proxmox para producción.

## Criterios de decisión

La decisión se toma con datos, no por preferencia:
- compatibilidad Android real;
- aceleración gráfica efectiva;
- rendimiento y estabilidad medidos;
- aislamiento y superficie de ataque;
- recuperación tras pérdida de red/controlador;
- complejidad operativa;
- soporte de seguridad disponible sin suscripción;
- licencias comerciales/redistribución;
- facilidad de migrar a otro host.

**No se aprobará producción** si una función crítica requiere una licencia de pago, una cuenta con tarjeta, un trial, un servicio externo permanente o si no puede mantenerse actualizado de forma segura con coste $0.

## Fuentes oficiales consultadas

- Debian — releases y ciclo de soporte: https://www.debian.org/releases/index.en.html
- Ubuntu — ciclo de soporte LTS: https://ubuntu.com/about/release-cycle
- Debian Stable — versión estable actual: https://wiki.debian.org/DebianStable
- Proxmox — repositorio no-subscription y limitación para producción: https://github.com/proxmox/pve-docs/blob/master/pve-package-repos.adoc
- Proxmox — suscripciones, repositorio Enterprise y soporte: https://www.proxmox.com/en/proxmox-ve/pricing
- redroid — arquitectura, módulos de kernel, seguridad ADB y licencias: https://github.com/remote-android/redroid-doc
- Android Open Source Project — licencias y excepciones de componentes: https://source.android.com/docs/setup/contribute/licenses?hl=es-419

## Estado real

Esta es una evaluación documental basada en fuentes oficiales. No se ha instalado ningún sistema operativo, no se ha ejecutado redroid, no se ha probado aceleración GPU y no existen mediciones de rendimiento. La elección final debe esperar a la POC reversible y a la aprobación explícita del usuario.


## Ubuntu LTS también debe compararse

ADR-001 en `main` nombra Ubuntu LTS como anfitrión de referencia, sin fijar versión exacta. A fecha de esta revisión, la comparación debe incluir Ubuntu 26.04 LTS, además de Debian 13 y Proxmox VE. No es correcto resolver la contradicción solo cambiando de nombre a Debian: hay que comparar los tres candidatos con la misma carga y la misma política de actualizaciones.

| Criterio | Ubuntu 26.04 LTS directo | Debian 13 Stable directo | Proxmox VE |
|---|---|---|---|
| Mantenimiento estándar sin suscripción | Hasta mayo de 2031 para paquetes cubiertos por el mantenimiento estándar de Ubuntu 26.04 LTS | Debian 13: soporte completo hasta agosto de 2028 y LTS hasta junio de 2030; durante LTS puede reducirse la lista de arquitecturas/paquetes cubiertos | Actualizaciones del repositorio no-subscription sin clave; el propio proyecto lo orienta a pruebas/no producción y recomienda Enterprise para producción |
| Ecosistema de virtualización y contenedores | Amplio; versión de kernel y compatibilidad de binder/redroid se deben probar | Amplio; versión de kernel y compatibilidad de binder/redroid se deben probar | Gestión de VMs y LXC integrada; para Android debe decidirse entre VM Linux con kernel propio o LXC con configuración de nesting/dispositivos |
| Capacidad de migrar el agente | Alta si el agente usa interfaces Linux estándar | Alta si el agente usa interfaces Linux estándar | Alta si Proxmox se limita a infraestructura y el agente no depende de sus APIs; menor si se acopla al panel/SDK de PVE |
| Riesgo principal | No fijar la versión/paquetes y descubrir incompatibilidades de kernel o dependencias | No fijar la versión/paquetes y descubrir incompatibilidades de kernel o dependencias | Más capas; riesgo de complejidad de GPU/kernel y política de actualización gratuita no recomendada por el proyecto para producción |
| Estado | Candidato documental pendiente | Candidato documental pendiente | Candidato documental pendiente |

Fuentes oficiales para la cobertura de seguridad:
- Ubuntu 26.04 LTS y ciclo de versiones: https://ubuntu.com/about/release-cycle
- Debian 13 “trixie”: https://www.debian.org/releases/trixie/index.es.html
- Proxmox, repositorios de paquetes: https://github.com/proxmox/pve-docs/blob/master/pve-package-repos.adoc

Los años de soporte no son una prueba de compatibilidad del motor Android. Tampoco debe contarse Ubuntu Pro como requisito: el criterio mínimo es que el sistema pueda recibir las actualizaciones críticas necesarias dentro del mantenimiento estándar sin pagos obligatorios.

## Aplicación al hardware declarado (sin inspección ni cambios físicos)

Inventario comunicado para planificar, pendiente de verificación por comandos de solo lectura:

| Equipo | CPU declarada | RAM | Almacenamiento | Gráficos |
|---|---|---:|---|---|
| PC-MASTER | Intel Core i7; modelo exacto pendiente | 16 GB | 500 GB | Sin GPU dedicada declarada; iGPU exacta pendiente |
| WORKER-01 | Intel Core i5-11400 | 32 GB | NVMe M.2 500 GB | UHD Graphics 730 según ficha de Intel; comprobar controlador y aceleración |
| WORKER-02 | Intel Core i5-11400 | 32 GB | NVMe M.2 500 GB | UHD Graphics 730 según ficha de Intel; comprobar controlador y aceleración |
| WORKER-03 | Intel Core i5-11400 | 32 GB | NVMe M.2 500 GB | UHD Graphics 730 según ficha de Intel; comprobar controlador y aceleración |

Los i5-11400 especifican VT-x y VT-d, pero esto no prueba que la placa base, el firmware y la configuración actual permitan usarlos. El i7 de PC-MASTER se ha mencionado previamente como posiblemente i7-11700, pero no debe tratarse como dato confirmado. Si se confirma ese modelo, Intel indica UHD Graphics 750, VT-x y VT-d; también requiere verificar firmware, controlador y acceso real a la GPU.

Red declarada: LAN Gigabit e Internet simétrico de 10 Mbps. Esto favorece descargar artefactos una vez y distribuirlos por LAN, con hashes, versiones, licencias y aprobación; no justifica que los nodos dependan de Internet para operar.

## Comparación enfocada al motor Android y al clúster

| Necesidad del proyecto | Debian 13 directo | Proxmox VE |
|---|---|---|
| Ejecutar redroid sobre kernel Linux del host | Camino más directo para probar binder/binderfs y contenedores; se debe auditar el modelo de privilegios | En un LXC hay que configurar nesting y dispositivos/kernel con cuidado; en una VM se obtiene un kernel invitado propio, pero se añaden capas |
| Acceso a iGPU Intel para renderizado/captura | Menos capas, pero depende del driver Mesa/kernel y de que el motor realmente use aceleración | Passthrough/compartición de iGPU puede complicar la configuración; no asumir aceleración dentro de las VMs |
| Aislar cada motor Android | Namespaces, cgroups, políticas de usuario, seccomp/AppArmor y red aislada; requiere diseñarlo y probarlo | Las VMs dan una frontera adicional más fuerte en ciertos escenarios; LXC comparte kernel. El aislamiento no queda garantizado por instalar Proxmox |
| Administrar cuatro hosts heterogéneos | GeeLark-IA implementa el inventario, planificador y ciclo de vida; SSH/gestión local deben protegerse | Añade panel y herramientas de gestión de infraestructura, pero GeeLark-IA aún necesita su propio control de tareas y estados |
| Mantener $0 sin suscripción | Repositorios oficiales de Debian y soporte de seguridad/LTS según sus políticas | El repositorio no-subscription existe sin clave, pero Proxmox lo documenta para pruebas/no producción; resolver ese riesgo antes de producción |
| Recuperación/rollback | Se puede usar imagen reproducible, backups y reinstalación automatizada; hay que construirlos | Snapshots/backups y gestión de VM facilitan ciertas recuperaciones, pero consumen almacenamiento y no reemplazan backups externos |
| Riesgo principal | Mayor responsabilidad propia por aislamiento, actualización y recuperación del host | Complejidad adicional, gestión de cluster/quorum si se usa esa función y posibles restricciones prácticas de iGPU/Android |

### Hipótesis de arquitectura que merece validación

Para GeeLark-IA, el candidato inicial más simple sigue siendo probar el motor Android directamente sobre Linux, pero no se toma una decisión final: redroid puede requerir permisos elevados y su modelo de seguridad debe evaluarse antes de confiarle aplicaciones o datos. Proxmox solo debe ganar si sus ventajas de aislamiento/gestión superan de forma medible las complicaciones de GPU, kernel y operación, y si existe una estrategia de actualizaciones aceptable sin suscripción.

No se debe convertir automáticamente cada PC en un nodo Proxmox de un cluster de infraestructura solo porque el producto GeeLark-IA tenga su propio cluster. Son capas distintas: el plano de control de GeeLark-IA debe seguir siendo portable y no depender de una API específica de Proxmox.

## Siguiente trabajo permitido sin modificar equipos

1. Mantener la selección del SO y del motor como **pendiente**.
2. Reconciliar este documento con ADR-001, que actualmente menciona Ubuntu LTS como referencia de host, para que el repositorio no tenga decisiones contradictorias: [Issue #64](https://github.com/D3ckardCain/Geelark-IA/issues/64).
3. Preparar una hoja de decisión con métricas, límites y comandos de inventario de solo lectura.
4. Definir la prueba comparable antes de ejecutarla: misma APK autorizada, misma versión de imagen, mismos límites de CPU/RAM, mismo conjunto de acciones y tres repeticiones por configuración.
5. No instalar paquetes, cambiar BIOS, particionar discos, descargar ISOs a los equipos ni arrancar instaladores hasta autorización explícita.

