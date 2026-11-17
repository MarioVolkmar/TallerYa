"""Regresión de la skill hacer-lamina según lo que cambió (después de tocar la skill, los scripts o el motor).

  python regresion.py                 decide qué revisar con git status (y lo ya revisado en la corrida anterior)
  python regresion.py <archivo> ...   decide a partir de esos archivos
  python regresion.py --todas         las láminas en el navegador, con caché (antes de un commit grande; córrelo en segundo plano)
  python regresion.py --todas --sin-cache    todas de verdad
  python regresion.py --aceptar       guarda como referencia el extractor, el esqueleto y las firmas de hoy (tras un cambio querido)

Siempre (< 1 min): validador en todas las láminas (en paralelo) y extractor + esqueleto de NMAX, Boxer, AKT y Honda
comparados byte a byte con regresion/ref/.
Cambió el motor (esquema*.js/css, piezas-comunes.js, medir_*, chequeo_rapido.py): chequeo en el navegador y firmas solo en
REPRESENTATIVAS. Cambiaron los datos, el arte o la página de una lámina: solo esa. Catálogo, plantillas, esqueleto o la
skill: nada de navegador. Resumen en regresion/ultimo.md.
"""
import hashlib, json, os, pathlib, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
REG = AQUI / "regresion"
PY = sys.executable
# la lista vive aquí: CVT NMAX (fig. 12), culata Honda y la última lámina creada (la última de metricas.json con página)
REPRESENTATIVAS = ["nmax-fig12", "cb125f-culata", "@ultima"]
MOTOR = re.compile(r"motor/(esquema[^/]*\.(js|css)|piezas-comunes\.js|medir_[^/]*|chequeo_rapido\.py)$")
SIN_NAVEGADOR = re.compile(r"motor/catalogo/|motor/(plantillas_ficha|esqueleto_v2|metricas|aplicar_hallazgos|informe_revision|regresion|validar_esquema|mas_controles|autocontrol)\.py$|\.claude/skills/hacer-lamina/")
CAPAS_RUIDO = ("guiasG", "marcasG")   # varían entre corridas aunque el motor no cambie
EXTRACTOR = [   # (nombre, pdf, argumentos)
    ("nmax", "despiece_local/N-MAX-BBE4-2024.pdf", []),
    ("boxer", "manual_despiece/auteco-bajaj-boxer-ct-100/bajaj-boxer-ct100-2017-colombia-catalogo-partes.pdf", ["--figura", "14", "--columna", "TEC"]),
    ("akt", "manual_despiece/akt-nkd-125/akt-nkd125-cbs-2025-catalogo-partes.pdf", ["--figura", "E4"]),
    ("honda", "manual_despiece/honda-cb-125f/honda-cb125f-glh125sh-catalogo-partes.pdf", ["--figura", "F10", "--columna", "C", "--saltar", "2U"]),
    ("honda-f22", "manual_despiece/honda-cb-125f/honda-cb125f-glh125sh-catalogo-partes.pdf", ["--figura", "F22-1", "--columna", "C", "--saltar", "2U"]),   # códigos sin sufijo y descripción en la línea del código
    ("crypton", "manual_despiece/yamaha-crypton-fi-115/yamaha-crypton-fi-115-2019-bf24-colombia-catalogo-partes.pdf", ["--moto", "crypton-bf24"]),   # Yamaha bilingüe
]
ESQUELETO = [("nmax", "nmax-bbe4", "22"), ("boxer", "boxer-ct100", "14"), ("akt", "akt-nkd125", "E4"), ("honda", "honda-cb125f", "F10"), ("akt-rueda", "akt-nkd125", "F8")]


def correr(args, timeout=600):
    r = subprocess.run([PY] + [str(a) for a in args], cwd=RAIZ, capture_output=True, timeout=timeout, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def sha(*rutas):
    h = hashlib.sha1()
    for p in rutas:
        p = pathlib.Path(p)
        h.update(p.name.encode()); h.update(p.read_bytes() if p.exists() else b"-")
    return h.hexdigest()[:16]


def paginas():
    """{lámina: página} (la de nombre más corto que hace fetch de datos/<lámina>.json)."""
    out = {}
    for f in sorted(AQUI.glob("*.html"), key=lambda x: len(x.name)):
        m = re.search(r'fetch\("datos/([\w\-]+)\.json"\)', f.read_text(encoding="utf-8", errors="replace"))
        if m and not m.group(1).endswith("-v1") and (AQUI / "datos" / f"{m.group(1)}.json").exists(): out.setdefault(m.group(1), f.name)
    return out


def laminas():
    return sorted(p.stem for p in (AQUI / "datos").glob("*.json") if not re.search(r"\.(antes|esqueleto|hallazgos)$|-v1$|^_", p.stem))


def ultima():
    try:
        M = json.loads((AQUI / "metricas.json").read_text(encoding="utf-8"))
        pag = paginas()
        return [k for k in M.get("laminas", {}) if k in pag][-1]
    except Exception:
        return None


def representativas():
    return list(dict.fromkeys(ultima() if x == "@ultima" else x for x in REPRESENTATIVAS if x))


def archivos_lamina(lam):
    pag = paginas().get(lam)
    return [AQUI / "datos" / f"{lam}.json", AQUI / "datos" / f"{lam}-arte.js"] + ([AQUI / pag] if pag else [])


def archivos_motor():
    return sorted(p for p in AQUI.iterdir() if p.is_file() and MOTOR.search("motor/" + p.name))


def relevantes():
    """Todo lo que la regresión vigila, con su hash (para saber qué cambió desde la corrida anterior)."""
    fs = [p for p in AQUI.rglob("*") if p.is_file() and p.suffix in (".py", ".js", ".css", ".html", ".json") and "regresion" not in p.parts
          and not re.search(r"\.(antes|esqueleto|hallazgos)\.json$|metricas\.json$|\.jpg$", p.name) and "prototipo" not in str(p)]
    fs += list((RAIZ / ".claude" / "skills" / "hacer-lamina").glob("*"))
    return {str(p.relative_to(RAIZ)).replace("\\", "/"): sha(p) for p in fs}


def cambiados(args):
    if args: return [str(pathlib.Path(a).resolve().relative_to(RAIZ)).replace("\\", "/") for a in args]
    r = subprocess.run(["git", "status", "--porcelain", "-uall", "--", str(AQUI), ".claude/skills/hacer-lamina"], cwd=RAIZ, capture_output=True)
    git = {l[3:].strip().strip('"') for l in r.stdout.decode("utf-8", "replace").splitlines()}
    ahora = relevantes()
    est = REG / "estado.json"
    if est.exists():   # de lo que git ve cambiado, solo lo que cambió desde la última regresión
        antes = json.loads(est.read_text(encoding="utf-8"))
        return sorted(f for f in ahora if f in git and antes.get(f) != ahora[f])
    return sorted(f for f in ahora if f in git)


def siempre(res):
    """Validador en todas (en paralelo) + extractor y esqueleto byte a byte."""
    t0 = time.time()
    def val(lam):
        c, o = correr([AQUI / "validar_esquema.py", AQUI / "datos" / f"{lam}.json"], 300)
        return lam, len([l for l in o.splitlines() if "ERROR" in l])
    with ThreadPoolExecutor(6) as ex: v = list(ex.map(val, laminas()))
    malos = [f"{l} ({n})" for l, n in v if n]
    res.append(("validador", not malos, f"{len(v)} láminas, " + (f"con errores: {', '.join(malos)}" if malos else "0 errores")))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="regresion_"))
    def ext(e):
        n, pdf, ar = e
        if not (RAIZ / pdf).exists(): return n, None
        correr([AQUI / "catalogo" / "extraer_catalogo.py", RAIZ / pdf, tmp / f"{n}.json"] + ar)
        return n, tmp / f"{n}.json"
    def esq(e):
        n, moto, fig = e; lam = f"_reg-{n}"
        correr([AQUI / "esqueleto_v2.py", moto, fig, lam, "--escribir"])
        out = AQUI / "datos" / f"{lam}.json"; t = out.read_bytes() if out.exists() else b""
        for x in (out, AQUI / "datos" / f"{lam}.esqueleto.json"):
            if x.exists(): x.unlink()
        (tmp / f"esq-{n}.json").write_bytes(t); return f"esq-{n}", tmp / f"esq-{n}.json"
    with ThreadPoolExecutor(8) as ex: salidas = list(ex.map(ext, EXTRACTOR)) + list(ex.map(esq, ESQUELETO))
    difieren, faltan = [], []
    for n, p in salidas:
        ref = REG / "ref" / f"{n if n.startswith('esq-') else 'ext-' + n}.json"
        if p is None: faltan.append(n); continue
        if not ref.exists(): faltan.append(n + " (sin referencia: --aceptar)"); continue
        if p.read_bytes() != ref.read_bytes(): difieren.append(n)
    res.append(("extractor y esqueleto", not difieren, ("idénticos" if not difieren else "DIFIEREN: " + ", ".join(difieren)) + (f" · sin comparar: {', '.join(faltan)}" if faltan else "")))
    return salidas, time.time() - t0


def navegador(lams, anchos, res, etiqueta):
    pag = paginas(); lista = [pag[l] for l in lams if l in pag]
    if not lista: return {}
    out = pathlib.Path(tempfile.mkstemp(suffix=".json")[1])
    t0 = time.time()
    correr([AQUI / "chequeo_rapido.py", "--paginas", ",".join(lista), "--sin-validador", "--json", out, "--anchos", anchos, "--paralelo", "5"], 1200)
    R = json.loads(out.read_text(encoding="utf-8") or "{}") if out.exists() else {}
    bloq = {l: r["bloq"] for l, r in R.items() if r["bloq"]}
    res.append((f"navegador ({etiqueta})", not bloq and len(R) == len(lista), f"{len(R)} de {len(lista)} láminas, anchos {anchos}, {time.time() - t0:.0f} s"
                + ("".join(f" · {l}: {'; '.join(b)[:160]}" for l, b in bloq.items()) if bloq else " · sin bloqueantes")
                + (f" · avisos en {', '.join(l for l, r in R.items() if r['avi'])}" if any(r["avi"] for r in R.values()) else "")))
    return R


def firmas(lams, res, aceptar=False):
    pag = paginas(); ps = [AQUI / pag[l] for l in lams if l in pag]
    ref = REG / "ref" / "firmas.json"
    if aceptar or not ref.exists():
        correr([AQUI / "firma_lamina.py"] + ps + ["--guardar", ref], 600); res.append(("firmas", True, f"guardadas de {len(ps)} láminas")); return
    c, o = correr([AQUI / "firma_lamina.py"] + ps + ["--comparar", ref], 600)
    cambios = [l.strip() for l in o.splitlines() if " capa " in l and not any(x in l for x in CAPAS_RUIDO)]
    def un_px(l):   # «antes ['pz-2', 322, 321, 278, 145, 42] · ahora [... 146 ...]»: el redondeo varía 1 px entre corridas
        m = re.findall(r"\[([^\]]*)\]", l)
        if len(m) < 2: return False
        a, b = [x.strip(" '") for x in m[-2].split(",")], [x.strip(" '") for x in m[-1].split(",")]
        return len(a) == len(b) and a[0] == b[0] and all(abs(float(x) - float(y)) <= 1 for x, y in zip(a[1:], b[1:]) if x.replace(".", "").lstrip("-").isdigit())
    ruido = [l for l in cambios if un_px(l)]; cambios = [l for l in cambios if l not in ruido]
    res.append(("firmas", not cambios, f"{len(ps)} láminas: " + ("iguales (fuera de guiasG/marcasG" + (f"; {len(ruido)} capa(s) con ±1 px de redondeo" if ruido else "") + ")" if not cambios else "; ".join(cambios)[:300])))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t0 = time.time(); REG.mkdir(exist_ok=True); (REG / "ref").mkdir(exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    res, decide = [], []
    if "--aceptar" in sys.argv:
        salidas, _ = siempre(res)
        for n, p in salidas:
            if p is not None: (REG / "ref" / f"{n if n.startswith('esq-') else 'ext-' + n}.json").write_bytes(p.read_bytes())
        firmas(representativas(), res, aceptar=True)
        print("referencias guardadas en motor/regresion/ref/ (extractor, esqueleto y firmas)"); return 0
    ch = cambiados(args)
    motor = [f for f in ch if MOTOR.search(f)]
    lams_cambio = sorted({l for l in laminas() for f in ch if any(f.endswith(str(x.relative_to(RAIZ)).replace("\\", "/")) for x in archivos_lamina(l))})
    cache_p = REG / "cache.json"; cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    hm = sha(*archivos_motor())
    if "--todas" in sys.argv:
        hs = {l: sha(*archivos_lamina(l), *archivos_motor()) for l in laminas()}
        revisar = [l for l in laminas() if "--sin-cache" in sys.argv or cache.get(l) != hs[l]]
        anchos = "360,390,1280" if cache.get("_motor") != hm else "390,1280"
        decide.append(f"--todas: {len(revisar)} de {len(hs)} láminas en el navegador ({len(hs) - len(revisar)} sin cambios desde su último OK); anchos {anchos}"
                      + (" (cambió el motor)" if cache.get("_motor") != hm else ""))
    elif motor:
        revisar, anchos = sorted(set(representativas()) | set(lams_cambio)), "360,390,1280"
        decide.append(f"cambió el motor ({', '.join(pathlib.Path(f).name for f in motor)}): navegador y firmas en {', '.join(revisar)}")
    elif lams_cambio:
        revisar, anchos = lams_cambio, "390,1280"
        decide.append(f"cambiaron datos/arte/página de: {', '.join(lams_cambio)}: solo esas en el navegador")
    else:
        revisar, anchos = [], ""
        otros = [pathlib.Path(f).name for f in ch]
        decide.append("sin cambios de motor ni de láminas" + (f" ({', '.join(otros[:6])}{'…' if len(otros) > 6 else ''}): nada de navegador" if otros else ": nada de navegador"))
    print("DECIDE: " + " · ".join(decide)); sys.stdout.flush()
    siempre(res)
    R = navegador(revisar, anchos, res, "todas" if "--todas" in sys.argv else ", ".join(revisar)) if revisar else {}
    if motor and "--todas" not in sys.argv: firmas(representativas(), res)
    for l in revisar:   # caché: lo que pasó sin bloqueantes no se vuelve a revisar mientras no cambie
        r = R.get(l)
        if r is not None and not r["bloq"]: cache[l] = sha(*archivos_lamina(l), *archivos_motor())
    if "--todas" in sys.argv and all(not (R.get(l) or {}).get("bloq") for l in revisar): cache["_motor"] = hm
    cache_p.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    (REG / "estado.json").write_text(json.dumps(relevantes(), indent=0), encoding="utf-8")
    ok = all(x[1] for x in res)
    lineas = [f"{'✓' if b else '✘'} {n}: {t}" for n, b, t in res] + [f"{'OK' if ok else 'FALLA'} · {time.time() - t0:.0f} s"]
    print("\n".join(lineas))
    (REG / "ultimo.md").write_text(f"# Regresión {time.strftime('%Y-%m-%d %H:%M')}\n\nDECIDE: {' · '.join(decide)}\n\n" + "\n".join(f"- {l}" for l in lineas) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
