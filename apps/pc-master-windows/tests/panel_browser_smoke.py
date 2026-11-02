"""Aceptación UI en navegador real con fixtures aislados; ejecutar directamente en CI."""
import json
import base64
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[3]
HTML = (ROOT / "packages/cluster-master-admin/src/geelark_master_admin/panel.html").read_text(encoding="utf-8").replace(
    '<!-- OPTIONAL_DIAGNOSTICS -->', '<a id="android-diagnostics" class="btn" href="/diagnostics" target="_blank" rel="noopener">Diagnóstico</a>')
DIAGNOSTICS = (ROOT / "packages/cluster-master-admin/src/geelark_master_admin/diagnostics.html").read_text(encoding="utf-8")
OUTPUT = ROOT / "panel-ui-artifacts"


def embedded_screen_browser_test(browser, multiple=False):
    """Decodifica H.264 real (fixture roja propia), controla y desconecta sin otra ventana."""
    screen_id = 'a'*32
    inputs=[]
    actions=[]
    video_connections=[]
    diagnostic_requests=[]
    diagnostic_logs={'primary':'REGISTRO-ANDROID-01','c'*32:'REGISTRO-ANDROID-02'}
    stop=threading.Event()
    profile={'configured':True,'name':'Perfil integrado de prueba','busy':False,'phase':'ready',
             'message':'Pantalla iniciada','screen_open':True,'screen_id':screen_id}
    profile_id='c'*32
    second_profile=dict(profile,name='Segundo Android detectado',screen_id='b'*32,profile_id=profile_id,primary=False)
    second_prefix='#profile-'+profile_id+'-'
    config=base64.b64decode('AAAAAWdCwAraImwEQAAAAwBAAAADAKPEiagAAAABaM4PyA==')
    keyframe=base64.b64decode('AAAAAWWIhDoRigACGPHAAED2OAAIeUnXXXXXXg==')
    packets=[struct.pack('>III',0x80000000,32,64),struct.pack('>QI',1<<62,len(config))+config,
             struct.pack('>QI',1<<61,len(keyframe))+keyframe]
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def send_body(self,body,kind='application/json'):
            self.send_response(200);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path.startswith('/admin/v1/android/video?'):
                video_connections.append(self.path)
                self.send_response(200);self.send_header('Content-Type','application/x-ndjson')
                self.send_header('Transfer-Encoding','chunked');self.end_headers()
                try:
                    for packet in packets:
                        body=(json.dumps({'packet':base64.b64encode(packet).decode()})+'\n').encode()
                        self.wfile.write(f'{len(body):x}\r\n'.encode()+body+b'\r\n');self.wfile.flush()
                    while not stop.wait(.1):
                        self.wfile.write(b'1\r\n\n\r\n');self.wfile.flush()
                    self.wfile.write(b'0\r\n\r\n');self.wfile.flush()
                except (BrokenPipeError,ConnectionResetError):pass
                return
            inventory=dict(profile,profiles=[dict(profile,primary=True,profile_id='d'*32),second_profile],discovery={'busy':False,'phase':'ready','message':'2 Android detectados en el worker'}) if multiple else profile
            data={'authenticated':True} if self.path=='/admin/v1/session' else inventory if self.path=='/admin/v1/android' else {'snapshots':[],'tasks':[]}
            path=urlsplit(self.path);query=parse_qs(path.query)
            if path.path=='/diagnostics':
                self.send_body(DIAGNOSTICS.encode(),'text/html')
            elif path.path=='/admin/v1/diagnostics/android':
                selected=profile_id if query.get('profile')==[profile_id] else 'primary'
                diagnostic_requests.append(selected)
                target=second_profile if selected==profile_id else profile
                self.send_body(json.dumps({'status':target,'log':diagnostic_logs[selected]}).encode())
            else:
                self.send_body(HTML.encode(),'text/html') if self.path=='/' else self.send_body(json.dumps(data).encode())
        def do_POST(self):
            body=self.rfile.read(int(self.headers.get('Content-Length','0')))
            data=json.loads(body) if body else {}
            path=urlsplit(self.path);query=parse_qs(path.query)
            if path.path=='/admin/v1/android/input':inputs.append(data)
            elif path.path=='/admin/v1/android/actions':
                actions.append(data)
                target=second_profile if query.get('profile')==[profile_id] else profile
                if data.get('action')=='disconnect':target['screen_open']=False
            elif path.path=='/admin/v1/diagnostics/android/clear':
                selected=profile_id if query.get('profile')==[profile_id] else 'primary'
                diagnostic_logs[selected]=''
            self.send_body(b'{"accepted":true}')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    page=browser.new_page(viewport={'width':1366,'height':900})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    try:
        page.goto(f'http://127.0.0.1:{server.server_port}/')
        expect(page.locator('#viewer-message')).to_contain_text('Conectado')
        assert page.evaluate("document.getElementById('android-canvas').getContext('2d').getImageData(10,10,1,1).data[0]")>200
        page.locator('#android-canvas').click(position={'x':10,'y':10})
        deadline=time.monotonic()+5
        while len(inputs)<2 and time.monotonic()<deadline:page.wait_for_timeout(50)
        assert [item['action'] for item in inputs if item['kind']=='touch']==[0,1],inputs
        assert all(item['screen']==screen_id for item in inputs)
        if multiple:
            expect(page.locator(second_prefix+'viewer-message')).to_contain_text('Conectado')
            expect(page.locator('#profiles-count')).to_have_text('2 de 2 perfiles')
            page.locator(second_prefix+'android-canvas').click(position={'x':10,'y':10})
            deadline=time.monotonic()+5
            while len(inputs)<4 and time.monotonic()<deadline:page.wait_for_timeout(50)
            assert [item['screen'] for item in inputs]==[screen_id,screen_id,'b'*32,'b'*32],inputs
            before_connections=list(video_connections)
            for section in ['nodes','tasks','system']:
                page.locator(f'[data-page="{section}"]').click()
                expect(page.locator(f'#page-{section}')).to_be_visible()
                page.locator('[data-page="android"]').click()
                expect(page.locator('#android-viewer')).to_be_visible()
                expect(page.locator(second_prefix+'android-viewer')).to_be_visible()
            with page.expect_popup() as popup:
                page.locator(second_prefix+'android-diagnostics').click()
            diagnostic=popup.value
            try:
                diagnostic.wait_for_load_state()
                assert diagnostic.url.endswith('/diagnostics?profile='+profile_id)
                expect(diagnostic.locator('#diagnostic-name')).to_have_text(second_profile['name'])
                expect(diagnostic.locator('#log')).to_have_text('REGISTRO-ANDROID-02')
                expect(diagnostic.locator('select')).to_have_count(0)
                assert diagnostic_requests and set(diagnostic_requests)=={profile_id}
                diagnostic.locator('#clear').click()
                expect(diagnostic.locator('#log')).to_have_text('')
                assert diagnostic_logs['primary']=='REGISTRO-ANDROID-01'
                assert page.url.endswith('/')
            finally:diagnostic.close()
            page.bring_to_front()
            expect(page.locator('#android-viewer')).to_be_visible()
            expect(page.locator(second_prefix+'android-viewer')).to_be_visible()
            assert video_connections==before_connections,'Cambiar de sección no debe abrir otra transmisión'
            assert not actions,'Navegar no debe enviar órdenes Android'
        second=browser.new_page()
        try:
            second.route('**/admin/v1/android/video?*',lambda route:route.fulfill(status=409,body='{}'))
            second.goto(f'http://127.0.0.1:{server.server_port}/')
            expect(second.locator('#android-message')).to_contain_text('ocupada')
            assert not actions, 'Un visor rechazado no debe desconectar al visor propietario'
            assert profile['screen_open']
            expect(page.locator('#android-viewer')).to_be_visible()
        finally:second.close()
        for width in [1366,390]:
            page.set_viewport_size({'width':width,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            for prefix in ['#']+([second_prefix] if multiple else []):
                recover=page.locator(prefix+'android-recover').bounding_box()
                diagnostic=page.locator(prefix+'android-diagnostics').bounding_box()
                assert recover and diagnostic
                assert abs((recover['y']+recover['height']/2)-(diagnostic['y']+diagnostic['height']/2))<2,(width,recover,diagnostic)
                assert diagnostic['x']>=recover['x']+recover['width'],(width,recover,diagnostic)
            label='dos-android' if multiple else 'pantalla-integrada'
            page.screenshot(path=str(OUTPUT/f'{label}-{width}.png'),full_page=True)
        if multiple:
            page.locator(second_prefix+'android-disconnect').click()
            expect(page.locator(second_prefix+'android-viewer')).to_be_hidden()
            expect(page.locator('#android-viewer')).to_be_visible()
            assert profile['screen_open']
        page.locator('#android-disconnect').click()
        expect(page.locator('#android-viewer')).to_be_hidden()
        assert not errors,errors
        assert len(page.context.pages)==1
    finally:
        stop.set();page.close();server.shutdown();server.server_close();thread.join(timeout=3)


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
        expect(page.locator('#android-profile-row .profile-actions a#android-diagnostics')).to_be_visible()
        expect(page.locator('nav a[href^="/diagnostics"]')).to_have_count(0)
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
        embedded_screen_browser_test(browser)
        embedded_screen_browser_test(browser,multiple=True)
        browser.close()
    print("UI: filtros, acciones, recuperación/cancelación, navegación, sesión y anchos 1366/960/390 correctos.")


if __name__ == "__main__":
    main()
