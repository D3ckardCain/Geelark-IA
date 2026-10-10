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


def relative_luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground, background):
    lighter, darker = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


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

    def test_navigation_exposes_current_page_accessibly(self):
        self.assertIn('aria-current="page"', self.html)
        self.assertIn('setAttribute("aria-current","page")', self.html)
        self.assertIn('removeAttribute("aria-current")', self.html)
        self.assertIn('aria-label="Navegación principal"', self.html)

    def test_navigation_handler_has_valid_block_structure(self):
        self.assertIn('forEach(el=>{el.classList.toggle("active",el.dataset.page===page);if(el.dataset.page===page)', self.html)
        self.assertNotIn('forEach(el=>el.classList.toggle("active",el.dataset.page===page);if(el.dataset.page===page)', self.html)

    def test_table_headers_and_decorative_icons_are_accessible(self):
        self.assertGreaterEqual(self.html.count('scope="col"'), 20)
        self.assertIn('<div class="nodeicon" aria-hidden="true">▣</div>', self.html)
        self.assertIn('<span aria-hidden="true">▦</span>', self.html)

    def test_tables_have_screen_reader_captions(self):
        self.assertEqual(self.html.count('<caption class="sr-only">'), 4)
        self.assertIn(".sr-only{position:absolute", self.html)
        self.assertIn("Resultados de CI de muestra, no consultados en vivo", self.html)

    def test_key_text_color_pairs_meet_wcag_aa_contrast(self):
        def resolve(value):
            value = value.strip()
            if value.startswith("var(") and value.endswith(")"):
                variable = value[4:-1].strip()
                match = re.search(rf"{re.escape(variable)}:(#[0-9a-fA-F]{{6}})", self.html)
                self.assertIsNotNone(match, f"Missing CSS variable {variable}")
                return match.group(1)
            self.assertRegex(value, r"^#[0-9a-fA-F]{6}$")
            return value

        def rule_value(selector, property_name):
            rule = re.search(re.escape(selector) + r"\{([^}]*)\}", self.html)
            self.assertIsNotNone(rule, f"Missing CSS rule {selector}")
            declaration = re.search(rf"(?:^|;){re.escape(property_name)}:([^;]+)", rule.group(1))
            self.assertIsNotNone(declaration, f"Missing {property_name} in {selector}")
            return resolve(declaration.group(1))

        pairs = [
            (resolve("var(--text)"), resolve("var(--bg)")),
            (resolve("var(--muted)"), resolve("var(--panel)")),
            (resolve("var(--muted)"), resolve("var(--bg)")),
            (resolve("var(--blue)"), resolve("var(--panel)")),
            (rule_value(".pill.green", "color"), rule_value(".pill.green", "background")),
            (rule_value(".pill.yellow", "color"), rule_value(".pill.yellow", "background")),
            (rule_value(".pill.red", "color"), rule_value(".pill.red", "background")),
            (rule_value(".demo", "color"), rule_value(".demo", "background")),
            (rule_value(".demo p", "color"), rule_value(".demo", "background")),
            (rule_value(".btn", "color"), rule_value(".btn", "background")),
        ]
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(contrast_ratio(foreground, background), 4.5)

    def test_rendered_dynamic_values_are_html_escaped(self):
        self.assertIn('function escapeHTML(value)', self.html)
        for expression in ('escapeHTML(n.name)', 'escapeHTML(n.role)', 'escapeHTML(n.last)',
                           'escapeHTML(n.cpu)', 'escapeHTML(n.ram)', 'escapeHTML(n.agent)',
                           'escapeHTML(m.name)', 'escapeHTML(m.node)', 'escapeHTML(m.version)',
                           'escapeHTML(m.time)', 'escapeHTML(m.source)'):
            with self.subTest(expression=expression):
                self.assertIn(expression, self.html)
        self.assertIn('escapeHTML(labelOverride||statusLabel[status]||status)', self.html)

    def test_keyboard_focus_indicator_exists(self):
        self.assertIn(':focus-visible', self.html)
        self.assertIn('outline-offset:2px', self.html)

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
