"""Run a browser smoke test against the real standalone HTML file.

Uses a browser already installed on the runner and Python's standard library.
No browser packages, external URLs, or network requests are required.
"""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys


HTML_FILE = Path(__file__).resolve().parents[1] / "prototypes" / "master-control" / "index.html"


class RenderedDOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.overview_rows = 0
        self.in_overview = False
        self.current_page = False
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tbody" and attrs.get("id") == "overview-nodes":
            self.in_overview = True
        if tag == "tr" and self.in_overview:
            self.overview_rows += 1
        if tag == "button" and attrs.get("data-page") == "overview" and attrs.get("aria-current") == "page":
            self.current_page = True

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
    url = HTML_FILE.resolve().as_uri()
    result = subprocess.run(
        [browser, "--headless", "--no-sandbox", "--disable-gpu",
         "--disable-dev-shm-usage", "--virtual-time-budget=1500", "--dump-dom", url],
        check=True, capture_output=True, text=True, timeout=25,
    )
    parser = RenderedDOMParser()
    parser.feed(result.stdout)
    parser.close()
    rendered_text = " ".join(parser._text)
    failures = []
    if parser.overview_rows != 3:
        failures.append(f"Se esperaban 3 Workers en Resumen; aparecieron {parser.overview_rows}.")
    if not parser.current_page:
        failures.append("La vista Resumen no está marcada como activa en el DOM renderizado.")
    if "Modo demostración: datos ficticios" not in rendered_text:
        failures.append("No aparece el aviso visible de datos ficticios.")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("Browser smoke test OK: HTML real abierto en Chrome/Chromium; 3 Workers, aviso demo y navegación activa presentes.")


if __name__ == "__main__":
    main()
