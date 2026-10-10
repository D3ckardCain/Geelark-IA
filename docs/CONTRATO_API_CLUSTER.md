# Contrato de API del plano de control distribuido

**Versión:** 0.1  
**Fecha:** 2026-10-09  
**Estado:** especificación preliminar; no implementada ni validada con pruebas.  
**Objetivo:** definir una API local y privada para administrar clúster, nodos, instancias Android y tareas sin acoplar el dominio a Proxmox VE o a un motor Android concreto.

## 1. Reglas de diseño

- Prefijo inicial: `/api/v1`.
- OpenAPI será la fuente publicada del contrato una vez que exista implementación FastAPI.
- IDs internos UUID; no reutilizar nombres de contenedor, IDs de VM, seriales ADB o nombres de host como claves primarias.
- Respuestas con esquema versionado, fechas UTC ISO-8601 y errores tipados.
- Operaciones de escritura requieren autenticación y autorización; operaciones destructivas requieren confirmación y, cuando proceda, respaldo previo.
- La API del plano de control no se expone directamente a Internet.
- Los agentes de nodo usan credenciales individuales y permisos limitados; no comparten la sesión administrativa de la UI.
- No enviar secretos en respuestas, logs, trazas o mensajes de error.
- Solicitudes que puedan repetirse deben aceptar una clave idempotente.
- Los endpoints descritos son un contrato de diseño, no endpoints que ya existan.

## 2. Convenciones comunes

### Identificadores
- `cluster_id`, `node_id`, `instance_id`, `profile_id`, `task_id`: UUID.
- `request_id`: UUID por solicitud para diagnóstico y auditoría.
- `idempotency_key`: valor aleatorio único para una operación lógica.

### Respuesta de error
Esquema recomendado:
```json
{
  "error": {
    "code": "NODE_NOT_ELIGIBLE",
    "message": "El nodo no cumple los requisitos de esta tarea.",
    "request_id": "uuid",
    "retryable": false,
    "details": {
      "reasons": ["INSUFFICIENT_RAM", "ENGINE_UNAVAILABLE"]
    }
  }
}
```
Los detalles nunca incluyen contraseñas, tokens, claves privadas ni payloads secretos.

Códigos iniciales: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `PERMISSION_DENIED`, `RESOURCE_NOT_FOUND`, `CONFLICT`, `IDEMPOTENCY_CONFLICT`, `NODE_OFFLINE`, `NODE_NOT_ELIGIBLE`, `INSUFFICIENT_RESOURCES`, `ENGINE_CAPABILITY_MISSING`, `OPERATION_UNCERTAIN`, `RATE_LIMITED`, `INTERNAL_ERROR`.

## 3. Plano administrativo: endpoints propuestos

| Método | Ruta | Propósito | Riesgo/condición |
|---|---|---|---|
| GET | `/api/v1/health` | Salud del servicio y versión | No revelar secretos ni datos internos sensibles |
| GET | `/api/v1/cluster` | Resumen de clúster | Requiere sesión autenticada |
| GET | `/api/v1/nodes` | Listar nodos y estado | Redactar identificadores sensibles |
| GET | `/api/v1/nodes/{node_id}` | Detalle/capacidades/último heartbeat | Permiso de lectura |
| POST | `/api/v1/nodes/enrollments` | Crear token de alta de un solo uso | Solo administrador; expiración corta |
| POST | `/api/v1/nodes/{node_id}/approve` | Aprobar nodo pendiente | Solo administrador |
| POST | `/api/v1/nodes/{node_id}/revoke` | Revocar credenciales | Confirmación explícita y auditoría |
| POST | `/api/v1/nodes/{node_id}/drain` | Impedir nuevas asignaciones | No parar cargas automáticamente |
| POST | `/api/v1/nodes/{node_id}/undrain` | Volver a admitir asignaciones | Verificar salud/capacidades |
| GET | `/api/v1/instances` | Listar instancias y su nodo propietario | Paginación obligatoria |
| POST | `/api/v1/instances` | Solicitar creación y asignación | Idempotencia; validar capacidad |
| GET | `/api/v1/instances/{instance_id}` | Consultar estado y capacidades | No mostrar secretos |
| POST | `/api/v1/instances/{instance_id}/start` | Iniciar instancia | Confirmar propiedad/lease |
| POST | `/api/v1/instances/{instance_id}/stop` | Detener instancia | Política de parada y confirmación |
| POST | `/api/v1/instances/{instance_id}/restart` | Reiniciar instancia | Idempotencia y auditoría |
| POST | `/api/v1/instances/{instance_id}/backup` | Solicitar respaldo | Validar espacio y compatibilidad |
| POST | `/api/v1/instances/{instance_id}/restore` | Restaurar respaldo | Evitar dos propietarios activos |
| POST | `/api/v1/tasks` | Encolar tarea tipada | Idempotency-Key obligatorio |
| GET | `/api/v1/tasks/{task_id}` | Consultar tarea | Estado incierto explícito |
| POST | `/api/v1/tasks/{task_id}/cancel` | Solicitar cancelación | Cancelación puede ser cooperativa |
| GET | `/api/v1/events` | Consultar eventos recientes | Paginación y permisos |
| GET | `/api/v1/events/stream` | SSE para cambios de estado | Solo red privada/autenticada; polling alternativo |
| GET | `/api/v1/audit` | Consultar auditoría | Solo roles autorizados |

Las rutas son candidatas. Antes de implementarlas, se revisarán los requisitos de cada módulo GeeLark y se evitará añadir endpoints sin necesidad funcional.

## 4. Protocolo de agente (interfaz privada)

El protocolo de agente puede compartir el host y el dominio de API, pero debe tener una autenticación y autorización separadas de la UI. Rutas candidatas:
- `POST /agent/v1/session`: validar identidad y establecer sesión corta.
- `POST /agent/v1/heartbeat`: informar salud, versión y estado resumido.
- `PUT /agent/v1/capabilities`: publicar inventario de capacidades versionado.
- `POST /agent/v1/tasks/claim`: reclamar de forma idempotente la siguiente asignación de la bandeja durable (solo nodo activo; devuelve una tarea o `task: null`).
- `POST /agent/v1/tasks/{task_id}/accept`: aceptar una asignación vigente.
- `POST /agent/v1/tasks/{task_id}/progress`: informar progreso y etapa.
- `POST /agent/v1/tasks/{task_id}/result`: publicar resultado tipado y redactado.
- `POST /agent/v1/reconcile`: intercambiar inventario real tras reconexión.

Si el agente no puede alcanzar el controlador, conservará un diario local mínimo y no aceptará tareas nuevas que dependan de una autoridad vigente. El controlador no interpretará la ausencia de heartbeat como prueba de que el nodo está apagado.

## 5. Modelos mínimos

### Nodo
```json
{
  "node_id": "uuid",
  "display_name": "nodo-lab-01",
  "state": "online",
  "agent_version": "0.1.0",
  "last_seen_at": "2026-10-09T22:00:00Z",
  "resources": {
    "cpu_load_percent": 12.4,
    "memory_total_bytes": 34359738368,
    "memory_available_bytes": 25769803776,
    "storage_available_bytes": 500000000000
  },
  "capabilities_version": 1
}
```

### Instancia
```json
{
  "instance_id": "uuid",
  "profile_id": "uuid",
  "owner_node_id": "uuid",
  "engine_id": "redroid",
  "engine_version": "unknown",
  "lifecycle_state": "stopped",
  "assignment_epoch": 3,
  "capabilities_status": "not_verified"
}
```

### Tarea
```json
{
  "task_id": "uuid",
  "idempotency_key": "opaque-unique-value",
  "kind": "instance.start",
  "state": "queued",
  "target_instance_id": "uuid",
  "assigned_node_id": null,
  "created_at": "2026-10-09T22:00:00Z",
  "attempt": 0,
  "result": null
}
```

Los ejemplos son ilustrativos. La implementación deberá usar modelos Pydantic estrictos, límites de tamaño y campos enumerados, no aceptar `kind` arbitrarios.

## 6. Asignación, lease y concurrencia

- Cada asignación incluye `assignment_epoch`, `lease_expires_at` y un identificador de propietario.
- Una nueva asignación incrementa el epoch y queda auditada.
- El nodo rechaza una orden si el epoch está obsoleto o la lease venció.
- La expiración de una lease no prueba que la instancia anterior se haya detenido; antes de recuperación se necesita comprobar fencing o una política de recuperación segura.
- Las operaciones que cambian estado usan transacciones y una clave idempotente.
- No iniciar la misma instancia en otro nodo solo porque el primero no responde.
- En caso de resultado incierto, exponer `OPERATION_UNCERTAIN` y requerir reconciliación.

La mecánica exacta de leases y exclusión mutua depende de la persistencia central que se seleccione y debe probarse frente a desconexiones y particiones de red.

## 7. Seguridad, límites y auditoría

- Autenticación por sesión de usuario para UI/API; identidad separada para agentes.
- Autorización por roles y recurso; principio de mínimo privilegio.
- TLS para comunicación entre nodos; certificados o credenciales rotables y revocables.
- Rate limits y límites de cuerpo, paginación y timeout.
- CORS restrictivo si se habilita UI web; no permitir orígenes arbitrarios.
- Protección CSRF cuando la autenticación use cookies.
- No aceptar rutas de archivo absolutas arbitrarias ni comandos shell desde API.
- Auditoría de actor, acción, recurso, resultado, fecha y request ID.
- Logs con redacción y rotación.
- Las respuestas no deben incluir claves, secretos, tokens de inscripción ni credenciales de proxy.

## 8. Offline y reconexión

La UI local puede consultar perfiles, configuración e historial cacheado cuando el controlador local esté disponible. Si un nodo pierde conexión, sus instancias pueden continuar según política local, pero la UI mostrará su estado como desconocido/obsoleto. No se debe presentar como estado confirmado un dato sin heartbeat reciente.

Tras reconectar, el flujo `reconcile` compara:
- instancias y estados reales;
- tareas en curso y resultados pendientes;
- versión del agente y del motor;
- epochs/leases y propietario registrado;
- checksums de artefactos cuando corresponda.

Los conflictos se registran y requieren una regla de reconciliación explícita; no se resuelven por “última escritura gana” para operaciones destructivas.

## 9. Pruebas contractuales requeridas

- Esquemas válidos e inválidos y compatibilidad de versiones.
- Roles y denegación de permisos.
- Repetición de solicitudes con clave idempotente.
- Dos solicitudes concurrentes para crear/iniciar una instancia.
- Nodo desconectado y reconectado con estado obsoleto.
- Lease vencida con nodo posiblemente activo.
- Payload excesivo, rate limiting y credencial revocada.
- No filtración de secretos en errores y logs.
- Paginación y orden estable de eventos.
- Contrato OpenAPI exportable y pruebas de conformidad del agente.

**No hay endpoints implementados ni pruebas ejecutadas. Este documento solo define el contrato de diseño.**
