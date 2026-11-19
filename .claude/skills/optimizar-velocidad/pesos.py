"""Peso real en producción (bruto / gzip -9 / brotli q11) de lo que pidió una página, desde el JSON de medir_chrome.py.
runserver entrega los estáticos SIN comprimir: por eso los KB «por red» del servidor de desarrollo no sirven para el
presupuesto. Este script busca cada /static/… con los finders de Django y lo comprime como lo haría WhiteNoise.
Uso: venv/Scripts/python.exe .claude/skills/optimizar-velocidad/pesos.py medicion.json [--top 10]
"""
import argparse, gzip, json, os, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.contrib.staticfiles import finders

try:
    import brotli
except ImportError:
    brotli = None
TOPE = {"js": 250, "css": 60, "json": 40, "svg": 60, "glb": 500, "img": 150}  # KB comprimidos (br) por tipo, presupuesto

def tipo(r):
    ext = r.split("?")[0].rsplit(".", 1)[-1].lower()
    return {"mjs": "js", "png": "img", "jpg": "img", "jpeg": "img", "webp": "img", "avif": "img"}.get(ext, ext if ext in TOPE else "otro")

ap = argparse.ArgumentParser(); ap.add_argument("json"); ap.add_argument("--top", type=int, default=8); a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
for med in json.load(open(a.json, encoding="utf-8")):
    if med.get("carga") != "fría":
        continue
    suma, filas = defaultdict(lambda: [0, 0, 0, 0]), []
    for ruta, bruto in med.get("recursos") or []:
        r = ruta.split("?")[0]
        f = finders.find(r[len("/static/"):]) if r.startswith("/static/") else None
        if f:
            datos = Path(f).read_bytes()
            gz = len(gzip.compress(datos, 9)); br = len(brotli.compress(datos, quality=11)) if brotli else gz
        elif tipo(r) in ("img", "glb"):  # ya comprimidos (o de media/): pesan lo mismo por red
            gz = br = bruto
        else:  # dinámico (JSON, SVG de vistas): GZipMiddleware nivel 6 ≈ bruto × 0,13-0,2; se usa 0,15 si no hay archivo
            gz = br = int(bruto * 0.15)
        s = suma[tipo(r)]; s[0] += 1; s[1] += bruto; s[2] += gz; s[3] += br
        filas.append((br, r[-60:], bruto, gz, "" if f else " (estimado)"))
    print(f"\n{med['url']} ({med['ancho']} px)  tipo: n · bruto / gzip / br KB  [tope br]")
    for t, (n, b, g, r) in sorted(suma.items(), key=lambda x: -x[1][3]):
        tope = TOPE.get(t); marca = " ✗" if tope and r / 1024 > tope else ""
        print(f"  {t:5} {n:3} · {b/1024:6.0f} / {g/1024:5.0f} / {r/1024:5.0f}  [{tope or '-'}]{marca}")
    print("  más pesados (br):")
    for br, r, b, g, e in sorted(filas, reverse=True)[:a.top]:
        print(f"    {br/1024:5.0f} KB br ({b/1024:.0f} bruto)  {r}{e}")
