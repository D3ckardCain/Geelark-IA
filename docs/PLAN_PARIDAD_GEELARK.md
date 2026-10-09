# Plan maestro de paridad funcional con GeeLark (solo Android, local y gratuito)

**Estado:** borrador de planificación basado en investigación pública inicial; requiere validación del usuario y pruebas prácticas.  
**Fecha:** 2026-10-09  
**Objetivo:** construir desde cero una plataforma de gestión y automatización de entornos Android virtualizados/emulados localmente en hardware anfitrión físico, con software gratuito y sin servicios de pago obligatorios, tomando GeeLark como referencia funcional. No se copiará código, marca, contenido privado ni activos propietarios de GeeLark; se hará una implementación independiente basada en requisitos observables.

## 1. Objetivo y límites no negociables

- Alcanzar la mayor paridad funcional verificable posible con GeeLark, inventariando cada función, opción, flujo y limitación.
- Solo Android. iOS queda excluido.
- Ejecución local: los dispositivos Android objetivo serán instancias virtualizadas/emuladas en el hardware anfitrión físico. No se presupone el uso de teléfonos físicos. La viabilidad, fidelidad y límites de cada virtualizador deben demostrarse con pruebas; no se dependerá de teléfonos en la nube.
- Objetivo de costo operativo: **0 USD**. No usar tarjeta obligatoria, trial temporal, cobro automático ni API de pago para funciones críticas.
- Usar herramientas open source o gratuitas de forma sostenible, comprobando licencias, límites y requisitos de hardware.
- Mantener capacidad de operación local sin Internet cuando sea técnicamente posible; separar claramente las funciones offline de las que necesitan Internet (por ejemplo, apps/redes sociales, descarga de APK, actualizaciones o servicios externos).
- GitHub será el registro principal de requisitos, investigación, decisiones, tareas, incidencias, pruebas, cambios y documentación.
- Cada módulo requiere pruebas, comparación con GeeLark y manual de usuario antes de darlo por terminado.

## 2. Investigación funcional inicial

La documentación pública de GeeLark presenta estas áreas en su Centro de ayuda: Profile, Proxies, Library, AIGC, Analytics, Applications, Automaton, Synchronizer, GeeHub, Resources, Referral, Billing, Members y Logs; además documenta grupos, perfiles, ADB, integración de proxy y conexión de dispositivo local. Su web de automatización presenta plantillas listas, sincronizador, RPA visual y API. La oferta incluye funciones de teléfono Android en la nube; esas funciones deberán traducirse a equivalentes locales, no reproducirse mediante infraestructura cloud.

Fuentes públicas iniciales:
- Centro de ayuda: https://help.geelark.com/
- Automatización: https://www.geelark.com/features/automation/
- RPA: https://www.geelark.com/features/rpa/
- API: https://www.geelark.com/features/api/
- Precios y límites publicados: https://www.geelark.com/pricing/

Esta lista es un inventario de áreas inicial, no una afirmación de que cada detalle ya se haya inspeccionado. La fase de descubrimiento ampliará el catálogo con páginas de ayuda, capturas autorizadas, pruebas manuales y criterios de aceptación por función.

## 3. Catálogo de módulos objetivo

### M00 — Descubrimiento y matriz de paridad
- Enumerar cada pantalla, menú, función, ajuste, estado, error y flujo de GeeLark.
- Registrar nombre, propósito, entradas, salidas, permisos, dependencias, evidencia y criterio de aceptación.
- Clasificar cada capacidad como: reproducible localmente; reproducible con adaptación; depende de un servicio externo; no viable o no confirmada.
- Identificar diferencias entre teléfonos físicos y teléfonos cloud. No asumir que un perfil virtual equivale a un dispositivo físico.

### M01 — Inventario de hardware y prueba de viabilidad
- Confirmar hardware anfitrión, sistema operativo, CPU, RAM, almacenamiento, GPU, virtualización por hardware y red. Los teléfonos objetivo serán virtuales; no se presupone disponibilidad de teléfonos físicos.
- Medir cuántas instancias Android virtuales se pueden ejecutar y controlar de forma estable.
- Probar creación/arranque de una instancia Android virtual, ADB si está disponible, reconexión, transferencia de archivos, captura de pantalla, entrada de texto, eventos táctiles, aceleración gráfica y compatibilidad de aplicaciones.
- Evaluar, por separado, si la virtualización/emulación local aporta valor; no prometer instancias Android ilimitadas ni perfiles con identidad de dispositivo genuina.
- Salida: informe de capacidad y límites reales antes de escoger arquitectura.

### M02 — Arquitectura y base local
- Diseñar una aplicación de escritorio/local con interfaz de administración y servicio local de dispositivos.
- Preferir componentes portables y sustituibles; separar interfaz, inventario, ejecución, automatización, almacenamiento y conectores.
- Definir base de datos local, migraciones, copias de seguridad, recuperación, logs y gestión de secretos.
- Establecer modelo de permisos y seguridad antes de exponer controles a la red.
- Decidir stack solo después de M01; no queda aprobada ninguna tecnología por adelantado.

### M03 — Gestión de dispositivos/perfiles
- Descubrir y administrar instancias virtuales, identificarlas, nombrarlas, etiquetarlas, agruparlas y consultar su estado.
- Crear/editar/eliminar perfiles de instancias virtuales, asociar configuración, imagen Android, recursos asignados, notas y estado.
- Acciones de conexión/desconexión lógica, reinicio cuando sea compatible, comprobación de salud y recuperación.
- Importación/exportación y clonación de configuración lógica cuando no implique copiar identificadores de hardware.
- Explicar explícitamente que un perfil de software no crea un teléfono físico ni puede garantizar una huella de dispositivo modificable.

### M04 — Control remoto local y visualización
- Ver la pantalla de una instancia Android virtual, iniciar/detener el control y enviar toques, deslizamientos, teclado y portapapeles si el motor elegido lo permite.
- Captura de pantalla, resolución/orientación cuando el dispositivo lo permita, latencia y recuperación de conexión.
- Control multi-dispositivo, con límites medidos.
- Funcionamiento exclusivamente en LAN/USB por defecto; acceso remoto fuera de LAN requerirá diseño de seguridad explícito y no dependerá de túneles de pago.

### M05 — Aplicaciones y archivos
- Enumerar paquetes instalados, abrir/cerrar aplicaciones cuando Android lo permita, instalar APK autorizados, consultar versión y desinstalar.
- Transferir, organizar y distribuir archivos multimedia y otros archivos a dispositivos seleccionados.
- Biblioteca local de recursos, etiquetado, búsqueda, metadatos, deduplicación y asignación a tareas.
- Permisos, compatibilidad de Android y restricciones de instalación documentados.

### M06 — Proxy y red
- Configurar y validar proxies solo cuando Android, la aplicación o el método de conexión lo permitan.
- Probar conectividad, resolver errores, registrar estado y asignar configuración por dispositivo/perfil.
- Importación masiva de configuraciones y pruebas sin exponer credenciales en logs.
- Los proxies gratuitos públicos no se considerarán fiables ni necesarios; el sistema no ofrecerá servicios de proxy de pago como dependencia.
- Documentar que cambiar un proxy no cambia automáticamente la IP de red móvil, GPS, SIM ni todos los indicadores del dispositivo.

### M07 — Motor de automatización RPA
- Editor visual de flujos: acciones, secuencia, pausas, condiciones, bucles, variables, datos, capturas y manejo de errores.
- Acciones iniciales: abrir aplicación, tap, swipe, escribir, esperar, capturar pantalla, comprobar elemento/estado y ejecutar una operación ADB permitida.
- Guardar, editar, duplicar, versionar, importar/exportar y ejecutar flujos.
- Cola de ejecución, cancelación, timeout, reintentos controlados, idempotencia cuando aplique, logs y evidencia de resultado.
- Plantillas reutilizables y validación previa de acciones destructivas.
- No prometer que las interfaces de terceros son estables; cambios de UI y CAPTCHA/2FA pueden requerir intervención humana.

### M08 — Sincronizador multi-dispositivo
- Reproducir acciones compatibles de una instancia Android virtual principal a otras instancias virtuales seleccionadas.
- Mapeo de acciones, sincronización de tiempos, pausa/reanudación, dispositivos excluidos y estado por dispositivo.
- Manejo de diferencias de resolución, versión, idioma y pantallas; no asumir sincronía perfecta.
- Pruebas de seguridad para evitar ejecutar una acción en el dispositivo equivocado.

### M09 — Programación, colas y operaciones por lotes
- Programar flujos, ejecutar lotes, limitar concurrencia, pausar/reanudar y reintentar fallos.
- Cola persistente local, identificadores únicos, idempotencia y registro por tarea/dispositivo.
- Recuperación después de reinicio del programa/PC y políticas para tareas pendientes.
- En offline, permitir editar y poner en cola tareas locales; la ejecución de apps online y sincronización externa necesitarán conectividad.

### M10 — API local, CLI y eventos
- API documentada en localhost/LAN con autenticación, permisos y límites.
- CLI para inventario, dispositivos, aplicaciones y ejecuciones.
- Eventos/webhooks locales cuando sean útiles; alternativa de polling y cola local.
- No depender de la API de GeeLark ni de servicios remotos de pago.
- Seguridad por defecto: no publicar endpoints sin autenticación en Internet.

### M11 — Analítica, historial y auditoría
- Historial de operaciones, logs filtrables, errores, tiempos de ejecución y resultados por dispositivo/flujo.
- Paneles de éxito/fallo, uso de recursos y tendencias locales.
- Exportación CSV/JSON; retención configurable y protección de datos sensibles.
- La analítica solo reflejará datos disponibles localmente; no inventará métricas de plataformas sociales.

### M12 — Usuarios, grupos y permisos
- En primera instancia, uso local de un solo operador; después, usuarios y roles si se confirma necesidad.
- Grupos de dispositivos, asignaciones, permisos mínimos y auditoría.
- El acceso multiusuario por LAN añade riesgo y complejidad: se implementará después de asegurar la base local.
- Sin depender de un proveedor de identidad de pago.

### M13 — Funciones de IA y generación de contenido
- Separar funciones deterministas de IA generativa.
- Investigar modelos locales gratuitos/open source para texto, imágenes o vídeo solo si el hardware lo soporta y la licencia lo permite.
- Funciones que dependan de modelos comerciales o APIs de pago tendrán alternativa local o se marcarán como no equivalentes.
- No prometer calidad, velocidad ni generación de vídeo comparable a servicios cloud sin benchmarks en el equipo real.
- Este módulo no bloqueará el núcleo de dispositivos y automatización.

### M14 — Marketplace/recursos y plantillas
- Catálogo local de flujos y recursos, etiquetas, versiones, importación/exportación y validación de procedencia.
- Repositorio local de plantillas, sin asumir acceso al marketplace propietario de GeeLark.
- Recursos compartidos entre dispositivos con trazabilidad y límites de tamaño.

### M15 — PWA/offline y recuperación
- Evaluar una interfaz web local instalable como PWA si encaja con la arquitectura elegida.
- Caché de interfaz, datos de configuración en almacenamiento local, estado de conexión y cola de operaciones.
- No afirmar que el control Android funciona offline cuando depende de ADB/USB o de que el dispositivo esté conectado; no afirmar que las apps sociales funcionan sin Internet.
- Definir sincronización y resolución de conflictos solo si se incorpora más de un equipo o fuente de datos.

### M16 — Instalación, actualización y mantenimiento
- Instalador o procedimiento reproducible local, dependencias versionadas, configuración de desarrollo y producción.
- Actualización reversible, copias de seguridad, migraciones y diagnóstico.
- Builds reproducibles cuando sea viable y documentación para reinstalar sin SaaS obligatorio.

### M17 — Calidad, seguridad y paridad final
- Pruebas unitarias, integración, dispositivos reales, recuperación, rendimiento, carga y regresión.
- Matriz de paridad por función con estados: no investigado, investigado, implementado, probado, equivalente con adaptación, no viable.
- Revisión de licencias y seguridad; no copiar código, marca ni recursos propietarios.
- Cada módulo incluye manual completo de usuario y documentación técnica.

## 4. Orden de ejecución y puertas de aprobación

1. **Fase A — Inventario exhaustivo de GeeLark** (M00): estudiar documentación pública y flujos disponibles; producir matriz de paridad y mapa de pantallas.
2. **Fase B — Auditoría del hardware** (M01): recoger especificaciones reales y probar una instancia Android virtual.
3. **Fase C — Decisión técnica y arquitectura mínima** (M02): escoger stack tras evidencia, confirmar costo y límites.
4. **Fase D — Núcleo operativo** (M03 y M04): inventario, conexión, pantalla y control de una instancia Android virtual.
5. **Fase E — Operaciones Android** (M05 y M06): apps, archivos y red.
6. **Fase F — Automatización** (M07, M08 y M09): primero flujo individual, luego sincronización y lotes.
7. **Fase G — Integración y trazabilidad** (M10 y M11): API local, CLI, logs y analítica.
8. **Fase H — Colaboración y recursos** (M12 y M14).
9. **Fase I — IA local** (M13), condicionada a la auditoría de hardware y licencias.
10. **Fase J — Offline, instalación y robustez** (M15 y M16).
11. **Fase K — Validación integral** (M17): revisar todas las funciones de la matriz, documentar diferencias y no declarar paridad total mientras existan huecos.

**Regla:** no se inicia la fase siguiente hasta que la fase actual tenga entregables, pruebas, documentación y aceptación del usuario.

## 5. Criterios de aceptación por módulo

- Requisitos y alcance acordados y registrados en una issue.
- Evidencia de investigación o prueba repetible.
- Pruebas normales, de error, reconexión y recuperación aplicables.
- Comparación explícita con la función equivalente de GeeLark.
- Costos obligatorios: cero; límites y dependencias documentados.
- Seguridad y licencias revisadas.
- Manual de usuario paso a paso y documentación técnica actualizados.
- Issue cerrada solo tras revisión y aceptación; código/documentación versionados en GitHub.

## 6. Riesgos y restricciones conocidos

- Una instancia Android virtual local y un cloud phone de GeeLark no son equivalentes automáticamente en aislamiento, huella, sensores, arquitectura de CPU, rendimiento ni escalabilidad.
- El número de dispositivos simultáneos depende de hardware, puertos, alimentación, sistema operativo y rendimiento; se medirá.
- Algunas funciones de GeeLark se ejecutan en infraestructura cloud propia o dependen de servicios de IA comerciales; no se copiarán esos servicios y puede haber diferencias inevitables.
- Cambiar identificadores sensibles de hardware o fabricar una huella idéntica no se considera garantizado ni un requisito técnico aprobado.
- Las aplicaciones de terceros pueden limitar automatización y cambiar sus interfaces. El uso deberá respetar leyes, permisos y términos aplicables.
- La operación local no elimina costos indirectos de electricidad, hardware, mantenimiento o conexión a Internet para funciones online.

## 7. Primer paso inmediato

Completar M00 con la documentación pública disponible y, en paralelo, recopilar especificaciones del equipo anfitrión y definir el perfil de carga objetivo para instancias virtuales Android. No escribir todavía el núcleo de la aplicación ni elegir definitivamente el stack hasta cerrar el inventario inicial y la prueba de viabilidad.

## 8. Registro de investigación

- 2026-10-09: se aclara el alcance: el hardware físico será el equipo anfitrión; los dispositivos Android objetivo serán virtualizados/emulados localmente, no teléfonos físicos. La auditoría de hardware debe medir la viabilidad de instancias virtuales.
- 2026-10-09: investigación funcional ampliada registrada en [INVESTIGACION_FUNCIONAL_GEELARK.md](INVESTIGACION_FUNCIONAL_GEELARK.md) y matriz inicial en [MATRIZ_PARIDAD_GEELARK.md](MATRIZ_PARIDAD_GEELARK.md).

- 2026-10-09: primera revisión de la web pública y del Centro de ayuda de GeeLark. Áreas visibles: Profile, Proxies, Library, AIGC, Analytics, Applications, Automaton, Synchronizer, GeeHub, Resources, Referral, Billing, Members y Logs; documentación adicional de grupos, ADB y conexión de dispositivos locales. Automatización pública: plantillas, Synchronizer, RPA visual y API.
- Fuentes: https://help.geelark.com/ ; https://www.geelark.com/features/automation/ ; https://www.geelark.com/features/rpa/ ; https://www.geelark.com/features/api/ ; https://www.geelark.com/pricing/


## Actualización de auditoría funcional — 2026-10-09

Se creó el documento [CATALOGO_FUNCIONAL_GEELARK.md](CATALOGO_FUNCIONAL_GEELARK.md) para convertir el inventario general en subfunciones verificables. Las fuentes públicas recientes hasta GeeLark v4.5.2 muestran que hay que considerar, entre otros detalles, el inspector de interfaz/árbol UI para RPA, consulta posterior de parámetros de tareas, etiquetado de Library, carga masiva de archivos desde Synchronizer, operaciones masivas de aplicaciones, clonación de perfiles y configuración de red en determinadas versiones Android.

**Diferencia estructural confirmada:** la función GeeLark “Add Custom Phone” documenta la extracción de parámetros desde un Android físico conectado por USB/ADB. Como el alcance de Geelark-IA no depende de teléfonos físicos, esa función no puede considerarse idéntica. Se estudiará una identidad sintética por instancia, con límites claros, sin afirmar que equivale a una huella física real.

El catálogo sigue siendo parcial y documental. La matriz de paridad conserva estados preliminares; no se declara ninguna función equivalente ni se selecciona todavía un motor Android.
