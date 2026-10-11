from cluster_agent_transport.policy import AgentPrincipal, Operation, PermissionDenied, authorize_operation


def principal(admin_state="pending", credential_status="pending"):
    return AgentPrincipal("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222", admin_state, credential_status)


def test_pending_can_only_send_telemetry_and_read_status():
    for operation in (Operation.HEARTBEAT, Operation.CAPABILITIES, Operation.STATUS_READ):
        authorize_operation(principal(), operation)
    for operation in (Operation.TASK_ACCEPT, Operation.TASK_PROGRESS, Operation.TASK_RESULT, Operation.RECONCILE):
        try:
            authorize_operation(principal(), operation)
        except PermissionDenied:
            pass
        else:
            raise AssertionError(f"{operation} no debe permitirse a un nodo pending")


def test_active_node_can_use_agent_operations():
    active = principal("active", "active")
    for operation in Operation:
        authorize_operation(active, operation)


def test_inconsistent_or_revoked_states_fail_closed():
    for p in (principal("active", "pending"), principal("pending", "active"), principal("revoked", "revoked")):
        try:
            authorize_operation(p, Operation.HEARTBEAT)
        except PermissionDenied:
            pass
        else:
            raise AssertionError("Un estado inconsistente no debe autorizarse")

def test_all_revoked_expired_unknown_and_inconsistent_pairs_fail_closed():
    denied_principals = (
        principal("active", "revoked"),
        principal("pending", "revoked"),
        principal("revoked", "active"),
        principal("revoked", "pending"),
        principal("revoked", "revoked"),
        principal("active", "expired"),
        principal("pending", "expired"),
        principal("expired", "active"),
        principal("unknown", "active"),
        principal("active", "unknown"),
        principal("", "active"),
        principal("active", ""),
    )
    for p in denied_principals:
        for operation in Operation:
            try:
                authorize_operation(p, operation)
            except PermissionDenied:
                continue
            raise AssertionError(
                f"Estado no autorizado {p.admin_state}/{p.credential_status} "
                f"permitió {operation.value}"
            )
