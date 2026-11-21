"""Render de control del despiece: colores falsos por pieza (o colores finales con --final), vistas lateral y 3/4.
Uso: python -I ver_despiece.py SALIDA_PREFIJO [--final] [--ancho 700] [--lado izq]"""
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from comun import TRABAJO, render_rapido  # noqa: E402


def falso(nombre):
    h = zlib.crc32(nombre.encode())
    return np.array([60 + h % 190, 60 + (h >> 8) % 190, 60 + (h >> 16) % 190])


if __name__ == "__main__":
    pref = sys.argv[1]
    ancho = int(sys.argv[sys.argv.index("--ancho") + 1]) if "--ancho" in sys.argv else 700
    d = np.load(TRABAJO / ("final.npz" if "--final" in sys.argv else "despiece.npz"), allow_pickle=True)
    W, F, lab = d["W"], d["F"], d["lab"]
    if "--final" in sys.argv:
        col = d["col"]
    else:
        col = np.array([falso(n) for n in lab])
    alfa = d["alfa"] if "--rayos" in sys.argv else None
    vistas = [(0, 0), (-35, 12)] if "--lado" not in sys.argv else [(180, 0), (215, 12)]
    imgs = [render_rapido(W, F, col, None, az=a, el=e, ancho=ancho, alfa=alfa, devolver=True) for a, e in vistas]
    alto = sum(i.height for i in imgs)
    hoja = Image.new("RGB", (ancho, alto), (255, 255, 255))
    yy = 0
    for i in imgs:
        hoja.paste(i, (0, yy)); yy += i.height
    hoja.save(pref + ".png")
    if "--final" not in sys.argv:
        # leyenda en texto: centro de cada pieza
        for n in sorted(set(lab)):
            m = lab == n
            c = W[F[m]].reshape(-1, 3).mean(0)
            print(n, int(m.sum()), c.round(2), falso(n))
