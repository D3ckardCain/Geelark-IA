-- Bandeja durable de asignaciones para entrega HTTPS saliente al agente.
-- No reutiliza outbox_events: su consumo es independiente y no ejecuta comandos.
BEGIN;

CREATE TABLE IF NOT EXISTS geelark_control.agent_tasks (
    task_id uuid PRIMARY KEY,
    operation_id uuid NOT NULL UNIQUE
        REFERENCES geelark_control.operations(operation_id) ON DELETE RESTRICT,
    node_id uuid NOT NULL
        REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    instance_id uuid NOT NULL
        REFERENCES geelark_control.instances(instance_id) ON DELETE RESTRICT,
    assignment_epoch bigint NOT NULL CHECK (assignment_epoch >= 1),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    status text NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'delivered', 'accepted', 'running',
                          'succeeded', 'rejected', 'failed', 'unknown', 'cancelled')),
    delivery_attempts integer NOT NULL DEFAULT 0 CHECK (delivery_attempts >= 0),
    delivery_lease_until timestamptz,
    delivered_at timestamptz,
    accepted_at timestamptz,
    completed_at timestamptz,
    result_summary jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(result_summary) = 'object'),
    last_error_code varchar(64)
        CHECK (last_error_code IS NULL OR last_error_code ~ '^[A-Z0-9_]{1,64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (instance_id, assignment_epoch, operation_id),
    CHECK (
        (status IN ('queued', 'delivered') AND completed_at IS NULL)
        OR status NOT IN ('queued', 'delivered')
    )
);

CREATE INDEX IF NOT EXISTS agent_tasks_claim_idx
    ON geelark_control.agent_tasks(node_id, created_at, task_id)
    WHERE status IN ('queued', 'delivered');

CREATE INDEX IF NOT EXISTS agent_tasks_instance_epoch_idx
    ON geelark_control.agent_tasks(instance_id, assignment_epoch, status);

COMMENT ON TABLE geelark_control.agent_tasks IS
    'Bandeja durable para entrega saliente al agente; independiente del outbox interno y protegida por epoch/lease.';

COMMIT;
