# Uso: python parches.py foto.jpg prefijo parches.json  (usa prefijo_alin.npz de medir.py)
import sys, json, importlib.util
import numpy as np
from PIL import Image, ImageDraw
spec = importlib.util.spec_from_file_location("m", __file__.replace("parches.py", "medir.py"))
src = open(spec.origin, encoding="utf-8").read().replace("\nmain()\n", "\n")
m = {}; exec(compile(src, "medir", "exec"), m)
foto, pref, pj = sys.argv[1:4]
fa = np.asarray(Image.open(foto).convert("RGB")); d = np.load(pref + "_alin.npz"); rr = d["rr"]
P = json.load(open(pj, encoding="utf-8")); res = {}
A, B = Image.fromarray(fa.copy()), Image.fromarray(rr.copy())
def clase_ok(c, cl):
    R, G, B = c; mx, mn = max(c), min(c)
    return {"rojo": R > 140 and G < 80 and B < 90, "blanco": mn > 185 and mx - mn < 20, "negro": mx < 90,
            "plata": 140 < mn and mx < 235 and mx - mn < 20}[cl]
def buscar(x0, y0, x1, y1, cl, r):
    mejor = None
    for cy in range(y0 + r, y1 - r, 2):
        for cx in range(x0 + r, x1 - r, 2):
            z = fa[cy-r:cy+r, cx-r:cx+r].reshape(-1, 3).astype(float)
            if not clase_ok(z.mean(0), cl): continue
            v = z.std(0).sum() + (z.min(0).min() < 1) * 99
            if mejor is None or v < mejor[0]: mejor = (v, cx, cy)
    return (mejor[1], mejor[2]) if mejor else (None, None)
for k, val in list(P.items()):
    if len(val) == 6:
        cx, cy = buscar(*val)
        if cx is None: print("SIN ZONA", k); del P[k]; continue
        P[k] = [cx, cy, val[5]]
json.dump(P, open(pj.replace(".json", "_fijos.json"), "w"))
for k, (cx, cy, r) in P.items():
    zf = fa[cy-r:cy+r, cx-r:cx+r].reshape(-1, 3).astype(float).mean(0); zr = rr[cy-r:cy+r, cx-r:cx+r].reshape(-1, 3).astype(float).mean(0)
    de = m["de2000"](m["srgb_lab"](zf), m["srgb_lab"](zr)); res[k] = round(de, 1)
    print(f"  {k:18s} dE={de:5.1f} foto={zf.astype(int).tolist()} render={zr.astype(int).tolist()}")
    for L in (A, B):
        g = ImageDraw.Draw(L); g.rectangle([cx-r-1, cy-r-1, cx+r+1, cy+r+1], outline=(0, 255, 0), width=2); g.text((cx+r+3, cy-r), k[:8], fill=(0, 140, 0))
ok = sum(v <= 5 for v in res.values()); print("color_pct", round(100*ok/len(res), 1), f"({ok}/{len(res)})")
json.dump(res, open(pref + "_dE.json", "w"))
ys, xs = np.where(d["mf"]); caja = (xs.min()-5, ys.min()-5, xs.max()+5, ys.max()+5)
a, b = A.crop(caja), B.crop(caja); pila = Image.new("RGB", (a.size[0], a.size[1]*2), "white"); pila.paste(a, (0, 0)); pila.paste(b, (0, a.size[1]))
pila.thumbnail((900, 1200)); pila.save(pref + "_parches.jpg", quality=80)
