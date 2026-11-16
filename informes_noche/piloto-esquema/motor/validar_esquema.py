"""Valida el JSON de una lámina del esquema sin abrir el navegador (corre en menos de un segundo).

Uso:
  python validar_esquema.py datos/nmax-fig22.json
  python validar_esquema.py datos/nmax-fig12.json --refs 1-18 --ancho 301

Qué revisa:
  1. Campos obligatorios (lámina, piezas, pasos, fichas, «Cómo funciona», «Cuándo»…).
  2. Cada número de la figura (refsFigura del JSON, o --refs) tiene al menos una pieza y una ficha.
  3. Referencias: pasos → piezas existentes; chips, ocultas y cadenas → fichas; arte → funciones del módulo *-arte.js.
  4. Anclas y números dentro del encuadre armado; en el despiece, el encuadre estimado (el real lo calcula el
     motor con el tamaño del arte, así que aquí es una cota optimista: el navegador tiene la última palabra).
  5. Áreas de toque: la mitad de la distancia entre dos números tocables a la vez (en pantalla, con el ancho del
     dibujo en un celular de 360 px = 301 px) no puede ser menor que radioToqueMin (9 px por defecto).
  6. Clases: todas con el prefijo esq- y ninguna que ya exista en talleres/static/talleres/css/tallerya.css.
Lo que no puede ver: si el arte de una pieza tapa el número de otra (eso se mide con elementFromPoint).
Sale con código 1 si hay errores.
"""
import json, math, pathlib, re, sys, argparse
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]  # TallerYa/
CSS_SITIO = RAIZ / "talleres" / "static" / "talleres" / "css" / "tallerya.css"
ASPECTO = 900 / 700

OBLIG = {
    "lamina": str, "moto": str, "figura": (int, str), "arte": str, "cabeza": dict, "visor": dict, "textos": dict,
    "encuadreArmado": list, "piezas": list, "pasos": list, "nombres": dict, "fichas": dict,
    "ordenChips": list, "ocultas": list, "textoArmado": str, "cadenas": list, "cuando": list,
    "funciona": dict, "fuentes": dict, "pie": str,
}
OBLIG_PIEZA = {"id": str, "n": str, "anc": list, "et": list, "vis": str}  # y «arte» o «comun» (biblioteca)
OBLIG_FICHA = ["nombre", "cat", "que", "sirve"]
OBLIG_TEXTOS = ["pestanasAria", "laminaAria", "introFunciona", "introCadenas", "introCuando"]


def rango(txt):
    out = []
    for parte in txt.split(","):
        if "-" in parte:
            a, b = parte.split("-"); out += [str(i) for i in range(int(a), int(b) + 1)]
        elif parte.strip():
            out.append(parte.strip())
    return out


def clases_sitio():
    if not CSS_SITIO.exists():
        return set()
    t = re.sub(r"/\*.*?\*/", "", CSS_SITIO.read_text(encoding="utf-8"), flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{[^{}]*\}", "{}", t)
    return set(re.findall(r"\.([a-zA-Z][\w-]*)", t))


def clases_en(texto):
    """Clases fijas dentro de class="…" (se ignoran las partes con ${…})."""
    out = set()
    for v in re.findall(r'class="([^"]*)"', texto):
        v = re.sub(r"\$\{[^}]*\}", " ", v)
        out |= {t for t in v.split() if re.fullmatch(r"[a-zA-Z][\w-]*", t)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--refs", help="números de la figura, p. ej. 1-15 o 1-10,12 (si no, refsFigura del JSON)")
    ap.add_argument("--ancho", type=float, default=301, help="ancho del dibujo en pantalla, en px (360 px de celular = 301)")
    ap.add_argument("--previa", action="store_true", help="borrador: los textos de introducción y «Cómo funciona» vacíos son aviso, no error")
    a = ap.parse_args()
    ruta = pathlib.Path(a.json)
    D = json.loads(ruta.read_text(encoding="utf-8"))
    err, avi = [], []

    # 1. campos obligatorios
    for k, tipo in OBLIG.items():
        if k not in D:
            err.append(f"falta el campo «{k}»")
        elif not isinstance(D[k], tipo):
            err.append(f"«{k}» debería ser {getattr(tipo, '__name__', None) or ' o '.join(t.__name__ for t in tipo)}")
    if err:
        return fin(err, avi)
    for k in OBLIG_TEXTOS:
        if not D["textos"].get(k):
            (avi if a.previa and k.startswith("intro") else err).append(f"falta textos.{k}" + (" (previa)" if a.previa and k.startswith("intro") else ""))
    if a.previa and not D.get("funciona", {}).get("pasos"):
        avi.append("«Cómo funciona» sin pasos (previa)")
    for k in ["cinta", "titulo", "aviso"]:
        if not D["cabeza"].get(k):
            err.append(f"falta cabeza.{k}")
    for k in ["vbCelular", "vbEscritorio", "pasos"]:
        if k not in D["funciona"]:
            err.append(f"falta funciona.{k}")
    for i, p in enumerate(D["funciona"].get("pasos", [])):
        if not p.get("t") or "s" not in p:
            err.append(f"funciona.pasos[{i}] necesita «t» (texto) y «s» (estado)")
    for i, r in enumerate(D["cuando"]):
        for k in ["que", "cuando", "fuente"]:
            if not r.get(k):
                err.append(f"cuando[{i}] sin «{k}»")
    for k in ["seguro", "aproximado", "lista"]:
        if not D["fuentes"].get(k):
            avi.append(f"fuentes.{k} vacío")
    vb = D["encuadreArmado"]
    if len(vb) != 4:
        err.append("encuadreArmado debe ser [x, y, ancho, alto]")
    elif abs(vb[2] / vb[3] - ASPECTO) > 0.01:
        err.append(f"encuadreArmado con proporción {vb[2]/vb[3]:.3f}; debe ser 900:700 = {ASPECTO:.3f} (si no, el encuadre salta)")

    piezas = D["piezas"]
    ids = set()
    for i, p in enumerate(piezas):
        for k, tipo in OBLIG_PIEZA.items():
            if not isinstance(p.get(k), tipo):
                err.append(f"piezas[{i}] ({p.get('id')}): falta «{k}» ({tipo.__name__})")
        if p.get("id") in ids:
            err.append(f"pieza repetida: {p.get('id')}")
        ids.add(p.get("id"))
        if p.get("vis") not in ("arm", "exp"):
            err.append(f"pieza {p.get('id')}: vis debe ser «arm» (se ve armada) o «exp» (solo en el despiece)")
    if err:
        return fin(err, avi)
    fichas = D["fichas"]
    for k, F in fichas.items():
        if F.get("ctx"):
            continue
        for c in OBLIG_FICHA:
            if not F.get(c):
                err.append(f"ficha {k}: falta «{c}»")
        if not F.get("fallas"):
            avi.append(f"ficha {k}: sin «fallas»")

    # 2. números de la figura
    cat = catalogo_de(D, avi)
    refs = rango(a.refs) if a.refs else (list(dict.fromkeys(q["ref"] for q in cat["partes"])) if cat else [str(r) for r in D.get("refsFigura", [])])
    if not refs:
        avi.append("sin refsFigura ni --refs: no se comprobó que estén todos los números del catálogo")
    ns = {p["n"] for p in piezas}
    kits = D.get("kits") or {}   # conjuntos de venta (clutch completo, juego de discos): sin dibujo, ni grupo, ni ficha propia
    kits = {str(k): [] for k in kits} if isinstance(kits, list) else {str(k): [str(x) for x in v] for k, v in kits.items()}
    for k, trae in kits.items():
        if k in ns: err.append(f"el kit {k} tiene pieza dibujada: los kits van sin dibujo ni grupo (solo en las fichas de lo que traen)")
        for x in trae:
            if x not in fichas: err.append(f"el kit {k} dice que trae la {x}, que no tiene ficha")
            elif "kit" not in json.dumps(fichas[x], ensure_ascii=False).lower(): avi.append(f"ficha {x}: no dice que se vende en el kit {k} (ponlo en «cat»: «… · también en el kit ref. {k}»)")
    for r in refs:
        if r in kits: continue
        if r not in ns:
            err.append(f"el número {r} de la figura no tiene pieza dibujada")
        if r not in fichas:
            err.append(f"el número {r} de la figura no tiene ficha")
    for n in sorted(ns, key=lambda x: (len(x), x)):
        if n not in fichas:
            err.append(f"la pieza {n} no tiene ficha")
        if n not in D["nombres"]:
            err.append(f"la pieza {n} no tiene nombre corto (nombres)")
        if refs and n not in refs:
            avi.append(f"la pieza {n} no está entre los números de la figura")

    # 3. referencias cruzadas
    for i, P in enumerate(D["pasos"]):
        if not P.get("t"):
            err.append(f"pasos[{i}] sin texto")
        for pid in P.get("m", {}):
            if pid not in ids:
                err.append(f"pasos[{i}] mueve «{pid}», que no es una pieza")
    for k in D["ordenChips"]:
        if k not in fichas:
            err.append(f"ordenChips: «{k}» no tiene ficha")
    for c in D.get("carcasas", []):
        if c.get("id") not in ids:
            err.append(f"carcasas: «{c.get('id')}» no es el id de una pieza")
        for campo in ("transparente", "rayosx"):
            if not isinstance(c.get(campo), (int, float)) or not 0 <= c[campo] <= 1:
                err.append(f"carcasas «{c.get('id')}»: «{campo}» tiene que ser un número entre 0 y 1")
    for k in D["ocultas"]:
        if k not in ns:
            err.append(f"ocultas: «{k}» no es una pieza")
    for c in D["cadenas"]:
        for k, _t in c.get("p", []):
            if k not in fichas:
                err.append(f"cadena «{c.get('t')}»: «{k}» no tiene ficha")
    arte_js = ruta.with_name(ruta.stem + "-arte.js")
    if arte_js.exists():
        tarte = arte_js.read_text(encoding="utf-8")
        exp = re.search(r"return\s*\{defs:DEFS,(.*?)funciona:", tarte, re.S)
        nombres_arte = set(re.findall(r"\w+", exp.group(1))) if exp else set()
        for p in piezas:
            if "arte" in p and p["arte"] not in nombres_arte:
                err.append(f"pieza {p['id']}: el arte «{p['arte']}» no está exportado en {arte_js.name}")
        for c in D.get("contexto", []):
            if c.get("arte") and c["arte"] not in nombres_arte:
                err.append(f"contexto: el arte «{c['arte']}» no está exportado")
    else:
        tarte = ""
        avi.append(f"no está {arte_js.name}: no se revisó el arte")

    # 4. encuadres
    suma = {}
    for P in D["pasos"]:
        for pid, (dx, dy) in P.get("m", {}).items():
            s = suma.setdefault(pid, [0, 0]); s[0] += dx; s[1] += dy
    R_DISCO = 12  # radio del círculo del número en unidades del dibujo (aprox., a escala 1)
    x0, y0, w, h = vb
    for p in piezas:
        ax, ay = p["anc"]; lx, ly = ax + p["et"][0], ay + p["et"][1]
        if not (x0 <= ax <= x0 + w and y0 <= ay <= y0 + h):
            avi.append(f"pieza {p['id']}: el ancla queda fuera del encuadre armado")
        if p["vis"] == "arm" and not (x0 + R_DISCO <= lx <= x0 + w - R_DISCO and y0 + R_DISCO <= ly <= y0 + h - R_DISCO):
            err.append(f"número {p['n']} ({p['id']}): queda fuera o pegado al borde del encuadre armado ({lx:.0f}, {ly:.0f})")
    fin_pos = {p["id"]: (p["anc"][0] + p["et"][0] + suma.get(p["id"], [0, 0])[0], p["anc"][1] + p["et"][1] + suma.get(p["id"], [0, 0])[1]) for p in piezas}
    xs = [x for x, _ in fin_pos.values()]; ys = [y for _, y in fin_pos.values()]
    ex0, ey0, ex1, ey1 = min(xs) - 34, min(ys) - 34, max(xs) + 34, max(ys) + 34  # como el motor: ±20 del número y 14 de margen
    ew, eh = ex1 - ex0, ey1 - ey0
    if ew / eh < ASPECTO: ew = eh * ASPECTO
    else: eh = ew / ASPECTO

    # 5. áreas de toque (en px de pantalla)
    rmin = D.get("radioToqueMin", 9)
    def revisar(nombre, pts, escala):
        peor = None
        for i, (ka, pa) in enumerate(pts):
            for kb, pb in pts[i + 1:]:
                d = math.dist(pa, pb) * escala / 2
                if peor is None or d < peor[0]:
                    peor = (d, ka, kb)
                if d < rmin:
                    err.append(f"{nombre}: los números {ka} y {kb} quedan a {d*2:.0f} px; su área de toque sería de {d:.1f} px de radio (mínimo {rmin})")
        return peor
    arm = [(p["n"] + "·" + p["id"], (p["anc"][0] + p["et"][0], p["anc"][1] + p["et"][1])) for p in piezas if p["vis"] == "arm"]
    trans = [(p["n"] + "·" + p["id"], (p["anc"][0] + p["et"][0], p["anc"][1] + p["et"][1])) for p in piezas]
    exp_ = [(p["n"] + "·" + p["id"], fin_pos[p["id"]]) for p in piezas]
    e_arm, e_exp = a.ancho / w, a.ancho / ew
    peores = {"armado": revisar("armado", arm, e_arm), "despiece": revisar("despiece", exp_, e_exp)}
    pt = revisar("armado transparente (los números de adentro aparecen al tocarlos)", trans, e_arm)
    if pt and pt[0] < rmin:  # en transparente los números internos están ocultos hasta tocarlos: se avisa, no se bloquea
        err[:] = [e for e in err if not e.startswith("armado transparente")]
        avi.append(f"armado transparente: {pt[1]} y {pt[2]} muy juntos ({pt[0]:.1f} px de radio); solo se ven al tocar la pieza")

    # 6. clases
    sitio = clases_sitio()
    textos = json.dumps(D, ensure_ascii=False) + tarte
    for c in sorted(clases_en(textos)):
        if not c.startswith("esq-"):
            err.append(f"clase sin prefijo esq-: «{c}»")
        if c in sitio:
            err.append(f"clase que ya existe en tallerya.css: «{c}»")
    css = AQUI / "esquema.css"
    if css.exists():
        t = re.sub(r"/\*.*?\*/", "", css.read_text(encoding="utf-8"), flags=re.S)
        for _ in range(3): t = re.sub(r"\{[^{}]*\}", "{}", t)
        malas = sorted({c for c in re.findall(r"\.([a-zA-Z][\w-]*)", t) if not c.startswith("esq-") or c in sitio})
        if malas:
            err.append(f"esquema.css tiene clases prohibidas: {', '.join(malas)}")

    import mas_controles
    mas_controles.revisar(D, ruta, cat, err, avi)

    print(f"Lámina {D['lamina']} · {len(piezas)} piezas · {len(D['pasos'])} pasos · {len(fichas)} fichas · {len(refs)} números de la figura")
    for k, v in peores.items():
        if v:
            print(f"  toque más justo en {k}: {v[1]} con {v[2]}, radio {v[0]:.1f} px (mínimo {rmin})")
    print(f"  despiece estimado: [{ex0:.0f}, {ey0:.0f}, {ew:.0f}, {eh:.0f}] (el motor lo agranda con el tamaño del arte)")
    return fin(err, avi)


def catalogo_de(D, avi):
    """Figura de la lámina en catalogo/<D.catalogo>.json (sacado del PDF una vez por moto)."""
    nombre = D.get("catalogo")
    if not nombre:
        avi.append("sin «catalogo» en el JSON: los números salen de refsFigura")
        return None
    C = json.loads((AQUI / "catalogo" / f"{nombre}.json").read_text(encoding="utf-8"))
    fig = C["figuras"].get(str(D["figura"]))
    if not fig:
        avi.append(f"la figura {D['figura']} no está en catalogo/{nombre}.json")
    return fig


def fin(err, avi):
    for a in avi:
        print("  aviso:", a)
    for e in err:
        print("  ERROR:", e)
    print("OK" if not err else f"{len(err)} error(es)")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
