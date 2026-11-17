"""Chequeo rápido (~15-25 s por lámina) de lo que hoy aparece recién en la medición completa, para medir una sola vez.
Uso:
  python informes_noche/piloto-esquema/motor/chequeo_rapido.py <pagina.html> [-v]
  python informes_noche/piloto-esquema/motor/chequeo_rapido.py --todas      tabla: lámina → qué incumple (todas las páginas de motor/)
Revisa, con las mismas reglas que medir_lamina.py y sin cambiarlo (reutiliza su servidor, Chrome y CDP):
  bloqueantes: etiquetas montadas en «Cómo funciona» (a 360, 390 y 1280), etiquetas tapadas por el dibujo en ≥ 40 %
               y pasos de «Cómo funciona» que no cambian nada;
  avisos: etiquetas tapadas por el dibujo entre 20 y 40 %, pasos de «Cómo funciona» con ≤ 2 cambios o de más de 250
          caracteres, marcas de grupo de menos de 44 px,
          pieza tapada en el desarme general (≥ 16 %, bloquea en 20 %; con medir_lamina.py --solape).
Con --todas suma el validador (errores, textos largos, píldoras sin pieza visible, regresiones).
Sale con 1 si hay bloqueantes."""
import base64, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.request
from http.server import ThreadingHTTPServer
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import medir_lamina as ML

JS = r"""(async()=>{const S=t=>new Promise(r=>setTimeout(r,t)),q=s=>document.querySelector(s),R={};
for(let i=0;i<100&&!q('#lamina .esq-pz');i++)await S(100);await S(600);
const visE=e=>{const r=e.getBoundingClientRect();if(!r.width)return false;for(let x=e;x&&x.nodeType===1;x=x.parentElement){const c=getComputedStyle(x);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.15)return false}return true};
// ronda 8: piezas de «ocultas» que se ven armadas encima de otra (falta esq-oculto-arm en su arte): área visible > 100 px²
if(__FULL__){const OC=new Set(__OCULTAS__);R.ocultas=[];
 for(const P of document.querySelectorAll('#lamina .esq-pz')){if(!OC.has(P.dataset.n))continue;const a=P.querySelector('.esq-arte');if(!a||!visE(a))continue;
  const r=a.getBoundingClientRect();let k=0;
  for(let x=r.left+1;x<r.right;x+=3)for(let y=r.top+1;y<r.bottom;y+=3){if(x<0||y<0||x>innerWidth||y>innerHeight)continue;const e=document.elementFromPoint(x,y);
   if(!e||e.closest('.esq-pz')!==P||e.classList.contains('esq-toque-pz')||e.closest('.esq-oculto-arm'))continue;const c=getComputedStyle(e);
   if((c.fill==='none'||+c.fillOpacity===0)&&(c.stroke==='none'||+c.strokeOpacity===0))continue;k++}
  if(k*9>100)R.ocultas.push(P.dataset.n+' ('+k*9+' px²)')}}
// ronda 9: roce de las marcas de grupo (lo mismo que medir_lamina: centro que no toca su marca, vecina a ±9 px, píldoras encimadas),
// en cada lado y en cada ancho (sobre todo 360), para que salga antes de la medición final
{const svgL=q('#lamina');if(svgL){svgL.scrollIntoView({block:'center',behavior:'instant'});await S(300)}
 const caja=e=>e.getBoundingClientRect(),pild=m=>[...m.querySelectorAll('.esq-pildora')].find(x=>caja(x).width&&visE(x))||m.querySelector('.esq-toque')||m;
 const nom=m=>(([...m.querySelectorAll('text')].find(t=>caja(t).width&&visE(t)))||m).textContent.trim();
 const lados=[...document.querySelectorAll('.esq-v2-lado [data-lado]')].filter(visE);R.marcasRoce=[];
 for(const b of (lados.length?lados:[null])){if(b){b.click();await S(400)}
  const ms=[...document.querySelectorAll('#marcasG .esq-marca-g')].filter(visE),L=b?b.dataset.lado+':':'';
  const de=(m,x,y)=>{const e=document.elementFromPoint(x,y),mm=e&&e.closest('.esq-marca');return mm===m?'ok':mm?nom(mm):(e?e.tagName:'fuera')};
  ms.forEach(m=>{const p=caja(pild(m)),cx=p.left+p.width/2,cy=p.top+p.height/2,c=de(m,cx,cy);if(c!=='ok')R.marcasRoce.push(L+nom(m)+'→'+c+' (centro)');
   for(const[dx,dy]of[[9,0],[-9,0],[0,9],[0,-9]]){const h=de(m,cx+dx,cy+dy);if(h!=='ok'&&ms.some(x=>nom(x)===h)){R.marcasRoce.push(L+nom(m)+'→'+h);break}}});
  for(let i=0;i<ms.length;i++)for(let j=i+1;j<ms.length;j++){const a=caja(pild(ms[i])),c=caja(pild(ms[j]));if(a.left<c.right&&a.right>c.left&&a.top<c.bottom&&a.bottom>c.top)R.marcasRoce.push(L+nom(ms[i])+' / '+nom(ms[j])+' (encimadas)')}}
 if(lados.length){lados[0].click();await S(300)}scrollTo(0,0);await S(150)}
const ms=[...document.querySelectorAll('#marcasG .esq-marca-g')].filter(visE).map(m=>(m.querySelector('.esq-toque')||m).getBoundingClientRect().height);
R.marcaMin=ms.length?Math.round(Math.min(...ms)):null;
const tf=q('#t-funciona');if(!tf)return JSON.stringify(R);tf.click();await S(500);const F=q('#fn');if(!F)return JSON.stringify(R);
const foto=()=>[...F.querySelectorAll('*')].map(e=>['transform','d','x','y','cx','cy','r','opacity','fill','stroke','points','width','height','style','class'].map(a=>e.getAttribute(a)).join('|')+'|'+(e.childElementCount?'':e.textContent));
const sol=()=>{const ts=[...F.querySelectorAll('text')].filter(visE),rs=ts.map(t=>t.getBoundingClientRect()),o=[];
 for(let i=0;i<rs.length;i++)for(let j=i+1;j<rs.length;j++){const a=rs[i],b=rs[j],ox=Math.min(a.right,b.right)-Math.max(a.left,b.left),oy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
  if(ox>2&&oy>2)o.push(ts[i].textContent.trim().slice(0,22)+' / '+ts[j].textContent.trim().slice(0,22))}return o};
// etiquetas tapadas por el dibujo: % de la etiqueta (franja central) que queda bajo una forma con relleno que se pinta encima
const tap=()=>{F.scrollIntoView({block:'center',behavior:'instant'});const o=[];
 for(const t of [...F.querySelectorAll('text')].filter(visE)){const r=t.getBoundingClientRect();let n=0,k=0;
  for(let x=r.left+1;x<r.right;x+=2)for(let y=r.top+r.height*.25;y<r.bottom-r.height*.2;y+=2){if(x<0||y<0||x>innerWidth||y>innerHeight)continue;
   const L=document.elementsFromPoint(x,y),i=L.findIndex(e=>e===t||t.contains(e));if(i<0)continue;n++;
   if(L.slice(0,i).some(e=>{if(e===F||!F.contains(e)||e.closest('text'))return false;const c=getComputedStyle(e);return c.fill!=='none'&&+c.fillOpacity>0.3&&+c.opacity>0.3}))k++}
  if(n>4&&k/n>=0.2)o.push(Math.round(k/n*100)+'% «'+t.textContent.trim().slice(0,24)+'»')}return o};
const quieto=async()=>{if(!__FULL__){await S(700);return}let p='';for(let i=0;i<25;i++){await S(120);const s=foto().join('#');if(s===p)return;p=s}};
const ad=q('#fnAdel'),at=q('#fnAtras');if(at)while(!at.disabled){at.click();await S(60)}await quieto();
R.sol=sol().map(s=>'1: '+s);R.tap=tap().map(s=>'1: '+s);R.cambios=[];R.largo=[];let n=1,ant=__FULL__?foto():[];
const largo=()=>(((q('#fnTexto')||{}).textContent)||'').trim().length;R.largo.push(largo());
for(let i=0;i<20&&ad&&!ad.disabled;i++){ad.click();await quieto();n++;if(__FULL__){const f=foto();R.cambios.push(f.filter((x,j)=>x!==ant[j]).length+Math.abs(f.length-ant.length));ant=f}R.sol.push(...sol().map(s=>n+': '+s));R.tap.push(...tap().map(s=>n+': '+s));R.largo.push(largo())}
R.pasos=n;return JSON.stringify(R)})()"""


def ancho(pcdp, url, w, h, salida):
    """Un ancho; con varias láminas a la vez Chrome a veces cierra la pestaña a medias: un reintento."""
    for intento in range(2):
        _ancho(pcdp, url, w, h, salida)
        if not str((salida.get(w) or {}).get("fatal", "")).strip(): return
        time.sleep(1.5)


def _ancho(pcdp, url, w, h, salida):
    try:
        nav = ML.CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{pcdp}/json/version", timeout=20))["webSocketDebuggerUrl"])
        tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=w, height=h)["targetId"]
        c = ML.CDP(f"ws://127.0.0.1:{pcdp}/devtools/page/{tid}")
        c("Emulation.setFocusEmulationEnabled", enabled=True)
        c("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=w < 768)
        c("Page.enable"); c("Page.navigate", url=url)
        for _ in range(400):
            if c("Runtime.evaluate", expression="document.readyState", returnByValue=True)["result"].get("value") == "complete": break
            time.sleep(0.1)
        if SOLO_SOLAPE: salida[w] = {}
        else:
            r = c("Runtime.evaluate", expression=JS.replace("__FULL__", "true" if w == 1280 else "false").replace("__OCULTAS__", json.dumps(ocultas_de(url))), awaitPromise=True, returnByValue=True, timeout=120000)
            salida[w] = json.loads(r["result"]["value"]) if "exceptionDetails" not in r else {"fatal": str(r["exceptionDetails"])[:200]}
        if w == 1280 and not salida[w].get("fatal"):
            # ronda 3: solape y captura en la misma pestaña (antes eran dos Chrome más: medir_lamina --solape y --solo-captura)
            if SOLAPE_AQUI:
                c("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
                ML.recargar(c)
                g = json.dumps(GRUPO) if GRUPO else "null"
                for intento in range(2):   # con varias láminas a la vez, la recarga puede no haber terminado: un reintento
                    r = c("Runtime.evaluate", expression="(async()=>{" + ML.JS_SOLAPE + f";return JSON.stringify(await medir_solape(14,{g}))}})()", awaitPromise=True, returnByValue=True, timeout=120000)
                    salida[w]["solape"] = json.loads(r["result"]["value"]) if "exceptionDetails" not in r else {"fatal": str(r["exceptionDetails"])[:200]}
                    if "fatal" not in salida[w]["solape"]: break
                    time.sleep(2); ML.recargar(c)
            if CAPTURA:
                ML.recargar(c); c("Runtime.evaluate", expression="scrollTo(0,0)"); time.sleep(0.4)
                img = c("Page.captureScreenshot", format="jpeg", quality=70, clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 0.5})
                with open(CAPTURA, "wb") as f: f.write(base64.b64decode(img["data"]))
        nav("Target.closeTarget", targetId=tid)
    except Exception as e:
        salida[w] = {"fatal": f"{type(e).__name__}: {e}"}


def solape(pagina):
    r = subprocess.run([sys.executable, os.path.join(AQUI, "medir_lamina.py"), pagina, "--solape"], cwd=ML.RAIZ, capture_output=True, timeout=300,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    t = (r.stdout + r.stderr).decode("utf-8", "replace")
    pe = [int(x) for x in re.findall(r"peor (\d+) %", t)]
    return max(pe) if pe else None, next((l for l in t.splitlines() if l.startswith("solape")), "")[:220]


def ocultas_de(url):
    """Números de «ocultas» de la lámina de esa página (las de la biblioteca con «oculto» ya se esconden solas)."""
    try:
        html = open(os.path.join(AQUI, url.split("?")[0].rsplit("/", 1)[-1]), encoding="utf-8", errors="replace").read()
        D = json.load(open(os.path.join(AQUI, "datos", re.search(r'fetch\("datos/([\w\-]+)\.json"\)', html).group(1) + ".json"), encoding="utf-8"))
        comunes = {p.get("n") for p in D.get("piezas", []) if p.get("comun") and p.get("oculto")}
        return [n for n in D.get("ocultas", []) if n not in comunes]
    except Exception:
        return []


def revisar(pcdp, base, ruta):
    R = {}
    hs = [threading.Thread(target=ancho, args=(pcdp, f"{base}/{ruta}", w, h, R), daemon=True) for w, h in ML.ANCHOS if w in ANCHOS]
    for t in hs: t.start()
    for t in hs: t.join(150)
    bloq, avi = [], []
    fat = {w: r["fatal"] for w, r in R.items() if r.get("fatal")}
    if fat: bloq.append("no se pudo revisar: " + "; ".join(f"{w}: {v}" for w, v in fat.items()))
    sol = {w: r["sol"] for w, r in sorted(R.items()) if r.get("sol")}
    if sol: bloq.append("etiquetas montadas en «Cómo funciona»: " + "; ".join(f"{w} px paso {s}" for w, ss in list(sol.items())[:2] for s in ss[:3]))
    # etiquetas tapadas por el dibujo: aviso desde 20 %, bloqueante desde 40 % (se lee mal); se toma el peor % de cada etiqueta
    peor = {}
    for w, r in sorted(R.items()):
        for s in r.get("tap") or []:
            m = re.match(r"(\d+): (\d+)% (.+)", s)
            if m:
                k = m.group(3); v = int(m.group(2))
                if k not in peor or v > peor[k][0]: peor[k] = (v, w, m.group(1))
    if peor:
        txt = lambda xs: "; ".join(f"{k} {v} % ({w} px, paso {p})" for k, (v, w, p) in xs[:3])
        graves = sorted([x for x in peor.items() if x[1][0] >= 40], key=lambda x: -x[1][0])
        leves = sorted([x for x in peor.items() if x[1][0] < 40], key=lambda x: -x[1][0])
        if graves: bloq.append("etiquetas de «Cómo funciona» tapadas por el dibujo: " + txt(graves))
        if leves: avi.append("etiquetas de «Cómo funciona» algo tapadas por el dibujo: " + txt(leves))
    r1 = R.get(1280, {})
    cam = r1.get("cambios") or []
    if 0 in cam: bloq.append("pasos de «Cómo funciona» sin cambio visible: " + ", ".join(str(i + 2) for i, c in enumerate(cam) if c == 0))
    justos = [str(i + 2) for i, c in enumerate(cam) if 0 < c <= 2]
    if justos: avi.append("pasos de «Cómo funciona» con ≤ 2 cambios: " + ", ".join(justos))
    lg = [f"{i + 1} ({n})" for i, n in enumerate(r1.get("largo") or []) if n > 250]
    if lg: avi.append("pasos de «Cómo funciona» de más de 250 caracteres: " + ", ".join(lg))
    # ronda 8: bloquea desde 600 px² visibles (el chiclé del carburador Boxer: 2.259); menos, aviso (un clip que asoma)
    ocs = sorted({x for r in R.values() for x in (r.get("ocultas") or [])}); px = lambda x: int(re.search(r"\((\d+) px", x).group(1))
    oc = [x for x in ocs if px(x) >= 600]
    if [x for x in ocs if px(x) < 600]: avi.append("piezas de «ocultas» que asoman armadas: " + ", ".join(x for x in ocs if px(x) < 600) + " · si son internas, esq-oculto-arm; si se ven a propósito, sácalas de «ocultas»")
    if oc: bloq.append("piezas internas (ocultas) que se ven armadas encima de otra: " + ", ".join(oc[:6]) + " · pon class=\"esq-oculto-arm\" en el <g> de su arte (o \"oculto\":true si es de la biblioteca)")
    ro = [f"{w}: {x}" for w, r in sorted(R.items()) for x in dict.fromkeys(r.get("marcasRoce") or [])]
    if ro: bloq.append("marcas de grupo que se rozan o no reciben su toque (criterio 6): " + "; ".join(ro[:6]) + " · sepáralas (v2.grupos[].marca)")
    mm = [r["marcaMin"] for r in R.values() if r.get("marcaMin")]
    if mm and min(mm) < ML.ALTO_MIN_MARCA: avi.append(f"marcas de grupo de {min(mm)} px (< {ML.ALTO_MIN_MARCA})")
    if "-v" in sys.argv: avi.append("marcas (px por ancho): " + ", ".join(f"{w}: {r.get('marcaMin')}" for w, r in sorted(R.items())))
    so = r1.get("solape")
    if so:
        if so.get("fatal"): bloq.append("solape: no se pudo medir " + so["fatal"][:150])
        else:
            peor = max([o.get("peor", 0) for o in so.get("lados", {}).values()] or [0])
            txt = ML.texto_solape(so) + (f" (solo {GRUPO})" if GRUPO else "")
            if peor >= 20: bloq.append(f"pieza tapada {peor} % en el desarme general (≥ 20): " + txt[:200])
            elif peor >= 16: avi.append(f"pieza tapada {peor} % en el desarme general: " + txt[:200])
            elif "-v" in sys.argv: avi.append(txt[:220])
    return bloq, avi


ANCHOS = (360, 390, 1280)   # celular (dos anchos) y escritorio: las tres maquetas de «Cómo funciona»; la medición final mira los 6
# ronda 3 (una sola lámina): --captura <ruta> (armado limpio a 1280, escala 0,5), --grupo <ids o data-g> (solape solo de esas piezas)
# y --solo-solape (sin «Cómo funciona»: para volver a medir el grupo que cambió en segundos)
def _opt(n):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv and sys.argv.index(n) + 1 < len(sys.argv) else None
CAPTURA, GRUPO, SOLO_SOLAPE = _opt("--captura"), _opt("--grupo"), "--solo-solape" in sys.argv
SOLAPE_AQUI = "--sin-solape" not in sys.argv and "--solape-aparte" not in sys.argv   # regresión: el solape va en la misma pestaña de 1280
PARALELO = int(_opt("--paralelo") or 4)   # láminas a la vez con --todas/--paginas
if _opt("--anchos"): ANCHOS = tuple(int(x) for x in _opt("--anchos").split(","))   # p. ej. 390,1280 (1280 siempre: ahí van «Cómo funciona», solape y captura)
if SOLO_SOLAPE: ANCHOS = (1280,)


class Servidor(ThreadingHTTPServer):
    daemon_threads = True
    def handle_error(self, request, client_address): pass   # Chrome corta conexiones al cerrar pestañas: sin ruido


def servidor():
    srv = Servidor(("127.0.0.1", 0), ML.Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def paginas():
    """Páginas de motor/ con su JSON de datos (la que hace fetch de datos/<lamina>.json)."""
    out = []
    for f in sorted(os.listdir(AQUI)):
        if not f.endswith(".html"): continue
        m = re.search(r'fetch\("datos/([\w\-]+)\.json"\)', open(os.path.join(AQUI, f), encoding="utf-8", errors="replace").read())
        if m and not m.group(1).startswith("zz") and not m.group(1).endswith("-v1") and os.path.exists(os.path.join(AQUI, "datos", m.group(1) + ".json")): out.append((m.group(1), f))
    vistos, res = set(), []
    for lam, f in out:   # una página por lámina (la de nombre más corto)
        if lam not in vistos: vistos.add(lam); res.append((lam, min((g for l, g in out if l == lam), key=len)))
    return res


def validador(lam):
    r = subprocess.run([sys.executable, os.path.join(AQUI, "validar_esquema.py"), os.path.join(AQUI, "datos", lam + ".json")], cwd=ML.RAIZ, capture_output=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=120)
    t = (r.stdout + r.stderr).decode("utf-8", "replace").splitlines()
    err = [l for l in t if "ERROR" in l]
    av = [l.strip()[7:] for l in t if l.strip().startswith("aviso:")]
    largos = sum(1 for x in av if re.search(r"caracteres \(> 300\)", x))
    pild = sum(1 for x in av if "píldora del grupo" in x)
    reg = [x for x in av + err if "regresi" in x]
    return err, largos, pild, reg


def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    valores = {_opt(o) for o in ("--captura", "--grupo", "--paginas", "--paralelo", "--anchos", "--json")} - {None}
    a = [x for x in sys.argv[1:] if not x.startswith("-") and x not in valores]; v = "-v" in sys.argv
    todas = "--todas" in sys.argv or "--paginas" in sys.argv
    if not a and not todas: sys.exit(__doc__)
    if "--paginas" in sys.argv:   # regresion.py: un subconjunto, con la misma tabla que --todas
        quiero = {os.path.basename(x) for x in _opt("--paginas").split(",") if x}
        lista = [(l, p) for l, p in paginas() if p in quiero or l in quiero]
    else:
        lista = paginas() if todas else [(None, os.path.relpath(ML.resolver(a[0]), AQUI))]
    srv, base = servidor(); tmp = tempfile.mkdtemp(prefix="chequeo_rapido_"); t0 = time.time()
    proc, pcdp = ML.lanzar(ML.buscar_chrome(None), tmp)
    filas, malo = [], False
    def una(lp):
        lam, pag = lp
        ruta = os.path.relpath(os.path.join(AQUI, pag), ML.RAIZ).replace(os.sep, "/")
        bloq, avi = revisar(pcdp, base, ruta)
        return [lam, pag, bloq, avi]
    try:
        # regresión: varias láminas a la vez en el mismo Chrome (cada una abre sus anchos en ventanas propias)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=PARALELO if len(lista) > 1 else 1) as ex:
            filas = list(ex.map(una, lista))
        # con carga, Chrome a veces mide antes de que asienten letras o animaciones: lo que bloquea se confirma solo, sin carga
        if len(lista) > 1:
            for i, f in enumerate(filas):
                if f[2]:
                    g = una((f[0], f[1]))
                    filas[i] = g if not g[2] else [g[0], g[1], [b + " (confirmado)" for b in g[2]], g[3]]
    finally:
        ML.cerrar(proc, pcdp); srv.shutdown(); time.sleep(0.5); shutil.rmtree(tmp, ignore_errors=True)
    for f in filas:
        if not SOLAPE_AQUI and "--sin-solape" not in sys.argv:   # camino viejo (un Chrome por lámina): solo si se pide
            peor, txt = solape(os.path.join(AQUI, f[1]))
            if peor is not None and peor >= 20: f[2].append(f"pieza tapada {peor} % en el desarme general (≥ 20)")
            elif peor is not None and peor >= 16: f[3].append(f"pieza tapada {peor} % en el desarme general")
            if v and txt: f[3].append(txt)
        malo = malo or bool(f[2])
    if _opt("--json"):
        with open(_opt("--json"), "w", encoding="utf-8") as fh: json.dump({f[0] or f[1]: {"pagina": f[1], "bloq": f[2], "avi": f[3]} for f in filas}, fh, ensure_ascii=False)
    if not todas:
        _, pag, bloq, avi = filas[0]
        if not bloq and not avi: print(f"CHEQUEO RÁPIDO: sin problemas · {time.time() - t0:.0f} s")
        else:
            print(f"CHEQUEO RÁPIDO: {len(bloq)} bloqueantes · {len(avi)} avisos · {time.time() - t0:.0f} s")
            for x in bloq: print("  BLOQUEA: " + x[:300])
            for x in avi: print("  aviso: " + x[:300])
        return 1 if bloq else 0
    sinval = "--sin-validador" in sys.argv
    print("| lámina | " + ("" if sinval else "validador | ") + "navegador (bloquea) | avisos |\n|---|" + ("" if sinval else "---|") + "---|---|")
    for lam, pag, bloq, avi in filas:
        if not sinval:
            err, largos, pild, reg = validador(lam)
            val = ", ".join(x for x in (f"{len(err)} errores" if err else "", f"{largos} pasos > 300 car." if largos else "", f"{pild} píldoras sin pieza visible" if pild else "",
                                        f"{len(reg)} regresiones" if reg else "") if x) or "ok"
        print(f"| {lam} | " + ("" if sinval else f"{val} | ") + f"{'; '.join(b[:120] for b in bloq) or 'ok'} | {'; '.join(x[:90] for x in avi) or '-'} |")
    print(f"\n{len(filas)} láminas · {time.time() - t0:.0f} s")
    return 1 if malo else 0


if __name__ == "__main__":
    sys.exit(main())
