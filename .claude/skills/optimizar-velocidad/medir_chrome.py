"""Mide páginas en Chrome sin ventana (cuenta como pestaña VISIBLE, GPU real) corriendo medir.js. Solo biblioteca estándar.

Uso:
  venv/Scripts/python.exe .claude/skills/optimizar-velocidad/medir_chrome.py http://127.0.0.1:8001 / /talleres/ \
      [--usuario correo@x.com] [--celular] [--veces 2] [--json salida.json]
- Cada URL: carga FRÍA (perfil nuevo, sin caché ni shaders) y, con --veces 2, una TIBIA (recarga con caché).
- --celular: 375×812, DPR 2, toque, CPU ×4 más lenta y red 4G (RTT 150 ms, 9 Mbps bajada, 3 Mbps subida). Sin él: 1366×768 sin freno.
- --sin-freno (con --celular): solo el ancho, para comparar con mediciones viejas sin freno.
- --usuario: crea una sesión de Django (sin contraseña) y la pone como cookie. Solo para servidores locales.
- --gpu swiftshader para una máquina sin GPU (los tiempos del 3D no son comparables con los de GPU real).
Salida: una línea por medición (tiempos en s) y, con --json, el detalle completo de medir.js.
"""
import argparse, base64, json, os, shutil, socket, struct, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
          shutil.which("google-chrome") or "", shutil.which("chromium") or ""]


class CDP:
    """Cliente mínimo de DevTools sobre websocket (sin dependencias)."""

    def __init__(self, ws):
        u = urlparse(ws)
        self.s = socket.create_connection((u.hostname, u.port), timeout=120)
        k = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {k}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        r = b""
        while b"\r\n\r\n" not in r:
            r += self.s.recv(1)
        self.n = 0

    def _leer(self, k):
        b = b""
        while len(b) < k:
            x = self.s.recv(k - len(b))
            if not x:
                raise RuntimeError("se cerró DevTools")
            b += x
        return b

    def _recibir(self):
        d = b""
        while True:
            c0, c1 = self._leer(2)
            L = c1 & 127
            if L == 126: L = struct.unpack(">H", self._leer(2))[0]
            elif L == 127: L = struct.unpack(">Q", self._leer(8))[0]
            d += self._leer(L)
            if c0 & 0x80:
                return json.loads(d.decode("utf-8", "replace"))

    def __call__(self, metodo, **params):
        self.n += 1
        c = json.dumps({"id": self.n, "method": metodo, "params": params}).encode()
        m = os.urandom(4); L = len(c)
        cab = bytes([0x81]) + (bytes([0x80 | L]) if L < 126 else bytes([0xFE]) + struct.pack(">H", L) if L < 65536 else bytes([0xFF]) + struct.pack(">Q", L))
        self.s.sendall(cab + m + bytes(b ^ m[i % 4] for i, b in enumerate(c)))
        while True:
            r = self._recibir()
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(f"{metodo}: {r['error']}")
                return r.get("result", {})


def sesion(correo):
    sys.path.insert(0, str(RAIZ))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from importlib import import_module
    from django.conf import settings
    from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model
    u = get_user_model().objects.get(email__iexact=correo)
    s = import_module(settings.SESSION_ENGINE).SessionStore()
    s[SESSION_KEY], s[HASH_SESSION_KEY] = str(u.pk), u.get_session_auth_hash()
    s[BACKEND_SESSION_KEY] = (getattr(settings, "AUTHENTICATION_BACKENDS", None) or ["django.contrib.auth.backends.ModelBackend"])[0]
    s.create()
    return settings.SESSION_COOKIE_NAME, s.session_key


def abrir(gpu):
    perfil = tempfile.mkdtemp(prefix="tallerya-vel-")
    chrome = next(c for c in CHROME if c and os.path.exists(c))
    args = [chrome, "--headless=new", "--remote-debugging-port=0", f"--user-data-dir={perfil}", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", "--mute-audio", "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows", "about:blank"]
    args[1:1] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] if gpu == "swiftshader" else ["--use-angle=d3d11" if os.name == "nt" else "--use-gl=angle", "--enable-gpu"]
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    f = os.path.join(perfil, "DevToolsActivePort")
    for _ in range(150):
        try:
            linea = open(f).readline().strip() if os.path.exists(f) else ""
        except OSError:
            linea = ""
        if linea:
            return p, int(linea), perfil
        time.sleep(0.1)
    raise RuntimeError("Chrome no abrió DevTools")


def cerrar(p, puerto, perfil):
    try:
        ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=3))["webSocketDebuggerUrl"]
        CDP(ws)("Browser.close")
        p.wait(timeout=5)
    except Exception:
        pass
    if p.poll() is None:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)] if os.name == "nt" else ["kill", str(p.pid)], capture_output=True)
    shutil.rmtree(perfil, ignore_errors=True)


def pestaña(puerto):
    req = urllib.request.Request(f"http://127.0.0.1:{puerto}/json/new?about:blank", method="PUT")
    return CDP(json.load(urllib.request.urlopen(req))["webSocketDebuggerUrl"])


def medir_url(base, ruta, a, cookie, script):
    p, puerto, perfil = abrir(a.gpu)
    filas = []
    try:
        t = pestaña(puerto)
        t("Network.enable"); t("Page.enable")
        if a.celular:
            t("Emulation.setDeviceMetricsOverride", width=375, height=812, deviceScaleFactor=2, mobile=True)
            t("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
            if not a.sin_freno:
                t("Emulation.setCPUThrottlingRate", rate=4)
                t("Network.emulateNetworkConditions", offline=False, latency=150, downloadThroughput=9e6 / 8, uploadThroughput=3e6 / 8)
        else:
            t("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        if cookie:
            t("Network.setCookie", name=cookie[0], value=cookie[1], url=base)
        origen = t("Runtime.evaluate", expression="performance.timeOrigin", returnByValue=True).get("result", {}).get("value")
        for vez in range(a.veces):
            if vez == 0:
                t("Page.navigate", url=base + ruta)
            else:
                t("Page.reload")
            for _ in range(600):  # espera a que exista el documento NUEVO (si no, medir.js corre en el anterior)
                o = t("Runtime.evaluate", expression="performance.timeOrigin", returnByValue=True).get("result", {}).get("value")
                if o and o != origen and o > 0:
                    origen = o
                    break
                time.sleep(0.05)
            r = t("Runtime.evaluate", expression=script, awaitPromise=True, returnByValue=True, timeout=60000)
            v = r.get("result", {}).get("value") or {"error": r}
            v["carga"] = "fría" if vez == 0 else "tibia"
            v["recursos"] = t("Runtime.evaluate", returnByValue=True, expression=
                "performance.getEntriesByType('resource').map(r => [r.name.replace(location.origin, ''), r.decodedBodySize])")["result"].get("value")
            filas.append(v)
            time.sleep(1)
    finally:
        cerrar(p, puerto, perfil)
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--usuario")
    ap.add_argument("--celular", action="store_true")
    ap.add_argument("--sin-freno", action="store_true", help="con --celular: solo 375 px, sin frenar CPU ni red")
    ap.add_argument("--veces", type=int, default=2)
    ap.add_argument("--gpu", default="real", choices=["real", "swiftshader"])
    ap.add_argument("--json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    a.rutas = [r[r.find("/Git/") + 4:] if ":" in r[:3] and "/Git/" in r else r for r in a.rutas]  # Git Bash
    base = a.base.rstrip("/")
    if urlparse(base).hostname not in ("127.0.0.1", "localhost"):
        sys.exit("Solo servidores locales")
    cookie = sesion(a.usuario) if a.usuario else None
    script = (AQUI / "medir.js").read_text(encoding="utf-8")
    todo = []
    for ruta in a.rutas:
        for v in medir_url(base, ruta, a, cookie, script):
            todo.append(v)
            td = v.get("tresD") or {}
            print(f"{ruta:22} {('375' + ('' if a.sin_freno else '/4G')) if a.celular else '1366'} {v['carga']:5} ttfb {v.get('ttfb')} fcp {v.get('fcp')} lcp {v.get('lcp')} ({v.get('lcpElem')}) "
                  f"load {v.get('load')} esquema {v.get('esquema', '-')} 3D {td.get('listo', '-')} "
                  f"tareaMax {v.get('largas', {}).get('maxS')} red {v.get('totalKB')} {v.get('aviso') or ''}")
    if a.json:
        Path(a.json).write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
