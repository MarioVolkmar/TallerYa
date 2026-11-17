"""Busca en los manuales de la moto (taller y propietario) sin volcar páginas: índice corto o frases con su página.
Los PDF solo se leen (pymupdf, texto; nunca imágenes).

  python buscar_manual.py <catalogo|carpeta|pdf> --indice [--cual taller]          secciones: «pág. PDF · impresa · título»
  python buscar_manual.py <catalogo|carpeta|pdf> "pastilla,purg,N·m" [--cual taller] [--paginas 88-112] [--max 12]

- <catalogo>: el de la lámina (crypton-bf24, nmax-bbe4…) → su carpeta en manual_despiece/; también una carpeta o un PDF.
- Cada resultado es una línea: «taller p.92 (6-7): …frase de ±80 caracteres…». «p.» es la página del PDF contando desde 1
  (la que se pasa a Read con pages o a pymupdf como índice p−1); entre paréntesis, el número impreso en la hoja.
- Un resultado por página y palabra, como máximo --max (12) en total: afina con --paginas tras mirar el índice.
"""
import pathlib, re, sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
IMPRESA = re.compile(r"(?<![\d.,])(\d{1,2})\s?[-\u00ad\u2010-\u2013]\s?(\d{1,3})(?![\d.,])")
CATALOGO = re.compile(r"catalog|partes|parts|repuestos|despiece", re.I)


def carpeta(catalogo):
    """Ronda 9: la carpeta de manual_despiece/ de la moto, sin lista fija: la que tiene el PDF fuente del catálogo, o un
    catálogo cuyo nombre trae el código de la versión («bbe4», «glh125sh», «ct100»…)."""
    md = RAIZ / "manual_despiece"
    try:
        import json
        C = json.loads((AQUI / "catalogo" / f"{catalogo}.json").read_text(encoding="utf-8"))
        fuente = pathlib.Path(str(C.get("fuente", "")).split(" (")[0]).name
        x = next(md.rglob(fuente), None) if fuente else None
        if x: return x.parent
    except (OSError, ValueError):
        pass
    cod = catalogo.split("-")[-1].lower()
    x = next((p for p in md.rglob("*.pdf") if cod in p.name.lower() and CATALOGO.search(p.name)), None)
    return x.parent if x else None


def tipo(pdf):
    """«servicio» (taller: torques y medidas) o «propietario» (mantenimiento básico); por el nombre y, si no dice, por las 3 primeras páginas."""
    n = pdf.name.lower()
    if re.search(r"taller|servicio|service|workshop|mantenimiento", n): return "servicio"
    if re.search(r"propietario|usuario|owner|guia|guía", n): return "propietario"
    try:
        import pymupdf
        d = pymupdf.open(str(pdf)); t = " ".join(d[i].get_text() for i in range(min(3, len(d)))).lower()
        if re.search(r"manual de (servicio|taller)|service manual|workshop", t): return "servicio"
        if re.search(r"propietario|owner|usuario", t): return "propietario"
    except Exception:
        pass
    return "¿?"


def pdfs(donde, cual):
    p = pathlib.Path(re.sub(r"^/([a-z])/", r"\1:/", donde))   # /c/... de Git Bash → C:/...
    if not p.exists(): p = carpeta(donde) or RAIZ / "manual_despiece" / donde
    lista = [p] if p.is_file() else sorted(x for x in p.glob("*.pdf") if not CATALOGO.search(x.name))
    return [x for x in lista if not cual or cual in x.name.lower() or {"taller": "servicio"}.get(cual, cual) == tipo(x)]


def limpio(t):
    return re.sub(r"\s+", " ", re.sub(r"[▲▼∙]+", " ", t)).strip()


def impresa(t):
    m = IMPRESA.search(t[:200]) or IMPRESA.search(t[-200:])
    return f"{m.group(1)}-{m.group(2)}" if m else "-"


def titulo(t):
    """Título de sección: lo que sigue al número impreso en la cabecera («6-4 RUEDA DELANTERA Y DISCO DE FRENO»)."""
    m = re.search(r"\d{1,2}\s?[-\u00ad]\s?\d{1,3}\s+((?:[A-ZÁÉÍÓÚÑ]{2,}[ ,/]*){2,8})", t[:300])
    return m.group(1).strip(" ,/") if m else ""


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 1
    import pymupdf
    cual = a[a.index("--cual") + 1].lower() if "--cual" in a else ""
    tope = int(a[a.index("--max") + 1]) if "--max" in a else 12
    rango = None
    if "--paginas" in a:
        x, _, y = a[a.index("--paginas") + 1].partition("-"); rango = (int(x), int(y or x))
    lista = pdfs(a[0], cual)
    if not lista: print(f"sin manual para «{a[0]}» (no hay carpeta en manual_despiece/ con su catálogo; pasa la carpeta o la ruta del PDF)"); return 1
    claves = [] if "--indice" in a or len(a) < 2 or a[1].startswith("--") else [w.strip().lower() for w in a[1].split(",") if w.strip()]
    n = 0
    for pdf in lista:
        d = pymupdf.open(str(pdf)); corto = tipo(pdf) + (" (sin torques de chasis ni motor: van «manual de servicio» o a pendientes)" if tipo(pdf) == "propietario" and not claves else "")
        if not claves:
            ultimo = None; filas = []
            for i, pg in enumerate(d):
                t = limpio(pg.get_text()); ti = " ".join(titulo(t).split()[:5])
                clave = " ".join(ti.split()[:2])   # una línea por sección, no por subtítulo
                if ti and clave != ultimo: filas.append(f"p.{i + 1} ({impresa(t)}) {ti[:40]}"); ultimo = clave
            print(f"{corto} ({len(d)} págs., {pdf.name}): " + (" · ".join(filas) if filas else "sin títulos de sección (¿escaneado?); busca palabras"))
            continue
        for i, pg in enumerate(d):
            if rango and not rango[0] <= i + 1 <= rango[1]: continue
            t = limpio(pg.get_text()); tl = t.lower()
            for w in claves:
                j = tl.find(w)
                if j < 0: continue
                print(f"{corto} p.{i + 1} ({impresa(t)}): …{t[max(0, j - 80):j + 80]}…"); n += 1
                if n >= tope: print(f"(tope de {tope}: afina con --paginas o más palabras)"); return 0
    if claves and not n: print("sin resultados (¿manual escaneado? mira garaje/intervalos y las notas del auditor)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
