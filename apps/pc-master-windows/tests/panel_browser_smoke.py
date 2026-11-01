"""Aceptación UI en navegador real con fixtures aislados; ejecutar directamente en CI."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[3]
HTML = (ROOT / "packages/cluster-master-admin/src/geelark_master_admin/panel.html").read_text(encoding="utf-8")
OUTPUT = ROOT / "panel-ui-artifacts"


def main():
    OUTPUT.mkdir(exist_ok=True)
    profile = {"configured": True, "name": "Perfil de prueba", "busy": False,
               "phase": "ready", "message": "Listo para conectar", "screen_open": False}
    snapshots = {"schema_version": "1.0", "snapshots": [{
        "generated_at": "2026-11-01T12:00:00Z", "freshness": {"state": "fresh", "age_seconds": 5},
        "node": {"node_id": "11111111-1111-4111-8111-111111111111", "display_name": "Equipo de prueba",
                 "authorization_state": "active", "health_state": "healthy", "reported_health_state": "healthy",
                 "last_heartbeat_at": "2026-11-01T11:59:55Z", "agent_version": "internal-agent", "modules": [], "capabilities": []}}]}
    task = {"task_id": "22222222-2222-4222-8222-222222222222", "node_id": snapshots["snapshots"][0]["node"]["node_id"],
            "status": "succeeded", "created_at": "2026-11-01T11:59:00Z", "completed_at": "2026-11-01T12:00:00Z"}
    posted = []
    authenticated = True
    logout_fail = True

    def route_request(route):
        nonlocal authenticated, logout_fail
        path = route.request.url.split("https://panel.test", 1)[1].split("?", 1)[0]
        if path == "/":
            route.fulfill(status=200, content_type="text/html", body=HTML)
            return
        if path == "/admin/v1/session":
            data = {"authenticated": authenticated}
        elif path == "/admin/v1/status/snapshots":
            data = snapshots
        elif path == "/admin/v1/android":
            data = profile
        elif path == "/admin/v1/android/actions":
            posted.append(route.request.post_data_json)
            data = {}
        elif path == "/admin/v1/tasks":
            data = {"schema_version": "1.0", "generated_at": "2026-11-01T12:00:00Z", "tasks": [task], "has_more": False}
        elif path == "/admin/v1/logout":
            if logout_fail:
                logout_fail = False
                route.fulfill(status=503, content_type="application/json", body="{}")
                return
            authenticated = False
            data = {"authenticated": False}
        else:
            route.fulfill(status=404, body="Not found")
            return
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768}, locale="es-MX")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("https://panel.test/**", route_request)
        page.goto("https://panel.test/")
        expect(page.locator("#login-gate")).to_be_hidden()
        expect(page.locator("#android-profile-row")).to_be_visible()
        page.screenshot(path=str(OUTPUT / "perfiles-desktop.png"), full_page=True)
        page.locator("#profile-search").fill("no existe")
        expect(page.locator("#android-profile-row")).to_be_hidden()
        expect(page.locator("#profiles-empty")).to_contain_text("No hay perfiles")
        page.locator("#profile-search").fill("PRUEBA")
        expect(page.locator("#android-profile-row")).to_be_visible()
        page.locator("#profile-state").select_option("open")
        expect(page.locator("#android-profile-row")).to_be_hidden()
        page.locator("#profile-state").select_option("closed")
        expect(page.locator("#android-profile-row")).to_be_visible()
        page.locator("#android-open").click()
        page.wait_for_function("!document.getElementById('android-open').disabled")
        assert posted == [{"action": "open"}]
        page.locator("#android-recover").click()
        expect(page.locator("#android-recovery")).to_be_visible()
        page.locator("#recovery-password").fill("fixture-password")
        page.locator("#recovery-cancel").click()
        expect(page.locator("#recovery-password")).to_have_value("")
        assert len(posted) == 1
        for section in ["nodes", "tasks", "system"]:
            page.locator(f'[data-page="{section}"]').click()
            expect(page.locator(f"#page-{section}")).to_be_visible()
            if section == "tasks":
                expect(page.locator("#tasks-node option")).to_have_count(2)
                expect(page.locator("#tasks-table")).to_contain_text("Equipo de prueba")
            page.screenshot(path=str(OUTPUT / f"{section}-desktop.png"), full_page=True)
        assert "GitHub Actions" not in page.locator("body").inner_text()
        assert "PostgreSQL" not in page.locator("body").inner_text()
        page.locator('[data-page="android"]').click()
        for width in [960, 390]:
            page.set_viewport_size({"width": width, "height": 800})
            expect(page.locator("#android-open")).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            for control in ["android-open", "android-disconnect", "android-recover"]:
                rect = page.locator(f"#{control}").bounding_box()
                assert rect and rect["x"] >= 0 and rect["x"] + rect["width"] <= width, (width, control, rect)
            page.screenshot(path=str(OUTPUT / f"perfiles-{width}.png"), full_page=True)
        page.locator("#logout").click()
        expect(page.locator("#session-notice")).to_be_visible()
        expect(page.locator("#login-gate")).to_be_hidden()
        page.locator("#logout").click()
        expect(page.locator("#login-gate")).to_be_visible()
        expect(page.locator("#android-profile-row")).to_be_hidden()
        assert not errors, errors
        browser.close()
    print("UI: filtros, acciones, recuperación/cancelación, navegación, sesión y anchos 1366/960/390 correctos.")


if __name__ == "__main__":
    main()
