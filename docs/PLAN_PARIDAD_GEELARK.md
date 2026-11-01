# Guía maestra de GeeLark para su reproducción local

**Revisión:** 1.0 — 2026-11-01. **Tipo:** investigación y planificación, sin implementación ni despliegue en esta revisión.

Objetivo: reproducir fielmente funciones y recorridos Android de GeeLark mediante una implementación independiente en equipos propios. No basta con copiar pestañas: cada capacidad requiere campos, persistencia, estados, errores, permisos, manual y prueba comparativa. Las diferencias se registran y resuelven; no se llaman equivalencia exacta sin demostrarlo.

Esta guía sustituye el plan preliminar de octubre como orden de construcción, conservando los módulos M00–M17. El [catálogo](CATALOGO_FUNCIONAL_GEELARK.md) conserva investigación histórica y la [matriz](MATRIZ_PARIDAD_GEELARK.md) conserva IDs anteriores. Las fuentes Sxx/Axx/U01 se encuentran en [FUENTES_GUIA_GEELARK.md](FUENTES_GUIA_GEELARK.md).

## 1. Reglas permanentes

- PC-MASTER es el panel web sobre Windows. El lanzador prepara y arranca, no es el centro operativo.
- Todos los PC-WORKER: Debian 13 en consola, sin escritorio gráfico; arranque `multi-user.target`; SSH/Docker/redroid como servicios sin login. VirtualBox es el laboratorio actual, no requisito para los workers físicos.
- Motor elegido: redroid. No volver a alternativas descartadas.
- Android, archivos, ejecución y automatización se alojan en hardware propio. Las redes sociales sí necesitan Internet; local no significa que una plataforma externa funcione offline.
- Software/servicios obligatorios: objetivo $0, sin tarjeta, pruebas temporales ni APIs de pago. No promete hardware, energía, Internet, proxies comerciales o comisiones de blockchain gratuitos.
- Alcance: Android, sin iOS ni motor de navegador de escritorio independiente. El navegador dentro de Android sí forma parte del entorno. La oferta de navegador de GeeLark queda inventariada como diferencia explícita.
- Objetivo inicial hasta 50 instancias, ampliable por medición; no implica 50 simultáneas demostradas ni 50 por worker.
- Código, marca, formatos y activos propios. Reproducir resultados y organización con el estilo oscuro acordado.
- Diagnóstico técnico separado, opcional por sesión. Operación diaria sin terminales, trazas, secretos ni comandos permanentes.
- Un incremento activo a la vez, probado, documentado y aceptado antes del siguiente.
- GitHub conserva requisitos y evidencias. El plan no autoriza fusionar PR dependientes, saltar #77 ni exponer el panel a LAN.

## 2. Estado real: reutilizar lo aceptado

| Capacidad existente | Evidencia | Lo que todavía no demuestra |
|---|---|---|
| Panel Windows, login local, HTTPS loopback, rol PostgreSQL lector | Instalación real del operador; ramas #146/#147 | Aceptación completa #77 o multiusuario |
| Abrir/cerrar conexión/recuperar Android | Un JSON, túnel SSH/ADB, scrcpy; pruebas reales | Inventario multiinstancia, creación desde panel o control completo de energía |
| Lanzador sin CMD permanente ni parpadeos | Corrección f90c8c21 y confirmación del operador en #147 | Recorrido completo de instalación limpia |
| Debian consola y recuperación tras reinicio | multi-user.target; display-manager inactivo; Docker/SSH activos; Android abrió sin login | Adopción de flota o reinicio del host Windows/VirtualBox |
| Asistente inicial | Código y pruebas en #147 | Prerrequisitos instalados automáticamente o aceptación de Windows limpio |
| Contratos/persistencia/colas | Paquetes y PR de infraestructura | Todas sus operaciones disponibles en UI y ejecutadas por agente |
| Catálogo de referencia | Auditoría histórica + revisión pública actual | Inspección autenticada de cada diálogo de GeeLark |

Las ramas de revisión no se presentan como fusionadas. No rehacer lo ya probado. La conexión única es una base operativa que debe convertirse en un perfil persistente, no desecharse.

## 3. Mapa de pantallas

U01 muestra menú español y Perfiles seleccionado. Se leen filtro de grupo, búsqueda por nombre y acciones Iniciar, Cerrar, Mover, Transferir, Exportar, Comprobar Proxy y Eliminar. No se asigna significado a los iconos sin etiqueta ni se inventan columnas de la tabla vacía.

| Entrada de referencia | Equivalente local | Módulo / diferencia |
|---|---|---|
| Principal | Resumen de perfiles, workers y tareas | M02/M11; contenido exacto original pendiente |
| Perfiles | Inventario principal de Android | M03/M04; worker y capacidad propios |
| Proxies | Inventario, prueba y asignación | M06; sin venta obligatoria de proxies |
| Biblioteca | Activos multimedia propios | M05; retención local, no caducidad cloud impuesta |
| AIGC | Generación/edición local | M13; modalidades condicionadas al hardware/licencia |
| GeeLark AI | Asistente propio de ayuda y flujos | M13; distinto de AIGC |
| Analíticas | Métricas sociales disponibles | M11; separar de consumo de infraestructura |
| Aplicaciones | Catálogo propio y paquetes por perfil/grupo | M05; no tienda comercial copiada |
| Automatización | Editor, plantillas, tareas y calendario | M07/M09/M14 |
| Sincronizador | Maestro y destinos de control simultáneo | M08; no es RPA programado |
| GeeHub | API, CLI, MCP y eventos propios | M10; sin token/API de GeeLark |
| Recursos | Manuales, herramientas e integraciones | M14; distinto de Biblioteca |
| Referidos | Área comercial inventariada | M14; no comisiones ficticias en app personal |
| Facturación | Capacidad, uso y cuotas | M11; adaptación explícita sin cobros por minuto |
| Miembros | Operadores, grupos y derechos | M12; posterior al núcleo de un operador |
| Registros | Auditoría operativa y ejecución | M11; independiente del diagnóstico temporal |
| Configuración | Imágenes, Android, idioma y mantenimiento | M02/M16; diálogos originales por completar |
| Workers | Infraestructura de la adaptación local | M01/M02/M16; no pantalla original observada |

## 4. Requisitos por módulo

IDs `Mxx.nn` son unidades comprobables. **V**: documentado oficialmente; **U**: visible en captura; **P**: propuesta/requisito de adaptación local; **H**: referencia histórica. Ninguna letra significa implementado o compatible con redroid. Las pruebas son criterios locales, no afirmaciones sobre pruebas realizadas.

Cada ficha de implementación debe contener fuente/versión, pantalla y campos, entradas/salidas, permisos, estados, errores, persistencia, dependencias, prueba normal y de fallo, recuperación/cancelación, manual y diferencias. Un detalle no observado queda pendiente antes de cerrar su ID.

### M00 — Inventario y paridad

| ID | Entregable | Criterio de cierre |
|---|---|---|
| M00.01 | V/U. Mapa de menús y acciones, S01/U01 | Cada entrada tiene módulo; acciones ocultas identificadas como pendientes |
| M00.02 | P. Fuente, fecha y clasificación | Distinguir observación, diseño local y evidencia histórica |
| M00.03 | P. Comparación de recorridos | Mismo caso en referencia/local con resultado y diferencias |
| M00.04 | P. Guía versionada | Nuevos hallazgos añaden IDs sin borrar pendientes ni evidencias |

Esta revisión completa la organización documental inicial. No declara inspección exhaustiva del cliente; faltan los detalles del apartado 9.

### M01 — Workers y capacidad de Android

| ID | Requisito | Prueba de aceptación |
|---|---|---|
| M01.01 | P. Debian consola y servicios automáticos | Reiniciar sin login, conservar perfil y abrir Android; laboratorio ya aceptado |
| M01.02 | P. Inventario CPU/RAM/disco/red/arquitectura | Datos reales; worker perdido se marca no disponible |
| M01.03 | V/P. Catálogo de imágenes y versiones, S02 | Versión real/hash coinciden; rechazar imagen incompatible |
| M01.04 | P. Android 10–14 objetivo progresivo | Matriz por versión: arranque, ADB, entrada, vídeo y apps; solo Android 12 de laboratorio confirmado |
| M01.05 | P. Escala medida | Cargas escalonadas desde una instancia; latencia, recursos y reinicios; no declarar 50 sin prueba |
| M01.06 | P. ABI, gráficos, servicios y sensores | App instala/abre/responde; error preciso de incompatibilidad, sin garantía universal ARM/GMS/DRM |

Salida: informe de capacidad y límites por worker/imagen. M02 integra el inventario al panel. No cambiar de motor para rehacer el trabajo.

### M02 — Núcleo PC-MASTER y workers

| ID | Requisito | Prueba de aceptación |
|---|---|---|
| M02.01 | U/P. Panel oscuro como centro operativo | Operaciones diarias sin consolas; preservar Android ya funcional |
| M02.02 | P. Worker, imagen, perfil, cuenta, pantalla y tarea separados | Cerrar pantalla no apaga Android; mover grupo no migra almacenamiento |
| M02.03 | P. Descubrimiento y adopción aprobada | Detectar sin instalar; rechazar adopción duplicada/no autorizada |
| M02.04 | P. Agente autenticado y heartbeat | Rechazar identidad inválida; distinguir detenido, ausente y error |
| M02.05 | P. Persistencia y canal de órdenes | Separar lectura del panel y componente autorizado de escritura; no elevar el DSN lector actual |
| M02.06 | P. Salud y errores operativos útiles | Mensaje/código y recuperación; trazas solo en diagnóstico independiente |
| M02.07 | U/P. Español, vacíos, carga y teclado | Sin datos inventados ni botones muertos; uso en pantalla de laptop |

Salida: inventario consistente tras reiniciar. La primera ficha puede usar el worker conocido sin afirmar descubrimiento automático.

### M03 — Perfiles y múltiples cuentas

Fuentes S02/S03/S04/U01. Perfil = entorno Android persistente; cuenta social = sesión de una aplicación asociada. Son entidades distintas.

| ID | Función | Prueba de aceptación |
|---|---|---|
| M03.01 | V/P. Alta individual: nombre, grupo, etiquetas, notas, Android/modelo, proxy, worker y recursos | Validar, guardar y recuperar ficha real tras reinicio; propiedades de modelo no se presentan como hardware físico |
| M03.02 | V/U. Lista, búsqueda, filtros, selección y acciones | Encontrar perfil, limpiar filtros, paginar sin duplicados y conservar solo selección válida |
| M03.03 | V/P. Grupos/etiquetas: crear, editar, fusionar y mover | Mover conserva datos/proxy; fusión no pierde perfiles; borrar grupo explica efecto antes de confirmar |
| M03.04 | U/P. Iniciar/detener Android, reiniciar, abrir pantalla, cerrar conexión | Estado real, doble clic idempotente, cerrar ventana no detiene ni borra |
| M03.05 | V/P. Creación y edición masiva | Preview/validación por fila y resultado parcial; rechazar edición incompatible en ejecución |
| M03.06 | V. Clonar configuración, A01 | Nuevo perfil con configuración seleccionada, apps/datos limpios; no anunciar copia completa de cuentas |
| M03.07 | V/P. Restablecer como nuevo, A02 | Confirmación destructiva y campos conservados/eliminados claros; distinto de recuperar conexión |
| M03.08 | U/P. Exportar/importar | Definir ficha frente a datos; manifiesto/versiones/hash y validación; secretos excluidos por defecto |
| M03.09 | V/P. Transferir propietario; migrar worker como operación diferente | S03: cesión de control. Local: recepción/permisos confirmados; migración comprueba datos antes de retirar origen |
| M03.10 | U/H/P. Borrado, papelera y restauración | Confirmar alcance, retención configurable y borrado definitivo; fallo de conexión nunca elimina |
| M03.11 | P. Asociar plataforma/cuenta/perfil | Dos entornos propios conservan sesiones independientes; credenciales fuera de listas/exportaciones |
| M03.12 | V/P. Configuración de dispositivo e importación física autorizada, S24 | Matriz de campos soportados/no disponibles por imagen; no copiar claves privadas ni prometer identidad física genuina |

Salida: crear → configurar → iniciar → usar → cerrar → reiniciar → conservar → eliminar, sin afectar otro perfil. La clonación documentada borra apps/datos; duplicación de almacenamiento y migración son contratos distintos.

### M04 — Pantalla Android y herramientas

| ID | Función | Prueba de aceptación |
|---|---|---|
| M04.01 | P. Abrir/cerrar/reabrir y recuperar transporte por perfil | Conexión única ya aceptada; generalizar sin cerrar dispositivos ajenos ni reiniciar servidor ADB global |
| M04.02 | V/P. Entrada manual: toque, teclado, Unicode, gestos y teclas Android | S09 documenta acciones; probar español/foco/orientación; barra exacta original pendiente |
| M04.03 | V/P. Captura y visualización, S13 | Imagen del perfil correcto; dimensiones y fecha. Resolución/FPS/mosaico locales por comparar |
| M04.04 | V/P. Transferencia de archivos, S06/S15 | Ruta permitida, hash, progreso, disco lleno y desconexión |
| M04.05 | V/P. ADB autorizado, S26 | Solo perfil permitido; conexión restringida y timeout; terminal técnica separada |
| M04.06 | V/P. GPS/tipo de red, S13/A02/A03 | Leer lo aplicado; distinguir IP, GPS y SIM; declarar limitaciones de imagen |
| M04.07 | V/P. Galería, cámara y mirroring, S27 | Imagen en galería; webcam/vídeo/móvil solo si soportados, permisos y origen visibles |
| M04.08 | V/P. Contactos/mensajes de prueba, A04/A05 | Resultado por tarea; inyección de texto no equivale a recibir SMS/OTP de operador |
| M04.09 | V/P. Root y capacidades especiales, S13 | Mostrar soporte/efecto por imagen; no garantizar certificación o integridad |
| M04.10 | V/P. Teléfono físico USB/Wi-Fi opcional, S25 | Autorizado/no autorizado/offline/múltiples; selección explícita y desconexión segura |

Salida: control estable con límites de compatibilidad. Keybox A10, ocultación de accesibilidad anunciada en S13 y mantenimiento remoto S28 quedan inventariados sin habilitación automática ni equivalencia demostrada. No fabricar sensores, SIM, claves o atestación.

### M05 — Aplicaciones, Biblioteca y archivos

| ID | Función | Prueba de aceptación |
|---|---|---|
| M05.01 | V/P. Catálogo propio, búsqueda, versiones e instaladas, S07 | Package/versionCode/ABI/origen/hash reales; no tienda ficticia |
| M05.02 | V/P. Instalar APK y divididos/XAPK soportados, S07 | Compatibilidad/firma/disco; error por perfil. Play Store/GMS no se presuponen redistribuibles |
| M05.03 | V/P. Abrir/detener/actualizar/desinstalar por perfil/lote, S07/S13 | Resultado parcial por destino; no modificar paquetes fuera del lote |
| M05.04 | V/P. Apps del equipo y autoinstalación por grupo, S07 | Política versionada al arranque y fallo recuperable; instalación distinta de autoarranque |
| M05.05 | V/P. Autoarranque, mantener viva y permisos, A06/S13 | Límite de reintentos y consumo; soporte por versión Android |
| M05.06 | V/P. Biblioteca de imágenes/vídeos locales, S06 | Hash y archivo persistente; copia a Android distinta del activo original |
| M05.07 | V. Etiquetas y vistas lista/tarjetas, S30 | Crear/editar/asignar/filtrar; usar activo sin perder referencia |
| M05.08 | V/P. Recursos en flujos y envío masivo, S06/S29 | Progreso por archivo/destino; reintento definido; activo ausente no da éxito falso |
| M05.09 | P. Preview, cuota, exportación y retención | Persistencia local sin borrado impuesto a 30 días; aviso de disco y borrado explícito |

Salida: cargar/localizar/enviar medio, instalar/usar app compatible y repetir tras reiniciar. Integraciones de almacenamiento externo opcionales, no obligatorias.

### M06 — Proxies y red

| ID | Función | Prueba de aceptación |
|---|---|---|
| M06.01 | V. Guardar/editar/eliminar HTTP/HTTPS/SOCKS5, S05 | Tipo/host/puerto/auth/grupo; secretos fuera de registros |
| M06.02 | P. Importación masiva y duplicados | Preview por fila sin perder entradas existentes |
| M06.03 | V. Comprobar conexión/IP, S05/U01 | Diferenciar timeout, DNS, credenciales y servicio caído |
| M06.04 | V/P. Ubicación/canal de consulta, S05 | Proveedor/fecha/dato no disponible; no confundir con GPS |
| M06.05 | V/P. Asignar por perfil y comprobar desde Android, S02 | Probar tráfico del dispositivo, DNS/UDP/IPv6 y política al caer proxy, no solo consulta desde master |
| M06.06 | V/P. Cambio IP/refresco y edición masiva, S28 | URL autorizada, intervalo/timeout y resultado; no llamar URLs inventadas |
| M06.07 | V/P. Reglas de dominios, A03 | Aplicación y recuperación de regla; diferenciar fallo de app/proxy |

Salida: dos perfiles con rutas efectivamente comprobadas y persistentes. No proveer IP residenciales gratis ni prometer anonimato.

### M07 — RPA: editor y ejecución

S08/S09 describen capacidades; S28/S29 inspector; A07 un ejemplo exportado. No se conoce todavía todo el catálogo de bloques y formularios.

| ID | Función | Prueba de aceptación |
|---|---|---|
| M07.01 | V/P. Crear/editar/guardar/duplicar/versionar flujo visual | Grafo persistente, validación localizada y versión de ejecución inmutable |
| M07.02 | V. App, toque, deslizamiento, scroll, texto, espera y archivos | App de prueba con resultado observable; operación no soportada falla explícitamente |
| M07.03 | V/P. Selectores y coordenadas | S28/A07: texto/ID/árbol; otros campos por verificar. Elemento correcto o fallo, no toque accidental |
| M07.04 | V. Esperas por tiempo/elemento y timeout | Ausencia/aparición tardía, sin espera infinita |
| M07.05 | V. Variables, parámetros, datos de elementos | Tipo/ámbito/salida definidos; valor ausente y marcado/seleccionado comprobados |
| M07.06 | V. Condiciones, bucles y errores | Ambas ramas, límite y fallo; reintento no duplica efectos externos |
| M07.07 | V/P. Biblioteca/archivos y datos | Activo por ID/etiqueta; validar tipo/ruta; no secretos en logs |
| M07.08 | V/P. Inspector, abrir/guardar árbol UI, S29 | Perfil correcto, diálogo separado y exportación sin campos sensibles |
| M07.09 | V/P. Prueba del flujo y trazabilidad | Resultado por paso, captura opcional y cancelación sin ejecutar pasos posteriores |
| M07.10 | V/P. Importar/exportar flujo, A07 | Formato local versionado y validado; GAL no se anuncia compatible por copiar un ejemplo |

Salida: flujo en app propia con entrada, rama, bucle, espera, archivo y error provocado. Primero motor mínimo fiable, luego editor/bloques avanzados. IA no es requisito para ejecutar un toque.

### M08 — Sincronizador

| ID | Función | Prueba de aceptación |
|---|---|---|
| M08.01 | V/P. Maestro y destinos, S10 | Solo selección explícita; advertir Android/resolución/interfaz distintos |
| M08.02 | V/P. Acciones manuales repetidas en directo, S10 | Toques/scroll/texto medidos; mapear o rechazar incompatibles |
| M08.03 | P. Pausa/reanudación, quitar destino y detener | Caída de uno no bloquea todos ni reproduce cola peligrosa al reconectar |
| M08.04 | H/P. Texto diferente por destino/pantalla completa | Catálogo v3.9.8/v3.9.1; contrastar UI actual antes de equivalencia |
| M08.05 | V/P. Subida masiva e historial, S29 | Progreso por archivo/teléfono, cancelación y errores parciales |

Salida: dos perfiles sincronizados, probando orientación/latencia/desconexión. Transmitir vídeo no prueba sincronización. No duplicar RPA.

### M09 — Tareas, calendario y lotes

| ID | Función | Prueba de aceptación |
|---|---|---|
| M09.01 | V/P. Publicar tarea con flujo/parámetros/destinos/horario, S08/S09 | Zona horaria, fecha pasada y capacidad validadas |
| M09.02 | V/P. Repetición y activos por etiqueta, S30 | Frecuencia/fin/comportamiento sin activos; no duplicar al reabrir master |
| M09.03 | V/P. Cola persistente y exclusión por perfil | S13/P. Dos tareas no controlan el mismo Android a la vez; falta de recursos queda en cola |
| M09.04 | V/P. Consultar/cancelar/reintentar/historial, S13 | Estado por destino; no repetir publicación ya confirmada |
| M09.05 | P. Recuperación de tarea interrumpida | Diferenciar no iniciada/interrumpida/efecto desconocido antes de reintentar |
| M09.06 | V. Ver parámetros publicados e informe, S28/S30 | Versión/activos/parámetros usados aunque cambie después el flujo |

Salida: ahora/programada/cancelada y reinicio con tareas pendientes/interrumpidas. No prometer pausa universal de acciones indivisibles.

### M10 — GeeHub: API, CLI, MCP y eventos

| ID | Función | Prueba de aceptación |
|---|---|---|
| M10.01 | V/P. API propia de perfiles/apps/medios/red/tareas, S12/S15 | Servicio común con UI, contrato versionado y mismos estados |
| M10.02 | V/P. Credenciales revocables y permisos, S13 | Lectura no modifica; revocación efectiva; sin token cloud GeeLark |
| M10.03 | V/P. CLI con ayuda, JSON/tabla y códigos, S14 | Listar/iniciar/consultar sin contraseña en argumentos |
| M10.04 | V/P. MCP propio, S14 | Descubrir herramienta y ejecutar solo acción autorizada; sin proveedor IA pagado obligatorio |
| M10.05 | V/P. Eventos/webhooks locales, A08 | ID/reintento/persistencia; destinatario caído o duplicado no pierde/repite efecto |
| M10.06 | V/P. ADB/shell opcional y ejemplos, S15/S26 | Perfil/tiempo acotados y redacción de secretos |

Salida: una operación consistente en UI/API/CLI y herramienta MCP con permisos. API se define con cada módulo; su interfaz externa se completa en esta etapa. No copiar endpoints comerciales como dependencia.

### M11 — Analíticas, auditoría y consumo

| ID | Función | Prueba de aceptación |
|---|---|---|
| M11.01 | V/P. Auditoría de acciones, S19 | Quién/cuándo/perfil/acción/resultado: acceso, apertura, edición, eliminación y transferencia |
| M11.02 | V/P. Reporte por tarea y parámetros, S30 | Correlación con ejecución/paso/destino/activos |
| M11.03 | P. Filtros/búsqueda/exportación | S20 no describe todos los campos; propuesta local con equivalencia exacta pendiente |
| M11.04 | V/P. Métricas sociales, S11 | Instagram/TikTok/YouTube/Reddit; fuente/fecha y dato ausente; acceso gratuito no supuesto |
| M11.05 | P. CPU/RAM/disco/red/tiempo/cuotas | Adaptación de finalidad de S23: consumo real separado de métricas sociales/dinero |
| M11.06 | P. Diagnóstico independiente y retención | Auditoría de acciones persiste aunque se desactive diagnóstico; exportación sin secretos |

Salida: acción encontrada por perfil/tarea con resultado verificable. No inventar estadísticas; no equiparar captura ocasional con integración estable.

### M12 — Miembros y colaboración

| ID | Función | Prueba de aceptación |
|---|---|---|
| M12.01 | V/P. Miembros y grupos de derechos locales, S18 | Alta/edición/baja/restablecimiento sin cuenta cloud obligatoria |
| M12.02 | V. Administrador/gestor/miembro, S18 | Matriz crear/editar/ejecutar/borrar/API/RPA y denegación comprobada |
| M12.03 | V/P. Acceso por grupos de perfiles y cuotas, S18 | No ver/operar otro grupo; cómputo de cuota coherente |
| M12.04 | V/P. Compartir/transferir, S19/S03 | Compartir acceso distinto de propiedad/copia; revocación efectiva |
| M12.05 | P. Sesiones y revocación auditadas | Baja/cambio de derechos bloquea accesos; secretos según permiso |

Salida: dos usuarios con acciones permitidas/denegadas reales. Multiusuario no habilita LAN antes de aceptar esa modalidad.

### M13 — Asistente y AIGC

| ID | Función | Prueba de aceptación |
|---|---|---|
| M13.01 | V/P. Ayuda/redacción, S16 | Manual local, español y reconocimiento de dato desconocido |
| M13.02 | P. Proponer flujos mediante lenguaje natural | Validar esquema y mostrar acciones antes de ejecutar. S16 conecta contenido/flujos, no prueba compilador universal |
| M13.03 | V/P. Imagen por texto/referencia, S17 | Licencia/modelo/hash/entradas/salida y recursos; guardar en Biblioteca |
| M13.04 | V/P. Texto a vídeo e imagen a vídeo, S17 | Benchmark de cada modalidad; si no viable en hardware, diferencia abierta sin API pagada oculta |
| M13.05 | V/P. Edición, largo a cortos y mejora, S17 | Edición convencional local separada de equivalencia IA; medir calidad/tiempos |
| M13.06 | V/P. Cola/historial/cancelación/cuotas, S29/S30 | Recursos no bloquean Android; errores y parciales; sin créditos comerciales |

Salida: cada modalidad individual con licencia y medición. Modelos propietarios no se prometen reproducibles con idéntica calidad/velocidad. Núcleo Android funciona sin IA.

### M14 — Plantillas, recursos y casos de uso

| ID | Función | Prueba de aceptación |
|---|---|---|
| M14.01 | V/P. Catálogo local de plantillas, S31 | Categoría/búsqueda/versión; app/Android/idioma/parámetros/permisos antes de publicar |
| M14.02 | V/P. Plantillas propias importables/exportables, A07 | Validar sin ejecutar al importar; no copiar catálogo propietario sin licencia |
| M14.03 | P. Adaptador por plataforma/versiones | Cada flujo tiene prueba y límites; una plantilla no da soporte universal a esa red |
| M14.04 | V/P. Recursos e integraciones, S21 | Directorio/manuales gratuitos; enlaces de terceros opcionales |
| M14.05 | U/P. Blog/glosario/prensa/enlaces/afiliación | Guía del operador: contenido comercial inventariado; manual/glosario sí, comisiones no equivalentes |

Salida: una plantilla propia completa antes de la siguiente, no ocho integraciones a la vez.

### M15 — Continuidad y recuperación

| ID | Requisito | Prueba de aceptación |
|---|---|---|
| M15.01 | P. Cierre/reapertura master | Android conserva datos; reconcilia estado real sin reiniciar todos los perfiles |
| M15.02 | P. Reinicio worker/reconexión | Laboratorio aceptado; generalizar por perfil sin login Debian |
| M15.03 | P. Master desconectado | Política explícita de lo que continúa en agente y lo que depende del master |
| M15.04 | P. Funciones locales sin Internet | Listado/control LAN/medios propios; distinguir servicios sociales/descargas ausentes |
| M15.05 | P. Exportación/restauración solicitada | Alcance y resultado verificables; no copias automáticas impuestas |

Salida: matriz de fallos master/worker/red/ADB sin pérdida ni duplicación. PWA es opción histórica, no requisito de exposición pública.

### M16 — Instalación y mantenimiento

| ID | Requisito | Prueba de aceptación |
|---|---|---|
| M16.01 | P. Preparador desde GitHub | Windows limpio; detectar requisitos, generar configuración y preservar existente |
| M16.02 | P. Arranque discreto/actualización | Sin CMD permanente, versión identificada, credenciales/datos conservados y fallo recuperable |
| M16.03 | P. Agente/redroid tras adopción | Equipo autorizado, pasos idempotentes y progreso; no instalar en candidato no adoptado |
| M16.04 | P. Debian mínimo por red/PXE | Estudio y prueba independiente en equipo vacío autorizado, consola, sin tocar discos ajenos |
| M16.05 | P. Caché/versiones/imágenes | Procedencia/hash/licencia; no sustituir imagen activa sin procedimiento de datos |
| M16.06 | P. Arranque headless del laboratorio | Diferenciar host apagado, VM apagada y worker físico; automatización comprobada por separado |

Salida: preparación reproducible sin múltiples consolas. Asistente actual no equivale a instalar Windows/Python/PostgreSQL ni PXE completo.

### M17 — Calidad, manuales y cierre

| ID | Entregable | Prueba de aceptación |
|---|---|---|
| M17.01 | P. Manual español por módulo | Opciones, procedimientos, requisitos, errores, límites y recuperación |
| M17.02 | P. Pruebas de comportamiento/regresión | Windows real + worker consola + Android; CI no reemplaza aceptación física |
| M17.03 | P. Matriz de diferencias | Cada ID con estado/evidencia, sin porcentaje global ficticio |
| M17.04 | P. Aislamiento y permisos | Completar #77 antes de exposición/fusión dependiente; no ampliar privilegios para ocultar fallos |

Salida: comportamiento comparado y aceptado. Describir una capacidad o pasar pruebas unitarias no demuestra paridad.

## 5. Redes sociales y casos de uso

Son flujos sobre los mismos perfiles/apps/Biblioteca/proxies/tareas; no motores Android distintos. Se operan cuentas propias/autorizadas. No garantía de ausencia de bloqueos ni ingresos.

| Plataforma | Referencia y primer alcance a especificar | Pendiente antes de automatizar |
|---|---|---|
| TikTok | S31/S28–S30: contenido propio, perfil y publicación vídeo/carrusel | Región/idioma/app/parámetros por plantilla |
| Instagram/Reels | S31/S11: publicación propia y medios de Reels | Stories/mensajes/otros flujos con evidencia individual |
| YouTube/Shorts | S31/S11: vídeo propio y metadatos | Formularios diferentes de Shorts/vídeo largo |
| Snapchat | Categoría del operador/sitio comercial: instalar/usar/aislar app | No plantilla específica comprobada en marketplace inspeccionado |
| X/Twitter | S31: texto/imagen/vídeo propios | Formatos/permisos/límites de app |
| Facebook | S31: publicación propia/Reels | Perfil/página/grupo no son el mismo destino |
| Reddit | S31/S11: contenido propio y comunidad | Reglas/permisos por comunidad |
| Pinterest | S32/S31: pines/tableros y contenido propio | Campos y formato por plantilla |
| Threads | S31: plantillas adicionales encontradas | Inventariado, no amplía automáticamente módulo activo |
| Google/SHEIN | Índice API S13: flujos adicionales anunciados | No se convierten automáticamente en alcance inmediato |

S13 anuncia más operaciones sociales (acceso, edición, publicaciones, comentarios, mensajes, mantenimiento). Se registra su existencia, no todos sus parámetros como contrato comprobado. Nombres comerciales como warm-up no acreditan seguridad o resultados.

| Caso solicitado | Piezas necesarias | Resultado verificable |
|---|---|---|
| Marketing social | Perfiles, medios, calendario, plantillas, analítica disponible | Publicación autorizada de prueba e informe |
| Afiliados | Lo anterior + campaña/enlaces/metadatos | Asociación contenido/campaña, sin prometer comisión |
| Ecommerce/dropshipping | Apps/medios/negocio/flujos propios | Caso autorizado de catálogo/publicación, sin pagos de prueba automáticos |
| Airdrops | Apps/carteras propias, perfiles y seguimiento | Tareas autorizadas; firmas/transferencias explícitas; sin rentabilidad ni tasas gratis prometidas |
| Verificación de anuncios | Red/localización/capturas/comparación | Evidencia de campaña propia, sin clics artificiales |
| Investigación de mercado | Fuentes permitidas/navegación/exportación | Datos con origen/fecha y cobertura |
| Pruebas de apps | App propia/versiones Android/RPA/reportes | Caso reproducible de instalación/interacción/error en dos entornos |

S33/S34 describen escenarios comerciales, no pruebas de ganancias, identidad física o rendimiento.

## 6. Orden cerrado de construcción

| Etapa | Trabajo | Condición de salida |
|---|---|---|
| 0 | Guía y lagunas documentadas | Sin implementar nuevos módulos en esta revisión |
| 1 | M03: registrar instancia existente en Perfiles | Contrato mínimo M02, nombre/worker/Android/estado reales; conservar abrir/cerrar |
| 2 | M03: grupos, etiquetas, filtros y ficha editable | Persistencia/errores y tabla funcional, no maqueta |
| 3 | M01/M03: segunda instancia y ciclo de vida | Primero crear; luego iniciar/detener; después aislamiento y medición |
| 4 | M02/M16: workers, adopción y despliegue | Un worker físico autorizado desde panel; no afirmar PXE por probar laboratorio |
| 5 | M05: Aplicaciones/Biblioteca | Paquete/medio enviados y resultado por destino |
| 6 | M06: Proxies/red | Prueba desde Android y tratamiento de fallo, sin proveedor pagado obligatorio |
| 7 | M04: herramientas restantes | Archivos/captura/configuración; avanzadas por soporte de imagen |
| 8 | M07: motor mínimo y editor RPA | Flujo en app propia, error controlado, versión/manual |
| 9 | M09: programación y lotes | Reinicio/cancelación sin duplicar efectos |
| 10 | M08: Sincronizador | Dos perfiles, divergencia y fallo aislados |
| 11 | M10: CLI/MCP/eventos | API nace con cada módulo; completar interfaces externas |
| 12 | M11: analíticas/consumo | Auditoría nace con cada acción; luego vistas completas y métricas disponibles |
| 13 | M12: Miembros | Permisos aceptados antes de acceso multiusuario/LAN |
| 14 | M14: plantillas por plataforma | Una app y caso a la vez, con versión y prueba |
| 15 | M13: asistente/AIGC | Cada modalidad con licencia/hardware/benchmark local |
| 16 | M15/M16/M17: ampliación y cierre | Recuperación/manuales en cada etapa; ampliar solo tras medir |

Las etapas expresan dependencias; no autorizan implementar varios módulos a la vez. Sin fechas o capacidades prometidas sin evidencia.

**Próximo incremento propuesto, sin ejecutarlo ahora:** listado/ficha de Perfiles que registra la instancia ya operativa; estado real, abrir/cerrar desde la fila y persistencia. No crear 50 instancias ni empezar IA/proxies/RPA.

## 7. Diferencias estructurales explícitas

| GeeLark / expectativa | Decisión local |
|---|---|
| Teléfono/granja cloud | PC-WORKER propios; master controla sin ejecutar todos los Android |
| ARM/modelos anunciados | Laboratorio x86_64 Android 12; compatibilidad por ABI/app medida, propiedades no transforman hardware |
| Identidad genuina/antidetección anunciada | Aislamiento/configuración verificables; sin garantía de anonimato o atestación física |
| Clonar | A01 limpia apps/datos; copia de datos/migración con contrato propio |
| Transferir | Propiedad/permisos/importación entre instalaciones, distinto de mover grupo o migrar worker |
| Minutos/saldo/planes | Sin cobros/recargas; consumo y capacidad reales, no saldo ficticio |
| Generación con proveedores comerciales | Modalidad local condicionada, diferencia de calidad/hardware explícita |
| Proxy comercial | Gestión de proxies propios, no suministro gratis prometido |
| Retención cloud | Biblioteca persistente con cuota por disco y borrado explícito |
| Soporte remoto de proveedor | Diagnóstico controlado por propietario, sin acceso de terceros automático |
| Referidos/afiliación | Inventariados sin comisiones en app personal |
| OEM/white label, A09 | Personalización propia, sin servicio comercial ajeno |
| Navegador independiente | Función registrada de GeeLark, fuera de Android acordado |
| SMS/cámara/sensores/keybox | Soporte individual comprobado, no telefonía/clave/certificación fabricada |
| Acceso desde cualquier lugar | LAN y acceso remoto propio posterior; no abrir Internet por defecto |

## 8. Entrega por incremento

1. Especificar IDs concretos, campos, recorrido original y diferencia local.
2. Implementar UI/servicio/persistencia necesarios sin añadir funciones ajenas.
3. Probar caso normal y errores/desconexiones relevantes.
4. Documentar manual completo y comparación con GeeLark.
5. Prueba física del operador de una acción por vez.
6. Registrar versión/evidencia; cerrar solo IDs aceptados y avanzar.

No marcar módulo equivalente por aspecto visual ni fusionarlo por CI si depende de aceptación pendiente. Esta revisión solo cambia documentación y mantiene intacta la instalación.

## 9. Lagunas de evidencia abiertas

- **G01:** formularios completos de alta rápida/masiva, edición, exportación, transferencia, papelera y menú oculto. U01 demuestra solo acciones visibles.
- **G02:** barra Android completa, audio, rotación, cámara/mirroring y ajustes.
- **G03:** todos los bloques RPA, parámetros, ámbitos y lenguaje GAL completo. Manual web no legible; ejemplo exportado insuficiente.
- **G04:** textos por destino, ventanas y política de errores actual del sincronizador; hay evidencia histórica, no contrato actual completo.
- **G05:** campos/filtros/retención de Logs, Principal, Referidos y ajustes. Página pública vacía no permite inferirlos.
- **G06:** IA, modelos/proveedores cambiantes y equivalencia por modalidad.
- **G07:** ABI/GMS/DRM/atestación/sensores/segundo plano por imagen. Cloud comercial no prueba redroid.
- **G08:** parámetros/versiones/idiomas de todas las plantillas; marketplace paginado y cambiante.
- **G09:** navegador de escritorio aparece en S35; diferencia conservada, no ampliación tácita de alcance.

Las lagunas se resuelven de una en una al entrar al módulo, antes de declarar equivalencia. No pedir ahora todas las capturas ni repetir pruebas ya aceptadas. La investigación pública amplia no se presenta como inspección autenticada exhaustiva.
