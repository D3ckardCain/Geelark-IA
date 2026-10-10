-- Smoke/invariant tests for 0001_cluster_control.sql.
-- Run against a fresh disposable database after applying the migration.
BEGIN;

INSERT INTO geelark_control.nodes (node_id, display_name, admin_state)
VALUES
 ('22222222-2222-4222-8222-222222222222', 'node-a', 'active'),
 ('33333333-3333-4333-8333-333333333333', 'node-b', 'active');

INSERT INTO geelark_control.instances
    (instance_id, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('66666666-6666-4666-8666-666666666666', 'running', 'unknown',
  '22222222-2222-4222-8222-222222222222', 1);

INSERT INTO geelark_control.resource_reservations
    (reservation_id, instance_id, node_id, assignment_epoch, cpu_units, memory_bytes, storage_bytes, status)
VALUES
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '66666666-6666-4666-8666-666666666666',
  '22222222-2222-4222-8222-222222222222', 1, 1.0, 1024, 4096, 'uncertain');

DO $$
BEGIN
    BEGIN
        INSERT INTO geelark_control.resource_reservations
            (reservation_id, instance_id, node_id, assignment_epoch, cpu_units, memory_bytes, storage_bytes, status)
        VALUES
            ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
             '66666666-6666-4666-8666-666666666666',
             '33333333-3333-4333-8333-333333333333', 2, 1.0, 1024, 4096, 'held');
        RAISE EXCEPTION 'Expected duplicate blocking reservation to fail';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

INSERT INTO geelark_control.operations
    (operation_id, request_id, instance_id, node_id, assignment_epoch, operation_type, status)
VALUES
 ('55555555-5555-4555-8555-555555555555',
  '11111111-1111-4111-8111-111111111111',
  '66666666-6666-4666-8666-666666666666',
  '22222222-2222-4222-8222-222222222222', 1, 'assign', 'accepted');

INSERT INTO geelark_control.idempotency_records
    (scope, idempotency_key, payload_sha256, operation_id)
VALUES
 ('node:22222222-2222-4222-8222-222222222222',
  'idempotency-key-test-0001',
  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  '55555555-5555-4555-8555-555555555555');

DO $$
BEGIN
    BEGIN
        INSERT INTO geelark_control.idempotency_records
            (scope, idempotency_key, payload_sha256, operation_id)
        VALUES
            ('node:22222222-2222-4222-8222-222222222222',
             'idempotency-key-test-0001',
             'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
             '55555555-5555-4555-8555-555555555555');
        RAISE EXCEPTION 'Expected duplicate idempotency key to fail';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE current_epoch bigint;
DECLARE observed text;
BEGIN
    SELECT assignment_epoch, observed_state INTO current_epoch, observed
      FROM geelark_control.instances
     WHERE instance_id = '66666666-6666-4666-8666-666666666666';
    IF current_epoch <> 1 OR observed <> 'unknown' THEN
        RAISE EXCEPTION 'Unexpected instance state after seed';
    END IF;
END $$;

ROLLBACK;
