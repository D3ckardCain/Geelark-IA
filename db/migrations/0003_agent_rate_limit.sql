-- Global, multiworker-safe request limiting for agent transport.
BEGIN;

ALTER TABLE geelark_control.nodes
    ADD COLUMN IF NOT EXISTS agent_rate_window_started_at timestamptz;

ALTER TABLE geelark_control.nodes
    ADD COLUMN IF NOT EXISTS agent_rate_window_count integer NOT NULL DEFAULT 0
        CHECK (agent_rate_window_count >= 0);

COMMENT ON COLUMN geelark_control.nodes.agent_rate_window_started_at IS
    'Inicio de la ventana de limitación de solicitudes del agente; actualizado atómicamente por PostgreSQL.';
COMMENT ON COLUMN geelark_control.nodes.agent_rate_window_count IS
    'Solicitudes consumidas en la ventana actual; se satura en max_requests + 1 para evitar desbordamiento.';

COMMIT;
