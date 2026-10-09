# Propuesta de DDL para persistencia del clúster

**Estado:** borrador técnico para revisión; NO es una migración aprobada ni se ha ejecutado contra PostgreSQL/Supabase.  
**Objetivo:** traducir los invariantes de `ESPECIFICACION_PERSISTENCIA_ASIGNACIONES.md` a restricciones verificables por PostgreSQL.  
**Coste:** PostgreSQL es software libre y puede ejecutarse localmente. Este borrador no requiere un servicio cloud.

## Decisiones y límites

- El controlador local de la Master es la autoridad del MVP. No se admite una segunda Master activa sin liderazgo y fencing probados.
- Las instancias conservan su fila cuando su estado es `unknown`; un timeout no libera automáticamente el propietario.
- UUID los genera la aplicación para mantener portabilidad; no se depende de extensiones específicas del proveedor.
- Las tablas viven en el esquema aislado `cluster_control`, no en `public`.
- El DDL usa PostgreSQL estándar (CHECK, FK, índices parciales, JSONB). Antes de producción deben fijarse versión, permisos y estrategia de migración.
- Las tablas no sustituyen autorización ni autenticación de agentes. El servicio de dominio debe aplicar esas comprobaciones.
- Si se decide alojar datos en Supabase, primero debe diseñarse RLS y revisar límites del plan; no se debe conectar un agente de nodo directamente con privilegios elevados. La opción local sigue siendo la referencia para el clúster de coste operativo cero.

## DDL candidato

El siguiente SQL está deliberadamente separado de las migraciones activas para impedir que se aplique por accidente.

```sql
BEGIN;

CREATE SCHEMA IF NOT EXISTS cluster_control;

CREATE TABLE cluster_control.nodes (
    node_id             uuid PRIMARY KEY,
    display_name        text NOT NULL CHECK (length(trim(display_name)) BETWEEN 1 AND 120),
    agent_version       text,
    protocol_version    text,
    admin_state         text NOT NULL DEFAULT 'pending'
        CHECK (admin_state IN ('pending','active','draining','maintenance','offline','quarantined','revoked')),
    health_state        text NOT NULL DEFAULT 'unknown'
        CHECK (health_state IN ('healthy','degraded','unhealthy','unknown')),
    last_seen_at        timestamptz,
    last_sequence       bigint NOT NULL DEFAULT -1 CHECK (last_sequence >= -1),
    capabilities        jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(capabilities) = 'object'),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX nodes_schedulable_idx
    ON cluster_control.nodes (admin_state, health_state, last_seen_at);

CREATE TABLE cluster_control.instances (
    instance_id         uuid PRIMARY KEY,
    display_name        text NOT NULL CHECK (length(trim(display_name)) BETWEEN 1 AND 160),
    desired_state       text NOT NULL DEFAULT 'stopped'
        CHECK (desired_state IN ('running','stopped')),
    observed_state      text NOT NULL DEFAULT 'stopped'
        CHECK (observed_state IN ('pending','reserved','starting','running','stopping','stopped','failed','unknown','reconciling')),
    owner_node_id       uuid REFERENCES cluster_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch    bigint NOT NULL DEFAULT 0 CHECK (assignment_epoch >= 0),
    lease_expires_at    timestamptz,
    engine_name         text,
    engine_version      text,
    android_api_level   integer CHECK (android_api_level IS NULL OR android_api_level BETWEEN 1 AND 100),
    android_abi         text,
    image_digest        text,
    resource_profile    jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(resource_profile) = 'object'),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (
      (owner_node_id IS NULL AND observed_state IN ('pending','stopped','failed'))
      OR owner_node_id IS NOT NULL
      OR observed_state IN ('pending','stopped','failed')
    ),
    CHECK (image_digest IS NULL OR image_digest ~ '^sha256:[0-9a-f]{64}$')
);

CREATE INDEX instances_owner_state_idx
    ON cluster_control.instances (owner_node_id, observed_state);
CREATE INDEX instances_state_updated_idx
    ON cluster_control.instances (observed_state, updated_at);

CREATE TABLE cluster_control.resource_reservations (
    reservation_id      uuid PRIMARY KEY,
    instance_id         uuid NOT NULL REFERENCES cluster_control.instances(instance_id) ON DELETE RESTRICT,
    node_id             uuid NOT NULL REFERENCES cluster_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch    bigint NOT NULL CHECK (assignment_epoch >= 1),
    memory_bytes        bigint NOT NULL CHECK (memory_bytes > 0),
    storage_bytes       bigint NOT NULL CHECK (storage_bytes > 0),
    cpu_units           numeric(10,3) NOT NULL CHECK (cpu_units > 0),
    reservation_state   text NOT NULL
        CHECK (reservation_state IN ('held','released','uncertain')),
    created_at          timestamptz NOT NULL DEFAULT now(),
    released_at         timestamptz,
    UNIQUE (instance_id, assignment_epoch),
    CHECK (
      (reservation_state = 'released' AND released_at IS NOT NULL)
      OR (reservation_state IN ('held','uncertain') AND released_at IS NULL)
    )
);

-- Defensa adicional en la base: una instancia no puede tener dos reservas
-- vigentes, incluso si por un error de aplicación se intenta usar otro epoch.
CREATE UNIQUE INDEX reservations_one_active_per_instance_idx
    ON cluster_control.resource_reservations (instance_id)
    WHERE reservation_state IN ('held','uncertain');

CREATE INDEX reservations_node_state_idx
    ON cluster_control.resource_reservations (node_id, reservation_state);
CREATE INDEX reservations_instance_epoch_idx
    ON cluster_control.resource_reservations (instance_id, assignment_epoch DESC);

CREATE TABLE cluster_control.operations (
    operation_id        uuid PRIMARY KEY,
    request_id          uuid NOT NULL,
    instance_id         uuid NOT NULL REFERENCES cluster_control.instances(instance_id) ON DELETE RESTRICT,
    node_id             uuid REFERENCES cluster_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch    bigint NOT NULL CHECK (assignment_epoch >= 0),
    operation_type      text NOT NULL CHECK (operation_type IN ('assign','start','stop','reconcile','backup','restore')),
    operation_state     text NOT NULL DEFAULT 'pending'
        CHECK (operation_state IN ('pending','accepted','running','succeeded','rejected','failed','unknown')),
    error_code          text,
    result_summary      jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(result_summary) = 'object'),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    finished_at         timestamptz,
    CHECK (
      (operation_state IN ('rejected','failed') AND error_code IS NOT NULL)
      OR operation_state NOT IN ('rejected','failed')
    )
);

CREATE INDEX operations_instance_created_idx
    ON cluster_control.operations (instance_id, created_at DESC);
CREATE INDEX operations_node_state_idx
    ON cluster_control.operations (node_id, operation_state, created_at);

CREATE TABLE cluster_control.idempotency_records (
    idempotency_id      uuid PRIMARY KEY,
    scope               text NOT NULL CHECK (length(trim(scope)) BETWEEN 1 AND 160),
    idempotency_key     text NOT NULL CHECK (length(idempotency_key) BETWEEN 16 AND 200),
    payload_sha256      char(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    operation_id        uuid REFERENCES cluster_control.operations(operation_id) ON DELETE RESTRICT,
    response_summary    jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(response_summary) = 'object'),
    created_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz,
    UNIQUE (scope, idempotency_key)
);

CREATE INDEX idempotency_expiry_idx
    ON cluster_control.idempotency_records (expires_at)
    WHERE expires_at IS NOT NULL;

CREATE TABLE cluster_control.assignment_events (
    event_id            uuid PRIMARY KEY,
    instance_id         uuid NOT NULL REFERENCES cluster_control.instances(instance_id) ON DELETE RESTRICT,
    assignment_epoch    bigint NOT NULL CHECK (assignment_epoch >= 0),
    node_id             uuid REFERENCES cluster_control.nodes(node_id) ON DELETE RESTRICT,
    previous_state      text,
    new_state           text NOT NULL
        CHECK (new_state IN ('pending','reserved','starting','running','stopping','stopped','failed','unknown','reconciling')),
    actor_type          text NOT NULL CHECK (actor_type IN ('controller','node_agent','operator','recovery')),
    actor_id            text,
    reason_code         text,
    request_id          uuid,
    operation_id        uuid REFERENCES cluster_control.operations(operation_id) ON DELETE RESTRICT,
    created_at          timestamptz NOT NULL DEFAULT now(),
    details             jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(details) = 'object')
);

CREATE INDEX assignment_events_instance_time_idx
    ON cluster_control.assignment_events (instance_id, created_at DESC);
CREATE INDEX assignment_events_node_time_idx
    ON cluster_control.assignment_events (node_id, created_at DESC);

CREATE TABLE cluster_control.outbox (
    event_id            uuid PRIMARY KEY,
    operation_id        uuid NOT NULL REFERENCES cluster_control.operations(operation_id) ON DELETE RESTRICT,
    instance_id         uuid NOT NULL REFERENCES cluster_control.instances(instance_id) ON DELETE RESTRICT,
    assignment_epoch    bigint NOT NULL CHECK (assignment_epoch >= 1),
    event_type          text NOT NULL CHECK (event_type IN ('assignment.requested','instance.start','instance.stop','instance.reconcile')),
    payload             jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    created_at          timestamptz NOT NULL DEFAULT now(),
    available_at        timestamptz NOT NULL DEFAULT now(),
    attempt_count       integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    claimed_at          timestamptz,
    claimed_by          text,
    delivered_at        timestamptz,
    last_error_code     text,
    UNIQUE (operation_id, event_type)
);

CREATE INDEX outbox_pending_idx
    ON cluster_control.outbox (available_at, created_at)
    WHERE delivered_at IS NULL;

COMMIT;
```

## Obligaciones de la capa transaccional

El DDL no puede expresar por sí solo todos los invariantes. El servicio de dominio debe realizar, dentro de transacciones cortas:

1. Insertar la clave idempotente y comparar `payload_sha256` si hay conflicto; misma clave y distinto hash significa `IDEMPOTENCY_CONFLICT`.
2. Bloquear primero la fila de instancia (`SELECT ... FOR UPDATE`) y después las filas de capacidad de los nodos en un orden determinista para reducir deadlocks.
3. Verificar que el nodo está activo, sano, compatible y con capacidad recalculada; la telemetría es una observación, no una reserva.
4. Incrementar `assignment_epoch` y persistir propietario, reserva, operación, evento de auditoría y outbox en una única transacción.
5. El dispatcher reclama eventos con `FOR UPDATE SKIP LOCKED`, pero la entrega puede repetirse; el agente debe deduplicar y comprobar epoch/fencing.
6. Un resultado del agente solo modifica estado si coinciden identidad autenticada, propietario actual, operación y epoch.
7. Un lease vencido NO libera propiedad. Se entra en reconciliación y se conserva `unknown` cuando no hay evidencia suficiente.
8. No borrar ni purgar claves idempotentes mientras puedan llegar reintentos legítimos. Definir retención con base en el horizonte máximo de reintentos.

## Revisión técnica pendiente

Antes de convertir esto en migración real:

- Revisar la regla de propietario/estado: acordar exactamente qué estados permiten `owner_node_id IS NULL` y cuáles lo exigen.
- Definir política de retención de eventos y registros idempotentes.
- Definir autenticación, privilegios SQL mínimos y auditoría de cambios.
- Probar deadlocks, dos asignaciones concurrentes, caídas antes/después del envío, reinicio y restauración.
- Ejecutar el SQL en una base PostgreSQL desechable de la misma versión objetivo y añadir pruebas automatizadas. No ejecutar directamente en producción.
- Añadir la migración al directorio oficial del proyecto solo tras decidir si la base autoritativa del clúster será PostgreSQL local o un servicio remoto.

## Matriz mínima de pruebas

| Caso | Resultado esperado |
|---|---|
| Dos transacciones asignan la misma instancia a nodos diferentes | Solo una obtiene el epoch y propietario |
| Reintento con misma clave y mismo hash | Se devuelve la operación registrada |
| Misma clave con hash diferente | Conflicto, sin mutación de la asignación |
| Resultado de un nodo con epoch antiguo | Rechazado; no libera reserva ni cambia estado |
| Lease vencido y nodo no localizable | Propietario conservado; estado `unknown`/reconciliación |
| Caída después del commit y antes del envío | El dispatcher vuelve a entregar el outbox |
| Caída después del envío y antes de marcar entregado | Reintento deduplicado por el agente |
| Nodo pierde capacidad entre selección y reserva | Transacción aborta o selecciona otro nodo sin sobreasignar |
| Restaurar backup | Se preservan epochs, operaciones, idempotencia y auditoría |
| Logs de error | Sin credenciales, tokens ni datos privados de perfiles |

## Estado honesto

Este archivo es una propuesta de esquema, no código ejecutado. No afirma que exista todavía persistencia funcional, protección contra doble asignación ni recuperación implementada.
