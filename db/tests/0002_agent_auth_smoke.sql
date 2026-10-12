-- Smoke tests for migration 0002_agent_auth.sql.
-- Run in the disposable PostgreSQL database after all migrations.
BEGIN;

INSERT INTO geelark_control.nodes (node_id, display_name, admin_state, health_state)
VALUES
 ('22222222-2222-4222-8222-222222222222', 'auth-node-a', 'pending', 'unknown'),
 ('33333333-3333-4333-8333-333333333333', 'auth-node-b', 'pending', 'unknown');

INSERT INTO geelark_control.node_credentials
    (credential_id, node_id, token_sha256, status, expires_at, activated_at)
VALUES
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '22222222-2222-4222-8222-222222222222',
  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  'active', now() + interval '30 days', now()),
 ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
  '33333333-3333-4333-8333-333333333333',
  'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  'active', now() + interval '30 days', now());

DO $$
BEGIN
    BEGIN
        INSERT INTO geelark_control.node_credentials
            (credential_id, node_id, token_sha256, status, expires_at, activated_at)
        VALUES
            ('cccccccc-cccc-4ccc-8ccc-cccccccccccc',
             '22222222-2222-4222-8222-222222222222',
             'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
             'active', now() + interval '30 days', now());
        RAISE EXCEPTION 'Expected one-active-credential constraint to fail';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

INSERT INTO geelark_control.node_credentials
    (credential_id, node_id, token_sha256, status, expires_at, replaces_credential_id)
VALUES
 ('dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  '22222222-2222-4222-8222-222222222222',
  'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
  'pending', now() + interval '30 days', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');

DO $$
BEGIN
    BEGIN
        INSERT INTO geelark_control.node_credentials
            (credential_id, node_id, token_sha256, status, expires_at, replaces_credential_id)
        VALUES
            ('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
             '22222222-2222-4222-8222-222222222222',
             'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
             'pending', now() + interval '30 days', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
        RAISE EXCEPTION 'Expected one-pending-rotation constraint to fail';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

INSERT INTO geelark_control.node_enrollments
    (enrollment_id, expected_node_id, token_sha256, created_by, expires_at)
VALUES
 ('ffffffff-ffff-4fff-8fff-ffffffffffff',
  '44444444-4444-4444-8444-444444444444',
  'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
  'admin-test', now() + interval '10 minutes');

UPDATE geelark_control.node_enrollments
   SET consumed_at = now()
 WHERE enrollment_id = 'ffffffff-ffff-4fff-8fff-ffffffffffff'
   AND consumed_at IS NULL
   AND revoked_at IS NULL
   AND expires_at > now();

DO $$
DECLARE affected integer;
BEGIN
    UPDATE geelark_control.node_enrollments
       SET consumed_at = now()
     WHERE enrollment_id = 'ffffffff-ffff-4fff-8fff-ffffffffffff'
       AND consumed_at IS NULL
       AND revoked_at IS NULL
       AND expires_at > now();
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 0 THEN
        RAISE EXCEPTION 'Consumed enrollment token must not be reusable';
    END IF;
END $$;

INSERT INTO geelark_control.agent_request_nonces
    (node_id, nonce, credential_id, request_id, expires_at)
VALUES
 ('22222222-2222-4222-8222-222222222222',
  '99999999-9999-4999-8999-999999999999',
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '11111111-1111-4111-8111-111111111111',
  now() + interval '5 minutes'),
 ('33333333-3333-4333-8333-333333333333',
  '99999999-9999-4999-8999-999999999999',
  'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
  '22222222-2222-4222-8222-222222222222',
  now() + interval '5 minutes');

DO $$
BEGIN
    BEGIN
        INSERT INTO geelark_control.agent_request_nonces
            (node_id, nonce, credential_id, request_id, expires_at)
        VALUES
            ('22222222-2222-4222-8222-222222222222',
             '99999999-9999-4999-8999-999999999999',
             'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
             '33333333-3333-4333-8333-333333333333',
             now() + interval '5 minutes');
        RAISE EXCEPTION 'Expected duplicate nonce for same node to fail';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

ROLLBACK;
