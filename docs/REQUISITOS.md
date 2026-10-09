# Requisitos y criterios de aceptación

## REQ-001 — Costo operativo de 0 USD

**Prioridad:** crítica.  
No depender de pagos obligatorios, tarjeta bancaria, pruebas temporales, APIs pagadas ni servicios con cobro automático.

**Aceptación:** antes de adoptar una dependencia, documentar precio, requisito de tarjeta, límites de uso, cuotas, restricciones comerciales, almacenamiento, ancho de banda, usuarios, ejecución y riesgo de suspensión. Debe existir alternativa local o gratuita sostenible para cada función crítica.

## REQ-002 — Administración de instancias Android

Administrar instancias con distintas versiones de Android; objetivo inicial de hasta 50, ampliable.

**Aceptación:** inventario de instancias, estado, versión, nodo asignado, acciones disponibles, errores y registros. El límite real de instancias se establecerá mediante pruebas de carga, no por estimación.

## REQ-003 — Infraestructura distribuida

Evaluar un controlador y nodos de trabajo en equipos separados, con posibilidad de añadir nodos.

**Aceptación:** un nodo nuevo puede incorporarse siguiendo un procedimiento documentado; la pérdida del controlador no debe corromper el estado y los trabajos ya iniciados deben comportarse según una política documentada.

## REQ-004 — Acceso remoto seguro

Administración desde PC y móvil, dentro o fuera de la red local.

**Aceptación:** autenticación, autorización por función, transporte cifrado, registro de acciones relevantes, revocación de sesiones y ausencia de credenciales en logs. El acceso externo debe usar un mecanismo seguro y documentado.

## REQ-005 — Operación offline o conectividad limitada

Implementar PWA/caché/cola local cuando sea viable.

**Aceptación:** cada módulo identifica explícitamente las operaciones disponibles offline, las que requieren red, política de reintentos, idempotencia, identificadores únicos, sincronización y resolución de conflictos.

## REQ-006 — Validación funcional contra GeeLark

GeeLark es la referencia de comportamiento observable.

**Aceptación:** por cada función, registrar el flujo de referencia, configuración, resultado esperado, resultado de Geelark-IA, evidencias y diferencias conocidas. No marcar paridad como lograda sin pruebas.

## REQ-007 — Documentación por módulo

Cada módulo debe incluir manual de usuario completo y documentación técnica.

**Aceptación:** propósito, requisitos, instalación, configuración, opciones, procedimientos, errores frecuentes, seguridad, pruebas, limitaciones y resolución de problemas.

## REQ-008 — Trazabilidad GitHub

Registrar requisitos, decisiones, tareas, errores, soluciones, pruebas y avances.

**Aceptación:** trabajo relevante vinculado a Issues/PRs/commits cuando corresponda; incidencias incluyen pasos para reproducir, resultado esperado/real, causa conocida o hipótesis, solución y prueba de regresión.

## REQ-009 — Seguridad y privacidad

**Aceptación:** secretos fuera del repositorio; configuración sensible en variables/archivos locales ignorados por Git; permisos mínimos; copias y recuperación documentadas.

## REQ-010 — Entrega incremental

**Aceptación:** no iniciar un módulo dependiente hasta que el módulo actual tenga criterios de aceptación, pruebas, documentación y estado explícito (pendiente/en curso/bloqueado/terminado).

## REQ-011 — Uso responsable de aplicaciones

Las automatizaciones deben respetar las condiciones aplicables de las plataformas y no prometer ganancias, recompensas o funcionamiento garantizado de aplicaciones externas.

## Pendiente de especificación

- Catálogo priorizado de funciones GeeLark.
- Requisitos medibles de rendimiento por instancia.
- Política de respaldo y recuperación.
- Compatibilidad por versión Android.
- Modelo de amenazas y roles de usuario.
