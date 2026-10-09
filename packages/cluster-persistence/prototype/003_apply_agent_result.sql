-- Prototipo NO productivo: aceptar un resultado de agente con comprobación de fencing.
-- p_authenticated_node_id debe proceder de una identidad autenticada por el servicio,
-- nunca de un valor arbitrario enviado por el cliente.
CREATE OR REPLACE FUNCTION cluster_control.apply_agent_result(
    p_authenticated_node_id uuid,
    p_instance_id uuid,
    p_operation_id uuid,
    p_event_id uuid,
    p_assignment_epoch bigint,
    p_new_state text,
    p_error_code text DEFAULT NULL,
    p_result_summary jsonb DEFAULT '{}'::jsonb
)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    v_instance cluster_control.instances%ROWTYPE;
    v_operation cluster_control.operations%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_operation_state text;
    v_error_code text;
BEGIN
    IF p_assignment_epoch < 0
       OR p_new_state NOT IN ('starting','running','stopping','stopped','failed','unknown','reconciling')
       OR p_result_summary IS NULL
       OR jsonb_typeof(p_result_summary) <> 'object' THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_AGENT_RESULT';
    END IF;

    -- Orden de locks: instancia -> operación.
    SELECT i.* INTO v_instance
      FROM cluster_control.instances AS i
     WHERE i.instance_id = p_instance_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INSTANCE_NOT_FOUND';
    END IF;

    IF v_instance.owner_node_id IS DISTINCT FROM p_authenticated_node_id THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'RESULT_FROM_NON_OWNER';
    END IF;

    IF v_instance.assignment_epoch <> p_assignment_epoch THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'STALE_ASSIGNMENT_EPOCH';
    END IF;

    SELECT o.* INTO v_operation
      FROM cluster_control.operations AS o
     WHERE o.operation_id = p_operation_id
     FOR UPDATE;

    IF NOT FOUND
       OR v_operation.instance_id <> p_instance_id
       OR v_operation.node_id <> p_authenticated_node_id
       OR v_operation.assignment_epoch <> p_assignment_epoch THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'OPERATION_OWNERSHIP_MISMATCH';
    END IF;

    -- Repetir exactamente el resultado terminal es idempotente.
    IF v_operation.operation_state IN ('succeeded','failed','rejected') THEN
        IF v_instance.observed_state = p_new_state THEN
            RETURN p_new_state;
        END IF;
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'OPERATION_ALREADY_TERMINAL';
    END IF;

    IF v_instance.observed_state = p_new_state THEN
        RETURN p_new_state;
    END IF;

    IF NOT (
       (v_instance.observed_state = 'reserved' AND p_new_state IN ('starting','running','failed','unknown'))
       OR (v_instance.observed_state = 'starting' AND p_new_state IN ('running','failed','unknown'))
       OR (v_instance.observed_state = 'running' AND p_new_state IN ('stopping','failed','unknown'))
       OR (v_instance.observed_state = 'stopping' AND p_new_state IN ('stopped','failed','unknown'))
       OR (v_instance.observed_state = 'unknown' AND p_new_state IN ('running','stopped','failed','reconciling'))
       OR (v_instance.observed_state = 'reconciling' AND p_new_state IN ('running','stopped','failed','unknown'))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_STATE_TRANSITION';
    END IF;

    v_error_code := CASE
        WHEN p_new_state = 'failed' THEN COALESCE(NULLIF(trim(p_error_code), ''), 'AGENT_REPORTED_FAILURE')
        ELSE NULL
    END;

    v_operation_state := CASE
        WHEN p_new_state IN ('running','stopped') THEN 'succeeded'
        WHEN p_new_state = 'failed' THEN 'failed'
        WHEN p_new_state = 'unknown' THEN 'unknown'
        ELSE 'running'
    END;

    UPDATE cluster_control.instances
       SET observed_state = p_new_state,
           updated_at = v_now
     WHERE instance_id = p_instance_id;

    UPDATE cluster_control.operations
       SET operation_state = v_operation_state,
           error_code = v_error_code,
           result_summary = p_result_summary,
           updated_at = v_now,
           finished_at = CASE
               WHEN v_operation_state IN ('succeeded','failed','rejected') THEN v_now
               ELSE NULL
           END
     WHERE operation_id = p_operation_id;

    INSERT INTO cluster_control.assignment_events
        (event_id, instance_id, assignment_epoch, node_id,
         previous_state, new_state, actor_type, actor_id,
         reason_code, request_id, operation_id, created_at, details)
    VALUES
        (p_event_id, p_instance_id, p_assignment_epoch, p_authenticated_node_id,
         v_instance.observed_state, p_new_state, 'node_agent',
         p_authenticated_node_id::text, 'agent_result',
         v_operation.request_id, p_operation_id, v_now, p_result_summary);

    RETURN p_new_state;
END;
$$;

-- Cerrado por defecto. El servicio de dominio debe conceder EXECUTE a un rol dedicado.
REVOKE ALL ON FUNCTION cluster_control.apply_agent_result(uuid, uuid, uuid, uuid, bigint, text, text, jsonb) FROM PUBLIC;
