-- Ejecutar conectado directamente como geelark_master_reader, tras aplicar
-- packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql y establecer su contraseña.
-- La prueba falla si el rol tiene más privilegios de los permitidos.
BEGIN READ ONLY;

DO $$
DECLARE
    forbidden_table text;
BEGIN
    IF current_setting('transaction_read_only') <> 'on' THEN
        RAISE EXCEPTION 'La transacción no está en modo read-only';
    END IF;
    IF NOT has_database_privilege(current_user, current_database(), 'CONNECT') THEN
        RAISE EXCEPTION 'Falta CONNECT sobre la base de datos actual';
    END IF;
    IF NOT has_schema_privilege(current_user, 'geelark_control', 'USAGE') THEN
        RAISE EXCEPTION 'Falta USAGE sobre geelark_control';
    END IF;
    IF has_schema_privilege(current_user, 'geelark_control', 'CREATE') THEN
        RAISE EXCEPTION 'El rol tiene CREATE sobre geelark_control';
    END IF;
    IF NOT has_table_privilege(current_user, 'geelark_control.nodes', 'SELECT') THEN
        RAISE EXCEPTION 'Falta SELECT sobre geelark_control.nodes';
    END IF;
    IF has_table_privilege(current_user, 'geelark_control.nodes', 'INSERT')
       OR has_table_privilege(current_user, 'geelark_control.nodes', 'UPDATE')
       OR has_table_privilege(current_user, 'geelark_control.nodes', 'DELETE')
       OR has_table_privilege(current_user, 'geelark_control.nodes', 'TRUNCATE')
       OR has_table_privilege(current_user, 'geelark_control.nodes', 'REFERENCES')
       OR has_table_privilege(current_user, 'geelark_control.nodes', 'TRIGGER') THEN
        RAISE EXCEPTION 'El rol tiene privilegios de escritura o DDL sobre nodes';
    END IF;

    FOR forbidden_table IN
        SELECT tablename
          FROM pg_tables
         WHERE schemaname = 'geelark_control'
           AND tablename <> 'nodes'
    LOOP
        IF has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'SELECT')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'INSERT')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'UPDATE')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'DELETE')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'TRUNCATE')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'REFERENCES')
           OR has_table_privilege(current_user, 'geelark_control.' || forbidden_table, 'TRIGGER') THEN
            RAISE EXCEPTION 'El rol tiene privilegios no permitidos sobre %', forbidden_table;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
          FROM pg_sequences
         WHERE schemaname = 'geelark_control'
           AND (
             has_sequence_privilege(current_user, format('%I.%I', schemaname, sequencename), 'USAGE')
             OR has_sequence_privilege(current_user, format('%I.%I', schemaname, sequencename), 'SELECT')
             OR has_sequence_privilege(current_user, format('%I.%I', schemaname, sequencename), 'UPDATE')
           )
    ) THEN
        RAISE EXCEPTION 'El rol tiene privilegios sobre secuencias';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_roles
         WHERE rolname = current_user
           AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
    ) THEN
        RAISE EXCEPTION 'El rol tiene atributos privilegiados';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_auth_members m
        JOIN pg_roles r ON r.oid = m.roleid
        JOIN pg_roles u ON u.oid = m.member
        WHERE u.rolname = current_user
    ) THEN
        RAISE EXCEPTION 'El rol es miembro de otros roles; revisar membresías heredadas';
    END IF;
END
$$;

SELECT node_id, display_name, admin_state, health_state, agent_version,
       last_seen_at, capabilities, module_reports, revoked_at
  FROM geelark_control.nodes
 ORDER BY display_name ASC NULLS LAST, node_id ASC
 LIMIT 500;

ROLLBACK;
