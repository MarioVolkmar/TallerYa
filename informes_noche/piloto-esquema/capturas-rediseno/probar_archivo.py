import sys, json, time, tempfile, urllib.request, pathlib
M = "C:/dev/TallerYa/informes_noche/piloto-esquema/motor"
sys.path.insert(0, M)
from medir_lamina import CDP, buscar_chrome, lanzar, GANCHO
url = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else M + "/prueba-nmax-fig26.html").resolve().as_uri()
PRUEBA = """(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<100&&!document.querySelector('.esq-marca-g');i++)await w(100);
const R=[location.protocol,document.querySelectorAll('.esq-marca-g').length];
document.querySelector('.esq-marca-g').dispatchEvent(new MouseEvent('click',{bubbles:true}));await w(900);
R.push(document.querySelector('#lamina').classList.contains('esq-engrupo'));
([...document.querySelectorAll('.esq-v2-item')].find(b=>(window.__con3d||[]).includes(b.dataset.k))||document.querySelector('.esq-v2-item')).click();await w(3000);
R.push(document.querySelector('#ficha h3').textContent,document.querySelectorAll('#ficha .esq-v2-sec').length,(document.querySelector('.esq-v3d-estado')||{}).textContent,(window.__errores||[]).join(' | ')||'sin errores');
return JSON.stringify(R)})()"""
proc, puerto = lanzar(buscar_chrome(None), tempfile.mkdtemp())
try:
    nav = CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=20))["webSocketDebuggerUrl"])
    for w, h in ((390, 844), (1280, 800)):
        tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=w, height=h)["targetId"]
        c = CDP(f"ws://127.0.0.1:{puerto}/devtools/page/{tid}")
        c("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=w < 768)
        c("Page.enable"); c("Page.addScriptToEvaluateOnNewDocument", source=GANCHO); c("Page.navigate", url=url); time.sleep(2)
        r = c("Runtime.evaluate", expression=PRUEBA, awaitPromise=True, returnByValue=True, timeout=30000)
        print(w, r["result"].get("value") or r)
finally:
    proc.kill()
