"""Juego de fotos por vista de una moto, en un paso: baja los cuadros de un visor 360° (opcional), arma las carpetas
v360_KK con foto y máscara y escribe vistas.json (qué cuadro es cada vista, si es ortogonal y su escala).

Uso:  python -I preparar_vistas.py modelos_3d_local/<moto> [--patron "https://.../360view/2026_x_1_{n}.jpg"]
      [--cuadros 36] [--lateral 5] [--fuente yamaha_jp_360] [--entre-ejes 1.34]
Sin --patron usa los cuadros ya bajados en fotos/<fuente>/c{n}.jpg. Con el número del cuadro de la lateral derecha
(--lateral, la vista de frente a la derecha) y 36 cuadros cada 10° calcula los demás: lateral izquierda (+18),
trasera (+9), frontal (+27), 3/4 delantera (-3) y 3/4 trasera (+22). Las fotos solo se bajan (urllib) y se leen:
nada de lo bajado se ejecuta. Quedan en modelos_3d_local/ (ignorada por git) con su FUENTE.txt.
"""
import sys
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import perfil

VISTAS = {"lateral_der": 0, "lateral_izq": 18, "trasera": 9, "frontal": 27, "tres_cuartos_del": -3, "tres_cuartos_tras": 22}
ORTOGONAL = {"lateral_der", "lateral_izq", "trasera", "frontal"}


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    carpeta = Path(argv[0]); fuente = opt("--fuente", "yamaha_jp_360"); n = int(opt("--cuadros", 36))
    lat = int(opt("--lateral", 5)); wb = float(opt("--entre-ejes", 1.34))
    dir_f = carpeta / "fotos" / fuente; dir_f.mkdir(parents=True, exist_ok=True)
    if opt("--patron"):
        for i in range(1, n + 1):
            destino = dir_f / f"c{i}.jpg"
            if not destino.exists():
                req = urllib.request.Request(opt("--patron").format(n=i), headers={"User-Agent": "Mozilla/5.0"})
                destino.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        (dir_f / "FUENTE.txt").write_text(f"Visor 360°: {opt('--patron')} (cuadros 1..{n}). Solo referencia de silueta.\n",
                                          encoding="utf-8")
    info = {}
    for nombre, d in VISTAS.items():
        k = (lat + d - 1) % n + 1
        v = carpeta / f"v360_{k:02d}"; v.mkdir(exist_ok=True)
        if not (v / "foto.jpg").exists():
            shutil.copy(dir_f / f"c{k}.jpg", v / "foto.jpg")
        info[nombre] = {"carpeta": v.name, "cuadro": k, "ortogonal": nombre in ORTOGONAL}
    faltan = [x["carpeta"] for x in info.values() if not (carpeta / x["carpeta"] / "mascara.png").exists()]
    if faltan:
        subprocess.run([sys.executable, "-I", str(Path(__file__).parent / "mascara_fondo_blanco.py"), str(carpeta), *faltan], check=True)
    for nombre in ("lateral_der", "lateral_izq"):
        m = np.asarray(Image.open(carpeta / info[nombre]["carpeta"] / "mascara.png").convert("L")) > 127
        _, k, *_ = perfil.calibrar(m, wb, "derecha" if nombre == "lateral_der" else "izquierda")
        info[nombre]["px_por_m"] = round(1 / k, 1)
    (carpeta / "vistas.json").write_text(json.dumps({"fuente": fuente, "entre_ejes": wb, "vistas": info}, indent=1,
                                                    ensure_ascii=False), encoding="utf-8")
    print(" ".join(x["carpeta"] for x in info.values()))


if __name__ == "__main__":
    main(sys.argv[1:])
