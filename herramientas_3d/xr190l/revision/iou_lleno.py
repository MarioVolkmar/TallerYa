# IoU con la sombra del piso de la foto quitada y, aparte, con huecos rellenos (rayos fuera). Usa pref_alin.npz y la foto.
import sys, numpy as np
from PIL import Image, ImageDraw
foto, pref = sys.argv[1:3]
d = np.load(pref + "_alin.npz"); mf, m2 = d["mf"].copy(), d["m2"]
fa = np.asarray(Image.open(foto).convert("RGB")).astype(int)
ys = np.where(mf.any(1))[0]; y1 = ys.max(); alto = y1 - ys.min()
gris = (fa.min(2) > 120) & (fa.max(2) - fa.min(2) < 14)
yy = np.arange(mf.shape[0])[:, None] * np.ones(mf.shape[1], bool)
mf &= ~(gris & (yy > y1 - 0.06 * alto))
def iou(a, b): return (a & b).sum() / (a | b).sum()
def lleno(m):
    im = Image.fromarray(np.pad(m, 1).astype(np.uint8) * 255).convert("RGB"); ImageDraw.floodfill(im, (0, 0), (128, 0, 0))
    return (np.asarray(im)[..., 0] != 128)[1:-1, 1:-1]
print(f"IoU_sin_sombra={iou(mf, m2):.4f} IoU_relleno={iou(lleno(mf), lleno(m2)):.4f}")
