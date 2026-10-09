\set ON_ERROR_STOP on
-- Smoke tests de restricciones para el prototipo. Todo se revierte al final.
BEGIN;

INSERT INTO cluster_control.nodes (node_id, display_name, admin_state, health_state)
VALUES
 ('10000000-0000-4000-8000-000000000001', 'test-node-a', 'active', 'healthy'),
 ('10000000-0000-4000-8000-000000000002', 'test-node-b', 'active', 'healthy');

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('20000000-0000-4000-8000-000000000001', 'test-instance', 'stopped', 'stopped', NULL, 0);

INSERT INTO cluster_control.resource_reservations
 (reservation_id, instance_id, node_id, assignment_epoch, memory_bytes, storage_bytes, cpu_units, reservation_state)
VALUES
 ('30000000-0000-4000-8000-000000000001',
  '20000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000001', 1, 1024, 2048, 1, 'held');

DO $$
BEGIN
  BEGIN
    INSERT INTO cluster_control.resource_reservations
     (reservation_id, instance_id, node_id, assignment_epoch, memory_bytes, storage_bytes, cpu_units, reservation_state)
    VALUES
     ('30000000-0000-4000-8000-000000000002',
      '20000000-0000-4000-8000-000000000001',
      '10000000-0000-4000-8000-000000000002', 2, 1024, 2048, 1, 'uncertain');
    RAISE EXCEPTION 'FALLO: se permitió una segunda reserva activa para la misma instancia';
  EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'OK: se rechazó una segunda reserva activa';
  END;

  BEGIN
    INSERT INTO cluster_control.resource_reservations
     (reservation_id, instance_id, node_id, assignment_epoch, memory_bytes, storage_bytes, cpu_units, reservation_state)
    VALUES
     ('30000000-0000-4000-8000-000000000003',
      '20000000-0000-4000-8000-000000000001',
      '10000000-0000-4000-8000-000000000002', 3, 0, 2048, 1, 'released');
    RAISE EXCEPTION 'FALLO: se permitió memoria no positiva';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'OK: se rechazó memoria no positiva';
  END;

  BEGIN
    INSERT INTO cluster_control.idempotency_records
      (idempotency_id, scope, idempotency_key, payload_sha256)
    VALUES
      ('40000000-0000-4000-8000-000000000001',
       'test-scope', 'idempotency-key-test-001', 'not-a-sha256-digest');
    RAISE EXCEPTION 'FALLO: se permitió un digest inválido';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'OK: se rechazó un digest inválido';
  END;
END $$;

ROLLBACK;
