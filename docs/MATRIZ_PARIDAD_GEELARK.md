# Matriz de paridad funcional con GeeLark

**Fecha:** 2026-10-09  
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
| P-006 | Archivos/Library | Biblioteca multimedia para automatización | Biblioteca local persistente, etiquetas, búsqueda y asignación | Ayuda Library | Investigación inicial | Importar/exportar, deduplicar y recuperación |
| P-007 | RPA visual | Flujos drag-and-drop, reutilizables/programables; inspector de layout; Get Element Data con opción Is checked; límites de tamaño al guardar | Editor visual versionado, validación, inspección UI, resultados y límites explícitos | Guía Automaton y notas v4.5.0; catálogo secciones 17 y 23 | Investigación inicial | Catálogo de bloques; validar selectores/estado marcado, límites de flujo, reintentos y errores |
| P-008 | Plantillas | Flujos listos para tareas repetitivas | Catálogo local versionado/importable | Página de automatización | Investigación inicial | Importar, validar, versionar y ejecutar |
| P-009 | Synchronizer | Copiar interacciones de una instancia principal a otras; texto masivo | Replicar eventos entre instancias seleccionadas | Página Synchronizer | Investigación inicial | Resolución distinta, latencia, exclusiones y pausa |
| P-010 | API | Operaciones de perfiles, automatización, apps, archivos y Library | API local autenticada | Página API | Investigación inicial | Contratos, autenticación, idempotencia y errores |
| P-011 | ADB | Habilitar ADB y ejecutar comandos en cloud phone | Puente ADB local a cada instancia compatible | Guía ADB | Investigación inicial | Conexión, autorización, comandos y reconexión |
| P-012 | Webhooks/eventos | Callbacks para operaciones | Eventos locales y cola persistente | Página API | Investigación inicial | Entrega, reintento, duplicados e idempotencia |
| P-013 | Analytics | Paneles/analítica por plan | Métricas locales de tareas y recursos | Precios/centro de ayuda | Investigación inicial | Exactitud y exportación |
| P-014 | Logs | Registros de operación | Logs filtrables, trazabilidad y exportación | Centro de ayuda/precios | Investigación inicial | Correlación tarea-dispositivo y redacción de secretos |
| P-015 | Miembros/roles | Miembros, permisos y roles | Usuarios/roles locales si el alcance lo requiere | Precios/centro de ayuda | Investigación inicial | Pruebas de autorización y auditoría |
| P-016 | AIGC/IA | Generación de contenido/medios con modelos integrados y cargos comerciales en funciones documentadas | Alternativa local opcional solo si licencia y hardware lo permiten; sin API comercial obligatoria | Centro de ayuda, guía AI Generation Function y catálogo sección 23 | Diferencia estructural pendiente de alternativa | Probar calidad/rendimiento local o marcar explícitamente no equivalente |
| P-017 | Recursos/marketplace | Recursos y plantillas compartidas | Repositorio local importable/exportable | Centro de ayuda | Investigación inicial | Procedencia, validación y versiones |
| P-018 | Facturación/planes | Planes, límites, uso por minuto y servicios pagados | No replicar cobros; medir y limitar recursos locales | Página precios/facturación | Diferencia estructural | Definir límites de recursos y reportes locales |
| P-019 | Cámara/sensores/GPS | Documentación parcial sobre cámara; no se han verificado todos los sensores | Emular solo lo soportado por el virtualizador | Centro de ayuda | No investigado a fondo | Probar cámara, ubicación, sensores, audio y notificaciones |
| P-020 | Instalación/actualización | Guías de descarga y notas de versión | Instalación local reproducible y actualización reversible | Centro de ayuda | Investigación inicial | Instalación limpia, backup, actualización y rollback |
| P-021 | Operación offline | GeeLark se basa en servicios cloud | Administración local y cola offline cuando sea posible | Requisito del proyecto | Adaptación propia | Definir funciones offline y pruebas de desconexión |
| P-022 | Escalabilidad | GeeLark ofrece paralelos y perfiles cloud | Escalar instancias locales según CPU/RAM/GPU/almacenamiento | Página precios | No equivalente por defecto | Benchmark incremental de 1, 2, 5, 10 instancias |
| P-023 | Android versions | Páginas consultadas enumeran Android 9–15 y Synchronizer menciona Android 9–16; fuentes no coinciden | Seleccionar imágenes locales compatibles tras investigar | Página Synchronizer/precios | Pendiente de aclarar | Confirmar soporte vigente y requisitos por versión |
| P-024 | Perfiles clonados | La página de precios indica clonado en planes superiores | Clonar configuración/imagen de instancia sin compartir accidentalmente identidad | Precios | Investigación inicial | Clonación, independencia y limpieza de datos |
| P-025 | Operaciones masivas | Crear perfiles y operar apps en grupos; Synchronizer | Cola de tareas por grupos con resultados individuales | Perfil/RPA/Synchronizer | Investigación inicial | Fallos parciales, cancelación y recuperación |
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
