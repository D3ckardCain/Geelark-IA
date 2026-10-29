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

-- Separar el dato reportado por el Worker de la salud derivada por el controlador.
ALTER TABLE geelark_control.nodes
    ADD COLUMN IF NOT EXISTS reported_health_state text NOT NULL DEFAULT 'unknown'
        CHECK (reported_health_state IN ('healthy', 'degraded', 'unhealthy', 'unknown'));

UPDATE geelark_control.nodes
   SET reported_health_state = health_state
 WHERE reported_health_state = 'unknown'
   AND health_state IN ('healthy', 'degraded', 'unhealthy', 'unknown');

ALTER TABLE geelark_control.nodes
    DROP CONSTRAINT IF EXISTS nodes_health_state_check;

UPDATE geelark_control.nodes
   SET health_state = 'degraded'
 WHERE health_state = 'unhealthy';

ALTER TABLE geelark_control.nodes
    ADD CONSTRAINT nodes_health_state_check
    CHECK (health_state IN ('healthy', 'degraded', 'unknown', 'offline'));

COMMENT ON COLUMN geelark_control.nodes.reported_health_state IS
    'Declaración del agente; no autoritativa y separada de health_state, que deriva el controlador.';

COMMIT;
