-- Prototipo NO productivo: asignación atómica en PostgreSQL.
-- La función solo debe ejecutarse en la base desechable del workflow mientras
-- no haya revisión de seguridad y pruebas de recuperación completas.
CREATE OR REPLACE FUNCTION cluster_control.assign_instance(
    p_instance_id uuid,
    p_node_id uuid,
    p_reservation_id uuid,
    p_operation_id uuid,
    p_event_id uuid,
    p_outbox_event_id uuid,
    p_idempotency_id uuid,
    p_request_id uuid,
    p_scope text,
    p_idempotency_key text,
    p_payload_sha256 text,
    p_memory_bytes bigint,
    p_storage_bytes bigint,
    p_cpu_units numeric,
    p_lease_duration interval DEFAULT interval '60 seconds',
    p_max_observation_age interval DEFAULT interval '30 seconds'
)
RETURNS TABLE(operation_id uuid, assignment_epoch bigint, replayed boolean)
LANGUAGE plpgsql
AS $$
DECLARE
    v_inserted_id uuid;
    v_existing_hash text;
    v_existing_operation_id uuid;
    v_existing_response jsonb;
    v_instance cluster_control.instances%ROWTYPE;
    v_node cluster_control.nodes%ROWTYPE;
    v_capacity cluster_control.node_capacity%ROWTYPE;
    v_epoch bigint;
    v_reserved_memory bigint;
    v_reserved_storage bigint;
    v_reserved_cpu numeric;
    v_now timestamptz := clock_timestamp();
BEGIN
    IF p_scope IS NULL OR length(trim(p_scope)) NOT BETWEEN 1 AND 160
       OR p_idempotency_key IS NULL OR length(p_idempotency_key) NOT BETWEEN 16 AND 200
       OR p_payload_sha256 IS NULL OR length(p_payload_sha256) <> 64
       OR p_payload_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_IDEMPOTENCY_INPUT';
    END IF;

    IF p_memory_bytes <= 0 OR p_storage_bytes <= 0 OR p_cpu_units <= 0
       OR p_lease_duration <= interval '0 seconds'
       OR p_max_observation_age <= interval '0 seconds' THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_RESOURCE_OR_TIMEOUT';
    END IF;

    INSERT INTO cluster_control.idempotency_records
        (idempotency_id, scope, idempotency_key, payload_sha256)
    VALUES
        (p_idempotency_id, p_scope, p_idempotency_key, p_payload_sha256)
    ON CONFLICT (scope, idempotency_key) DO NOTHING
    RETURNING idempotency_id INTO v_inserted_id;

    IF v_inserted_id IS NULL THEN
        SELECT ir.payload_sha256, ir.operation_id, ir.response_summary
          INTO v_existing_hash, v_existing_operation_id, v_existing_response
          FROM cluster_control.idempotency_records AS ir
         WHERE ir.scope = p_scope AND ir.idempotency_key = p_idempotency_key
         FOR UPDATE;

        IF v_existing_hash IS DISTINCT FROM p_payload_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'IDEMPOTENCY_CONFLICT';
        END IF;

        IF v_existing_operation_id IS NULL
           OR v_existing_response->>'assignment_epoch' IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'IDEMPOTENCY_RECORD_INCOMPLETE';
        END IF;

        RETURN QUERY SELECT
            v_existing_operation_id,
            (v_existing_response->>'assignment_epoch')::bigint,
            true;
        RETURN;
    END IF;

    -- Orden de locks documentado: instancia -> nodo -> instantánea de capacidad.
    SELECT i.* INTO v_instance
      FROM cluster_control.instances AS i
     WHERE i.instance_id = p_instance_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INSTANCE_NOT_FOUND';
    END IF;

    IF v_instance.owner_node_id IS NOT NULL
       OR v_instance.observed_state IN ('reserved','starting','running','stopping','unknown','reconciling') THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INSTANCE_ALREADY_ASSIGNED_OR_UNCERTAIN';
    END IF;

    SELECT n.* INTO v_node
      FROM cluster_control.nodes AS n
     WHERE n.node_id = p_node_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'NODE_NOT_FOUND';
    END IF;

    IF v_node.admin_state <> 'active'
       OR v_node.health_state NOT IN ('healthy','degraded')
       OR v_node.last_seen_at IS NULL
       OR v_node.last_seen_at < v_now - p_max_observation_age THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'NODE_NOT_ELIGIBLE_OR_TELEMETRY_STALE';
    END IF;

    SELECT nc.* INTO v_capacity
      FROM cluster_control.node_capacity AS nc
     WHERE nc.node_id = p_node_id
     FOR UPDATE;

    IF NOT FOUND OR v_capacity.observed_at < v_now - p_max_observation_age THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'NODE_CAPACITY_MISSING_OR_STALE';
    END IF;

    SELECT
        COALESCE(sum(rr.memory_bytes), 0),
        COALESCE(sum(rr.storage_bytes), 0),
        COALESCE(sum(rr.cpu_units), 0)
      INTO v_reserved_memory, v_reserved_storage, v_reserved_cpu
      FROM cluster_control.resource_reservations AS rr
     WHERE rr.node_id = p_node_id
       AND rr.reservation_state IN ('held','uncertain');

    IF p_memory_bytes > v_capacity.memory_usable_bytes - v_reserved_memory
       OR p_storage_bytes > v_capacity.storage_usable_bytes - v_reserved_storage
       OR p_cpu_units > v_capacity.cpu_usable_units - v_reserved_cpu THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'NODE_CAPACITY_EXCEEDED';
    END IF;

    v_epoch := v_instance.assignment_epoch + 1;

    UPDATE cluster_control.instances
       SET owner_node_id = p_node_id,
           assignment_epoch = v_epoch,
           lease_expires_at = v_now + p_lease_duration,
           observed_state = 'reserved',
           updated_at = v_now
     WHERE instance_id = p_instance_id;

    INSERT INTO cluster_control.resource_reservations
        (reservation_id, instance_id, node_id, assignment_epoch,
         memory_bytes, storage_bytes, cpu_units, reservation_state)
    VALUES
        (p_reservation_id, p_instance_id, p_node_id, v_epoch,
         p_memory_bytes, p_storage_bytes, p_cpu_units, 'held');

    INSERT INTO cluster_control.operations
        (operation_id, request_id, instance_id, node_id, assignment_epoch,
         operation_type, operation_state, created_at, updated_at)
    VALUES
        (p_operation_id, p_request_id, p_instance_id, p_node_id, v_epoch,
         'assign', 'accepted', v_now, v_now);

    INSERT INTO cluster_control.assignment_events
        (event_id, instance_id, assignment_epoch, node_id,
         previous_state, new_state, actor_type, reason_code,
         request_id, operation_id, created_at, details)
    VALUES
        (p_event_id, p_instance_id, v_epoch, p_node_id,
         v_instance.observed_state, 'reserved', 'controller',
         'assignment_reserved', p_request_id, p_operation_id, v_now,
         jsonb_build_object('memory_bytes', p_memory_bytes,
                            'storage_bytes', p_storage_bytes,
                            'cpu_units', p_cpu_units));

    INSERT INTO cluster_control.outbox
        (event_id, operation_id, instance_id, assignment_epoch,
         event_type, payload, created_at, available_at)
    VALUES
        (p_outbox_event_id, p_operation_id, p_instance_id, v_epoch,
         'assignment.requested',
         jsonb_build_object('operation_id', p_operation_id,
                            'instance_id', p_instance_id,
                            'node_id', p_node_id,
                            'assignment_epoch', v_epoch),
         v_now, v_now);

    UPDATE cluster_control.idempotency_records
       SET operation_id = p_operation_id,
           response_summary = jsonb_build_object(
               'operation_id', p_operation_id,
               'assignment_epoch', v_epoch
           )
     WHERE idempotency_id = p_idempotency_id;

    RETURN QUERY SELECT p_operation_id, v_epoch, false;
END;
$$;
