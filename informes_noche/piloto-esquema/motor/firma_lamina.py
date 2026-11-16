"""Firma de una o varias láminas: caja y cantidad de elementos de cada capa del dibujo (piezas y contexto), en orden.
Sirve para comprobar que un cambio del motor no mueve nada en las láminas que ya existen.

  python firma_lamina.py <pagina.html> [...] --guardar firmas.json     antes del cambio
  python firma_lamina.py <pagina.html> [...] --comparar firmas.json    después: dice «idéntica» o qué capas cambiaron

Las rutas son relativas a la raíz del proyecto. Usa el mismo servidor y Chrome sin ventana que medir_lamina.py.
"""
import argparse, hashlib, json, os, sys, tempfile, threading, time, urllib.request
from http.server import ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from medir_lamina import RAIZ, Manejador, CDP, buscar_chrome, lanzar

FIRMA = r"""(async()=>{for(let i=0;i<200&&!document.querySelector('#capas .esq-pz');i++)await new Promise(r=>setTimeout(r,100));
await new Promise(r=>setTimeout(r,600));
return JSON.stringify([...document.querySelectorAll('#capas > *')].map(g=>{const b=g.getBBox();
 return [g.id||g.getAttribute('class')||g.tagName,Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height),g.querySelectorAll('*').length]}))})()"""


def firmar(paginas, chrome):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    proc, puerto = lanzar(buscar_chrome(chrome), tempfile.mkdtemp())
    res = {}
    try:
        nav = CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=20))["webSocketDebuggerUrl"])
        for pag in paginas:
            rel = os.path.relpath(os.path.abspath(pag), RAIZ).replace("\\", "/")
            tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=1280, height=800)["targetId"]
            c = CDP(f"ws://127.0.0.1:{puerto}/devtools/page/{tid}")
            c("Emulation.setDeviceMetricsOverride", width=1280, height=800, deviceScaleFactor=1, mobile=False)
            c("Page.navigate", url=f"http://127.0.0.1:{srv.server_address[1]}/{rel}")
            time.sleep(0.5)
            r = c("Runtime.evaluate", expression=FIRMA, awaitPromise=True, returnByValue=True, timeout=60000)
            res[rel] = json.loads(r["result"]["value"]) if "exceptionDetails" not in r else {"error": str(r["exceptionDetails"])[:300]}
    finally:
        proc.kill(); srv.shutdown()
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("paginas", nargs="+")
    ap.add_argument("--guardar"); ap.add_argument("--comparar"); ap.add_argument("--chrome")
    a = ap.parse_args()
    F = firmar(a.paginas, a.chrome)
    for pag, capas in F.items():
        h = hashlib.sha1(json.dumps(capas).encode()).hexdigest()[:12]
        print(f"{pag}: {len(capas) if isinstance(capas, list) else 'ERROR'} capas · firma {h}")
    if a.guardar:
        open(a.guardar, "w", encoding="utf-8").write(json.dumps(F)); print("guardada en", a.guardar)
    if a.comparar:
        V = json.load(open(a.comparar, encoding="utf-8")); dif = 0
        for pag, capas in F.items():
            if V.get(pag) == capas: print(f"{pag}: idéntica"); continue
            dif += 1; viejas = V.get(pag) or []
            for i in range(max(len(capas), len(viejas))):
                x = capas[i] if i < len(capas) else None; y = viejas[i] if i < len(viejas) else None
                if x != y: print(f"  {pag} capa {i}: antes {y} · ahora {x}")
        return 1 if dif else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
