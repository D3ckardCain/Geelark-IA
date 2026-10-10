"""Errores de dominio de la persistencia del clúster."""


class AssignmentError(Exception):
    """Error esperado al intentar reservar una instancia."""


class InvalidAssignmentRequest(AssignmentError):
    """La solicitud no cumple las reglas de entrada."""


class IdempotencyConflict(AssignmentError):
    """La clave idempotente ya fue usada con otro payload."""


class IdempotencyRecordIncomplete(AssignmentError):
    """Existe una clave idempotente sin respuesta final persistida."""


class InstanceNotFound(AssignmentError):
    """La instancia no está registrada."""


class InstanceAlreadyAssigned(AssignmentError):
    """La instancia ya tiene propietario o reserva vigente."""


class InstanceStateBlocked(AssignmentError):
    """El estado incierto impide una nueva asignación."""


class NodeNotEligible(AssignmentError):
    """El nodo no está autorizado/operativo para recibir asignaciones."""


class NodeCapacityNotConfigured(AssignmentError):
    """El nodo no tiene una capacidad reservable configurada."""


class InsufficientCapacity(AssignmentError):
    """La asignación superaría la capacidad reservable del nodo."""
