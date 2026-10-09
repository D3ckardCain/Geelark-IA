-- PROTOTIPO NO PRODUCTIVO: ejecutar solo en una base desechable.
-- Aún no es una migración oficial del clúster.
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

-- Capacidad utilizable, ya descontadas las reservas de seguridad del sistema.
-- El agente actualiza esta instantánea; la asignación siempre la vuelve a validar.
CREATE TABLE cluster_control.node_capacity (
    node_id                 uuid PRIMARY KEY REFERENCES cluster_control.nodes(node_id) ON DELETE RESTRICT,
    memory_usable_bytes     bigint NOT NULL CHECK (memory_usable_bytes > 0),
    storage_usable_bytes    bigint NOT NULL CHECK (storage_usable_bytes > 0),
    cpu_usable_units        numeric(10,3) NOT NULL CHECK (cpu_usable_units > 0),
    observed_at             timestamptz NOT NULL,
    capacity_revision       bigint NOT NULL DEFAULT 1 CHECK (capacity_revision >= 1)
);


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
    payload_sha256      text NOT NULL CHECK (length(payload_sha256) = 64 AND payload_sha256 ~ '^[0-9a-f]{64}$'),
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
