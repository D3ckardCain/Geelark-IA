-- Prototipo NO productivo de dispatcher outbox con entrega al menos una vez.
-- La autenticación del worker/controlador debe ocurrir fuera de estas funciones.
CREATE OR REPLACE FUNCTION cluster_control.claim_outbox(
    p_worker_id text,
    p_claim_lease interval DEFAULT interval '30 seconds',
    p_batch_size integer DEFAULT 10
)
RETURNS TABLE(
    event_id uuid,
    operation_id uuid,
    instance_id uuid,
    assignment_epoch bigint,
    event_type text,
    payload jsonb,
    attempt_count integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_worker_id IS NULL OR length(trim(p_worker_id)) NOT BETWEEN 1 AND 120
       OR p_claim_lease <= interval '0 seconds'
       OR p_batch_size NOT BETWEEN 1 AND 100 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_OUTBOX_CLAIM_INPUT';
    END IF;

    RETURN QUERY
    WITH candidates AS (
        SELECT o.event_id
          FROM cluster_control.outbox AS o
         WHERE o.delivered_at IS NULL
           AND o.available_at <= clock_timestamp()
           AND (o.claimed_at IS NULL OR o.claimed_at < clock_timestamp() - p_claim_lease)
         ORDER BY o.available_at, o.created_at, o.event_id
         FOR UPDATE SKIP LOCKED
         LIMIT p_batch_size
    )
    UPDATE cluster_control.outbox AS o
       SET claimed_at = clock_timestamp(),
           claimed_by = p_worker_id,
           attempt_count = o.attempt_count + 1
      FROM candidates AS c
     WHERE o.event_id = c.event_id
    RETURNING o.event_id, o.operation_id, o.instance_id,
              o.assignment_epoch, o.event_type, o.payload, o.attempt_count;
END;
$$;

CREATE OR REPLACE FUNCTION cluster_control.mark_outbox_delivered(
    p_event_id uuid,
    p_worker_id text
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_delivered_at timestamptz;
BEGIN
    SELECT o.delivered_at INTO v_delivered_at
      FROM cluster_control.outbox AS o
     WHERE o.event_id = p_event_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'OUTBOX_EVENT_NOT_FOUND';
    END IF;

    IF v_delivered_at IS NOT NULL THEN
        RETURN true;
    END IF;

    UPDATE cluster_control.outbox
       SET delivered_at = clock_timestamp()
     WHERE event_id = p_event_id
       AND delivered_at IS NULL
       AND claimed_by = p_worker_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'OUTBOX_CLAIM_LOST';
    END IF;

    RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION cluster_control.release_outbox_failure(
    p_event_id uuid,
    p_worker_id text,
    p_error_code text,
    p_retry_after interval
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_error_code IS NULL OR length(trim(p_error_code)) NOT BETWEEN 1 AND 120
       OR p_retry_after <= interval '0 seconds' THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'INVALID_OUTBOX_RETRY_INPUT';
    END IF;

    UPDATE cluster_control.outbox
       SET available_at = clock_timestamp() + p_retry_after,
           claimed_at = NULL,
           claimed_by = NULL,
           last_error_code = p_error_code
     WHERE event_id = p_event_id
       AND delivered_at IS NULL
       AND claimed_by = p_worker_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'OUTBOX_CLAIM_LOST';
    END IF;

    RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION cluster_control.claim_outbox(text, interval, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION cluster_control.mark_outbox_delivered(uuid, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION cluster_control.release_outbox_failure(uuid, text, text, interval) FROM PUBLIC;
