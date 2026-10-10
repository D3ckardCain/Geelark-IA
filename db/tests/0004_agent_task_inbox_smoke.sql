-- Smoke tests de la bandeja durable de tareas del agente.
BEGIN;

DO $$
DECLARE
    v_node uuid := '8f4a0ef0-7e65-4bb7-9f12-8c3b66b1b001';
    v_instance uuid := '8f4a0ef0-7e65-4bb7-9f12-8c3b66b1b002';
    v_operation uuid := '8f4a0ef0-7e65-4bb7-9f12-8c3b66b1b003';
    v_task uuid := '8f4a0ef0-7e65-4bb7-9f12-8c3b66b1b004';
BEGIN
    IF to_regclass('geelark_control.agent_tasks') IS NULL THEN
        RAISE EXCEPTION 'Falta geelark_control.agent_tasks';
    END IF;

    INSERT INTO geelark_control.nodes(node_id, display_name, admin_state)
    VALUES (v_node, 'schema-smoke-task-node', 'active');
    INSERT INTO geelark_control.instances(
        instance_id, desired_state, observed_state, owner_node_id,
        assignment_epoch, lease_expires_at
    ) VALUES (
        v_instance, 'running', 'reserved', v_node, 1, now() + interval '5 minutes'
    );
    INSERT INTO geelark_control.operations(
        operation_id, request_id, instance_id, node_id, assignment_epoch,
        operation_type, status
    ) VALUES (
        v_operation, v_operation, v_instance, v_node, 1, 'assign', 'accepted'
    );
    INSERT INTO geelark_control.agent_tasks(
        task_id, operation_id, node_id, instance_id, assignment_epoch, payload
    ) VALUES (
        v_task, v_operation, v_node, v_instance, 1, '{"schema_version":1,"kind":"instance.assign"}'::jsonb
    );

    BEGIN
        INSERT INTO geelark_control.agent_tasks(
            task_id, operation_id, node_id, instance_id, assignment_epoch, payload, status
        ) VALUES (
            '8f4a0ef0-7e65-4bb7-9f12-8c3b66b1b005', v_operation, v_node, v_instance, 1,
            '{"schema_version":1}'::jsonb, 'arbitrary_command'
        );
        RAISE EXCEPTION 'El esquema aceptó un estado de tarea arbitrario';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    DELETE FROM geelark_control.agent_tasks WHERE node_id = v_node;
    DELETE FROM geelark_control.operations WHERE operation_id = v_operation;
    DELETE FROM geelark_control.instances WHERE instance_id = v_instance;
    DELETE FROM geelark_control.nodes WHERE node_id = v_node;
END $$;

COMMIT;
