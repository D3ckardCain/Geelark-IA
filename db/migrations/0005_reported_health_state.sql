-- Separate Worker-reported health from the Master-derived health state.
-- Preserve the prior Worker declaration, then conservatively derive current health
-- from the Master clock and the last heartbeat timestamp.
BEGIN;

ALTER TABLE geelark_control.nodes
    ADD COLUMN reported_health_state text NOT NULL DEFAULT 'unknown'
        CHECK (reported_health_state IN ('healthy', 'degraded', 'unhealthy', 'unknown'));

UPDATE geelark_control.nodes
   SET reported_health_state = CASE
           WHEN health_state IN ('healthy', 'degraded', 'unhealthy', 'unknown')
               THEN health_state
           ELSE 'unknown'
       END,
       health_state = CASE
           WHEN last_seen_at IS NULL OR last_seen_at <= now() - interval '90 seconds'
               THEN 'offline'
           WHEN health_state IN ('degraded', 'unhealthy')
               THEN 'degraded'
           WHEN health_state = 'healthy'
               THEN 'healthy'
           ELSE 'unknown'
       END;

COMMENT ON COLUMN geelark_control.nodes.reported_health_state IS
    'Declaración de salud enviada por el Worker; no es autoritativa por sí sola.';
COMMENT ON COLUMN geelark_control.nodes.health_state IS
    'Estado derivado conservador por el Master a partir del reporte y la frescura del heartbeat.';

COMMIT;
