# Estado del proyecto Geelark-IA

**Actualizado:** 2026-10-11  
**Fase:** A — inventario funcional de GeeLark y estudio de viabilidad de Android virtualizado local.  
**Implementación:** no hay módulos declarados como terminados o verificados.

## Objetivo acordado

Replicar las funciones de GeeLark aplicables a Android en una plataforma local. Los dispositivos objetivo serán instancias Android virtualizadas/emuladas en el hardware anfitrión físico; no se presupone el uso de teléfonos físicos. iOS queda excluido. Se busca la máxima paridad funcional que pueda verificarse, sin prometer equivalencia total antes de investigar y probar.

## Principios permanentes

1. Objetivo de coste operativo de software/servicios obligatorios: **0 USD**; evitar tarjeta obligatoria, pruebas temporales, cobros automáticos y APIs de pago.
2. Priorizar software libre, local o autoalojado; minimizar dependencia de proveedores y facilitar migración.
3. Operación offline cuando sea técnicamente viable, documentando sus límites.
4. GeeLark es la referencia funcional. Cada equivalencia requiere evidencia y pruebas.
5. Avanzar por fases completas, probadas, documentadas y aceptadas.
6. Cada módulo tendrá manual de usuario completo y documentación técnica.
7. GitHub es el registro principal de requisitos, decisiones, tareas, problemas, soluciones, pruebas y cambios.
8. Todo el registro del proyecto se mantendrá en español.
9. No declarar una función, prueba o capacidad como terminada sin evidencia.
10. Implementación independiente; no copiar código, marca ni activos propietarios.

## Documentos principales

- [Plan maestro de paridad funcional](PLAN_PARIDAD_GEELARK.md)
- [Investigación funcional de GeeLark](INVESTIGACION_FUNCIONAL_GEELARK.md)
- [Matriz de paridad funcional](MATRIZ_PARIDAD_GEELARK.md)
- [Plan de trabajo](PLAN_TRABAJO.md)
- [Comparativa de motores Android locales](COMPARATIVA_MOTORES_ANDROID.md)
- [Modelo de amenazas y requisitos de seguridad](MODELO_AMENAZAS_SEGURIDAD.md)
- [Guía de inventario del equipo anfitrión](GUIA_INVENTARIO_EQUIPO.md)
- [Arquitectura tecnológica propuesta](ARQUITECTURA_TECNOLOGICA_PROPUESTA.md)
- [ADR-001 — Stack principal](decisiones/ADR-001-STACK-PRINCIPAL.md)
- [ADR-002 — Estrategia de selección del motor Android](decisiones/ADR-002-ESTRATEGIA-MOTOR-ANDROID.md)
- [Inventario de licencias y coste](INVENTARIO_LICENCIAS_COSTE.md)
- [Contrato del adaptador Android](CONTRATO_ADAPTADOR_ANDROID.md)
- [Especificación del motor RPA](ESPECIFICACION_MOTOR_RPA.md)
- [Requisitos](REQUISITOS.md)

## Investigación documental inicial

El Centro de ayuda de GeeLark lista Profile, Proxies, Library, AIGC, Analytics, Applications, Automaton, Synchronizer, GeeHub, Resources, Referral, Billing, Members y Logs; además hay documentación sobre grupos, ADB, perfiles, conexión de dispositivos locales y cámara. Las páginas oficiales describen automatización mediante plantillas, RPA visual, Synchronizer, API y webhooks.

Fuentes principales:
- https://help.geelark.com/
- https://www.geelark.com/es/producto/cloud-phone/
- https://www.geelark.com/es/pricing/
- https://www.geelark.com/features/automation/
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/features/api/
- https://www.geelark.com/features/synchronizer/

La investigación y la matriz son preliminares: aún falta desglosar cada pantalla, campo, flujo, restricción y error, y realizar pruebas prácticas.

## Fase activa: entregables pendientes

- [ ] Desglosar los artículos del centro de ayuda y notas de versión por función.
- [ ] Registrar evidencia y criterios de aceptación en la matriz.
- [x] Investigar preliminarmente motores de virtualización/emulación Android local y registrar candidatos.
- [ ] Comparar licencias, compatibilidad y límites con mayor profundidad y ejecutar pruebas.
- [ ] Recopilar especificaciones del equipo anfitrión.
- [ ] Definir una prueba técnica reproducible de una instancia Android virtual.
- [ ] Ejecutar y documentar la prueba antes de seleccionar stack definitivo.

## Decisiones pendientes

No están aprobados el sistema operativo anfitrión, el stack, la base de datos, el motor de control, el virtualizador, las imágenes Android, el número simultáneo de instancias ni la tecnología de IA local. Estas decisiones requieren investigación de licencias, compatibilidad, rendimiento, seguridad y costes.

## Registro de cambios

- 2026-10-09: se confirma el objetivo de paridad funcional con GeeLark, solo Android y con coste obligatorio de software/servicios de 0 USD.
- 2026-10-09: se aclara que el hardware físico será el anfitrión y los dispositivos objetivo serán Android virtualizados/emulados localmente, no teléfonos físicos.
- 2026-10-09: se crea la investigación funcional inicial y la matriz de paridad, con fuentes oficiales y límites aún no verificados.
- 2026-10-09: se corrige el plan maestro para eliminar el supuesto de teléfonos Android físicos como requisito.
- 2026-10-09: se registran candidatos de virtualización local (redroid, Android Emulator, Waydroid y Android-x86) sin seleccionar todavía un motor.
- 2026-10-09: se crea la issue [#5 — Evaluar motores de Android virtualizado local](https://github.com/D3ckardCain/Geelark-IA/issues/5) con criterios de selección y entregables.


## Actualización de auditoría — 2026-10-09

Se creó el [catálogo funcional detallado de GeeLark](CATALOGO_FUNCIONAL_GEELARK.md), que desglosa de forma preliminar perfiles, proxies, RPA, Synchronizer, Library, aplicaciones, API/CLI/ADB, logs y AIGC a partir del centro de ayuda y notas de versión oficiales hasta v4.5.2. Se detectaron funciones que deben añadirse a la especificación: clonado de perfiles, configuración de red celular/Wi-Fi en versiones Android específicas, importación/exportación de RPA, inspección del árbol UI, carga masiva de archivos desde Synchronizer, etiquetado de activos y consulta posterior de parámetros de tareas.

- [x] Crear catálogo funcional detallado inicial.
- [x] Registrar la issue [#6 — Completar el catálogo funcional](https://github.com/D3ckardCain/Geelark-IA/issues/6).
- [ ] Completar campos, acciones, errores y restricciones de cada módulo.
- [ ] Completar el inventario de bloques RPA y contratos API/ADB.
- [ ] Añadir criterios de aceptación verificables a todas las filas relevantes de la matriz.
- [ ] Continuar investigación de motores Android y prueba práctica tras recopilar las especificaciones del anfitrión.

La investigación sigue siendo documental y parcial. No se ha seleccionado un motor, no hay pruebas de ejecución local y no se declara ningún módulo implementado ni equivalente.


### Hallazgo crítico de paridad: huella extraída de teléfono físico

La documentación oficial de GeeLark para “Add Custom Phone” describe la extracción de parámetros desde un Android físico conectado por USB/ADB. Como el proyecto se definió sin depender de teléfonos físicos, esa función específica no puede reproducirse de forma idéntica bajo el alcance actual. Se registró como diferencia estructural: la alternativa posible es una identidad sintética por instancia, limitada a los campos que admita el motor y sin prometer equivalencia con un dispositivo físico real. Este hallazgo queda desarrollado en `docs/CATALOGO_FUNCIONAL_GEELARK.md` y `docs/MATRIZ_PARIDAD_GEELARK.md`.


## Actualización de alcance — importación desde dispositivos físicos

El usuario confirmó que son viables ambas rutas: identidades sintéticas por instancia e importación de configuración/identidad desde un Android físico. La importación por USB/ADB queda incluida como capacidad candidata; ya no se considera excluida por alcance. Se deben investigar los campos realmente accesibles y compatibles, ofrecer selección campo por campo, excluir datos privados por defecto, no modificar el dispositivo de origen y no prometer clonación íntegra.

Nuevos requisitos preliminares P-027 a P-031 añadidos a la matriz: detección ADB, inspección de campos, importación selectiva, aplicación/verificación y trazabilidad segura. Pendiente: probar con un dispositivo Android compatible y registrar resultados antes de declarar viabilidad o equivalencia.


Issue específica de esta capacidad: [#7 — Investigar importación selectiva desde Android físico por USB/ADB](https://github.com/D3ckardCain/Geelark-IA/issues/7).

### Decisión registrada — compatibilidad amplia de Android por ADB

El usuario confirma que desea compatibilidad objetivo con **cualquier teléfono Android que permita ADB**, sin priorizar una marca o versión concreta. La estrategia será un adaptador genérico con validación progresiva y una matriz de compatibilidad por fabricante, modelo, versión Android/API, herramientas ADB y campos disponibles. “Cualquier Android” es el objetivo, no una promesa de compatibilidad universal antes de probar cada combinación. Cada dispositivo tendrá resultados explícitos de detección, lectura e importación de campos; las limitaciones del fabricante/versión se documentarán.

- [Catálogo funcional y decisión de compatibilidad](CATALOGO_FUNCIONAL_GEELARK.md#161-compatibilidad-objetivo-android-de-cualquier-marca-y-versión-progresiva)
- [Issue #7 — Importación selectiva por USB/ADB](https://github.com/D3ckardCain/Geelark-IA/issues/7)



## Actualización — comparativa documental de motores Android (2026-10-09)

Se creó [COMPARATIVA_MOTORES_ANDROID.md](COMPARATIVA_MOTORES_ANDROID.md) con revisión preliminar de redroid, Android Emulator, Waydroid y Android-x86/derivados, incluyendo fuentes oficiales, licencias, requisitos, riesgos de seguridad y protocolo de prueba reproducible. **No se ha seleccionado motor**: no hay pruebas en el equipo anfitrión real y el rendimiento no puede certificarse sin sus especificaciones.

- [x] Registrar comparativa documental preliminar.
- [x] Crear [issue #8 — Comparar y validar motores Android locales](https://github.com/D3ckardCain/Geelark-IA/issues/8).
- [ ] Revisar licencias y componentes de terceros de cada versión candidata.
- [ ] Obtener especificaciones del anfitrión y ejecutar la prueba mínima.
- [ ] Comparar resultados de ADB, captura/entrada, APK, persistencia, aislamiento y recursos.

Hallazgo provisional: redroid se prioriza para la primera prueba si el anfitrión es Linux compatible, por su enfoque de multiinstancia; esta prioridad no equivale a una selección definitiva. Android Emulator queda condicionado a revisión de las condiciones del SDK y las imágenes. Waydroid y Android-x86/derivados requieren validar modelo de instancias, mantenimiento y aislamiento.


## Actualización de auditoría funcional y contratos locales — 2026-10-09

Se amplió el catálogo funcional con verificaciones directas de Profile, Proxies, Applications, Profile management, Automaton/RPA, GeeHub/API, Synchronizer y el CLI público de GeeLark. El catálogo ahora separa funciones expresamente documentadas de los detalles que siguen sin evidencia y añade criterios de aceptación preliminares.

- [x] Verificar campos y restricciones visibles de perfiles/proxies.
- [x] Verificar operaciones descritas de aplicaciones y grupos.
- [x] Verificar funciones generales de RPA, API/CLI y Synchronizer.
- [x] Añadir una lista inicial de contratos funcionales para el API/CLI local.
- [x] Añadir criterios de aceptación preliminares a la matriz.
- [ ] Completar catálogo exhaustivo de bloques RPA y esquemas de importación/exportación.
- [ ] Enumerar endpoints API publicados, métodos, esquemas, errores y límites.
- [ ] Completar el inventario de funciones de Library, Members, Logs, Analytics, cámara y sensores.
- [ ] Validar funciones en el motor Android local tras elegirlo mediante pruebas.

La nueva evidencia no cambia los estados a “implementado” o “equivalente”. El producto sigue sin módulos implementados. La selección del motor está bloqueada hasta conocer el anfitrión y ejecutar pruebas reproducibles.


## Actualización de auditoría — Library, Members, Analytics, ADB y cámara (2026-10-09)

Se incorporaron al catálogo los hallazgos de las guías oficiales de Library, Members, Analytics, ADB y cámara, y se actualizaron las filas P-006, P-011, P-013, P-015 y P-019 de la matriz.

Puntos clave:
- Library de GeeLark se describe como función Pro y con retención cloud temporal; Geelark-IA prioriza archivos locales persistentes.
- La guía ADB consultada enumera Android 11–16; el acceso local se diseñará restringido y no se expondrá públicamente.
- Analytics de redes sociales es una integración externa distinta de las métricas locales del motor.
- Multiusuario/roles requieren matriz de permisos; no se obliga a crear cuentas cloud para uso local.
- La cámara se evaluará por fuente (imagen, webcam, vídeo pregrabado, cámara física opcional), sin afirmar equivalencia física.
- La guía pública de Logs no aporta contenido suficiente para inferir su esquema; P-014 sigue pendiente de evidencia.

No hay implementación ni pruebas de motor. El inventario continúa en fase A.


## Actualización — notas v4.5.1 y v4.5.2 (2026-10-09)

Se revisaron las notas oficiales recientes y se añadieron al catálogo criterios para carga masiva de archivos e historial de Synchronizer, inspector/árbol UI, etiquetas y vistas de Library, parámetros de tareas publicados y seguimiento de uso AIGC. Se actualizaron las filas P-006, P-007, P-009 y P-014 de la matriz.

- [x] Registrar novedades de v4.5.1 y v4.5.2 en el catálogo.
- [x] Vincular criterios de aceptación en la matriz.
- [ ] Completar el manual RPA por bloques y formato de exportación.
- [ ] Completar contratos de API a partir de la documentación accesible.
- [ ] Cerrar los huecos de evidencia de Logs y otras áreas de equipo.
- [ ] Validar el motor Android en hardware anfitrión real.

La fase continúa siendo investigación. El inventario todavía no está completo y no hay módulos implementados.


## Actualización — modelo de amenazas y seguridad (2026-10-09)

Se creó [MODELO_AMENAZAS_SEGURIDAD.md](MODELO_AMENAZAS_SEGURIDAD.md) y la [issue #9 — Controles de seguridad local, ADB, RPA e importación](https://github.com/D3ckardCain/Geelark-IA/issues/9). Es un documento de requisitos, no evidencia de que el producto actual ya sea seguro.

Incluye límites de confianza, protección de credenciales, aislamiento entre instancias, restricciones de ADB/shell, validación de archivos, seguridad de webhooks, importación de solo lectura desde Android físico, backups, operación offline y pruebas de seguridad antes de publicar. Se subraya el riesgo de contenedores privilegiados y puertos ADB expuestos.

- [x] Registrar modelo de amenazas y controles.
- [ ] Implementar y probar controles después de seleccionar motor y arquitectura.
- [ ] Revisar riesgos residuales antes de cualquier versión usable.


## Bloqueo para pruebas físicas — especificaciones del anfitrión

La investigación documental y los protocolos están preparados, pero la comparación final requiere datos del equipo real. Se creó [GUIA_INVENTARIO_EQUIPO.md](GUIA_INVENTARIO_EQUIPO.md) con comandos de lectura para Windows, Linux y macOS, y la [issue #10 — Recopilar especificaciones del anfitrión](https://github.com/D3ckardCain/Geelark-IA/issues/10).

No se requiere instalar nada ni compartir números de serie. Hasta recibir los datos, se continuará con la documentación funcional; no se inventarán resultados de rendimiento ni se aprobará un motor por intuición.


## Cambio de enfoque — selección de software por arquitectura, no por hardware (2026-10-09)

Se acepta la directriz de no bloquear la estrategia en las especificaciones de un equipo concreto. Se creó [ARQUITECTURA_TECNOLOGICA_PROPUESTA.md](ARQUITECTURA_TECNOLOGICA_PROPUESTA.md) y la [issue #11](https://github.com/D3ckardCain/Geelark-IA/issues/11).

Propuesta inicial: Tauri 2 + React/TypeScript/Vite; FastAPI/Python; SQLite con migraciones; adaptadores desacoplados para motores Android; Android Emulator oficial como baseline de compatibilidad y redroid en Linux como experimento de densidad; ADB encapsulado; RPA propio con estados, límites y recuperación; Appium/UIAutomator2 y Playwright para pruebas.

La elección del motor sigue pendiente de pruebas comparativas, pero ya no se requiere hardware del usuario para diseñar el stack y los contratos. Se continuará con decisiones tecnológicas, licencias, contratos y pruebas reproducibles genéricas. Ninguna función se considera implementada por la sola creación de estos documentos.


## Decisiones tecnológicas preliminares registradas

- [ADR-001 — Stack principal](decisiones/ADR-001-STACK-PRINCIPAL.md): Linux Ubuntu LTS x86_64 como anfitrión de referencia; Tauri/React/TypeScript, FastAPI/Python, SQLite; Android Emulator como baseline y redroid como candidato de densidad sujeto a pruebas.
- [Inventario de licencias y coste](INVENTARIO_LICENCIAS_COSTE.md): licencias de componentes principales, advertencias sobre imágenes/APK y build local obligatorio.

Estas son decisiones de diseño para prototipo; no certifican todavía la compatibilidad del motor Android ni la seguridad de una instalación real.


## Contratos funcionales para la implementación

Se añadieron [CONTRATO_ADAPTADOR_ANDROID.md](CONTRATO_ADAPTADOR_ANDROID.md) y [ESPECIFICACION_MOTOR_RPA.md](ESPECIFICACION_MOTOR_RPA.md). El primero define capacidades, estados, errores, idempotencia y pruebas de conformidad por motor. El segundo define bloques RPA tipados, límites, cancelación, recuperación y sincronización explícita. Ambos son especificaciones, no implementaciones.


La estrategia del motor Android quedó registrada en ADR-002: redroid es candidato de experimento para multiinstancia; Android Emulator es baseline de compatibilidad y Waydroid alternativa de laboratorio. La decisión final depende de pruebas de conformidad, seguridad y licencias.


## Actualización — clúster heterogéneo como requisito central (2026-10-09)

Se confirma que Geelark-IA debe administrar varios PC físicos heterogéneos mediante una PC principal de operación y agentes por nodo. El planificador distribuirá instancias Android y trabajos según recursos y compatibilidad; el diseño no puede asumir un solo anfitrión.

- [x] Documentar la arquitectura de clúster: [ARQUITECTURA_CLUSTER_HETEROGENEO.md](ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- [x] Registrar la decisión distribuida: [ADR-003](decisiones/ADR-003-ARQUITECTURA-DISTRIBUIDA-CLUSTER.md).
- [x] Especificar el contrato del agente/planificador: [CONTRATO_AGENTE_NODO_PLANIFICADOR.md](CONTRATO_AGENTE_NODO_PLANIFICADOR.md).
- [x] Documentar comparación inicial: [COMPARATIVA_INFRAESTRUCTURA_CLUSTER.md](COMPARATIVA_INFRAESTRUCTURA_CLUSTER.md).
- [x] Crear [issue #14](https://github.com/D3ckardCain/Geelark-IA/issues/14) para seguimiento.
- [ ] Validar contrato mediante pruebas de esquema y seguridad.
- [ ] Ejecutar prueba de concepto con al menos dos nodos heterogéneos.
- [ ] Medir rendimiento Android, aislamiento, pérdida de red, recuperación y backups.
- [ ] Aprobar Proxmox VE o Linux directo con evidencia, no por preferencia teórica.

Hallazgo documental: Proxmox VE puede usarse sin comprar una licencia de software y su código es AGPLv3, pero el acceso a repositorios Enterprise y el soporte son comerciales; el repositorio no-subscription es una opción sin clave cuyo nivel de validación tiene advertencias oficiales. Proxmox tiene gestión de clúster multi-master y quorum, así que la PC principal de Geelark-IA es un rol operativo del producto y no un supuesto nodo maestro exclusivo de Proxmox. Fuentes y límites en [COMPARATIVA_INFRAESTRUCTURA_CLUSTER.md](COMPARATIVA_INFRAESTRUCTURA_CLUSTER.md).

**Estado real:** documentos y criterios creados; no existe aún agente, planificador ni clúster implementado y no se han ejecutado pruebas de rendimiento.


## Actualización — planificador de recursos y prueba de concepto (2026-10-09)

- [x] Crear la especificación documental del planificador de recursos.
- [x] Crear el protocolo de prueba de concepto para comparar Linux directo y Proxmox VE.
- [ ] Definir persistencia autoritativa, consistencia y fencing para asignaciones distribuidas.
- [ ] Validar esquemas del agente y protocolo mediante pruebas.
- [ ] Ejecutar pruebas con al menos dos nodos heterogéneos.
- [ ] Medir capacidad, rendimiento, desconexión, reconciliación y restauración.
- [ ] Decidir infraestructura a partir de evidencia y revisar licencias.

Documentos: [ESPECIFICACION_PLANIFICADOR_RECURSOS.md](ESPECIFICACION_PLANIFICADOR_RECURSOS.md) y [PLAN_PRUEBA_CONCEPTO_CLUSTER.md](PLAN_PRUEBA_CONCEPTO_CLUSTER.md).

**Estado real:** se añadieron especificaciones y un plan de pruebas, no código ejecutable. No se ha medido rendimiento ni se ha aprobado Proxmox/Linux directo.


### Propuesta de persistencia del plano de control (2026-10-09)

Se añadió [ADR-004 — Persistencia y consistencia del clúster](decisiones/ADR-004-PERSISTENCIA-CONSISTENCIA-CLUSTER.md). La propuesta para el MVP es PostgreSQL local en la Master, un solo controlador activo y sin failover automático hasta contar con pruebas de fencing/quorum. Si la Master cae, se pausan nuevas asignaciones; no se deben detener automáticamente instancias existentes. La propuesta requiere validación y no está implementada.


### Contrato de mensajes del agente (2026-10-09)

- [x] Definir documentalmente mensajes de alta, heartbeat, inventario, asignación y resultado.
- [x] Definir códigos de error, reglas de idempotencia, epochs y estados inciertos.
- [ ] Crear modelos Pydantic y fixtures.
- [ ] Ejecutar pruebas de contrato, concurrencia y reconciliación.

Documento: [CONTRATO_MENSAJES_AGENTE_CLUSTER.md](CONTRATO_MENSAJES_AGENTE_CLUSTER.md).

**Límite:** contrato documental sin código ni pruebas ejecutadas.


### Regla operativa de continuidad (2026-10-09)

El trabajo debe continuar proactivamente entre tareas y fases, sin pedir confirmación en pasos rutinarios. Solo solicitar intervención del usuario cuando sea imprescindible por acceso, credenciales, decisión de producto no inferible, aprobación personal o ejecución de una prueba física. Cada avance, decisión, problema, solución y prueba se registra en GitHub en español; distinguir siempre diseño, implementación y verificación real.


### Primer paquete de contratos en revisión (2026-10-09)

Se abrió el PR borrador [#16 — modelos tipados y máquina de estados](https://github.com/D3ckardCain/Geelark-IA/pull/16). La rama contiene un paquete Python aislado con modelos Pydantic, reglas de transición de estados y pruebas unitarias. La copia de trabajo local correspondiente pasó 32 casos; esto no equivale a validar un checkout limpio del PR. La integración permanece pendiente hasta ejecutar la instalación y pruebas exactas del branch y revisar los cambios.

No se ha implementado el agente, el scheduler, la persistencia autoritativa, la autenticación entre nodos ni fencing.


### Revisión de contrato actualizada (2026-10-09)

El PR borrador #16 ahora incluye validación de coherencia entre `status` y `observed_state`, además de la máquina de estados. La copia de trabajo local pasó 33 casos de prueba. Sigue sin equivaler a validación del checkout exacto del PR; la integración queda pendiente de esa verificación.


### Persistencia de asignaciones documentada (2026-10-09)

Se creó [ESPECIFICACION_PERSISTENCIA_ASIGNACIONES.md](ESPECIFICACION_PERSISTENCIA_ASIGNACIONES.md). Define transacciones, restricciones para un único propietario, idempotencia durable, outbox y pruebas de caída/concurrencia. No hay DDL, migraciones ni código de persistencia implementados; PostgreSQL local sigue siendo una propuesta pendiente de validar.


## Auditoría del trabajo en ramas no integradas — 2026-10-10 UTC

Esta sección distingue explícitamente el trabajo que existe en ramas/PR de lo que está integrado en `main`. **Un PR abierto, aunque tenga CI verde, no significa que el código esté integrado ni validado en las PCs físicas.**

### Estado de GitHub observado

- Repositorio privado: `D3ckardCain/Geelark-IA`; rama predeterminada: `main`.
- 14 PR abiertos en la instantánea tomada inmediatamente antes de crear el propio PR #45; todos estaban en borrador. La creación de #45 elevó el total a 15 PR abiertos.
- 29 Issues abiertas en esa instantánea; no se cerraron Issues automáticamente durante la auditoría.
- No se fusionó ningún PR ni se desplegó código en equipos físicos.

### Cadenas de cambios abiertas

| Área | Cadena de PR | Estado y precaución |
|---|---|---|
| Contratos del clúster | #16 → #30; #28 se basa en la rama de #16 | Borradores; ejecutar/revisar el checkout exacto antes de integrar |
| Persistencia y asignación | #32 → #34 → #36 → #38 | Borradores apilados; no integrar fuera de orden |
| Autenticación de agentes | #42 → #44; #40 documenta la ADR por separado | Borradores; revisar dependencia documental de ADR-005 y CI del HEAD actual |
| Documentación/investigación | #21, #23, #25, #26 | Borradores independientes basados en `main` |

### Hallazgos y controles de auditoría

1. PR #19 fue cerrado como supersedido, no fusionado; Issue #20 sigue abierta porque recuperación, backup/restauración y reconciliación aún no están demostrados.
2. PR #44 recibió una corrección de calidad: el workflow de integración ahora contempla cambios del guardián y autenticación también en `push` a `main`; las credenciales tienen un máximo de vigencia de 365 días, con 90 días por defecto.
3. La primera CI tras ese cambio detectó una omisión en la ruta de rotación de credenciales. Se corrigió en el commit `10df3c863f7a9ec2d1abd751964d7f9818eb0351`; la corrección no se considera validada hasta que una nueva ejecución de CI termine en éxito.
4. La implementación de persistencia, outbox, journal offline y autenticación descrita en los PR sigue siendo trabajo de ramas. No es todavía una capacidad integrada de `main` ni una validación operativa en hardware real.
5. Mantener abiertas las Issues relacionadas hasta que los PR sucesores estén integrados y sus criterios de aceptación se hayan demostrado. No cerrar en bloque ni considerar duplicada una Issue solo porque exista un PR.

### Próximos pasos de integración

- Obtener CI satisfactoria para el HEAD actualizado de PR #44.
- Revisar los diffs y dependencias de las cadenas apiladas como conjuntos, incluida la decisión ADR-005.
- Añadir pruebas pendientes de expiración, rotación concurrente, recuperación y backup/restauración.
- Revisar permisos mínimos, HTTPS con CA local, redacción de secretos y límites antes de cualquier transporte real.
- Conservar el coste operativo obligatorio de 0 USD y no instalar/desplegar nada en las PCs físicas sin autorización explícita.


## Auditoría de continuidad del repositorio — 2026-10-11

Corte de auditoría: 2026-10-11 UTC. Esta revisión es de solo lectura sobre GitHub; no se fusionó, desplegó, instaló ni ejecutó código en PCs físicas y no se modificó ninguna base de datos del usuario.

### Inventario y estado integrado

- Repositorio privado; rama predeterminada `main`, HEAD observado `f62fd1163fcb45e338978b6d8f777135dc87584b`.
- GitHub reporta la rama `main` sin protección. El árbol de `main` no contiene `.github/workflows/` ni archivos de automatización de seguridad; los workflows que se observan viven en ramas/PR y no equivalen a CI integrada en `main`.
- Se observaron **29 PR abiertos, los 29 en draft**, y **40 Issues abiertas**. Ningún PR se fusionó durante esta auditoría.
- Las PRs abiertas de módulos no representan funcionalidades integradas: el panel de PC-MASTER sigue siendo una maqueta; el proveedor de snapshots aún no tiene endpoint administrativo ni conexión con el panel; el inventario de módulos solo existe en una rama apilada.

### CI verificada en HEADs actuales

- PR #70, HEAD `ba22e44a67d4253f08cc7a2bad79acdabca7f465`: check de prototipo **success**. Esto acredita el workflow del prototipo, no validación física ni accesibilidad completa.
- PR #73, HEAD `23675a4f8970ce9a827014ebc3c2652897bbdd92`: **3 checks success** (transporte, persistencia y migraciones/invariantes).
- PR #74, HEAD `80e7f17865fc34f6f64832180ae4ad81d71a2042`: la API de check-runs muestra **1 check success** (servicio de persistencia). La descripción de la PR afirma también checks Guard y Autenticación para ese mismo HEAD, pero no aparecen asociados a ese SHA en la consulta actual; no dar esos dos checks por confirmados hasta aportar sus ejecuciones exactas.
- PR #48, HEAD `2c58c3edf732de265235dae3dc683aa958e4208d`: **3 checks success**.
- PR #54, HEAD `9533e9b14e815b86771d21e62d10f03b4f3e5bdd`: **3 checks success**.
- PR #68, HEAD `db09da25ac37b612489931408156f04d9c89079e`: **3 checks success**.
- PR #38, HEAD `b41a2e6ce44e881f7f3e03c18e3fe586f1cdb584`: **1 check success y 1 failure**. Falló `test_v1_journal_migrates_to_v2_and_preserves_synced_ack` en `packages/cluster-agent-guard/tests/test_journal.py:363`: la prueba esperaba versión 2 y observó 3. No se reintentó para evitar consumo innecesario de minutos; corregir prueba/migración y ejecutar de nuevo cuando el cambio esté listo.
- Los HEADs de PRs documentales #21, #23, #25, #26, #40, #45 y #60 no muestran check-runs; se consideran **CI no aplicable/no confirmada**, no CI aprobada.
- No se hallaron revisiones formales ni hilos inline en las PRs clave #38, #48, #54, #68, #70, #73 y #74; tampoco hay revisores solicitados en la lista de PRs abiertas consultada.

### Dependencias, deriva y posibles duplicados

- Cadena reciente del control: #48 (transporte HTTPS) → #73 (inventario versionado de módulos) → #74 (proveedor interno de snapshots). #73 y #74 siguen en draft.
- #74 copia el esquema/ejemplo del contrato que vive en la PR #70 no fusionada. Riesgo de divergencia del contrato; antes de integrar, establecer una fuente única versionada o validar automáticamente los hashes/contenidos contra el contrato canónico.
- #47 introduce `cluster_agent_auth.authorization`; #48 mantiene otra matriz de operaciones/estados en `cluster_agent_transport.policy`. Ambas contienen listas de operaciones permitidas para nodos pending/active. La Issue #65 prohíbe duplicar esta lógica: decidir un único dueño de política y hacer que el transporte lo adapte, o documentar/testear formalmente la separación.
- #52 y #54 implementan la bandeja de tareas sobre el mismo transporte. #54 es la rama “clean” para el núcleo del claim, pero #52 además contiene contrato/manuales, pruebas adicionales y trabajo de reconciliación/runtime que no se demuestra cubierto íntegramente por #54. **No cerrar #52 todavía**: mapear lo restante a #61/#57 y conservar o portar los entregables exclusivos antes de declarar supersesión completa.
- #59 y #67 son variantes que se solapan en supervisor/heartbeat. #67 agrega monitor de conectividad y endurecimiento de credenciales, mientras #59 contiene piezas de bootstrap/proveedor de credenciales; la cobertura no es idéntica. No cerrar ninguna hasta comparar y decidir explícitamente la variante canónica.
- Las comparaciones de ramas indican deriva con respecto a sus bases actuales: #52 y #54 van 8 commits detrás de `feat/agent-https-transport`; #68 también 8; #59 va 7 detrás de `feat/agent-lifecycle-sync-inbox`; #34 va 7 detrás de `feat/cluster-persistence-schema`; #36 va 3 detrás de `feat/cluster-assignment-service`; #38 va 5 detrás de `feat/cluster-outbox-dispatcher`. Los compares reportan ramas divergentes. Antes de integrar, actualizar cada pila en orden y volver a validar el merge result/HEAD combinado.
- La Issue #20 mantiene pendientes autenticación real, dispatcher, recuperación y backup/restauración; no se cierra por las pruebas parciales de PostgreSQL desechable.

### Seguridad, coste y operación

- Riesgo de gobernanza alto: `main` no está protegida y no tiene workflows integrados. Recomendación: después de integrar y validar workflows de coste bajo, habilitar protección/PR review y checks requeridos sin permitir auto-merge.
- Los workflows inspeccionados declaran `permissions: contents: read` y usan PostgreSQL desechable, lo que limita privilegios. Sin embargo, algunos usan `actions/checkout@v4` y `actions/setup-python@v5`; Actions ha emitido advertencia por Node.js 20/deprecación. Actualizar versiones soportadas y, para mayor garantía de cadena de suministro, considerar pinning a SHA completo. Los paquetes declaran rangos de dependencias en `pyproject.toml`; no se encontró lockfile en la rama de transporte inspeccionada.
- La CI privada genera ejecuciones repetidas en PRs apilados. La Issue #63 sigue abierta; no se dispararon re-runs manuales. Mantener `concurrency`, filtros `paths` y evitar triggers duplicados. El gasto mensual real de Actions no fue accesible desde este corte y no se afirma que el consumo total sea cero.
- Se conserva el objetivo obligatorio de coste operativo de **0 USD**: no se incorporaron servicios de pago, trials ni requisitos de tarjeta. Se mantienen procedimientos offline donde son viables; el proveedor PostgreSQL de snapshots requiere conectividad local y no tiene caché offline.
- No se cerraron PRs ni Issues en este corte: las coincidencias encontradas aún no prueban supersesión completa, y varias tareas tienen puertas de seguridad/recuperación pendientes.

### Próximos pasos ordenados

1. Corregir el fallo de migración del journal en #38 y obtener CI verde del HEAD exacto.
2. Resolver la política duplicada #47/#48 y confirmar pruebas negativas de pending/revoked/expired en el stack completo (#65).
3. Re-sincronizar las pilas #32→#34→#36→#38 y #48→#54→#57→#59/#67→#61; resolver explícitamente #52 frente a #54 antes de cerrar cualquier rama.
4. Verificar las ejecuciones Guard/Auth del HEAD exacto de #74; mantener el proveedor como solo lectura, sin endpoint ni UI hasta autenticar/autorizAR al operador.
5. Mantener #70/#73/#74 en draft hasta revisión humana, contrato único, pruebas de accesibilidad/seguridad y validación de integración.
6. Tratar CI, integración de PR, validación operativa en LAN y prueba en hardware como cuatro estados distintos. No instalar agentes, ejecutar ADB/shell ni tocar bases del usuario sin autorización explícita.


### Seguimiento de auditoría y acciones registradas — 2026-10-10

Se publicaron comentarios de auditoría en las conversaciones de GitHub:
- [PR #38 — journal offline](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6104209742): fallo de migración/esquema; corregir según contrato y validar el HEAD nuevo.
- [PR #48 — transporte HTTPS](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6104209949): política de autorización duplicada frente a #47.
- [PR #54 — bandeja durable](https://github.com/D3ckardCain/Geelark-IA/pull/54#issuecomment-6104210222): solapamiento con #52; conservar entregables exclusivos hasta demostrar supersesión.
- [PR #59 — supervisor](https://github.com/D3ckardCain/Geelark-IA/pull/59#issuecomment-6104210458) y [PR #67 — supervisor/heartbeat](https://github.com/D3ckardCain/Geelark-IA/pull/67#issuecomment-6104210726): comparar cobertura y decidir variante canónica sin cerrar prematuramente.
- [PR #70 — contrato Master/Worker](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6104210916): evitar copia divergente del esquema v1; establecer fuente canónica y verificación.
- [PR #74 — snapshots](https://github.com/D3ckardCain/Geelark-IA/pull/74#issuecomment-6104211090): reconciliar evidencia CI con SHA/jobs exactos; separar CI de autorización real e integración.
- [Issue #63 — coste de CI](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6104211309): mantener 0 USD, reducir ejecuciones redundantes y no afirmar coste real cero sin datos de uso.

**Estado de resolución:** los comentarios y decisiones quedaron registrados, pero las correcciones de código y la validación combinada siguen pendientes. No se fusionó ninguna PR, no se cerraron elementos, no se desplegó, no se tocaron PCs físicas ni bases de datos del usuario. El fallo #38 no se debe declarar corregido hasta obtener evidencia verde sobre el nuevo HEAD.

### Corrección aplicada después del corte — journal offline (#38)

- Commit de test: [61284c2e0f936a17c2d2236370f08baa9868e00d](https://github.com/D3ckardCain/Geelark-IA/commit/61284c2e0f936a17c2d2236370f08baa9868e00d).
- Se actualizó el nombre de la prueba de migración de v1→v2 a v1→v3, se espera `schema_migrations.version == 3` y se verifica la columna `task_id`, manteniendo la comprobación de ACK sincronizado.
- Se actualizaron el comentario y la sección de criterios de aceptación de PR #38.
- **CI pendiente de evidencia:** para el SHA nuevo, el conector no reporta workflow runs ni status checks. No declarar el fallo resuelto hasta comprobar una ejecución verde sobre ese SHA.
- Comentarios de seguimiento en [PR #38](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6104215555), [Issue #65](https://github.com/D3ckardCain/Geelark-IA/issues/65#issuecomment-6104217466) y [Issue #20](https://github.com/D3ckardCain/Geelark-IA/issues/20#issuecomment-6104217719).

**Balance de esta sesión:** cambios documentales y una corrección de prueba implementados; arquitectura de autorización duplicada, sincronización de ramas y verificación de CI siguen pendientes. No se fusionó ni cerró ningún elemento, no se desplegó ni se tocó hardware o base de datos operativa.


### Última actualización de CI en #38 — 10-oct-2026

- Se actualizaron las acciones del workflow `.github/workflows/cluster-persistence-service.yml` de `actions/checkout@v4`/`actions/setup-python@v5` a `@v5`/`@v6`, alineadas con las versiones modernas usadas en otras ramas.
- Commit más reciente de la rama de #38: [e37e5aaef72837c19837eb5b648c29f05ae9b3c3](https://github.com/D3ckardCain/Geelark-IA/commit/e37e5aaef72837c19837eb5b648c29f05ae9b3c3). Incluye la corrección de expectativa v1→v3 anterior y el ajuste del workflow.
- En la consulta posterior, tanto los status checks como los workflow runs visibles para ese SHA siguen vacíos. Aunque el workflow tiene trigger `pull_request` y filtros de paths que incluyen `packages/cluster-agent-guard/**`, no hay evidencia para declarar CI iniciada o aprobada. Investigar el motivo sin lanzar reintentos redundantes.
- PR #38 sigue abierta y en draft. No se cerró por falta de evidencia; CI, integración de ramas y validación operativa permanecen como estados separados.


### Evidencia CI corregida para el journal offline (#38) — 2026-10-10

Una consulta posterior sí devolvió ejecuciones completas en verde asociadas al HEAD consultado `e37e5aaef72837c19837eb5b648c29f05ae9b3c3`; se corrige la nota anterior que decía que no había runs visibles:
- [Cluster persistence schema #38102140362](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102140362): job de migraciones PostgreSQL y pruebas de esquema/invariantes, completed/success.
- [Cluster persistence service #38102140404](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102140404): job de persistencia/concurrencia, agent guard y `pip check`, completed/success.
- Se actualizaron los criterios de aceptación en [PR #38](https://github.com/D3ckardCain/Geelark-IA/pull/38) y se añadió evidencia en [comentario de seguimiento](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6104234181).

**Estado exacto:** la prueba del journal y el workflow están implementados y CI está verde en el HEAD consultado. No significa que la PR esté integrada ni que el módulo esté validado en operación real. Permanecen pendientes cobertura explícita de migración v1/v2, comprobación de la pila completa y validación operativa; la PR sigue abierta y en borrador.


### Contrato de autorización: incompatibilidad concreta entre #47 y #48 — 2026-10-10

La inspección de código confirma que la duplicación de policy no se puede resolver con un simple import:
- Módulo canónico de #47: `AgentOperation` usa `PUBLISH_CAPABILITIES`, `READ_OWN_STATUS`, `ACCEPT_TASK`, `REPORT_PROGRESS`, `REPORT_RESULT`; `AgentAuthorizationContext` requiere `credential_expires_at` y valida expiración/revocación.
- Policy local de #48: enum `Operation` usa `CAPABILITIES`, `STATUS_READ`, `TASK_ACCEPT`, `TASK_PROGRESS`, `TASK_RESULT`; `AgentPrincipal` no incluye expiración de credencial.
- Se registró el hallazgo en [PR #47](https://github.com/D3ckardCain/Geelark-IA/pull/47#issuecomment-6104236633) y [PR #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6104236868).

**Decisión:** no borrar todavía la policy del transporte ni cambiar imports hasta hacer explícita la dependencia apilada de #47, crear un adaptador que mapee todas las operaciones y pase la expiración real, instalar el paquete local en CI y probar los casos pending/active/revoked/expired. Esto evita introducir una autorización incompleta por una refactorización prematura.

**Estado actualizado de #38:** CI verde en el HEAD `e37e5aaef72837c19837eb5b648c29f05ae9b3c3`: [schema #38102140362](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102140362) y [persistence/guard #38102140404](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102140404). La PR continúa abierta y en draft; CI no equivale a integración ni a validación operativa.


### Revalidación de CI del transporte y dependencias de autorización — 2026-10-10

La auditoría de `packages/cluster-agent-transport/src/cluster_agent_transport/db_auth.py` confirma que la consulta de autenticación exige `c.expires_at > now()` y que solo acepta pares coherentes `active/active` o `pending/pending`. No obstante, la expiración no se devuelve en `AgentPrincipal`; la policy canónica de PR #47 requiere `credential_expires_at`. Por tanto, la expiración sí se filtra en la autenticación actual, pero las dos políticas siguen sin ser equivalentes ni estar integradas.

También se verificó la topología real de ramas: PR #47 y PR #48 son hermanas basadas en `feat/cluster-agent-auth-service`; #48 no hereda automáticamente el paquete de autorización de #47. No cambiar imports ni eliminar la policy local hasta decidir si se apila #48 sobre #47 o se define un adaptador/dependencia de monorepo verificable.

Se actualizó `.github/workflows/cluster-agent-transport.yml` en [commit `62bfdbe74bba49652058420d7485ee8afab8750e`](https://github.com/D3ckardCain/Geelark-IA/commit/62bfdbe74bba49652058420d7485ee8afab8750e): `actions/checkout@v5`, `actions/setup-python@v6` y checkout del journal desde el HEAD `e37e5aaef72837c19837eb5b648c29f05ae9b3c3` de PR #38. La consulta inmediatamente posterior aún no devolvía workflow runs ni check-runs para el nuevo SHA; **CI pendiente de confirmación**, no declarada como aprobada.

Siguiente paso: confirmar el resultado de CI en ese SHA y, con base en ello, ejecutar pruebas de conformidad entre operaciones de ambas policies (incluyendo pending/active, estados incoherentes y expiración) antes de integrar la dependencia. No se ha fusionado ni desplegado nada.

### Actualización de evidencia CI del panel Master — 2026-10-10

Se volvió a consultar la rama de PR #70: HEAD `ba22e44a67d4253f08cc7a2bad79acdabca7f465`. Para ese SHA, [Master control prototype checks #38095144974](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38095144974) está `completed/success`; se verificaron los pasos de regresión Python, render del HTML real con Chrome/Chromium y análisis de sintaxis del JavaScript embebido. La evidencia quedó registrada también en [comentario de PR #70](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6104296571). Esto no cubre accesibilidad manual completa ni integración con estado real de Workers; la PR sigue abierta y draft.


### Resultado CI posterior a la actualización del transporte — 2026-10-10

La actualización de `.github/workflows/cluster-agent-transport.yml` quedó validada para el HEAD `62bfdbe74bba49652058420d7485ee8afab8750e`: [transporte HTTPS #38102709434](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102709434), [esquema #38102709315](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102709315) y [servicio de persistencia #38102709380](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38102709380) terminaron `completed/success`; los tres jobs aparecen completados sin pasos fallidos. La descripción de [PR #48](https://github.com/D3ckardCain/Geelark-IA/pull/48) se actualizó con esta evidencia. Sigue sin probarse la pila final con #47 ni resolverse la policy duplicada; #48 permanece draft.


### Comparación de ramas de bandeja durable y ciclo de vida — 2026-10-10

La comparación de archivos confirma que PR #52 y #54 son alternativas superpuestas: comparten `0004_agent_task_inbox.sql`, handlers/rutas de transporte, policy y servicio de persistencia. #52 contiene entregables adicionales (runtime y reconciliación read-only, validación de datos sensibles); #54 documenta pruebas específicas de API/handler y carrera concurrente de claim. No se declara #54 supersedida hasta verificar que su cobertura exclusiva está incorporada y pasa en un único HEAD combinado. Registro en [comentario de #52](https://github.com/D3ckardCain/Geelark-IA/pull/52#issuecomment-6104302286).

PR #59 y #67 tampoco son duplicados exactos: #59 aporta proveedor de credenciales/bootstrap/supervisor coordinador; #67 aporta entrada CLI configurable y monitor netlink con fallback. Comparten base y parte de documentación, por lo que hay que conservar los componentes complementarios y revisar las colisiones de contrato antes de integrar. Registro en [comentario de #67](https://github.com/D3ckardCain/Geelark-IA/pull/67#issuecomment-6104302505). No se cerró ni fusionó ninguna PR.


### Contrato Master/Worker compartido entre #70 y #74 — 2026-10-10

Se compararon los artefactos en los HEAD consultados: el JSON Schema `master-worker-status-v1.schema.json` es idéntico en #70 y #74 (blob SHA `6802ec9d2a973840edd774301b2c9259bc514c2e`), y el ejemplo también (blob SHA `9a7976293e4c874d369fcfb4f1aadf4677234b02`). No existe divergencia actual; sí hay riesgo de deriva futura porque viven en ramas independientes. Se recomienda fijar dueño canónico del contrato o añadir una prueba de CI que exija igualdad. Hallazgo registrado en [comentario de PR #74](https://github.com/D3ckardCain/Geelark-IA/pull/74#issuecomment-6104303695).

### Revisión de base y numeración de migraciones de la bandeja — 2026-10-11

Revalidado el HEAD de PR #52: `ea3e0d099e4b6e09b63162f6af8ccb12f6d767e6`, base declarada `feat/master-status-snapshot-provider-v1` (`c5bc7925a83f00d3f021cc73ca196f46300e414f`). El cuerpo de #52 aún dice que se apila sobre #48, lo que no coincide con la metadata actual. #52 añade `db/migrations/0005_agent_task_inbox.sql`; #54 contiene `db/migrations/0004_agent_task_inbox.sql`; ambos archivos tienen el mismo blob SHA `c1468c0e9bee0032d09a2905329fe8b92a5d095b`. Es la misma migración DDL con versiones distintas, riesgo de duplicación histórica y confusión de orden. Se registró en [#52](https://github.com/D3ckardCain/Geelark-IA/pull/52#issuecomment-6111193628) y [#54](https://github.com/D3ckardCain/Geelark-IA/pull/54#issuecomment-6111193984).

Los workflows del HEAD de #52 (`ea3e0d0…`) terminaron `completed/success`: transporte #38124212390, persistencia #38124212414, esquema #38124212515. Esto acredita los tests CI de esa rama, pero no resuelve la base incorrectamente descrita ni la doble numeración. Decisión: mantener ambas PR abiertas y draft; determinar la única secuencia de migraciones de la base final, preservar las pruebas exclusivas de cada rama y ejecutar CI en el HEAD consolidado antes de marcar supersesión.


### Integración de autorización canónica en transporte — 2026-10-11

Se extendió el contrato de PR #47 con `claim_task` y `report_modules`; los nodos `pending` siguen limitados a heartbeat, capacidades y lectura de estado. PR #48 se apiló sobre `feat/agent-operation-authorization`, reemplazó su matriz duplicada por un adaptador hacia `cluster_agent_auth.authorization`, y `db_auth.py` ahora devuelve `credential_expires_at` desde PostgreSQL. Se añadió una prueba de credencial con timestamp expirado y se documentó la instalación conjunta de ambos paquetes en README/manual y CI.

El HEAD `e2b868e66e91c6a58502f5b38a26020cb351aaf9` de [PR #48](https://github.com/D3ckardCain/Geelark-IA/pull/48) terminó con tres workflows exitosos: [transporte #38156174591](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156174591), [esquema #38156174563](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156174563), [persistencia #38156174584](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156174584). Los jobs y pasos quedaron `completed/success`, incluyendo pruebas, migraciones PostgreSQL desechable y `pip check`. Evidencia registrada en [comentario de #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6111244685).

Siguiente integración obligatoria: PR #73 debe mapear `modules_report` a `report_modules` (solo nodos activos), y la bandeja durable debe mapear `task_fetch` a `claim_task` (nunca permitido para pending). CI de #48 no valida automáticamente esas ramas descendientes. No hubo merge, despliegue ni acceso a bases de datos del usuario.


### Reconciliación de PR #73 con autorización canónica — 2026-10-11

PR #73 había quedado divergida respecto de la nueva base de PR #48. Se combinaron sus cambios con la base actual mediante el commit de merge de rama [`a4205a78fa63273ab92784ae5a750831f7167639`](https://github.com/D3ckardCain/Geelark-IA/commit/a4205a78fa63273ab92784ae5a750831f7167639); no se fusionó la PR. La policy de transporte en la rama de inventario mapea `MODULES_REPORT` a `AgentOperation.REPORT_MODULES`; el inventario de módulos sigue prohibido para nodos pending. Se conservaron las pruebas del endpoint, rechazo de módulos desconocidos/duplicados, persistencia y frescura; se reconciliaron las fixtures para incluir `credential_expires_at`, los manuales y los workflows.

GitHub ahora devuelve `mergeable=true` para [PR #73](https://github.com/D3ckardCain/Geelark-IA/pull/73). Los workflows del nuevo HEAD `a4205a78fa63273ab92784ae5a750831f7167639` estaban en ejecución: [transporte #38156617380](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156617380), [esquema #38156617349](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156617349), [persistencia #38156617397](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156617397). No declarar validada hasta que los tres terminen correctamente.


### Revalidación final de PR #48 y workflow de esquema — 2026-10-11

El HEAD actualizado de [PR #48](https://github.com/D3ckardCain/Geelark-IA/pull/48) es `dbd9dc5058053f49c1be20d33298f5e8b68ca5db`; los tres workflows terminaron `completed/success`: [transporte #38156537832](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156537832), [esquema #38156537911](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156537911) y [persistencia #38156537998](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156537998). La verificación de jobs confirma pruebas, migraciones desechables y chequeo de dependencias exitosos. Se actualizó `actions/checkout@v5` en el workflow de esquema; la descripción y [comentario de #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6111300074) contienen la evidencia.


### Pila de autorización y módulos: ramas con historia sincronizada — 2026-10-11

Se corrigió un problema de topología Git detectado por CI: cambiar la base de una PR no añade por sí solo los commits de esa base a su rama de origen. Se creó el merge commit [`a1b2298d2dc5385a792dd5dec65a69b2e51cce10`](https://github.com/D3ckardCain/Geelark-IA/commit/a1b2298d2dc5385a792dd5dec65a69b2e51cce10) para incorporar realmente #47 en la rama de #48, conservando el adaptador y sus pruebas. El HEAD a1b2298 tiene los tres workflows `completed/success`: [transporte #38156857103](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857103), [esquema #38156857152](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857152), [persistencia #38156857127](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857127).

Después se sincronizó la rama de #73 con ese HEAD mediante [`31c93b3ab54f91d357b7cd16bba9d205e277deab`](https://github.com/D3ckardCain/Geelark-IA/commit/31c93b3ab54f91d357b7cd16bba9d205e277deab). La policy de módulos conserva el mapeo canónico `MODULES_REPORT → REPORT_MODULES`; `db_auth.py` conserva el vencimiento de credencial. #73 informa `mergeable=true`, comparación `ahead 14 / behind 0`; su CI nuevo está en cola: [transporte #38156909185](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909185), [esquema #38156909211](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909211), [persistencia #38156909212](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909212). No se fusionó ninguna PR.


### CI final de PR #73 con autorización canónica — 2026-10-11

El HEAD sincronizado `31c93b3ab54f91d357b7cd16bba9d205e277deab` terminó con los tres workflows exitosos: [transporte #38156909185](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909185), [esquema #38156909211](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909211), [persistencia #38156909212](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156909212). Los logs del transporte confirman **58 pruebas aprobadas**, `pip check` correcto y un warning deprecatorio Starlette/httpx; no es fallo de CI. Quedó registrado en [comentario de #73](https://github.com/D3ckardCain/Geelark-IA/pull/73#issuecomment-6111345986). La PR sigue draft, no fusionada ni desplegada.


### Sincronización del proveedor de snapshots y divergencia real del schema v1 — 2026-10-11

Se incorporó la base actual de PR #73 a la rama del proveedor de snapshots mediante el commit [`a8ce049458e94ae2587caeb8a42269a0b094b09a`](https://github.com/D3ckardCain/Geelark-IA/commit/a8ce049458e94ae2587caeb8a42269a0b094b09a), sin fusionar #74. La comparación de ramas indica `ahead 3 / behind 0` y `mergeable=true`. El workflow de persistencia #38157104581 está en cola.

Corrección del hallazgo previo: el schema v1 ya no es idéntico entre #70 y #74. #70 conserva blob `6802ec9d2a973840edd774301b2c9259bc514c2e`; #74 usa `d7f5975aebf3ac605e1afa5bee75d1674636fb62`, con enum cerrado para `module_id` y validaciones más estrictas de estado/origen/versión. Se registró en [#74](https://github.com/D3ckardCain/Geelark-IA/pull/74#issuecomment-6111362474) y [#70](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6111362841). La decisión pendiente es consolidar una fuente canónica y actualizar los tests del panel/proveedor en consecuencia; no se cerró ni fusionó ninguna PR.


### CI de PR #74 proveedor de snapshots — 2026-10-11

El HEAD `a8ce049458e94ae2587caeb8a42269a0b094b09a` de [PR #74](https://github.com/D3ckardCain/Geelark-IA/pull/74) pasó el workflow [#38157104581](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157104581), `completed/success`. La suite valida el proveedor de snapshots y la prueba de rol SELECT-only contra PostgreSQL desechable, además de las suites de persistencia/guard/auth disponibles. No valida permisos del rol real ni autenticación humana del panel. El comentario y el cuerpo de #74 fueron actualizados; la divergencia de schema con #70 sigue abierta.


### Sincronización de bandeja durable sobre pila canónica — 2026-10-11

La base real de PR #52 es `feat/master-status-snapshot-provider-v1` (#74), que depende de #73 → #48 → #47; su descripción original decía incorrectamente que se apilaba directamente sobre #48. Se incorporó la base actual con el merge commit [`9fc25e10fd0ba9b14c4febd1b8072498c596cb54`](https://github.com/D3ckardCain/Geelark-IA/commit/9fc25e10fd0ba9b14c4febd1b8072498c596cb54). GitHub informa `mergeable=true`, `ahead 14 / behind 0`.

La migración `0005_agent_task_inbox.sql` es secuencial y adecuada en esta pila porque el inventario de módulos usa `0004_worker_module_inventory.sql`. La alternativa #54 basada directamente en #48 utiliza `0004_agent_task_inbox.sql`, por lo que no se deben combinar ambos archivos de migración sin resolver antes la cadena base. La policy de #52 ahora mapea `TASK_FETCH → CLAIM_TASK` y `MODULES_REPORT → REPORT_MODULES` en la política canónica; se actualizaron fixtures con `credential_expires_at`. CI del HEAD `9fc25e10fd0ba9b14c4febd1b8072498c596cb54` está en cola: [persistencia #38157391979](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157391979), [esquema #38157392001](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157392001). Pendiente comprobar el workflow de transporte y comparar la cobertura con #54.


### CI final de bandeja durable y cobertura de terminal replay — 2026-10-11

El HEAD `2e0f9011e60850aa2d6fd13d140615d7f23921fc` de [PR #52](https://github.com/D3ckardCain/Geelark-IA/pull/52) pasó los tres workflows: [transporte #38157472745](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157472745) con **63 pruebas aprobadas**, 1 warning deprecatorio Starlette/httpx y `pip check` correcto; [esquema #38157472743](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157472743); [persistencia #38157472794](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157472794). La suite PostgreSQL confirma doble claim concurrente con un ganador, leases de entrega/instancia, idempotencia, repetición terminal idéntica, conflicto terminal, epoch obsoleto y reconciliación read-only. La cobertura incluye los casos que motivaron #54 y el arreglo #68; se registró en [comentario de #52](https://github.com/D3ckardCain/Geelark-IA/pull/52#issuecomment-6111421290).

Decisión: #52 es el sucesor funcional de las alternativas #54 y #68 dentro de la pila que además incorpora inventario de módulos y autorización canónica. Se cerrarán #54/#68 como supersedidas, con enlaces a #52 y sin fusionar ninguna rama.


### Cierre justificado de alternativas de bandeja — 2026-10-11

Se cerraron [PR #54](https://github.com/D3ckardCain/Geelark-IA/pull/54) y [PR #68](https://github.com/D3ckardCain/Geelark-IA/pull/68) como `closed`, `merged=false`, **supersedidas por #52**. No se cerraron en bloque ni se fusionaron: se compararon archivos y pruebas; #52 integra la migración secuencial después de inventario, autorización canónica, claim concurrente, leases/attempts, idempotencia terminal, conflicto terminal y epoch obsoleto. Los tres workflows de #52 pasaron en HEAD `2e0f9011e60850aa2d6fd13d140615d7f23921fc` con 63 pruebas de transporte. Comentarios con evidencia y sucesor: [#54](https://github.com/D3ckardCain/Geelark-IA/pull/54#issuecomment-6111424748), [#68](https://github.com/D3ckardCain/Geelark-IA/pull/68#issuecomment-6111425123). La PR #52 sigue abierta y draft; no se ha fusionado ninguna rama.


### Unificación del contrato Master/Worker status v1 — 2026-10-11

La divergencia de schema entre #70 y #74 quedó resuelta al actualizar el esquema de la rama canónica del panel con el endurecimiento de inventario Worker. Ambas ramas comparten blob `d7f5975aebf3ac605e1afa5bee75d1674636fb62`; el ejemplo ficticio continúa idéntico (blob `9a7976293e4c874d369fcfb4f1aadf4677234b02`). El schema restringe `module_id` a IDs soportados y valida estado/origen/versión. Se actualizaron [PR #70](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6111435560) y [PR #74](https://github.com/D3ckardCain/Geelark-IA/pull/74#issuecomment-6111435860). CI de #70 para HEAD `195cd0012806d539304c1d0ec27d9a616e6f5081` está en cola (#38157662672); hasta que pase, la unificación está hecha en código pero no revalidada por CI.


### CI del contrato v1 unificado — 2026-10-11

El HEAD `195cd0012806d539304c1d0ec27d9a616e6f5081` de [PR #70](https://github.com/D3ckardCain/Geelark-IA/pull/70) pasó [Master control prototype checks #38157662672](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157662672): regresión Python, renderizado HTML real con Chrome/Chromium y sintaxis JavaScript completados en success. El esquema v1 ahora coincide con #74 (blob `d7f5975aebf3ac605e1afa5bee75d1674636fb62`), y el ejemplo también es idéntico. Quedan accesibilidad manual e integración con estado real. Evidencia en [comentario de #70](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6111439985).


### Sincronización del ciclo de recibos con la bandeja canónica — 2026-10-11

PR #57 se sincronizó con el HEAD validado de #52 mediante [`3bbd65d6c49884408086219a364f251ddbd8c9b7`](https://github.com/D3ckardCain/Geelark-IA/commit/3bbd65d6c49884408086219a364f251ddbd8c9b7). GitHub informa `mergeable=true`, `ahead 6 / behind 0`. La rama conserva `0004_worker_module_inventory.sql`, `0005_agent_task_inbox.sql`, auth canónica/expiración y agrega el lifecycle SQLite de recibos; README/manual documentan la instalación conjunta de paquetes. Workflow transporte [#38157876743](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157876743) en cola; revisar la integración TLS loopback/PostgreSQL antes de validar.


### CI final de sincronización durable #57 — 2026-10-11

El HEAD `3bbd65d6c49884408086219a364f251ddbd8c9b7` de [PR #57](https://github.com/D3ckardCain/Geelark-IA/pull/57) pasó [Transporte HTTPS #38157876743](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157876743): **83 pruebas aprobadas**, un warning deprecatorio Starlette/httpx y `pip check` correcto. El job instaló la autorización canónica y ejecutó la integración SQLite→HTTPS/TLS loopback→PostgreSQL desechable. No es validación física. Evidencia en [comentario de #57](https://github.com/D3ckardCain/Geelark-IA/pull/57#issuecomment-6111468700).


### Sincronización del supervisor con ciclo de recibos canónico — 2026-10-11

PR #67 se sincronizó con el HEAD validado de #57 mediante [`3b1c21610e7de8d608a967f68daabc7abc5bda30`](https://github.com/D3ckardCain/Geelark-IA/commit/3b1c21610e7de8d608a967f68daabc7abc5bda30). GitHub informa `mergeable=true`, `ahead 5 / behind 0`. Se conservaron CLI/supervisor, proveedores file/systemd, monitor netlink y la base canónica con lifecycle/auth/expiración. CI transporte [#38158083417](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158083417) está en ejecución; revisar el resultado combinado antes de validar.


### CI final del supervisor sobre lifecycle y auth canónica — 2026-10-11

El HEAD `3b1c21610e7de8d608a967f68daabc7abc5bda30` de [PR #67](https://github.com/D3ckardCain/Geelark-IA/pull/67) pasó [Transporte HTTPS #38158083417](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158083417) con **129 pruebas aprobadas**, un warning deprecatorio Starlette/httpx y `pip check` correcto. El workflow instaló auth canónica y transporte; no hay validación física. Reconciliación conservadora permanece en #61. Evidencia en [comentario de #67](https://github.com/D3ckardCain/Geelark-IA/pull/67#issuecomment-6111500419).


### Reconciliación de inventario portado al supervisor canónico — 2026-10-11

PR #61 se sincronizó con #67 mediante [`4d4b5a1e9aac3f6ad8e8f62dc165bd4ae7a4712a`](https://github.com/D3ckardCain/Geelark-IA/commit/4d4b5a1e9aac3f6ad8e8f62dc165bd4ae7a4712a); `ahead 140 / behind 0`, `mergeable=true`. Se resolvió el conflicto de contrato detectado: `POST /agent/v1/reconcile` queda para `assignments`; el inventario local usa `POST /agent/v1/reconcile/inventory`, operación `RECONCILE_INVENTORY` mapeada a autorización canónica `RECONCILE`. La migración se renumeró a `0006_agent_reconciliation_reports.sql` para seguir a `0004_worker_module_inventory.sql` y `0005_agent_task_inbox.sql`.

El worker se portó a `AgentNodeSupervisor`, usa hilo separado, espera un heartbeat exitoso, conserva UUID/snapshot durante reintentos y renueva al reconectar. El proveedor de inventario es opcional y no se activa desde la CLI sin una fuente explícita. CI del HEAD combinado en cola: [transporte #38158919448](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158919448), [esquema #38158919574](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158919574), [persistencia #38158919454](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158919454).


### CI final de reconciliación integrada — 2026-10-11

El código de PR #61 se validó en HEAD `481e9701fabca3cddc0b107203f29d30ad0f3f92`; después solo se añadieron contratos documentales en [commit `38045db`](https://github.com/D3ckardCain/Geelark-IA/commit/38045dbbe3efbd42b22bc6c8694c77619f78269f) y [commit `10f9545`](https://github.com/D3ckardCain/Geelark-IA/commit/10f95457e236275ab1c232e5e5c4ef44f0190e90). Los tres workflows fueron exitosos: [transporte #38159012184](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38159012184) con **154 pruebas aprobadas**, un warning deprecatorio Starlette/httpx y `pip check` correcto; [esquema #38159012165](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38159012165); [persistencia #38159012167](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38159012167). La migración 0006 se aplica después de 0004 Worker y 0005 bandeja. Se separaron las rutas de reconciliación de tareas e inventario; el inventario sigue opt-in mediante callback explícito. Evidencia en [comentario de #61](https://github.com/D3ckardCain/Geelark-IA/pull/61#issuecomment-6111621584).


### Auditoría 11-oct-2026: modelo de reconciliación duplicado en PR #52

En el HEAD previo `2e0f9011e60850aa2d6fd13d140615d7f23921fc` de PR #52, `packages/cluster-agent-transport/src/cluster_agent_transport/app.py` definía `ReconcilePayload` dos veces; la segunda definición sobrescribía la primera en tiempo de importación. La primera dependía de `ReconcileAssignment`, con estados y límites diferentes. Se eliminó el bloque duplicado/no utilizado y se dejó una sola definición con `ReconcileItem`, en [commit `7ce874b20b01c05c7233eb8955fefec78dd4f70b`](https://github.com/D3ckardCain/Geelark-IA/commit/7ce874b20b01c05c7233eb8955fefec78dd4f70b). CI del nuevo SHA queda pendiente hasta consultar sus ejecuciones.

La revalidación también encontró que la base actual de #52 es `feat/master-status-snapshot-provider-v1` (SHA `c5bc7925a83f00d3f021cc73ca196f46300e414f`), no `feat/agent-https-transport` como indicaba el texto anterior. Debe comprobarse la dependencia real en el diff combinado antes de integrar. El CI verde del HEAD anterior no acredita el commit nuevo ni la integración final.


### Auditoría 11-oct-2026: dependencia declarada para la autorización canónica

La policy de transporte en #52 adapta los nombres HTTP a `cluster_agent_auth.authorization`, y el autenticador SQL entrega `expires_at` al principal; por tanto, el contrato de expiración ya se transmite a la política canónica en esta rama. Sin embargo, `packages/cluster-agent-transport/pyproject.toml` no declaraba la distribución `geelark-cluster-agent-auth`, mientras que CI la instalaba manualmente antes del transporte. Se añadió `geelark-cluster-agent-auth>=0.1.0,<0.2.0` a las dependencias del transporte en [commit `1fc6f4ffe41e40a8264075bccd8d5c133c464f49`](https://github.com/D3ckardCain/Geelark-IA/commit/1fc6f4ffe41e40a8264075bccd8d5c133c464f49). Los workflows del nuevo HEAD están en curso: [transporte #38172698726](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698726), [persistencia #38172698723](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698723), [esquema #38172698717](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698717). No marcar validado hasta confirmar su resultado. La instalación local debe instalar primero el paquete interno `packages/cluster-agent-auth`; no se debe asumir que existe publicado en PyPI.


### Resultado CI confirmado de PR #52 tras correcciones — 2026-10-11

Para el HEAD `1fc6f4ffe41e40a8264075bccd8d5c133c464f49`, los tres workflows terminaron correctamente y los jobs consultados no muestran pasos fallidos: [transporte HTTPS #38172698726](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698726), [servicio de persistencia #38172698723](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698723) y [esquema PostgreSQL #38172698717](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698717). El HEAD incluye la eliminación del modelo de reconciliación duplicado y la declaración de dependencia del paquete de autorización. El resultado se registró en el cuerpo y comentarios de [PR #52](https://github.com/D3ckardCain/Geelark-IA/pull/52). La PR sigue draft y su base es `feat/master-status-snapshot-provider-v1`; la integración combinada y validación operativa siguen pendientes.


### Comparación final provisional de PR #54 contra el HEAD corregido de #52 — 2026-10-11

Las pruebas y rutas presentes en #54 parecen estar cubiertas por #52 en el HEAD `1fc6f4ffe41e40a8264075bccd8d5c133c464f49`: claim con lease y nodo activo, denegación de nodos pending, validaciones HTTP/headers, claim concurrente, lease y fencing. El CI de #52 está verde en [transporte #38172698726](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698726), [persistencia #38172698723](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698723) y [esquema #38172698717](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172698717).

No cerrar #54 todavía: #52 sigue en draft y su base/migración (`feat/master-status-snapshot-provider-v1`, migración 0005) difiere de #54 (base transporte, migración 0004). Falta comprobar el diff combinado y la numeración de migraciones antes de declarar formalmente supersesión. Registro en [comentario de #54](https://github.com/D3ckardCain/Geelark-IA/pull/54#issuecomment-6113459412).


### Corrección de topología de ramas y revalidación CI — 2026-10-11

La topología actual de GitHub corrige la descripción previa de #47/#48 como ramas hermanas: #48 está basada en `feat/agent-operation-authorization` (HEAD de #47 `b03d225c5824b51848061bc206c84c888580bcd2`). La cadena actual es **#47 → #48 → #73 → #74 → #52**, con #57 apilada sobre #52. El adaptador de política canónica y la transferencia de expiración están en #73/#74/#52, no deben forzarse en #48 aislada. Corrección registrada en [comentario #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6113470601) y [comentario #73](https://github.com/D3ckardCain/Geelark-IA/pull/73#issuecomment-6113470997).

CI revalidada para los HEAD actuales consultados: #47 `b03d225…` tiene persistencia #38156018743 en success; #48 `a1b2298…` tiene transporte #38156857103, esquema #38156857152 y persistencia #38156857127 en success; #73 `31c93b3…` tiene transporte #38156909185, persistencia #38156909212 y esquema #38156909211 en success; #52 `1fc6f4f…` tiene transporte #38172698726, persistencia #38172698723 y esquema #38172698717 en success; #57 `3bbd65d…` tiene transporte #38157876743 en success; #61 `10f9545…` tiene transporte #38159108522, persistencia #38159107744 y esquema #38159107343 en success. Para #74, en esta consulta solo se confirmó el workflow de persistencia #38157104581 en success; falta demostrar que los workflows de transporte y esquema corrieron en el HEAD exacto `a8ce049458e94ae2587caeb8a42269a0b094b09a` antes de marcar CI integral de #74 como completa.


### Auditoría 11-oct-2026: idempotencia terminal con lease de instancia vencida (#68 → #52)

La comparación de `domain_handlers.py` y sus pruebas encontró una diferencia de seguridad/recuperación que impedía declarar #68 supersedida sin cambios: #68 reconoce un reenvío terminal idéntico aun con la lease de instancia vencida, pero exige mismo propietario y `assignment_epoch`; el HEAD previo de #52 cubría solo el vencimiento de la lease de entrega. Se portó la condición de replay terminal con fencing a #52 en [commit `f5f99b1671cb0978e42c35c73133fb11a4993921`](https://github.com/D3ckardCain/Geelark-IA/commit/f5f99b1671cb0978e42c35c73133fb11a4993921) y se amplió la prueba PostgreSQL en [commit `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`](https://github.com/D3ckardCain/Geelark-IA/commit/3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a) para vencer ambas leases antes del replay y restaurar la lease antes de las comprobaciones de reconciliación. CI del último SHA pendiente; no cerrar #68 hasta validar el test y la denegación después del cambio de epoch. Hallazgo registrado en [comentario de #68](https://github.com/D3ckardCain/Geelark-IA/pull/68#issuecomment-6113486866).


### Coste de GitHub Actions: control de concurrencia y límite de evidencia — 2026-10-11

Se revisaron los workflows de transporte, esquema PostgreSQL, servicio de persistencia y panel Master. Todos configuran `concurrency` con `cancel-in-progress: true` para cancelar validaciones obsoletas de la misma PR/ref. Esto reduce ejecuciones duplicadas, pero no demuestra que el gasto real sea cero: el conector del repositorio no expone los datos de facturación/uso de Actions a nivel de cuenta. Se registró en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6113494486). Para confirmar el objetivo de $0 USD, el propietario debe revisar Billing/Actions y los límites vigentes del plan. En el HEAD actual #52, persistencia #38172963423 y esquema #38172963435 terminaron success; transporte #38172963463 seguía ejecutando pruebas en la última consulta.


### Cierre individual de alternativas supersedidas #54 y #68 — 2026-10-11

Tras comparar los archivos y las pruebas en el sucesor #52, se cerraron individualmente [PR #54](https://github.com/D3ckardCain/Geelark-IA/pull/54) y [PR #68](https://github.com/D3ckardCain/Geelark-IA/pull/68), ambas con comentario de cierre y enlace a [PR #52](https://github.com/D3ckardCain/Geelark-IA/pull/52). #54 queda supersedida por claim durable, leases, seguridad de rutas y pruebas de concurrencia presentes en #52; #68 queda supersedida por replay terminal idempotente con ambas leases vencidas, conflicto de payload y rechazo tras cambio de epoch. El HEAD sucesor `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a` pasó transporte [#38172963463](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963463), persistencia [#38172963423](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963423) y esquema [#38172963435](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963435), todos `completed/success`. Ambos cierres son por supersesión, no por merge; #52 sigue draft y no hay despliegue ni validación en equipos reales.


### Auditoría estática de PR #76: SQL de grants y ACL Windows — 2026-10-11

Se corrigió el delimitador inválido del bloque `DO` en `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql`: commit [7bf92e17a9d9fed2b47932c31b034053f146b375](https://github.com/D3ckardCain/Geelark-IA/commit/7bf92e17a9d9fed2b47932c31b034053f146b375) cambia a `$grant$`. No se ejecutó contra una base real ni se lanzó Actions, porque el workflow de #76 es manual-only para evitar consumo no previsto.

Se registró un pendiente de seguridad en [PR #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6113518962): `_restrict_windows_acl()` quita ACE heredadas y otorga permisos al usuario actual, pero no demuestra que elimine ACE explícitas preexistentes de otros usuarios. Debe endurecerse y probarse la DACL efectiva en Windows antes de declarar protegidos los secretos/SQLite; no se modificó ni instaló nada en el PC-MASTER real. CI del HEAD actual sigue pendiente por diseño manual-only.


El script de rol lector se reforzó también en [commit `9fee5b72900df76193a9aab3bc9868f73abeab1a`](https://github.com/D3ckardCain/Geelark-IA/commit/9fee5b72900df76193a9aab3bc9868f73abeab1a) para fijar `NOBYPASSRLS` al crear/alterar el rol, alineado con la verificación de atributos privilegiados. Sigue pendiente ejecutar la validación real de grants y resolver/probar las ACL NTFS; no se ejecutó Actions ni se tocó la base real.


### Corrección final de estado CI y coste — 2026-10-11

Corrección de la nota anterior de coste: transporte #38172963463 terminó `completed/success`, al igual que persistencia #38172963423 y esquema #38172963435 para el HEAD `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a` de #52. La aclaración quedó en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6113529038). El coste real de Actions sigue sin verificarse porque no hay datos de Billing disponibles en el conector de repositorio.


### PR #76: alcance de revocación/verificación de grants — 2026-10-11

Se identificó un límite adicional del rol lector: el script de preparación y `verify_readonly_role.sql` revisan privilegios sobre `geelark_control`, pero no detectan grants explícitos preexistentes del rol en otros esquemas de usuario. La API ejecuta una consulta fija sobre `geelark_control.nodes`, por lo que no se ha demostrado una ruta de explotación directa; aun así, el rol no puede declararse estrictamente de privilegio mínimo hasta ampliar preparación/verificación a otros esquemas o usar un rol nuevo en una base dedicada. Registrado en [comentario de PR #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6113533519). No se ejecutó SQL contra una base real.


### CI de descendientes tras actualizar la base #52 — 2026-10-11

La base de PR #57 apunta a `feat/agent-task-inbox-v2` (#52), cuyo HEAD avanzó a `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a` después de su CI anterior. El run verde de #57 [#38157876743](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157876743) corresponde a la ejecución asociada a su HEAD `3bbd65d6c49884408086219a364f251ddbd8c9b7`, pero no acredita que el merge result use la base actualizada. Lo mismo aplica a descendientes #59/#67/#61. Antes de integrar, deben revalidarse los merge results actuales y revisarse conflictos de migraciones/contratos. Hallazgo registrado en [comentario de #57](https://github.com/D3ckardCain/Geelark-IA/pull/57#issuecomment-6113535586).


### PR #49 frente al journal v3 actual — 2026-10-11

La rama #38 está en esquema v3 (`task_id`, estado `rejected`, tabla `synced_receipts` y migración v1→v3); la PR #49 sigue en v2 con `controller_ack_at`, sin `task_id` ni `rejected`, y su test afirma `version == 2`. Su CI [#38015505670](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38015505670) pasó en su propio HEAD `936857a0cded51079b94769f09c641751113fb13`, pero no acredita compatibilidad con la base actual. La mejora exclusiva de #49 es validar nodo y `assignment_epoch` al marcar ACK, además de filtrar estados pendientes; #38 ya tiene ACK durable, pero `mark_receipt_synced()` no recibe epoch. No cerrar ni fusionar #49 hasta portar esas salvaguardas al esquema v3, adaptar migraciones/pruebas y validar la pila. Hallazgo registrado en [comentario de #49](https://github.com/D3ckardCain/Geelark-IA/pull/49#issuecomment-6113543879). No se modificó esa rama para no disparar Actions adicionales sin verificar cuota.


### Seguimiento de Issues #50 y #72 — 2026-10-11

Se actualizó [Issue #50](https://github.com/D3ckardCain/Geelark-IA/issues/50#issuecomment-6113553786) con el HEAD de #52, CI verde, prueba de replay terminal con ambas leases vencidas, cierres supersedidos #54/#68 y puertas pendientes para la pila descendiente. Se actualizó [Issue #72](https://github.com/D3ckardCain/Geelark-IA/issues/72#issuecomment-6113554628) con el estado del inventario (#73), proveedor (#74) y panel autenticado (#76), manteniendo la salvedad de CI exacta para el HEAD de #74 y de grants/ACL aún no verificados en operación real.


### PR #76: límite de cuerpo HTTP añadido — 2026-10-11

Se añadió un `BodyLimitMiddleware` con límite de 16 KiB para la API administrativa, incluido el caso de cuerpos sin `Content-Length`, y un test que espera 413 sin reflejar el contenido. Commits: [implementación `f67d17a64276aae650467aa42480d97ca0f60627`](https://github.com/D3ckardCain/Geelark-IA/commit/f67d17a64276aae650467aa42480d97ca0f60627) y [test `4124edc2ea4f0f0bb13978e6e22a93758fef56b9`](https://github.com/D3ckardCain/Geelark-IA/commit/4124edc2ea4f0f0bb13978e6e22a93758fef56b9). CI no se ejecutó porque el workflow es manual-only; no declarar la prueba aprobada hasta ejecutar con cuota confirmada. Continúan pendientes ACL NTFS efectiva y verificación de grants fuera de `geelark_control`.


### PR #74: consulta de snapshot con nombre de columna incorrecto — 2026-10-11

El HEAD actual `a8ce049458e94ae2587caeb8a42269a0b094b09a` de #74 consulta `reported_health_state` como columna física de `geelark_control.nodes`; el esquema real expone `health_state`. La corrección `health_state AS reported_health_state` existe en la rama descendiente #76, pero no en #74. Se registró en [comentario de #74](https://github.com/D3ckardCain/Geelark-IA/pull/74#issuecomment-6113572496). No se modificó #74 para no disparar workflows automáticos hasta verificar la cuota de Actions; no integrar el proveedor de forma independiente hasta portar el alias y probar la consulta real.


### Colisión de numeración ADR en PR #40/#70/#76 — 2026-10-11

La carpeta `docs/decisiones` en `main` contiene ADR-001 a ADR-004. Tres ramas abiertas proponen independientemente ADR-005 para decisiones diferentes: autenticación de agentes (#40), lectura de estado del clúster (#70) y autenticación local PC-MASTER (#76). Se registró en los tres PRs la propuesta de reservar ADR-005 para #40, renumerar #70 a ADR-006 y #76 a ADR-007, actualizando referencias. No se renombraron archivos todavía para no disparar workflows automáticos de documentación sin verificar cuota de Actions. Comentarios: [#40](https://github.com/D3ckardCain/Geelark-IA/pull/40#issuecomment-6113583351), [#70](https://github.com/D3ckardCain/Geelark-IA/pull/70#issuecomment-6113583636), [#76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6113583939).


### Corrección de estado PR #59/#67 — 2026-10-11

La comparación inicial que describía #59 y #67 como ramas complementarias quedó obsoleta: la rama actual #67 (`3b1c21610e7de8d608a967f68daabc7abc5bda30`) incorpora `credentials.py`, `SystemdCredentialProvider`, `bootstrap.py`, CLI/configuración, `AgentNodeSupervisor` y monitor netlink. PR #59 está cerrada como sustituida por #67 (comentario de cierre #6107033798). El HEAD actual de #67 tiene CI [#38158083417](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158083417) `completed/success`, con 129 pruebas, un warning deprecatorio y `pip check` correcto. Se corrigió la nota en [comentario de #67](https://github.com/D3ckardCain/Geelark-IA/pull/67#issuecomment-6113593229). No hay merge ni despliegue.


### Aclaración: CI de #67/#61 anterior al último avance de #52 — 2026-10-11

Aunque #67 [#38158083417](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158083417) y #61 [#38159108522](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38159108522) (junto con los otros workflows de #61) terminaron success para sus HEADs, esas ejecuciones son anteriores al último avance de #52 a `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`. No acreditan el merge result actual de la pila descendiente; revalidar #57/#67/#61 con la base actualizada antes de integrar. Comentarios: [#67](https://github.com/D3ckardCain/Geelark-IA/pull/67#issuecomment-6113595941), [#61](https://github.com/D3ckardCain/Geelark-IA/pull/61#issuecomment-6113596241).


### Reconciliación de la pila descendiente #57 y seguridad ACL de PC-MASTER — 2026-10-11

**PR #57:** `compare_commits` entre el HEAD canónico #52 (`3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`) y el HEAD de #57 (`3bbd65d6c49884408086219a364f251ddbd8c9b7`) informa `diverged`: #57 tiene 6 commits propios y le faltan 4 commits del #52 actual. La CI verde de #57 corresponde a su SHA propio, no al árbol combinado vigente. Archivos con cambios concurrentes incluyen `docs/ESTADO_PROYECTO.md`, README y `__init__.py`; sincronizar sin perder los tests de lifecycle y SQLite→HTTPS→PostgreSQL y ejecutar CI antes de integrar. Hallazgo: [comentario #57](https://github.com/D3ckardCain/Geelark-IA/pull/57#issuecomment-6114064984).

**PR #76:** se corrigió `_restrict_windows_acl()` para restablecer la ACL existente (`icacls /reset`) antes de desactivar herencia y conceder acceso al usuario actual. Se añadieron tests mock para archivos/directorios y fallo cerrado. Commits: [implementación](https://github.com/D3ckardCain/Geelark-IA/commit/26121a632fba74eb046a085f3a47a598a69b3393), [tests](https://github.com/D3ckardCain/Geelark-IA/commit/5bf01714394493d034258d028cb225428284fb4d), [fixture](https://github.com/D3ckardCain/Geelark-IA/commit/d74f70d40fafefbf2a0af2f8da7ec2b6af76682f). La ejecución de persistencia #38177200860 se encontraba en curso al registrar. Esto no demuestra ACL efectiva segura en Windows; hace falta CI completa y validación DACL real en Windows. Hallazgo: [comentario #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6114065390).


### Resultado del workflow incidental y divergencia #74/#76 — 2026-10-11

El workflow de persistencia [#38177200860](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38177200860) terminó `completed/success`: migraciones, integración/concurrencia, suites guard/auth y `pip check` pasaron. **No ejecuta** `packages/cluster-master-admin/tests`, por lo que no valida las nuevas pruebas mock de ACL. No se ejecutó el workflow manual-only de administración para no consumir minutos sin confirmar la cuota.

La comparación de #74 HEAD `a8ce049458e94ae2587caeb8a42269a0b094b09a` con #76 HEAD `d74f70d40fafefbf2a0af2f8da7ec2b6af76682f` devuelve `diverged` (81 commits únicos de #76, 32 commits de #74 ausentes según la comparación). #76 sí contiene `health_state AS reported_health_state`, pero la divergencia indica que no debe asumirse que su árbol incluye todos los cambios recientes de #74. Antes de integrar: reconciliar la historia/árbol, ejecutar pruebas del proveedor y schema en un único HEAD y validar la DACL efectiva en Windows. Registro en [comentario #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6114072448).


### Comparación de journal offline #38/#49 — 2026-10-11

La comparación de commits de #38 (`e37e5aaef72837c19837eb5b648c29f05ae9b3c3`) con #49 (`936857a0cded51079b94769f09c641751113fb13`) da `diverged`: #49 tiene 4 commits propios y le faltan 13 de #38. No son duplicados idénticos. #38 ya conserva el esquema v3 con `rejected`, `task_id` y reinicia el ACK cuando cambia el resultado/progreso; #49 aporta filtro configurable de estados y exige `assignment_epoch` al confirmar entrega, mientras #38 `mark_receipt_synced()` solo recibe `operation_id`. El run [#38015505670](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38015505670) pasó en el HEAD de #49, pero no valida el árbol combinado. Próxima decisión: portar las dos garantías exclusivas y pruebas a #38, conservar migraciones v3, ejecutar CI solo tras revisar cuota, y entonces determinar si #49 queda supersedida. Registro: [comentario #49](https://github.com/D3ckardCain/Geelark-IA/pull/49#issuecomment-6114086702).

### Evidencia adicional de ejecuciones redundantes de Actions — 2026-10-11

El commit que ajustó el fixture en `packages/cluster-master-admin/tests/test_auth.py` dentro de la PR apilada #76 provocó la ejecución de [Cluster persistence service #38177200860](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38177200860), porque el diff total de esa PR incluye cambios en `packages/cluster-persistence/**`. El job pasó, pero no ejecutó tests del paquete `cluster-master-admin`. Esto demuestra que los pushes repetidos a ramas apiladas pueden gastar minutos aunque el archivo editado no pertenezca al workflow; se registró en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6114090257). Mitigación inmediata: agrupar cambios y no volver a hacer push a #76 hasta revisar la cuota; mantener su workflow específico manual-only. El gasto real sigue sin verificarse en Billing.


### Reconciliación pendiente de la cadena base → asignaciones → outbox → journal → auth — 2026-10-11

Comparaciones de HEAD actuales (no se ha modificado ninguna base de PR):
- #32 → #34: `diverged`, #34 tiene 29 commits propios y le faltan 7 de #32; diff común en migración `0001_cluster_control.sql`, servicio, dominio, tests y workflows. [Comentario #34](https://github.com/D3ckardCain/Geelark-IA/pull/34#issuecomment-6114097322).
- #34 → #36: `diverged`, #36 tiene 12 commits propios y le faltan 3 de #34; diff en outbox, tests y workflows. [Comentario #36](https://github.com/D3ckardCain/Geelark-IA/pull/36#issuecomment-6114097619).
- #36 → #38: `diverged`, #38 tiene 33 commits propios y le faltan 5 de #36; diff en journal/tests y workflows. [Comentario #38](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6114097979).
- #38 → #42: `diverged`, #42 tiene 3 commits propios y le faltan 13 de #38; diff en migración `0002_agent_auth.sql`, smoke test y manual. [Comentario #42](https://github.com/D3ckardCain/Geelark-IA/pull/42#issuecomment-6114098269).

Estas diferencias no prueban por sí solas que falte cada cambio funcional (algunas ramas pueden haber portado cambios manualmente), pero sí impiden tratar la cadena como lineal o dar por validado el árbol final con CI de cada SHA por separado. Próximo trabajo: inventariar diferencias funcionales exclusivas por PR, decidir la única secuencia de migraciones y sincronizar un nivel a la vez, solo después de revisar cuota de Actions. Ninguna PR se fusionó o cerró.

### Rama inicial de contratos #16 desactualizada respecto de main — 2026-10-11

La comparación de `main` actual (`f62fd1163fcb45e338978b6d8f777135dc87584b`) con HEAD #16 (`6fa17c579b7743e75a205bfb09619dd28b337307`) devuelve `diverged`: 20 commits propios de #16 y 12 commits recientes de `main` ausentes. El diff visible se concentra en `.github/workflows/cluster-contracts.yml`, `packages/cluster-contracts/{README.md,pyproject.toml}`, modelos, máquina de estados y tests. #28 y #30 dependen de este HEAD, así que una sincronización debe hacerse primero en #16 y luego validar sus descendientes. No se modificó la base para evitar disparar CI sin verificar cuota. Hallazgo: [comentario #16](https://github.com/D3ckardCain/Geelark-IA/pull/16#issuecomment-6114103278).

### Corte de auditoría del repositorio — 2026-10-11

Consulta de GitHub al corte: **27 PR abiertas** y **40 Issues abiertas** (incluye PR en draft; Issues no incluyen PRs). Este conteo es una instantánea, no una métrica permanente.

Bloqueos prioritarios confirmados:
1. Sincronizar la cadena #32 → #34 → #36 → #38 → #42 en orden, revisando árbol y migraciones, porque cada comparación sucesiva devuelve `diverged`.
2. Portar a #38 las garantías exclusivas del journal #49 (filtro de estados y ACK validado por epoch) antes de decidir supersesión.
3. Sincronizar #57 con el HEAD vigente de #52 antes de validar la integración de ciclo de vida.
4. Validar la seguridad ACL de #76 con pruebas propias de `cluster-master-admin` y DACL efectiva Windows; el workflow de persistencia no cubre esas pruebas.
5. Mantener el control de coste: no hay acceso a facturación real de Actions desde el conector; no afirmar $0 facturado sin comprobar Billing.

En esta auditoría no se fusionó ni cerró ninguna PR/Issue, no se desplegó ningún servicio y no se tocó hardware ni base de datos del usuario. La única ejecución automática incidental observada en el trabajo ACL (#38177200860) terminó `success`, pero no validó el paquete de administración.

### Revalidación de dependencias y seguridad — 2026-10-11

**PR #52 y #54/#68:** la situación evolucionó desde la alerta anterior. #54 y #68 aparecen cerradas individualmente como supersedidas por #52. El HEAD actual de #52 es `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`, con base `feat/master-status-snapshot-provider-v1` (`c5bc7925a83f00d3f021cc73ca196f46300e414f`). La migración `0005_agent_task_inbox.sql` (blob `c1468c0…`) se encuentra después de `0004_worker_module_inventory.sql` (blob `8fcec1e…`), por lo que la alerta anterior sobre duplicación entre #52/#54 queda resuelta por el cierre de #54 y la secuencia que declara #52. Los tres workflows del HEAD actual de #52 (`#38172963463`, `#38172963423`, `#38172963435`) terminaron `completed/success`. Los tests de PostgreSQL del HEAD cubren claim/concurrencia, fencing por epoch, rechazo de epoch obsoleto y conflicto/idempotencia de operaciones. #52 sigue draft; no hay merge ni validación física.

**PR #57 sobre #52:** el HEAD #57 (`3bbd65d6c49884408086219a364f251ddbd8c9b7`) y el HEAD #52 (`3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`) están `diverged`: #57 tiene 6 commits propios y está 4 commits detrás de #52 (merge-base `2e0f9011e60850aa2d6fd13d140615d7f23921fc`). El workflow de #57 pasó con 83 pruebas en su SHA, pero no valida el código actualizado de #52. Debe reconciliarse la rama antes de afirmar integración.

**PR #38 y #49 (journal offline):** #49 y #38 divergen desde `707e9b643f9ffee07c34b3106173d92f99d163b6`; #49 tiene 4 commits propios y carece de 13 commits de #38. #38 ya tiene esquema v3, `task_id`, `synced_receipts` y filtro de estados; #49 aporta selección configurable de estados y un ACK que valida `assignment_epoch`, mientras que #38 expone `mark_receipt_synced(operation_id)` sin epoch explícito y el runtime descendiente usa esa firma. Se requiere integrar esa garantía con pruebas y actualizar consumidores; no se debe sustituir el journal v3 por el v2 de #49.

**PR #76 (API local de PC-MASTER):** el workflow `cluster-master-admin.yml` es manual (`workflow_dispatch`) para evitar minutos automáticos. No se encontró una ejecución de ese workflow para HEAD `d74f70d40fafefbf2a0af2f8da7ec2b6af76682f`; el run #38177200860 pertenece a persistencia y no acredita la seguridad de la API. El SQL de verificación de privilegios es manual; no afirmar validación efectiva de ACL hasta ejecutarlo de forma controlada con cuota verificada o implementar una prueba aislada de permisos.

Comentarios con evidencias: [PR #57](https://github.com/D3ckardCain/Geelark-IA/pull/57#issuecomment-6114244700), [PR #49](https://github.com/D3ckardCain/Geelark-IA/pull/49#issuecomment-6114245023), [PR #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6114245306). No se fusionó, desplegó ni ejecutó el workflow manual; se evitó consumir minutos adicionales sin información de cuota.


## Revalidación de CI, supersesión e instalación de autorización — 2026-10-11

### Estado corregido de alternativas cerradas
La consulta actual confirma que PR #54 y #59 están cerradas sin merge. #54 se declara supersedida por #52; el HEAD actual de #52 `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a` pasó los tres workflows: [transporte #38172963463](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963463), [persistencia #38172963423](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963423), [esquema #38172963435](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963435). #59 se declara sustituida por #67; el HEAD actual `3b1c21610e7de8d608a967f68daabc7abc5bda30` pasó [transporte #38158083417](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38158083417) con 129 pruebas reportadas. Cierres sin merge, no equivalen a despliegue ni validación física.

### Autorización #47 → #48
La topología actual ya apila #48 sobre #47. La policy del transporte importa `cluster_agent_auth.authorization`, mapea operaciones de ruta a la policy canónica y pasa `credential_expires_at`; `db_auth.py` devuelve `c.expires_at` tras filtrar vencidas en PostgreSQL. Para el HEAD anterior `a1b2298d2dc5385a792dd5dec65a69b2e51cce10`, los workflows [esquema #38156857152](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857152), [transporte #38156857103](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857103) y [persistencia #38156857127](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38156857127) pasaron. Se corrigió la documentación de instalación local en commit [f653c95](https://github.com/D3ckardCain/Geelark-IA/commit/f653c95e7c050f308738ec6279dd6b739d575c94) para instalar explícitamente auth antes del transporte. Este nuevo HEAD aún necesita confirmación de CI; no reutilizar el resultado del SHA anterior como si fuera evidencia del nuevo commit. Hallazgo registrado en [comentario #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6114247882).

### PC-MASTER #76 — límites de prueba ACL
La PR #76 mantiene workflow manual-only para evitar consumo/cargos de Actions. En el HEAD `d74f70d40fafefbf2a0af2f8da7ec2b6af76682f`, la prueba de ACL Windows simula `whoami.exe` e `icacls.exe`; verifica argumentos pero no la DACL efectiva del sistema. Por ello la protección de credenciales Windows no se considera validada operativamente. Se requiere una prueba Windows con coste revisado o comprobación manual controlada de permisos efectivos, sin credenciales reales. No se ejecutó workflow manual ni se instaló/inició el panel. Ver [comentario #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6114248121).

### Límites de coste y acciones
No hay acceso a la facturación real de Actions desde el conector; no afirmar coste real de $0 solo por CI verde. No se fusionó ni desplegó ninguna PR en esta revalidación. Los cierres preexistentes #54/#59 se registran como cierres documentados por supersesión, no como merge.


### Revalidación de la cadena de persistencia #32 → #34 → #36 → #38 → #42 — 2026-10-11

Se compararon los HEAD actuales (no solo los títulos ni las bases declaradas):

- **#32 → #34:** `diverged`; #34 tiene 29 commits exclusivos y está 7 detrás de #32; merge-base `54e35fa42d335e0f0e91c099de72e86a49df3cf2`. Cambios incluyen workflow y migración `0001_cluster_control.sql`, además del servicio.
- **#34 → #36:** `diverged`; #36 tiene 12 commits exclusivos y está 3 detrás de #34; merge-base `ef56529f943394d3c3b6fb7c185876760e173945`.
- **#36 → #38:** `diverged`; #38 tiene 33 commits exclusivos y está 5 detrás de #36; merge-base `208c5a29e8eb0790ba7f3ef70e68dd3caf08412b`. #38 aporta el journal SQLite v3, `task_id` y fencing/deduplicación.
- **#38 → #42:** `diverged`; #42 tiene 3 commits exclusivos y está 13 detrás de #38; merge-base `707e9b643f9ffee07c34b3106173d92f99d163b6`. #42 añade migración `0002_agent_auth.sql` y pruebas de humo.

Los workflows de cada HEAD listado terminaron success en sus propios SHAs, pero no existe evidencia de CI de la pila consolidada. Se añadieron comentarios con los conteos y pasos requeridos en [#34](https://github.com/D3ckardCain/Geelark-IA/pull/34#issuecomment-6114248845), [#36](https://github.com/D3ckardCain/Geelark-IA/pull/36#issuecomment-6114249187), [#38](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6114249529) y [#42](https://github.com/D3ckardCain/Geelark-IA/pull/42#issuecomment-6114249887). No se cambió ninguna base ni se disparó CI adicional: el orden seguro es reconciliar cada rama, revisar migraciones/contratos y ejecutar las pruebas en el HEAD combinado, sin cierres automáticos.


### CI final de la corrección de instalación de #48 — 2026-10-11

Actualización de la nota anterior: el commit `f653c95e7c050f308738ec6279dd6b739d575c94` ya tiene tres workflows `completed/success`: [esquema #38178437802](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38178437802), [persistencia #38178437815](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38178437815) y [transporte #38178437890](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38178437890). La corrección del README de transporte —instalar primero `cluster-agent-auth` y luego el transporte— queda validada en CI para ese SHA. [Comentario de seguimiento en #48](https://github.com/D3ckardCain/Geelark-IA/pull/48#issuecomment-6114251685). La CI no prueba despliegue ni seguridad operativa en el host real.


### Contratos de clúster #16/#28/#30 — 2026-10-11

La comparación confirma que #16 está `diverged` de `main` actual (`f62fd1163fcb45e338978b6d8f777135dc87584b`): 20 commits exclusivos de la PR y 12 commits de main ausentes; merge-base `5b339c7c016725118070c0d5a3d3404a7d8b28ea`. El diff toca el workflow, modelos y máquina de estados. #28 depende de ese HEAD y añade simulador/tests; #30 es rama hermana que endurece validación y también modifica `models.py`. Comparar #28 con #30 devuelve `diverged` (4 commits exclusivos de #30, 5 de #28; merge-base #16). Las tres CI históricas (#38000986766, #38005289762 y #38006188257) pasaron en sus HEADs consultados, pero no prueban la combinación actualizada. Comentarios registrados en [#16](https://github.com/D3ckardCain/Geelark-IA/pull/16#issuecomment-6114254175), [#28](https://github.com/D3ckardCain/Geelark-IA/pull/28#issuecomment-6114254571) y [#30](https://github.com/D3ckardCain/Geelark-IA/pull/30#issuecomment-6114254922). Secuencia segura: sincronizar #16 con main, luego integrar #28 y #30 en rama temporal y validar conjuntamente. No se cambió base ni se disparó CI adicional.


### Bloqueo de divergencia entre bandeja durable #52 y sincronización #57 — 2026-10-11

Comparación actual de GitHub: base #52 HEAD `3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`; consumidor #57 HEAD `3bbd65d6c49884408086219a364f251ddbd8c9b7`. Resultado `diverged`, `ahead_by=6`, `behind_by=4`, merge-base `2e0f9011e60850aa2d6fd13d140615d7f23921fc`. El diff relevante de #57 contiene `lifecycle.py`, `test_lifecycle.py`, `test_receipt_sync_postgres_integration.py` y manuales, mientras #52 tiene cuatro commits más recientes de inbox. Por tanto, el CI previo de #57 no valida la integración con el HEAD actual de #52.

Acción registrada en [#57](https://github.com/D3ckardCain/Geelark-IA/pull/57#issuecomment-6114260441) y [#52](https://github.com/D3ckardCain/Geelark-IA/pull/52#issuecomment-6114260847): sincronizar la rama de recibos sobre la bandeja actual, preservar ambos conjuntos de pruebas y ejecutar workflows en el HEAD combinado. No se ha modificado la historia de las ramas ni se ha fusionado ninguna PR. Mantener ambas en draft hasta que CI combinado y revisión de seguridad pasen.


### Bloqueo de historial del journal #38/#49 — 2026-10-11

PR #49 aparece `mergeable=false`. Comparación entre #38 HEAD `e37e5aaef72837c19837eb5b648c29f05ae9b3c3` y #49 HEAD `936857a0cded51079b94769f09c641751113fb13`: `diverged`, 4 commits exclusivos de #49, 13 exclusivos del journal base, merge-base `707e9b643f9ffee07c34b3106173d92f99d163b6`. #49 extiende el journal con ACK de recibos y una migración documentada v1→v2, mientras el journal actual de #38 ya está en v3 y contiene `task_id`; no se puede asumir que ambas migraciones/contratos se combinen sin rebase y pruebas específicas. Hallazgo registrado en [#49](https://github.com/D3ckardCain/Geelark-IA/pull/49#issuecomment-6114266840) y [#38](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6114267245). Acción: sincronizar historial y validar migración, filtros, ACK por epoch y flujo de recibos antes de integrar. No se cambió la rama ni se fusionó nada.


### Reconciliación de inventario, snapshots y supervisor — 2026-10-11

- **#73 inventario Worker:** HEAD `31c93b3ab54f91d357b7cd16bba9d205e277deab` es 14 commits por delante de la base actual de transporte `a1b2298d2dc5385a792dd5dec65a69b2e51cce10`, sin commits faltantes. CI de esquema #38156909211, servicio #38156909212 y transporte #38156909185 completó en success.
- **#74 proveedor de snapshots:** HEAD `a8ce049458e94ae2587caeb8a42269a0b094b09a` es 3 commits por delante de #73. El único run asociado a este HEAD es persistencia #38157104581 en success; no hay evidencia de runs de transporte/esquema para ese SHA. El contrato JSON Master/Worker es idéntico al de #70 (blob `d7f5975aebf3ac605e1afa5bee75d1674636fb62`).
- **#61 reconciliación/supervisor:** CI de su HEAD `10f95457e236275ab1c232e5e5c4ef44f0190e90` pasó en los tres workflows (#38159107744, #38159108522, #38159107343), pero el HEAD no contiene cuatro commits de #52 posteriores al merge-base `2e0f9011e60850aa2d6fd13d140615d7f23921fc`. Los commits faltantes cambian `app.py`, `domain_handlers.py`, `pyproject.toml` y pruebas PostgreSQL; `domain_handlers.py` tiene blobs diferentes en #52 y #61. Hay que reconciliar antes de declarar integrada la bandeja con el supervisor.

Hallazgos comentados en [PR #61](https://github.com/D3ckardCain/Geelark-IA/pull/61), [PR #73](https://github.com/D3ckardCain/Geelark-IA/pull/73) y [PR #74](https://github.com/D3ckardCain/Geelark-IA/pull/74). No se ejecutaron workflows manuales, ni se fusionaron o desplegaron ramas.


### Revisión formal de PRs y control de coste Actions — 2026-10-11

Se consultaron reviews y review threads de PR #38, #48, #52, #57 y #76: el conector devuelve cero reviews formales y cero threads inline en esas cinco PRs. Los hallazgos técnicos y decisiones están registrados en comentarios de conversación y el registro central; sigue pendiente una revisión independiente humana antes de integrar.

El HEAD de #52 y el de #61 tienen cada uno tres workflows exitosos asociados. #76 usa `workflow_dispatch` para evitar minutos automáticos. No hay acceso desde el conector a la facturación/uso de Actions, por lo que **no se puede afirmar que el gasto real sea $0**. Se mantiene la política conservadora: no ejecutar workflows manuales ni reintentos sin revisar antes Billing/usage; mantener cancelación de runs redundantes y evaluar filtros `paths` solo con matriz de dependencias para no omitir pruebas críticas. Hallazgo registrado en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6114273401).


### Control de coste y divergencias pendientes — actualización 11-oct-2026

Se dejó comentario en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6114272784): `concurrency.cancel-in-progress` y filtros de rutas reducen ejecuciones redundantes, pero no certifican coste real cero; el conector no expone Billing/Actions usage. Para no arriesgar cargos mientras se revisa la cuota, continuar revisión estática y documentación; evitar commits nuevos en ramas de código que disparen CI hasta verificar el uso disponible. No deshabilitar workflows sin decisión explícita.

Se actualizaron [Issue #50](https://github.com/D3ckardCain/Geelark-IA/issues/50#issuecomment-6114272069) e [Issue #37](https://github.com/D3ckardCain/Geelark-IA/issues/37#issuecomment-6114272428) con dos bloqueos vigentes: (1) #57 diverge del HEAD actual #52, seis commits propios y cuatro commits recientes de #52 ausentes; (2) #49 está `mergeable=false` y diverge del journal actual #38, por lo que la migración ACK v1→v2 no puede asumirse compatible con journal v3. No se ha fusionado ninguna rama ni se han disparado nuevas pruebas tras estos comentarios.


### Corrección de estado de la reconciliación — 2026-10-11

La nota histórica de que la reconciliación seguía totalmente deshabilitada/503 quedó desactualizada. En el HEAD vigente de #52 (`3d54bab99b4b5acdba8f6c0a1c821a0ba31e143a`), `domain_handlers.reconcile()` compara asignaciones por identificadores, nodo, epoch, propietario y lease; devuelve `read_only: true`, `mutations_applied: 0` y exige revisión del operador ante conflictos o epoch obsoleto. No modifica estados de tareas/operaciones/instancias. La Issue #50 se actualizó para distinguir esta reconciliación read-only, ya implementada en #52, de la reconciliación de inventario añadida en #61, cuya integración sigue pendiente por la divergencia de cuatro commits con el HEAD actual de #52. Antes de validar #61, comprobar que sus escrituras están limitadas a `agent_reconciliation_reports` y que no alteran tareas/operaciones. Evidencia registrada en [Issue #50](https://github.com/D3ckardCain/Geelark-IA/issues/50#issuecomment-6114278285).


### Divergencia entre asignaciones #34 y dispatcher outbox #36 — 2026-10-11

La comparación de los HEAD actuales muestra `diverged`: #34 `2a0bfe691106be3698eec73c717fb7df48e8d0ce`; #36 `afad1a49570c6ad1851f17230cd26fcda7bcadea`; merge-base `ef56529f943394d3c3b6fb7c185876760e173945`. #36 tiene 12 commits exclusivos y le faltan 3 commits de #34. Los workflows de #36 sí pasaron en su HEAD (#38010153057 esquema, #38010153246 persistencia), pero no prueban compatibilidad con los cambios recientes de asignaciones. Se registró en [#36](https://github.com/D3ckardCain/Geelark-IA/pull/36#issuecomment-6114278802), [#34](https://github.com/D3ckardCain/Geelark-IA/pull/34#issuecomment-6114279210) y [Issue #35](https://github.com/D3ckardCain/Geelark-IA/issues/35#issuecomment-6114279629). Antes de integrar, sincronizar la rama y volver a validar transacciones, leases, reintentos, dead-letter y fencing. No se modificaron ramas ni se fusionó nada.


### Divergencia entre esquema #32 y servicio de asignaciones #34 — 2026-10-11

Comparación actual: #32 HEAD `ce19821a2e0814b9cae2b76a82309089da83c664`; #34 HEAD `2a0bfe691106be3698eec73c717fb7df48e8d0ce`; resultado `diverged`, 29 commits exclusivos de #34 y 7 commits más recientes de #32 ausentes, merge-base `54e35fa42d335e0f0e91c099de72e86a49df3cf2`. El servicio #34 pasa CI en su propio HEAD, pero no se considera validado contra el esquema actual. Hallazgo registrado en [#34](https://github.com/D3ckardCain/Geelark-IA/pull/34#issuecomment-6114283837), [#32](https://github.com/D3ckardCain/Geelark-IA/pull/32#issuecomment-6114284281) y [Issue #31](https://github.com/D3ckardCain/Geelark-IA/issues/31#issuecomment-6114284668). Sincronizar DDL y servicio antes de integración; verificar que `0001_cluster_control.sql` no se duplique y ejecutar smoke tests PostgreSQL, rollback, concurrencia, idempotencia y fencing sobre un único HEAD. No se modificaron ramas ni se fusionó nada.


### Riesgo de interrupción en migración SQLite v2→v3 — 2026-10-11

En `AgentJournal.initialize()` de #38, la rama `version == 2` ejecuta `ALTER TABLE operation_receipts ADD COLUMN task_id TEXT` y después registra la versión 3 en `schema_migrations`, con `isolation_level=None` y sin una transacción explícita que agrupe ambas sentencias. Una interrupción entre ellas puede dejar la columna creada pero la versión en 2; el siguiente inicio reintenta el `ALTER TABLE` y puede fallar por columna duplicada. El test actual valida v1→v3, pero no v2→v3 ni recuperación desde ese estado parcial. Bloqueo registrado en [PR #38](https://github.com/D3ckardCain/Geelark-IA/pull/38#issuecomment-6114289744). Corrección requerida antes de declarar el journal migrable: hacer v2→v3 transaccional o detectar columna existente de forma segura, y probar migración v2, preservación de `synced_receipts`, reapertura e interrupción simulada. No se modificó código ni se disparó CI adicional debido a la restricción de coste $0 y falta de acceso a Billing.


### Verificación de ramas de contratos y autenticación; PR documental del SO — 2026-10-11

- PR #30 está correctamente apilada sobre el HEAD de #16: comparación `ahead 4 / behind 0`, merge-base igual al HEAD de #16. CI de contratos para #30 (`8be0020316dd627d5f2c88e9a9bd287904e3c1ca`) terminó success en [run #38006188257](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38006188257); #16 también pasó su suite en [run #38000986766](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38000986766). Esto valida los contratos y sus pruebas, no la integración con persistencia/agentes.
- PR #44 está correctamente apilada sobre #42: comparación `ahead 21 / behind 0`, merge-base igual al HEAD de #42. CI del servicio de autenticación para #44 terminó success en [run #38012174016](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38012174016); #42 tiene CI verde de esquema/persistencia (#38010243600 y #38010243545). Queda pendiente seguridad operativa y despliegue.
- PR #60 solo modifica documentación de decisiones/POC del host y no tiene ejecución de CI para el HEAD `85ca3bdaf988e08a22bc0208a9559ad78370b1a8`; no se etiqueta como CI aprobada. Su propio cuerpo prohíbe instalaciones, cambios BIOS/UEFI o discos sin autorización explícita.

Se continúa revisión estática mientras no se confirme la cuota de Actions; no se lanzan workflows manuales ni se hacen commits de código que disparen CI sin esa verificación.


### Hallazgo de mínimo privilegio en verificación del rol PC-MASTER — 2026-10-11

La revisión estática de `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` y `verify_readonly_role.sql` detectó que ambos limitan las comprobaciones a `geelark_control`. La verificación no recorre todos los esquemas no sistémicos para detectar grants directos o efectivos vía `PUBLIC` sobre otras tablas/secuencias ni `EXECUTE` sobre funciones. En una base preexistente, eso no demuestra que `geelark_master_reader` carezca de permisos fuera del esquema esperado. Hallazgo registrado en [PR #76](https://github.com/D3ckardCain/Geelark-IA/pull/76#issuecomment-6114296576). Antes de usar el rol en PC-MASTER, ampliar la verificación global o limitar explícitamente el alcance del script y exigir un rol nuevo/dedicado; no ejecutar contra la base real sin autorización. La PR permanece draft y su workflow manual-only no se ejecutó.


### Revisión formal completa de PRs abiertas — 2026-10-11

Se consultaron reviews y threads inline en las 27 PR abiertas devueltas por GitHub. Resultado: **1 review formal en estado `COMMENTED` (#16), 0 threads inline y 0 threads sin resolver**; las otras 26 PR no tienen reviews formales registradas. La review #16 la publicó el propio usuario/propietario del repositorio y enumera seis áreas pendientes: rechazar NaN/infinito, unicidad de identificadores, límites de colecciones/texto, matriz de resultados UNKNOWN/REJECTED, transiciones de estado y reproducibilidad de dependencias. No es una aprobación independiente. Por tanto, aunque las CI de varias ramas estén verdes, no existe evidencia de aprobación técnica independiente en las PR consultadas. El resumen de control de coste se mantiene en [Issue #63](https://github.com/D3ckardCain/Geelark-IA/issues/63#issuecomment-6114273401).


### Revalidación del contrato de salud reportada/derivada — Issue #71 — 2026-10-11

El código actual de la pila #52/#73/#74 separa el dato del Worker (`reported_health_state`) del estado derivado (`health_state`). `domain_handlers.py` guarda el primero y calcula el segundo con `last_seen_at`; `status_snapshot.py` vuelve a derivar el estado según frescura del heartbeat. La suite de snapshots incluye pruebas para heartbeat ausente/vencido, reporte `unknown`, timestamp futuro y rechazo del esquema cuando un snapshot stale afirma `healthy`. CI de #52 pasó en [transporte #38172963463](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963463), [persistencia #38172963423](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963423) y [esquema #38172963435](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38172963435); #74 pasó en [#38157104581](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38157104581). [Comentario actualizado en Issue #71](https://github.com/D3ckardCain/Geelark-IA/issues/71#issuecomment-6114301919).

Issue #71 permanece abierta porque la divergencia de #57 frente a #52 impide validar el stack completo y aún hay que verificar en la integración del panel que el dato reportado no se presenta como autoritativo y que telemetría de un nodo pending no cambia su autorización ni lo convierte en operativo.


### Seguimiento de la review de contratos #16/#30 — 2026-10-11

La review formal `COMMENTED` de #16 enumeró seis áreas. La rama de #30 está apilada limpiamente sobre el HEAD de #16 (`ahead 4 / behind 0`) y cubre con código/pruebas cinco: rechazo de floats no finitos, unicidad de IDs, límites de colecciones/textos, combinaciones de resultados y transiciones exhaustivas. CI #30 pasó en [#38006188257](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38006188257). Falta una decisión explícita sobre reproducibilidad de dependencias (constraints/lock o política de actualización); la review original no es aprobación independiente y los contratos puros no validan propiedad/epoch transaccional. Registrado en [#30](https://github.com/D3ckardCain/Geelark-IA/pull/30#issuecomment-6114315861) y [#16](https://github.com/D3ckardCain/Geelark-IA/pull/16#issuecomment-6114316197). Issue #15 permanece abierta.
