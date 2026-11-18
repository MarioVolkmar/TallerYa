"""Extrae las tablas de partes de un catálogo (PDF, solo lectura) a JSON.
Uso:
  python extraer_catalogo.py <pdf> <salida.json>                              Yamaha (cabecera 'PART NO.'): todas las figuras [--moto crypton-bf24]
      Yamaha Colombia (bilingüe, «DESCRIPCION/DESCRIPTION»): «descripcion» en español y «descripcion_en» en inglés.
  python extraer_catalogo.py <pdf> <salida.json> --figura 14 --columna TEC [--moto boxer-ct100]
      Otros catálogos (Auteco/Bajaj y genéricos en español: cabecera 'PARTE'/'CÓDIGO' + 'DESCRIPCIÓN' + columnas de
      versión o de cantidad): extrae solo la figura N por palabras y la agrega a <salida.json> si ya existe.
      Sin --columna, si hay varias columnas de versión, las lista y no escribe nada.
  python extraer_catalogo.py <pdf> <salida.json> --figura E4 [--moto akt-nkd125]
      Catálogo AKT (cabecera 'Ref.'/'Descripciones'/'Cant', figuras 'E- 4' = motor y 'F- 4' = chasis): la figura se
      guarda con letra y número («E4», así no choca con «F4»). Los conjuntos («Cta», «Completo») quedan en «partes»
      porque tienen número en la foto; el código se separa del EAN-13 pegado y puede ir vacío.
  python extraer_catalogo.py <pdf> <salida.json> --figura F10 --columna C [--saltar 2U] [--moto honda-cb125f]
      Catálogo Honda (inglés; 'Reqd. QTY' por versión con columnas «7 8 A C» y códigos de mercado): se guarda como «F10».
      Sin --columna lista las versiones. Las filas de reemplazo heredan la ref; --saltar descarta mercados (2U = Nissin).
  python extraer_catalogo.py <pdf> <salida.json> --figura 8 [--moto tvs-apache160-4v]
      Catálogo TVS Colombia (cabecera «FIG. No. | PARTE Nº | DESCRIPCIÓN | CANT. | SAP»): se detecta solo; el SAP va a «nota».
Si no reconoce la tabla (o salen menos de 3 piezas con número), sale con error y NO escribe nada.
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
    # Yamaha Colombia (bilingüe): cabecera «DESCRIPCION» sobre «DESCRIPTION» y cada fila en dos renglones, español arriba
    bilingue = any(a[4] == "DESCRIPCION" for a in w) and any(a[4] == "DESCRIPTION" for a in w)
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
        cols = {"codigo": [], "desc": [], "desc_en": [], "cant": [], "nota": []}
        for a in sorted(f["w"], key=lambda a: (round(a[1] / 4), a[0])):
            x = a[0] - px
            k = "codigo" if x < 50 else "desc" if x < 205 else "cant" if x < 270 else "nota"
            if k == "desc" and bilingue and (a[1] + a[3]) / 2 > f["y"] + 3: k = "desc_en"   # renglón de abajo = inglés
            cols[k].append(a[4])
        cant = " ".join(cols["cant"]).strip()
        fila = {"ref": f["ref"], "descripcion": limpiar(" ".join(cols["desc"]))}
        if bilingue: fila["descripcion_en"] = limpiar(" ".join(cols["desc_en"]))
        fila.update({"cantidad": int(cant) if cant.isdigit() else cant, "codigo": limpiar("".join(cols["codigo"])),
                     "nota": limpiar(" ".join(cols["nota"]))})
        out.append(fila)
    return out


# ---------- catálogos que no son Yamaha (tablas en español con columnas de versión) ----------
CABECERA_COD = ("PARTE", "CÓDIGO", "CODIGO", "REFERENCIA")
NO_VERSION = {"DESCRIPCIÓN", "DESCRIPCION", "OBSERVACIÓN", "OBSERVACION", "OBSERVACIONES", "Nº.", "N°.", "Nº", "N°", "FIG.", "FIG", "NO.", "PARTE", "CÓDIGO", "CODIGO", "REFERENCIA"}

def figura_generica(page):
    t = re.sub(r"\s+", " ", page.get_text())
    # ronda 8: «16A» es otra figura (no la 16) y el título puede cerrar con un paréntesis de letras: «CARBURADOR (TEC-S1D)»
    m = re.search(r"FIGURA\s*N\W{0,2}\s*(\d+[A-Z]?)(?![A-Za-z0-9])\s*:?\s*([^(\d]+?)\s*(\(\s*\d+\s*/\s*\d+\s*\)|\([^)]*\)|FIG\.|PARTE|\d|$)", t)
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

# ---------- catálogo TVS: una celda por línea, 5 por fila (No. | PARTE Nº | DESCRIPCIÓN | CANT. | SAP) ----------
def tabla_tvs(page):
    L = [x.strip() for x in page.get_text().split("\n")]
    if "SAP" not in L or not any(x.upper().startswith("CANT") for x in L):
        return []
    i, out = L.index("SAP") + 1, []
    while i + 4 < len(L) and re.fullmatch(r"\d+[A-Z]?", L[i]):
        ref, cod, desc, cant, sap = L[i:i + 5]
        if not re.fullmatch(r"\d+", cant):
            break
        out.append({"ref": ref, "descripcion": limpiar(desc), "cantidad": int(cant), "codigo": cod.strip(), "nota": f"SAP {sap}"})
        i += 5
    return out

def main_tvs(pdf, salida, figura, moto):
    d = pymupdf.open(pdf)
    partes, paginas, titulo = [], [], ""
    for i, page in enumerate(d):
        fg = figura_generica(page)
        if not fg or fg[0] != str(figura):
            continue
        fs = tabla_tvs(page)
        if fs:
            partes += fs; paginas.append(i + 1); titulo = titulo or fg[1]
    if not partes:
        return None
    m = re.search(r"FIGURA\s*N\W{0,2}\s*" + re.escape(str(figura)) + r"\s*:\s*(.+?)\s*$", re.sub(r"\s+", " ", d[paginas[0] - 1].get_text()))
    if m: titulo = m.group(1).strip()
    return guardar(pdf, salida, figura, moto, {"titulo": titulo, "paginas": paginas, "partes": partes}, "TVS")

def guardar(pdf, salida, figura, moto, fig, formato):
    """Control de cordura común: con menos de 3 piezas con número, error y no escribe (antes dejaba 1 pieza basura)."""
    buenas = [p for p in fig["partes"] if re.fullmatch(r"\d+[A-Za-z]?", str(p.get("ref", "")))]
    if len(buenas) < 3:
        print(f"ERROR figura {figura}: el formato {formato} dio {len(fig['partes'])} filas y {len(buenas)} con número; no escribo nada. "
              "Mira UNA página de la tabla y extrae a mano (ref, descripcion, cantidad, codigo, nota) o agrega el formato aquí.")
        return 3
    res = json.load(open(salida, encoding="utf-8")) if os.path.exists(salida) else {"moto": moto or os.path.splitext(os.path.basename(salida))[0], "fuente": os.path.basename(pdf), "figuras": {}}
    res["figuras"][str(figura)] = fig
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(f"figura {figura} «{fig['titulo']}» ({formato}), pp. {fig['paginas']}: {len(fig['partes'])} piezas")
    for p in fig["partes"]: print(f"  {p['ref']:>3} {p['codigo']:12} {p['cantidad']:>2} {p['descripcion']}")
    return 0

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

# ---------- catálogo Honda: «F-10» + tabla Ref. No. | Part No. | Description | Reqd. QTY por versión (7 8 A C) | mercados ----------
COD_HONDA = r"\d{5}-[A-Z0-9]{3,5}(?:-[A-Z0-9]{2,5})?"   # también tornillería estándar «95701-06014-00» y sin sufijo «92812-20000» (ronda 9)

def main_honda(pdf, salida, figura, columna, moto, saltar):
    """Filas de reemplazo (sin número) heredan la ref de la anterior; se toma la primera fila con cantidad en la columna
    cuyo mercado no esté en «saltar» (p. ej. 2U = versión Nissin)."""
    m = re.fullmatch(r"([A-Z])-?(\d+)(?:-(\d+))?", str(figura).upper().replace(" ", ""))   # «F10», «F-10» y de tres niveles «E-1-2» / «E1-2»
    if not m: return None
    letra, num, sub = m.groups(); clave = letra + num + (f"-{sub}" if sub else "")
    eti = f"{letra}-{num}" + (f"-{sub}" if sub else "")
    d = pymupdf.open(pdf); textos, paginas, titulo, cols = [], [], "", []
    for i, page in enumerate(d):
        t = page.get_text()
        if "Parts catalogue code" not in t or not re.search(rf"(?m)^\s*{eti}\s*$", t):
            continue
        tm = re.search(rf"(?m)^\s*{eti}\s*\n(?:\s*\d+\s*\n)?\s*([A-Z][^\n]+)", t)   # en la 2.ª página va el número de página antes del título
        tt = re.sub(r"[^\x20-\x7e]", "", tm.group(1)).strip() if tm else ""
        if not tt or (titulo and tt != titulo):   # índices u otras páginas que solo nombran la figura
            continue
        titulo = tt
        cm = re.search(r"(?m)^([ \t]*[0-9A-Z]{1,2}(?:[ \t]+[0-9A-Z]{1,2})+)[ \t]*\nSerial No\.", t)
        cols = cols or (cm.group(1).split() if cm else [])
        textos.append(t); paginas.append(i + 1)
    if not textos or not cols: return None
    if columna is None and len(cols) > 1:
        print(f"figura {clave} «{titulo}», pp. {paginas}: varias columnas de versión {cols}. Pasa --columna <una> (y --saltar mercados, p. ej. 2U)."); return 2
    col = columna or cols[0]
    if col not in cols:
        print(f"columna «{col}» no está; hay {cols}"); return 2
    k = cols.index(col); n = len(cols)
    pat = re.compile(rf"(?:^|\n)[ \t]*(?:\(?(\d+)\)?[ \t]+)?({COD_HONDA})(?:[ \t]*\n|[ \t]+(?=[A-Z]))(.*?)((?:[ \t\n]+\(?[\d-]+\)?){{{n}}})(?:[ \t\n]+-{{4,}}[ \t\n]+-{{4,}}[ \t\n]+([A-Z0-9,]*))?", re.S)   # sin guiones de serie (E-1-2) no hay mercados: no tomar la ref de la fila siguiente
    ref, base, partes, vistos = None, "", [], set()
    salta = set(x.strip() for x in (saltar or "").split(",") if x.strip())
    for t in textos:
        for mm in pat.finditer(t):
            r, cod, desc, qs, mk = mm.groups(); mk = mk or ""
            desc = re.sub(r"\s+", " ", re.sub(r"[^\x20-\x7e]", " ", desc)).strip()
            desc = re.sub(r"\s*\*[A-Z0-9]+\*.*$", "", desc).strip()   # ronda 9: color en la 2.ª línea («*NH303M* MAT AXIS GRAY…»)
            if r: ref, base = r, desc
            q = qs.split()[k]
            if q.startswith("("):   # «(1)»: alternativa (otra bujía, etc.); se toma la fila con cantidad normal
                continue
            if ref is None or ref in vistos or q == "-" or (salta and set(mk.split(",")) <= salta):
                continue
            vistos.add(ref)
            partes.append({"ref": ref, "descripcion": desc or base, "descripcion_en": desc or base, "cantidad": int(q), "codigo": cod,
                           "nota": f"columna {col}; mercados {mk}"})
    partes.sort(key=lambda p: int(p["ref"]))
    res = json.load(open(salida, encoding="utf-8")) if os.path.exists(salida) else {"moto": moto or os.path.splitext(os.path.basename(salida))[0], "fuente": os.path.basename(pdf), "figuras": {}}
    viejo = res["figuras"].get(clave, {})
    for p in partes:
        q = next((x for x in viejo.get("partes", []) if x.get("ref") == p["ref"]), {})
        for kk, v in q.items(): p.setdefault(kk, v)
    res["figuras"][clave] = {"titulo": titulo, "paginas": paginas, "columna": col, "columnas": cols, "saltar": sorted(salta), "partes": partes}
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(f"figura {clave} «{titulo}», pp. {paginas}, columna {col}" + (f", sin {','.join(sorted(salta))}" if salta else "") + f": {len(partes)} piezas")
    for p in partes: print(f"  {p['ref']:>3} {p['codigo']:14} {p['cantidad']:>2} {p['descripcion']}")
    return 0

def main_generico(pdf, salida, figura, columna, moto, saltar=None):
    if clave_fig(figura):   # «E4», «E-4»: catálogo AKT
        r = main_akt(pdf, salida, figura, moto)
        if r is not None: return r
    if clave_fig(figura) or re.fullmatch(r"\s*[A-Za-z]-?\d+-\d+\s*", str(figura)):
        r = main_honda(pdf, salida, figura, columna, moto, saltar)   # «F10», «F-10», «E-1-2»: catálogo Honda
        if r is not None: return r
    r = main_tvs(pdf, salida, figura, moto)   # TVS: «PARTE Nº … CANT. | SAP», una celda por línea
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
        print(f"figura {figura}: no encontré su tabla (cabecera PARTE/CÓDIGO + DESCRIPCIÓN, AKT «Ref./Descripciones» con figura E-N, u Honda «Parts catalogue code» con figura F-N)"); return 1
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
    if len([p for p in partes if re.fullmatch(r"\d+[A-Za-z]?", p["ref"])]) < 3:
        print(f"ERROR figura {figura}: solo {len(partes)} piezas reconocibles (formato no reconocido); no escribo nada. Mira UNA página y extrae a mano."); return 3
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

def main(pdf, salida, moto=None):
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
    res = {"moto": moto or "nmax-bbe4", "fuente": os.path.basename(pdf), "figuras": figuras}
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(len(figuras), "figuras,", sum(len(f["partes"]) for f in figuras.values()), "filas")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("salida")
    ap.add_argument("--figura"); ap.add_argument("--columna"); ap.add_argument("--moto"); ap.add_argument("--saltar")
    a = ap.parse_args()
    if a.figura:
        sys.exit(main_generico(a.pdf, a.salida, a.figura, a.columna, a.moto, a.saltar))
    main(a.pdf, a.salida, a.moto)
