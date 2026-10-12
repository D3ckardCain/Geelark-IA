-- Agent enrollment and per-node credentials for the private control plane.
-- No tokens or credential secrets are stored in this schema.
BEGIN;

CREATE TABLE geelark_control.node_enrollments (
    enrollment_id uuid PRIMARY KEY,
    expected_node_id uuid NOT NULL,
    token_sha256 char(64) NOT NULL UNIQUE
        CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
    created_by varchar(128) NOT NULL CHECK (length(trim(created_by)) > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    revoked_at timestamptz,
    CHECK (expires_at > created_at),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    CHECK (NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL))
);

CREATE INDEX node_enrollments_expected_expiry_idx
    ON geelark_control.node_enrollments(expected_node_id, expires_at);
CREATE INDEX node_enrollments_expiry_cleanup_idx
    ON geelark_control.node_enrollments(expires_at)
    WHERE consumed_at IS NULL AND revoked_at IS NULL;

CREATE TABLE geelark_control.node_credentials (
    credential_id uuid PRIMARY KEY,
    node_id uuid NOT NULL REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    token_sha256 char(64) NOT NULL UNIQUE
        CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL
        CHECK (status IN ('pending', 'active', 'revoked', 'expired')),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    activated_at timestamptz,
    revoked_at timestamptz,
    last_used_at timestamptz,
    replaces_credential_id uuid,
    UNIQUE (credential_id, node_id),
    FOREIGN KEY (replaces_credential_id, node_id)
        REFERENCES geelark_control.node_credentials(credential_id, node_id)
        ON DELETE RESTRICT,
    CHECK (expires_at > created_at),
    CHECK (activated_at IS NULL OR activated_at >= created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    CHECK (
        (status = 'revoked' AND revoked_at IS NOT NULL)
        OR (status <> 'revoked' AND revoked_at IS NULL)
    ),
    CHECK (
        (status = 'pending' AND activated_at IS NULL)
        OR (status IN ('active', 'expired') AND activated_at IS NOT NULL)
        OR status = 'revoked'
    ),
    CHECK (replaces_credential_id IS NULL OR replaces_credential_id <> credential_id)
);

CREATE UNIQUE INDEX one_active_credential_per_node
    ON geelark_control.node_credentials(node_id)
    WHERE status = 'active';
CREATE UNIQUE INDEX one_pending_credential_rotation_per_node
    ON geelark_control.node_credentials(node_id)
    WHERE status = 'pending';
CREATE INDEX node_credentials_node_status_idx
    ON geelark_control.node_credentials(node_id, status);
CREATE INDEX node_credentials_expiry_idx
    ON geelark_control.node_credentials(expires_at)
    WHERE status IN ('active', 'pending');

CREATE TABLE geelark_control.agent_request_nonces (
    node_id uuid NOT NULL REFERENCES geelark_control.nodes(node_id) ON DELETE RESTRICT,
    nonce uuid NOT NULL,
    credential_id uuid NOT NULL,
    request_id uuid NOT NULL,
    seen_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (node_id, nonce),
    FOREIGN KEY (credential_id, node_id)
        REFERENCES geelark_control.node_credentials(credential_id, node_id)
        ON DELETE RESTRICT,
    CHECK (expires_at > seen_at)
);

CREATE INDEX agent_request_nonces_expiry_idx
    ON geelark_control.agent_request_nonces(expires_at);

COMMENT ON TABLE geelark_control.node_enrollments IS
    'Tokens de enrolamiento: solo hash SHA-256, vencimiento y consumo atómico; nunca almacenar el secreto en claro.';
COMMENT ON TABLE geelark_control.node_credentials IS
    'Credenciales opacas individuales por nodo. La autorización también debe comprobar estado del nodo y expiración.';
COMMENT ON TABLE geelark_control.agent_request_nonces IS
    'Bloquea la repetición exacta de un nonce por nodo; no sustituye la protección contra robo de credenciales.';

COMMIT;
