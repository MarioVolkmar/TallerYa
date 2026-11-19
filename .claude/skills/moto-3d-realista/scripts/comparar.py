"""Hoja comparativa de versiones del GLB sin navegador: mismas cámaras fijas para todas (frontal, lateral, trasera, 3/4
delantera, 3/4 trasera y desde arriba), un renglón por GLB.

Uso:  python -I comparar.py salida.jpg v3=ruta/a.glb v4=ruta/b.glb [--alto 240]
Render propio de revisar.py (pintor por triángulo, colores de glb.COLORES, luz fija): sirve para revisar formas,
proporciones y filos en segundos. Para la apariencia con los materiales del visor, la captura del visor
(scripts/capturas_visor.js).
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageDraw
import glb
import iou as I
import revisar as R

# (giro, cabeceo): giro 0 = lateral derecha (convención de iou.py), -90 = trasera, -270 = frontal
CAMARAS = {"frontal": (-270, -4), "lateral": (0, -3), "trasera": (-90, -4), "3/4 del.": (35, -12),
           "3/4 tras.": (-215, -12), "arriba": (0, -88)}


def proyector(giro, cab, W, H):
    Rm = I.rotacion(giro, cab, 0); dist = 9.0; centro = np.array([0, 0.55, 0])

    def proy(X):
        q = (np.asarray(X, float) - centro) @ Rm.T; z = q[..., 2] + dist
        f = 0.62 * H * dist  # (1 m de moto ≈ 0,62 del alto de la hoja)
        return q[..., 0] / z * f + W / 2, -q[..., 1] / z * f + H / 2, z
    return proy


def main(argv):
    alto = int(argv[argv.index("--alto") + 1]) if "--alto" in argv else 240
    salida = argv[0]
    modelos = [a.split("=", 1) for a in argv[1:] if "=" in a]
    W = int(alto * 1.25)
    filas = []
    for etiqueta, ruta in modelos:
        ims = []
        for nombre, (giro, cab) in CAMARAS.items():
            col, _, _, _ = R.render(ruta, proyector(giro, cab, W, alto), (alto, W))
            im = Image.fromarray(col.astype(np.uint8)); d = ImageDraw.Draw(im)
            d.text((6, 4), f"{etiqueta} · {nombre}", fill=(20, 20, 20))
            ims.append(im)
        fila = Image.new("RGB", (len(ims) * (W + 6), alto), "white")
        for i, im in enumerate(ims):
            fila.paste(im, (i * (W + 6), 0))
        filas.append(fila)
    hoja = Image.new("RGB", (filas[0].size[0], len(filas) * (alto + 6)), "white")
    for j, f in enumerate(filas):
        hoja.paste(f, (0, j * (alto + 6)))
    hoja.save(salida, quality=88)
    print(f"{salida}: {len(modelos)} versiones × {len(CAMARAS)} vistas")


if __name__ == "__main__":
    main(sys.argv[1:])
