-- Geelark-IA cluster control plane: initial PostgreSQL schema.
-- PostgreSQL 15+; no extensions required. Apply once using a privileged migration role.
-- The application role should receive only the minimum required privileges separately.
BEGIN;

CREATE SCHEMA IF NOT EXISTS geelark_control;

CREATE TABLE geelark_control.schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now(),
    checksum_sha256 char(64) NOT NULL
        CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE geelark_control.nodes (
    node_id uuid PRIMARY KEY,
    display_name varchar(128) NOT NULL CHECK (length(trim(display_name)) > 0),
    agent_version varchar(64),
    protocol_version varchar(32),
    admin_state text NOT NULL DEFAULT 'pending'
        CHECK (admin_state IN ('pending', 'active', 'draining', 'maintenance', 'quarantined', 'revoked')),
    health_state text NOT NULL DEFAULT 'unknown'
        CHECK (health_state IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_seen_at timestamptz,
    last_sequence bigint NOT NULL DEFAULT 0 CHECK (last_sequence >= 0),
    capabilities jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(capabilities) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz
);

CREATE TABLE geelark_control.instances (
    instance_id uuid PRIMARY KEY,
    desired_state text NOT NULL DEFAULT 'stopped'
        CHECK (desired_state IN ('running', 'stopped')),
    observed_state text NOT NULL DEFAULT 'unknown'
        CHECK (observed_state IN ('pending', 'reserved', 'starting', 'running', 'stopping', 'stopped', 'failed', 'unknown', 'reconciling')),
    owner_node_id uuid REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL DEFAULT 0 CHECK (assignment_epoch >= 0),
    lease_expires_at timestamptz,
    engine_name varchar(128),
    engine_version varchar(64),
    image_digest varchar(128),
    resource_profile jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(resource_profile) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (owner_node_id IS NOT NULL OR lease_expires_at IS NULL)
);

CREATE INDEX instances_owner_state_idx
    ON geelark_control.instances(owner_node_id, observed_state);
CREATE INDEX instances_lease_expiry_idx
    ON geelark_control.instances(lease_expires_at)
    WHERE owner_node_id IS NOT NULL;

CREATE TABLE geelark_control.operations (
    operation_id uuid PRIMARY KEY,
    request_id uuid NOT NULL,
    instance_id uuid NOT NULL REFERENCES geelark_control.instances(instance_id) ON DELETE RESTRICT,
    node_id uuid REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL CHECK (assignment_epoch >= 1),
    operation_type text NOT NULL
        CHECK (operation_type IN ('assign', 'start', 'stop', 'release', 'reconcile', 'backup', 'restore')),
    status text NOT NULL DEFAULT 'accepted'
        CHECK (status IN ('accepted', 'running', 'succeeded', 'rejected', 'failed', 'unknown', 'cancelled')),
    error_code varchar(64),
    result_summary jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(result_summary) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE INDEX operations_instance_epoch_idx
    ON geelark_control.operations(instance_id, assignment_epoch, created_at DESC);
CREATE INDEX operations_status_created_idx
    ON geelark_control.operations(status, created_at);

CREATE TABLE geelark_control.resource_reservations (
    reservation_id uuid PRIMARY KEY,
    instance_id uuid NOT NULL REFERENCES geelark_control.instances(instance_id) ON DELETE RESTRICT,
    node_id uuid NOT NULL REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL CHECK (assignment_epoch >= 1),
    cpu_units numeric(10,3) NOT NULL CHECK (cpu_units > 0),
    memory_bytes bigint NOT NULL CHECK (memory_bytes > 0),
    storage_bytes bigint NOT NULL CHECK (storage_bytes > 0),
    status text NOT NULL CHECK (status IN ('held', 'uncertain', 'released')),
    created_at timestamptz NOT NULL DEFAULT now(),
    released_at timestamptz,
    CHECK ((status = 'released' AND released_at IS NOT NULL) OR
           (status <> 'released' AND released_at IS NULL))
);

-- Unknown/uncertain ownership remains a blocker; expiry alone never frees capacity.
CREATE UNIQUE INDEX one_blocking_reservation_per_instance
    ON geelark_control.resource_reservations(instance_id)
    WHERE status IN ('held', 'uncertain');
CREATE INDEX reservations_node_status_idx
    ON geelark_control.resource_reservations(node_id, status);

CREATE TABLE geelark_control.idempotency_records (
    scope varchar(128) NOT NULL CHECK (length(trim(scope)) > 0),
    idempotency_key varchar(200) NOT NULL CHECK (length(idempotency_key) >= 16),
    payload_sha256 char(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    operation_id uuid REFERENCES geelark_control.operations(operation_id) ON DELETE RESTRICT,
    response_snapshot jsonb CHECK (response_snapshot IS NULL OR jsonb_typeof(response_snapshot) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    PRIMARY KEY (scope, idempotency_key)
);

CREATE INDEX idempotency_expiry_idx
    ON geelark_control.idempotency_records(expires_at)
    WHERE expires_at IS NOT NULL;

CREATE TABLE geelark_control.assignment_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instance_id uuid NOT NULL REFERENCES geelark_control.instances(instance_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL CHECK (assignment_epoch >= 0),
    previous_node_id uuid REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    new_node_id uuid REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    previous_state text,
    new_state text NOT NULL,
    actor_type text NOT NULL CHECK (actor_type IN ('controller', 'agent', 'operator', 'recovery')),
    actor_id text,
    request_id uuid,
    operation_id uuid REFERENCES geelark_control.operations(operation_id) ON DELETE RESTRICT,
    reason text,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX assignment_events_instance_epoch_idx
    ON geelark_control.assignment_events(instance_id, assignment_epoch, occurred_at);

CREATE TABLE geelark_control.outbox_events (
    event_id uuid PRIMARY KEY,
    deduplication_key varchar(256) NOT NULL UNIQUE,
    instance_id uuid NOT NULL REFERENCES geelark_control.instances(instance_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL CHECK (assignment_epoch >= 1),
    operation_id uuid NOT NULL REFERENCES geelark_control.operations(operation_id) ON DELETE RESTRICT,
    event_type text NOT NULL
        CHECK (event_type IN ('assignment.requested', 'instance.start', 'instance.stop', 'assignment.release', 'instance.reconcile')),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'inflight', 'delivered', 'dead')),
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    available_at timestamptz NOT NULL DEFAULT now(),
    claimed_by uuid,
    claim_until timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    delivered_at timestamptz,
    last_error_code varchar(64),
    CHECK ((status = 'inflight' AND claimed_by IS NOT NULL AND claim_until IS NOT NULL) OR
           (status <> 'inflight' AND claimed_by IS NULL AND claim_until IS NULL)),
    CHECK ((status = 'delivered' AND delivered_at IS NOT NULL) OR
           (status <> 'delivered' AND delivered_at IS NULL))
);

CREATE INDEX outbox_pending_dispatch_idx
    ON geelark_control.outbox_events(available_at, created_at)
    WHERE status IN ('pending', 'inflight');
CREATE INDEX outbox_instance_epoch_idx
    ON geelark_control.outbox_events(instance_id, assignment_epoch);

COMMENT ON TABLE geelark_control.instances IS
    'Autoridad persistente de asignación. Unknown/reconciling bloquea la reasignación.';
COMMENT ON TABLE geelark_control.resource_reservations IS
    'Reservas de recursos; held/uncertain bloquean capacidad hasta liberación transaccional explícita.';
COMMENT ON TABLE geelark_control.idempotency_records IS
    'La capa de dominio compara payload_sha256 antes de devolver la respuesta original o producir conflicto.';
COMMENT ON TABLE geelark_control.outbox_events IS
    'Entrega al menos una vez; el agente debe deduplicar y validar assignment_epoch.';
COMMENT ON TABLE geelark_control.assignment_events IS
    'Historial de auditoría; las mutaciones de aplicación deben ser append-only por permisos y código.';

COMMIT;
