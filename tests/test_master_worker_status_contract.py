"""Dependency-free tests for the versioned Master/Worker status contract."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "contracts" / "master-worker-status-v1.schema.json"
EXAMPLE_PATH = ROOT / "docs" / "contracts" / "examples" / "master-worker-status-v1.example.json"


def _matches_type(value, expected):
    types = expected if isinstance(expected, list) else [expected]
    for item in types:
        if item == "null" and value is None:
            return True
        if item == "object" and isinstance(value, dict):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
    return False


def validate_subset(value, schema, path="$"):
    """Validate the JSON Schema keywords used by this contract; not a full JSON Schema engine."""
    errors = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value is outside the allowed enum")
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append(f"{path}: wrong type, expected {expected_type!r}")
        return errors
    if value is None:
        return errors

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required property is missing")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(f"{path}.{key}: unknown property")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_subset(value[key], child_schema, f"{path}.{key}"))
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len(value) != len({json.dumps(item, sort_keys=True) for item in value}):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(validate_subset(item, schema["items"], f"{path}[{index}]"))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is too short")
        if len(value) > schema.get("maxLength", len(value)):
            errors.append(f"{path}: string is too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: string does not match pattern")
        if schema.get("format") == "uuid":
            try:
                uuid.UUID(value)
            except (ValueError, AttributeError):
                errors.append(f"{path}: invalid UUID")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone required")
            except ValueError:
                errors.append(f"{path}: invalid date-time")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", value):
            errors.append(f"{path}: below minimum")
        if value > schema.get("maximum", value):
            errors.append(f"{path}: above maximum")
    return errors


class MasterWorkerStatusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_schema_and_example_are_valid_json(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], "1.0")
        self.assertEqual(self.schema["additionalProperties"], False)

    def test_example_conforms_to_contract_subset(self):
        self.assertEqual(validate_subset(self.example, self.schema), [])

    def test_contract_keeps_authorization_health_and_freshness_separate(self):
        node = self.example["node"]
        self.assertIn("authorization_state", node)
        self.assertIn("health_state", node)
        self.assertIn("freshness", self.example)
        self.assertNotEqual(node["authorization_state"], node["health_state"])

    def test_capability_allowlist_excludes_remote_execution(self):
        allowed = self.schema["properties"]["node"]["properties"]["capabilities"]["items"]["enum"]
        self.assertNotIn("task-execution", allowed)
        self.assertNotIn("shell", allowed)
        self.assertNotIn("adb", allowed)

    def test_rejects_unknown_top_level_secret_field(self):
        candidate = deepcopy(self.example)
        candidate["access_token"] = "never-store-secrets"
        self.assertTrue(any("unknown property" in error for error in validate_subset(candidate, self.schema)))

    def test_rejects_unsupported_execution_capability(self):
        candidate = deepcopy(self.example)
        candidate["node"]["capabilities"].append("shell")
        self.assertTrue(any("allowed enum" in error for error in validate_subset(candidate, self.schema)))

    def test_rejects_unknown_module_state(self):
        candidate = deepcopy(self.example)
        candidate["node"]["modules"][0]["state"] = "success"
        self.assertTrue(any("allowed enum" in error for error in validate_subset(candidate, self.schema)))

    def test_rejects_negative_freshness_age(self):
        candidate = deepcopy(self.example)
        candidate["freshness"]["age_seconds"] = -1
        self.assertTrue(any("below minimum" in error for error in validate_subset(candidate, self.schema)))

    def test_pending_unknown_states_remain_explicit(self):
        candidate = deepcopy(self.example)
        candidate["node"]["authorization_state"] = "pending"
        candidate["node"]["health_state"] = "unknown"
        self.assertEqual(validate_subset(candidate, self.schema), [])
        self.assertEqual(candidate["node"]["authorization_state"], "pending")
        self.assertEqual(candidate["node"]["health_state"], "unknown")


if __name__ == "__main__":
    unittest.main()
