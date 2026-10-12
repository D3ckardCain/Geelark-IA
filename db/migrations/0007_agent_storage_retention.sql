-- Retención conservadora para nonces, snapshots idempotentes e informes de reconciliación.
-- La función solo borra al confirmar exportación explícita; no elimina evidencia incierta/conflictiva.
BEGIN;

-- Backfill de snapshots existentes. Scopes desconocidos quedan sin vencimiento y no se podan.
UPDATE geelark_control.idempotency_records
   SET expires_at = created_at + CASE split_part(scope, ':', 3)
       WHEN 'heartbeat' THEN interval '1 day'
       WHEN 'capabilities' THEN interval '1 day'
       WHEN 'modules_report' THEN interval '1 day'
       WHEN 'status_read' THEN interval '1 day'
       WHEN 'task_fetch' THEN interval '90 days'
       WHEN 'task_accept' THEN interval '90 days'
       WHEN 'task_progress' THEN interval '90 days'
       WHEN 'task_result' THEN interval '90 days'
       WHEN 'reconcile' THEN interval '90 days'
       WHEN 'reconcile_inventory' THEN interval '90 days'
       ELSE NULL
   END
 WHERE expires_at IS NULL
   AND split_part(scope, ':', 1) = 'agent'
   AND split_part(scope, ':', 3) IN (
       'heartbeat', 'capabilities', 'modules_report', 'status_read',
       'task_fetch', 'task_accept', 'task_progress', 'task_result',
       'reconcile', 'reconcile_inventory'
   );

CREATE INDEX IF NOT EXISTS agent_reconciliation_reports_created_idx
    ON geelark_control.agent_reconciliation_reports(created_at, report_id);

CREATE OR REPLACE FUNCTION geelark_control.prune_agent_storage(
    p_confirmed_export boolean DEFAULT false
)
RETURNS TABLE (
    eligible_nonces bigint,
    deleted_nonces bigint,
    eligible_idempotency_records bigint,
    deleted_idempotency_records bigint,
    eligible_reconciliation_reports bigint,
    deleted_reconciliation_reports bigint
)
LANGUAGE plpgsql
AS $function$
DECLARE
    v_eligible_nonces bigint := 0;
    v_deleted_nonces bigint := 0;
    v_eligible_idempotency bigint := 0;
    v_deleted_idempotency bigint := 0;
    v_eligible_reports bigint := 0;
    v_deleted_reports bigint := 0;
BEGIN
    SELECT count(*) INTO v_eligible_nonces
      FROM geelark_control.agent_request_nonces
     WHERE expires_at <= now() - interval '1 hour';

    SELECT count(*) INTO v_eligible_idempotency
      FROM geelark_control.idempotency_records
     WHERE expires_at IS NOT NULL AND expires_at <= now();

    WITH safe_reports AS (
        SELECT r.report_id, r.node_id, r.created_at,
               row_number() OVER (
                   PARTITION BY r.node_id
                   ORDER BY r.created_at DESC, r.report_id DESC
               ) AS safe_rank
          FROM geelark_control.agent_reconciliation_reports AS r
         WHERE NOT EXISTS (
             SELECT 1
               FROM jsonb_array_elements(r.decisions) AS decision_item(value)
              WHERE coalesce(decision_item.value ->> 'decision', '')
                    NOT IN ('ALREADY_CONFIRMED', 'CONTINUE_SAME_EPOCH')
         )
    ),
    eligible_reports AS (
        SELECT report_id
          FROM safe_reports
         WHERE created_at <= now() - interval '90 days'
            OR safe_rank > 10000
    )
    SELECT count(*) INTO v_eligible_reports FROM eligible_reports;

    -- Preview por defecto: ninguna fila se borra sin confirmación explícita de exportación.
    IF p_confirmed_export THEN
        DELETE FROM geelark_control.agent_request_nonces
         WHERE expires_at <= now() - interval '1 hour';
        GET DIAGNOSTICS v_deleted_nonces = ROW_COUNT;

        DELETE FROM geelark_control.idempotency_records
         WHERE expires_at IS NOT NULL AND expires_at <= now();
        GET DIAGNOSTICS v_deleted_idempotency = ROW_COUNT;

        WITH safe_reports AS (
            SELECT r.report_id, r.node_id, r.created_at,
                   row_number() OVER (
                       PARTITION BY r.node_id
                       ORDER BY r.created_at DESC, r.report_id DESC
                   ) AS safe_rank
              FROM geelark_control.agent_reconciliation_reports AS r
             WHERE NOT EXISTS (
                 SELECT 1
                   FROM jsonb_array_elements(r.decisions) AS decision_item(value)
                  WHERE coalesce(decision_item.value ->> 'decision', '')
                        NOT IN ('ALREADY_CONFIRMED', 'CONTINUE_SAME_EPOCH')
             )
        ),
        eligible_reports AS (
            SELECT report_id
              FROM safe_reports
             WHERE created_at <= now() - interval '90 days'
                OR safe_rank > 10000
        )
        DELETE FROM geelark_control.agent_reconciliation_reports AS report
         USING eligible_reports AS eligible
         WHERE report.report_id = eligible.report_id;
        GET DIAGNOSTICS v_deleted_reports = ROW_COUNT;
    END IF;

    RETURN QUERY SELECT
        v_eligible_nonces, v_deleted_nonces,
        v_eligible_idempotency, v_deleted_idempotency,
        v_eligible_reports, v_deleted_reports;
END
$function$;

-- No exponer la rutina de mantenimiento al rol lector ni a PUBLIC.
REVOKE ALL ON FUNCTION geelark_control.prune_agent_storage(boolean) FROM PUBLIC;
DO $revoke_reader$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'geelark_master_reader') THEN
        EXECUTE 'REVOKE ALL ON FUNCTION geelark_control.prune_agent_storage(boolean) FROM geelark_master_reader';
    END IF;
END
$revoke_reader$;

COMMENT ON FUNCTION geelark_control.prune_agent_storage(boolean) IS
    'Preview por defecto. Con true borra nonces expirados con 1h de gracia, snapshots idempotentes vencidos y solo informes seguros (90d/10k por nodo); exige exportación previa. Nunca poda unknown/conflictos/decisiones no reconocidas.';

COMMIT;
