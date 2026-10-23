"""Contract drift tests using only the Python standard library."""
import json
from pathlib import Path

from cluster_agent_transport.module_registry import SUPPORTED_MODULE_IDS

ROOT = Path(__file__).resolve().parents[3]


def test_module_inventory_schema_matches_closed_code_registry():
    schema = json.loads((ROOT / "docs/contracts/worker-module-inventory-v1.schema.json").read_text())
    ids = schema["properties"]["modules"]["items"]["properties"]["module_id"]["enum"]
    assert ids == sorted(SUPPORTED_MODULE_IDS)
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["modules"]["maxItems"] == 32


def test_module_inventory_example_uses_only_allowed_fields_and_ids():
    example = json.loads((ROOT / "docs/contracts/examples/worker-module-inventory-v1.example.json").read_text())
    assert set(example) == {"schema_version", "modules"}
    assert example["schema_version"] == 1
    ids = [item["module_id"] for item in example["modules"]]
    assert len(ids) == len(set(ids))
    assert set(ids) <= SUPPORTED_MODULE_IDS
    assert all(set(item) <= {"module_id", "state", "version", "error_code"} for item in example["modules"])
