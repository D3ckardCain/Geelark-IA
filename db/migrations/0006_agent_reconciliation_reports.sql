-- Evidencia durable de reconciliación del inventario del agente.
-- No cambia estados de tareas/instancias: las decisiones son auditables y conservadoras.
BEGIN;

CREATE TABLE IF NOT EXISTS geelark_control.agent_reconciliation_reports (
    report_id uuid PRIMARY KEY,
    node_id uuid NOT NULL REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    inventory_sha256 char(64) NOT NULL CHECK (inventory_sha256 ~ '^[0-9a-f]{64}$'),
    inventory_count integer NOT NULL CHECK (inventory_count BETWEEN 0 AND 100),
    decisions jsonb NOT NULL CHECK (jsonb_typeof(decisions) = 'array'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS agent_reconciliation_reports_node_created_idx
    ON geelark_control.agent_reconciliation_reports(node_id, created_at DESC);

COMMENT ON TABLE geelark_control.agent_reconciliation_reports IS
    'Auditoría durable de comparación de inventario/epochs/resultados; no aplica mutaciones automáticas a tareas ni instancias.';

COMMIT;
