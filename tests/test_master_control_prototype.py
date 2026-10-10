"""Static regression tests for the standalone Master/Workers demo.

Run from the repository root with:
    python -m unittest tests/test_master_control_prototype.py
Only Python's standard library is required.
"""
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

    def test_visible_demo_and_read_only_warnings(self):
        self.assertIn("Modo demostración: datos ficticios", self.html)
        self.assertIn("No envía órdenes ni modifica equipos", self.html)

    def test_no_network_apis_or_calls(self):
        patterns = [
            r"\bfetch\s*\(",
            r"\bXMLHttpRequest\b",
            r"\bWebSocket\b",
            r"\bEventSource\b",
        ]
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.html))
        self.assertEqual(self.parser.external_resources, [])

    def test_element_ids_are_unique(self):
        ids = self.parser.ids
        self.assertEqual(len(ids), len(set(ids)), "HTML contains duplicate IDs")

    def test_javascript_dom_references_exist(self):
        ids = set(self.parser.ids)
        refs = re.findall(r'getElementById\(["\']([^"\']+)["\']\)', self.html)
        self.assertTrue(refs, "Expected getElementById references")
        self.assertEqual(sorted(set(refs) - ids), [])

    def test_master_is_not_listed_as_worker(self):
        self.assertIn('n.id!=="master"', self.html)

    def test_required_views_and_filters_exist(self):
        ids = set(self.parser.ids)
        for page in ("overview", "nodes", "modules", "audit"):
            with self.subTest(page=page):
                self.assertIn("page-" + page, ids)
        for element_id in ("node-search", "node-filter", "module-search", "module-filter"):
            with self.subTest(element_id=element_id):
                self.assertIn(element_id, ids)


if __name__ == "__main__":
    unittest.main()
