\set ON_ERROR_STOP on
-- Pruebas de integración del prototipo transaccional. Todo se revierte al final.
BEGIN;

INSERT INTO cluster_control.nodes
 (node_id, display_name, admin_state, health_state, last_seen_at)
VALUES
 ('51000000-0000-4000-8000-000000000001', 'assignment-node-a', 'active', 'healthy', clock_timestamp());

INSERT INTO cluster_control.node_capacity
 (node_id, memory_usable_bytes, storage_usable_bytes, cpu_usable_units, observed_at)
VALUES
 ('51000000-0000-4000-8000-000000000001', 100, 1000, 10, clock_timestamp());

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('52000000-0000-4000-8000-000000000001', 'assignment-instance', 'running', 'stopped', NULL, 0),
 ('52000000-0000-4000-8000-000000000002', 'capacity-instance', 'running', 'stopped', NULL, 0);

DO $$
DECLARE
  v_operation_id uuid;
  v_replay_operation_id uuid;
  v_epoch bigint;
  v_replay_epoch bigint;
  v_replayed boolean;
  v_replay_flag boolean;
  v_message text;
  v_count bigint;
BEGIN
  SELECT operation_id, assignment_epoch, replayed
    INTO v_operation_id, v_epoch, v_replayed
    FROM cluster_control.assign_instance(
      '52000000-0000-4000-8000-000000000001',
      '51000000-0000-4000-8000-000000000001',
      '53000000-0000-4000-8000-000000000001',
      '54000000-0000-4000-8000-000000000001',
      '55000000-0000-4000-8000-000000000001',
      '56000000-0000-4000-8000-000000000001',
      '57000000-0000-4000-8000-000000000001',
      '58000000-0000-4000-8000-000000000001',
      'test-assignment',
      'assignment-key-000001',
      repeat('a',64),
      60, 600, 2,
      interval '60 seconds', interval '30 seconds'
    );

  IF v_epoch <> 1 OR v_replayed THEN
    RAISE EXCEPTION 'FAIL: first assignment should return epoch 1 and replayed=false';
  END IF;

  SELECT operation_id, assignment_epoch, replayed
    INTO v_replay_operation_id, v_replay_epoch, v_replay_flag
    FROM cluster_control.assign_instance(
      '52000000-0000-4000-8000-000000000001',
      '51000000-0000-4000-8000-000000000001',
      '53000000-0000-4000-8000-000000000099',
      '54000000-0000-4000-8000-000000000099',
      '55000000-0000-4000-8000-000000000099',
      '56000000-0000-4000-8000-000000000099',
      '57000000-0000-4000-8000-000000000099',
      '58000000-0000-4000-8000-000000000099',
      'test-assignment',
      'assignment-key-000001',
      repeat('a',64),
      60, 600, 2,
      interval '60 seconds', interval '30 seconds'
    );

  IF v_replay_operation_id <> v_operation_id OR v_replay_epoch <> 1 OR NOT v_replay_flag THEN
    RAISE EXCEPTION 'FAIL: idempotent retry did not return the original operation';
  END IF;

  BEGIN
    PERFORM * FROM cluster_control.assign_instance(
      '52000000-0000-4000-8000-000000000001',
      '51000000-0000-4000-8000-000000000001',
      '53000000-0000-4000-8000-000000000098',
      '54000000-0000-4000-8000-000000000098',
      '55000000-0000-4000-8000-000000000098',
      '56000000-0000-4000-8000-000000000098',
      '57000000-0000-4000-8000-000000000098',
      '58000000-0000-4000-8000-000000000098',
      'test-assignment',
      'assignment-key-000001',
      repeat('b',64),
      60, 600, 2,
      interval '60 seconds', interval '30 seconds'
    );
    RAISE EXCEPTION 'FAIL: same idempotency key with different hash was accepted';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'IDEMPOTENCY_CONFLICT' THEN RAISE; END IF;
  END;

  BEGIN
    PERFORM * FROM cluster_control.assign_instance(
      '52000000-0000-4000-8000-000000000002',
      '51000000-0000-4000-8000-000000000001',
      '53000000-0000-4000-8000-000000000002',
      '54000000-0000-4000-8000-000000000002',
      '55000000-0000-4000-8000-000000000002',
      '56000000-0000-4000-8000-000000000002',
      '57000000-0000-4000-8000-000000000002',
      '58000000-0000-4000-8000-000000000002',
      'test-capacity',
      'capacity-key-000001',
      repeat('c',64),
      50, 500, 1,
      interval '60 seconds', interval '30 seconds'
    );
    RAISE EXCEPTION 'FAIL: assignment exceeded available capacity';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'NODE_CAPACITY_EXCEEDED' THEN RAISE; END IF;
  END;

  SELECT count(*) INTO v_count FROM cluster_control.resource_reservations
   WHERE instance_id = '52000000-0000-4000-8000-000000000001'
     AND reservation_state = 'held';
  IF v_count <> 1 THEN RAISE EXCEPTION 'FAIL: expected exactly one held reservation'; END IF;

  SELECT count(*) INTO v_count FROM cluster_control.outbox
   WHERE instance_id = '52000000-0000-4000-8000-000000000001'
     AND event_type = 'assignment.requested';
  IF v_count <> 1 THEN RAISE EXCEPTION 'FAIL: expected exactly one outbox event'; END IF;

  RAISE NOTICE 'PASS: atomic assignment, idempotent replay, hash conflict and capacity rejection';
END $$;

ROLLBACK;
