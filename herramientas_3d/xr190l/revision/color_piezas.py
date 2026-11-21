# Uso: python color_piezas.py render.png id.png foto.jpg parches_fijos.json
# Color medio de cada pieza en el render (máscara por ID, cuartil medio de luminancia) vs parche de la foto.
import sys, json, importlib.util
import numpy as np
from PIL import Image
src = open(__file__.replace("color_piezas.py", "medir.py"), encoding="utf-8").read().replace("\nmain()\n", "\n"); m = {}; exec(src, m)
rend, idp, foto, pj = sys.argv[1:5]
R = np.asarray(Image.open(rend).convert("RGBA")).astype(float); I = np.asarray(Image.open(idp).convert("RGBA")).astype(int)
F = np.asarray(Image.open(foto).convert("RGB")).astype(float)
ids = json.load(open(sys.argv[5] if len(sys.argv) > 5 else "ids.json"))
enc = lambda v: [round(255 * ((x/255) * 12.92 if x/255 <= 0.0031308 else 1.055 * (x/255) ** (1/2.4) - 0.055)) for x in v]
ids = {k: enc(v) for k, v in ids.items()}
print("ej", list(ids.items())[:2]); P = json.load(open(pj))
mapa = {"aletas": ["pintura.aletas"], "guardabarros_del": ["pintura.guardabarros_del"], "mascara": ["pintura.mascara"], "colin": ["pintura.colin"],
        "tapa_lateral": ["blanco.tapa_lateral"], "tanque": ["plastico.tanque"], "asiento": ["asiento.asiento"], "chasis": ["chasis.chasis"],
        "basculante": ["metal.basculante"], "rines": ["metal.aro_del", "metal.aro_tras"], "motor": ["titanio.motor"], "escape": ["oscuro.escape"]}
ok = 0; filas = []
for k, (cx, cy, r) in P.items():
    msk = np.zeros(I.shape[:2], bool)
    for n in mapa[k]:
        cand = [kk for kk in ids if kk.split(".")[1] == n.split(".")[1]]
        if not cand: continue
        c = ids[cand[0]]; msk |= (np.abs(I[..., :3] - c).sum(2) < 12) & (I[..., 3] > 250)
    px = R[..., :3][msk & (R[..., 3] > 250)]
    if len(px) < 30: print(f"  {k:16s} sin pixeles visibles ({len(px)})"); continue
    lum = px @ [0.3, 0.59, 0.11]; q1, q3 = np.percentile(lum, [25, 75]); sel = px[(lum >= q1) & (lum <= q3)]
    cr = sel.mean(0); cf = F[cy-r:cy+r, cx-r:cx+r].reshape(-1, 3).mean(0)
    d = m["de2000"](m["srgb_lab"](cf), m["srgb_lab"](cr)); ok += d <= 5
    print(f"  {k:16s} dE={d:5.1f} foto={cf.astype(int).tolist()} render={cr.astype(int).tolist()} px={len(px)}")
print("color_pct", round(100 * ok / len(P), 1), f"({ok}/{len(P)})")
