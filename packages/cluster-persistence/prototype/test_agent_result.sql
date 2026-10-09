\set ON_ERROR_STOP on
-- Prueba de fencing: solo el propietario y epoch vigente pueden mutar estado.
BEGIN;

INSERT INTO cluster_control.nodes
 (node_id, display_name, admin_state, health_state, last_seen_at)
VALUES
 ('71000000-0000-4000-8000-000000000001', 'result-owner', 'active', 'healthy', clock_timestamp()),
 ('71000000-0000-4000-8000-000000000002', 'result-non-owner', 'active', 'healthy', clock_timestamp());

INSERT INTO cluster_control.node_capacity
 (node_id, memory_usable_bytes, storage_usable_bytes, cpu_usable_units, observed_at)
VALUES
 ('71000000-0000-4000-8000-000000000001', 100, 1000, 10, clock_timestamp()),
 ('71000000-0000-4000-8000-000000000002', 100, 1000, 10, clock_timestamp());

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('72000000-0000-4000-8000-000000000001', 'result-instance', 'running', 'stopped', NULL, 0);

DO $$
DECLARE
  v_operation_id uuid;
  v_epoch bigint;
  v_replayed boolean;
  v_state text;
  v_message text;
  v_count bigint;
BEGIN
  SELECT operation_id, assignment_epoch, replayed
    INTO v_operation_id, v_epoch, v_replayed
    FROM cluster_control.assign_instance(
      '72000000-0000-4000-8000-000000000001',
      '71000000-0000-4000-8000-000000000001',
      '73000000-0000-4000-8000-000000000001',
      '74000000-0000-4000-8000-000000000001',
      '75000000-0000-4000-8000-000000000001',
      '76000000-0000-4000-8000-000000000001',
      '77000000-0000-4000-8000-000000000001',
      '78000000-0000-4000-8000-000000000001',
      'test-result',
      'result-key-0000001',
      repeat('e',64),
      10, 100, 1
    );

  SELECT cluster_control.apply_agent_result(
      '71000000-0000-4000-8000-000000000001',
      '72000000-0000-4000-8000-000000000001',
      v_operation_id,
      '79000000-0000-4000-8000-000000000001',
      v_epoch,
      'running',
      NULL,
      jsonb_build_object('reported_state','running')
  ) INTO v_state;

  IF v_state <> 'running' THEN RAISE EXCEPTION 'FAIL: owner result was not applied'; END IF;

  -- Repetir el resultado terminal exacto debe ser idempotente y no duplicar auditoría.
  SELECT cluster_control.apply_agent_result(
      '71000000-0000-4000-8000-000000000001',
      '72000000-0000-4000-8000-000000000001',
      v_operation_id,
      '79000000-0000-4000-8000-000000000002',
      v_epoch,
      'running',
      NULL,
      jsonb_build_object('reported_state','running')
  ) INTO v_state;

  BEGIN
    PERFORM cluster_control.apply_agent_result(
      '71000000-0000-4000-8000-000000000001',
      '72000000-0000-4000-8000-000000000001',
      v_operation_id,
      '79000000-0000-4000-8000-000000000003',
      0,
      'stopped',
      NULL,
      '{}'::jsonb
    );
    RAISE EXCEPTION 'FAIL: stale epoch was accepted';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'STALE_ASSIGNMENT_EPOCH' THEN RAISE; END IF;
  END;

  BEGIN
    PERFORM cluster_control.apply_agent_result(
      '71000000-0000-4000-8000-000000000002',
      '72000000-0000-4000-8000-000000000001',
      v_operation_id,
      '79000000-0000-4000-8000-000000000004',
      v_epoch,
      'stopped',
      NULL,
      '{}'::jsonb
    );
    RAISE EXCEPTION 'FAIL: non-owner result was accepted';
  EXCEPTION WHEN SQLSTATE 'P0001' THEN
    GET STACKED DIAGNOSTICS v_message = MESSAGE_TEXT;
    IF v_message <> 'RESULT_FROM_NON_OWNER' THEN RAISE; END IF;
  END;

  SELECT observed_state INTO v_state FROM cluster_control.instances
   WHERE instance_id = '72000000-0000-4000-8000-000000000001';
  IF v_state <> 'running' THEN RAISE EXCEPTION 'FAIL: rejected result changed instance state'; END IF;

  SELECT count(*) INTO v_count FROM cluster_control.assignment_events
   WHERE instance_id = '72000000-0000-4000-8000-000000000001';
  IF v_count <> 2 THEN RAISE EXCEPTION 'FAIL: duplicate or rejected results changed audit count'; END IF;

  RAISE NOTICE 'PASS: current owner/epoch accepted; duplicate terminal result is idempotent; stale and non-owner results rejected';
END $$;

ROLLBACK;
