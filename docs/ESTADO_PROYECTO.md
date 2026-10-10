# Estado del proyecto Geelark-IA

**Actualizado:** 2026-10-09  
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


### Bandeja durable de tareas por nodo (2026-10-10)

- PR borrador [#53 — bandeja durable y consulta saliente de tareas](https://github.com/D3ckardCain/Geelark-IA/pull/53), apilado sobre el transporte privado.
- Se añadió la migración `0004_agent_task_inbox.sql` para separar la cola de asignaciones del outbox de eventos.
- La asignación inserta la tarea en la misma transacción que operación, reserva y outbox.
- El endpoint `POST /agent/v1/tasks/claim` aplica autenticación, nonce anti-replay, idempotencia y permisos por operación. Solo nodos activos pueden reclamar; nodos pendientes solo envían heartbeat/capacidades y consultan estado.
- El claim bloquea tarea, instancia y operación con `FOR UPDATE ... SKIP LOCKED`, valida epoch/lease y devuelve el vencimiento de la lease.
- Se añadieron pruebas unitarias y una prueba de integración PostgreSQL real que crea nodo, credencial activa, instancia, operación y tarea; valida el claim, el lease de entrega y el lease de instancia por separado, y confirma el estado durable `delivered`.
- CI del commit `c6c004d`: transporte **#38018593438 success**, persistencia/auth **#38018593437 success** y esquema PostgreSQL **#38018593402 success**. Todas las migraciones se aplicaron en PostgreSQL 16 y pasó la suite configurada; la prueba de integración quedó incluida. No equivale todavía a una prueba de estrés con doble claim concurrente ni a validación física.
- El commit `efbf8a6` añade una comprobación PostgreSQL adicional: una segunda consulta durante el lease vigente no vuelve a entregar la misma tarea. CI del commit `efbf8a6` pasó en los tres workflows: transporte **#38018668716**, persistencia/auth **#38018668703** y esquema **#38018668702**.
- El PR sigue draft; no se fusiona ni se despliega. Siguientes pruebas: doble consumidor realmente concurrente, epoch obsoleto, transiciones terminales y recuperación/reconciliación tras caída.
- La reconciliación continúa sin configurar (503). No hay ejecución de Android, ADB, shell ni despliegue en PCs físicas.


### Ciclo de vida de sincronización de recibos del agente (2026-10-10)

- PR borrador #56 en rama original: https://github.com/D3ckardCain/Geelark-IA/pull/56. Esta integración se porta a una rama apilada sobre la bandeja durable #54 para que los endpoints de progreso/resultado estén presentes en el mismo stack.
- El commit ejecutable `e6d93147d1e04460770241d83e28938eb948bbbe` pasó GitHub Actions run 128: 57 pruebas aprobadas, una advertencia deprecatoria de Starlette/httpx y `pip check` correcto. La integración usa TLS real en loopback, SQLite y PostgreSQL desechable; simula la pérdida del primer ACK y verifica el reintento idempotente. No hay pruebas en PCs físicas.
- Se endureció la validación de configuración y contadores; una excepción del callback de telemetría no debe detener el worker. Se añadieron pruebas para drenaje de lotes, contadores inválidos y callback defectuoso.
- Manual técnico: [MANUAL_CICLO_VIDA_SINCRONIZACION_AGENTE.md](MANUAL_CICLO_VIDA_SINCRONIZACION_AGENTE.md). Manual de usuario/operación: [MANUAL_USUARIO_SINCRONIZACION_AGENTES.md](MANUAL_USUARIO_SINCRONIZACION_AGENTES.md).
- Límite: biblioteca de ciclo de vida, todavía no conectada a un proceso de agente instalable ni con interfaz/comando de usuario. CI no equivale a prueba en PCs físicas. No fusionar ni desplegar antes de revisar el flujo SQLite→HTTPS→PostgreSQL y los controles de seguridad.


### Supervisor portable del agente (2026-10-10)

- PR borrador [#59 — coordinar heartbeat y sincronización durable](https://github.com/D3ckardCain/Geelark-IA/pull/59), apilado sobre #57, #54 y #48.
- El commit ejecutable `b622c0eead3d2eee896b7442fca6dca479c7b78d` pasó GitHub Actions run 143: 90 pruebas aprobadas, migraciones PostgreSQL y `pip check` correctos; permanece una advertencia deprecatoria de Starlette/httpx.
- `AgentSupervisor` coordina heartbeat/capacidades y el sincronizador durable en hilos separados; la recuperación despierta la cola de recibos y los errores se reportan con códigos genéricos. `CredentialProvider` abstrae el secreto; `SystemdCredentialProvider` lee credenciales entregadas por systemd y `build_agent_components` ensambla los objetos sin arrancarlos.
- Manual técnico: [MANUAL_TECNICO_SUPERVISOR_AGENTE.md](MANUAL_TECNICO_SUPERVISOR_AGENTE.md). Manual de usuario: [MANUAL_SUPERVISOR_AGENTE.md](MANUAL_SUPERVISOR_AGENTE.md).
- Límite: biblioteca inyectable, no un servicio/CLI instalable. La elección del SO y almacén de credenciales depende de la decisión de arquitectura documentada en [PR #60](https://github.com/D3ckardCain/Geelark-IA/pull/60) y sigue pendiente. No se ha probado en hardware físico.


### Reconciliación conservadora del agente (2026-10-10)

- PR borrador [#61 — reconciliar inventario sin mutaciones automáticas](https://github.com/D3ckardCain/Geelark-IA/pull/61), apilado sobre #59.
- El commit ejecutable `eb5e71e8b4848f6761b4da15507d070bcc9dfded` pasó Actions run 174 (transporte: 110 pruebas, una advertencia deprecatoria), run 154 (migraciones/invariantes PostgreSQL) y run 188 (servicio/concurrencia PostgreSQL); los tres terminaron correctamente.
- Migration 0005 añade informes de reconciliación auditables. El endpoint compara identidad, propietario, assignment_epoch, leases y resultados; no cambia automáticamente tareas, operaciones ni propietario/epoch de instancias.
- `AgentTransportRuntime.reconcile_inventory` usa un UUID por intento; el supervisor lo conserva para reintentos y lo renueva para una reconciliación nueva. Un worker separado evita bloquear heartbeat/capacidades.
- Manuales: [MANUAL_RECONCILIACION_AGENTES.md](MANUAL_RECONCILIACION_AGENTES.md) y [MANUAL_TECNICO_RECONCILIACION_AGENTES.md](MANUAL_TECNICO_RECONCILIACION_AGENTES.md).
- Límite: no se ha probado en hardware físico; decisiones manuales de conflictos/unknown y el entry point instalable siguen pendientes.


### Control de coste de CI (2026-10-10)

- El repositorio es privado y GitHub Actions consume cuota mensual en runners alojados. No tenemos visibilidad desde este flujo sobre los minutos restantes.
- Issue [#63](https://github.com/D3ckardCain/Geelark-IA/issues/63) registra la optimización pendiente: cancelar ejecuciones obsoletas por PR, limitar rutas y evitar disparar varios workflows por cada commit.
- Hasta revisar la cuota y optimizar concurrencia, evitar pushes repetidos que disparen CI. El código ejecutable de PR #61 ya pasó los tres workflows en el commit `eb5e71e8b4848f6761b4da15507d070bcc9dfded`; la actualización posterior de este estado es solo documentación.
