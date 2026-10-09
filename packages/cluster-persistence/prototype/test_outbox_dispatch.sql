\set ON_ERROR_STOP on
-- Pruebas de claim, reintento y entrega idempotente del outbox.
BEGIN;

INSERT INTO cluster_control.nodes
 (node_id, display_name, admin_state, health_state, last_seen_at)
VALUES
 ('81000000-0000-4000-8000-000000000001', 'outbox-node', 'active', 'healthy', clock_timestamp());

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('82000000-0000-4000-8000-000000000001', 'outbox-instance', 'running', 'reserved',
  '81000000-0000-4000-8000-000000000001', 1);

INSERT INTO cluster_control.operations
 (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type, operation_state)
VALUES
 ('83000000-0000-4000-8000-000000000001', '84000000-0000-4000-8000-000000000001',
  '82000000-0000-4000-8000-000000000001', '81000000-0000-4000-8000-000000000001', 1, 'assign', 'accepted'),
 ('83000000-0000-4000-8000-000000000002', '84000000-0000-4000-8000-000000000002',
  '82000000-0000-4000-8000-000000000001', '81000000-0000-4000-8000-000000000001', 1, 'start', 'accepted'),
 ('83000000-0000-4000-8000-000000000003', '84000000-0000-4000-8000-000000000003',
  '82000000-0000-4000-8000-000000000001', '81000000-0000-4000-8000-000000000001', 1, 'stop', 'accepted');

INSERT INTO cluster_control.outbox
 (event_id, operation_id, instance_id, assignment_epoch, event_type, payload)
VALUES
 ('85000000-0000-4000-8000-000000000001', '83000000-0000-4000-8000-000000000001',
  '82000000-0000-4000-8000-000000000001', 1, 'assignment.requested', '{"test":1}'),
 ('85000000-0000-4000-8000-000000000002', '83000000-0000-4000-8000-000000000002',
  '82000000-0000-4000-8000-000000000001', 1, 'instance.start', '{"test":2}'),
 ('85000000-0000-4000-8000-000000000003', '83000000-0000-4000-8000-000000000003',
  '82000000-0000-4000-8000-000000000001', 1, 'instance.stop', '{"test":3}');

DO $$
DECLARE
  v_event_a uuid;
  v_event_b uuid;
  v_event_c uuid;
  v_claimed uuid;
  v_attempt integer;
  v_message text;
  v_result boolean;
BEGIN
  SELECT event_id INTO v_event_a
    FROM cluster_control.claim_outbox('worker-a', interval '30 seconds', 1);
  IF v_event_a IS NULL THEN RAISE EXCEPTION 'FAIL: worker-a did not claim an event'; END IF;

  SELECT event_id INTO v_event_b
    FROM cluster_control.claim_outbox('worker-b', interval '30 seconds', 1);
  IF v_event_b IS NULL OR v_event_b = v_event_a THEN
    RAISE EXCEPTION 'FAIL: worker-b did not claim a different event';
  END IF;

  SELECT cluster_control.mark_outbox_delivered(v_event_b, 'worker-b') INTO v_result;
  IF NOT v_result THEN RAISE EXCEPTION 'FAIL: mark delivered returned false'; END IF;
  SELECT cluster_control.mark_outbox_delivered(v_event_b, 'worker-b') INTO v_result;
  IF NOT v_result THEN RAISE EXCEPTION 'FAIL: duplicate delivery mark was not idempotent'; END IF;

  PERFORM cluster_control.release_outbox_failure(v_event_a, 'worker-a', 'TEMPORARY_FAILURE', interval '5 minutes');

  BEGIN
    PERFORM cluster_control.mark_outbox_delivered(v_event_a, 'worker-a');
    RAISE EXCEPTION 'FAIL: released claim was still accepted';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'OUTBOX_CLAIM_LOST' THEN RAISE; END IF;
  END;

  SELECT event_id INTO v_event_c
    FROM cluster_control.claim_outbox('worker-c', interval '30 seconds', 1);
  IF v_event_c IS NULL OR v_event_c IN (v_event_a, v_event_b) THEN
    RAISE EXCEPTION 'FAIL: worker-c did not claim the remaining event';
  END IF;

  UPDATE cluster_control.outbox
     SET claimed_at = clock_timestamp() - interval '10 minutes'
   WHERE event_id = v_event_c;

  SELECT event_id, attempt_count INTO v_claimed, v_attempt
    FROM cluster_control.claim_outbox('worker-d', interval '30 seconds', 1);
  IF v_claimed <> v_event_c OR v_attempt <> 2 THEN
    RAISE EXCEPTION 'FAIL: expired claim was not reclaimed with attempt_count=2';
  END IF;

  BEGIN
    PERFORM cluster_control.mark_outbox_delivered(v_event_c, 'worker-c');
    RAISE EXCEPTION 'FAIL: previous claimant could mark event delivered';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'OUTBOX_CLAIM_LOST' THEN RAISE; END IF;
  END;

  SELECT cluster_control.mark_outbox_delivered(v_event_c, 'worker-d') INTO v_result;
  IF NOT v_result THEN RAISE EXCEPTION 'FAIL: current claimant could not mark delivered'; END IF;

  RAISE NOTICE 'PASS: outbox claims are exclusive, retry is delayed, expired claims can be reclaimed and delivery marks are idempotent';
END $$;

ROLLBACK;
