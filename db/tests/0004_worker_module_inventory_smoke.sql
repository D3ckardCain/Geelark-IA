-- Smoke/invariant tests for migration 0004_worker_module_inventory.sql.
-- Run in a fresh disposable PostgreSQL database after all migrations.
BEGIN;

INSERT INTO geelark_control.nodes (node_id, display_name, admin_state)
VALUES ('77777777-7777-4777-8777-777777777777', 'module-inventory-test', 'active');

DO $$
DECLARE
    stored jsonb;
BEGIN
    SELECT module_reports INTO stored
      FROM geelark_control.nodes
     WHERE node_id = '77777777-7777-4777-8777-777777777777';
    IF stored <> '[]'::jsonb THEN
        RAISE EXCEPTION 'module_reports default must be an empty array';
    END IF;
END $$;

UPDATE geelark_control.nodes
   SET module_reports = '[{"module_id":"agent-supervisor","state":"operational"}]'::jsonb
 WHERE node_id = '77777777-7777-4777-8777-777777777777';

DO $$
DECLARE
    invalid_value jsonb;
BEGIN
    BEGIN
        UPDATE geelark_control.nodes
           SET module_reports = '{}'::jsonb
         WHERE node_id = '77777777-7777-4777-8777-777777777777';
        RAISE EXCEPTION 'Expected non-array module_reports to be rejected';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    SELECT jsonb_agg(jsonb_build_object('module_id', 'module-' || i))
      INTO invalid_value
      FROM generate_series(1, 33) AS nums(i);

    BEGIN
        UPDATE geelark_control.nodes
           SET module_reports = invalid_value
         WHERE node_id = '77777777-7777-4777-8777-777777777777';
        RAISE EXCEPTION 'Expected module_reports with more than 32 items to be rejected';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
END $$;

ROLLBACK;
