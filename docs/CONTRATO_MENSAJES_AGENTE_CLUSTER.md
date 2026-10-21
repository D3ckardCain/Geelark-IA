# Contrato de mensajes del agente de nodo — Geelark-IA

**Versión del contrato:** 0.2  
**Fecha:** 2026-10-09  
**Estado:** propuesta de esquema; aún no validada por código.  
**Relacionado:** `CONTRATO_API_CLUSTER.md`, `CONTRATO_AGENTE_NODO_PLANIFICADOR.md`, ADR-004.

## 1. Alcance

Define mensajes mínimos entre el controlador y los agentes de PC. No define un protocolo de ejecución de shell. Los agentes solo aceptan operaciones tipadas que estén en la lista permitida. Este contrato es independiente de la implementación concreta del runtime Android.

## 2. Convenciones comunes

- Codificación UTF-8; transporte HTTP(S) privado para la primera versión.
- Fechas UTC ISO-8601 con sufijo `Z`.
- Identificadores internos UUID.
- Campos desconocidos se rechazan en mensajes de control de escritura para evitar errores silenciosos.
- Tamaño máximo del cuerpo HTTP configurable; propuesta inicial 1 MiB para mensajes normales y canal separado para artefactos.
- Toda solicitud tiene `request_id`; las operaciones mutables tienen `operation_id` y `idempotency_key`.
- Autenticación por nodo; credenciales individuales y revocables. En red no confiable, cifrado obligatorio.
- Nunca incluir contraseñas, tokens de usuario, cookies, contenido privado de apps ni secretos de proxy en telemetría.
- Las cifras de recursos tienen unidad explícita y no se mezclan porcentajes con bytes.
- Un campo no medido se representa como `null` más estado de confianza, no como cero.

## 3. Sobre común de mensajes

```json
{
  "protocol_version": "0.2",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "sent_at": "2026-10-09T18:00:00Z"
}
```

Reglas:
- `protocol_version` debe pertenecer al rango compatible declarado por ambos extremos.
- `request_id` identifica una interacción y sirve para correlación; no sustituye la idempotencia.
- Los agentes rechazan timestamps absurdamente futuros y mensajes caducados según la política de reloj.
- No confiar en el reloj del mensaje como prueba de autoridad; epochs y estado durable controlan las asignaciones.

## 4. Registro de nodo

Solicitud de incorporación, enviada por un proceso autorizado y aprobada por el controlador:

```json
{
  "protocol_version": "0.2",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "sent_at": "2026-10-09T18:00:00Z",
  "node": {
    "node_id": "22222222-2222-4222-8222-222222222222",
    "display_name": "nodo-laboratorio-01",
    "agent_version": "0.1.0",
    "os": {"family": "linux", "architecture": "x86_64", "kernel": "unknown"},
    "capabilities": {
      "virtualization": ["kvm"],
      "android_engines": [],
      "android_abis": ["x86_64"],
      "gpu_acceleration": "unknown"
    }
  }
}
```

El ejemplo ilustra la forma del mensaje, no declara que un motor o una capacidad esté disponible. El ID se asigna una sola vez y no debe derivarse de MAC, número de serie o nombre del equipo.

## 5. Heartbeat y telemetría

```json
{
  "protocol_version": "0.2",
  "request_id": "33333333-3333-4333-8333-333333333333",
  "sent_at": "2026-10-09T18:00:30Z",
  "node_id": "22222222-2222-4222-8222-222222222222",
  "sequence": 42,
  "health": "healthy",
  "resources": {
    "cpu": {"logical_cores": 16, "utilization_percent": 21.5, "confidence": "observed"},
    "memory": {"total_bytes": 34359738368, "available_bytes": 21474836480, "confidence": "observed"},
    "volumes": [{"volume_id": "data", "free_bytes": 500000000000, "confidence": "observed"}]
  },
  "engines": [],
  "active_assignments": []
}
```

Validaciones:
- `sequence` aumenta por agente; un valor menor o repetido se registra como duplicado/obsoleto.
- Los porcentajes deben estar en [0,100]; bytes son enteros no negativos.
- `available_bytes` no puede exceder `total_bytes`.
- El controlador calcula frescura según hora de recepción y política local; no confía exclusivamente en `sent_at`.
- Telemetría incompleta puede mantener el nodo visible, pero no habilita una asignación que requiera el recurso desconocido.
- Los heartbeats no autorizan al agente a crear o cambiar por sí mismo un propietario.

## 6. Solicitud de asignación

```json
{
  "protocol_version": "0.2",
  "request_id": "44444444-4444-4444-8444-444444444444",
  "sent_at": "2026-10-09T18:01:00Z",
  "operation_id": "55555555-5555-4555-8555-555555555555",
  "idempotency_key": "random-per-logical-operation",
  "instance_id": "66666666-6666-4666-8666-666666666666",
  "assignment_epoch": 7,
  "lease_expires_at": "2026-10-09T18:02:00Z",
  "desired_state": "running",
  "engine": {"name": "engine-id", "version": "required-version"},
  "android": {"api_level": 0, "abi": "x86_64", "image_digest": "sha256:..."},
  "resource_reservation": {"memory_bytes": 4294967296, "storage_bytes": 16000000000, "cpu_units": 2}
}
```

Reglas:
- El controlador crea y persiste la asignación antes de enviar la orden.
- El agente verifica que su identidad coincida con el destinatario, que la carga sea compatible y que los recursos sigan disponibles.
- El agente rechaza epochs menores al último epoch durable que conoce para esa instancia.
- La clave de idempotencia debe asociarse a una huella del payload; reutilizarla con payload distinto devuelve conflicto.
- El ejemplo de versión/API/recursos es ilustrativo y no representa valores mínimos aprobados.
- Un lease vencido no autoriza por sí solo a otro nodo a iniciar la instancia. Primero se necesita fencing y reconciliación verificables.

## 7. Confirmación y resultado

```json
{
  "protocol_version": "0.2",
  "request_id": "77777777-7777-4777-8777-777777777777",
  "sent_at": "2026-10-09T18:01:03Z",
  "operation_id": "55555555-5555-4555-8555-555555555555",
  "node_id": "22222222-2222-4222-8222-222222222222",
  "instance_id": "66666666-6666-4666-8666-666666666666",
  "assignment_epoch": 7,
  "status": "accepted",
  "observed_state": "starting",
  "error": null
}
```

Estados de resultado permitidos:
- `accepted`: validado y aceptado, todavía no significa Android listo.
- `rejected`: rechazado antes de iniciar; incluye código y razones tipadas.
- `running`: motor confirma estado operativo conforme a una comprobación definida.
- `stopped`: parada comprobada por el adaptador del motor.
- `failed`: error conocido.
- `unknown`: no se puede verificar el resultado.

Los timeouts del transporte se traducen a resultado incierto hasta reconciliar, no a fallo confirmado.

## 8. Códigos de error iniciales

- `AUTHENTICATION_FAILED`
- `NODE_REVOKED`
- `PROTOCOL_VERSION_UNSUPPORTED`
- `SCHEMA_VALIDATION_FAILED`
- `MESSAGE_EXPIRED`
- `STALE_SEQUENCE`
- `STALE_ASSIGNMENT_EPOCH`
- `IDEMPOTENCY_CONFLICT`
- `INSTANCE_ALREADY_ASSIGNED`
- `NODE_NOT_ELIGIBLE`
- `INSUFFICIENT_MEMORY`
- `INSUFFICIENT_STORAGE`
- `ENGINE_UNAVAILABLE`
- `ANDROID_IMAGE_INCOMPATIBLE`
- `CAPACITY_CHANGED`
- `LEASE_STATE_UNCERTAIN`
- `OPERATION_RESULT_UNKNOWN`
- `RATE_LIMITED`
- `INTERNAL_ERROR`

Los mensajes públicos no deben exponer stack traces, rutas sensibles, secretos ni datos del sistema innecesarios.

## 9. Máquina de estados

Transiciones permitidas de alto nivel:
- `pending -> reserved -> starting -> running`
- `starting -> failed|unknown`
- `running -> stopping -> stopped`
- `running -> unknown` ante pérdida de observabilidad
- `unknown -> reconciling -> running|stopped|failed`
- `unknown -> unknown` mientras no haya evidencia suficiente

No permitir `unknown -> starting` en otro nodo sin resolver propiedad anterior. Las transiciones deben comprobarse en servidor; la UI no puede imponer estados arbitrarios.

## 10. Pruebas de conformidad del protocolo

Pruebas positivas:
1. Mensaje válido de nodo compatible pasa validación.
2. Heartbeat válido incrementa secuencia y actualiza última observación.
3. Repetición de una operación con la misma clave y payload devuelve el resultado original.
4. El agente acepta una asignación con epoch actual y capacidad suficiente.
5. El resultado de operación se correlaciona por `operation_id`.

Pruebas negativas:
1. Campos desconocidos en una escritura se rechazan.
2. UUID mal formado, fecha inválida, byte negativo o porcentaje fuera de rango se rechaza.
3. Protocolo incompatible o mensaje caducado se rechaza.
4. Clave de idempotencia repetida con payload distinto devuelve conflicto.
5. Epoch antiguo, nodo revocado o destinatario incorrecto se rechaza.
6. Recursos insuficientes o imagen/ABI incompatibles se rechazan.
7. Orden fuera de lista permitida y solicitud de shell arbitrario se rechazan.
8. Timeout durante start deja estado `unknown` hasta reconciliar.
9. Heartbeat duplicado/antiguo no revierte el estado del nodo.
10. Dos asignaciones concurrentes para la misma instancia no producen dos propietarios.

## 11. Requisitos para pasar a implementación

- Traducir este contrato a modelos Pydantic estrictos y OpenAPI.
- Añadir pruebas automatizadas de serialización, validación y transición.
- Guardar fixtures JSON sintéticos versionados en el repositorio.
- Ejecutar pruebas de concurrencia contra la persistencia elegida.
- Probar reinicio del controlador y pérdida de red.
- Versionar cambios incompatibles y mantener pruebas de contrato.
- Documentar configuración, diagnóstico y recuperación en el manual del agente.

**Estado real:** ejemplos y reglas documentales; no hay agente implementado ni validación automatizada ejecutada.
