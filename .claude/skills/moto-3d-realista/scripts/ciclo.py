"""Una iteración completa en un comando: generar → IoU (torno) → revisión estricta → hoja comparativa con la versión
anterior. Imprime solo el resumen (≈ 1 min de máquina, sin navegador).

Uso:  python -I ciclo.py motos/<id>.json modelos_3d_local/<moto> garaje/static/garaje/modelos/<id>.glb
      [--anterior ruta/v_anterior.glb] [--umbral 0.85]
Lee las vistas de <moto>/vistas.json (preparar_vistas.py). Deja en <moto>/revision/: revision.json,
hoja_revision.jpg (foto | render | líneas) y comparacion.jpg (anterior frente a actual, 6 cámaras fijas).
Aprueba si: IoU ≥ umbral en cada vista Y todos los rasgos cumplidos (en ≥ 2 vistas ortogonales).
"""
import sys
import json
import time
import os
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # (consola de Windows en cp1252)
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8"}

AQUI = Path(__file__).parent


def correr(*args):
    r = subprocess.run([sys.executable, "-I", *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENTORNO)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(r.returncode)
    return r.stdout


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    ficha, carpeta, glb = Path(argv[0]), Path(argv[1]), Path(argv[2])
    t0 = time.perf_counter()
    vistas = [v["carpeta"] for v in json.loads((carpeta / "vistas.json").read_text(encoding="utf-8"))["vistas"].values()]
    print(correr(AQUI / "generar.py", ficha, glb).strip())
    salida_iou = correr(AQUI / "iou.py", glb, carpeta, *vistas, "--torno", "--umbral", opt("--umbral", "0.85"))
    print(salida_iou.strip().splitlines()[-1])
    rev = carpeta / "revision"
    salida = correr(AQUI / "revisar.py", glb, carpeta, *vistas, "--ficha", ficha, "--salida", rev)
    print("\n".join(l for l in salida.splitlines() if l.startswith(("PROMEDIO", "  NO cumple"))))
    if opt("--anterior"):
        correr(AQUI / "comparar.py", rev / "comparacion.jpg", f"anterior={opt('--anterior')}", f"actual={glb}")
    r = json.loads((rev / "revision.json").read_text(encoding="utf-8")); i = json.loads((carpeta / "iou.json").read_text())
    hechos, total = map(int, r["rasgos_cumplidos"].split("/"))
    ok = i["aprobado"] and hechos == total
    print(f"{'APROBADO' if ok else 'NO aprobado'}: IoU {i['iou_promedio']}, rasgos {r['rasgos_cumplidos']}, "
          f"bordes {r['precision_bordes']}/{r['cobertura_bordes']} — {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
