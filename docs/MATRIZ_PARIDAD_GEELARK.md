# Matriz de paridad funcional con GeeLark

**Fecha:** 2026-10-12  
**Estado:** versión 0.1; catálogo preliminar basado en fuentes oficiales públicas.  
**Regla:** ninguna fila se marca como equivalente hasta tener pruebas reproducibles.

## Estados permitidos

- **No investigado:** no hay evidencia suficiente todavía.
- **Investigación inicial:** hay una o más fuentes públicas, falta el desglose completo.
- **Especificado:** alcance, entradas, salidas y criterios de aceptación documentados.
- **En implementación:** existe trabajo de código en curso.
- **Implementado:** código terminado, aún sin validación completa.
- **Probado:** pruebas documentadas pasaron.
- **Equivalente con adaptación:** se reproduce el objetivo funcional con diferencias descritas y aceptadas.
- **No viable / no equivalente:** existe una limitación técnica, legal o económica que impide la equivalencia; debe documentarse la alternativa.

## Matriz

| ID | Área de GeeLark | Capacidades observadas/documentadas | Adaptación objetivo local | Evidencia | Estado | Prueba pendiente |
|---|---|---|---|---|---|---|
| P-001 | Perfiles/cloud phone | Crear perfiles individuales, rápidos y por lotes; elegir grupo, Android, proxy y modelo | Crear, configurar, iniciar, detener y eliminar instancias Android virtuales | Ayuda de perfiles | Investigación inicial | Crear y reiniciar instancias, persistencia y aislamiento |
| P-002 | Identidad/huella | Se publicita huella única y opción de huella personalizada; v4.5.0 documenta Change IP URL y Auto Refresh para proxy personalizado | Identidad sintética configurable donde el motor lo permita; refresco IP opcional para proxy compatible | Página de producto/precios y nota v4.5.0; catálogo sección 23 | Investigación inicial | Identificar campos; validar URL de cambio de IP, frecuencia y diferencias de señales de red |
| P-003 | Grupos/etiquetas | Organización de perfiles | Grupos, etiquetas, filtros y operaciones por grupo | Centro de ayuda | Investigación inicial | CRUD, filtrado y acciones masivas |
| P-004 | Proxies | Proxies guardados/personalizados, prueba de conexión | Gestión de endpoints y asignación por instancia | Ayuda de perfiles | Investigación inicial | Conexión, credenciales protegidas y errores |
| P-005 | Aplicaciones | Operaciones de apps por perfil/grupo | Listar, instalar, iniciar, detener, actualizar y quitar APK | Centro de ayuda/notas de versión | Investigación inicial | Compatibilidad, permisos y operación por lotes |
| P-006 | Archivos/Library | Biblioteca multimedia; v4.5.2 documenta etiquetas editables, etiqueta en carga y vista tarjeta/lista | Biblioteca local persistente, etiquetas, búsqueda, hash, backup y límites por disco; sin dependencia cloud | Ayuda Library y notas v4.5.2; catálogo secciones 25 y 28 | Investigación inicial | Carga local, persistencia, etiquetas, vistas, iteración por etiqueta y límite de disco |
| P-007 | RPA visual | Flujos drag-and-drop reutilizables/programables; inspector de layout y árbol UI; Get Element Data/Is checked; límites de tamaño; informes con activos | Editor visual versionado, validación, inspección UI, resultados, recursos por etiqueta y límites explícitos | Guía Automaton y notas v4.5.0–v4.5.2; catálogo secciones 17, 23 y 28 | Investigación inicial | Catálogo de bloques; selectores/estado marcado; import/export; recursos por etiqueta; reintentos y errores |
| P-008 | Plantillas | Flujos listos para tareas repetitivas | Catálogo local versionado/importable | Página de automatización | Investigación inicial | Importar, validar, versionar y ejecutar |
| P-009 | Synchronizer | Sincronización de acciones y, según v4.5.1, carga masiva de archivos con historial; guía enumera Android 9–15 | Replicar eventos/archivos soportados a destinos seleccionados con resultados por elemento | Guía Synchronizer y nota v4.5.1; catálogo secciones 17 y 28 | Investigación inicial | Eventos soportados, carga masiva, historial, cancelación, desconexión y diferencias por destino |
| P-010 | API | Guías/CLI documentan ciclo de vida de perfiles, apps, archivos, ADB, tareas, medios con etiquetas, informes y creación por lotes en notas históricas | API local autenticada y versionada con contratos propios, idempotencia y errores tipados | GeeHub/API, CLI público y notas v3.8.0/v3.9.1; catálogo secciones 17, 22 y 30 | Investigación inicial | Enumerar endpoints públicos y diseñar contrato local; auth, paginación, errores, límites y pruebas |
| P-011 | ADB | Habilitar ADB por perfil/grupo y ejecutar comandos; guía consultada enumera Android 11–16 | Puente local restringido a loopback/red interna; shell con permisos mínimos | Guía ADB y catálogo sección 25 | Investigación inicial | Conexión autorizada/no autorizada, reconexión, aislamiento de puerto y errores |
| P-012 | Webhooks/eventos | Callbacks para operaciones | Eventos locales y cola persistente | Página API | Investigación inicial | Entrega, reintento, duplicados e idempotencia |
| P-013 | Analytics | Seguimiento de métricas de cuentas de Instagram, TikTok, YouTube y Reddit en GeeLark; actualización diaria descrita | Priorizar métricas locales; métricas externas solo mediante interfaces legítimas y coste cero verificable | Guía Analytics y catálogo sección 25 | Investigación inicial | Separar métricas locales/externas; no inventar datos ni depender de API de pago |
| P-014 | Logs | v4.5.2 documenta View Task para consultar parámetros configurados tras publicar; la página Logs general no muestra todos los campos | Logs estructurados, instantánea de parámetros de tarea, filtros, exportación y redacción de secretos | Nota v4.5.2 y evidencia parcial de Logs; catálogo secciones 25 y 28 | Investigación inicial parcial | Confirmar campos/filtros/retención; comprobar instantánea y correlación tarea-instancia-bloque |
| P-015 | Miembros/roles | Grupos de derechos, roles administrador/gestor/miembro, grupos autorizados y límites de perfiles | Modo local de usuario único por defecto; multiusuario con RBAC, sesiones revocables y auditoría si se aprueba | Guía Members y catálogo sección 25 | Investigación inicial | Matriz de permisos, aislamiento por grupo y denegación de accesos |
| P-016 | AIGC/IA | Generación de contenido/medios con modelos integrados y cargos comerciales en funciones documentadas | Alternativa local opcional solo si licencia y hardware lo permiten; sin API comercial obligatoria | Centro de ayuda, guía AI Generation Function y catálogo sección 23 | Diferencia estructural pendiente de alternativa | Probar calidad/rendimiento local o marcar explícitamente no equivalente |
| P-017 | Recursos/marketplace | Recursos y plantillas compartidas | Repositorio local importable/exportable | Centro de ayuda | Investigación inicial | Procedencia, validación y versiones |
| P-018 | Facturación/planes | Planes, límites, uso por minuto y servicios pagados | No replicar cobros; medir y limitar recursos locales | Página precios/facturación | Diferencia estructural | Definir límites de recursos y reportes locales |
| P-019 | Cámara/sensores/GPS | Guía describe imagen desde galería, cámara física vía mirroring y webcam/pregrabado; resto de sensores incompleto | Evaluar por separado imagen local, webcam, fuente pregrabada, GPS y sensores soportados | Guía cámara y catálogo sección 25 | Investigación inicial parcial | Pruebas por motor/host; declarar explícitamente simulación y límites de hardware real |
| P-020 | Instalación/actualización | Guías de descarga y notas de versión | Instalación local reproducible y actualización reversible | Centro de ayuda | Investigación inicial | Instalación limpia, backup, actualización y rollback |
| P-021 | Operación offline | GeeLark se basa en servicios cloud | Administración local y cola offline cuando sea posible | Requisito del proyecto | Adaptación propia | Definir funciones offline y pruebas de desconexión |
| P-022 | Escalabilidad | GeeLark ofrece paralelos y perfiles cloud | Escalar instancias locales según CPU/RAM/GPU/almacenamiento | Página precios | No equivalente por defecto | Benchmark incremental de 1, 2, 5, 10 instancias |
| P-023 | Android versions | Páginas consultadas enumeran Android 9–15 y Synchronizer menciona Android 9–16; fuentes no coinciden | Seleccionar imágenes locales compatibles tras investigar | Página Synchronizer/precios | Pendiente de aclarar | Confirmar soporte vigente y requisitos por versión |
| P-024 | Perfiles clonados | Nota v3.9.0 documenta clonado de perfiles; el detalle actual requiere confirmación | Clonar configuración declarada y datos seleccionados, con identidad nueva por defecto y sin copiar secretos | Nota v3.9.0 y catálogo sección 30 | Investigación inicial | Probar independencia de datos, identidad, aplicaciones, archivos y credenciales; rollback ante fallo |
| P-025 | Operaciones masivas | Creación de perfiles por lotes, apps por grupo, sincronización y operaciones históricas de lotes | Cola persistente, validación previa, límite por recursos, idempotencia y resultado por elemento | Guías Profile/Applications/Synchronizer y notas v3.6–v3.9; catálogo sección 30 | Investigación inicial | Pruebas de fallos parciales, cancelación, reinicio, duplicados y límites de concurrencia |
| P-026 | Motor Android local | Candidatos: redroid, Android Emulator, Waydroid, Android-x86/derivados | Seleccionar motor según compatibilidad, aislamiento, automatización, rendimiento y coste | [Comparativa de motores](COMPARATIVA_MOTORES_ANDROID.md) y documentación oficial | Investigación documental inicial | Benchmark y prueba de paridad en el anfitrión real; ver issue #8 |

## Reglas para completar cada fila

1. Adjuntar enlace y fragmento de evidencia oficial.
2. Enumerar todas las opciones/campos del flujo, incluidos errores y restricciones por plan.
3. Documentar si es función del producto, del servicio cloud, del sistema operativo o de un proveedor externo.
4. Definir alternativa local gratuita y dependencias de hardware/software.
5. Añadir criterios de aceptación y prueba reproducible.
6. Registrar diferencias entre GeeLark y Geelark-IA.
7. Cambiar estado solo cuando haya evidencia del hito.


## 2.1 Hallazgos detallados añadidos el 2026-10-09

El catálogo funcional ampliado está en [CATALOGO_FUNCIONAL_GEELARK.md](CATALOGO_FUNCIONAL_GEELARK.md). Esta ampliación no cambia automáticamente el estado de paridad: sigue siendo investigación documental.

| Subárea detectada | Funciones adicionales documentadas | Filas relacionadas | Acción de auditoría |
|---|---|---|---|
| Creación de perfiles | Creación individual, rápida y por lotes; grupo; versión Android; proxy guardado/personalizado; prueba de proxy; modelo y método de cobro del servicio | P-001, P-003, P-004 | Enumerar todos los campos, valores permitidos, errores y restricciones |
| Clonación de perfiles | Las notas v3.9.0 anuncian clonado | P-024 | Definir semántica de copia, identidad, credenciales y datos persistentes |
| Red por perfil | v3.9.0 menciona red celular/Wi-Fi personalizada en Android 12/13/15 | P-002, P-019, P-023 | Investigar campos reales y qué puede simular legal/técnicamente un motor local |
| Proxy | HTTP, HTTPS, SOCKS5; host, puerto, usuario, contraseña; prueba de conexión y ubicación estimada | P-004 | Diseñar gestión segura de secretos y pruebas sin garantía de anonimato |
| RPA | Editor visual, flujos personalizados, plantillas, programación; inspector UI/árbol de elementos; revisión posterior de parámetros de tareas | P-007, P-008, P-014 | Desglosar todos los bloques y sus contratos en el manual RPA |
| Synchronizer | Acciones entre teléfonos; Android 9–15 en la guía consultada; entrada masiva de textos diferentes; carga masiva de archivos | P-009, P-025 | Definir matriz de eventos soportados, diferencias por instancia y errores parciales |
| Library | Etiquetas, edición de etiquetas, carga con etiquetas, vista tarjeta/lista, selección de activos por etiqueta en flujos | P-006, P-008 | Especificar catálogo local y API interna de activos |
| Aplicaciones | Operaciones masivas por grupo: abrir, cerrar, reiniciar, desinstalar; actualización e instalación dirigida a grupos | P-005, P-025 | Definir estados por instancia y recuperación de fallos parciales |
| API/CLI/ADB | Ciclo de vida de perfiles, apps, archivos, ADB, tareas; token Bearer y endpoints multimedia en versiones históricas | P-010, P-011, P-012 | Inventariar contratos documentados; implementación propia y local |
| Logs | Ver parámetros configurados tras publicar tareas; nombres de activos en reportes de ejecución | P-014 | Incluir trazabilidad por tarea, instancia, bloque y recurso, sin secretos |
| IA/AIGC | Integraciones de modelos comerciales y seguimiento de uso | P-016 | Separar cada función; evaluar alternativas locales y registrar cualquier diferencia |

### Criterio para estado

No marcar estas subáreas como “Especificado” hasta que el catálogo incluya campos/acciones, entradas/salidas, errores, restricciones, fuente y prueba de aceptación concreta. Las páginas de marketing y las notas de versión sirven como evidencia de existencia, no como especificación completa.


## 2.2 Hallazgos adicionales de gestión de perfiles (2026-10-09)

Fuente de apoyo: [gestión de perfiles y grupos](https://help.geelark.com/Group-management-c91b6291bb954a69a5d231781a03d0e1), [aplicaciones](https://help.geelark.com/Applications-95cfce3d74e443b8a5f57f5123669e60), [Add Custom Phone](https://help.geelark.com/Add-Custom-Phone-2ee0be7d9e418045ac69ffd6eb043e63?pvs=21).

| Función concreta | Evidencia | Adaptación local | Estado / diferencia |
|---|---|---|---|
| Filtrar perfiles y editar solo cerrados | La guía de gestión describe filtros y edición de perfiles cerrados | Filtros locales; edición con reglas de estado para evitar corrupción | Investigación inicial |
| Crear, renombrar, borrar y fusionar grupos | Guía de gestión de perfiles | CRUD de grupos y fusión con tratamiento de conflictos | Investigación inicial |
| Mover perfiles y gestionar acceso de miembros | Guía de gestión de perfiles | Cambiar grupo/propietario/permisos, registrar auditoría | Investigación inicial |
| Instalar/actualizar apps individualmente y por lotes | Guía Applications | APK aportados por usuario, asignación a grupo y estado por instancia | Investigación inicial |
| Extraer huella desde teléfono físico | Guía Add Custom Phone requiere un Android físico conectado por USB/ADB | No se puede replicar exactamente sin contradecir el alcance de no depender de teléfonos físicos; alternativa: identidad sintética configurable y limitaciones documentadas | Diferencia estructural explícita |
| Retención/recuperación de perfiles eliminados | Notas históricas de versión mencionan papelera y retención temporal | Diseñar papelera local configurable y recuperación probada | Investigación inicial |
| Sustitución/configuración masiva | Notas de versión documentan operaciones masivas con límites de versión/plan | Cola local con resultados por elemento y límite basado en recursos reales | Investigación inicial |

**Nota de paridad importante:** la función de extracción de huella de un teléfono real queda registrada como **no equivalente bajo el alcance actual**, no como tarea de implementación pendiente que se pueda resolver solo con software. Si el alcance cambia en el futuro, habrá que revisar esta decisión expresamente.


## 2.3 Importación opcional desde Android físico (decisión del usuario, 2026-10-09)

Se aprueban dos vías de configuración por instancia: **identidad sintética** e **importación selectiva desde Android físico por USB/ADB**. No son excluyentes. La importación queda como capacidad por investigar y probar; no se presupone que todos los campos puedan leerse o aplicarse.

| ID | Capacidad | Requisito de aceptación | Estado |
|---|---|---|---|
| P-027 | Detectar Android físico conectado | Detectar dispositivos autorizados/no autorizados, versión Android y errores ADB sin modificar el origen | No especificado |
| P-028 | Inspeccionar campos importables | Listar campos accesibles, origen del dato, compatibilidad, si es editable y limitaciones | No especificado |
| P-029 | Importar selección a perfil local | Vista previa y selección explícita; no copiar cuentas, tokens ni datos personales por defecto | No especificado |
| P-030 | Aplicar configuración al Android virtual | Aplicar solo campos compatibles, reiniciar cuando proceda y reportar diferencias por campo | No especificado |
| P-031 | Trazabilidad y seguridad de la importación | Registrar fecha y resultado sin secretos; permitir cancelar y borrar el perfil de importación | No especificado |

**Límite de paridad:** no afirmar que se clona íntegramente una identidad física. Los identificadores protegidos, claves de hardware, attestation, SIM/módem y señales derivadas del host pueden no ser accesibles o reproducibles. No se eludirán mecanismos de seguridad ni antiabuso.


## 2.4 Comparativa de motores Android locales (2026-10-09)

La comparación documental y el protocolo de pruebas están en [COMPARATIVA_MOTORES_ANDROID.md](COMPARATIVA_MOTORES_ANDROID.md). No se ha aprobado ningún motor. Se revisarán licencias, componentes de terceros, requisitos de host, ADB, gráficos, persistencia, aislamiento, APK, sensores y seguridad.

| Candidato | Evaluación inicial | Prueba que falta | Estado de decisión |
|---|---|---|---|
| redroid | Prioridad para probar si el host es Linux compatible; orientado a múltiples instancias; requiere funciones de kernel y atención especial a privilegios/ADB | Arranque, aislamiento, persistencia, control, recursos y revisión de componentes | No seleccionado |
| Android Emulator oficial | Referencia útil de AVD/ADB; la licencia del SDK e imágenes debe revisarse para el uso concreto del producto | Licencia aplicable, multiinstancia, automatización y rendimiento | Condicionado |
| Waydroid | Alternativa de contenedor para GNU/Linux; investigar el manejo de instancias separadas y licencias de todos los componentes | Control independiente, aislamiento, estabilidad y compatibilidad de apps | No seleccionado |
| Android-x86/derivado | Solo evaluable al seleccionar una distribución concreta con mantenimiento verificable | Versión, licencia, gráficos, ADB y soporte de aplicaciones | Pendiente de concretar |

Issue de seguimiento: [#8 — Comparar y validar motores Android locales](https://github.com/D3ckardCain/Geelark-IA/issues/8). Las conclusiones documentales no sustituyen las pruebas del hardware anfitrión.


## 2.5 Criterios de aceptación preliminares derivados del contraste documental (2026-10-09)

El catálogo funcional contiene la evidencia y el contexto. Esta tabla convierte una parte de esa evidencia en pruebas concretas para cuando exista motor y UI local.

| Área | Criterios de aceptación de Geelark-IA | Dependencia / límite | Estado |
|---|---|---|---|
| Creación de perfiles | Crear uno; crear lote con validación por fila; asignar grupo/versión; mostrar estado de instancia; reintento no duplica recursos | Requiere motor Android aprobado | Especificación preliminar |
| Clonación | Copiar configuración declarada, generar identidad local nueva por defecto y no copiar cuentas/tokens/datos privados sin selección explícita | Solo campos que soporte el motor | Pendiente |
| Proxies | Importar lista con vista previa; validar formato y conexión; proteger credenciales; diferenciar fallo de proxy y fallo de geolocalización | Consulta geográfica externa opcional | Especificación preliminar |
| Aplicaciones | Instalar APK legítima; consultar paquetes; operar por grupo; reportar éxito/fallo por instancia; persistir política de instalación automática | Compatibilidad de ABI, firma y Android | Especificación preliminar |
| Grupos | CRUD, filtros, mover instancias, fusionar con reglas explícitas y confirmar acciones destructivas | No borrar instancias al borrar grupo sin confirmación | Especificación preliminar |
| RPA | Guardar/versionar flujo; validar bloques; seleccionar destinos; programar; ejecutar/cancelar; consultar historial y errores | Catálogo exhaustivo de bloques aún pendiente | Investigación inicial |
| Synchronizer | Seleccionar fuente/destinos; mostrar compatibilidad; reproducir eventos soportados; informar fallos individuales; pausar/detener | Diferencias de resolución/Android y estado de destino | Investigación inicial |
| API/CLI | Operaciones de instancia, apps, archivos, ADB y tareas con permisos, idempotencia, errores tipados y resultados por elemento | Contratos exactos aún por diseñar | Especificación preliminar |
| Webhooks | Firma, validación de destino, cola persistente, reintentos, deduplicación e indicador de entrega | Requiere red para receptores externos; eventos locales pueden persistir offline | Pendiente |
| Logs | Correlación por instancia/tarea/bloque; exportación; redacción de secretos; resultados parciales explícitos | No registrar contenido privado por defecto | Especificación preliminar |
| Offline | Abrir catálogo/configuración local, inspeccionar tareas ya guardadas y mantener cola de operaciones locales; sincronización externa se pausa y reanuda | Aplicaciones objetivo y descargas pueden requerir Internet | Diseño pendiente |
| IA/AIGC | Deshabilitada por defecto hasta comprobar licencia, hardware y coste cero; alternativa local aislada y opcional | Calidad/velocidad dependen del anfitrión | Pendiente |

Estos criterios no indican implementación ni pruebas realizadas. La etiqueta “Especificación preliminar” significa que hay un criterio inicial, pero faltan diseño completo y aprobación.


La nota v4.5.0 y la guía AIGC se registraron en `docs/CATALOGO_FUNCIONAL_GEELARK.md`, sección 23. Los cambios de versión se consideran evidencia de funciones y no una especificación completa; se requieren pruebas antes de cambiar el estado de paridad.


La guía pública de Logs consultada solo muestra encabezado, por lo que la equivalencia de P-014 continúa sin evidencia suficiente para campos, filtros y retención. No se inferirán detalles hasta obtener una fuente más completa o evidencia observable.


Las notas v4.5.1 y v4.5.2 se incorporaron al catálogo (sección 28). Las funciones de Library, Synchronizer, RPA y View Task siguen en investigación documental; no se declara equivalencia ni implementación.


Las notas históricas v3.6–v3.9 se documentaron en el catálogo, sección 30. Sus límites y opciones no se consideran garantía actual ni límites que debamos copiar; la implementación local deberá validarse con pruebas propias.


## 2.7 Revalidación de fuentes oficiales (2026-10-12)

| Área | Evidencia actualizada | Implicación para la adaptación local | Estado |
|---|---|---|---|
| P-001 Perfiles | Creación individual, rápida y por lotes; Quick Create y Batch Create son Pro. La guía individual exige grupo, OS y proxy, y describe comprobación de proxy. | Crear perfiles locales sin facturación cloud; operaciones por lotes deben ser idempotentes, con validación por fila y recuperación. | Investigación inicial; ver catálogo §32.1 |
| P-004 Proxies | Proxy estático/rotativo, guardados/personalizados, asociación con perfiles y comprobación de conexión/ubicación; proxy expirado no permitido. | Guardar secretos cifrados o en almacén del sistema, nunca en logs; ubicación será estimación y no garantía de anonimato. | Investigación inicial |
| P-006 Library | Pro-only; 100 GB y eliminación tras 30 días en el servicio cloud de GeeLark. | Biblioteca local persistente con límites por disco configurables, backup y borrado explícito; no copiar el límite comercial de 30 días. | Investigación inicial |
| P-009 Synchronizer | Pro-only; teléfono principal replica acciones a otros; guía recomienda dispositivos apagados y del mismo tipo; Android 9–15. | Verificar estado/compatibilidad antes de iniciar, informar resultados por destino y no prometer equivalencia entre layouts distintos. | Investigación inicial |
| P-010 API | La página pública enumera ciclo de vida de cloud phones, automatización, apps/contenido, archivos, Library, ADB y webhooks. | API local propia y versionada; ninguna dependencia de endpoints ni credenciales de GeeLark. | Investigación inicial |
| P-011 ADB | Guía consultada enumera Android 11–16 para ADB; no coincide con la lista de Synchronizer. | Restringir ADB a loopback/red interna y validar por motor/imagen; mantener la discrepancia de versiones abierta. | Pendiente de aclarar |
| P-018 Facturación/planes | El cloud phone se factura por minuto salvo paquete de tiempo/alquiler mensual; varias funciones son Pro. | No reproducir cobros cloud; medir uso local y limitar por hardware. | Diferencia estructural |
| P-023 Versiones Android | Synchronizer publica Android 9–15; ADB publica Android 11–16. | No inferir soporte general a partir de una lista específica de función. | Pendiente de aclarar |

Fuentes oficiales revisadas:
- Perfil y facturación: https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8
- Gestión de perfiles: https://help.geelark.com/Profile-management-c91b6291bb954a69a5d231781a03d0e1
- Synchronizer: https://help.geelark.com/Synchronizer-82c1c9a8f62d489ca81b1f753d2a7bfa
- Library: https://help.geelark.com/Library-1c20be7d9e41800a8535ea943b930bd4
- API: https://www.geelark.com/features/api/
- ADB: https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad

Esta revalidación actualiza evidencia documental únicamente. No cambia filas a “Implementado”, “Probado” o “Equivalente”; la compatibilidad real de Geelark-IA requiere pruebas propias.


### Requisito adicional RPA — selectores y variables (2026-10-12)

| Área | Evidencia oficial | Adaptación local | Prueba de aceptación pendiente |
|---|---|---|---|
| P-007 RPA: selectores | Texto visible, atributos `fullId`/`desc`/`className`, coordenadas; Equals/Contains; orden fijo/aleatorio; timeout; opción de elementos invisibles; resultado booleano | Selectores tipados con prioridad semántica, timeout obligatorio, resultado estructurado y modo coordenadas explícitamente frágil | Selector único/ambiguo/ausente, timeout, elemento oculto, resolución distinta, idioma distinto y reintento sin duplicar efectos |
| P-007 RPA: variables y control | Variables string, number, boolean y object; extracción/reutilización de texto; loops por cantidad/elementos/datos; condiciones y manejo de excepción skip/stop | Variables tipadas, límites de memoria/iteraciones, esquema validado y excepción tipada; no ejecutar scripts arbitrarios | Tipos incompatibles, variable inexistente, loop infinito, cancelación, error en bloque intermedio y persistencia de resultados |

Fuentes:
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- https://www.geelark.com/blog/geelark-rpa-guide-5/
- https://www.geelark.com/es/blog-es/automatizacion-de-apps-android-y-navegador-geelark-rpa/

Estos detalles amplían la especificación de RPA, pero no cierran la auditoría exhaustiva de bloques. La documentación pública y las capturas disponibles no demuestran todos los módulos, parámetros ni errores de la versión actual.


### Requisito adicional RPA — selectores y variables (2026-10-12)

| Área | Evidencia oficial | Adaptación local | Prueba de aceptación pendiente |
|---|---|---|---|
| P-007 RPA: selectores | Texto visible, atributos `fullId`/`desc`/`className`, coordenadas; Equals/Contains; orden fijo/aleatorio; timeout; opción de elementos invisibles; resultado booleano | Selectores tipados con prioridad semántica, timeout obligatorio, resultado estructurado y modo coordenadas explícitamente frágil | Selector único/ambiguo/ausente, timeout, elemento oculto, resolución distinta, idioma distinto y reintento sin duplicar efectos |
| P-007 RPA: variables y control | Variables string, number, boolean y object; extracción/reutilización de texto; loops por cantidad/elementos/datos; condiciones y manejo de excepción skip/stop | Variables tipadas, límites de memoria/iteraciones, esquema validado y excepción tipada; no ejecutar scripts arbitrarios | Tipos incompatibles, variable inexistente, loop infinito, cancelación, error en bloque intermedio y persistencia de resultados |

Fuentes:
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- https://www.geelark.com/blog/geelark-rpa-guide-5/
- https://www.geelark.com/es/blog-es/automatizacion-de-apps-android-y-navegador-geelark-rpa/

Estos detalles amplían la especificación de RPA, pero no cierran la auditoría exhaustiva de bloques. La documentación pública no demuestra todos los módulos, parámetros ni errores de la versión actual.


### Bloques RPA adicionales identificados (2026-10-12)

| Bloque | Evidencia publicada | Adaptación local / pruebas pendientes |
|---|---|---|
| Open app | Package name y URI opcional | Validar app instalada, URI permitida y resultado |
| Waiting time | Valor fijo o intervalo aleatorio | Límites, unidades, cancelación y registro de valor aplicado |
| Scroll Page / Page back | Distancia, tiempo, coordenadas, dirección; regreso a pantalla anterior | Probar resoluciones, límites de pantalla, máximo de back y resultados observables |
| Upload File | Selección múltiple; orden por flujo, por entorno o aleatorio | Rutas aprobadas, tamaño/hash, fallos parciales y resultado por archivo |
| IF Condition | Exists/Does Not Exist, comparadores, Include/Not Include y porcentaje aleatorio | Tipado, variables ausentes, evaluación reproducible y pruebas de cada rama |
| For Loop Times / Elements / Data | Repetición por cantidad, elementos visibles o datos; Exit Loop | Límite de iteraciones, colección cambiante, cancelación y contrato de For Loop Data pendiente |
| End Task / Exception handling | Parada inmediata; Skip o Interrupt ante error | Verificar estados terminales, no ejecutar pasos posteriores y registro de causa |
| Task Settings / Schedule / Logs | Variables String, Batch Text, Boolean, Number, File; perfiles destino y horarios; cancelación/edición de publicación | Persistencia, zona horaria, idempotencia, reintentos y cancelación segura |

Fuentes: guías oficiales RPA 2, 3 y 6 enlazadas en el catálogo, sección 32.7. La matriz sigue en estado de investigación; no se declara el motor implementado ni equivalente.


### Acciones UI: precisión adicional de la guía 4 (2026-10-12)

| Acción | Campos observados | Riesgo / aceptación local |
|---|---|---|
| Clic/pulsación prolongada en elemento | fullId/text/desc/className, Equals/Contains, índice o rango, timeout, elementos invisibles, resultado booleano, nota | Probar selector vacío/ambiguo, jerarquía anidada y resultado false en timeout |
| Clic/pulsación prolongada por coordenadas | X/Y; puede derivarse del centro de los límites del elemento | Marcar resolución de referencia; probar al menos dos resoluciones y detectar coordenadas fuera de pantalla |
| Ingresar contenido | Selector, coincidencia, orden, timeout y texto/variable | No registrar contenido sensible; validar foco/campo y fallos de entrada |
| Operación de teclado | Teclas como Enter/Delete | Lista permitida de teclas y resultado verificable |
| Esperar elemento | Selector, condición, orden, timeout, elementos invisibles y resultado booleano | Timeout limitado, cancelación y no continuar silenciosamente cuando sea requisito crítico |

Fuente: https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/


### API: categorías y límites publicados por el CLI oficial (2026-10-12)

| Categoría | Operaciones expuestas por el CLI | Relevancia local | Restricción/evidencia |
|---|---|---|---|
| Cloud phone | CRUD, start/stop, status, clone, screenshot, GPS, reset, root, SMS, contactos, transfer | Inventario de funciones de gestión a mapear contra módulos locales | Servicio cloud requiere token y puede requerir plan/saldo |
| Automation | Consultar/cancelar/reiniciar tareas; crear tareas personalizadas y de plataforma | API local propia para colas, estado, cancelación e idempotencia | No integrar API de GeeLark como dependencia |
| Apps/files/Library | Catálogo, instalar/desinstalar, carga APK/archivo, resultados de carga, materiales y tags | Gestor local de paquetes y medios con auditoría | Retención/capacidad cloud no se copia como requisito local |
| ADB/shell | Datos de conexión, habilitar/deshabilitar ADB, ejecución de shell remoto | Solo control local autorizado y explícito | No exponer shell/ADB remoto en panel admin |
| Browser/proxy/groups/tags | CRUD de perfiles de navegador, proxies, grupos y etiquetas | Comparar con alcance del producto; navegador queda separado de Android | La API cloud puede tener límites y cargos |
| Webhook/OEM/analytics/billing | Callbacks, marca, cuentas/datos y saldo/planes/transacciones | Webhooks locales opcionales; facturación cloud fuera de alcance | CLI MIT no convierte el backend cloud en gratuito |

El README del CLI oficial publica límites de 200 solicitudes/minuto y 24.000/hora, con 10/minuto para balance, y una restricción de dos horas tras exceder límites. Son valores declarados por el CLI, no un SLA; deben confirmarse contra la documentación API vigente antes de cualquier integración. El portal https://open.geelark.com/api no expuso texto legible en esta revisión.

Fuente: https://github.com/GeeLark/geelark-cli
