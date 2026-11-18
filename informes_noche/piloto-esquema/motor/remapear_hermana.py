"""Receta 3b con otra numeración: cambia los números de pieza de la hermana por los de esta lámina, UNA sola vez y en todos lados.

  python remapear_hermana.py <lamina> --desde <hermana> --mapa '{"1":"3","8":"8",...}' [--arte] [--escribir]
        [--catalogo <moto> --figura N] [--espejo <x> --mapa-lado '{"10":"30","11":"31",...}']

- Parte de datos/<hermana>.json (o de datos/<lamina>.json si ya existe y trae «remapeo» de esa hermana) y escribe datos/<lamina>.json.
- El cambio es simultáneo (3→1 y 1→3 no se pisan) y cubre: piezas (id y n, también «5a»→«3a»), pasos[].m, funciona, fichas
  (claves, conecta, efectos), enlaces [[n|…]] de todos los textos, ids de cadenas («Si falla»), sujeta, ocultas, carcasas,
  ordenChips, nombres, kits, refsFigura, contexto[].despuesDe y v2 (grupos, torn, con3d, toqueExtra).
- Idempotente: anota {"remapeo": {"desde", "mapa"}} y "hermana" en el JSON; si ya está con el mismo mapa no hace nada,
  y con otro mapa se niega (remapear dos veces manda los enlaces a la ficha equivocada). Los números que no están en el mapa
  quedan igual; las piezas de la hermana sin número nuevo se listan para quitarlas o dibujarlas.
- --arte: copia también el -arte.js de la hermana y lista sus funciones y rótulos con su línea (no hace falta leerlo entero).
- El mapa puede tener identidades («8»:«8»): la pieza conserva su número.
- --espejo X --mapa-lado: el lado repetido (dos barras con números distintos y la hermana dibuja una sola): duplica piezas
  (reflejadas en x = X: anclas, `et`, biblioteca y `tr` para el arte), fichas, nombres, enlaces, grupos, pasos y sujeta, con
  «izquierda/derecha» cambiados en la copia. Los números del mapa-lado son los ya remapeados.
- Al final lista lo heredado que el catálogo nuevo no respalda: cada ficha cuyo nombre trae una pieza que su descripción no
  dice (o-ring donde el catálogo dice GASKET, «asiento»), y piezas nombradas en los textos que la figura nueva no tiene
  («tija de arriba»). Catálogo: --catalogo/--figura o los de datos/<lamina>.esqueleto.json. Revísalo antes de la revisora.
- Imprime cuántas piezas de la figura nueva cubre la hermana (%): con menos del 50 %, combina hermanas (--arte-extra) o
  parte de la biblioteca y plantillas. Lista también las cifras con unidad heredadas (dientes, mm, L, N·m, balineras 6xxx,
  «cuatro resortes») que el catálogo nuevo no respalda.
- --arte-extra <lamina2>:<funcion1,funcion2>: con --arte, trae esas funciones del -arte.js de una segunda hermana (avisa de
  degradados url(#…) y ayudantes que no existen en el arte copiado).
- Sin --escribir: solo dice qué cambiaría.
Después: plantillas_ficha.py --hermana, separar_numeros.py y autocontrol.py --rapido (avisa si un enlace o una cadena quedó con
el número viejo).
"""
import json, pathlib, re, sys

AQUI = pathlib.Path(__file__).resolve().parent
ENLACE = re.compile(r"\[\[([^|\]]+)\|")


def hacer_m(N):
    def m(x):
        if not isinstance(x, str): return x
        if x in N: return N[x]
        r = re.fullmatch(r"(\d+)([a-z])", x)
        return N[r.group(1)] + r.group(2) if r and r.group(1) in N else x
    return m


def remapear(D, N):
    m = hacer_m(N)
    lista = lambda xs: [m(x) for x in xs] if isinstance(xs, list) else xs
    claves = lambda d: {m(k): v for k, v in d.items()} if isinstance(d, dict) else d

    def textos(x):   # enlaces [[n|…]] en cualquier texto, en una sola pasada
        if isinstance(x, str): return ENLACE.sub(lambda r: f"[[{m(r.group(1))}|", x)
        if isinstance(x, list): return [textos(v) for v in x]
        if isinstance(x, dict): return {k: textos(v) for k, v in x.items()}
        return x
    D = textos(D)
    for p in D.get("piezas", []):
        p["id"] = m(p.get("id")); p["n"] = m(p.get("n"))
    for P in D.get("pasos", []):
        if "m" in P: P["m"] = claves(P["m"])
    for P in D.get("funciona", {}).get("pasos", []):
        if isinstance(P.get("s"), dict) and any(k in N for k in P["s"]): P["s"] = claves(P["s"])
    D["fichas"] = claves(D.get("fichas", {}))
    for F in D["fichas"].values():
        for c in ("conecta", "efectos"):
            if isinstance(F.get(c), list): F[c] = [m(x) if isinstance(x, str) else [m(x[0])] + x[1:] if isinstance(x, list) and x else x for x in F[c]]
    for c in D.get("cadenas", []):
        c["p"] = [[m(k), t] for k, t in c.get("p", [])]
    if isinstance(D.get("sujeta"), dict): D["sujeta"] = {m(k): lista(v) for k, v in D["sujeta"].items()}
    for k in ("ocultas", "ordenChips", "refsFigura"):
        if k in D: D[k] = lista(D[k])
    for c in D.get("carcasas", []): c["id"] = m(c.get("id"))
    if isinstance(D.get("nombres"), dict): D["nombres"] = claves(D["nombres"])
    if isinstance(D.get("kits"), dict): D["kits"] = {m(k): lista(v) for k, v in D["kits"].items()}
    for c in D.get("contexto", []):
        if "despuesDe" in c: c["despuesDe"] = m(c["despuesDe"])
    v2 = D.get("v2", {})
    for g in v2.get("grupos", []):
        g["piezas"] = lista(g.get("piezas", []))
        for t in g.get("torn", []): t["ids"] = lista(t.get("ids", []))
    for k in ("con3d", "toqueExtra"):
        if isinstance(v2.get(k), list): v2[k] = lista(v2[k])
        elif isinstance(v2.get(k), dict): v2[k] = claves(v2[k])
    return D


LADOS = [("izquierd", "derech"), ("Izquierd", "Derech"), ("IZQUIERD", "DERECH"), ("LEFT", "RIGHT")]


def cambia_lado(t):
    if not isinstance(t, str): return t
    for a, b in LADOS: t = t.replace(a, "\0").replace(b, a).replace("\0", b)
    return t


def espejar(D, L, X):
    """Duplica el lado repetido: L = {número: número del otro lado}, reflejado en x = X."""
    import copy
    hl = hacer_m(L); mx = lambda x: round(2 * X - x, 1)
    def textos(x):
        if isinstance(x, str): return cambia_lado(ENLACE.sub(lambda r: f"[[{hl(r.group(1))}|", x))
        if isinstance(x, list): return [textos(v) for v in x]
        if isinstance(x, dict): return {k: textos(v) for k, v in x.items()}
        return x
    nuevas = []
    for pz in D.get("piezas", []):
        nuevas.append(pz)
        if hl(pz.get("n")) == pz.get("n"): continue
        q = copy.deepcopy(pz); q["id"], q["n"] = hl(pz["id"]), hl(pz["n"])
        if "anc" in q: q["anc"] = [mx(q["anc"][0]), q["anc"][1]]
        if "et" in q: q["et"] = [-q["et"][0], q["et"][1]]
        if "comun" in q and isinstance(q.get("p"), dict):
            if "x" in q["p"]: q["p"]["x"] = mx(q["p"]["x"])
            for k in ("puntos", "contorno"):
                if k in q["p"]: q["p"][k] = [[-a, b] + list(r) for a, b, *r in q["p"][k]]
        else: q["tr"] = f"translate({round(2 * X, 1)} 0) scale(-1 1)" + (f" {pz['tr']}" if pz.get("tr") else "")
        nuevas.append(q)
    D["piezas"] = nuevas
    F = D.get("fichas", {})
    for k in list(F):
        if hl(k) != k and hl(k) not in F:
            G = textos(copy.deepcopy(F[k]))
            if G.get("nombre") == F[k].get("nombre"): G["nombre"] = F[k]["nombre"] + " (otro lado)"
            F[hl(k)] = G
    if isinstance(D.get("nombres"), dict):
        for k in list(D["nombres"]):
            if hl(k) != k and hl(k) not in D["nombres"]: D["nombres"][hl(k)] = F.get(hl(k), {}).get("nombre") or cambia_lado(D["nombres"][k])
    for P in D.get("pasos", []):
        for k in list(P.get("m", {})):
            if hl(k) != k and hl(k) not in P["m"]: v = P["m"][k]; P["m"][hl(k)] = [-v[0], v[1]] + list(v[2:]) if isinstance(v, list) else v
    if isinstance(D.get("sujeta"), dict):
        for k in list(D["sujeta"]):
            if hl(k) != k: D["sujeta"][hl(k)] = [hl(x) for x in D["sujeta"][k]]
    for k in ("ocultas", "ordenChips", "refsFigura"):
        if k in D: D[k] = D[k] + [hl(x) for x in D[k] if hl(x) != x and hl(x) not in D[k]]
    D["carcasas"] = D.get("carcasas", []) + [dict(c, id=hl(c["id"])) for c in D.get("carcasas", []) if hl(c.get("id")) != c.get("id")]
    grupos = []
    for g in D.get("v2", {}).get("grupos", []):
        grupos.append(g)
        ids = g.get("piezas", []) + [i for t in g.get("torn", []) for i in t.get("ids", [])]
        if ids and all(hl(i) != i for i in ids):   # el grupo entero es de un lado: grupo gemelo
            h = copy.deepcopy(g); h["id"] = g["id"] + "-2"; h["nombre"] = cambia_lado(g["nombre"]) if cambia_lado(g["nombre"]) != g["nombre"] else g["nombre"] + " (otro lado)"
            h["piezas"] = [hl(i) for i in g.get("piezas", [])]
            for t in h.get("torn", []): t["ids"] = [hl(i) for i in t["ids"]]
            if "marca" in h: h["marca"] = [mx(h["marca"][0]), h["marca"][1]]
            grupos.append(h)
        else:   # mezclado: las copias van al mismo grupo
            g["piezas"] = g.get("piezas", []) + [hl(i) for i in g.get("piezas", []) if hl(i) != i]
            for t in g.get("torn", []): t["ids"] = t["ids"] + [hl(i) for i in t["ids"] if hl(i) != i]
    if "v2" in D: D["v2"]["grupos"] = grupos
    return D


PALABRAS = [  # pieza en español → lo que la respalda en la descripción del catálogo (inglés o español)
    (r"o-?rings?", r"O-?RING|ORING|ANILLO"), (r"empaques?", r"GASKET|EMPAQUE|JUNTA"), (r"ret[eé]n(es)?", r"OIL SEAL|SEAL|RETEN"),
    (r"guardapolvos?", r"DUST|GUARDAPOLVO|SEAL"), (r"rodamientos?|balineras?", r"BEARING|BALINERA|RODAMIENTO"),
    (r"bujes?", r"BUSH|COLLAR|BUJE|SLIDE METAL|METAL"), (r"resortes?", r"SPRING|RESORTE"), (r"seguros?", r"CIRCLIP|CLIP|SEGURO|RING"),
    (r"asientos?", r"SEAT|ASIENTO"), (r"arandelas?", r"WASHER|ARANDELA"), (r"tap[oó]n(es)?", r"CAP|PLUG|BOLT|TAPON|TAPA"),
    (r"pist[oó]n(es)?", r"PISTON"), (r"amortiguador(es)?", r"DAMPER|ABSORBER|AMORTIG|CYLINDER|ROD")]
EQUIPO = [  # piezas que una moto tiene y otra no: si la figura nueva no las trae, las frases de la hermana sobran
    (r"tija de arriba|tija superior|puente superior", r"UPPER BRACKET|CROWN|HANDLE CROWN|BRACKET, UPPER|TIJA SUP"),
    (r"tija de abajo|tija inferior|puente inferior", r"UNDER BRACKET|LOWER BRACKET|BRACKET, UNDER|STEERING STEM|TIJA INF"),
    (r"\bABS\b", r"ABS|HYDRAULIC UNIT"), (r"\bCBS\b", r"CBS|EQUALIZER"), (r"carburador", r"CARBURETOR|CARBURADOR"),
    (r"cadena", r"CHAIN|CADENA"), (r"correa", r"BELT|CORREA"), (r"radiador|refrigerante", r"RADIATOR|RADIADOR"), (r"tambor|bandas", r"SHOE|BANDA|DRUM|TAMBOR")]


NUM_PAL = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8}
CIFRA = re.compile(r"\b\d+(?:[.,]\d+)?(?:\s*[x×]\s*\d+(?:[.,]\d+)?)*\s*(?:mm|cm|L|cc|ml|N·m|kgf|dientes|T)\b|\b6[0-3]\d{2}(?:[-\s]?(?:2RS|ZZ|Z))?\b|\b\d+\s?T\b")

def cifras(D, C, fig):
    """Cifras con unidad y cantidades en palabras de las fichas que el catálogo nuevo no respalda (restos de la hermana)."""
    norm = lambda t: re.sub(r"\s+", "", t.upper().replace("×", "X").replace(",", "."))
    toda = norm(" ".join(q.get("descripcion", "") + " " + q.get("descripcion_en", "") for q in C["partes"]))
    cant = {q["ref"]: q.get("cantidad") for q in C["partes"]}
    o = []
    for k, F in D.get("fichas", {}).items():
        t = re.sub(r"<[^>]+>|\[\[[^|\]]+\||\]\]", "", json.dumps({x: F.get(x) for x in F if x not in ("cat", "codigo", "certeza")}, ensure_ascii=False))
        for m in CIFRA.finditer(t):
            c = norm(m.group(0)); c0 = re.sub(r"(MM|CM|L|CC|ML|N·M|KGF|DIENTES)$", "", c)
            if c0 and c0 not in toda: o.append(f"ficha {k}: «{m.group(0)}» no está en la fig. {fig}")
        q = cant.get(re.sub(r"[a-z]$", "", k))
        for m in re.finditer(r"\b(dos|tres|cuatro|cinco|seis|siete|ocho)\b", t, re.I):
            if q and NUM_PAL[m.group(1).lower()] != q: o.append(f"ficha {k}: «{t[m.start():m.end() + 12].strip()}…», el catálogo dice {q}")
    return o

def ajenas(D, lam, cat_moto=None, fig=None, N=None):
    """Lo heredado que el catálogo nuevo no respalda (una línea por hallazgo)."""
    import re as _re
    esq = AQUI / "datos" / f"{lam}.esqueleto.json"
    if not cat_moto and esq.exists():
        E = json.loads(esq.read_text(encoding="utf-8")); cat_moto, fig = E.get("catalogo"), E.get("figura")
    if not cat_moto: print("  (sin --catalogo/--figura ni esqueleto: no se revisó lo heredado contra el catálogo nuevo)"); return
    C = json.loads((AQUI / "catalogo" / f"{cat_moto}.json").read_text(encoding="utf-8"))["figuras"].get(str(fig))
    if not C: print(f"  (la figura {fig} no está en catalogo/{cat_moto}.json)"); return
    desc = {}
    for q in C["partes"]: desc[q["ref"]] = desc.get(q["ref"], "") + " " + q.get("descripcion", "") + " " + q.get("descripcion_en", "")
    toda = " ".join(desc.values()).upper()
    sin_tag = lambda t: _re.sub(r"<[^>]+>|\[\[[^|\]]+\||\]\]", "", t or "")
    o = []
    for k, F in D.get("fichas", {}).items():
        d = desc.get(_re.sub(r"[a-z]$", "", k), "").upper()
        if not d: continue
        for es, en in PALABRAS:
            m = _re.match(rf"\s*({es})\b", F.get("nombre", ""), _re.I)   # el sustantivo que encabeza el nombre
            if m and not _re.search(en, d): o.append(f"ficha {k} «{F['nombre']}»: «{m.group(0)}», pero el catálogo dice «{d.strip()[:50]}»")
    todo = " ".join(sin_tag(json.dumps(x, ensure_ascii=False)) for x in (D.get("pasos"), D.get("fichas"), D.get("funciona"), D.get("cadenas"), D.get("cabeza"), D.get("textoArmado")))
    for es, en in EQUIPO:
        n = len(_re.findall(es, todo, _re.I))
        if n and not _re.search(en, toda): o.append(f"«{_re.search(es, todo, _re.I).group(0)}» aparece {n} vez/veces y la fig. {fig} no trae esa pieza (¿equipo de la hermana?)")
    if N is not None:
        refs = {q["ref"] for q in C["partes"] if not re.search(r"\bKIT\b|COMPL", q.get("descripcion", ""), re.I)}
        cub = refs & set(N.values()); pct = round(100 * len(cub) / max(1, len(refs)))
        print(f"  la hermana cubre {len(cub)} de {len(refs)} piezas de la fig. {fig} ({pct} %)" + ("" if pct >= 50 else
              " · MENOS DE LA MITAD: combina con otra hermana (--arte-extra) o parte de la biblioteca y plantillas"))
        falta = sorted(refs - cub, key=lambda x: (len(x), x))
        if falta: print(f"  sin pieza de la hermana: {', '.join(falta)}")
    o += cifras(D, C, fig)
    print(f"  heredado sin respaldo en el catálogo nuevo ({len(o)}; corrígelo antes de la revisora):" if o else "  heredado contra el catálogo nuevo: sin diferencias de nombre ni de equipo")
    for x in o[:25]: print("   - " + x)
    if len(o) > 25: print(f"   … y {len(o) - 25} más")


def copiar_arte(D, herm, lam):
    """Copia datos/<hermana>-arte.js a datos/<lamina>-arte.js (si no existe) y lista solo lo que suele cambiar:
    funciones de arte y rótulos de texto, con su línea (así no hace falta leer el arte entero)."""
    org = AQUI / "datos" / f"{D.get('arte') or herm}-arte.js"; dst = AQUI / "datos" / f"{lam}-arte.js"
    if not org.exists(): print(f"aviso: no está {org.name}"); return
    if dst.exists(): print(f"{dst.name} ya existe: no se copió")
    else: dst.write_text(org.read_text(encoding="utf-8").replace(herm, lam), encoding="utf-8"); print(f"copiado {org.name} → {dst.name}")
    D["arte"] = lam
    L = dst.read_text(encoding="utf-8").splitlines()
    fun = [f"{i + 1}:{m.group(1)}" for i, l in enumerate(L) for m in re.finditer(r"function\s+(arte\w+)", l)]
    rot = [f"{i + 1}:«{t.strip()[:40]}»" for i, l in enumerate(L) for t in re.findall(r">([^<>{}$]{3,})<", l) if re.search(r"[A-Za-zÁÉÍÓÚáéíóúñ]{3}", t)]
    print(f"  funciones ({len(fun)}): {' '.join(fun)}")
    print(f"  rótulos de texto ({len(rot)}; cámbialos si nombran otra moto o figura): {' '.join(rot)}")
    usadas = {p.get("arte") for p in D.get("piezas", [])} | {c.get("arte") for c in D.get("contexto", [])}
    sobran = [f.split(":")[1] for f in fun if f.split(":")[1] not in usadas]
    if sobran: print(f"  sin pieza que las use (bórralas o úsalas): {', '.join(sobran)}")


def arte_extra(lam, spec):
    """--arte-extra lamina2:f1,f2 → copia esas funciones del arte de lamina2 al de esta lámina y las exporta."""
    org, _, fs = spec.partition(":"); src = (AQUI / "datos" / f"{org}-arte.js").read_text(encoding="utf-8")
    dst = AQUI / "datos" / f"{lam}-arte.js"; t = dst.read_text(encoding="utf-8")
    for f in [x for x in fs.split(",") if x]:
        if re.search(rf"function\s+{f}\s*\(", t): print(f"  {f}: ya está"); continue
        m = re.search(rf"^function\s+{f}\s*\(.*?^\}}\s*$", src, re.S | re.M)
        if not m: print(f"  aviso: {f} no está en {org}-arte.js"); continue
        cuerpo = m.group(0).replace(org, lam)
        t = t.replace("return {defs:", f"/* traída de {org} (--arte-extra) */\n{cuerpo}\nreturn {{defs:", 1).replace("return {defs:DEFS,", f"return {{defs:DEFS,{f},", 1)
        ids = sorted(set(re.findall(r"url\(#([\w-]+)\)", cuerpo)) - set(re.findall(r'id="([\w-]+)"', t)))
        ayud = sorted({x for x in re.findall(r"\b([a-zA-Z_]\w*)\(", cuerpo) if not re.search(rf"(function\s+{x}\b|const\s+{x}\s*=)", t)}
                      - {"function", "if", "for", "while", "return", "Math", "round", "max", "min", "map", "join", "forEach", "push", "abs", "cos", "sin", "hypot", "atan2", "sqrt", "url", "rgba", "rotate", "translate", "scale", "matrix", "slice", "filter", "toFixed", "concat", "fill", "keys", "entries", "replace", "repeat", "String", "Number", "Array", "from", "includes", "indexOf", "reduce", "split", "parseFloat", "parseInt", "floor", "ceil", "PI"})
        print(f"  traída {f} de {org}" + (f" · degradados que faltan: {', '.join(ids)}" if ids else "") + (f" · ayudantes que faltan: {', '.join(ayud)}" if ayud else ""))
    dst.write_text(t, encoding="utf-8")


def main():
    a = sys.argv[1:]
    if len(a) < 1 or "--desde" not in a or "--mapa" not in a: print(__doc__); return 1
    lam, herm = a[0], a[a.index("--desde") + 1]
    N = {str(k): str(v) for k, v in json.loads(a[a.index("--mapa") + 1]).items()}
    destino = AQUI / "datos" / f"{lam}.json"
    if destino.exists():
        D = json.loads(destino.read_text(encoding="utf-8"))
        hecho = D.get("remapeo")
        if hecho and hecho.get("desde") == herm:
            if hecho.get("mapa") == N: print(f"{lam}: ya remapeado desde {herm} con este mapa; no se aplica otra vez"); return 0
            print(f"{lam}: ya se remapeó desde {herm} con otro mapa. Remapear encima manda los enlaces a la ficha equivocada:\n"
                  f"  borra datos/{lam}.json (o su clave «remapeo») y vuelve a correr desde la hermana."); return 1
    D = json.loads((AQUI / "datos" / f"{herm}.json").read_text(encoding="utf-8"))
    viejos = {p.get("n") for p in D.get("piezas", []) if p.get("n")}
    orden = lambda xs: sorted(xs, key=lambda x: (len(x), x))
    quedan = {v for v in viejos if hacer_m(N)(v) == v and re.sub(r"[a-z]$", "", v) not in N and re.fullmatch(r"\d+[a-z]?", v)}
    choque = orden(quedan & set(N.values()))   # un número viejo sin mapa que coincide con uno nuevo: dos piezas con el mismo número
    if choque: print(f"error: {', '.join(choque)} quedan sin mapa y chocan con números nuevos; agrégalos al mapa (aunque sea a «x{choque[0]}» para quitarlos)"); return 1
    sin = orden(quedan)
    D = remapear(D, N)
    D["lamina"], D["hermana"], D["remapeo"] = lam, herm, {"desde": herm, "mapa": N}
    if "--espejo" in a:
        L = {str(k): str(v) for k, v in json.loads(a[a.index("--mapa-lado") + 1]).items()}
        D = espejar(D, L, float(a[a.index("--espejo") + 1])); D["remapeo"]["lado"] = L
        print(f"  espejo en x = {a[a.index('--espejo') + 1]}: {len(L)} números del otro lado (piezas, fichas, enlaces, grupos y pasos)")
    ajenas(D, lam, a[a.index("--catalogo") + 1] if "--catalogo" in a else None, a[a.index("--figura") + 1] if "--figura" in a else None, N)
    print(f"{lam} desde {herm}: {len(N)} números cambiados" + (f" · quedan con el mismo número (revisa que sean la misma pieza; si no, mapéalas): {', '.join(sin)}" if sin else ""))
    if "--escribir" not in a: print("(sin --escribir: no se guardó)"); return 0
    if "--arte" in a: copiar_arte(D, herm, lam)
    if "--arte" in a and "--arte-extra" in a: arte_extra(lam, a[a.index("--arte-extra") + 1])
    destino.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escrito datos/{lam}.json; ahora: plantillas_ficha.py datos/{lam}.json --hermana {herm} --escribir")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
