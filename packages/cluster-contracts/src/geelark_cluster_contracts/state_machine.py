"""Reglas puras de transición de estado para instancias del clúster.

No controla procesos ni garantiza exclusión distribuida. La capa persistente
debe aplicar estas reglas dentro de una transacción y validar epochs/propiedad.
"""

from enum import StrEnum


class InstanceState(StrEnum):
    PENDING = "pending"
    RESERVED = "reserved"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"
    RECONCILING = "reconciling"


_ALLOWED_TRANSITIONS: dict[InstanceState, frozenset[InstanceState]] = {
    InstanceState.PENDING: frozenset({InstanceState.RESERVED, InstanceState.FAILED}),
    InstanceState.RESERVED: frozenset({
        InstanceState.STARTING,
        InstanceState.STOPPED,
        InstanceState.FAILED,
        InstanceState.UNKNOWN,
    }),
    InstanceState.STARTING: frozenset({
        InstanceState.RUNNING,
        InstanceState.FAILED,
        InstanceState.UNKNOWN,
    }),
    InstanceState.RUNNING: frozenset({
        InstanceState.STOPPING,
        InstanceState.UNKNOWN,
    }),
    InstanceState.STOPPING: frozenset({
        InstanceState.STOPPED,
        InstanceState.FAILED,
        InstanceState.UNKNOWN,
    }),
    InstanceState.STOPPED: frozenset({InstanceState.RESERVED}),
    InstanceState.FAILED: frozenset(),
    InstanceState.UNKNOWN: frozenset({InstanceState.RECONCILING}),
    InstanceState.RECONCILING: frozenset({
        InstanceState.RUNNING,
        InstanceState.STOPPED,
        InstanceState.FAILED,
        InstanceState.UNKNOWN,
    }),
}


def can_transition(current: InstanceState | str, target: InstanceState | str) -> bool:
    """Indica si la transición es válida según la máquina de estados del MVP."""
    try:
        current_state = InstanceState(current)
        target_state = InstanceState(target)
    except ValueError:
        return False
    return target_state in _ALLOWED_TRANSITIONS[current_state]


def require_transition(current: InstanceState | str, target: InstanceState | str) -> InstanceState:
    """Devuelve el estado objetivo o lanza ValueError si la transición no está permitida."""
    current_state = InstanceState(current)
    target_state = InstanceState(target)
    if target_state not in _ALLOWED_TRANSITIONS[current_state]:
        raise ValueError(
            f"Transición de estado no permitida: {current_state.value} -> {target_state.value}"
        )
    return target_state
