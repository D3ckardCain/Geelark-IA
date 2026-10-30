-- Ejecutar una sola vez como administrador PostgreSQL en la base GeeLark-IA.
-- No incluye contraseña. Después de crear el rol, configure la contraseña de forma interactiva:
--   psql "$ADMIN_DSN" -v ON_ERROR_STOP=1 -f packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql
--   psql "$ADMIN_DSN" y luego: \password geelark_master_reader
-- Nunca coloque la contraseña en Git, comandos shell ni logs.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'geelark_master_reader') THEN
        EXECUTE 'CREATE ROLE geelark_master_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS';
    END IF;
END
$$;

ALTER ROLE geelark_master_reader
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
ALTER ROLE geelark_master_reader SET default_transaction_read_only = on;
ALTER ROLE geelark_master_reader SET statement_timeout = '1500ms';
ALTER ROLE geelark_master_reader SET lock_timeout = '500ms';
ALTER ROLE geelark_master_reader SET idle_in_transaction_session_timeout = '5000ms';

DO $grant$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO geelark_master_reader', current_database());
END
$grant$;

REVOKE ALL PRIVILEGES ON SCHEMA geelark_control FROM geelark_master_reader;
GRANT USAGE ON SCHEMA geelark_control TO geelark_master_reader;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA geelark_control FROM geelark_master_reader;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA geelark_control FROM geelark_master_reader;
GRANT SELECT ON TABLE geelark_control.nodes TO geelark_master_reader;
-- Metadatos exclusivamente; payload y result_summary permanecen inaccesibles.
GRANT SELECT (task_id, operation_id, node_id, instance_id, assignment_epoch, status, delivery_attempts, created_at, updated_at, delivered_at, accepted_at, completed_at, last_error_code)
    ON TABLE geelark_control.agent_tasks TO geelark_master_reader;

COMMIT;
