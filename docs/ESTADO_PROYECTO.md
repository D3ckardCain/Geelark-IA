# Estado del proyecto GeeLark-IA

**Actualizado:** 2026-10-24  
**Estado operativo:** ningún módulo se considera aceptado para producción; la aceptación manual de PC-MASTER en Windows sigue pendiente en [issue #77](https://github.com/D3ckardCain/Geelark-IA/issues/77).  
**Integración candidata:** la PR #117 combina el panel autenticado, snapshots y bandeja durable; permanece en draft y sin fusionar. Su CI verde no sustituye las pruebas manuales ni la revisión de seguridad.  
**Workers:** la adopción independiente de redroid está especificada en [issue #118](https://github.com/D3ckardCain/Geelark-IA/issues/118) y bloqueada por la aceptación de #77. Los nodos pendientes no deben ejecutar tareas.  
**Android:** redroid es el motor candidato acordado; no arrancar contenedores ni instalar imágenes hasta resolver el bloqueo de seguridad [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27). La investigación de imágenes ligeras sigue abierta en [#119](https://github.com/D3ckardCain/Geelark-IA/issues/119).  
**Seguridad temporal y del agente:** heartbeat obsoleto [#120](https://github.com/D3ckardCain/Geelark-IA/issues/120); leases de tareas [#121](https://github.com/D3ckardCain/Geelark-IA/issues/121); anti-replay [#124](https://github.com/D3ckardCain/Geelark-IA/issues/124); salud/frescura del estado propio [#125](https://github.com/D3ckardCain/Geelark-IA/issues/125); lease de asignación [#126](https://github.com/D3ckardCain/Geelark-IA/issues/126); TTL y reloj de autorización [#127](https://github.com/D3ckardCain/Geelark-IA/issues/127). Las correcciones de reloj y los fallbacks locales obligatorios están validados en CI en `4081f37abfe9f0071fbc2ea2eaf2b723d07f2faf`. Sigue abierto el diseño de lease local segura ante desfase/reinicio [#128](https://github.com/D3ckardCain/Geelark-IA/issues/128), además de la semántica de `health_state` [#71](https://github.com/D3ckardCain/Geelark-IA/issues/71); no conectar ejecución real hasta resolverlos.  

> **Nota de vigencia:** las secciones posteriores de este documento contienen apuntes históricos desde el 2026-10-09 y aún incluyen decisiones que han cambiado. Este encabezado resume el estado más reciente; antes de tomar decisiones operativas, contrastar las issues enlazadas y los ADR vigentes. La reconciliación completa del documento sigue pendiente.

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

## Decisiones vigentes y pendientes (revisión 2026-10-24)

**Decisiones vigentes de trabajo (no equivalen a aceptación de producción):**

- **PC-MASTER:** aplicación Windows existente en fase de aceptación manual; la integración candidata de panel y bandeja es la PR #117.
- **Workers:** Debian 13 Stable es la base prevista para la primera prueba de nodos; Proxmox VE no está descartado y sigue siendo una alternativa que debe compararse con criterios medibles.
- **Motor Android:** redroid es el primer candidato acordado para evaluación local; no se debe iniciar hasta cerrar el bloqueo de seguridad #27.
- **Control y coordinación distribuida:** arquitectura Master/Worker; los nodos pendientes solo pueden reportar heartbeat/capacidades/estado propio y no pueden reclamar tareas.
- **Persistencia de la integración del clúster:** PostgreSQL local/autohospedado para los contratos distribuidos y las pruebas de integración; no convertir un servicio cloud de pago en requisito.
- **Autenticación del panel:** gestionada localmente en PC-MASTER; conexión PostgreSQL con rol de solo lectura.
- **Coste:** objetivo obligatorio de 0 USD en servicios operativos; CI solo con runners estándar gratuitos para repositorios públicos, sin asumir que el saldo de facturación de la cuenta esté verificado.
- **GitHub:** registro principal de requisitos, decisiones, hallazgos, pruebas y aceptación.

**Pendiente de validar con pruebas reales o investigación:**

- Capacidad por worker y cantidad sostenible de instancias simultáneas.
- Kernel Debian, módulos y requisitos exactos de cada digest redroid.
- Compatibilidad de APK objetivo, ABI y servicios de Google cuando correspondan.
- Rendimiento de CPU/RAM/almacenamiento, aislamiento, persistencia, recuperación y distribución LAN de imágenes.
- Aceptación manual de PC-MASTER en Windows (#77) y revisión final del diff de la PR #117.
- El uso/cargo real de GitHub Actions solo puede confirmarse desde el panel de facturación de la cuenta.

Las secciones siguientes conservan el registro histórico del 2026-10-09 y días posteriores. Las frases históricas como «no se ha seleccionado motor/stack/base de datos» no representan el estado vigente por sí solas; contrastar siempre esta sección con las issues y ADR enlazadas antes de ejecutar cambios.

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

## Panel PC-MASTER — implementación de solo lectura en revisión (actualizado 2026-10-21)

La implementación administrativa continúa en la [PR #104](https://github.com/D3ckardCain/Geelark-IA/pull/104), que recupera el trabajo de la PR #84 (cerrada sin fusionar) y agrega correcciones posteriores de Windows/CA y pruebas de regresión. Incluye login local, sesiones SQLite revocables, panel del mismo origen, TLS obligatorio, bind loopback por defecto, consulta autenticada de snapshots y rol PostgreSQL dedicado de solo lectura. No expone mutaciones, tareas, ADB ni shell.

La consulta del panel lee `reported_health_state` desde su columna separada; la salud derivada se calcula con frescura del heartbeat. El panel no debe declarar operativo un módulo ausente, obsoleto o incoherente.

CI verificada para HEAD reconciliado `09d6a5ba322b636fd5d277c1cdb366416e057845` (2026-10-21):
- [Persistencia/PostgreSQL y Windows ACL #591](https://github.com/D3ckardCain/Geelark-IA/actions/runs/39686519813): ambos jobs terminaron en success.
- [Transporte HTTPS #462](https://github.com/D3ckardCain/Geelark-IA/actions/runs/39686519850): success.

Se añadió `pytest.ini` con `--import-mode=importlib` y un job aislado de suite integral desde la raíz para PR #104, con PostgreSQL 16 desechable. En HEAD `03da584894ee713af8d74212a81aa07a91cb407b`, la suite raíz terminó con **293 passed, 3 skipped** y `pip check` limpio; Windows ACL terminó con **50 passed, 8 skipped**, y PostgreSQL/persistencia + verificación del rol lector también pasó. Transporte HTTPS pasó en la ejecución [#466](https://github.com/D3ckardCain/Geelark-IA/actions/runs/39686861612).

La aceptación manual en el PC-MASTER Windows 11 sigue pendiente. La CI no demuestra certificados y confianza TLS del equipo, login/logout real ni permisos/conectividad de la base del equipo. Completar el checklist de la issue #77 con evidencia sanitizada antes de declarar operativo el panel.

Pendiente antes de fusionar o desplegar: aceptación manual del checklist de la issue #77 y revisión final de PR. No fusionar ni desplegar todavía. Coste operativo objetivo $0 USD; no restaurar Supabase ni habilitar facturación/runners propios.
