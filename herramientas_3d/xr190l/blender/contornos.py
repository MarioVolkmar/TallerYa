"""Paso 2 (python del sistema): malla limpia de Blender → despiece grueso (reglas de segmentar.py) y contornos LISOS
de los paneles en la vista lateral (tapa lateral, aletas, colín), para que Blender corte la malla por esas curvas.
Uso: python -I contornos.py PREP.npz SALIDA_DIR"""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib import path as mpath
from matplotlib import pyplot as plt
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun import a_moto, normales_cara  # noqa: E402
import segmentar as sg  # noqa: E402

PANELES = ("tapa_lateral", "aletas", "colin")  # (orden de prioridad al reetiquetar)
PASO = 0.003  # m por celda de la vista lateral
X0, Y0, NX, NY = -1.2, 0.2, 800, 400


def contorno(W, F, lab, pieza, nC):
    """Silueta lateral de las caras de la pieza que miran hacia afuera, cerrada, sin huecos y suavizada (σ 9 mm)."""
    im = Image.new("L", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    m = (lab == pieza) & (np.abs(nC[:, 2]) > 0.25)
    for tri in W[F[m]][:, :, :2]:
        d.polygon([((x - X0) / PASO, (y - Y0) / PASO) for x, y in tri], fill=255)
    a = np.asarray(im) > 0
    a = ndimage.binary_closing(a, iterations=4)
    a = ndimage.binary_opening(a, iterations=3)
    a = ndimage.binary_fill_holes(a)
    k, n = ndimage.label(a)
    if n == 0:
        return []
    a = k == (np.argmax(np.bincount(k.ravel())[1:]) + 1)
    s = ndimage.gaussian_filter(a.astype(float), 3.0)
    cs = plt.contour(np.arange(NX) * PASO + X0, np.arange(NY) * PASO + Y0, s, levels=[0.5])
    lazos = [p for p in cs.allsegs[0] if len(p) > 20]
    plt.close("all")
    lazo = max(lazos, key=len)
    # (un punto cada ~1 cm: tramos rectos para bisect, curva lisa al ojo)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(lazo, axis=0), axis=1))]
    t = np.linspace(0, L[-1], max(12, int(L[-1] / 0.01)), endpoint=False)
    return np.stack([np.interp(t, L, lazo[:, 0]), np.interp(t, L, lazo[:, 1])], 1)


if __name__ == "__main__":
    prep, sal = Path(sys.argv[1]), Path(sys.argv[2])
    d = np.load(prep)
    W = a_moto(d["V"], 1)
    W[:, 2] *= -1  # (Tripo la dejó espejada: cadena a la izquierda, escape a la derecha, como la XR real)
    F = d["F"][:, [0, 2, 1]]
    lab, rd, fork = sg.segmentar(W, F)
    nC, _ = normales_cara(W, F)
    polis = {p: contorno(W, F, lab, p, nC) for p in PANELES}
    np.savez_compressed(sal / "grueso.npz", W=W, F=F, lab=lab.astype(str))
    json.dump({k: np.round(v, 4).tolist() for k, v in polis.items()}, open(sal / "contornos.json", "w"))
    u, c = np.unique(lab.astype(str), return_counts=True)
    print(dict(zip(u, c.tolist())))
    print({k: len(v) for k, v in polis.items()})
    # vista de control de los contornos sobre la silueta
    fig, ax = plt.subplots(figsize=(9, 4.5))
    C = W[F].mean(1)
    ax.scatter(C[:, 0], C[:, 1], s=0.1, c="0.7")
    for k, v in polis.items():
        ax.plot(*np.vstack([v, v[:1]]).T, lw=1.5, label=k)
    ax.set_aspect("equal"); ax.legend(); fig.savefig(sal / "contornos.png", dpi=90); plt.close(fig)
