"""Deterministic in-memory runtime simulator for control-plane tests only.

This module never starts processes, containers, emulators, or network services.
It is deliberately not a production Android runtime adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from uuid import UUID, uuid4

from .state_machine import InstanceState, require_transition


class SimulatorError(RuntimeError):
    """Base class for expected simulator rejections."""


class StaleAssignmentEpoch(SimulatorError):
    """The command epoch does not match the epoch registered for the instance."""


class IdempotencyConflict(SimulatorError):
    """An idempotency key was reused for a different logical command."""


class UnsupportedSimulationOperation(SimulatorError):
    """The simulator intentionally supports only start and stop."""


@dataclass(frozen=True)
class SimulationResult:
    operation_id: UUID
    instance_id: UUID
    assignment_epoch: int
    desired_state: str
    observed_state: InstanceState
    changed: bool


@dataclass(frozen=True)
class SimulationSnapshot:
    instance_id: UUID
    assignment_epoch: int
    observed_state: InstanceState


class RuntimeSimulator:
    """In-memory fake adapter with epoch fencing and idempotency.

    Instances and results live only in this Python object's memory. Restarting
    the process loses all state; this is a test double, not durable storage.
    """

    def __init__(self) -> None:
        self._instances: dict[UUID, tuple[int, InstanceState]] = {}
        self._idempotency: dict[str, tuple[str, SimulationResult]] = {}

    def register_instance(
        self, instance_id: UUID, assignment_epoch: int, *,
        initial_state: InstanceState = InstanceState.STOPPED,
    ) -> None:
        """Register a fixture with a known epoch; production ownership is external."""
        if assignment_epoch < 1:
            raise ValueError("assignment_epoch debe ser >= 1")
        if instance_id in self._instances:
            raise ValueError("La instancia ya está registrada en este simulador")
        if initial_state not in {InstanceState.STOPPED, InstanceState.RUNNING}:
            raise ValueError("El estado inicial debe ser stopped o running")
        self._instances[instance_id] = (assignment_epoch, initial_state)

    def inspect(self, instance_id: UUID) -> SimulationSnapshot:
        """Return current simulated state without inventing an operation ID."""
        epoch, state = self._require_instance(instance_id)
        return SimulationSnapshot(
            instance_id=instance_id,
            assignment_epoch=epoch,
            observed_state=state,
        )

    def execute(
        self,
        instance_id: UUID,
        *,
        assignment_epoch: int,
        desired_state: str,
        idempotency_key: str,
    ) -> SimulationResult:
        if desired_state not in {"running", "stopped"}:
            raise UnsupportedSimulationOperation(
                "El simulador solo admite desired_state=running o stopped"
            )
        if not 16 <= len(idempotency_key) <= 200:
            raise ValueError("idempotency_key debe tener entre 16 y 200 caracteres")

        fingerprint = sha256(json.dumps({
            "instance_id": str(instance_id),
            "assignment_epoch": assignment_epoch,
            "desired_state": desired_state,
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

        previous = self._idempotency.get(idempotency_key)
        if previous is not None:
            previous_fingerprint, previous_result = previous
            if previous_fingerprint != fingerprint:
                raise IdempotencyConflict(
                    "La clave de idempotencia ya se usó con otro payload"
                )
            return previous_result

        epoch, current = self._require_instance(instance_id)
        if assignment_epoch != epoch:
            raise StaleAssignmentEpoch(
                f"Epoch recibido {assignment_epoch}; epoch vigente {epoch}"
            )

        target = InstanceState(desired_state)
        changed = current != target
        if changed:
            if current in {InstanceState.UNKNOWN, InstanceState.RECONCILING}:
                raise SimulatorError("La instancia requiere reconciliación explícita")
            if target == InstanceState.RUNNING:
                path = (InstanceState.RESERVED, InstanceState.STARTING, InstanceState.RUNNING)
            else:
                path = (InstanceState.STOPPING, InstanceState.STOPPED)
            state = current
            for next_state in path:
                state = require_transition(state, next_state)
            self._instances[instance_id] = (epoch, state)
        else:
            state = current

        result = SimulationResult(
            operation_id=uuid4(),
            instance_id=instance_id,
            assignment_epoch=epoch,
            desired_state=desired_state,
            observed_state=state,
            changed=changed,
        )
        self._idempotency[idempotency_key] = (fingerprint, result)
        return result

    def _require_instance(self, instance_id: UUID) -> tuple[int, InstanceState]:
        try:
            return self._instances[instance_id]
        except KeyError as exc:
            raise SimulatorError("Instancia no registrada en el simulador") from exc
