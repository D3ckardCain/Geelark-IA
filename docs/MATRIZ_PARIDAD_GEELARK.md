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
| P-002 | Identidad/huella | Se publicita huella única y opción de huella personalizada | Identidad configurable por instancia solo donde la virtualización lo permita | Página de producto/precios | No especificado | Identificar campos exactos y detectar diferencias de virtualización |
| P-003 | Grupos/etiquetas | Organización de perfiles | Grupos, etiquetas, filtros y operaciones por grupo | Centro de ayuda | Investigación inicial | CRUD, filtrado y acciones masivas |
| P-004 | Proxies | Proxies guardados/personalizados, prueba de conexión | Gestión de endpoints y asignación por instancia | Ayuda de perfiles | Investigación inicial | Conexión, credenciales protegidas y errores |
| P-005 | Aplicaciones | Operaciones de apps por perfil/grupo | Listar, instalar, iniciar, detener, actualizar y quitar APK | Centro de ayuda/notas de versión | Investigación inicial | Compatibilidad, permisos y operación por lotes |
| P-006 | Archivos/Library | Biblioteca multimedia para automatización | Biblioteca local persistente, etiquetas, búsqueda y asignación | Ayuda Library | Investigación inicial | Importar/exportar, deduplicar y recuperación |
| P-007 | RPA visual | Taps, swipes, escritura, esperas, lógica, bucles, variables, manejo de errores | Editor visual y motor de flujos | Página RPA | Investigación inicial | Ejecutar flujo simple y validar errores/reintentos |
| P-008 | Plantillas | Flujos listos para tareas repetitivas | Catálogo local versionado/importable | Página de automatización | Investigación inicial | Importar, validar, versionar y ejecutar |
| P-009 | Synchronizer | Copiar interacciones de una instancia principal a otras; texto masivo | Replicar eventos entre instancias seleccionadas | Página Synchronizer | Investigación inicial | Resolución distinta, latencia, exclusiones y pausa |
| P-010 | API | Operaciones de perfiles, automatización, apps, archivos y Library | API local autenticada | Página API | Investigación inicial | Contratos, autenticación, idempotencia y errores |
| P-011 | ADB | Habilitar ADB y ejecutar comandos en cloud phone | Puente ADB local a cada instancia compatible | Guía ADB | Investigación inicial | Conexión, autorización, comandos y reconexión |
| P-012 | Webhooks/eventos | Callbacks para operaciones | Eventos locales y cola persistente | Página API | Investigación inicial | Entrega, reintento, duplicados e idempotencia |
| P-013 | Analytics | Paneles/analítica por plan | Métricas locales de tareas y recursos | Precios/centro de ayuda | Investigación inicial | Exactitud y exportación |
| P-014 | Logs | Registros de operación | Logs filtrables, trazabilidad y exportación | Centro de ayuda/precios | Investigación inicial | Correlación tarea-dispositivo y redacción de secretos |
| P-015 | Miembros/roles | Miembros, permisos y roles | Usuarios/roles locales si el alcance lo requiere | Precios/centro de ayuda | Investigación inicial | Pruebas de autorización y auditoría |
| P-016 | AIGC/IA | Generación de contenido y asistente IA | Alternativas locales libres, según hardware | Centro de ayuda | Investigación inicial | Licencia, calidad, rendimiento y memoria |
| P-017 | Recursos/marketplace | Recursos y plantillas compartidas | Repositorio local importable/exportable | Centro de ayuda | Investigación inicial | Procedencia, validación y versiones |
| P-018 | Facturación/planes | Planes, límites, uso por minuto y servicios pagados | No replicar cobros; medir y limitar recursos locales | Página precios/facturación | Diferencia estructural | Definir límites de recursos y reportes locales |
| P-019 | Cámara/sensores/GPS | Documentación parcial sobre cámara; no se han verificado todos los sensores | Emular solo lo soportado por el virtualizador | Centro de ayuda | No investigado a fondo | Probar cámara, ubicación, sensores, audio y notificaciones |
| P-020 | Instalación/actualización | Guías de descarga y notas de versión | Instalación local reproducible y actualización reversible | Centro de ayuda | Investigación inicial | Instalación limpia, backup, actualización y rollback |
| P-021 | Operación offline | GeeLark se basa en servicios cloud | Administración local y cola offline cuando sea posible | Requisito del proyecto | Adaptación propia | Definir funciones offline y pruebas de desconexión |
| P-022 | Escalabilidad | GeeLark ofrece paralelos y perfiles cloud | Escalar instancias locales según CPU/RAM/GPU/almacenamiento | Página precios | No equivalente por defecto | Benchmark incremental de 1, 2, 5, 10 instancias |
| P-023 | Android versions | Páginas consultadas enumeran Android 9–15 y Synchronizer menciona Android 9–16; fuentes no coinciden | Seleccionar imágenes locales compatibles tras investigar | Página Synchronizer/precios | Pendiente de aclarar | Confirmar soporte vigente y requisitos por versión |
| P-024 | Perfiles clonados | La página de precios indica clonado en planes superiores | Clonar configuración/imagen de instancia sin compartir accidentalmente identidad | Precios | Investigación inicial | Clonación, independencia y limpieza de datos |
| P-025 | Operaciones masivas | Crear perfiles y operar apps en grupos; Synchronizer | Cola de tareas por grupos con resultados individuales | Perfil/RPA/Synchronizer | Investigación inicial | Fallos parciales, cancelación y recuperación |

## Reglas para completar cada fila

1. Adjuntar enlace y fragmento de evidencia oficial.
2. Enumerar todas las opciones/campos del flujo, incluidos errores y restricciones por plan.
3. Documentar si es función del producto, del servicio cloud, del sistema operativo o de un proveedor externo.
4. Definir alternativa local gratuita y dependencias de hardware/software.
5. Añadir criterios de aceptación y prueba reproducible.
6. Registrar diferencias entre GeeLark y Geelark-IA.
7. Cambiar estado solo cuando haya evidencia del hito.
