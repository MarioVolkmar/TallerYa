# Uso: python zonas_iou.py foto.jpg caps/vN  -> píxeles de diferencia por zona (sin la sombra del piso) y cuánto subiría el IoU si se arreglara cada una
import sys, numpy as np
from PIL import Image
foto, pref = sys.argv[1:3]
d = np.load(pref + "_alin.npz"); mf, m2 = d["mf"].copy(), d["m2"]
fa = np.asarray(Image.open(foto).convert("RGB")).astype(int)
ys = np.where(mf.any(1))[0]; y1 = ys.max(); y0 = ys.min(); alto = y1 - y0
xs = np.where(mf.any(0))[0]; x0, x1 = xs.min(), xs.max(); ancho = x1 - x0
gris = (fa.min(2) > 120) & (fa.max(2) - fa.min(2) < 14)
yy = np.arange(mf.shape[0])[:, None] * np.ones(mf.shape[1], bool)
mf &= ~(gris & (yy > y1 - 0.06 * alto))
H, W = mf.shape; Y, X = np.mgrid[:H, :W]; u = (X - x0) / ancho; v = (Y - y0) / alto
zonas = {"espejos (arriba)": v < 0.18, "rueda trasera": (u < 0.36) & (v > 0.52), "rueda delantera": (u > 0.66) & (v > 0.48)}
zonas["resto"] = ~np.any(list(zonas.values()), 0)
I, U = (mf & m2).sum(), (mf | m2).sum(); print(f"IoU={I/U:.4f}")
for k, z in zonas.items():
    sf, sr = (mf & ~m2 & z).sum(), (m2 & ~mf & z).sum()
    print(f"  {k:18s} solo_foto={sf:6d} solo_render={sr:6d} IoU_si_perfecta={(I+sf)/(U-sr):.4f}")
