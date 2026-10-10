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
        pairs = [
            ("#edf3ff", "#0b1020"),  # Texto principal sobre fondo
            ("#9caec8", "#121a2c"),  # Texto secundario sobre panel
            ("#9caec8", "#0b1020"),  # Texto secundario sobre fondo
            ("#8db7ff", "#121a2c"),  # Azul sobre panel
            ("#70ddb0", "#153329"),  # Estado verde
            ("#f5cd79", "#332b1b"),  # Estado amarillo
            ("#ff9299", "#351f2a"),  # Estado rojo
            ("#f8dfaa", "#2a2418"),  # Aviso de demostración
            ("#ddcda7", "#2a2418"),  # Texto secundario del aviso
            ("#edf3ff", "#1a2941"),  # Texto de botones
        ]
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(contrast_ratio(foreground, background), 4.5)

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
