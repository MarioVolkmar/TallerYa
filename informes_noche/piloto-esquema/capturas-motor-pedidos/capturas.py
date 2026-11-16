"""Capturas a escala 0,5 con Chrome sin ventana (reutiliza medir_lamina.py).
Uso: python capturas.py trabajos.json   — lista de {url, w, h, js (async, opcional), clip (selector, opcional), salida}
"""
import json, sys, time, base64, tempfile, urllib.request, shutil
sys.path.insert(0, r"C:\dev\TallerYa\informes_noche\piloto-esquema\motor")
import medir_lamina as ML

trabajos = json.load(open(sys.argv[1], encoding="utf-8"))
perfil = tempfile.mkdtemp()
proc, puerto = ML.lanzar(ML.buscar_chrome(None), perfil)
try:
    for t in trabajos:
        nav = ML.CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=20))["webSocketDebuggerUrl"])
        tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=t["w"], height=t["h"])["targetId"]
        c = ML.CDP(f"ws://127.0.0.1:{puerto}/devtools/page/{tid}")
        c("Emulation.setFocusEmulationEnabled", enabled=True)
        c("Emulation.setDeviceMetricsOverride", width=t["w"], height=t["h"], deviceScaleFactor=1, mobile=t["w"] < 768)
        c("Page.enable"); c("Network.enable"); c("Network.setCacheDisabled", cacheDisabled=True)
        c("Page.navigate", url=t["url"])
        for _ in range(200):
            v = c("Runtime.evaluate", expression="document.readyState+'|'+!!document.querySelector('#lamina .esq-pz')", returnByValue=True)["result"].get("value", "")
            if v == "complete|true": break
            time.sleep(0.1)
        time.sleep(1.5)
        if t.get("js"):
            r = c("Runtime.evaluate", expression="(async()=>{const S=t=>new Promise(r=>setTimeout(r,t));" + t["js"] + "})()", awaitPromise=True, returnByValue=True, timeout=120000)
            print(t["salida"], "js:", json.dumps(r.get("result", {}).get("value"), ensure_ascii=False)[:300] if "exceptionDetails" not in r else r["exceptionDetails"].get("exception", {}).get("description", "")[:300])
        clip = {"x": 0, "y": 0, "width": t["w"], "height": t["h"], "scale": 0.5}
        if t.get("clip"):
            r = c("Runtime.evaluate", expression=f"(()=>{{const r=document.querySelector({json.dumps(t['clip'])}).getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,r.height]}})()", returnByValue=True)["result"]["value"]
            clip = {"x": r[0], "y": r[1], "width": r[2], "height": r[3], "scale": 0.5}
        img = c("Page.captureScreenshot", format="jpeg", quality=80, clip=clip, captureBeyondViewport=True)
        open(t["salida"], "wb").write(base64.b64decode(img["data"]))
        print("guardada", t["salida"])
        nav("Target.closeTarget", targetId=tid)
finally:
    proc.kill(); shutil.rmtree(perfil, ignore_errors=True)
