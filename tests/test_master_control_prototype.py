"""Regression checks for the read-only live-snapshot dashboard."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

HTML_PATH = Path(__file__).resolve().parents[1] / "prototypes" / "master-control" / "index.html"


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.external_resources = []
        self.lang = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag in {"script", "link", "img", "iframe"}:
            for attr in ("src", "href"):
                value = attrs.get(attr, "")
                if value.startswith(("http://", "https://", "//")):
                    self.external_resources.append((tag, attr, value))


class MasterControlPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.parser = DocumentParser()
        cls.parser.feed(cls.html)
        cls.parser.close()

    def test_html5_document_in_spanish(self):
        self.assertTrue(self.html.lower().lstrip().startswith("<!doctype html>"))
        self.assertEqual(self.parser.lang, "es")

    def test_live_mode_is_default_and_no_fake_data_is_injected(self):
        self.assertIn('const API_PATH="/admin/v1/status/snapshots"', self.html)
        self.assertIn("Esperando al servicio de control", self.html)
        self.assertIn("No se muestran datos de muestra automáticamente", self.html)
        self.assertIn('state.snapshots=[]', self.html)
        self.assertIn('id="demo-toggle"', self.html)

    def test_read_only_request_is_same_origin_and_not_cached(self):
        self.assertIn('method:"GET"', self.html)
        self.assertIn('credentials:"same-origin"', self.html)
        self.assertIn('cache:"no-store"', self.html)
        self.assertNotIn("XMLHttpRequest", self.html)
        self.assertNotIn("WebSocket", self.html)
        self.assertNotIn("EventSource", self.html)
        self.assertNotIn("localStorage", self.html)
        self.assertNotIn("sessionStorage", self.html)

    def test_endpoint_contract_and_live_api_limits_are_visible(self):
        self.assertIn("schema_version", self.html)
        self.assertIn("snapshots", self.html)
        self.assertIn("state.snapshots.length>500", self.html)
        self.assertIn("Autenticación/autorización requerida", self.html)
        self.assertIn("No se inventan nodos ni estados", self.html)

    def test_element_ids_are_unique(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)), "HTML contains duplicate IDs")

    def test_javascript_dom_references_exist(self):
        ids = set(self.parser.ids)
        refs = re.findall(r'getElementById\(["\']([^"\']+)["\']\)', self.html)
        self.assertTrue(refs, "Expected getElementById references")
        self.assertEqual(sorted(set(refs) - ids), [])

    def test_navigation_exposes_current_page_accessibly(self):
        self.assertIn('aria-current="page"', self.html)
        self.assertIn('setAttribute("aria-current","page")', self.html)
        self.assertIn('removeAttribute("aria-current")', self.html)
        self.assertIn('aria-label="Navegación principal"', self.html)

    def test_tables_have_accessible_headers_and_focus_styles(self):
        self.assertGreaterEqual(self.html.count('scope="col"'), 15)
        self.assertIn(":focus-visible", self.html)
        self.assertIn("outline-offset:2px", self.html)
        self.assertIn('aria-live="polite"', self.html)

    def test_remote_values_are_escaped_before_insertion(self):
        self.assertIn('function esc(value)', self.html)
        for expression in ("esc(n.display_name)", "esc(n.node_id)", "esc(s.freshness.age_seconds)",
                           "esc(m.module_id)", "esc(m.version)", "esc(m.source||\"unknown\")"):
            with self.subTest(expression=expression):
                self.assertIn(expression, self.html)

    def test_no_external_runtime_resources(self):
        self.assertEqual(self.parser.external_resources, [])
        self.assertIn('href="https://github.com/D3ckardCain/Geelark-IA/actions"', self.html)

    def test_demo_is_explicit_and_separate_from_live_data(self):
        self.assertIn("Ver ejemplo ficticio", self.html)
        self.assertIn('if(state.demo)return', self.html)
        self.assertIn("Ejemplo ficticio activado", self.html)

    def test_only_read_only_admin_endpoint_is_called(self):
        endpoints = re.findall(r'fetch\(([^)]*)\)', self.html)
        self.assertEqual(endpoints, ["API_PATH"])
        self.assertIn('const API_PATH="/admin/v1/status/snapshots"', self.html)
        self.assertNotIn("/admin/v1/reconcile", self.html)
        self.assertNotIn("/agent/v1/tasks/claim", self.html)


if __name__ == "__main__":
    unittest.main()
