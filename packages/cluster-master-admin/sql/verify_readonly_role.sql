-- Ejecutar conectado directamente como geelark_master_reader, tras aplicar
-- packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql y establecer su contraseña.
-- La prueba falla si el rol conserva privilegios fuera del único objeto permitido.
BEGIN READ ONLY;

DO $$
DECLARE
    forbidden_object text;
    role_oid oid;
BEGIN
    SELECT oid INTO role_oid FROM pg_roles WHERE rolname = current_user;

    IF current_setting('transaction_read_only') <> 'on' THEN
        RAISE EXCEPTION 'La transacción no está en modo read-only';
    END IF;
    IF role_oid IS NULL OR NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE oid = role_oid AND rolcanlogin
    ) THEN
        RAISE EXCEPTION 'El rol lector no tiene LOGIN habilitado';
    END IF;
    IF NOT has_database_privilege(current_user, current_database(), 'CONNECT') THEN
        RAISE EXCEPTION 'Falta CONNECT sobre la base de datos actual';
    END IF;
    IF has_database_privilege(current_user, current_database(), 'CREATE') THEN
        RAISE EXCEPTION 'El rol tiene CREATE sobre la base de datos actual';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_database
         WHERE datname = current_database() AND datdba = role_oid
    ) THEN
        RAISE EXCEPTION 'El rol no puede ser propietario de la base de datos';
    END IF;
    IF NOT has_schema_privilege(current_user, 'geelark_control', 'USAGE') THEN
        RAISE EXCEPTION 'Falta USAGE sobre geelark_control';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_namespace n
         WHERE n.nspname NOT LIKE 'pg\_%' ESCAPE '\'
           AND n.nspname <> 'information_schema'
           AND has_schema_privilege(current_user, n.oid, 'CREATE')
    ) THEN
        RAISE EXCEPTION 'El rol tiene CREATE sobre un esquema no permitido';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_namespace
         WHERE nspowner = role_oid
           AND nspname NOT LIKE 'pg\_%' ESCAPE '\'
           AND nspname <> 'information_schema'
    ) THEN
        RAISE EXCEPTION 'El rol es propietario de un esquema no permitido';
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

    IF EXISTS (
        SELECT 1
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
           AND n.nspname NOT LIKE 'pg\_%' ESCAPE '\'
           AND n.nspname <> 'information_schema'
           AND NOT (n.nspname = 'geelark_control' AND c.relname = 'nodes')
           AND (
             has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'SELECT')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'INSERT')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'UPDATE')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'DELETE')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'TRUNCATE')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'REFERENCES')
             OR has_table_privilege(current_user, format('%I.%I', n.nspname, c.relname), 'TRIGGER')
           )
    ) THEN
        RAISE EXCEPTION 'El rol tiene privilegios efectivos sobre un objeto distinto de geelark_control.nodes';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_sequences s
         WHERE s.schemaname NOT LIKE 'pg\_%' ESCAPE '\'
           AND s.schemaname <> 'information_schema'
           AND (
             has_sequence_privilege(current_user, format('%I.%I', s.schemaname, s.sequencename), 'USAGE')
             OR has_sequence_privilege(current_user, format('%I.%I', s.schemaname, s.sequencename), 'SELECT')
             OR has_sequence_privilege(current_user, format('%I.%I', s.schemaname, s.sequencename), 'UPDATE')
           )
    ) THEN
        RAISE EXCEPTION 'El rol tiene privilegios sobre secuencias no permitidas';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_class c
         WHERE c.relowner = role_oid
           AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
           AND c.relnamespace IN (
             SELECT n.oid FROM pg_namespace n
              WHERE n.nspname NOT LIKE 'pg\_%' ESCAPE '\'
                AND n.nspname <> 'information_schema'
           )
    ) THEN
        RAISE EXCEPTION 'El rol es propietario de una relación no permitida';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_proc p
         WHERE p.proowner = role_oid
           AND p.pronamespace IN (
             SELECT n.oid FROM pg_namespace n
              WHERE n.nspname NOT LIKE 'pg\_%' ESCAPE '\'
                AND n.nspname <> 'information_schema'
           )
    ) THEN
        RAISE EXCEPTION 'El rol es propietario de una función no permitida';
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
