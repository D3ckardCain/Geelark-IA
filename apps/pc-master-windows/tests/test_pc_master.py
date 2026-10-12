import importlib.util
import sys
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "pc_master.py"
spec = importlib.util.spec_from_file_location("pc_master", APP)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DsnSafetyTests(unittest.TestCase):
    def test_accepts_passwordless_local_dsn(self):
        self.assertTrue(module._safe_dsn("postgresql://geelark_master_reader@localhost:5432/geelark?sslmode=disable"))

    def test_rejects_password_in_uri(self):
        self.assertFalse(module._safe_dsn("postgresql://reader:secret@localhost:5432/geelark"))

    def test_rejects_password_keyword(self):
        self.assertFalse(module._safe_dsn("host=localhost user=reader password=secret dbname=geelark"))

    def test_rejects_empty_dsn(self):
        self.assertFalse(module._safe_dsn("   "))


if __name__ == "__main__":
    unittest.main()
