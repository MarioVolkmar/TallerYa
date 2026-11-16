"""Extrae las tablas de partes de un catálogo (PDF, solo lectura) a JSON.
Uso:
  python extraer_catalogo.py <pdf> <salida.json>                              Yamaha (cabecera 'PART NO.'): todas las figuras
  python extraer_catalogo.py <pdf> <salida.json> --figura 14 --columna TEC [--moto boxer-ct100]
      Otros catálogos (Auteco/Bajaj y genéricos en español: cabecera 'PARTE'/'CÓDIGO' + 'DESCRIPCIÓN' + columnas de
      versión o de cantidad): extrae solo la figura N por palabras y la agrega a <salida.json> si ya existe.
      Sin --columna, si hay varias columnas de versión, las lista y no escribe nada.
  python extraer_catalogo.py <pdf> <salida.json> --figura E4 [--moto akt-nkd125]
      Catálogo AKT (cabecera 'Ref.'/'Descripciones'/'Cant', figuras 'E- 4' = motor y 'F- 4' = chasis): la figura se
      guarda con letra y número («E4», así no choca con «F4»). Los conjuntos («Cta», «Completo») quedan en «partes»
      porque tienen número en la foto; el código se separa del EAN-13 pegado y puede ir vacío.
Usa pymupdf (words) y agrupa por columnas relativas a la cabecera."""
import argparse, json, os, re, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)
import pymupdf

def limpiar(s):
    return re.sub(r"[‐-―\x96�]", "-", s).strip()

def pagina_figura(page):
    t = page.get_text("text").split("\n")
    txt = " ".join(t[:3])
    m = re.match(r"\s*FIG\.\s*(\d+)\s+(.+?)\s*$", " ".join(x.strip() for x in t[:2] if x.strip()))
    return (m.group(1), m.group(2).strip()) if m else None

def filas_pagina(page):
    w = page.get_text("words")
    px = next((a[0] for a in w if a[4] == "PART"), None)
    if px is None:
        return []
    ytab = next(a[3] for a in w if a[4] == "PART")  # bajo la cabecera
    w = [a for a in w if a[1] > ytab + 1]
    refs = [a for a in w if a[0] < px - 22 and re.fullmatch(r"\*?\d+[a-zA-Z]?", a[4])]
    if not refs:
        return []
    ys = [(a[1] + a[3]) / 2 for a in refs]
    filas = [{"ref": a[4].lstrip("*"), "y": y, "w": []} for a, y in zip(refs, ys)]
    for a in w:
        if a in refs:
            continue
        yc = (a[1] + a[3]) / 2
        f = min(filas, key=lambda f: abs(f["y"] - yc))
        if abs(f["y"] - yc) > 14:
            continue
        f["w"].append(a)
    out = []
    for f in filas:
        cols = {"codigo": [], "desc": [], "cant": [], "nota": []}
        for a in sorted(f["w"], key=lambda a: (round(a[1] / 4), a[0])):
            x = a[0] - px
            k = "codigo" if x < 50 else "desc" if x < 205 else "cant" if x < 270 else "nota"
            cols[k].append(a[4])
        cant = " ".join(cols["cant"]).strip()
        out.append({"ref": f["ref"], "descripcion": limpiar(" ".join(cols["desc"])),
                    "cantidad": int(cant) if cant.isdigit() else cant,
                    "codigo": limpiar("".join(cols["codigo"])),
                    "nota": limpiar(" ".join(cols["nota"]))})
    return out


# ---------- catálogos que no son Yamaha (tablas en español con columnas de versión) ----------
CABECERA_COD = ("PARTE", "CÓDIGO", "CODIGO", "REFERENCIA")
NO_VERSION = {"DESCRIPCIÓN", "DESCRIPCION", "OBSERVACIÓN", "OBSERVACION", "OBSERVACIONES", "Nº.", "N°.", "Nº", "N°", "FIG.", "FIG", "NO.", "PARTE", "CÓDIGO", "CODIGO", "REFERENCIA"}

def figura_generica(page):
    t = re.sub(r"\s+", " ", page.get_text())
    m = re.search(r"FIGURA\s*N\W{0,2}\s*(\d+)\s*:?\s*([^(\d]+?)\s*(\(\s*\d+\s*/\s*\d+\s*\)|FIG\.|PARTE|\d|$)", t)
    return (m.group(1), m.group(2).strip(" :")) if m else None

def filas_genericas(page):
    """Filas de una página: [{ref, codigo, descripcion, cant:{columna: texto}, nota}] y la lista de columnas."""
    w = page.get_text("words")
    cab = next((a for a in w if a[4].upper() in CABECERA_COD), None)
    des = next((a for a in w if a[4].upper().startswith("DESCRIP")), None)
    if not cab or not des:
        return [], []
    ycab = (cab[1] + cab[3]) / 2
    banda = [a for a in w if abs((a[1] + a[3]) / 2 - ycab) < 14]
    obs = next((a for a in banda if a[4].upper().startswith("OBSERV")), None)
    xder = obs[0] if obs else page.rect.width
    cols = sorted([a for a in banda if a[0] > des[2] and a[2] <= xder + 1 and a[4].upper() not in NO_VERSION], key=lambda a: a[0])
    cols = [(a[4], (a[0] + a[2]) / 2) for a in cols]
    if not cols:
        return [], []
    ytab = max(a[3] for a in banda) + 1
    x0 = cab[0] - 30
    w = [a for a in w if a[1] > ytab and a[0] >= x0]
    anclas = [a for a in w if cab[0] - 4 <= a[0] < des[0] - 20 and re.fullmatch(r"[A-Z0-9][A-Z0-9\-]{4,}", a[4])]
    filas = [{"y": (a[1] + a[3]) / 2, "cod": a, "w": []} for a in anclas]
    if not filas:
        return [], [c[0] for c in cols]
    for a in w:
        if a in anclas:
            continue
        yc = (a[1] + a[3]) / 2
        f = min(filas, key=lambda f: abs(f["y"] - yc))
        if abs(f["y"] - yc) <= 7:
            f["w"].append(a)
    xv = cols[0][1] - 8
    out = []
    for f in sorted(filas, key=lambda f: f["y"]):
        ref = next((a[4] for a in f["w"] if a[2] < cab[0] - 2 and re.fullmatch(r"\d+[a-zA-Z]?", a[4])), "")
        desc = " ".join(a[4] for a in sorted(f["w"], key=lambda a: a[0]) if a[0] > f["cod"][2] + 2 and a[2] < xv)
        cant = {}
        for nom, cx in cols:
            v = [a[4] for a in f["w"] if abs((a[0] + a[2]) / 2 - cx) < 5]
            cant[nom] = v[0] if v else ""
        nota = " ".join(a[4] for a in f["w"] if obs and a[0] >= obs[0] - 2)
        out.append({"ref": ref, "codigo": limpiar(f["cod"][4]), "descripcion": limpiar(desc), "cant": cant, "nota": limpiar(nota)})
    return out, [c[0] for c in cols]

# ---------- catálogo AKT: «E- 4» + tabla Ref. | PLM | Articulo | Descripciones | Cant | NOTA (filas «E4-1») ----------
def clave_fig(f):
    m = re.fullmatch(r"\s*([A-Za-z])\s*-?\s*(\d+)\s*", str(f))
    return (m.group(1).upper() + m.group(2)) if m else None

def tabla_akt(page):
    """(clave «E4», título, partes) de una página AKT, o None."""
    t = [x.strip() for x in page.get_text().split(chr(10)) if x.strip()]
    m = re.match(r"([A-Z])-\s*(\d+)$", t[0]) if t else None
    if not m or "Descripciones" not in t or "NOTA" not in t:
        return None
    fila = re.compile(rf"{m.group(1)}{m.group(2)}-(\d+[A-Z]?)$")
    partes, titulo, k = [], "", t.index("NOTA") + 1
    while k < len(t):
        r = fila.match(t[k])
        if not r:
            titulo = t[k]; k += 1; continue
        k += 1; campos = []
        while k < len(t) and not fila.match(t[k]):
            campos.append(t[k]); k += 1
        ic = max((j for j, c in enumerate(campos) if re.fullmatch(r"\d+", c)), default=None)
        if ic is None or ic == 0:
            continue
        desc, pre, nota = campos[ic - 1], campos[:ic - 1], " ".join(campos[ic + 1:])
        cod = re.sub(r"\s*\d{13}$", "", pre[0]).strip() if pre else ""
        if re.fullmatch(r"\d{13}", cod): cod = ""
        partes.append({"ref": r.group(1), "descripcion": limpiar(re.sub(r"\s+Rp$", "", desc)), "cantidad": int(campos[ic]), "codigo": limpiar(cod), "nota": limpiar(nota)})
    if partes and partes[-1]["nota"].isupper():   # el título de la figura (MAYÚSCULAS) cae como nota de la última fila
        titulo = titulo or partes[-1]["nota"]; partes[-1]["nota"] = ""
    return m.group(1) + m.group(2), titulo.title(), partes

def main_akt(pdf, salida, figura, moto):
    d = pymupdf.open(pdf); clave = clave_fig(figura)
    for i, page in enumerate(d):
        ta = tabla_akt(page)
        if not ta or ta[0] != clave:
            continue
        _, titulo, partes = ta
        res = json.load(open(salida, encoding="utf-8")) if os.path.exists(salida) else {"moto": moto or os.path.splitext(os.path.basename(salida))[0], "fuente": os.path.basename(pdf), "figuras": {}}
        viejo = res["figuras"].get(clave, {})
        for p in partes:
            q = next((x for x in viejo.get("partes", []) if x.get("ref") == p["ref"]), {})
            for k, v in q.items(): p.setdefault(k, v)
        res["figuras"][clave] = {"titulo": titulo, "paginas": [i + 1], "partes": partes}
        with open(salida, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False)
        sin = [p["ref"] for p in partes if not p["codigo"]]
        print(f"figura {clave} «{titulo}», p. {i + 1}: {len(partes)} piezas" + (f" · sin código: {', '.join(sin)}" if sin else ""))
        for p in partes: print(f"  {p['ref']:>3} {p['codigo'] or '-':16} {p['cantidad']:>2} {p['descripcion']}")
        return 0
    return None

def main_generico(pdf, salida, figura, columna, moto):
    if clave_fig(figura):   # «E4», «E-4»: catálogo AKT
        r = main_akt(pdf, salida, figura, moto)
        if r is not None: return r
    d = pymupdf.open(pdf)
    filas, paginas, titulo, columnas = [], [], "", []
    for i, page in enumerate(d):
        fg = figura_generica(page)
        if not fg or fg[0] != str(figura):
            continue
        fs, cs = filas_genericas(page)
        if not fs:
            continue
        titulo = titulo or re.sub(r"\s*\(.*$", "", fg[1]); paginas.append(i + 1); filas += fs
        columnas = columnas or cs
    if not filas:
        print(f"figura {figura}: no encontré su tabla (cabecera PARTE/CÓDIGO + DESCRIPCIÓN, o AKT «Ref./Descripciones» con figura E-N)"); return 1
    if columna is None and len(columnas) > 1:
        print(f"figura {figura} «{titulo}», pp. {paginas}: varias columnas de versión {columnas}. Pasa --columna <una>."); return 2
    col = columna or columnas[0]
    if col not in columnas:
        print(f"columna «{col}» no está; hay {columnas}"); return 2
    ref = desc = ""
    porref = {}
    for f in filas:   # filas de continuación: sin número ni descripción, heredan los de la anterior
        if f["ref"]: ref, desc = f["ref"], ""
        if f["descripcion"]: desc = f["descripcion"]
        f["ref"], f["descripcion"] = ref, f["descripcion"] or desc
        porref.setdefault(ref, []).append(f)
    partes, fuera, conjuntos = [], [], []
    for r, fs in porref.items():
        desc = next((x["descripcion"] for x in fs if x["descripcion"]), "")
        sel = next((x for x in fs if re.fullmatch(r"\d+", x["cant"].get(col, ""))), None)
        if not sel:
            fuera.append(f"{r} {desc}"); continue
        if re.search(r"\bcomplet[oa]s?\b", desc, re.I):   # «Clutch Completo»: kit de venta (recuadro punteado), no una pieza del dibujo
            conjuntos.append({"ref": r, "descripcion": desc, "codigo": sel["codigo"]}); continue
        partes.append({"ref": r, "descripcion": desc, "cantidad": int(sel["cant"][col]), "codigo": sel["codigo"], "nota": f"columna {col}" + (f"; {sel['nota']}" if sel["nota"] else "")})
    res = json.load(open(salida, encoding="utf-8")) if os.path.exists(salida) else {"moto": moto or os.path.splitext(os.path.basename(salida))[0], "fuente": os.path.basename(pdf), "figuras": {}}
    fig = {"titulo": titulo, "paginas": paginas, "columna": col, "columnas": columnas, "partes": partes}
    if fuera: fig["fuera"] = f"No aplican a la columna {col}: " + "; ".join(fuera) + "."
    if conjuntos: fig["conjuntos"] = conjuntos   # se piden completos; si la lámina los necesita, pásalos a «partes» a mano
    viejo = res["figuras"].get(str(figura), {})
    for p in partes:   # conserva descripcion_en u otros campos agregados a mano
        q = next((x for x in viejo.get("partes", []) if x.get("ref") == p["ref"]), {})
        for k, v in q.items(): p.setdefault(k, v)
    res["figuras"][str(figura)] = fig
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(f"figura {figura} «{titulo}», pp. {paginas}, columna {col}: {len(partes)} piezas" + (f" · fuera: {', '.join(x.split()[0] for x in fuera)}" if fuera else "")
          + (f" · conjuntos de venta: {', '.join(c['ref'] for c in conjuntos)}" if conjuntos else ""))
    for p in partes: print(f"  {p['ref']:>3} {p['codigo']:12} {p['cantidad']:>2} {p['descripcion']}")
    return 0

def main(pdf, salida):
    d = pymupdf.open(pdf)
    figuras = {}
    for i, page in enumerate(d):
        fg = pagina_figura(page)
        if not fg:
            continue
        num, tit = fg
        f = figuras.setdefault(num, {"titulo": tit, "paginas": [], "partes": []})
        f["paginas"].append(i + 1)
        f["partes"].extend(filas_pagina(page))
    res = {"moto": "nmax-bbe4", "fuente": os.path.basename(pdf), "figuras": figuras}
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(len(figuras), "figuras,", sum(len(f["partes"]) for f in figuras.values()), "filas")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("salida")
    ap.add_argument("--figura"); ap.add_argument("--columna"); ap.add_argument("--moto")
    a = ap.parse_args()
    if a.figura:
        sys.exit(main_generico(a.pdf, a.salida, a.figura, a.columna, a.moto))
    main(a.pdf, a.salida)
