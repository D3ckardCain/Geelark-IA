"""Exercise the actual standalone dashboard HTML in installed headless Chrome/Chromium.

The test adds a temporary test-only script to a temporary copy of the real HTML.
No browser packages, external URLs, or network requests are required.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile


HTML_FILE = Path(__file__).resolve().parents[1] / "prototypes" / "master-control" / "index.html"

TEST_SCRIPT = r"""
<script>
(() => {
  const result = {};
  const count = selector => document.querySelectorAll(selector).length;
  result.initialOverviewCurrent = document.querySelector('[data-page="overview"]').getAttribute('aria-current') === 'page';
  document.querySelector('[data-page="nodes"]').click();
  result.nodesCount = count('#nodes-table tr');
  result.masterExcluded = !document.getElementById('nodes-table').textContent.includes('PC-MASTER');
  const search = document.getElementById('node-search');
  search.value = 'WORKER-02';
  search.dispatchEvent(new Event('input', {bubbles: true}));
  result.searchCount = count('#nodes-table tr');
  search.value = '';
  search.dispatchEvent(new Event('input', {bubbles: true}));
  const nodeFilter = document.getElementById('node-filter');
  nodeFilter.value = 'pending';
  nodeFilter.dispatchEvent(new Event('change', {bubbles: true}));
  result.pendingCount = count('#nodes-table tr');
  result.pendingWorker = document.getElementById('nodes-table').textContent.includes('WORKER-03');
  nodeFilter.value = 'all';
  nodeFilter.dispatchEvent(new Event('change', {bubbles: true}));
  const worker2 = nodes.find(n => n.id === 'w2');
  const originalWorkerName = worker2.name;
  worker2.name = '<img src=x onerror="window.__xss=true">';
  renderNodes();
  result.nodeXssEscaped = count('#nodes-table img') === 0 && document.getElementById('nodes-table').textContent.includes(worker2.name) && !window.__xss;
  worker2.name = originalWorkerName;
  renderNodes();
  document.querySelector('[data-page="modules"]').click();
  const moduleFilter = document.getElementById('module-filter');
  const originalModuleName = modules[0].name;
  moduleFilter.value = 'all';
  moduleFilter.dispatchEvent(new Event('change', {bubbles: true}));
  modules[0].name = '<svg onload="window.__xss=true"></svg>';
  renderModules();
  result.moduleXssEscaped = count('#modules-table svg') === 0 && document.getElementById('modules-table').textContent.includes(modules[0].name) && !window.__xss;
  modules[0].name = originalModuleName;
  moduleFilter.value = 'unknown';
  moduleFilter.dispatchEvent(new Event('change', {bubbles: true}));
  result.unknownModules = count('#modules-table tr');
  document.querySelector('[data-page="audit"]').click();
  result.auditCurrent = document.querySelector('[data-page="audit"]').getAttribute('aria-current') === 'page';
  result.noHorizontalPageOverflow = document.documentElement.scrollWidth <= window.innerWidth;
  result.jsErrors = window.__browserErrors || [];
  document.body.setAttribute('data-browser-test-results', JSON.stringify(result));
})();
</script>
"""


class RenderedDOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.overview_rows = 0
        self.in_overview = False
        self.current_page = False
        self.demo_warning = False
        self.results = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tbody" and attrs.get("id") == "overview-nodes":
            self.in_overview = True
        if tag == "tr" and self.in_overview:
            self.overview_rows += 1
        if tag == "button" and attrs.get("data-page") == "overview" and attrs.get("aria-current") == "page":
            self.current_page = True
        if tag == "body" and attrs.get("data-browser-test-results"):
            self.results = json.loads(attrs["data-browser-test-results"])

    def handle_endtag(self, tag):
        if tag == "tbody" and self.in_overview:
            self.in_overview = False

    def handle_data(self, data):
        self._text.append(data)


def main():
    browser = next((shutil.which(name) for name in (
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"
    ) if shutil.which(name)), None)
    if browser is None:
        raise SystemExit("No se encontró Chrome/Chromium preinstalado en el runner.")
    source = HTML_FILE.read_text(encoding="utf-8")
    error_listener = (
        "<script>window.__browserErrors=[];"
        "window.addEventListener('error',e=>window.__browserErrors.push(String(e.message)));"
        "</script><script>"
    )
    if "<script>" not in source or "</body>" not in source:
        raise SystemExit("El HTML no contiene los puntos de inserción esperados.")
    source = source.replace("<script>", error_listener, 1)
    source = source.replace("</body>", TEST_SCRIPT + "</body>", 1)

    for label, size in (("desktop", "1440,900"), ("mobile", "390,844")):
        with tempfile.TemporaryDirectory(prefix="master-control-browser-") as temp_dir:
            test_file = Path(temp_dir) / "index.html"
            test_file.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [browser, "--headless", "--no-sandbox", "--disable-gpu",
                 "--disable-dev-shm-usage", f"--window-size={size}",
                 "--virtual-time-budget=1500", "--dump-dom", test_file.resolve().as_uri()],
                check=True, capture_output=True, text=True, timeout=25,
            )
            parser = RenderedDOMParser()
            parser.feed(result.stdout)
            parser.close()
            if parser.overview_rows != 3:
                raise AssertionError(f"{label}: se esperaban 3 Workers en Resumen; aparecieron {parser.overview_rows}")
            if "Modo demostración: datos ficticios" not in " ".join(parser._text):
                raise AssertionError(f"{label}: falta el aviso visible de datos ficticios")
            if parser.results is None:
                raise AssertionError(f"{label}: no se publicaron los resultados de interacción")
            expected = {
                "initialOverviewCurrent": True,
                "nodesCount": 3,
                "masterExcluded": True,
                "searchCount": 1,
                "pendingCount": 1,
                "pendingWorker": True,
                "unknownModules": 2,
                "nodeXssEscaped": True,
                "moduleXssEscaped": True,
                "auditCurrent": True,
                "noHorizontalPageOverflow": True,
                "jsErrors": [],
            }
            if parser.results != expected:
                raise AssertionError(f"{label}: resultados inesperados: {parser.results!r}")
            print(f"{label}: navegación, búsqueda, filtros, accesibilidad, 3 Workers y layout sin desbordamiento horizontal OK")
    print("Browser interaction smoke test OK: HTML real probado en Chrome/Chromium a 1440x900 y 390x844.")


if __name__ == "__main__":
    main()
