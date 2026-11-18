"""Controles extra del validador (parte C de mejoras.md). Los llama validar_esquema.py; también sirven solos:
    python mas_controles.py datos/nmax-fig12.json
1. Un solo nombre por pieza: en pasos, cadenas, «Cuándo» y fichas, la palabra que acompaña a «(n)» tiene que ser la del
   nombre de la pieza, sin sinónimos (retén/retenedor/sello, empaque/junta, rodamiento/balinera...).
2. Referencias: pasos, chips, conecta, efectos y cadenas apuntan a piezas que existen y están en el catálogo.
3. Catálogo: la descripción en inglés y la cantidad de cada ficha («cat») coinciden con catalogo/<moto>.json.
4. Intervalos: las filas de «Cuándo» con «tarea» dicen los mismos km y años que garaje/intervalos/<intervalos>.json.
5. forma3d y piezas comunes: tipos conocidos, medidas necesarias y perfiles válidos.
"""
import json, os, pathlib, re, sys, unicodedata
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]

SINONIMOS = [
    {"reten", "retenedor", "sello", "estopera"},
    {"empaque", "junta", "empaquetadura"},
    {"rodamiento", "balinera", "cojinete", "rulimán", "ruliman"},
    {"buje", "casquillo"},
    {"seguro", "pin", "clip", "circlip"},
    {"zapata", "banda"},
]
TIPOS3D = {"torno": ["perfil"], "sector": ["r", "ang", "z"], "cilindro": ["r", "z"], "caja": ["tam", "pos"],
           "correa": ["c1", "r1", "c2", "r2", "seccion"], "prisma": ["contorno", "z"], "esfera": ["r"],
           "resorte": ["r", "largo", "vueltas", "alambre"]}
COMUNES = {"tuerca": [], "arandela": ["r", "ri"], "seguro": ["r"], "reten": [], "oring": ["r"],
           "rodamiento": ["r", "ri"], "buje": ["r", "ri", "largo"], "resorte": ["r", "largo"],
           "pasador": ["r", "largo"], "tornillo": [], "revolucion": ["perfil"],
           "manguera": ["puntos"], "abrazadera": ["r"], "caja": [], "ducto": ["puntos"], "placa": [],
           "rin": ["r"], "llanta": ["r"], "pinon": ["r"], "cadena": [], "eje": [], "tensor": []}   # ronda 6: rueda y transmisión final


def base(palabra):
    """minúsculas, sin tildes y una raíz común al singular y al plural: buje/bujes → buj, retén/retenes → reten."""
    p = "".join(c for c in unicodedata.normalize("NFD", palabra.lower()) if unicodedata.category(c) != "Mn")
    if len(p) > 3 and p.endswith("s"):
        p = p[:-1]
    if len(p) > 3 and p.endswith("e"):
        p = p[:-1]
    return p


def grupo(p):
    for g in GRUPOS:
        if p in g:
            return g
    return None


GRUPOS = [{base(w) for w in g} for g in SINONIMOS]


def sin_html(t):
    return re.sub(r"<[^>]+>", "", t or "")


def textos_con_numeros(D):
    """(dónde, texto) de todo lo que el usuario lee con números de pieza."""
    for i, P in enumerate(D["pasos"]):
        yield f"pasos[{i}]", P.get("t", "")
    for c in D["cadenas"]:
        yield f"cadena «{c.get('t')}»", " ".join(t for _k, t in c.get("p", []))
    for i, r in enumerate(D["cuando"]):
        yield f"cuando[{i}]", r.get("que", "") + " " + r.get("cuando", "")
    for k, F in D["fichas"].items():
        yield f"ficha {k}", " ".join(str(F.get(c, "")) for c in ("que", "sirve", "cuando", "compra"))


NUM = re.compile(r"((?:[A-Za-zÁÉÍÓÚáéíóúñÑ]+\s+){0,4})\(((?:\d+[a-z]?)(?:\s*(?:,|y|e)\s*\d+[a-z]?)*)\)")


def revisar_nombres(D, err, avi):
    nombres = {k: {base(w) for w in re.findall(r"\w+", v + " " + D["fichas"].get(k, {}).get("nombre", ""))} for k, v in D["nombres"].items()}
    for donde, t in textos_con_numeros(D):
        for m in NUM.finditer(sin_html(t)):
            palabras = [base(w) for w in m.group(1).split()]
            for n in re.findall(r"\d+[a-z]?", m.group(2)):
                propio = nombres.get(n) or nombres.get(re.sub(r"[a-z]$", "", n))
                if not propio or not palabras:
                    continue
                otros = [w for w in palabras if grupo(w) and w not in propio]   # sinónimo, o nombre de otra pieza
                if otros:
                    err.append(f"{donde}: «{otros[0]} ({n})», pero la pieza {n} se llama «{D['nombres'].get(n, '')}»: usar un solo nombre")


def revisar_referencias(D, cat, err, avi):
    fichas, ids = D["fichas"], {p["id"] for p in D["piezas"]}
    en_cat = {q["ref"] for q in cat["partes"]} if cat else None
    def existe(k, donde):
        if k not in fichas:
            err.append(f"{donde}: «{k}» no tiene ficha")
        elif en_cat is not None and not fichas[k].get("ctx") and k not in en_cat:
            err.append(f"{donde}: «{k}» no está en el catálogo (figura {D['figura']})")
    for k, F in fichas.items():
        for o in F.get("conecta", []):
            existe(o, f"ficha {k} · conecta")
        for o, _t in F.get("efectos", []):
            existe(o, f"ficha {k} · efectos")
    for c in D["cadenas"]:
        for k, _t in c.get("p", []):
            existe(k, f"cadena «{c.get('t')}»")
    for k in D["ordenChips"]:
        existe(k, "ordenChips")
    for i, P in enumerate(D["pasos"]):
        for pid in P.get("m", {}):
            if pid not in ids:
                err.append(f"pasos[{i}] mueve «{pid}», que no es una pieza")


def norm_desc(t):
    return re.sub(r"[^A-Z0-9]+", " ", t.upper()).strip()


def revisar_catalogo(D, cat, err, avi):
    if not cat:
        return
    filas = {}
    for q in cat["partes"]:
        filas.setdefault(q["ref"], []).append(q)
    for k, F in D["fichas"].items():
        if F.get("ctx") or k not in filas:
            continue
        cab = F.get("cat", "")
        ingles, _, resto = cab.partition("·")
        descs = [norm_desc(q[c]) for q in filas[k] for c in ("descripcion", "descripcion_en") if q.get(c)]
        if not any(d and (d in norm_desc(ingles) or norm_desc(ingles) in d) for d in descs):
            err.append(f"ficha {k}: «{ingles.strip()}» no coincide con el catálogo ({filas[k][0]['descripcion']})")
        m = re.search(r"(\d+)", resto)
        cants = {q["cantidad"] for q in filas[k]}
        if m and int(m.group(1)) not in cants:
            err.append(f"ficha {k}: cantidad {m.group(1)} en «cat», el catálogo dice {'/'.join(map(str, sorted(cants)))}")
        elif not m:
            avi.append(f"ficha {k}: «cat» sin cantidad (catálogo: {filas[k][0]['cantidad']})")


def revisar_intervalos(D, err, avi):
    nombre = D.get("intervalos")
    if not nombre:
        avi.append("sin «intervalos» en el JSON: no se compararon los plazos de «Cuándo»")
        return
    I = json.loads((RAIZ / "garaje" / "intervalos" / f"{nombre}.json").read_text(encoding="utf-8"))["tareas"]
    for i, r in enumerate(D["cuando"]):
        tarea = r.get("tarea")
        if not tarea:
            continue
        if tarea not in I:
            err.append(f"cuando[{i}]: la tarea «{tarea}» no está en intervalos/{nombre}.json")
            continue
        t = sin_html(r["cuando"]).replace(".", "")
        km = [int(x) for x in re.findall(r"(\d+)\s*km", t)]
        anos = [int(x) for x in re.findall(r"(\d+)\s*años?", t)]
        meses = [int(x) for x in re.findall(r"(\d+)\s*meses", t)]
        k_i, d_i = I[tarea].get("km") or 0, I[tarea].get("dias") or 0
        if k_i and k_i not in km:
            err.append(f"cuando[{i}] ({tarea}): dice {km or 'sin km'}, intervalos dice {k_i} km")
        if km and not k_i:
            err.append(f"cuando[{i}] ({tarea}): dice {km[0]} km, intervalos no tiene km")
        dias = [a * 365 for a in anos] + [m * 30 for m in meses]
        if d_i and not any(abs(d - d_i) <= 31 for d in dias):
            err.append(f"cuando[{i}] ({tarea}): plazo {dias or 'sin tiempo'} días, intervalos dice {d_i} días")


def revisar_3d(D, ruta, err, avi):
    perfiles = D.get("perfiles", {})
    def perfil_ok(v, donde):
        if isinstance(v, str):
            if not v.startswith("@") or v[1:] not in perfiles:
                err.append(f"{donde}: perfil «{v}» no está en «perfiles»")
            return
        if not (isinstance(v, list) and len(v) >= 3 and all(isinstance(q, list) and len(q) == 2 and q[0] >= 0 for q in v)):
            err.append(f"{donde}: el perfil tiene que ser [[r,z],...] con 3 puntos o más y r ≥ 0")
    for k, v in perfiles.items():
        perfil_ok(v, f"perfiles.{k}")
    for k, F in D["fichas"].items():
        f3 = F.get("forma3d")
        if f3 is None:
            continue
        if not isinstance(f3.get("partes"), list) or not f3["partes"]:
            err.append(f"ficha {k}: forma3d necesita «partes»")
            continue
        for j, q in enumerate(f3["partes"]):
            donde = f"ficha {k} · forma3d[{j}]"
            if q.get("tipo") not in TIPOS3D:
                err.append(f"{donde}: tipo «{q.get('tipo')}» desconocido ({', '.join(TIPOS3D)})")
                continue
            for c in TIPOS3D[q["tipo"]]:
                if c not in q:
                    err.append(f"{donde}: «{q['tipo']}» necesita «{c}»")
            if q["tipo"] == "torno" and "perfil" in q:
                perfil_ok(q["perfil"], donde)
    marcos = set()
    arte = ruta.with_name(ruta.stem + "-arte.js")
    if arte.exists():
        m = re.search(r"marcos:\{([^}]*)\}", arte.read_text(encoding="utf-8"))
        marcos = set(re.findall(r"\w+", m.group(1))) if m else set()
    for p in D["piezas"]:
        if "comun" not in p:
            if "arte" not in p:
                err.append(f"pieza {p['id']}: necesita «arte» o «comun»")
            continue
        if not D.get("comun"):
            err.append("hay piezas comunes y falta «comun» (atras y colores) en la lámina")
        if p["comun"] not in COMUNES:
            err.append(f"pieza {p['id']}: pieza común «{p['comun']}» desconocida ({', '.join(COMUNES)})")
            continue
        for c in COMUNES[p["comun"]] + ["x", "y"]:
            if c not in p.get("p", {}):
                err.append(f"pieza {p['id']} ({p['comun']}): falta p.{c}")
        if p["comun"] == "pasador" and p["p"].get("cuerpo") == "lateral" and "cabeza" not in p["p"]:
            err.append(f"pieza {p['id']}: pasador lateral necesita p.cabeza")
        if p.get("marco") and p["marco"] not in marcos:
            err.append(f"pieza {p['id']}: el marco «{p['marco']}» no está en marcos:{{}} de {arte.name}")
        if "perfil" in p.get("p", {}):
            perfil_ok(p["p"]["perfil"], f"pieza {p['id']}")


# ---------- autocontrol-mecanico.md: preguntas [S] 2, 4, 9, 12, 16, 18 y sistemas ----------
VACIAS = {"de", "la", "el", "lo", "los", "las", "del", "y", "e", "su", "sus", "con", "que", "un", "una", "por", "al", "a",
          "en", "se", "o", "tambien", "nuevo", "nueva", "nuevos", "nuevas", "viejo", "vieja", "mismo", "misma", "otro", "otra",
          "trasero", "trasera", "delantero", "delantera", "izquierdo", "izquierda", "derecho", "derecha", "interior", "exterior"}
MARCA_APROX = re.compile(r"aprox|unos?\s|unas?\s|cerca de|varias|alrededor|más o menos|sin dato|manual de servicio|según el manual|hasta\s", re.I)


def textos_ficha(F):
    yield from (str(F.get(c, "")) for c in ("que", "sirve", "cuando", "compra"))
    yield from (t for _c, t in F.get("fallas", []))
    yield from F.get("sintomas", [])
    yield from (t for _o, t in F.get("efectos", []))


def frases(t):
    return [f for f in re.split(r"(?<!aprox\.)(?<!Aprox\.)(?<=[.;!?])\s+", sin_html(t)) if f.strip()]


def revisar_seguro_catalogo(D, cat, err, avi):
    """2: lo que sale del catálogo (nombre, cantidad, lado) va como «Seguro», no como «aprox.»."""
    if not cat:
        return
    refs = {q["ref"] for q in cat["partes"]}
    for k, F in D["fichas"].items():
        if k not in refs:
            continue
        for s, t in F.get("certeza", []):
            if s != "ok" and re.search(r"cat[aá]logo|\bcantidad|\blado (derecho|izquierdo)", sin_html(t), re.I) and not re.search(r"plano|confirma|fotos?\b|deducid", t, re.I):   # «deducido de las fotos del catálogo» es aprox. de verdad
                err.append(f"ficha {k}: «{sin_html(t)[:60]}…» sale del catálogo y está como «aprox.»: va como «Seguro»")


def revisar_nombre_viejo(D, err, avi):
    """4: la palabra pegada a «(N)» tiene que ser del nombre de N (atrapa nombres viejos tras renombrar)."""
    nombres = {k: {base(w) for w in re.findall(r"\w+", v + " " + D["fichas"].get(k, {}).get("nombre", ""))} for k, v in D["nombres"].items()}
    vistos = set()
    for donde, t in textos_con_numeros(D):
        for m in NUM.finditer(sin_html(t)):
            ws = [w for w in m.group(1).split() if base(w) not in VACIAS]
            if not ws:
                continue
            w = base(ws[-1])
            ns = re.findall(r"\d+[a-z]?", m.group(2))
            if any(w in nombres.get(n, set()) or w in nombres.get(re.sub(r"[a-z]$", "", n), set()) for n in ns):
                continue
            if all(n in nombres for n in ns) and (donde.split()[0], ws[-1], m.group(2)) not in vistos:
                vistos.add((donde.split()[0], ws[-1], m.group(2)))
                avi.append(f"{donde}: «{ws[-1]} ({m.group(2)})» no es parte del nombre de {'/'.join(ns)} ({D['nombres'][ns[0]]}): ¿nombre viejo?")


def revisar_desarme(D, err, avi):
    """9 (parcial): cada número sale en el desarme, y lo que lo sujeta (D.sujeta = {"tuerca":["lo que sujeta"]}) sale antes o en el mismo paso."""
    primero = {}
    for i, P in enumerate(D["pasos"]):
        for pid in P.get("m", {}):
            primero.setdefault(pid, i)
    carcasas = {c["id"] for c in D.get("carcasas", [])}
    for p in D["piezas"]:
        if p["id"] not in primero and p["id"] not in carcasas:
            avi.append(f"desarme: la pieza {p['id']} no se mueve en ningún paso")
    suj = D.get("sujeta")
    if not suj:
        avi.append("sin «sujeta» en el JSON: no se revisó que lo que sujeta salga antes")
        return
    for a, bs in suj.items():
        for b in bs:
            if a in primero and b in primero and primero[a] > primero[b]:
                err.append(f"desarme: {b} sale en el paso {primero[b] + 1}, antes que {a} (que lo sujeta), en el paso {primero[a] + 1}")


def fuentes_texto(D):
    t = " ".join(D["fuentes"].get("seguro", [])) + " " + " ".join(r.get("cuando", "") + r.get("fuente", "") for r in D["cuando"])
    for F in D["fichas"].values():
        t += " " + " ".join(x for s, x in F.get("certeza", []) if s == "ok")
    return sin_html(t).replace(".", "")


def revisar_cifras(D, err, avi):
    """12 y 18: cifras con unidad sin fuente ni «aprox.»; torques y medidas en mm, más estricto (error)."""
    fuente = fuentes_texto(D)
    todos = [(f"pasos[{i}]", P.get("t", "")) for i, P in enumerate(D["pasos"])]
    todos += [(f"ficha {k}", t) for k, F in D["fichas"].items() for t in textos_ficha(F)]
    todos += [(f"funciona[{i}]", P.get("t", "")) for i, P in enumerate(D["funciona"].get("pasos", []))]
    for donde, t in todos:
        for fr in frases(t):
            for m in re.finditer(r"(\d[\d.,]*)\s*(N·m|Nm|kgf|mm|km|rpm|°C|%|bar|psi|g\b|ml|cc)", fr):
                num, u = m.group(1).replace(".", ""), m.group(2)
                if MARCA_APROX.search(fr) or re.search(r"(?<!\d)" + re.escape(num) + r"(?!\d)", fuente):
                    continue
                msg = f"{donde}: «{m.group(0)}» sin fuente ni «aprox.» («{fr[:70]}…»)"
                (err if u in ("N·m", "Nm", "kgf", "mm") else avi).append(msg)


def revisar_fuente_certeza(D, err, avi):
    """16 (parcial): cada fila de «Cuándo» con fuente y certeza; cada ficha con su certeza."""
    for i, r in enumerate(D["cuando"]):
        if not re.search(r"esq-s-(ok|ap)", r.get("fuente", "")):
            err.append(f"cuando[{i}]: la fuente no dice si es «Seguro» o «Aproximado»")
    for k, F in D["fichas"].items():
        if not F.get("ctx") and not F.get("certeza"):
            err.append(f"ficha {k}: sin «certeza» (qué es seguro y qué aproximado)")


def revisar_lado_version(D, cat, err, avi):
    """Sistemas: lado y versión de la moto como en el catálogo de esa versión."""
    if not cat:
        return
    cod = (D.get("catalogo") or "").split("-")[-1].upper()
    if cod and cod not in D["moto"].upper():
        err.append(f"la moto dice «{D['moto']}», pero el catálogo es de la versión {cod}")
    lados = {"RIGHT": ("derech", "izquierd"), "LEFT": ("izquierd", "derech")}
    for q in cat["partes"]:
        for L, (bien, mal) in lados.items():
            if f"({L})" in q.get("descripcion_en", q["descripcion"]) and q["ref"] in D["fichas"]:
                t = " ".join(textos_ficha(D["fichas"][q["ref"]])).lower()
                if mal in t and bien not in t:
                    err.append(f"ficha {q['ref']}: el catálogo dice {L} ({q['descripcion']}) y el texto dice «{mal}…»")
    for clave in ("ABS", "CBS"):
        if re.search(rf"\b{clave}\b", D["moto"] + " " + (cat.get("moto") or "") + " " + str(D.get("catalogo", "")), re.I):
            continue   # es parte del nombre de la moto (AKT NKD 125 CBS), no un sistema de la figura
        en_cat = clave in cat.get("titulo", "").upper() or any(clave in q["descripcion"] + q.get("descripcion_en", "") for q in cat["partes"])
        # «sin ABS», «no tiene ABS» dicen que no lo hay: no cuentan como mención
        en_texto = re.search(rf"\b{clave}\b", re.sub(rf"\b(sin|no\s+(tiene|trae|lleva|usa))\s+{clave}\b", "", json.dumps(D["cabeza"], ensure_ascii=False) + D["visor"]["titulo"], flags=re.I))
        if en_texto and not en_cat:
            err.append(f"la lámina dice {clave} y la figura del catálogo no")


def revisar_cuando_repetido(D, err, avi):
    """V2: una fila de «Cuándo» repetida (mismo «que», sin mayúsculas, tildes ni etiquetas) es un error."""
    vistos = {}
    for i, r in enumerate(D["cuando"]):
        clave = unicodedata.normalize("NFD", sin_html(r.get("que", "")).lower())
        clave = re.sub(r"[^a-z0-9 ]", "", "".join(c for c in clave if unicodedata.category(c) != "Mn")).strip()
        if clave in vistos:
            err.append(f"cuando[{i}] repite la fila cuando[{vistos[clave]}] («{sin_html(r.get('que', ''))[:60]}»)")
        else:
            vistos[clave] = i


SELLOS_FRENO = re.compile(r"\b(kit|empaque|sello|copa|ret[eé]n)\b|SEAL|CYLINDER KIT|CUP\b", re.I)
HIDRAULICO = re.compile(r"bomba|c[aá]liper|freno|MASTER|CALIPER|BRAKE", re.I)


def revisar_sellos_freno(D, err, avi):
    """V1: kits, empaques y sellos de bomba o cáliper llevan el intervalo del líquido (2 años) en su «cuando»."""
    for k, F in D["fichas"].items():
        if F.get("ctx"):
            continue
        # ronda 10: solo la descripción propia (no «· también en el kit ref. N») y sin manigueta, tornillos, interruptor ni cable
        texto = F.get("nombre", "") + " " + F.get("cat", "").split(" · ")[0]
        if SELLOS_FRENO.search(texto) and HIDRAULICO.search(texto) and not re.search(
                r"pastilla|zapata|\bPAD\b|SHOE|manigueta|palanca|LEVER|tornillo|BOLT|interruptor|SWITCH|cable", texto, re.I):
            c = sin_html(F.get("cuando", ""))
            if not re.search(r"\b2 años\b|cada dos años|con el (cambio del )?l[ií]quido", c, re.I):
                err.append(f"ficha {k} ({F.get('nombre')}): un kit o sello del freno hidráulico va con el intervalo del líquido "
                           f"(cada 2 años, según el manual) en «cuando»; dice «{c[:60]}»")


REF_N = re.compile(r"\(\s*(?:n\.?º\s*)?\d+[a-z]?(?:\s*(?:,|y|a|o)\s*\d+[a-z]?)*\s*\)")
ENLACE = re.compile(r"\[\[[^|\]]+\|([^\]]+)\]\]")


def textos_prosa(D):
    """Prosa que lee el motero: fichas, pasos, cadenas, «Cuándo» y «Cómo funciona» (sin certeza ni fuentes)."""
    for k, F in D["fichas"].items():
        for c in ("que", "sirve", "porque", "cuando"):
            if F.get(c): yield f"ficha {k}.{c}", F[c]
        for c in ("sintomas", "arrastra"):
            for i, t in enumerate(F.get(c) or []): yield f"ficha {k}.{c}[{i}]", t
        for i, (_, t) in enumerate(F.get("fallas") or []): yield f"ficha {k}.fallas[{i}]", t
    for i, p in enumerate(D.get("pasos", [])): yield f"pasos[{i}]", p.get("t", "")
    yield "textoArmado", D.get("textoArmado", "")
    for i, c in enumerate(D.get("cadenas", [])):
        for j, (_, t) in enumerate(c["p"]): yield f"cadenas[{i}].p[{j}]", t
    for i, r in enumerate(D.get("cuando", [])): yield f"cuando[{i}].que", r.get("que", "")
    for i, p in enumerate((D.get("funciona") or {}).get("pasos", [])): yield f"funciona.pasos[{i}]", p.get("t", "")


def revisar_estilo_v2(D, cat, err, avi):
    """Guía de estilo v2 (láminas con «v2»): sin nombres de catálogo ni «(N)» en la prosa; los enlaces [[n|texto]] apuntan a fichas que existen.
    Los nombres de catálogo van solo en la línea «Para pedirla» (sale de «cat» y «codigo»)."""
    if not D.get("v2"):
        return
    nombres = set()
    for p in (cat or {}).get("partes", []):
        d = p.get("descripcion_en", p["descripcion"]).lstrip(". ").strip()
        nombres.add(d)
        nombres.update(w for w in re.split(r"[ ,/]+", d) if len(w) >= 3 and w.isalpha() and w.isupper())
    nombres.update({"ASSY"})
    patron = re.compile(r"(?<![A-Za-zÁÉÍÓÚÑáéíóúñ])(" + "|".join(sorted(map(re.escape, nombres), key=len, reverse=True)) + r")(?![A-Za-zÁÉÍÓÚÑáéíóúñ])") if nombres else None
    malos = 0
    for donde, t in textos_prosa(D):
        for m in re.finditer(r"\[\[([^|\]]+)\|", t):
            if m.group(1) not in D["fichas"] and not str(m.group(1)).startswith("t:"):
                err.append(f"{donde}: el enlace [[{m.group(1)}|…]] no lleva a ninguna ficha")
        plano = sin_html(ENLACE.sub(r"", t))
        r = REF_N.search(plano)
        if r:
            malos += 1
            if malos <= 12: err.append(f"{donde}: «{r.group(0)}» en la prosa; nombra la pieza con un enlace [[n|nombre]]")
        c = patron.search(plano) if patron else None
        if c:
            malos += 1
            if malos <= 12: err.append(f"{donde}: nombre de catálogo «{c.group(1)}» en la prosa; va solo en «Para pedirla»")
    if malos > 12:
        err.append(f"… y {malos - 12} textos más con «(N)» o nombres de catálogo")


SEGURIDAD = {"jeringa": r"jeringa", "purgar": r"purg", "probar": r"pru[eé]b|probar", "nuevo": r"\bnuev[oa]s?\b",
             "apriete": r"apriet", "marca": r"\bmarca\b", "pintura": r"pintura"}


def revisar_seguridad_v2(D, ruta, err, avi):
    """Estilo v2: se acorta la explicación, nunca la seguridad. Si la v2 sale de una v1 (v2.deriva), avisa cuando un paso,
    una ficha o la lámina entera pierden una palabra de seguridad o de cierre que estaban en la v1."""
    origen = (D.get("v2") or {}).get("deriva")
    if not origen:
        return
    ruta1 = os.path.join(os.path.dirname(os.path.abspath(ruta)), origen)
    if not os.path.exists(ruta1):
        avi.append(f"v2.deriva: no está {origen}"); return
    V1 = json.load(open(ruta1, encoding="utf8"))
    def tiene(t, clave): return re.search(SEGURIDAD[clave], sin_html(t or ""), re.I)
    def texto_ficha(F): return " ".join(str(F.get(c, "")) for c in ("que", "sirve", "cuando", "compra", "porque")) + " " + " ".join(map(str, F.get("sintomas", []) + F.get("arrastra", []))) + " " + " ".join(t for _, t in F.get("fallas", []))
    pares = [(f"pasos[{i}]", p.get("t", ""), D["pasos"][i].get("t", "")) for i, p in enumerate(V1.get("pasos", [])) if i < len(D.get("pasos", []))]
    pares += [(f"ficha {k}", texto_ficha(F), texto_ficha(D["fichas"][k])) for k, F in V1.get("fichas", {}).items() if k in D["fichas"]]
    for donde, t1, t2 in pares:
        faltan = [c for c in SEGURIDAD if tiene(t1, c) and not tiene(t2, c)]
        if faltan:
            avi.append(f"{donde}: la v1 decía {', '.join(faltan)} y la v2 ya no (seguridad o cierre: no se quita al acortar)")


def revisar_orden_y_dificultad(D, err, avi):
    """Desarme: aflojar el cable (o soltar el mando) va primero; la dificultad cuenta drenar aceite o quitar una tapa."""
    pasos = [sin_html(re.sub(r"^\s*<b>.*?</b>", "", p.get("t", ""))) for p in D.get("pasos", [])]   # sin el título en negrita
    if not pasos: return
    MANDO = r"afloj\w*(?: \w+)? (el |los )?cables?|suelt\w* (el |los )?(cable|mando)"  # «desconecta el cable» no: es el del interruptor de freno (fig. 26), no el mando
    i = next((k for k, t in enumerate(pasos) if re.search(MANDO, t, re.I)), None)
    if i is not None:
        frases = [f for f in re.split(r"(?<=[.;:!?])\s+", pasos[i]) if f.strip()]
        pos = next((k for k, f in enumerate(frases) if re.search(MANDO, f, re.I)), 0)
        if i > 0 or pos > 0:
            avi.append(f"paso {i + 1}: aflojar el cable o soltar el mando va primero (primera frase del paso 1), antes de drenar o quitar tapas")
    # solo el verbo: «drena el aceite», «vacía el refrigerante», «quita la tapa». No el sustantivo «drenaje» (manguera, tubo o perno de drenaje),
    # que marcaba todas las piezas de admisión y del respiradero (fig. 8: 22 avisos falsos)
    PESADO = r"\bdren(?:a|ar|as|e|en|ando|ado|ada|ados)\b|vac[ií]a\w* (?:todo )?(?:el |la )?(?:aceite|refrigerante|l[ií]quido)|quita\w* la tapa|desmonta\w* la tapa"
    for n, f in D.get("fichas", {}).items():
        if f.get("dif") != "facil" or f.get("ctx"): continue
        ids = {p["id"] for p in D.get("piezas", []) if p["n"] == n}
        k = next((j for j, p in enumerate(D.get("pasos", [])) if ids & set(p.get("m", {}))), None)
        if k is not None and any(re.search(PESADO, t, re.I) for t in pasos[:k + 1]):
            avi.append(f"ficha {n}: dificultad «facil», pero para llegar hay que drenar aceite o quitar una tapa (paso ≤ {k + 1}): «taller»")


def revisar_estructura_v2(D, err, avi):
    """Modelo v2: grupos (piezas = ids del dibujo), tornillería, pasos por grupo, lados opcionales, certezaDe y con3d."""
    V = D.get("v2")
    if not V:
        return
    ids = {p["id"] for p in D["piezas"]}; fichas = D.get("fichas", {})
    lados = set((V.get("lados") or {"unico": ""}).keys()); vistos = {}
    for g in V.get("grupos", []):
      nom = f"v2.grupos[{g.get('id') if isinstance(g, dict) else g}]"
      try:
        if not isinstance(g, dict): err.append(f"{nom}: cada grupo va como objeto {{id, nombre, piezas, torn, pasos}}"); continue
        torn = g.get("torn", [])
        buenos = [t for t in torn if isinstance(t, dict) and isinstance(t.get("ids"), list)] if isinstance(torn, list) else []
        if not isinstance(torn, list) or len(buenos) != len(torn):
            err.append(f"{nom}: «torn» va como lista de objetos {{nombre, corto, ids:[…], cant}}, no {json.dumps(torn, ensure_ascii=False)[:60]}")
        g = {**g, "torn": buenos}   # se sigue revisando el grupo con la tornillería que sí tiene formato
        for c in ("id", "nombre", "piezas", "torn", "pasos"):
            if c not in g: err.append(f"{nom}: falta «{c}»")
        if (g.get("lado") or "unico") not in lados: err.append(f"{nom}: lado «{g.get('lado')}» no está en v2.lados")
        todos = list(g.get("piezas", [])) + [i for t in g.get("torn", []) for i in t.get("ids", [])]
        for i in todos:
            if i not in ids: err.append(f"{nom}: «{i}» no es un id de piezas")
            elif i in vistos: err.append(f"{nom}: «{i}» ya está en el grupo {vistos[i]}")
            else: vistos[i] = g.get("id")
        for t in g.get("torn", []):
            for c in ("nombre", "corto", "ids", "cant"):
                if c not in t: err.append(f"{nom}: tornillería sin «{c}»")
        for k in g.get("pasos", []):
            if not (isinstance(k, int) and 0 <= k < len(D["pasos"])): err.append(f"{nom}: paso {k} fuera de rango")
            elif not set(D["pasos"][k]["m"]) & set(todos): avi.append(f"{nom}: el paso {k} no mueve ninguna pieza del grupo")
        PZ = {p["id"]: p for p in D["piezas"]}
        if todos and all(PZ.get(i, {}).get("vis") == "exp" or PZ.get(i, {}).get("oculto") for i in todos):
            avi.append(f"{nom}: la píldora del grupo apunta a piezas que no se ven armadas (¿kit sin cuerpo? va en «kits», sin grupo)")
        movidas = {i for k in g.get("pasos", []) if isinstance(k, int) and 0 <= k < len(D["pasos"]) for i in D["pasos"][k]["m"]}
        quietas = [i for i in todos if i not in movidas]
        if quietas: avi.append(f"{nom}: «Desarmar» no mueve {', '.join(quietas)}")
        if "marca" in g and len(g["marca"]) != 2: err.append(f"{nom}: «marca» va como [x, y]")
      except Exception as e:
        err.append(f"{nom}: el control de grupos falló ({type(e).__name__}: {e}); revisa el formato del grupo")
    sueltas = sorted(ids - set(vistos))
    if sueltas: err.append("v2: piezas sin grupo (no se pueden tocar): " + ", ".join(sueltas))
    for i in V.get("toqueExtra", []):
        if i not in ids: err.append(f"v2.toqueExtra: «{i}» no es un id de piezas")
    for k in V.get("con3d", []):
        if k not in fichas: err.append(f"v2.con3d: «{k}» no tiene ficha")
    if len(lados) > 1 and V.get("lado") not in lados: err.append("v2.lado: no está en v2.lados")
    CAMPOS = {"que", "sirve", "sintomas", "fallas", "porque", "cuando"}
    for k, F in fichas.items():
        cd = F.get("certezaDe")
        if cd is None:
            if not F.get("ctx"): avi.append(f"ficha {k}: sin certezaDe (las marcas ✓ manual / ≈ aprox. no salen)")
            continue
        for c, v in cd.items():
            if c not in CAMPOS: err.append(f"ficha {k}.certezaDe: campo «{c}» desconocido")
            elif v not in ("ok", "ap"): err.append(f"ficha {k}.certezaDe.{c}: «{v}» (va ok o ap)")
            elif not F.get(c): avi.append(f"ficha {k}.certezaDe.{c}: el campo está vacío")
        if (F.get("decision") or None) not in (None, "repara", "reutiliza", "cambia"): err.append(f"ficha {k}.decision: «{F['decision']}»")


# Tecnología de cada moto (por catálogo); una lámina puede declarar "tecnologia":{"inyeccion":true,"abs":true} y gana esa.
TECNOLOGIA = {"nmax-bbe4": {"inyeccion": True, "abs": True}}
# «rica» como palabra completa: nunca dentro de «eléctrica», aunque venga con tilde combinada, guion suave o un enlace [[n|…]] en medio
PAL_CARBURADOR = re.compile(r"(?<![\ẁ-ͯ-])(rica|rico en gasolina|chicl[eé]s?|carburador\w*|carbura\w*|ahogador)(?![\ẁ-ͯ])", re.I)


def texto_plano(t):
    """Texto para buscar palabras: sin etiquetas ni enlaces [[n|…]], en NFC y sin guiones suaves ni espacios de ancho cero."""
    t = re.sub(r"\[\[\d+[a-z]?\|", "", sin_html(t)).replace("]]", "")
    return unicodedata.normalize("NFC", t).replace("­", "").replace("​", "")
PAL_SILBIDO = re.compile(r"\b(silbido|succi[oó]n|aire falso)\b", re.I)
ANTES_MARIPOSA = re.compile(r"\b(uni[oó]n|caja|filtro|ducto|tapa)\b", re.I)
PAL_GASOLINA = re.compile(r"\b(gasolina|inyector|combustible)\b", re.I)


def todos_los_textos(D):
    """(dónde, texto) de todo lo que se lee: pasos, cadenas, «Cómo funciona», «Cuándo» y fichas completas."""
    for i, P in enumerate(D.get("pasos", [])): yield f"pasos[{i}]", P.get("t", ""), None
    for c in D.get("cadenas", []):
        for k, t in c.get("p", []): yield f"cadena «{c.get('t')}» ({k})", t, str(k)
    for i, P in enumerate(D.get("funciona", {}).get("pasos", [])): yield f"funciona[{i}]", P.get("t", ""), None
    for i, r in enumerate(D.get("cuando", [])): yield f"cuando[{i}]", r.get("que", "") + " " + r.get("cuando", ""), None
    for k, F in D.get("fichas", {}).items():
        for c in ("que", "sirve", "porque", "cuando"): yield f"ficha {k}.{c}", str(F.get(c, "")), k
        for c in ("sintomas", "arrastra"):
            for t in F.get(c, []): yield f"ficha {k}.{c}", t, k
        for _causa, t in F.get("fallas", []): yield f"ficha {k}.fallas", t, k


def revisar_tecnologia(D, err, avi):
    """14a [S]: palabras de carburador en una moto con inyección. 14b [S]: silbido (aire falso) en una pieza antes de la mariposa.
    10a [S]: un paso que toca gasolina pide chispas y revisar que no gotee."""
    tec = D.get("tecnologia") or TECNOLOGIA.get(D.get("catalogo", ""), {})
    nombres = {k: F.get("nombre", "") for k, F in D.get("fichas", {}).items()}
    for donde, t, k in todos_los_textos(D):
        if tec.get("inyeccion"):
            m = PAL_CARBURADOR.search(texto_plano(t))
            if m: err.append(f"{donde}: «{m.group(0)}» es de carburador; esta moto es de inyección (un filtro tapado no da mezcla rica: el computador manda menos gasolina)")
        if k and PAL_SILBIDO.search(t) and ANTES_MARIPOSA.search(nombres.get(k, "")) and "falso" not in t.lower():
            err.append(f"{donde}: silbido o succión en «{nombres[k]}», que va antes de la mariposa: ahí una grieta deja entrar aire sin filtrar, no aire falso")
    for i, P in enumerate(D.get("pasos", [])):
        t = sin_html(P.get("t", "")).lower()
        if PAL_GASOLINA.search(t) and not ("chispa" in t and "gote" in t):
            err.append(f"pasos[{i}]: toca gasolina y falta el aviso de incendio (motor frío, sin chispas, trapo para la presión residual y revisar que no gotee antes de prender)")


def revisar(D, ruta, cat, err, avi):
    """Corre todos los controles; si uno falla (formato inesperado), se reporta como error y se sigue con los demás."""
    controles = [
        (revisar_estructura_v2, (D,)),
        (revisar_orden_y_dificultad, (D,)),
        (revisar_seguridad_v2, (D, ruta,)),
        (revisar_estilo_v2, (D, cat,)),
        (revisar_cuando_repetido, (D,)),
        (revisar_sellos_freno, (D,)),
        (revisar_pasos_largos, (D,)),
        (revisar_regresion, (D, ruta,)),
        (revisar_sobremedida, (D,)),
        (revisar_nombres, (D,)),
        (revisar_referencias, (D, cat,)),
        (revisar_catalogo, (D, cat,)),
        (revisar_intervalos, (D,)),
        (revisar_3d, (D, ruta,)),
        (revisar_seguro_catalogo, (D, cat,)),
        (revisar_nombre_viejo, (D,)),
        (revisar_desarme, (D,)),
        (revisar_cifras, (D,)),
        (revisar_fuente_certeza, (D,)),
        (revisar_lado_version, (D, cat,)),
        (revisar_tecnologia, (D,)),
        (revisar_nombres_unicos, (D,)),
        (revisar_cantidad_texto, (D, cat,)),
        (revisar_rastros, (D, cat, ruta,)),
        (revisar_jerga, (D,)),
        (revisar_dos_nombres, (D,)),
        (revisar_orden_sistema, (D,)),
        (revisar_gato, (D,)),
        (revisar_n_dos_grupos, (D, cat)),
    ]
    for f, args in controles:
        try: f(*args, err, avi)
        except Exception as e: err.append(f"{f.__name__} no terminó ({type(e).__name__}: {e}): revisa el formato de lo que mira; los demás controles sí corrieron")


PAL_PASADOR = re.compile(r"^(pasador|pasadores|perno de centrado|pernos de centrado|anillo gu[ií]a|anillos gu[ií]a)\b", re.I)



def revisar_pasos_largos(D, err, avi):
    """Un paso del desarme o de «Cómo funciona» pasa de 250 caracteres de texto: lo que sale antes va a la ficha o a «Antes de esto»
    (los avisos de seguridad y los cierres nunca se acortan). Meta: 250."""
    for i, p in enumerate(D.get("pasos", [])):
        t = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", sin_html(p.get("t", "")))
        if len(t) > 250:
            avi.append(f"paso {i + 1}: {len(t)} caracteres (> 250); acórtalo y pasa «lo que sale antes» a la ficha (sin acortar avisos ni cierres)")
    for i, p in enumerate(D.get("funciona", {}).get("pasos", [])):
        t = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", sin_html(p.get("t", "")))
        if len(t) > 250: avi.append(f"funciona[{i}]: {len(t)} caracteres (> 250); acórtalo")


PAL_SOBREMEDIDA = re.compile(r"sobremedida|rectific\w*\s+(el|del)?\s*cilindro|cilindro\s+\w*\s*rectific|\bcamisa\b", re.I)


def revisar_sobremedida(D, err, avi):
    """Una ficha habla de sobremedida, de rectificar el cilindro o de camisa, y el catálogo de la moto no trae piezas de sobremedida."""
    if not D.get("catalogo"): return
    try:
        C = json.loads((AQUI / "catalogo" / f"{D['catalogo']}.json").read_text(encoding="utf-8"))
    except Exception:
        return
    hay = any(re.search(r"O/S|\(OS\)|\bO\.S\.|OVERSIZE|OVER SIZE|\b2ND\b|\b1ST\b.*SIZE", (pt.get("descripcion") or "").upper())   # Honda marca «(OS)»
              for f in C.get("figuras", {}).values() for pt in f.get("partes", []))
    if hay: return
    for k, F in D.get("fichas", {}).items():
        txt = " ".join(str(F.get(c, "")) for c in ("que", "sirve", "porque", "cuando")) + " " + " ".join(t for _c, t in F.get("fallas", [])) + " " + " ".join(F.get("arrastra", []))
        for m in PAL_SOBREMEDIDA.finditer(sin_html(txt)):
            if re.search(r"(no|sin)\s+(lleva\s+)?(\w+\s+){0,3}" + re.escape(m.group(0)), sin_html(txt), re.I): continue
            avi.append(f"ficha {k}: habla de «{m.group(0)}» y el catálogo {D['catalogo']} no trae piezas de sobremedida; ¿se rectifica de verdad?")
            break


PAL_PROCEDIMIENTO = ["PMS", "marca", "jeringa", "purga", "prueba", "probar", "nuev", "apriete", "torque", "N·m", "frío", "caliente",
                     "radiador", "gato", "guantes", "cadena", "cuidado", "nunca", "orden", "en cruz", "manual de servicio", "tapa la pintura"]


def textos_todos(D):
    yield from (p.get("t", "") for p in D.get("pasos", []))
    yield D.get("textoArmado", "")
    for F in D.get("fichas", {}).values():
        yield from (str(F.get(c, "")) for c in ("que", "sirve", "porque", "cuando"))
        yield from (t for _c, t in F.get("fallas", [])); yield from F.get("sintomas", []); yield from F.get("arrastra", [])
    yield from (x.get("t", "") for x in D.get("funciona", {}).get("pasos", []))
    yield from (c.get("que", "") + " " + c.get("cuando", "") for c in D.get("cuando", []))


def revisar_regresion(D, ruta, err, avi):
    """Compara las palabras de seguridad y de procedimiento con la versión guardada antes de corregir
    (datos/<lamina>.antes.json, que deja `autocontrol.py <lamina> --antes`): aviso por cada una que desaparece o baja
    de un paso concreto."""
    antes = pathlib.Path(ruta).with_suffix(".antes.json")
    if not antes.exists(): return
    try: A = json.loads(antes.read_text(encoding="utf-8"))
    except Exception: return
    ta, tn = sin_html(" ".join(textos_todos(A))).lower(), sin_html(" ".join(textos_todos(D))).lower()
    for w in PAL_PROCEDIMIENTO:
        na, nn = ta.count(w.lower()), tn.count(w.lower())
        if na and nn < na: avi.append(f"regresión: «{w}» aparecía {na} vez(es) antes de la corrección y ahora {nn}; revisa que no se perdiera un aviso o un paso")
    pa = {i: sin_html(p.get("t", "")).lower() for i, p in enumerate(A.get("pasos", []))}
    for i, p in enumerate(D.get("pasos", [])):
        t = sin_html(p.get("t", "")).lower()
        for w in PAL_PROCEDIMIENTO:
            if i in pa and w.lower() in pa[i] and w.lower() not in t:
                avi.append(f"regresión: el paso {i + 1} decía «{w}» y ya no (ponlo de vuelta o muévelo a la ficha a propósito)")

def revisar_nombres_unicos(D, err, avi):
    """V1: dos fichas con el mismo nombre de base, o un nombre con número suelto («Tapa 2»), dan aviso.
    V2: pasadores, pernos de centrado y anillos guía con decisión «repara» dan aviso (van «reutiliza» o «cambia»)."""
    base = {}
    for k, F in D.get("fichas", {}).items():
        n = (F.get("nombre") or "").strip()
        if not n: continue
        if re.search(r"(^|\s)(?<![A-Z]{2} )\d+(\s|$)", re.sub(r"\(.*?\)", "", n)) and not re.search(r"\b[A-Z]{2,}\s\d+", n):
            avi.append(f"ficha {k}: «{n}» lleva un número; mejor un nombre de lugar o de función")
        b = re.sub(r"\s+\d+$", "", n).lower()   # lo que va entre paréntesis («(trasera)», «(cortos)») sí distingue
        base.setdefault(b, []).append(k)
        cat = (F.get("cat") or "").upper()
        if F.get("decision") == "repara" and (PAL_PASADOR.search(n) or re.match(r"(PIN|DOWEL|PIN, DOWEL)\b", cat)):
            avi.append(f"ficha {k}: «{n}» con decisión «repara»; un pasador o anillo guía va «reutiliza» o «cambia»")
    for b, ks in base.items():
        if len(ks) > 1: avi.append(f"fichas {', '.join(ks)}: mismo nombre de base «{b}»; dales un nombre que las distinga")


# ---------- Revisión v2: lo que las revisoras encontraban a mano y la máquina puede ver ----------
# Cada control cubre una categoría de motor/revision/hallazgos.jsonl (ver aplicar_hallazgos.py --candidatas).
MARCAS = {"nmax-bbe4": ["NMAX", "Yamaha", "BBE4"], "honda-cb125f": ["Honda", "CB 125F", "CB125F", "GLH125"],
          "boxer-ct100": ["Boxer", "Bajaj", "CT100", "CT 100"], "akt-nkd125": ["AKT", "NKD"], "crypton-bf24": ["Crypton", "BF24"]}
FABRICANTES = ("Yamaha", "Honda", "Bajaj", "Auteco", "AKT", "Suzuki", "TVS", "Hero")   # la marca propia no es rastro de otra moto
JERGA = re.compile(r"copia entregada|consultad[oa]s? el\b|\(escribe|\bplantilla\b|scratchpad|según el json|(?-i:\bTODO\b|\bXXX\b)", re.I)
JERGA_SUAVE = re.compile(r"\((manual|cat[aá]logo)\)", re.I)   # fuente entre paréntesis sin decir cuál: aviso
REF_FIG = re.compile(r"\b([Ll][aá]mina|[Ff]ig\.?|[Ff]igura)\s*([A-Z]?\s?-?\s?\d+(?:\s?-\s?\d+)?)\b")
DET_SING = re.compile(r"^(un|una|el|la|del|al)$", re.I)
SOLO_UNO = re.compile(r"\b(un solo|una sola|[uú]nic[oa])\s+$", re.I)
DET_PLUR = re.compile(r"^(los|las|dos|ambos|ambas)$", re.I)
SIN_CANT = {"tornillo", "tuerca", "arandela", "perno", "esparrago", "espárrago", "oring", "o-ring", "anillo", "seguro", "pasador",
            "grapa", "abrazadera", "juego", "kit", "conjunto", "tapon", "tapón"}   # tornillería y conjuntos: el texto suele hablar en genérico


def textos_visibles(D):
    """(dónde, texto, ficha) de todo lo que se lee en la página, incluidas fuentes, cabeza y textos sueltos."""
    yield from todos_los_textos(D)
    for c in ("seguro", "aproximado"):
        for i, t in enumerate(D.get("fuentes", {}).get(c, [])): yield f"fuentes.{c}[{i}]", t, None
    for k, v in (D.get("cabeza") or {}).items(): yield f"cabeza.{k}", str(v), None
    for k, v in (D.get("visor") or {}).items(): yield f"visor.{k}", str(v), None   # ronda 7: «Fig. F-8 · 19 números» en el sub
    if D.get("pie"): yield "pie", str(D["pie"]), None
    for k, v in (D.get("textos") or {}).items():
        if isinstance(v, str): yield f"textos.{k}", v, None
    yield "textoArmado", D.get("textoArmado", ""), None
    for k, F in D.get("fichas", {}).items():
        if F.get("nombre"): yield f"ficha {k}.nombre", F["nombre"], k
    for i, t in enumerate(D.get("pendientes", [])): yield f"pendientes[{i}]", t, None


def arte_texto(D, ruta):
    a = pathlib.Path(ruta).parent / f"{D.get('arte') or D.get('lamina')}-arte.js"
    return a.read_text(encoding="utf-8") if a.exists() else ""


def palabras(t):
    return re.findall(r"[A-Za-zÁÉÍÓÚÜáéíóúüñÑ-]+", texto_plano(t))


def revisar_cantidad_texto(D, cat, err, avi):
    """R1: «un solo pistón» (error) o «el/un pistón» (aviso) cuando el catálogo trae 2 o más; «los/dos …» con 1."""
    if not cat: return
    cant = {}
    for q in cat["partes"]: cant[q["ref"]] = max(cant.get(q["ref"], 0), q.get("cantidad") or 0)
    desc = {}
    for q in cat["partes"]: desc[q["ref"]] = desc.get(q["ref"], "") + " " + q.get("descripcion", "")
    cabezas, cuantas, juego = {}, {}, set()
    for k, F in D.get("fichas", {}).items():
        if F.get("ctx") or k not in cant or not F.get("nombre"): continue
        w = palabras(F["nombre"])
        if not w or base(w[0]) in {base(x) for x in SIN_CANT}: continue
        b = base(w[0]); cabezas.setdefault(b, set()).add(cant[k] >= 2); cuantas[b] = cuantas.get(b, 0) + 1
        if w[0].lower().endswith("s") or re.search(r"\b(SET|KIT|COMP|JUEGO|ASSY|PAD|SHOE)\b", desc[k].upper()): juego.add(b)
    cabezas = {b: v.pop() for b, v in cabezas.items() if len(v) == 1}   # si dos piezas con la misma cabeza difieren, no se juzga
    # el plural con 1 no se juzga si la cabeza es de varias fichas («las guías» = admisión + escape), va en plural en el nombre
    # o es un juego (pastillas, zapatas, rodillos: el catálogo cuenta el juego); tampoco si habla de las de otra lámina («las bombas»)
    plural_ok = {b for b in cabezas if cuantas[b] > 1 or b in juego}
    vistos = set()
    for donde, t, _k in todos_los_textos(D):
        plano_ = texto_plano(t)
        for m in re.finditer(r"[A-Za-zÁÉÍÓÚÜáéíóúüñÑ-]+", plano_):
            w = m.group(0); b = base(w)
            if b not in cabezas or (donde.split(".")[0], b) in vistos: continue
            antes = plano_[max(0, m.start() - 20):m.start()]
            prev = (antes.split() or [""])[-1]
            plural = w.lower().endswith("s")
            muchos = cabezas[b]
            if muchos and not plural and SOLO_UNO.search(antes):
                err.append(f"{donde}: «{antes.split()[-2]} {prev} {w}», pero el catálogo trae 2 o más"); vistos.add((donde.split(".")[0], b))
            elif muchos and not plural and DET_SING.match(prev) and prev.lower() in ("un", "una"):
                avi.append(f"{donde}: «{prev} {w}», pero el catálogo trae 2 o más (¿«uno de los…» o plural?)"); vistos.add((donde.split(".")[0], b))
            elif not muchos and plural and DET_PLUR.match(prev) and b not in plural_ok:
                avi.append(f"{donde}: «{prev} {w}», pero el catálogo trae 1"); vistos.add((donde.split(".")[0], b))


def revisar_rastros(D, cat, ruta, err, avi):
    """R2: rastros de la lámina hermana: nombre de otra moto (error) y «lámina N»/«fig. N» que no es la propia (aviso),
    en textos visibles (cabeza.cinta incluida), fuentes y rótulos del arte. Con «hermana» en el JSON (receta 3b), además:
    la figura de la hermana nombrada (error) y referencias copiadas tal cual de la hermana de otro catálogo (aviso)."""
    propias = set(MARCAS.get(D.get("catalogo", ""), []))
    dueño = " ".join([str(D.get("moto", "")), str(D.get("catalogo", "")), (cat or {}).get("fuente", ""), (cat or {}).get("moto", "")]).lower()
    propias |= {f for f in FABRICANTES if f.lower() in dueño}
    if propias & set(MARCAS.get("nmax-bbe4", [])) or D.get("catalogo", "").startswith(("crypton", "nmax")): propias.add("Yamaha")
    otras = [m for c, ms in MARCAS.items() if c != D.get("catalogo") for m in ms if m not in propias]
    pat = re.compile(r"(?<![\w-])(" + "|".join(re.escape(m) for m in otras) + r")(?![\w-])") if otras else None
    fig = re.sub(r"[\s-]", "", str(D.get("figura", ""))).upper()
    arte = arte_texto(D, ruta)
    H, hfig, hrefs = None, None, set()
    hj = pathlib.Path(ruta).parent / f"{D.get('hermana')}.json" if D.get("hermana") else None
    if hj and hj.exists():
        H = json.loads(hj.read_text(encoding="utf-8"))
        hfig = re.sub(r"[\s-]", "", str(H.get("figura", ""))).upper()
        if H.get("catalogo") != D.get("catalogo"): hrefs = {r for _d, t, _k in textos_visibles(H) for r in refs_fig(texto_plano(t))} | refs_fig(arte_texto(H, hj))
    fuentes = list(textos_visibles(D)) + [("arte", " ".join(re.findall(r">([^<>{}]{2,})<", arte)) + " " + " ".join(re.findall(r"[\"'`]([^\"'`]{3,80})[\"'`]", arte)), None)]
    if H is not None and (D.get("remapeo") or H.get("catalogo") == D.get("catalogo")):   # enlaces y cadenas copiados de la hermana: su número tiene que ser el remapeado (ni el viejo ni remapeado dos veces)
        N = (D.get("remapeo") or {}).get("mapa") or {}
        def m(x):
            r = re.fullmatch(r"(\d+)([a-z]?)", x or "")
            return N[x] if x in N else (N[r.group(1)] + r.group(2) if r and r.group(1) in N else x)
        hcad = {}
        for c in H.get("cadenas", []):
            for k, t in c.get("p", []): hcad.setdefault(texto_plano(t).strip(), set()).add(k)
        for c in D.get("cadenas", []):
            for k, t in c.get("p", []):
                hs = hcad.get(texto_plano(t).strip())
                if hs and len(hs) == 1 and (not N or (re.sub(r"[a-z]$", "", k) in set(N.values()) and re.sub(r"[a-z]$", "", next(iter(hs))) in N)) and k != m(next(iter(hs))):
                    err.append(f"cadena «{c.get('t')}»: el eslabón «{texto_plano(t)[:40]}» apunta a {k}; en la hermana era {next(iter(hs))} → debería ser {m(next(iter(hs)))} (¿remapeo?)")
        henl = {}
        for _d, t, _k in textos_visibles(H):
            for r in re.finditer(r"\[\[([^|\]]+)\|([^\]]+)\]\]", t or ""): henl.setdefault(r.group(2).strip().lower(), set()).add(r.group(1))
        malos = set()
        destinos = set(N.values())
        base = lambda x: re.sub(r"[a-z]$", "", x or "")
        # ronda 7: solo enlaces entre piezas que vienen del mapa (las nuevas, el lado espejado y las fichas propias no se comparan)
        heredado = lambda k, h: (not N or (base(k) in destinos and base(h) in N))
        for donde, t, _k in textos_visibles(D):
            if N and _k is not None and base(_k) not in destinos: continue   # ficha nueva: sus enlaces son propios
            for r in re.finditer(r"\[\[([^|\]]+)\|([^\]]+)\]\]", t or ""):
                hs = henl.get(r.group(2).strip().lower())
                if hs and len(hs) == 1 and heredado(r.group(1), next(iter(hs))) and r.group(1) != m(next(iter(hs))) and (r.group(0)) not in malos:
                    malos.add(r.group(0)); err.append(f"{donde}: enlace «{r.group(2)}» apunta a {r.group(1)}; en la hermana era {next(iter(hs))} → debería ser {m(next(iter(hs)))} (¿remapeado dos veces?)")
    for donde, t, _k in fuentes:
        tp = texto_plano(t) if donde != "arte" else t
        if pat:
            m = pat.search(tp)
            # en Fuentes puede ir a propósito («de tres cuartos, como el clutch de la Boxer»): ahí es aviso
            if m: (avi if donde.startswith("fuentes") else err).append(f"{donde}: «{m.group(0)}» es de otra moto (¿rastro de la lámina hermana?)")
        if H is not None and "pendientes" not in donde:
            for r in refs_fig(tp) - {fig}:
                if r == hfig and H.get("figura") != D.get("figura"):
                    err.append(f"{donde}: nombra la fig. {r}, que es la de la lámina hermana ({D['hermana']}): rastro"); break
                if r in hrefs:
                    avi.append(f"{donde}: «fig./lámina {r}» está igual en la hermana ({D['hermana']}, otro catálogo): verifícala en el catálogo de esta moto"); break
        for m in REF_FIG.finditer(tp):
            r = re.sub(r"[\s-]", "", m.group(2)).upper()
            # «ver fig. 7» del mismo catálogo vale; se marca la figura con el formato de otro catálogo (22 en una Honda F10)
            if r != fig and r[:1].isalpha() != fig[:1].isalpha() and "pendientes" not in donde:
                avi.append(f"{donde}: «{m.group(0)}» no es la figura de esta lámina ({D.get('figura')}): ¿rastro de la hermana?"); break


def refs_fig(t):
    """{"21","18","26"} de «fig. 21», «(lámina 18/26)»."""
    out = set()
    for m in re.finditer(r"\b(?:[Ll][aá]mina|[Ff]ig\.?|[Ff]igura)s?\s*([A-Z]?\s?-?\s?\d+(?:\s*/\s*[A-Z]?\d+)*)", t or ""):
        out |= {re.sub(r"[\s-]", "", x).upper() for x in m.group(1).split("/")}
    return out


def revisar_jerga(D, err, avi):
    """R3: jerga interna o relleno en lo que se lee («copia entregada por el usuario», «consultado el», «(manual)», «(Escribe…)»)."""
    for donde, t, _k in textos_visibles(D):
        if donde.startswith("pendientes"): continue
        m = JERGA.search(texto_plano(t))
        if m: err.append(f"{donde}: «{m.group(0)}» es jerga interna o relleno; no va en un texto que se lee")
        m = JERGA_SUAVE.search(texto_plano(t))
        if m: avi.append(f"{donde}: «{m.group(0)}» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes")


def revisar_dos_nombres(D, err, avi):
    """R4: una misma pieza con dos nombres (sinónimos del glosario: empaque/junta, retén/sello, rodamiento/balinera…):
    error si el enlace [[n|…]] o «nombres» usan un sinónimo distinto del nombre de la ficha; aviso si la prosa usa
    un sinónimo que ninguna ficha usa como nombre."""
    F = D.get("fichas", {})
    nb = {k: {base(w) for w in palabras(f.get("nombre", ""))} for k, f in F.items()}
    for k, v in D.get("nombres", {}).items():
        for w in palabras(v):
            g = grupo(base(w))
            if g and k in nb and base(w) not in nb[k] and g & nb[k]:
                err.append(f"nombres.{k}: «{w}», pero la ficha {k} se llama «{F[k].get('nombre')}»: un solo nombre por pieza")
    usados = set().union(*nb.values()) if nb else set()
    original = {base(w): w.lower() for f in F.values() for w in palabras(f.get("nombre", ""))}
    vistos = set()
    for donde, t, _k in todos_los_textos(D):
        for m in re.finditer(r"\[\[([^|\]]+)\|([^\]]+)\]\]", t or ""):
            k = m.group(1)
            for w in palabras(m.group(2)):
                g = grupo(base(w))
                if g and k in nb and base(w) not in nb[k] and g & nb[k]:
                    err.append(f"{donde}: enlace «{m.group(2)}» a {k}, que se llama «{F[k].get('nombre')}»: un solo nombre por pieza")
        ws = palabras(re.sub(r"\[\[[^\]]+\]\]", " ", t or ""))
        for i, w in enumerate(ws):
            b = base(w); g = grupo(b)
            if b == "junta" and (i == 0 or not re.fullmatch(r"(?i)la|las|una|su|sus|esta|nueva|de|del|sin|otra", ws[i - 1])): continue   # verbo «juntar»
            if g and b not in usados and g & usados and (b, donde.split()[0]) not in vistos:
                vistos.add((b, donde.split()[0]))
                avi.append(f"{donde}: «{w}», pero las fichas usan «{'/'.join(sorted(original.get(x, x) for x in g & usados))}»: ¿la misma pieza con otro nombre?")


def revisar_n_dos_grupos(D, cat, err, avi):
    """Ronda 8: un mismo número de pieza (n) en dos grupos del mismo lado rompe el toque en escritorio (tocarlo cambia de grupo).
    Si el catálogo trae esa pieza con cantidad 2 o más (dos barras iguales), es aviso; si no, error."""
    V = D.get("v2") or {}
    n = {p["id"]: str(p.get("n", p["id"])) for p in D.get("piezas", [])}
    cant = {}
    for q in (cat or {}).get("partes", []):
        try: cant[q["ref"]] = max(cant.get(q["ref"], 0), int(q.get("cantidad") or 1))
        except (TypeError, ValueError): pass
    donde = {}
    for g in V.get("grupos", []):
        if not isinstance(g, dict): continue
        ids = list(g.get("piezas", [])) + [i for t in g.get("torn", []) if isinstance(t, dict) for i in t.get("ids", [])]
        for i in ids: donde.setdefault((n.get(i, i), g.get("lado") or ""), {}).setdefault(g.get("id"), []).append(i)
    for (k, _lado), gs in donde.items():
        if len(gs) < 2: continue
        txt = " y ".join(f"«{g}» ({', '.join(ids)})" for g, ids in gs.items())
        if cant.get(k, 1) >= len(gs): avi.append(f"el número {k} está en dos grupos: {txt}; el catálogo trae {cant[k]}, revisa que tocarlo abra el grupo correcto")
        else: err.append(f"el número {k} está en dos grupos: {txt}. Un número por grupo: si son piezas distintas, dales su propio número del catálogo; si es la misma, déjala en un solo grupo (rompe el toque a 1024/1280)")


def revisar_gato(D, err, avi):
    """Ronda 7 (anexo-desarme, por tipo de moto): el gato central levanta la trasera; la delantera necesita calzo o elevador."""
    pat = re.compile(r"gato central[^.]{0,90}(rueda )?delanter\w*[^.]{0,40}(aire|levant|suspend|libre)|delanter\w*[^.]{0,40}(en el aire|levantad)[^.]{0,60}gato central", re.I)
    for donde, t, _k in todos_los_textos(D):
        m = pat.search(texto_plano(t))
        if m and not re.search(r"calz|elevador|bajo el chasis|bajo el motor|soporte bajo", texto_plano(t)[max(0, m.start() - 80):m.end() + 80], re.I):
            avi.append(f"{donde}: el gato central levanta la rueda trasera, no la delantera: calza firme bajo el chasis o usa elevador (anexo-desarme, por tipo de moto)"); break


# ---------- Ronda 4: orden del desarme por sistema (.claude/skills/hacer-lamina/anexo-desarme.md) ----------
# (lo que va primero, lo que no puede ir antes, aviso). Se busca en el texto de los pasos, en orden; solo si aparecen los dos.
ORDEN_SISTEMA = [
    (r"\btap[oó]n\b", r"(afloj|suelt|sac)\w*\s+(los\s+|sus\s+)?(pernos|tornillos)[^.]{0,30}tijera", "suspensión: el tapón se afloja con la barra aún apretada en la tijera de abajo; después, los pernos de la tijera"),
    (r"(saca|retira|quita|afloja)\w*\s+(el\s+)?eje\b", r"(saca|retira|quita|baja)\w*\s+la\s+rueda", "rueda: primero se suelta y saca el eje; después sale la rueda"),
    (r"c[aá]liper", r"(saca|retira|quita|baja)\w*\s+la\s+rueda\s+delantera", "rueda delantera: primero el cáliper; después la rueda"),
    (r"\bPMS\b|marcas?\s+(de\s+)?(sincron|alinea)", r"(saca|suelta|retira)\w*\s+(la\s+)?cadena\s+de\s+distribuci|(saca|suelta|retira)\w*\s+(el\s+)?pi[ñn][oó]n\s+del\s+[aá]rbol", "culata: PMS y marcas alineadas antes de soltar la cadena o el piñón del árbol de levas"),
    (r"tensor", r"(saca|suelta|retira)\w*\s+(el\s+)?pi[ñn][oó]n\s+del\s+[aá]rbol", "culata: el tensor sale antes del piñón del árbol de levas"),
    (r"(afloja|suelta)\w*\s+(el\s+)?cable|juego\s+libre", r"(saca|abre|retira|quita)\w*\s+la\s+tapa\s+del\s+clutch", "clutch: el cable se afloja antes de abrir la tapa"),
    (r"negativo", r"(desconecta|suelta|saca)\w*\s+(el\s+)?(borne\s+)?positivo", "eléctrico: primero el borne negativo"),
]


def revisar_orden_sistema(D, err, avi):
    """Ronda 4: un paso que hace algo antes de lo que debe ir primero (anexo-desarme.md). Aviso, con el paso."""
    tramos, pos = [], 0
    for i, P in enumerate(D.get("pasos", [])):
        t = texto_plano(P.get("t", "")); tramos.append((pos, pos + len(t), i)); pos += len(t) + 1
    todo = " ".join(texto_plano(P.get("t", "")) for P in D.get("pasos", []))
    paso = lambda o: next((i for a, b, i in tramos if a <= o <= b), 0) + 1
    for antes, despues, msg in ORDEN_SISTEMA:
        ma, md = re.search(antes, todo, re.I), re.search(despues, todo, re.I)
        if ma and md and md.start() < ma.start():
            avi.append(f"orden del desarme: paso {paso(md.start())} «{md.group(0)[:40]}» antes de «{ma.group(0)[:30]}» (paso {paso(ma.start())}) · {msg}")


if __name__ == "__main__":
    ruta = pathlib.Path(sys.argv[1])
    D = json.loads(ruta.read_text(encoding="utf-8"))
    err, avi = [], []
    cat = None
    if D.get("catalogo"):
        cat = json.loads((AQUI / "catalogo" / f"{D['catalogo']}.json").read_text(encoding="utf-8"))["figuras"].get(str(D["figura"]))
    revisar(D, ruta, cat, err, avi)
    for a in avi:
        print("  aviso:", a)
    for e in err:
        print("  ERROR:", e)
    print("OK" if not err else f"{len(err)} error(es)")
