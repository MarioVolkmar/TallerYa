"""Resumen compacto de una lámina para las revisoras: revision/<lamina>.md (lo escribe «autocontrol.py <lamina> --informe»).
Revisión v2: solo lo que se lee (textos visibles), las cantidades del catálogo, fuentes y certezas, y las páginas del manual
que aplican. Con una lámina hermana (`--hermana <lamina>` o "hermana" en el JSON), lo heredado sin cambio se resume en una línea:
ya se revisó en la hermana. La revisión mira solo lo que la máquina no mide (guia-revision-rapida.md)."""
import json, pathlib, re, subprocess, sys, unicodedata

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
from buscar_manual import carpeta, tipo, impresa, limpio   # carpeta de manual_despiece por el catálogo (ronda 9: sin lista fija)


def plano(t):
    t = re.sub(r"\[\[(\w+)\|([^\]]+)\]\]", r"\2 (\1)", str(t))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def clave(t):
    """Para comparar con la hermana: sin enlaces ni números de pieza, minúsculas y sin tildes."""
    t = re.sub(r"\[\[\w+\|([^\]]+)\]\]", r"\1", str(t))
    t = re.sub(r"<[^>]+>|\(\d+[a-z]?\)", "", t).lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return re.sub(r"\W+", " ", t).strip()


def todos(x):
    if isinstance(x, str): yield x
    elif isinstance(x, dict):
        for v in x.values(): yield from todos(v)
    elif isinstance(x, list):
        for v in x: yield from todos(v)


def paginas_manual(D, tope=6):
    """Páginas del manual de la moto donde aparecen las piezas de la lámina (texto con pymupdf; los PDF solo se leen)."""
    try: import pymupdf
    except ImportError: return ["- (pymupdf no está: busca a mano en el índice del manual)"]
    d = RAIZ / "manual_despiece" / D["manual"] if D.get("manual") else carpeta(D.get("catalogo", ""))
    if not d or not d.exists(): return [f"- sin carpeta de manual para «{D.get('catalogo')}» (pon \"manual\": \"<carpeta de manual_despiece>\" en el JSON)"]
    claves = set()
    for F in D.get("fichas", {}).values():
        claves |= {w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñ]{5,}", F.get("nombre", ""))[:1]}
    claves |= {w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñ]{5,}", D.get("cabeza", {}).get("titulo", ""))}
    claves -= {"honda", "yamaha", "boxer", "delantero", "trasero", "conjunto"}
    o = []
    for pdf in sorted(d.glob("*.pdf")):
        if "catalogo" in pdf.name.lower(): continue
        try: doc = pymupdf.open(pdf)
        except Exception: continue
        puntos = []
        for i, p in enumerate(doc):
            t = p.get_text().lower()
            n = sum(1 for c in claves if c in t)
            if n: puntos.append((n, i + 1, impresa(limpio(p.get_text()))))
        if not puntos: o.append(f"- `{pdf.name}`: sin texto con esas piezas (¿escaneado?)"); continue
        mejores = sorted(puntos, reverse=True)[:tope]
        o.append(f"- `{pdf.name}` (manual de {tipo(pdf)}{', sin torques de chasis ni motor' if tipo(pdf) == 'propietario' else ''}; {len(doc)} págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) " + ", ".join(f"{i} (impresa {imp}, {n} piezas)" for n, i, imp in sorted(mejores, key=lambda x: x[1])))
    o.append(f"  claves buscadas: {', '.join(sorted(claves))} · para más: `buscar_manual.py {D.get('catalogo')} \"palabra,otra\" --paginas N-M`")
    return o


def huella(lam):
    """Huella del JSON de la lámina: el informe la lleva en su primera línea para saber si quedó viejo."""
    import hashlib
    return hashlib.sha1((AQUI / "datos" / f"{lam}.json").read_bytes()).hexdigest()[:12]


def viejo(lam):
    """True si revision/<lam>.md existe y se hizo con otro JSON (hubo correcciones después)."""
    inf = AQUI / "revision" / f"{lam}.md"
    if not inf.exists(): return False
    primera = inf.read_text(encoding="utf-8").split("\n", 1)[0]
    return huella(lam) not in primera


def escribir(lam, hermana=None):
    D = json.loads((AQUI / "datos" / f"{lam}.json").read_text(encoding="utf-8"))
    hermana = hermana or D.get("hermana")
    H = json.loads((AQUI / "datos" / f"{hermana}.json").read_text(encoding="utf-8")) if hermana else {}
    ya = {clave(t) for t in todos(H) if len(clave(t)) > 25}
    nuevo = lambda t: not hermana or clave(t) not in ya
    F = D.get("fichas", {}); V = D.get("v2", {})
    nom = {p["id"]: F.get(p["n"], {}).get("nombre", p["n"]) for p in D.get("piezas", [])}
    r = subprocess.run([sys.executable, str(AQUI / "validar_esquema.py"), str(AQUI / "datos" / f"{lam}.json")], cwd=RAIZ, capture_output=True)
    val = [l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if "ERROR" in l or l.strip().startswith("aviso:")]
    med = AQUI / "revision" / f"{lam}-medicion.txt"
    mt = med.read_text(encoding="utf-8").splitlines() if med.exists() else []
    heredado = []
    o = [f"# Revisión rápida · {lam}", "",
         f"{D.get('cabeza', {}).get('titulo', '')} · catálogo {D.get('catalogo', '')} fig. {D.get('figura', '')} · página `motor/{lam}.html`"
         + (f" · hermana `{hermana}` (lo heredado sin cambio ya se revisó allá y va resumido)" if hermana else ""),
         "", "Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.", "",
         "## Lo que ya midió la máquina (no lo repitas)", f"- Validador: {len([v for v in val if 'ERROR' in v])} errores, {len([v for v in val if v.startswith('aviso')])} avisos."]
    o += [f"  - {v[:160]}" for v in val[:10]]
    if mt: o += [f"- Medición: {next((l for l in mt if l.startswith('Bloqueantes')), '-')} · {next((l for l in mt if l.startswith('Notas')), '')}"]
    cat = None
    if D.get("catalogo"):
        cat = json.loads((AQUI / "catalogo" / f"{D['catalogo']}.json").read_text(encoding="utf-8"))["figuras"].get(str(D["figura"]))
    if cat:
        o += ["", "## Catálogo (ref · nombre en la lámina · cantidad · código)"]
        o += ["- " + " · ".join(f"{q['ref']} {F.get(q['ref'], {}).get('nombre', q['descripcion'])} ×{q['cantidad']}" for q in cat["partes"])]
    # ronda 8: con el id entre paréntesis, para que la revisora nombre ids que existen
    o += ["", "## Grupos (nombre (id); tornillería aparte)"] + [f"- **{g['nombre']}** [{g.get('id')}]: {', '.join(f'{nom.get(i, i)} ({i})' for i in g['piezas'])}"
                                     + ("".join(f" · {t.get('nombre')} ({', '.join(t.get('ids', []))})" for t in g.get('torn', []) if isinstance(t, dict))) for g in V.get("grupos", [])]
    pasos = [(i, p) for i, p in enumerate(D.get("pasos", []))]
    o += ["", "## Desarme"] + [f"{i + 1}. {plano(p['t'])}" if nuevo(p["t"]) else f"{i + 1}. (heredado)" for i, p in pasos]
    o += ["", "## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)"]
    for n, f in sorted(F.items(), key=lambda x: (len(x[0]), x[0])):
        ap = [k for k, v in f.get("certezaDe", {}).items() if v == "ap"]
        o.append(f"- **{n} · {f.get('nombre')}** · {f.get('decision', '— falta decisión')} · {f.get('dif', '')} · {plano(f.get('cat', ''))}" + (f" · aprox.: {', '.join(ap)}" if ap else ""))
        partes = []
        for c in ("que", "sirve", "porque", "cuando", "compra"):
            t = f.get(c)
            if c == "compra" and not t: continue
            partes.append(f"  - {c}: " + ("— falta" if not t else plano(t) if nuevo(t) else "(heredado)"))
        for c in ("fallas", "sintomas", "arrastra"):
            xs = f.get(c) or []
            un = lambda x: (x if isinstance(x, str) else x[1])
            partes.append(f"  - {c}: " + ("— falta" if not xs else "; ".join(
                (plano(x) if isinstance(x, str) else f"{x[0]}: {plano(x[1])}") if nuevo(un(x)) else "(heredado)" for x in xs)))
        if f.get("conecta") or f.get("efectos"):
            partes.append(f"  - conecta: {', '.join(f.get('conecta', []))} · efectos: {len(f.get('efectos', []))}")
        o += partes
        if hermana and all("(heredado)" in p for p in partes[:4]): heredado.append(n)
    if heredado: o.append(f"- fichas con los textos principales heredados: {', '.join(heredado)}")
    fn = D.get("funciona", {}).get("pasos", [])
    o += ["", "## Cómo funciona"] + [f"{i + 1}. {plano(p['t'])}" if nuevo(p["t"]) else f"{i + 1}. (heredado)" for i, p in enumerate(fn)]
    o += ["", "## Si falla"] + [f"- **{c['t']}**: " + " → ".join(f"{F.get(n, {}).get('nombre', n)}: {plano(t)}" for n, t in c["p"])
                                for c in D.get("cadenas", []) if not hermana or any(nuevo(t) for _n, t in c["p"])]
    o += ["", "## Cuándo"] + [f"- {plano(c['que'])}: {plano(c['cuando'])} · {plano(c.get('fuente', ''))}" for c in D.get("cuando", [])]
    fu = D.get("fuentes", {})
    o += ["", "## Fuentes y certezas"] + [f"- Seguro: {plano(x)}" for x in fu.get("seguro", [])] + [f"- Aprox.: {plano(x)}" for x in fu.get("aproximado", [])]
    o += ["", "## Páginas del manual que aplican (para la mecánica: lee solo estas)"] + paginas_manual(D)
    o += ["", "## Pendientes de la creadora"] + [f"- {plano(x)}" for x in D.get("pendientes", [])] + [""]
    (AQUI / "revision").mkdir(exist_ok=True)
    dest = AQUI / "revision" / f"{lam}.md"
    dest.write_text(f"<!-- json {huella(lam)} -->\n" + "\n".join(o), encoding="utf-8")
    nerr = sum(1 for l in val if "ERROR" in l)
    if nerr: print(f"aviso: el validador tiene {nerr} errores; corrígelos (autocontrol --rapido) antes de lanzar la revisora")
    return f"escrito {dest.relative_to(RAIZ)} ({len(o)} líneas, {len(dest.read_text(encoding='utf-8')) // 4} tokens aprox.)"


if __name__ == "__main__":
    print(escribir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
