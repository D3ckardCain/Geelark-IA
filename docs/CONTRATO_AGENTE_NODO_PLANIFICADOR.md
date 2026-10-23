# Contrato del agente de nodo y planificador distribuido

**Versión:** 0.1  
**Fecha:** 2026-10-09  
**Estado:** especificación de diseño; no implementada ni probada.  
**Relacionado:** `ARQUITECTURA_CLUSTER_HETEROGENEO.md`, ADR-003, issue #14.

## 1. Objetivo

Definir el contrato entre el plano de control de Geelark-IA y cada PC del clúster. Los nodos pueden tener CPU, RAM, GPU, almacenamiento, sistema operativo y motores Android distintos. El controlador debe poder descubrir capacidades, asignar trabajos compatibles, supervisar ejecuciones y recuperarse de desconexiones sin asumir que todos los equipos son idénticos.

## 2. Principios obligatorios

- El agente se ejecuta como servicio local con usuario y permisos mínimos; no acepta shell arbitrario.
- Cada nodo tiene un UUID interno estable, nombre legible, credencial propia y estado de revocación.
- El agente no confía en mensajes no autenticados ni en identificadores enviados por la interfaz sin validación.
- La API de administración, ADB, sockets de Docker/Podman, hipervisor y consola del sistema no se exponen a Internet.
- El controlador solo puede solicitar operaciones incluidas en una lista permitida y versionada.
- Las credenciales de nodo se almacenan fuera de logs, reportes y payloads genéricos.
- Las capacidades llevan versión, fecha de medición y nivel de confianza: `observed`, `configured` o `unknown`.
- La pérdida de conexión no implica que el nodo o las instancias hayan parado.
- Nunca se permite que una misma instancia tenga dos propietarios activos confirmados al mismo tiempo.
- Una operación con resultado incierto no se repite automáticamente si puede causar efectos duplicados.

## 3. Componentes

### Plano de control
Mantiene inventario de nodos, configuración deseada, asignaciones, permisos, cola de tareas, historial y política de recuperación. Su base de datos es la fuente autoritativa de metadatos, con copias de seguridad y migraciones versionadas.

### Agente de nodo
Servicio que:
1. registra/renueva su sesión autenticada;
2. envía latidos y telemetría de recursos;
3. anuncia motores y capacidades Android disponibles;
4. recibe tareas permitidas;
5. valida la tarea antes de ejecutarla;
6. ejecuta mediante adaptadores locales;
7. informa progreso, resultado y errores redactados;
8. conserva un diario local mínimo para reconciliar tras desconexión;
9. admite drenaje y mantenimiento controlado.

### Adaptador de motor
Encapsula el runtime redroid detrás del contrato Android. El agente no debe asumir capacidades no verificadas: la compatibilidad de comandos, formatos de disco, ABI y recursos debe medirse para la imagen y el kernel fijados.

### Planificador
Calcula elegibilidad, puntuación, asignación y capacidad restante. La primera versión no migrará instancias activas automáticamente; asignará nuevas instancias y trabajos, y permitirá recuperación mediante backup/restore solo cuando el motor lo soporte y las pruebas lo validen.

## 4. Registro de nodo y estados

Estados sugeridos:
- `pending_enrollment`: detectado pero no autorizado;
- `online`: autenticado y con heartbeat reciente;
- `degraded`: responde, pero faltan capacidades o hay alertas;
- `draining`: no recibe nuevas asignaciones;
- `offline`: heartbeat vencido;
- `revoked`: acceso revocado;
- `maintenance`: mantenimiento autorizado.

El alta debe requerir aprobación explícita del administrador o un token de inscripción de un solo uso con expiración. La baja/revocación debe invalidar las credenciales y registrar quién la solicitó.

El estado `offline` es una observación del controlador, no prueba de que el equipo esté apagado. Al reconectar, el nodo envía su inventario y estado real; el controlador reconcilia antes de enviar acciones nuevas.

## 5. Esquema mínimo de recursos

Cada informe debe incluir:
- UUID y versión del agente;
- sistema operativo, kernel y arquitectura;
- CPU lógica/física cuando sea detectable, carga actual y características relevantes;
- RAM total, disponible y reserva del sistema;
- discos, capacidad libre y directorios de datos;
- GPU y aceleración disponible cuando corresponda;
- virtualización de hardware y capacidades del kernel;
- motores Android instalados, versiones, imágenes, ABI y capacidades probadas;
- instancias en ejecución y recursos asignados;
- salud del nodo, última actualización y errores de sensores/medición.

No se requiere recopilar números de serie del hardware ni identificadores personales. Telemetría opcional debe documentarse y poder desactivarse cuando no sea necesaria.

Cada capacidad debe distinguirse entre:
- `observed`: comprobada por el agente;
- `configured`: definida por el administrador;
- `tested`: comprobada mediante prueba de conformidad;
- `unknown`: no se dispone de evidencia suficiente.

## 6. Contrato de tareas

Cada tarea lleva:
- `task_id` UUID;
- `idempotency_key`;
- versión del esquema;
- tipo de operación de lista permitida;
- instancia/perfil objetivo si aplica;
- restricciones de compatibilidad;
- prioridad y vencimiento opcionales;
- límite de tiempo, memoria y reintentos;
- política de cancelación;
- datos de entrada validados;
- identidad del solicitante y referencia de auditoría.

Estados mínimos:
`queued`, `assigned`, `accepted`, `running`, `pause_requested`, `cancel_requested`, `succeeded`, `failed`, `cancelled`, `unknown_after_disconnect`.

El agente debe rechazar tareas expiradas, mal formadas, no autorizadas, incompatibles o repetidas con la misma clave idempotente. Las tareas de larga duración deben enviar progreso y heartbeat.

## 7. Reglas iniciales del planificador

### Filtros obligatorios (hard constraints)
1. Nodo online y no drenado.
2. Credenciales válidas y versión del agente compatible.
3. Motor, imagen Android, ABI y capacidades requeridas disponibles.
4. RAM libre suficiente más reserva de seguridad configurable.
5. Disco libre suficiente para la instancia y margen de crecimiento.
6. Límite configurado de instancias y de concurrencia no excedido.
7. Etiquetas/restricciones del perfil satisfechas.
8. Nodo no marcado como comprometido, en mantenimiento o degradado de forma incompatible.

### Puntuación (soft constraints)
Después de filtrar, puntuar por:
- margen de RAM;
- carga de CPU y capacidad observada;
- espacio y rendimiento del disco;
- afinidad con datos/artefactos ya presentes;
- coste de transferencia de backup;
- equilibrio de carga;
- prioridad de trabajo y preferencia administrativa.

La ponderación debe ser configurable y quedar registrada para explicar cada asignación. No usar solo el número de núcleos ni asumir que más RAM siempre resuelve cuellos de botella de CPU/GPU/disco.

### Sobreasignación
Por defecto, no permitir sobreasignación de RAM ni espacio de disco por encima de límites conservadores. Solo habilitar ratios configurables después de pruebas y con alertas. La estimación de capacidad por nodo se obtiene empíricamente con una carga de referencia Android; no se calcula una cifra universal por fórmula.

## 8. Protocolo de comunicación

La primera implementación debe usar un protocolo documentado y versionado sobre la red privada:
- TLS con autenticación mutua o mecanismo equivalente con identidad individual de nodo;
- expiración, rotación y revocación de credenciales;
- límite de tamaño y tasa de mensajes;
- validación de esquema y versión;
- nonce/ID de mensaje o mecanismo equivalente para evitar repetición;
- heartbeat separado de tareas de larga duración;
- respuestas idempotentes a solicitudes repetidas;
- auditoría sin secretos.

La tecnología concreta (HTTPS REST, WebSocket/SSE para eventos u otra) se decidirá al implementar. No introducir un broker distribuido adicional hasta que pruebas lo justifiquen.

## 9. Reconciliación y recuperación

Al perder conexión:
- el controlador marca el nodo como `offline` tras un umbral configurable;
- no asume que sus instancias se detuvieron;
- congela nuevas asignaciones a ese nodo;
- marca tareas en ejecución como estado incierto, salvo que exista evidencia del agente;
- no vuelve a ejecutar acciones no idempotentes automáticamente.

Al reconectar:
1. autenticar y validar versión;
2. consultar inventario real de instancias y tareas;
3. comparar con el estado autoritativo;
4. detectar conflictos o datos obsoletos;
5. reconciliar con política explícita y eventos de auditoría;
6. reanudar nuevas asignaciones solo después de resolver conflictos.

La recuperación en otro nodo exige confirmar que el nodo anterior no puede seguir ejecutando la misma instancia, y que backup/restore es compatible. No asumir fencing automático sin mecanismo probado.

## 10. Fallo del controlador

La primera versión tendrá un controlador lógico principal, pero los agentes y las instancias deben poder continuar localmente mientras su política/lease lo permita. Para evitar decisiones divididas:
- el controlador emite asignaciones con lease y vencimiento;
- las operaciones de escritura requieren una autoridad válida;
- si no hay autoridad, el nodo no crea nuevas asignaciones ni inicia recuperación conflictiva;
- se define una copia de seguridad restaurable del estado central.

La elección de un controlador secundario y failover automático se pospone hasta decidir base de datos, quorum y mecanismo de exclusión mutua. No declarar alta disponibilidad en el MVP.

## 11. Seguridad

- Agente con usuario dedicado y privilegios mínimos.
- Lista permitida de operaciones; nunca ejecutar argumentos de shell arbitrarios recibidos por red.
- ADB solo accesible localmente desde el agente, mediante adaptador y permisos.
- Cortafuegos por defecto, administración solo por LAN/VPN autenticada.
- Revocación rápida de un nodo comprometido.
- Firmas/checksums para artefactos y límites de tamaño.
- Logs redactados, rotación y retención configurada.
- Actualizaciones firmadas o verificadas, rollback y versiones compatibles.
- Pruebas de abuso: repetición de mensajes, credencial revocada, payload grande, nodo desactualizado y red partida.

## 12. Pruebas de aceptación para el prototipo

1. Alta de dos nodos con capacidades diferentes.
2. Rechazo de un nodo no autorizado.
3. Heartbeat, desconexión y reconexión sin asumir falsamente que instancias desaparecieron.
4. Planificador elige solo un nodo compatible y con recursos suficientes.
5. Dos solicitudes duplicadas no crean dos instancias.
6. Disco/RAM insuficientes bloquean asignación con explicación.
7. Nodo drenado no recibe tareas nuevas.
8. Pérdida de controlador no detiene por sí sola la instancia existente.
9. Acción no idempotente con resultado incierto no se repite sola.
10. Revocación impide nuevas órdenes y queda auditada.
11. Manual de instalación, alta, mantenimiento, diagnóstico y retirada en español.

**No hay código ni pruebas ejecutadas por la creación de este documento.**
