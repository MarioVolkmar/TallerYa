"""Auditoría de líneas de TallerYa: qué tiene y qué le falta cada línea del catálogo.

Uso (desde la raíz del proyecto):
    venv/Scripts/python.exe .claude/skills/agregar-moto/auditar.py            # tabla Markdown de todas las líneas
    venv/Scripts/python.exe .claude/skills/agregar-moto/auditar.py nmax       # solo las que contienen "nmax"
    venv/Scripts/python.exe .claude/skills/agregar-moto/auditar.py --faltas   # solo las líneas a las que les falta algo

Solo lee: base local (líneas, despieces, partes) y archivos del repo. No escribe nada.
Columnas:
  Int.     intervalos: tareas exactas/total en garaje/intervalos/<slug>.json (~ = alguna aproximada; — = no hay)
  Fallas   fallas «del modelo»/total en garaje/fallas_frecuentes/<slug>.json
  Desp.    despieces activos en la base · láminas · partes (— = ninguno)
  Trad.    % de partes con nombre visible en español (nombre_es o catálogo ya en español); Tareas = tareas del plan con pieza enlazada / tareas de la línea
  Mapa     mapa en garaje/despiece_mapas/ (sí/no)
  Lám.     láminas del esquema pedagógico (informes_noche/piloto-esquema/motor/datos/*.json con "intervalos": <slug>)
  3D       GLB = carrocería realista (moto3d/glb.js); rasgos = rasgos propios en moto3d/rasgos.js; fam = familia genérica
  Puntos   0-7, para ordenar qué completar primero (más bajo = más le falta)
"""
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import django  # noqa: E402

django.setup()

from django.db.models import Count  # noqa: E402

from garaje.intervalos import slug_linea  # noqa: E402
from garaje.models import Despiece, LineaMoto, ParteDespiece, TareaMantenimiento  # noqa: E402

GARAJE = RAIZ / "garaje"
DATOS_LAMINAS = RAIZ / "informes_noche/piloto-esquema/motor/datos"
JS3D = GARAJE / "static/garaje/js/moto3d"
INGLES = re.compile(r"(ASSY|BOLT|SCREW|WASHER|COVER|GEAR|PLATE|SPRING|NUT|SEAL|CAP|BEARING|SHAFT|LEVER|HOSE|PIPE|"
                    r"BRACKET|CABLE|PLUG|CLIP|GASKET|HOLDER|STAY|GUIDE|BAND|CASE|WHEEL|TIRE|TUBE)", re.I)


def _json(ruta):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def intervalos(slug):
    d = _json(GARAJE / "intervalos" / f"{slug}.json")
    if not d:
        return "—", 0
    grupos = [d.get("tareas") or {}] + [v.get("tareas") or {} for v in d.get("versiones", [])]  # Gixxer: versiones
    todas = [t for g in grupos for t in g.values() if isinstance(t, dict)]
    aprox = sum(1 for t in todas if t.get("aproximado"))
    total = len(todas)
    texto = f"{total - aprox}/{total}" + (" ~" if aprox else "")
    return texto, (1 if aprox == 0 else 0.5)


def fallas(slug):
    d = _json(GARAJE / "fallas_frecuentes" / f"{slug}.json")
    if not d:
        return "—", 0
    lista = d.get("fallas", [])
    modelo = sum(1 for f in lista if f.get("alcance") == "modelo")
    return f"{modelo}/{len(lista)}", (1 if modelo else 0.5)


def mapas_por_linea():
    salida = {}
    for ruta in (GARAJE / "despiece_mapas").glob("*.json"):
        d = _json(ruta) or {}
        salida.setdefault((d.get("marca", ""), d.get("linea", "")), []).append(ruta.stem)
    return salida


def laminas_por_slug():
    cuenta = {}
    if not DATOS_LAMINAS.exists():
        return cuenta
    for ruta in DATOS_LAMINAS.glob("*.json"):
        n = ruta.name
        if n.endswith((".antes.json", ".esqueleto.json", "-v1.json")) or "-estilo" in n:
            continue
        d = _json(ruta)
        slug = d.get("intervalos") if isinstance(d, dict) else None
        if slug:
            cuenta[slug] = cuenta.get(slug, 0) + 1
    return cuenta


def patrones_3d():
    rasgos, glb = [], []
    try:
        for m in re.finditer(r"^\s*\[/(.+?)/i,", (JS3D / "rasgos.js").read_text(encoding="utf-8"), re.M):
            rasgos.append(re.compile(m.group(1), re.I))
        bloque = re.search(r"const MODELOS = \{(.*?)\};", (JS3D / "glb.js").read_text(encoding="utf-8"), re.S)
        glb = [re.compile(k, re.I) for k in re.findall(r"(\w+)\s*:", bloque.group(1))] if bloque else []
    except OSError:
        pass
    return rasgos, glb


def tres_d(nombre, rasgos, glb):
    if any(p.search(nombre) for p in glb):
        return "GLB", 1
    if any(p.search(nombre) for p in rasgos):
        return "rasgos", 0.5
    return "fam", 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_faltas = "--faltas" in sys.argv
    filtro = args[0].lower() if args else ""
    mapas, lams = mapas_por_linea(), laminas_por_slug()
    rasgos, glb = patrones_3d()
    filas = []
    for linea in LineaMoto.objects.filter(activo=True).select_related("marca"):
        nombre = f"{linea.marca.nombre} {linea.nombre}"
        if filtro and filtro not in nombre.lower():
            continue
        slug = slug_linea(linea)
        i_txt, i_pt = intervalos(slug)
        f_txt, f_pt = fallas(slug)
        desp = Despiece.objects.filter(linea=linea, activo=True).annotate(n=Count("laminas", distinct=True))
        partes = ParteDespiece.objects.filter(lamina__despiece__in=desp)
        n_partes = partes.count()
        if desp:
            d_txt = f"{len(desp)} · {sum(d.n for d in desp)} · {n_partes}"
            # Sin traducir = sin nombre_es y con la descripción del catálogo en inglés (los catálogos en español no la necesitan)
            sin = sum(1 for d in partes.filter(nombre_es="").values_list("descripcion", flat=True) if INGLES.search(d))
            trad = (n_partes - sin) * 100 // max(n_partes, 1)
            con_tarea = set(partes.filter(tarea__isnull=False).values_list("tarea__clave", flat=True))
            aplican = _tareas_de(linea)
            t_txt = f"{trad}% · {len(con_tarea & aplican)}/{len(aplican)}"
            d_pt = 1 + (1 if trad >= 90 and len(con_tarea & aplican) >= len(aplican) - 1 else 0.5)
        else:
            d_txt, t_txt, d_pt = "—", "—", 0
        mapa = "sí" if mapas.get((linea.marca.nombre, linea.nombre)) else "no"
        n_lam = lams.get(slug, 0)
        l_pt = 1 if n_lam >= 3 else (0.5 if n_lam else 0)
        t3, t_pt = tres_d(nombre, rasgos, glb)
        puntos = 1 + i_pt + f_pt + d_pt + l_pt + t_pt  # 1 = ficha en el catálogo
        filas.append((puntos, nombre, slug, i_txt, f_txt, d_txt, t_txt, mapa, n_lam or "—", t3))
    filas.sort(key=lambda f: (f[0], f[1]))
    print("| Línea | Int. | Fallas | Desp. (n · lám · partes) | Trad. · Tareas | Mapa | Lám. | 3D | Puntos |")
    print("|---|---|---|---|---|---|---|---|---|")
    for p, nombre, slug, i, f, d, t, m, lam, t3 in filas:
        if solo_faltas and p >= 7:
            continue
        print(f"| {nombre} | {i} | {f} | {d} | {t} | {m} | {lam} | {t3} | {p:g} |")
    print(f"\n{len(filas)} líneas · puntos: ficha 1 + intervalos 1 + fallas 1 + despiece 2 + láminas 1 + 3D 1 = 7")


def _tareas_de(linea):
    """Claves de las tareas del plan que aplican a la línea (TareaMantenimiento.aplica_a, el mismo criterio del plan)."""
    specs = linea.specs()
    return {t.clave for t in TareaMantenimiento.objects.all() if t.aplica_a(specs)}


if __name__ == "__main__":
    main()
