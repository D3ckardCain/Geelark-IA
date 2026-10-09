# Catálogo funcional detallado de GeeLark — avance de auditoría

**Fecha de actualización:** 2026-10-09  
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
