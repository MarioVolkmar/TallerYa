import sys, os, json, time, base64, tempfile, threading, urllib.request
M = "C:/Users/volkm/OneDrive/Desktop/TallerYa/informes_noche/piloto-esquema/motor"
sys.path.insert(0, M)
from http.server import ThreadingHTTPServer
from medir_lamina import RAIZ, Manejador, CDP, buscar_chrome, lanzar
SAL = sys.argv[1]
ACC2 = """(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<100&&!document.querySelector('.esq-marca-g');i++)await w(100);await w(500);
document.querySelector('.esq-marca-g[data-g="bomba-del"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));await w(900);
seleccion=null;document.querySelector('.esq-v2-item[data-k="1"]').click();await w(1200);return 1})()"""
ACC1 = """(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<100&&!document.querySelector('#capas .esq-pz');i++)await w(100);await w(500);
document.querySelector('.esq-chip[data-k="1"]').click();await w(1200);return 1})()"""
GEN = """(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<100&&!document.querySelector('.esq-marca-g');i++)await w(100);await w(800);return 1})()"""
FICHA = """(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<100&&!document.querySelector('.esq-marca-g');i++)await w(100);
document.querySelector('.esq-marca-g').dispatchEvent(new MouseEvent('click',{bubbles:true}));await w(1000);
document.querySelector('.esq-pz.esq-engr').dispatchEvent(new MouseEvent('click',{bubbles:true}));await w(900);
const v=document.getElementById('h2Ver');if(innerWidth<960&&v&&!document.getElementById('hoja2').hidden){v.click();await w(500)}return 1})()"""
srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador); threading.Thread(target=srv.serve_forever, daemon=True).start()
proc, puerto = lanzar(buscar_chrome(None), tempfile.mkdtemp())
try:
    nav = CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=20))["webSocketDebuggerUrl"])
    for pag, acc, nom in (("bomba-freno.html", GEN, "general"), ("bomba-freno.html", FICHA, "ficha")):
        for w, h in ((1280, 800), (390, 844)):
            tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=w, height=h)["targetId"]
            c = CDP(f"ws://127.0.0.1:{puerto}/devtools/page/{tid}")
            c("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=w < 768)
            c("Page.enable"); c("Page.navigate", url=f"http://127.0.0.1:{srv.server_address[1]}/informes_noche/piloto-esquema/motor/{pag}")
            time.sleep(1.5)
            c("Runtime.evaluate", expression=acc, awaitPromise=True, returnByValue=True, timeout=30000)
            c("Runtime.evaluate", expression="scrollTo(0,0)"); time.sleep(0.4)
            img = c("Page.captureScreenshot", format="jpeg", quality=72, clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 0.5})
            ruta = f"{SAL}/fig26-{nom}-{w}.jpg"; open(ruta, "wb").write(base64.b64decode(img["data"])); print(ruta)
            nav("Target.closeTarget", targetId=tid)
finally:
    proc.kill()
