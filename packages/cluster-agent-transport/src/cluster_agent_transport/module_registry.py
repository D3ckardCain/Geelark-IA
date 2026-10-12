"""Lista cerrada de módulos que puede declarar un agente Worker."""
from datetime import timedelta

SUPPORTED_MODULE_IDS = frozenset({
    "agent-supervisor", "agent-transport", "agent-guard", "task-journal", "android-engine",
})
MODULE_REPORT_STALE_AFTER = timedelta(minutes=5)
