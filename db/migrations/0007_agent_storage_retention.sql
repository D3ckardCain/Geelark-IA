-- Retención conservadora para nonces, snapshots idempotentes e informes de reconciliación.
-- Preview por defecto. La poda requiere confirmación explícita de exportación; evidencia
-- unknown/conflictiva solo se elimina con una segunda confirmación y antigüedad >365 días.
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

CREATE TABLE IF NOT EXISTS geelark_control.agent_storage_maintenance_runs (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    requested_by name NOT NULL DEFAULT current_user,
    started_at timestamptz NOT NULL DEFAULT now(),
    confirmed_export boolean NOT NULL,
    confirmed_review_evidence_export boolean NOT NULL,
    eligible_nonces bigint NOT NULL,
    deleted_nonces bigint NOT NULL,
    eligible_idempotency_records bigint NOT NULL,
    deleted_idempotency_records bigint NOT NULL,
    eligible_safe_reports bigint NOT NULL,
    deleted_safe_reports bigint NOT NULL,
    eligible_review_reports bigint NOT NULL,
    deleted_review_reports bigint NOT NULL
);

CREATE INDEX IF NOT EXISTS agent_storage_maintenance_runs_started_idx
    ON geelark_control.agent_storage_maintenance_runs(started_at DESC);

CREATE OR REPLACE FUNCTION geelark_control.prune_agent_storage(
    p_confirmed_export boolean DEFAULT false,
    p_confirmed_review_evidence_export boolean DEFAULT false
)
RETURNS TABLE (
    eligible_nonces bigint,
    deleted_nonces bigint,
    eligible_idempotency_records bigint,
    deleted_idempotency_records bigint,
    eligible_safe_reports bigint,
    deleted_safe_reports bigint,
    eligible_review_reports bigint,
    deleted_review_reports bigint
)
LANGUAGE plpgsql
AS $function$
DECLARE
    v_eligible_nonces bigint := 0;
    v_deleted_nonces bigint := 0;
    v_eligible_idempotency bigint := 0;
    v_deleted_idempotency bigint := 0;
    v_eligible_safe_reports bigint := 0;
    v_deleted_safe_reports bigint := 0;
    v_eligible_review_reports bigint := 0;
    v_deleted_review_reports bigint := 0;
BEGIN
    SELECT count(*) INTO v_eligible_nonces
      FROM geelark_control.agent_request_nonces
     WHERE expires_at <= now() - interval '1 hour';

    SELECT count(*) INTO v_eligible_idempotency
      FROM geelark_control.idempotency_records
     WHERE expires_at IS NOT NULL
       AND expires_at <= now()
       AND split_part(scope, ':', 1) = 'agent'
       AND split_part(scope, ':', 3) IN (
           'heartbeat', 'capabilities', 'modules_report', 'status_read',
           'task_fetch', 'task_accept', 'task_progress', 'task_result',
           'reconcile', 'reconcile_inventory'
       );

    WITH safe_reports AS (
        SELECT r.report_id, r.node_id, r.created_at,
               row_number() OVER (
                   PARTITION BY r.node_id
                   ORDER BY r.created_at DESC, r.report_id DESC
               ) AS safe_rank
          FROM geelark_control.agent_reconciliation_reports AS r
         WHERE NOT EXISTS (
             SELECT 1
               FROM pg_catalog.jsonb_array_elements(r.decisions) AS decision_item(value)
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
    SELECT count(*) INTO v_eligible_safe_reports FROM eligible_reports;

    SELECT count(*) INTO v_eligible_review_reports
      FROM geelark_control.agent_reconciliation_reports AS r
     WHERE r.created_at <= now() - interval '365 days'
       AND EXISTS (
           SELECT 1
             FROM pg_catalog.jsonb_array_elements(r.decisions) AS decision_item(value)
            WHERE coalesce(decision_item.value ->> 'decision', '')
                  NOT IN ('ALREADY_CONFIRMED', 'CONTINUE_SAME_EPOCH')
       );

    -- Preview por defecto: ninguna fila se borra sin confirmación explícita de exportación.
    IF p_confirmed_export THEN
        DELETE FROM geelark_control.agent_request_nonces
         WHERE expires_at <= now() - interval '1 hour';
        GET DIAGNOSTICS v_deleted_nonces = ROW_COUNT;

        DELETE FROM geelark_control.idempotency_records
         WHERE expires_at IS NOT NULL
           AND expires_at <= now()
           AND split_part(scope, ':', 1) = 'agent'
           AND split_part(scope, ':', 3) IN (
               'heartbeat', 'capabilities', 'modules_report', 'status_read',
               'task_fetch', 'task_accept', 'task_progress', 'task_result',
               'reconcile', 'reconcile_inventory'
           );
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
                   FROM pg_catalog.jsonb_array_elements(r.decisions) AS decision_item(value)
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
        GET DIAGNOSTICS v_deleted_safe_reports = ROW_COUNT;

        -- Evidencia unknown/conflictiva nunca se poda por la confirmación genérica.
        -- Hace falta una segunda confirmación explícita y que el informe tenga >365 días.
        IF p_confirmed_review_evidence_export THEN
            DELETE FROM geelark_control.agent_reconciliation_reports AS report
             WHERE report.created_at <= now() - interval '365 days'
               AND EXISTS (
                   SELECT 1
                     FROM pg_catalog.jsonb_array_elements(report.decisions) AS decision_item(value)
                    WHERE coalesce(decision_item.value ->> 'decision', '')
                          NOT IN ('ALREADY_CONFIRMED', 'CONTINUE_SAME_EPOCH')
               );
            GET DIAGNOSTICS v_deleted_review_reports = ROW_COUNT;
        END IF;
    END IF;

    INSERT INTO geelark_control.agent_storage_maintenance_runs (
        requested_by, confirmed_export, confirmed_review_evidence_export,
        eligible_nonces, deleted_nonces,
        eligible_idempotency_records, deleted_idempotency_records,
        eligible_safe_reports, deleted_safe_reports,
        eligible_review_reports, deleted_review_reports
    ) VALUES (
        current_user, p_confirmed_export, p_confirmed_review_evidence_export,
        v_eligible_nonces, v_deleted_nonces,
        v_eligible_idempotency, v_deleted_idempotency,
        v_eligible_safe_reports, v_deleted_safe_reports,
        v_eligible_review_reports, v_deleted_review_reports
    );

    RETURN QUERY SELECT
        v_eligible_nonces, v_deleted_nonces,
        v_eligible_idempotency, v_deleted_idempotency,
        v_eligible_safe_reports, v_deleted_safe_reports,
        v_eligible_review_reports, v_deleted_review_reports;
END
$function$;

-- No exponer la rutina de mantenimiento al rol lector ni a PUBLIC.
REVOKE ALL ON FUNCTION geelark_control.prune_agent_storage(boolean, boolean) FROM PUBLIC;
DO $revoke_reader$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'geelark_master_reader') THEN
        EXECUTE 'REVOKE ALL ON FUNCTION geelark_control.prune_agent_storage(boolean, boolean) FROM geelark_master_reader';
    END IF;
END
$revoke_reader$;

COMMENT ON TABLE geelark_control.agent_storage_maintenance_runs IS
    'Auditoría append-only de previews y podas manuales de almacenamiento de agentes.';

COMMENT ON FUNCTION geelark_control.prune_agent_storage(boolean, boolean) IS
    'Preview por defecto. Con confirmed_export=true borra nonces con 1h de gracia, snapshots vencidos y reportes seguros (>90d o fuera de los últimos 10.000 por nodo). Los informes unknown/conflictivos (>365d) solo se borran con confirmed_export=true y confirmed_review_evidence_export=true tras exportación verificada. Scopes idempotentes desconocidos no se podan.';

COMMIT;
