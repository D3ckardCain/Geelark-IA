# Catálogo funcional detallado de GeeLark — avance de auditoría

**Fecha de actualización:** 2026-10-12  
**Versión del catálogo:** 0.1  
**Estado:** parcial; basado en documentación pública oficial y notas de versión. No equivale a inspección exhaustiva del cliente ni a pruebas prácticas.  
**Idioma:** español.

## 1. Propósito y reglas

Este catálogo convierte las áreas generales de la investigación en funciones verificables que después se implementarán o se marcarán como no equivalentes en Geelark-IA. GeeLark es la referencia observable. Ninguna capacidad se considerará replicada solo porque exista una función con nombre parecido.

- Registrar la fuente oficial y la fecha/versión cuando esté disponible.
- Separar funciones de gestión de Android de funciones de navegador, facturación o servicios propietarios.
- Para cada función, especificar entradas, salidas, estados, errores, permisos y restricciones antes de implementarla.
- No depender de la nube ni de APIs comerciales de GeeLark.
- El coste obligatorio de software/servicios del proyecto debe permanecer en 0 USD.
- Las funciones de Android son el alcance principal. Las funciones exclusivamente de navegador, iOS, marketplace propietario, pagos y operaciones de soporte cloud se marcarán como fuera de alcance o con adaptación explícita, sin ocultar la diferencia.

## 2. Perfiles Android

**Fuente principal:** [Centro de ayuda — Profile](https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8)

Funciones documentadas:
- Crear perfiles de forma individual, rápida y por lotes; las dos últimas aparecen restringidas por plan en GeeLark.
- Asignar un grupo existente o crear un grupo durante la creación.
- Elegir el sistema operativo y versión de Android.
- Asignar proxy guardado o introducir uno personalizado.
- Probar conectividad y ubicación aparente del proxy antes de confirmar.
- Elegir un modelo Android y método comercial de uso en GeeLark.
- La ayuda señala que un proxy expirado no se puede asignar.
- Las notas v3.9.0 indican clonado de perfiles y configuración de red celular/Wi-Fi personalizada para ciertos Android (12/13/15).

**Requisitos de adaptación local por especificar:**
1. Crear una instancia vacía con nombre, grupo, versión Android y recursos asignados.
2. Creación por lotes mediante formulario y archivo importable con validación por fila.
3. Editar configuración, clonar, exportar, importar, iniciar, detener, reiniciar y eliminar.
4. Mantener el estado de cada instancia y mostrar errores accionables.
5. Definir el comportamiento de clonación: copiar imagen/configuración sin duplicar accidentalmente identidad, credenciales, claves o datos privados.
6. No modelar tarifas comerciales cloud; medir recursos locales y explicar que el rendimiento depende del hardware.
7. Aclarar que el proxy solo enruta tráfico compatible y no modifica automáticamente todos los indicadores de red, SIM, GPS o hardware.

## 3. Proxies

**Fuente:** [Centro de ayuda — Proxies](https://help.geelark.com/Proxies-7fc88fa5ead344ff8b975cddf51592a9)

Funciones documentadas:
- Añadir, guardar, editar y eliminar proxies.
- Tipos: HTTP, HTTPS y SOCKS5.
- Campos habituales: tipo, host, puerto, usuario y contraseña.
- Importación de varias entradas, una por línea.
- Prueba de conexión/IP y consulta de ubicación por canales externos de geolocalización IP.
- Visualización de información detallada, incluida ciudad aproximada.

**Requisitos de adaptación local por especificar:**
- Validación de formato, prueba de conectividad con timeout y códigos de error.
- Credenciales cifradas en reposo cuando la arquitectura lo permita; nunca registrarlas en logs.
- Asignación de proxy por instancia y estado de salud.
- Distinguir “proxy accesible”, “IP detectada” y “geolocalización estimada”; no presentar estos resultados como garantía de anonimato.
- Los proxies de terceros no son un servicio gratuito provisto por Geelark-IA.

## 4. RPA / Automaton

**Fuentes:** [Automaton](https://help.geelark.com/AI-featured-RPA-b93ed760fada424291afe759a27ff7e3?pvs=21), [página de automatización](https://www.geelark.com/features/automation/), [página RPA](https://www.geelark.com/features/rpa/).

Funciones documentadas:
- Editor visual de flujos por arrastrar y soltar.
- Flujos personalizados y plantillas reutilizables.
- Selección previa de los teléfonos que ejecutarán cada tarea.
- Reutilización y programación de flujos.
- Acciones de interfaz documentadas en páginas públicas: toques/clics, deslizamientos, scroll, entrada de texto, esperas, carga de archivos y operaciones de aplicaciones.
- Lógica de flujo: variables, condiciones, bucles y manejo de errores, según la descripción pública de RPA.
- La documentación v4.5.0 añade inspector de diseño/interfaz para flujos de cloud phone y opción “Is checked” en recuperación de datos de elementos.
- La documentación v4.5.1 menciona análisis de alcance del layout, apertura y guardado del archivo de árbol UI.
- La documentación v4.5.2 indica que los registros permiten abrir “View Task” y revisar parámetros configurados después de publicar una tarea.
- La documentación v3.9.8 registra importación/exportación de plantillas en GeeLark Automation Language, una operación “Get element data” y una operación “Clear the folder”.

**Pendiente de investigar en el manual RPA oficial:**
- Catálogo exhaustivo de bloques y parámetros.
- Tipos de dato, variables globales/locales, salida de bloques y propagación de errores.
- Selectores por texto, ID, paquete, jerarquía y coordenadas.
- Capturas, esperas, reintentos, límites de ejecución, cancelación y resultados parciales.
- Esquema/formato del lenguaje exportado, validación y compatibilidad entre versiones.
- Programación, concurrencia, límites por tarea y reportes.

**Adaptación local:** motor de flujo versionado, editor visual, esquema portable, cola de tareas persistente, cancelación/reintentos explícitos, aislamiento por instancia y logs redactados. No se importarán plantillas propietarias ni se dependerá de su marketplace; el formato local será propio y documentado.

## 5. Synchronizer

**Fuente:** [Centro de ayuda — Synchronizer](https://help.geelark.com/Synchronizer-82c1c9a8f62d489ca81b1f753d2a7bfa).

Funciones documentadas:
- Sincronizar acciones de un cloud phone principal hacia otros teléfonos seleccionados.
- La ayuda recomienda seleccionar teléfonos apagados y del mismo tipo para reducir diferencias de interfaz.
- La versión consultada enumera Android 9–15 como compatibles.
- La nota v3.9.8 documenta entrada masiva de texto diferente en distintos teléfonos.
- La nota v3.9.1 documenta modo de pantalla completa.
- La nota v4.5.1 documenta carga masiva de archivos y consulta del historial de cargas.

**Adaptación local:**
- Sesión de sincronización con instancia fuente y destinos seleccionados explícitamente.
- Eventos compatibles (toque, deslizamiento, scroll, entrada de texto, teclas y carga de archivos) según soporte real del motor.
- Mostrar estado y errores por destino; permitir pausar, reanudar y detener.
- No ocultar divergencias de resolución, orientación, versión Android, latencia o estado de aplicaciones.
- Probar si la sincronización requiere que los destinos estén detenidos antes de iniciar la sesión o si el comportamiento local será diferente.

## 6. Biblioteca local / Library

**Fuentes:** [Centro de ayuda](https://help.geelark.com/) y notas de versión [v4.5.2](https://help.geelark.com/v4-5-2-3e40be7d9e418006a508d2f22696e0fb?pvs=21).

Funciones documentadas:
- Carga y administración de recursos multimedia.
- Etiquetas de recursos; v4.5.2 añade edición de etiquetas y selector de etiquetas en el diálogo de carga de archivos locales.
- Vistas de tarjetas y lista.
- Los flujos pueden utilizar recursos de la biblioteca; una plantilla de publicación de vídeo puede iterar sobre activos de una etiqueta.
- La cifra de 100 GB y la retención de 30 días mencionadas en una página de ayuda describen el servicio GeeLark, no un límite que debamos copiar a una biblioteca local.

**Adaptación local:**
- Archivos locales, etiquetas, filtros, metadatos, vista previa, hashes para detectar duplicados, exportación y copia de seguridad.
- Permitir que RPA consulte recursos por ID/etiqueta sin depender de almacenamiento remoto.
- Límites configurables por disco disponible, con avisos antes de agotar espacio.

## 7. Aplicaciones Android

**Fuentes:** [Centro de ayuda](https://help.geelark.com/) y notas de versión [v3.8.0](https://help.geelark.com/v3-8-0-3080be7d9e41816a8b2bc0bbc2964ed1?pvs=21), [v3.9.0](https://help.geelark.com/v3-9-0-3080be7d9e4181099973d62272a9c309?pvs=21).

Funciones documentadas:
- Operaciones masivas sobre aplicaciones para grupos de perfiles: abrir, cerrar, reiniciar y desinstalar.
- Actualización de versiones.
- Instalación automática dirigida a grupos específicos, según v3.9.8.
- El resultado dependerá de arquitectura de APK, permisos, versión Android, licencias y disponibilidad legal de la aplicación.

**Adaptación local:**
- Enumerar paquetes instalados por instancia; instalar APK, abrir, detener, actualizar y desinstalar.
- Registrar resultado por instancia y por paquete, con errores como ABI incompatible, falta de espacio, fallo de instalación o paquete no encontrado.
- No descargar ni redistribuir aplicaciones propietarias sin autorización; el usuario aportará APK o fuentes legítimas cuando proceda.

## 8. API, CLI, ADB y eventos

**Fuentes:** [GeeHub/API](https://help.geelark.com/API-2f50be7d9e4180358f4ee14f4c958889), [API de producto](https://www.geelark.com/features/api/), [guía ADB](https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad).

Funciones documentadas:
- API para crear, iniciar, detener y eliminar perfiles, además de gestión de apps, archivos, ADB y tareas.
- El centro de ayuda enlaza documentación API y un CLI público de GeeLark.
- La nota v3.8.0 añade token Bearer y endpoints para gestión multimedia con etiquetas e informes de tareas.
- La nota v3.9.1 menciona creación de perfiles por lotes en OpenAPI.
- ADB permite ejecutar comandos contra teléfonos cloud según la guía.

**Adaptación local:**
- API HTTP local y CLI propias; no copiar claves ni depender de la API de GeeLark.
- Autenticación local, permisos mínimos, límites de tasa configurables, validación de entradas y auditoría.
- Operaciones de escritura idempotentes cuando sea posible; identificadores únicos de tarea y recuperación ante reinicios.
- ADB limitado a instancias locales y puertos internos; no exponer ADB sin protección en la red.
- Definir eventos y webhooks locales opcionales, con cola persistente, reintentos e idempotencia.

## 9. Logs, informes y analítica

**Fuentes:** [centro de ayuda](https://help.geelark.com/), notas [v4.5.1](https://help.geelark.com/v4-5-1-3d60be7d9e4180c5a0bef756578b881e?pvs=21) y [v4.5.2](https://help.geelark.com/v4-5-2-3e40be7d9e418006a508d2f22696e0fb?pvs=21).

Funciones documentadas:
- Logs de operación y tareas.
- En v4.5.2, “View Task” permite consultar parámetros configurados tras publicar la tarea.
- Los informes de ejecución incluyen nombres de recursos, según v4.5.0.

**Adaptación local:**
- Registro por instancia, tarea, bloque, archivo y marca temporal.
- Estados mínimos: pendiente, en cola, ejecutando, completada, fallida, cancelada y resultado parcial.
- Métricas de duración, reintentos, errores y recursos del anfitrión.
- Redacción de contraseñas, tokens, cookies y otros secretos.
- Exportación local en formatos abiertos.

## 10. IA/AIGC, recursos externos y presupuesto

**Fuentes:** [centro de ayuda](https://help.geelark.com/), notas [v4.5.0](https://help.geelark.com/v4-5-0-3c90be7d9e4180a2b575c7112e7b34d0) y [v4.5.2](https://help.geelark.com/v4-5-2-3e40be7d9e418006a508d2f22696e0fb?pvs=21).

Las notas recientes mencionan modelos de generación integrados y seguimiento de uso. Estos proveedores no cumplen automáticamente el requisito de coste obligatorio cero.

**Adaptación local:**
- Auditar cada función de IA por separado.
- Preferir modelos que puedan ejecutarse localmente con licencia compatible, sin API de pago.
- Medir RAM/VRAM, almacenamiento, velocidad, calidad y restricciones de licencia.
- Si el hardware no puede ejecutar una función local con calidad suficiente, documentar la diferencia y no presentarla como equivalente.
- No crear dependencias en servicios externos de generación de imagen/video ni en un proveedor de modelo concreto.

## 11. Funciones no Android o estructuralmente distintas

| Función GeeLark | Tratamiento del proyecto |
|---|---|
| Perfiles de navegador y su Synchronizer | Fuera del alcance principal Android; registrar explícitamente, no confundir con sincronización de Android |
| iOS | Excluido por decisión del proyecto |
| Facturación, suscripciones, alquiler cloud y minutos | No se replican cobros; se sustituyen por administración local de recursos |
| Soporte remoto de GeeLark y mantenimiento de cloud phones | No aplica a instancias locales; sustituir por diagnóstico local controlado por el propietario |
| Marketplace y plantillas propietarias | No copiar activos sin licencia; implementar catálogo local importable/exportable |
| Modelos AIGC comerciales integrados | Solo alternativa local gratuita compatible con licencias |
| Infraestructura cloud, escalado remoto y red de dispositivos GeeLark | Sustituida por capacidad física local; límites dependen del anfitrión |
| Funciones que requieran SIM, llamadas o SMS reales | No prometer equivalencia sin soporte de hardware/servicio apropiado |

## 12. Hallazgos recientes de notas de versión

La página oficial de notas de versión consultada el 2026-10-09 llega a v4.5.2, con fecha de edición 2026-09-23. Los cambios de v4.5.0–v4.5.2 revelan que el catálogo debe incluir no solo funciones base, sino también:
- edición y asignación de etiquetas en Library, vistas de tarjeta/lista y seguimiento de uso AIGC;
- ejecución iterativa de activos por etiqueta y configuración avanzada de plantillas;
- visualización posterior de parámetros de tareas;
- inspección del árbol UI y datos de elementos;
- carga masiva de archivos desde Synchronizer;
- configuración de red celular/Wi-Fi y clonación de perfiles, según v3.9.0;
- importación/exportación de flujos RPA y operaciones de carpetas, según v3.9.8.

La lista no es exhaustiva de todas las versiones históricas. Se debe continuar con las guías completas de Profile management, Applications, Library, ADB, API y el manual RPA.

## 13. Próximas tareas de auditoría

1. Completar el catálogo de campos y acciones de creación/edición/clonación de perfiles.
2. Desglosar todos los bloques del manual RPA con entradas, salidas y errores.
3. Enumerar operaciones/endpoints de API con método, parámetros, respuesta, autenticación y errores.
4. Completar funciones de Library, Applications, Groups, Members, Logs y Analytics.
5. Documentar las funciones de red, cámara, GPS, sensores y ADB.
6. Completar la matriz con criterios de aceptación y enlaces de evidencia por función.
7. Hacer la prueba comparativa de motor Android local tras recopilar las especificaciones del anfitrión.

## 14. Historial

- 2026-10-09: creación del catálogo detallado inicial con evidencia de Profile, Proxies, RPA, Synchronizer, Library, Applications, API/ADB y notas de versión hasta v4.5.2.


## 15. Hallazgos adicionales: grupos, perfiles y huella de dispositivo

### 15.1 Gestión de perfiles y grupos

**Fuente:** [Profile management / Groups](https://help.geelark.com/Group-management-c91b6291bb954a69a5d231781a03d0e1).

La guía documenta:
- Filtrar perfiles por grupo, categoría y otros criterios.
- Editar perfiles cuando están cerrados.
- Transferir perfiles a otros usuarios; la transferencia descrita es irreversible para quien transfiere.
- Crear grupos, editar sus nombres, eliminarlos y fusionarlos.
- Consultar el número de perfiles de cada grupo.
- Mover perfiles a otro grupo y conceder acceso a otros miembros.

**Adaptación local requerida:**
- Definir una papelera de reciclaje para instancias eliminadas y política de retención recuperable, configurable y documentada.
- Operaciones de grupo deben ser transaccionales o informar qué elementos fallaron.
- Las transferencias entre usuarios no se consideran idénticas a GeeLark: en modo local equivaldrán a cambiar propietario/permisos o exportar/importar un paquete cifrado, según el modo de operación.
- Toda operación destructiva debe mostrar confirmación y registrar auditoría.

### 15.2 Instalación y actualización de aplicaciones

**Fuente:** [Applications](https://help.geelark.com/Applications-95cfce3d74e443b8a5f57f5123669e60).

La ayuda documenta instalación individual desde una tienda disponible en el teléfono, Google Play o un APK aportado; instalación por lotes de aplicaciones asignadas a grupos; y actualización individual o masiva. Para APK/XAPK cargados, las operaciones por lotes se administran desde el apartado de aplicaciones del equipo.

**Adaptación local requerida:**
- Permitir APK proporcionado por el usuario y repositorios legítimos configurados voluntariamente.
- No integrar una tienda propietaria ni redistribuir APKs de terceros sin permiso.
- Validar firma, ABI, espacio libre, versión mínima de Android y resultado de instalación.
- Una aplicación asignada a un grupo puede quedar en cola y aplicarse cuando la instancia vuelva a iniciar, si así se especifica.
- Registrar estado por instancia y no dar por exitosa toda una operación por lotes si hubo fallos parciales.

### 15.3 Huella de dispositivo y dependencia de teléfono físico

**Fuente:** [Add Custom Phone / Team device library](https://help.geelark.com/Add-Custom-Phone-2ee0be7d9e418045ac69ffd6eb043e63?pvs=21).

La documentación oficial describe una función que recopila parámetros de un dispositivo Android físico conectado por USB mediante ADB y permite aplicar esa información a un cloud phone. La guía menciona versiones Android 9, 10, 11, 12, 13 y 15.

**Implicación crítica para Geelark-IA:** el alcance confirmado no contempla teléfonos físicos como fuente de huella. Por tanto, no debemos prometer equivalencia exacta con esta función concreta. La alternativa local será generar/configurar una identidad sintética por instancia con los campos que el motor realmente permita modificar y documentar de forma explícita qué señales permanecen fijas, derivadas del host o detectables como virtualizadas. No se afirmará que una identidad sintética equivale a la huella de un dispositivo físico real.

Esta limitación no impide estudiar ni replicar el resto del sistema de perfiles, pero sí debe aparecer como diferencia funcional explícita en la matriz y en el manual de usuario.

### 15.4 Operaciones masivas y límites de versiones

Las notas de versión consultadas documentan límites/operaciones concretos en distintas versiones: sustitución por lotes de dispositivos (v3.6.0), prueba por lotes de proxies (v3.9.1), creación por lotes por API (v3.9.1) y configuración de red por perfil para ciertas versiones Android (v3.9.0). Esas notas demuestran que las capacidades han cambiado con el tiempo; no deben tratarse como garantía de que cada límite sigue vigente en la versión actual.

La implementación local deberá usar límites configurables según recursos anfitriones y mostrar el resultado por elemento. Los límites históricos de GeeLark sirven como evidencia de funcionalidad, no como límites obligatorios para nuestro producto.


## 16. Decisión de alcance: importar configuración e identidad desde Android físico

**Fecha:** 2026-10-09. **Estado:** aprobado como vía candidata de investigación por decisión del usuario; viabilidad técnica pendiente de pruebas.

Se contemplan dos vías compatibles, no excluyentes:

1. **Identidad sintética:** definir una configuración propia para cada instancia Android virtual, dentro de los campos que el motor y Android permitan controlar.
2. **Importación desde Android físico:** conectar un dispositivo compatible por USB/ADB, consultar los parámetros disponibles y permitir seleccionar cuáles se importarán como configuración de una instancia virtual.

### Flujo local propuesto
1. Detectar dispositivos ADB conectados y mostrar modelo, versión Android, estado de autorización y número de serie enmascarado cuando corresponda.
2. Explicar los permisos solicitados y solicitar confirmación explícita antes de leer o importar parámetros.
3. Obtener únicamente los campos documentados y técnicamente accesibles mediante interfaces autorizadas.
4. Presentar una vista previa campo por campo: valor detectado, importable sí/no, editable sí/no, motivo de incompatibilidad y efecto previsto.
5. Permitir seleccionar campos; excluir por defecto datos privados, credenciales, cuentas, tokens, contenido de usuario y datos de aplicaciones.
6. Guardar un perfil de importación local, con fecha, dispositivo de origen identificado de forma segura y procedencia de cada campo.
7. Aplicar solo los campos que admita la instancia destino; verificar el resultado tras reinicio y mostrar diferencias.
8. Mantener separados el origen físico, el perfil de importación y la identidad efectiva de la instancia virtual.

### Límites y salvaguardas
- No prometer una copia íntegra ni una identidad indistinguible de un teléfono físico real.
- Algunos identificadores protegidos, claves de hardware, señales de integridad/attestation, datos de SIM, módem, sensores y atributos derivados del host pueden ser inaccesibles o no modificables desde una VM/contenedor.
- No eludir controles de seguridad, attestation ni mecanismos antiabuso de aplicaciones.
- No copiar datos personales no solicitados; permitir revisar y excluir cada campo.
- No hacer escritura ni cambios en el dispositivo físico de origen durante la importación.
- Cifrar los perfiles exportados cuando contengan información sensible; nunca incluir secretos en logs.
- Verificar licencias, permisos, compatibilidad Android/ADB y límites de cada motor antes de implementar.

### Pruebas de aceptación pendientes
- Detectar un dispositivo compatible y uno no autorizado, con errores comprensibles.
- Mostrar inventario de campos realmente legibles sin modificar el origen.
- Importar una selección a un perfil de prueba y documentar campos aplicados/no aplicados.
- Reiniciar la instancia y comprobar persistencia de cada campo aplicable.
- Confirmar que cuentas, archivos personales, tokens y datos de apps no se importan por defecto.
- Probar desconexión USB, cancelación, permisos denegados y fallos parciales.
- Comparar resultados observables del origen y del destino, documentando cada diferencia.

Esta capacidad amplía el alcance aprobado, pero sigue siendo investigación hasta completar las pruebas con hardware compatible.


### 16.1 Compatibilidad objetivo: Android de cualquier marca y versión (progresiva)

**Decisión del usuario, 2026-10-09:** el objetivo es admitir cualquier teléfono Android que permita conexión mediante ADB, sin limitar el diseño inicial a una marca concreta.

Esto define un objetivo de compatibilidad amplia, no una garantía inmediata de que todos los dispositivos, versiones o fabricantes funcionarán igual. La compatibilidad se incorporará progresivamente y se publicará con evidencia.

- Diseñar un adaptador ADB genérico y separar la detección de dispositivo de las capacidades específicas de fabricante/versión.
- Detectar y registrar fabricante, modelo, versión Android/API, estado ADB y capacidades observadas; evitar almacenar identificadores completos innecesarios.
- Crear una matriz de compatibilidad por versión Android, fabricante/modelo probado, sistema anfitrión, versión de herramientas ADB y campos que realmente se pueden leer/importar.
- Clasificar cada combinación como **no probada**, **detectada**, **lectura validada**, **importación parcial validada** o **compatibilidad validada para campos concretos**. No usar una etiqueta genérica de “compatible” sin indicar qué se probó.
- Empezar con dispositivos disponibles para pruebas y añadir fabricantes/versiones según se obtenga hardware o evidencia reproducible.
- Ante campos no disponibles, restricciones del fabricante o permisos denegados, mostrar una explicación y continuar con el resto cuando sea seguro.
- Mantener la lectura como modo predeterminado; cualquier operación de importación/aplicación requiere vista previa y confirmación explícita.
- No asumir que una versión de Android reciente, un fabricante específico o un teléfono con ADB autorizado expone todos los mismos campos.

**Criterio de aceptación:** cada combinación incluida en la lista de compatibilidad debe tener resultados de pruebas reproducibles, lista de campos admitidos y no admitidos, errores conocidos y versión de herramientas utilizada. Hasta entonces, se describe como objetivo de diseño, no como compatibilidad demostrada.


## 17. Verificación directa de guías oficiales — RPA, API y Synchronizer

**Consulta:** 2026-10-09. Estas observaciones proceden del texto visible de las guías oficiales; no sustituyen la inspección de todas las pantallas ni pruebas del producto.

### 17.1 Automaton / RPA

La guía oficial «Automaton» confirma explícitamente:
- Editor de flujos de arrastrar y soltar para usuarios no técnicos.
- Reutilización de flujos y posibilidad de programarlos.
- Biblioteca de plantillas para escenarios/plataformas; selección de plantilla, configuración y publicación de una tarea automatizada.
- Creación de flujos propios en la sección de tareas personalizadas.
- Selección previa de los cloud phones que ejecutarán cada tarea.
- Acceso a una función de generación de contenido llamada GeeLark AI, descrita en esa guía como integrada con DeepSeek.

Fuente: https://help.geelark.com/AI-featured-RPA-b93ed760fada424291afe759a27ff7e3?pvs=21

**Implicaciones para la especificación local:**
1. Separar el editor/definición del flujo de la tarea publicada y de sus ejecuciones concretas.
2. Guardar una selección explícita de instancias destino al crear una tarea, con validación si la instancia no existe, está apagada o no admite la versión requerida.
3. Versionar el flujo y registrar qué versión se ejecutó, quién la inició, destinos, programación, estado y resultados parciales.
4. La biblioteca local debe permitir plantillas propias/importables de formato documentado, pero no depender del marketplace propietario ni copiar sus activos.
5. La IA integrada comercial se auditará como función separada. No se usará una API de pago ni se afirmará que el proveedor mencionado en GeeLark cumple el objetivo de 0 USD; cualquier alternativa debe evaluarse para ejecución local y licencia compatible.

**Pendiente de evidencia:** la guía general no enumera todos los bloques, parámetros, tipos de dato, reglas de reintento ni formato de archivo. No inferirlos; deben extraerse de la documentación técnica específica y probarse.

### 17.2 API y CLI

La guía oficial GeeHub/API indica que la API de GeeLark permite, programáticamente, crear, iniciar, detener y eliminar cloud phones, gestionar archivos y aplicaciones, ejecutar comandos ADB y procesar tareas automatizadas. También indica que el cliente dispone de un API Key y enlaza un CLI para gestionar cloud phones, navegadores, proxies, grupos, etiquetas, facturación y otras funciones.

Fuentes:
- https://help.geelark.com/API-2f50be7d9e4180358f4ee14f4c958889
- https://open.geelark.com/api
- https://github.com/geelark-tech/geelark-cli

**Implicaciones para la API local:**
- La primera especificación de endpoints debe cubrir ciclo de vida de instancia, estado, aplicaciones, archivos, ejecución ADB y tareas.
- Separar el API local de cualquier endpoint o clave de GeeLark. No copiar ni requerir API Keys de GeeLark.
- Diseñar autenticación local revocable, permisos mínimos, límites de tasa, validación, trazabilidad, operaciones idempotentes y errores por elemento.
- La CLI local debe ser una interfaz del API propio y no una dependencia del CLI de GeeLark.
- La lista completa de endpoints, métodos HTTP, parámetros, esquemas de respuesta, paginación y errores sigue pendiente de revisar en la documentación técnica publicada.

### 17.3 Synchronizer

La guía oficial consultada señala que Synchronizer está disponible en suscripción Pro de GeeLark y enumera compatibilidad Android 9 a 15 para la función descrita. También indica que las acciones de un cloud phone se sincronizan con otros cloud phones y recomienda seleccionar dispositivos apagados y del mismo tipo para reducir diferencias de interfaz. La misma página distingue la sincronización de perfiles de navegador como función diferente.

Fuente: https://help.geelark.com/Synchronizer-82c1c9a8f62d489ca81b1f753d2a7bfa

**Implicaciones para Geelark-IA:**
- No copiar la restricción comercial Pro como dependencia: el sincronizador local se evaluará como función propia sin servicio de suscripción obligatorio.
- La selección de destinos y la compatibilidad se comprobarán antes de iniciar; la interfaz mostrará diferencias de resolución, versión y estado.
- Tratar sincronización Android y sincronización de perfiles de navegador como áreas distintas; esta última queda fuera del alcance principal Android.
- La guía general no determina todos los eventos ni garantiza que cada acción sea reproducible en destinos diferentes. La matriz de eventos soportados requiere pruebas.

## 18. Registro de cambios

- 2026-10-09: contraste directo de las guías oficiales de Automaton, GeeHub/API y Synchronizer; se añadieron implicaciones de diseño y límites de evidencia sin declarar paridad.


## 19. Verificación directa de perfiles, proxies, aplicaciones y grupos

**Consulta:** 2026-10-09. Esta sección registra únicamente lo que las guías oficiales consultadas muestran de forma explícita.

### 19.1 Creación de perfiles

La guía Profile confirma tres modalidades: creación individual, rápida y por lotes; la guía señala que las dos últimas están reservadas a Pro en GeeLark. Para la creación individual describe grupo, sistema operativo, proxy, comprobación del proxy, método de facturación del modelo Android y selección de versión del sistema operativo. Los proxies guardados muestran país y número de perfiles asociados; se admite asignación aleatoria con preferencia por proxies no utilizados y no se admite asignar un proxy expirado.

Fuente: https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8

**Especificación local pendiente:**
- Separar el concepto de perfil/configuración de la instancia Android ejecutable.
- Formularios individual y por lotes deben compartir validadores y mostrar errores por campo/fila.
- En modo local, sustituir el método de facturación cloud por asignación de recursos locales; no replicar tarifas por minuto.
- Definir estados de instancia (creada, iniciando, activa, deteniéndose, detenida, fallida, eliminando) con transiciones válidas y recuperación.
- Documentar campos de versión/modelo que el motor realmente soporte; no exponer opciones que no puedan aplicarse.
- Un proxy es opcional según el diseño local si la instancia funciona sin él; su estado debe diferenciarse de la disponibilidad de la instancia.

### 19.2 Proxies

La guía oficial confirma los campos tipo, host, puerto, usuario y contraseña; los tipos HTTP, HTTPS y SOCKS5; importación por lotes de una entrada por línea con formato tipo://host:puerto:usuario:contraseña; y comprobaciones de conexión/IP/ubicación usando los canales IP2Location e IP-API.

Fuente: https://help.geelark.com/Proxies-7fc88fa5ead344ff8b975cddf51592a9

**Especificación local pendiente:**
- El importador debe validar líneas individualmente, no registrar contraseñas en errores ni logs y ofrecer previsualización antes de guardar.
- La prueba de conexión debe indicar timeout, resolución DNS, conexión, autenticación y consulta de IP como etapas separadas cuando la biblioteca lo permita.
- La geolocalización IP es estimada y depende del proveedor; no garantiza ubicación física ni anonimato.
- No se dependerá de IP2Location/IP-API para funciones críticas; la consulta externa será opcional, visible y desactivable. La prueba básica de conectividad debe funcionar sin servicio de geolocalización.
- No se incluirá un proveedor proxy de pago. El usuario podrá introducir un proxy propio; operar sin proxy también debe ser posible cuando la aplicación lo permita.

### 19.3 Aplicaciones

La guía Applications confirma instalación/actualización individual o por lotes. La instalación individual puede realizarse desde Google Play o mediante APK aportado. La guía describe asignación de una aplicación a un grupo para que se instale al iniciar los cloud phones del grupo; también describe cargas APK/XAPK y actualizaciones por grupo. Para aplicaciones instaladas desde archivos cargados, la guía indica eliminar la versión anterior antes de subir e instalar la nueva.

Fuente: https://help.geelark.com/Applications-95cfce3d74e443b8a5f57f5123669e60

**Especificación local pendiente:**
- Separar archivo APK/XAPK, paquete Android, versión instalada y política de despliegue por grupo.
- Validar paquete, firma, ABI, versión mínima, espacio y compatibilidad antes de ejecutar la instalación.
- La asignación por grupo será una política persistente: se aplicará en el siguiente arranque si así se configura y se informará del estado por instancia.
- No integrar ni redistribuir Google Play, APK/XAPK ni aplicaciones de terceros sin autorización y sin revisar sus condiciones. El flujo base debe aceptar archivos aportados legítimamente por el usuario.
- Una actualización por lotes tendrá resultados individuales y recuperación ante fallos parciales.

### 19.4 Grupos y administración de perfiles

La guía Profile management confirma filtros por grupo/categoría, edición cuando el perfil está cerrado, transferencia de perfiles a otro usuario (irreversible en el flujo descrito), y creación, renombrado, eliminación y fusión de grupos. También permite mover perfiles a otro grupo y conceder acceso a miembros.

Fuente: https://help.geelark.com/Group-management-c91b6291bb954a69a5d231781a03d0e1

**Especificación local pendiente:**
- La edición de configuración de una instancia se bloqueará mientras esté ejecutándose si el motor no soporta cambios seguros en caliente.
- La fusión de grupos definirá cómo resolver nombres duplicados, reglas de acceso y políticas de aplicación.
- Las operaciones masivas deberán mostrar una vista previa, un resumen de alcance y resultados por elemento.
- En Geelark-IA, transferir propiedad será una operación local reversible o exportación/importación explícita; no se replicará una transferencia irreversible por defecto.
- Borrar un grupo no debe borrar silenciosamente las instancias que contiene; la regla deberá explicarse en el manual y probarse.

## 20. Criterios de aceptación derivados de las guías

Estos criterios se proponen para el producto local y no implican que ya estén implementados:

1. Crear un perfil individual con grupo, versión Android y configuración de red válida; mostrar un error accionable si la imagen no existe.
2. Crear perfiles por lotes desde archivo con validación por fila y un identificador estable por perfil.
3. Probar un proxy con timeout; distinguir proxy no accesible, credenciales inválidas, consulta de IP fallida y geolocalización no disponible.
4. Importar proxies por lotes con vista previa y sin exposición de credenciales en logs.
5. Asignar una APK válida a un perfil y comprobar instalación; probar paquete incompatible y falta de espacio.
6. Asignar una aplicación a un grupo y comprobar su aplicación al siguiente inicio, registrando los fallos por instancia.
7. Filtrar perfiles por grupo/estado y mover varios perfiles con confirmación previa.
8. Intentar editar una instancia en ejecución y comprobar que el sistema bloquea o usa un mecanismo seguro documentado.
9. Crear, renombrar, fusionar y eliminar un grupo sin perder perfiles por accidente.
10. Verificar que la UI diferencia funciones de GeeLark que dependen de suscripciones o servicios cloud de las alternativas locales gratuitas.

## 21. Historial adicional

- 2026-10-09: revisión directa de las guías Profile, Proxies, Applications y Profile management; se registraron campos, restricciones y criterios de aceptación pendientes.


## 22. Inventario ampliado del CLI público de GeeLark (solo referencia funcional)

**Fuente revisada:** repositorio público oficial GeeLark CLI, README y comandos documentados: https://github.com/GeeLark/geelark-cli  
**Licencia que declara el repositorio:** MIT. Esta revisión se usa únicamente para inventariar capacidades observables; Geelark-IA tendrá implementación propia y no copiará código ni dependerá del CLI, API, token o servicio de GeeLark.

### 22.1 Categorías funcionales documentadas

El README del CLI publica estas familias de capacidades:

| Categoría | Acciones que enumera la documentación | Tratamiento en Geelark-IA |
|---|---|---|
| Gestión de teléfono/perfil | Listar, crear, iniciar, detener, eliminar, actualizar, clonar, capturar pantalla, GPS, restablecer, root, SMS, transferencia y contactos | Incluir ciclo de vida, captura y GPS solo tras probar soporte real. Root será una opción de laboratorio explícita. SMS/telefonía real no se prometerá sin módem/SIM/servicio compatible. |
| Automatización | Consultar tareas/historial, cancelar/reiniciar tareas, crear tareas personalizadas programadas y acciones predefinidas por plataforma | Implementar un motor local genérico y auditable; las recetas específicas de plataformas se evaluarán individualmente, sin automatizar acciones que infrinjan reglas del servicio destino. |
| Aplicaciones | Catálogo, instalación, desinstalación, inicio, detención, carga, operaciones por lotes y política de aplicaciones de equipo/grupo | Adaptar a APK/paquetes locales y despliegues por grupo; no integrar marketplace propietario ni redistribuir apps sin permiso. |
| Archivos | Subida temporal, transferencia al dispositivo, consultas de estado y operación keybox | Biblioteca y transferencia locales. No replicar almacenamiento temporal cloud ni copiar material sensible de keybox sin requisito y análisis de seguridad. |
| Library | Crear/buscar/eliminar recursos multimedia y gestionar etiquetas | Biblioteca local persistente con etiquetas, hash, vista previa, copia de seguridad y límites por disco. |
| ADB y shell | Consultar conexión ADB, activar/desactivar ADB y ejecutar comandos shell | Puente ADB solo a instancias propias; autenticar la API local, limitar comandos y no exponer ADB a redes no confiables. |
| Webhooks | Consultar y configurar URL de callback | Webhooks locales opcionales con cola persistente, firma, reintentos, idempotencia y validación de destino para reducir SSRF. |
| Proxy | Listar, añadir, actualizar, eliminar y comprobar proxies | Gestión local de HTTP/HTTPS/SOCKS5, secretos protegidos y comprobaciones de red independientes de geolocalización externa. |
| Grupos y etiquetas | CRUD de grupos y etiquetas | CRUD transaccional con resultados por elemento y auditoría. |
| Analítica | Gestionar cuentas de analítica y consultar datos | Métricas propias de instancias/tareas; conectores externos solo si son opcionales, legítimos y no requieren pagos obligatorios. |
| Navegador | Perfiles de navegador, captura y automatización | Fuera del alcance principal Android; no mezclar con perfiles de instancias Android. |
| Facturación y planes | Saldo, transacciones, planes, renovación, compra de tiempo y paralelismo | Fuera de alcance como cobro. Sustituir por uso local de CPU/RAM/disco y límites configurables, sin pagos ni tarifas por minuto. |
| Personalización OEM | Marca, logotipo, cabecera y barra de herramientas | Valorar como personalización de la interfaz propia, sin usar la marca/activos de GeeLark. |

### 22.2 Contratos de API local que se deben especificar

Antes de programar el API, documentar como mínimo los siguientes grupos de operaciones:

1. **Instancias:** crear, listar, consultar, actualizar, clonar con identidad nueva por defecto, iniciar, detener, reiniciar, eliminar y consultar estado.
2. **Captura/control:** captura de pantalla, entrada de toque/deslizamiento/teclado, orientación y resolución si el motor lo admite.
3. **Configuración del dispositivo:** versión Android, resolución/DPI, red, ubicación de prueba y campos de identidad sintética admitidos; los campos no soportados deben declararse.
4. **Aplicaciones:** enumerar paquetes, instalar desde archivo local, consultar progreso, iniciar, detener, actualizar y desinstalar.
5. **Archivos y biblioteca:** subir/importar archivos, consultar progreso, listar/buscar/etiquetar/eliminar activos y transferir archivos hacia/desde la instancia.
6. **ADB:** consultar conexión, abrir/cerrar acceso local y ejecutar comandos permitidos con timeout; no exponer shell arbitrario a usuarios no autorizados.
7. **Tareas RPA:** crear, validar, publicar, programar, ejecutar, cancelar, reintentar, consultar estado/historial y descargar informes.
8. **Grupos/etiquetas:** crear, editar, listar, filtrar, mover instancias y operaciones masivas con informe por elemento.
9. **Eventos:** registrar webhooks, firmar mensajes, reintentar entregas y deduplicar por ID de evento.
10. **Observabilidad:** logs, auditoría, uso de recursos, diagnóstico y exportación de informes.

Para cada endpoint se debe especificar método/ruta, autenticación, permisos, esquema de entrada/salida, códigos de error, timeout, paginación, idempotencia, límites de concurrencia y pruebas. No copiar los contratos privados de GeeLark como dependencia; la matriz se basa en las funciones documentadas y los contratos locales serán propios.

### 22.3 Riesgos de seguridad y diferencias estructurales

- El README del CLI muestra operaciones privilegiadas o sensibles (root, shell, contactos, SMS, keybox y credenciales de plataformas). Geelark-IA debe ocultar o deshabilitar por defecto acciones que no sean necesarias y exigir permisos explícitos para las que se implementen.
- Los límites de tasa, códigos de error, saldos y restricciones de plan publicados para la API cloud de GeeLark describen su servicio y no se trasladan como requisitos técnicos de Geelark-IA.
- La presencia de un comando en el CLI no demuestra que pueda ejecutarse en una instancia virtual local ni que la función sea técnicamente equivalente. Cada capacidad necesita prueba del motor elegido.
- La automatización local debe ofrecer controles de parada, límites de ejecución y auditoría, y respetar los términos y controles de seguridad de las aplicaciones de terceros.

### 22.4 Criterios de aceptación del API/CLI local

1. Cada operación documentada cuenta con una prueba de éxito y, al menos, una prueba de error.
2. Las operaciones de escritura aceptan un identificador idempotente cuando proceda y no duplican instancias/tareas al reintentar.
3. Las operaciones masivas devuelven resultados separados por elemento.
4. Los permisos impiden que un usuario no autorizado ejecute shell/ADB, lea secretos o elimine instancias.
5. Los logs omiten contraseñas, tokens, cookies, datos personales y cuerpos sensibles.
6. La API local funciona sin Internet para las operaciones de administración local, salvo funciones claramente marcadas como externas.
7. Ningún endpoint requiere token, saldo, plan o API comercial de GeeLark.


## 23. Notas de versión y restricciones adicionales verificadas

### 23.1 GeeLark v4.5.0 — perfiles y automatización

La nota oficial v4.5.0, editada el 27 de agosto de 2026, documenta:
- Acceso de mantenimiento remoto por parte del equipo de soporte GeeLark, filtro de perfiles con dicho acceso y ampliación del número de perfiles con mantenimiento simultáneo.
- En creación de perfil con proxy personalizado, campo Change IP URL, con opción Auto Refresh y frecuencia configurable.
- En automatización de cloud phones: nombres de activos en los informes de ejecución, inspector de layout para flujos canvas, opción “Is checked” en el paso Get Element Data y límites de tamaño del flujo al guardar.
- Funciones adicionales de plantillas concretas de TikTok, que deben considerarse específicas de esa plantilla, no bloques universales.

Fuente: https://help.geelark.com/v4-5-0-3c90be7d9e4180a2b575c7112e7b34d0

**Adaptación local y límites:**
- El mantenimiento remoto de GeeLark no se replica como acceso de un tercero; el diagnóstico local debe ser controlado por el propietario y quedar registrado.
- Auto Refresh solo se puede soportar cuando el proxy proporcionado por el usuario tenga una URL de cambio de IP válida. La aplicación no debe inventar ni llamar una URL sin consentimiento.
- La frecuencia de refresco debe tener límites, validación de URL, timeout y registro de resultado; no se debe asumir que cambiar IP cambia todas las señales de red.
- El editor RPA debe mostrar errores de tamaño/límites de flujo antes de guardar y dar ubicación del problema.
- Los informes deben incluir el nombre/ID de los activos usados y la versión del flujo.
- El inspector de UI y la opción de estado marcado requieren pruebas por versión Android y motor; no se declara equivalencia hasta comprobar selectores y estados.

### 23.2 Plantillas y límites de flujo

La nota de versión v3.9.8 menciona importación/exportación de plantillas de automatización mediante GeeLark Automation Language, operación Get element data y Page operations / Clear the folder; también describe entrada masiva de textos diferentes para Synchronizer.

Fuente: https://help.geelark.com/v3-9-8-2630be7d9e4180858643d02184fb694c

El catálogo registra estos elementos como evidencia histórica de existencia, no como contrato actual completo. Antes de implementar importación/exportación se debe conocer el formato exacto y sus reglas de versión; el formato local será propio y documentado, sin afirmar compatibilidad binaria con GeeLark Automation Language.

### 23.3 Límites de las funciones de IA y costes

La guía oficial AI Generation Function consultada indica que la generación de imágenes/vídeos y edición de vídeo están disponibles bajo suscripción Pro y presenta cargos por uso (por ejemplo, generación de imagen y vídeo).

Fuente: https://help.geelark.com/AI-Generation-Function-2f90be7d9e418031a825ea76ce8528e2

Esta función comercial no puede ser dependencia obligatoria de Geelark-IA. La alternativa candidata será una capacidad local opcional solo si el hardware y la licencia del modelo lo permiten; de lo contrario, la función se marcará como no equivalente bajo el objetivo de coste obligatorio cero. No se prometerá generación de vídeo local sin pruebas de rendimiento y calidad.

## 24. Cambios y decisiones derivados

- Se añade a la auditoría el requisito de un inspector de UI, Get Element Data con condición de marcado, límites de tamaño de flujo y nombres de activos en informes.
- Se añade a perfiles la configuración opcional de URL de cambio de IP y refresco automático, únicamente cuando el usuario disponga de un proxy compatible.
- El acceso de mantenimiento remoto de GeeLark se marca como función cloud propietaria no equivalente; el diagnóstico local será explícito y controlado por el propietario.
- Las funciones AIGC con cargo por uso se marcan como incompatibles con una dependencia obligatoria de coste cero.


## 25. Verificación directa: Library, miembros, analítica, ADB y cámara

### 25.1 Library y activos multimedia

La guía Library indica que GeeLark limita la función a la suscripción Pro, permite almacenar fotos y vídeos, cargar manualmente, importar desde Google Drive u otros servicios compatibles y usar los activos en automatización. La guía indica un máximo de 100 GB y eliminación a los 30 días; esos límites describen el servicio cloud de GeeLark y no se copiarán a la biblioteca local.

Fuente: https://help.geelark.com/Library-1c20be7d9e41800a8535ea943b930bd4?pvs=21

**Adaptación local:** activos persistentes por defecto, etiquetas, búsqueda, metadatos, hash, detección de duplicados, vista previa, backup/exportación y límite configurable por espacio de disco. Las integraciones con Google Drive u otros repositorios serán opcionales y no críticas; la biblioteca debe funcionar con archivos locales y sin Internet.

### 25.2 Miembros y permisos

La guía Members describe grupos de usuarios con derechos funcionales compartidos; alta de miembros con nombre, correo, contraseña y rol (administrador, gestor o miembro), autorización por grupos y límite opcional de perfiles. También describe modificación y eliminación de información y restablecimiento de contraseña.

Fuente: https://help.geelark.com/Members-59810b22074f4dc08f58cc2e4262a9c8?pvs=21

**Adaptación local:** si se implementa colaboración multiusuario, se exigirán contraseñas almacenadas con un algoritmo de hash resistente, permisos mínimos, aislamiento por grupo, revocación de sesiones, auditoría y protección contra escalada de privilegios. El sistema de un solo usuario local no debe obligar a crear cuentas cloud. La función de miembros se priorizará después del núcleo y de la definición del modo local/multiusuario.

### 25.3 Analytics

La guía Analytics describe el registro de cuentas de Instagram, TikTok, YouTube y Reddit para consultar métricas como seguidores, me gusta y comentarios; indica actualización diaria a partir de las 02:00 y que se introduce el identificador exacto de la plataforma.

Fuente: https://help.geelark.com/Analytics-2df0be7d9e41807da29ee97619ecf365?pvs=21

**Adaptación local:** diferenciar métricas de ejecución interna (tareas, tiempos, errores, uso de CPU/RAM/disco) de métricas externas de redes sociales. Las métricas de plataformas externas solo se implementarán mediante interfaces legítimas y disponibles; no se asumirá acceso gratuito ni se eludirán límites de autenticación, API o términos de uso. Si una integración no puede hacerse sin pagos o credenciales, se marcará como opcional/no equivalente.

### 25.4 ADB

La guía ADB de GeeLark indica soporte para Android 11, 12, 13, 14, 15 y 16 en la versión consultada; permite habilitar ADB por perfil o en varios perfiles, iniciar el perfil y obtener datos de conexión para ejecutar comandos ADB.

Fuente: https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad

**Adaptación local:** en las instancias virtuales propias, preferir ADB local por socket/puerto restringido a loopback o red interna aislada. No publicar ADB en Internet. La API local debe exponer operaciones de alto nivel por defecto y permitir shell solo a usuarios autorizados, con timeout, auditoría y redacción de secretos. Las diferencias de ADB en Android 9/10 o versiones futuras se documentarán por motor y versión.

### 25.5 Cámara y entrada multimedia

La guía de cámara describe tres vías: usar una imagen subida desde el ordenador para escanear QR desde la galería, usar la cámara de un teléfono físico mediante mirroring y usar la cámara web del ordenador o vídeo pregrabado.

Fuente: https://help.geelark.com/How-to-use-the-camera-on-the-cloud-phone-3500be7d9e41802e8dbddb948a1b78c7?pvs=21

**Adaptación local:** evaluar por separado:
1. Importar una imagen local a la galería de la instancia (no necesita cámara real).
2. Proveer cámara web del anfitrión, solo si el motor y el sistema anfitrión lo soportan.
3. Proveer una fuente multimedia de prueba/pregrabada, claramente identificada como simulada.
4. Integrar cámara física vía mirroring solo como función opcional, con consentimiento y permisos.
No afirmar que una imagen o cámara virtual es equivalente a una cámara/sensor físico real; algunas apps pueden detectar diferencias del entorno virtual.

### 25.6 Logs

La guía pública Logs consultada solo muestra el encabezado del módulo, sin detalles de campos ni filtros en el contenido accesible. Por tanto, la especificación completa de GeeLark Logs permanece **sin evidencia suficiente** y no debe inferirse a partir del nombre.

La adaptación local prevista se mantiene como propuesta de diseño: eventos estructurados, filtros por instancia/tarea/fecha/estado, exportación, correlación y redacción de datos sensibles. Falta evidencia para afirmar equivalencia de filtros, retención o vistas concretas.

## 26. Criterios de aceptación añadidos

1. Library: cargar archivo local, etiquetar, buscar, recuperar después de reiniciar y exportar sin servicio cloud.
2. Library: alcanzar un límite de almacenamiento configurado debe generar aviso y evitar corrupción; no eliminar archivos sin política explícita.
3. Miembros: probar matriz de permisos para administrador, gestor y miembro; denegar acceso a grupo no autorizado y registrar el intento sin exponer secretos.
4. Analytics: distinguir claramente métricas locales de métricas externas y manejar datos no disponibles sin inventar valores.
5. ADB: permitir conexión a una instancia local autorizada, denegar una no autorizada y comprobar que el puerto no es accesible desde redes externas por defecto.
6. Cámara: probar imagen desde galería, webcam si está soportada y una fuente pregrabada; mostrar el modo usado y sus limitaciones.
7. Logs: no marcar equivalencia con GeeLark hasta obtener evidencia adicional sobre las pantallas y campos de la función original.

## 27. Historial

- 2026-10-09: se verificaron las guías públicas de Library, Members, Analytics, ADB y cámara; se registraron límites de evidencia, adaptaciones locales y criterios de aceptación.


## 28. Revisión de notas oficiales v4.5.1 y v4.5.2

Fuentes:
- https://help.geelark.com/v4-5-1-3d60be7d9e4180c5a0bef756578b881e?pvs=21
- https://help.geelark.com/v4-5-2-3e40be7d9e418006a508d2f22696e0fb?pvs=21

### 28.1 Synchronizer — carga masiva de archivos (v4.5.1)

La nota v4.5.1 documenta carga masiva de archivos en Synchronizer para cloud phones y un listado/historial de cargas accesible después de la operación.

**Requisito local:** permitir seleccionar explícitamente instancias destino, archivos y destino de almacenamiento; mostrar progreso y resultado por archivo/instancia; conservar un historial local consultable; permitir cancelación cuando el motor lo soporte; reanudar o repetir de forma idempotente sin crear duplicados inesperados.

### 28.2 Inspector de interfaz / árbol UI (v4.5.1)

La nota v4.5.1 separa el inspector de layout en un diálogo e indica acciones para analizar el alcance del layout, abrir un archivo de árbol UI y guardar el árbol UI.

**Requisito local:** inspector de solo lectura para depuración y construcción de selectores, con exportación a un formato documentado. No incluir valores de campos sensibles por defecto. Los selectores deben volver a validarse después de cambios de versión o layout; no confiar solo en coordenadas absolutas.

### 28.3 Library, etiquetas y tareas (v4.5.2)

La nota v4.5.2 documenta:
- Editar etiquetas desde el menú de acciones de Library.
- Seleccionar etiquetas al subir archivos locales.
- Alternar vista de tarjetas/lista.
- Iterar activos por etiqueta en una plantilla concreta de publicación de vídeo.
- Consultar desde Logs la opción View Task para ver parámetros configurados después de publicar una tarea.

**Requisito local:** etiquetas editables, selector de etiquetas en carga, vistas de lista/tarjetas, iteración de recursos en flujos genéricos y visualización de una instantánea inmutable de los parámetros publicados. Las funciones específicas de plantillas comerciales de plataformas no se consideran bloques universales ni se replican automáticamente.

### 28.4 AIGC y presupuestos (v4.5.1/v4.5.2)

Las notas describen integración de modelos y seguimiento de uso AIGC; v4.5.1 incluye presupuesto AIGC por miembro. Estas funciones dependen de proveedores/modelos y de las condiciones comerciales de GeeLark.

**Requisito local:** el sistema de permisos puede tener cuotas de recursos locales, pero no se copiará un modelo de créditos de generación pagada. No se usará IA externa de pago como dependencia. El uso de modelos locales debe registrar modelo, licencia, hardware y consumo aproximado, sin telemetría externa obligatoria.

### 28.5 Seguridad de contraseñas en perfiles de navegador

La nota v4.5.1 menciona permisos para contraseñas, claves 2FA y gestor de contraseñas de perfiles de navegador. Esta función es de navegador y queda fuera del alcance Android principal; no obstante, refuerza una regla de diseño transversal: secretos deben poder ocultarse por permisos y nunca aparecer en logs/exportaciones por defecto.

## 29. Criterios de aceptación adicionales

1. Carga masiva: resultado por archivo y destino, historial persistente y comportamiento definido ante desconexión.
2. Inspector UI: abrir/guardar árbol UI, buscar un elemento y exportar una muestra sin valores sensibles.
3. Etiquetas: crear/renombrar/eliminar etiqueta, asignar a múltiples activos, filtrar y seleccionar activos por etiqueta en un flujo.
4. Parámetros de tarea: la vista posterior a publicar coincide con la instantánea usada para esa ejecución, incluso si el flujo se edita después.
5. Recursos por etiqueta: el motor define comportamiento ante etiqueta vacía, archivo eliminado y archivo incompatible.
6. Presupuestos: límites de tareas/recursos locales no se confunden con cargos comerciales; sin llamadas de IA externas obligatorias.


## 30. Notas históricas de versiones v3.6.0, v3.8.0, v3.9.0 y v3.9.1

Fuentes oficiales:
- https://help.geelark.com/v3-6-0-3080be7d9e4181748064e63be60784dd?pvs=21
- https://help.geelark.com/v3-8-0-3080be7d9e41816a8b2bc0bbc2964ed1?pvs=21
- https://help.geelark.com/v3-9-0-3080be7d9e4181099973d62272a9c309?pvs=21
- https://help.geelark.com/v3-9-1-3080be7d9e4181788653c8f6790f8e1f?pvs=21

### 30.1 Operaciones de perfiles y red

Las notas históricas v3.6.0 describen etiquetas, operaciones por lotes de hasta 100 dispositivos en una acción concreta y con los dispositivos apagados, configuración de proxy en tiempo real y acceso ROOT en dispositivos encendidos. Estas cantidades y restricciones pertenecen a esa versión/plan y no se asumen como límites actuales.

La nota v3.9.0 documenta clonado de perfiles y configuración personalizada de red celular/Wi-Fi solo para Android 12/13/15 en esa versión.

**Adaptación local:** límites de operaciones masivas configurables según recursos y resultados por instancia; edición de red solo si el motor admite el campo; root no se activa por defecto; clonar no debe duplicar accidentalmente secretos, cuentas ni identidad de origen.

### 30.2 Operaciones de aplicaciones

La nota v3.8.0 describe operaciones masivas por grupo para abrir, cerrar, reiniciar y desinstalar aplicaciones, además de actualización de versiones de aplicaciones del equipo.

**Adaptación local:** cola de tareas con progreso por instancia y por paquete, cancelación cuando sea segura, errores parciales y recuperación ante reinicio. No replicar la tienda propietaria como dependencia.

### 30.3 API, medios y tareas

La nota v3.8.0 documenta autenticación Bearer y endpoints OpenAPI para administrar medios con etiquetas (añadir, eliminar, consultar, configurar etiquetas) y consultar informes de tareas. La nota v3.9.1 documenta creación masiva de perfiles por OpenAPI.

**Adaptación local:** autenticar el API propio mediante credenciales locales revocables; especificar recursos de medios, etiquetas e informes; admitir creación masiva idempotente con validación por fila. No copiar tokens, URL privadas ni dependencias del servicio de GeeLark.

### 30.4 RPA y Synchronizer

La nota v3.9.1 registra opción de entrada por coordenadas para automatización, soporte de portadas en una plantilla específica, selección de plataforma al compartir plantillas y modo de pantalla completa en Synchronizer. Estas funciones son evidencia histórica; no garantizan el comportamiento en la versión actual.

**Adaptación local:** soportar selectores semánticos cuando existan y coordenadas como alternativa frágil documentada; los flujos deben declarar resolución/orientación esperadas y fallar con diagnóstico cuando cambien. El modo de pantalla completa es una función de presentación, separada del motor de sincronización.

### 30.5 Retención de perfiles eliminados

La nota v3.7.0 describe una papelera en la que perfiles eliminados se conservaban durante siete días en esa versión.

**Adaptación local:** ofrecer papelera recuperable y periodo de retención configurable, con borrado definitivo explícito y pruebas de restauración. No copiar siete días como límite fijo sin validar el comportamiento actual de referencia.

### 30.6 Límites de evidencia histórica

Los números de perfiles por lote, tareas por lote, retención, restricciones de plan, versiones Android, características de root y opciones de red pueden haber cambiado. Cada dato histórico debe incluir versión y fuente y no debe convertirse en una promesa actual. El comportamiento final local se basará en recursos anfitriones, pruebas y decisiones explícitas del proyecto.


## 31. Conexión de dispositivo físico local: evidencia adicional para importación

La guía oficial «How to connect a local device» describe activar opciones de desarrollador y depuración USB, autorizar el equipo anfitrión en el teléfono, conectar por USB, abrir el área Local Device y reconocer el modelo. También describe que, tras conectar primero por USB, se puede conectar mediante Wi-Fi cuando el ordenador y el dispositivo estén en la misma red.

Fuente: https://help.geelark.com/connect-real-device

**Distinción importante:** esta guía documenta conexión y operación de un dispositivo físico local en GeeLark; no demuestra que todos sus parámetros de identidad puedan leerse o importarse. La importación de Geelark-IA seguirá limitada a los campos disponibles mediante interfaces autorizadas y comprobados por pruebas.

**Requisitos derivados:**
- Detectar los estados ADB habituales: dispositivo autorizado, no autorizado, offline, desconectado y múltiples dispositivos conectados.
- Mostrar instrucciones de autorización sin intentar saltarse el diálogo del sistema.
- Identificar el dispositivo de forma segura y enmascarar el serial en la interfaz/logs salvo necesidad técnica explícita.
- Permitir seleccionar el dispositivo cuando hay varios conectados; nunca escoger automáticamente uno para una operación de escritura.
- Admitir conexión USB como camino inicial; valorar conexión Wi-Fi solo tras emparejamiento autorizado, con una explicación del riesgo de red.
- La desconexión del cable no debe provocar pérdida silenciosa de una importación ni modificar el origen.
- Mantener por separado la función de control de un teléfono físico, la inspección de campos y la aplicación de configuración a una instancia virtual.

### Pruebas adicionales de compatibilidad ADB

1. Un solo dispositivo autorizado.
2. Un dispositivo que no ha aceptado la clave RSA.
3. Dos o más dispositivos conectados.
4. Dispositivo desconectado durante lectura.
5. ADB reiniciado o dispositivo marcado como offline.
6. Depuración USB desactivada y permiso revocado.
7. Conexión por Wi-Fi tras emparejamiento autorizado, si se decide implementar.
8. Verificación de que la inspección no ejecuta comandos de escritura en el origen.

No se afirma compatibilidad universal a partir de esta guía: cada fabricante/versión se validará progresivamente.


## 32. Revalidación de fuentes oficiales — 2026-10-12

Esta sección registra una nueva lectura de páginas públicas oficiales. No significa que GeeLark-IA ya implemente estas funciones; sirve para precisar la referencia y evitar copiar restricciones comerciales al diseño local.

### 32.1 Creación y gestión de perfiles

La guía oficial de creación de perfiles documenta tres modalidades: creación individual, rápida y por lotes. La misma página señala que Quick Create y Batch Create son exclusivas de Pro. En creación individual se seleccionan grupo, sistema operativo, proxy y método de facturación; la guía describe proxies estáticos y rotativos, selección de proxies guardados, asociación con perfiles, emparejamiento aleatorio con preferencia por proxies menos usados y comprobación de conexión/ubicación. No se permiten proxies expirados. El uso del cloud phone se factura por minuto salvo que el usuario tenga un paquete de tiempo o alquiler mensual.

La guía de gestión añade filtros por grupo/categoría, edición solo cuando el perfil está cerrado, transferencia irreversible a otro usuario y administración de grupos (crear, renombrar, eliminar, fusionar y mover perfiles).

**Adaptación local:** mantener creación individual como ruta base y añadir creación por lotes local solo con validación por fila, vista previa, límites basados en recursos del anfitrión, idempotencia y recuperación de fallos parciales. No replicar facturación cloud, suscripciones ni restricciones Pro como dependencias del producto local. La transferencia irreversible se sustituye por operaciones locales explícitas con confirmación, auditoría y posibilidad de recuperación cuando sea viable.

Fuentes:
- https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8
- https://help.geelark.com/Profile-management-c91b6291bb954a69a5d231781a03d0e1

### 32.2 Synchronizer

La guía consultada indica que Synchronizer es una función de suscripción Pro. Para teléfonos cloud, las acciones realizadas en un teléfono principal se replican a los otros teléfonos seleccionados; la guía pide seleccionar teléfonos apagados y recomienda usar el mismo tipo/modelo para reducir diferencias de interfaz. La lista publicada enumera Android 9 a Android 15. La sincronización de perfiles de navegador se documenta como disponible solo en Windows, con versión macOS en desarrollo.

**Adaptación local:** el alcance de Geelark-IA es Android local, por lo que la sincronización de perfiles de navegador queda fuera de alcance. Antes de replicar eventos se debe comprobar que todas las instancias están en un estado compatible, registrar por destino el resultado y error, permitir pausar/detener y manejar resoluciones o layouts diferentes. No asumir que todas las acciones de interfaz se pueden reproducir de forma determinista.

Fuente: https://help.geelark.com/Synchronizer-82c1c9a8f62d489ca81b1f753d2a7bfa

### 32.3 Library

La guía oficial indica que Library solo está disponible en Pro, centraliza fotos y vídeos para teléfonos cloud y flujos de automatización, permite carga manual e importación desde Google Drive u otros servicios compatibles, y describe un límite de 100 GB con eliminación del contenido 30 días después de la carga. Ese límite es una política del servicio cloud de GeeLark, no un requisito para la biblioteca local.

**Adaptación local:** priorizar archivos locales persistentes, etiquetas, búsqueda, hashes, control de duplicados, límites configurables por disco, backup/restauración y eliminación solo con política explícita. Las integraciones cloud serán opcionales y nunca obligatorias; no se incorporará Google Drive como dependencia crítica.

Fuente: https://help.geelark.com/Library-1c20be7d9e41800a8535ea943b930bd4

### 32.4 API y ADB

La página pública de API enumera operaciones de gestión del ciclo de vida de cloud phones, automatización, apps y contenido, archivos, Library, ADB y webhooks. La guía ADB consultada enumera compatibilidad con Android 11–16 y describe habilitar ADB en el perfil, iniciar el teléfono cloud y usar dirección/puerto y código de conexión. Esta lista no debe confundirse con la compatibilidad de Synchronizer, que publica Android 9–15.

**Adaptación local:** diseñar una API propia versionada con autenticación local revocable, permisos mínimos, errores tipados, idempotencia y eventos durables. En local, ADB se mantendrá en loopback o red interna aislada; no se expondrá ADB público ni se convertirá shell en una ruta remota administrativa por defecto. La compatibilidad se validará por motor e imagen Android.

Fuentes:
- https://www.geelark.com/features/api/
- https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad

**Límite de evidencia de API:** la página comercial enlaza el portal oficial https://open.geelark.com/api, pero el contenido de ese portal no fue legible en la consulta documental actual. Por tanto, aquí solo se registran categorías anunciadas (cloud phones, automatización, apps/archivos, ADB, Library y webhooks); no se inventan rutas, esquemas JSON, firmas, errores ni requisitos de autenticación. El inventario de endpoints sigue pendiente de acceso a documentación textual o exportación pública verificable.

### 32.5 Conclusión de esta revalidación

Las páginas consultadas confirman que GeeLark combina gestión de perfiles, proxies, automatización, sincronización, recursos multimedia y APIs sobre una infraestructura cloud con funciones sujetas a plan y facturación. La paridad local debe replicar el objetivo funcional donde sea viable, no los cargos, la retención temporal de Library ni las restricciones Pro. Las diferencias de versiones Android entre funciones se mantienen como una incertidumbre que requiere pruebas por motor.


### 32.6 RPA: selectores, variables y control de flujo

La página pública de RPA describe un editor visual sin código para combinar acciones, lógica, bucles, variables, manejo de excepciones y ejecución/monitorización de tareas. La guía práctica de RPA detalla opciones concretas que conviene modelar en el catálogo local:

- **Acciones observadas:** abrir aplicaciones, tocar/clicar elementos, pulsación prolongada, deslizar/desplazar, introducir texto, esperar, subir archivos y navegar por pantallas.
- **Localización de elementos:** texto visible, atributos del elemento y coordenadas. La guía de principiantes menciona atributos como `fullId`, `desc` y `className`.
- **Configuración de selector:** coincidencia exacta (`Equals`) o parcial (`Contains`), orden fijo o selección aleatoria dentro de un intervalo, tiempo máximo de espera en milisegundos y opción de buscar elementos no visibles.
- **Resultado y diagnóstico:** la guía describe guardar el resultado de una acción en una variable booleana y añadir notas para explicar el propósito del paso.
- **Variables documentadas:** texto/cadena, número, booleano y objeto (por ejemplo, una referencia a un elemento UI). La guía incluye extraer texto de un elemento, guardarlo y reutilizarlo en acciones posteriores.
- **Control de flujo:** condiciones, bucles por cantidad/elementos/datos y reglas de excepción como omitir un paso o detener el flujo.
- **Operación:** asignar el flujo a perfiles seleccionados, ejecutar o programar tareas y consultar estado/logs.

**Adaptación local y seguridad:** cada bloque debe tener esquema versionado, tipos de entrada/salida, timeout, resultado booleano/estructurado, política de fallo, permisos, idempotencia y registro redactado. El motor local no ejecutará Python, JavaScript ni shell arbitrario como parte normal de un flujo. Los selectores por coordenadas son frágiles; deben marcarse como menos robustos que los selectores semánticos y validarse por resolución, idioma y versión Android. Las acciones aleatorias se modelarán como opción explícita y reproducible (semilla/registro), no como evasión de controles de plataformas.

Fuentes:
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- https://www.geelark.com/blog/geelark-rpa-guide-5/
- https://www.geelark.com/es/blog-es/automatizacion-de-apps-android-y-navegador-geelark-rpa/


### 32.6 RPA: selectores, variables y control de flujo

La página pública de RPA describe un editor visual sin código para combinar acciones, lógica, bucles, variables, manejo de excepciones y ejecución/monitorización de tareas. La guía práctica de RPA detalla opciones concretas que conviene modelar en el catálogo local:

- **Acciones observadas:** abrir aplicaciones, tocar/clicar elementos, pulsación prolongada, deslizar/desplazar, introducir texto, esperar, subir archivos y navegar por pantallas.
- **Localización de elementos:** texto visible, atributos del elemento y coordenadas. La guía de principiantes menciona atributos como `fullId`, `desc` y `className`.
- **Configuración de selector:** coincidencia exacta (`Equals`) o parcial (`Contains`), orden fijo o selección aleatoria dentro de un intervalo, tiempo máximo de espera en milisegundos y opción de buscar elementos no visibles.
- **Resultado y diagnóstico:** la guía describe guardar el resultado de una acción en una variable booleana y añadir notas para explicar el propósito del paso.
- **Variables documentadas:** texto/cadena, número, booleano y objeto (por ejemplo, una referencia a un elemento UI). La guía incluye extraer texto de un elemento, guardarlo y reutilizarlo en acciones posteriores.
- **Control de flujo:** condiciones, bucles por cantidad/elementos/datos y reglas de excepción como omitir un paso o detener el flujo.
- **Operación:** asignar el flujo a perfiles seleccionados, ejecutar o programar tareas y consultar estado/logs.

**Adaptación local y seguridad:** cada bloque debe tener esquema versionado, tipos de entrada/salida, timeout, resultado booleano/estructurado, política de fallo, permisos, idempotencia y registro redactado. El motor local no ejecutará Python, JavaScript ni shell arbitrario como parte normal de un flujo. Los selectores por coordenadas son frágiles; deben marcarse como menos robustos que los selectores semánticos y validarse por resolución, idioma y versión Android. La selección aleatoria será explícita, acotada y auditable.

Fuentes:
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- https://www.geelark.com/blog/geelark-rpa-guide-5/
- https://www.geelark.com/es/blog-es/automatizacion-de-apps-android-y-navegador-geelark-rpa/


### 32.7 Bloques concretos documentados en las guías RPA (2026-10-12)

Las guías de principiantes permiten concretar el inventario inicial de bloques. No son una lista exhaustiva del editor actual; las opciones deben verificarse cuando exista acceso práctico a una versión de referencia.

| Bloque o grupo | Parámetros/semántica observados | Requisitos para la adaptación local |
|---|---|---|
| Open app | Nombre de paquete; URI opcional para abrir una pantalla/recurso concreto | Validar paquete instalado, URI permitido y resultado; no ejecutar comandos arbitrarios |
| Waiting time | Valor fijo o intervalo aleatorio | Límites mínimos/máximos, unidades explícitas, semilla registrada cuando sea aleatorio |
| Scroll Page | Distancia en píxeles, tiempo de desplazamiento, punto inicial X/Y y dirección arriba/abajo/izquierda/derecha | Validar límites de coordenadas y resolución; timeout y cancelación |
| Page back | Regresar a la pantalla anterior; puede requerir más de una acción para volver al inicio | Resultado observable, límite de repetición y no asumir que una pulsación siempre vuelve al mismo destino |
| Upload File | Uno o varios archivos; selección secuencial por flujo, por entorno o aleatoria | Solo rutas permitidas, vista previa, validación de tamaño/hash y resultado por archivo |
| IF Condition | Existe/no existe; comparaciones menor/igual/distinto/mayor; incluye/no incluye; condición porcentual aleatoria | Tipos compatibles, reglas explícitas y registro de la rama seleccionada |
| For Loop Times | Repetir acciones un número definido de veces | Máximo de iteraciones, cancelación y checkpoint seguro |
| For Loop Elements | Iterar sobre elementos visibles que cumplen el selector; variables para elemento actual e índice (base 1) | Congelar/validar lista de elementos, limitar cantidad y detectar cambios de UI |
| For Loop Data | La guía enumera el bloque, pero indica que la explicación detallada sigue en preparación | Mantener el contrato como pendiente; no inventar campos hasta obtener evidencia adicional |
| Exit Loop / End Task | Salir del bucle antes de terminar o detener la tarea inmediatamente | Distinguir salida del bucle de cancelación global; registrar causa y estado terminal |
| Task Settings / variables | Variables String, Batch Text, Boolean, Number y File; valores configurables antes de publicar. Las acciones de UI también pueden almacenar referencias de elementos como objetos | Tipos versionados, validación de valores por tarea y separación entre parámetros del usuario y variables temporales |
| Exception handling | Skip (omitir paso fallido) o Interrupt (detener tarea) | Política por bloque y por flujo, error tipado y estado final visible |
| Task scheduling/logs | Nombre y notas del plan, perfiles destino, horarios por perfil o comunes; logs con opción de cancelar ejecución o modificar hora de publicación | Cola persistente, zona horaria explícita, idempotencia, cancelación cooperativa e historial auditable |

Fuentes oficiales:
- Guía 2 — plantillas, asignación a perfiles, planificación y logs: https://www.geelark.com/blog/geelark-rpa-guide-2/
- Guía 3 — Open app, Waiting time, Scroll Page, Page back y depuración: https://www.geelark.com/blog/geelark-rpa-guide-3/
- Guía 4 — selectores, interacción y parámetros: https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- Guía 5 — variables y extracción de texto: https://www.geelark.com/blog/geelark-rpa-guide-5/
- Guía 6 — carga de archivos, condiciones, bucles, salida y excepciones: https://www.geelark.com/blog/geelark-rpa-guide-6/

**Pendiente:** el inventario no se considera exhaustivo; la propia guía deja For Loop Data para una explicación posterior y el marketing menciona más módulos que los descritos aquí. No se implementará un bloque solo por aparecer en una lista comercial sin especificar su contrato y pruebas.


### 32.8 Acciones UI y campos de selector (guía 4)

La guía en español confirma acciones adicionales y parámetros comunes:

- **Haz clic en elemento / pulsación prolongada en elemento:** selector por `fullId`, texto, `desc` o `className`; Equals/Contains; posición fija o rango; timeout en ms; incluir o excluir elementos no visibles; variable booleana de resultado; notas.
- **Clic en coordenadas / pulsación prolongada en coordenadas:** X/Y de pantalla. La guía explica calcular el centro de los límites del elemento y advierte que las mismas coordenadas pueden apuntar a otro control al cambiar la resolución o la versión Android.
- **Ingresar contenido:** selecciona el campo mediante atributos, define coincidencia/orden/timeout y configura el contenido. La guía también muestra variables como fuente de texto.
- **Operación con teclado:** teclas como Enter o Delete.
- **Esperar a que aparezca un elemento:** selector por atributos/texto, condición, orden, timeout, opción de elementos invisibles y resultado booleano.
- **Inspección de UI:** el flujo de referencia usa una herramienta de análisis de jerarquía/accesibilidad para inspeccionar clase, descripción, ID completo, texto y límites del elemento. No todos los elementos tienen `desc` o un `fullId` único; los controles pueden estar anidados.

**Reglas para Geelark-IA:** dar prioridad a selectores semánticos y combinaciones de atributos; advertir si el selector coincide con varios elementos; hacer explícita la selección por índice; registrar la resolución y versión Android cuando se usan coordenadas; y devolver `success=false` más un error estable si el elemento no aparece dentro del timeout. Nunca asumir que un ID, texto o coordenada es universal entre apps/versiones.

Fuente: https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/


### 32.9 Inventario API a partir del CLI oficial (2026-10-12)

El repositorio público del CLI oficial se presenta con licencia MIT y afirma cobertura de las interfaces API de GeeLark. Esto describe la licencia del cliente, **no** una API cloud gratuita: el README requiere un token obtenido en el cliente GeeLark y enumera respuestas de “solo usuarios de pago”, saldo insuficiente y límites de cuenta. Geelark-IA no dependerá de ese servicio ni del CLI para funcionar.

El README del CLI organiza capacidades en estas áreas:

- **Cloud phone:** listar, crear, iniciar/detener, eliminar, actualizar, clonar, consultar estado, captura, GPS, reset, root, SMS, transferir y contactos.
- **Automatización:** consultar historial/estado, cancelar/reiniciar tareas, crear tareas personalizadas y lanzar automatizaciones de plataforma.
- **Aplicaciones/equipo:** consultar catálogo, instalar/desinstalar/iniciar/detener, cargar APK, consultar estado de carga y operaciones por lote.
- **Archivos/Library:** carga temporal, carga al teléfono, estado de carga, materiales y etiquetas.
- **ADB/shell:** obtener datos de conexión, habilitar/deshabilitar ADB y ejecutar comandos remotos.
- **Webhooks/OEM/analítica:** gestionar URL de callback, configuración de marca y cuentas/datos analíticos.
- **Navegador:** listar/crear/editar/iniciar/detener/eliminar y automatización.
- **Proxy/grupos/tags:** listar y crear/actualizar/eliminar; proxy también permite comprobación/detección.
- **Facturación:** consultar saldo, transacciones, planes, renovaciones y paquetes de tiempo.

El README del CLI publica límites de 200 solicitudes por minuto y 24.000 por hora, y 10 solicitudes por minuto para balance; indica una restricción de dos horas tras exceder límites. Son límites publicados por el cliente oficial, no garantías de SLA ni límites transferibles a Geelark-IA. También enumera códigos como parámetros inválidos, rate limit, solo pago, saldo insuficiente, teléfono no encontrado/no iniciado, tarea activa y límite de perfiles.

**Límite de evidencia:** el inventario del CLI no reemplaza los contratos de cada endpoint. El portal de documentación API no expuso contenido textual legible en esta revisión, por lo que no se infieren payloads, autenticación completa, callbacks ni todos los errores.

Fuente: https://github.com/GeeLark/geelark-cli (README y licencia del repositorio oficial).
