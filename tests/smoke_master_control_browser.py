"""Exercise the dashboard in headless Chrome/Chromium at desktop and mobile sizes."""
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

HTML_FILE = Path(__file__).resolve().parents[1] / "prototypes" / "master-control" / "index.html"

TEST_SCRIPT = r"""
<script>
(async () => {
  await new Promise(resolve => setTimeout(resolve, 100));
  const result = {};
  const count = selector => document.querySelectorAll(selector).length;
  result.liveModeStartsEmpty = document.getElementById('overview-nodes').textContent.trim() === '';
  result.initialOverviewCurrent = document.querySelector('[data-page="overview"]').getAttribute('aria-current') === 'page';
  document.getElementById('demo-toggle').click();
  result.demoExplicitlyEnabled = document.getElementById('demo-toggle').getAttribute('aria-pressed') === 'true';
  document.querySelector('[data-page="nodes"]').click();
  result.nodeCount = count('#nodes-table tr');
  const search = document.getElementById('node-search');
  search.value = 'WORKER-DEMO-02';
  search.dispatchEvent(new Event('input', {bubbles: true}));
  result.searchCount = count('#nodes-table tr');
  result.searchMatch = document.getElementById('nodes-table').textContent.includes('WORKER-DEMO-02');
  search.value = '';
  search.dispatchEvent(new Event('input', {bubbles: true}));
  const originalName = demoSnapshots[0].node.display_name;
  demoSnapshots[0].node.display_name = '<img src=x onerror="window.__xss=true">';
  render();
  result.nodeXssEscaped = count('#overview-nodes img') === 0 && document.getElementById('overview-nodes').textContent.includes(demoSnapshots[0].node.display_name) && !window.__xss;
  demoSnapshots[0].node.display_name = originalName;
  document.querySelector('[data-page="modules"]').click();
  const originalModuleId = demoSnapshots[0].node.modules[0].module_id;
  demoSnapshots[0].node.modules[0].module_id = '<svg onload="window.__xss=true"></svg>';
  render();
  result.moduleXssEscaped = count('#modules-table svg') === 0 && document.getElementById('modules-table').textContent.includes(demoSnapshots[0].node.modules[0].module_id) && !window.__xss;
  demoSnapshots[0].node.modules[0].module_id = originalModuleId;
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
        self.results = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body" and attrs.get("data-browser-test-results"):
            self.results = json.loads(attrs["data-browser-test-results"])


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
                 "--virtual-time-budget=2000", "--dump-dom", test_file.resolve().as_uri()],
                check=True, capture_output=True, text=True, timeout=25,
            )
            parser = RenderedDOMParser()
            parser.feed(result.stdout)
            parser.close()
            if parser.results is None:
                raise AssertionError(f"{label}: no se publicaron los resultados de interacción")
            expected = {
                "liveModeStartsEmpty": True,
                "initialOverviewCurrent": True,
                "demoExplicitlyEnabled": True,
                "nodeCount": 2,
                "searchCount": 1,
                "searchMatch": True,
                "nodeXssEscaped": True,
                "moduleXssEscaped": True,
                "auditCurrent": True,
                "noHorizontalPageOverflow": True,
                "jsErrors": [],
            }
            if parser.results != expected:
                raise AssertionError(f"{label}: resultados inesperados: {parser.results!r}")
            print(f"{label}: estado vacío seguro, modo demo explícito, navegación, búsqueda, escape HTML y layout OK")
    print("Browser smoke test OK: HTML real probado en Chrome/Chromium a 1440x900 y 390x844.")

if __name__ == "__main__":
    main()
