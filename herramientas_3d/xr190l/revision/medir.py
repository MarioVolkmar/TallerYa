# Uso: python medir.py foto.jpg render.png salida_prefijo [parches.json]
# IoU de silueta (render alineado a la foto por escala+traslado) y ΔE2000 por parche.
import sys, json
import numpy as np
from PIL import Image, ImageDraw

def mascara_foto(a, umbral=28):
    return np.abs(255 - a.astype(int)).max(2) > umbral

def srgb_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2); Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm**7 / (Cm**7 + 25**7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    if C1p * C2p == 0: hm = hs
    elif abs(h1p - h2p) <= 180: hm = hs / 2
    else: hm = (hs + 360) / 2 if hs < 360 else (hs - 360) / 2
    T = 1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm)) + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63))
    dth = 30 * np.exp(-(((hm - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cmp**7 / (Cmp**7 + 25**7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return float(np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh)))

def bbox(m):
    ys, xs = np.where(m); return xs.min(), ys.min(), xs.max(), ys.max()

def main():
    foto, rend, pref = sys.argv[1:4]
    F = Image.open(foto).convert("RGB"); fa = np.asarray(F)
    mf = mascara_foto(fa)
    R = Image.open(rend).convert("RGBA"); ra = np.asarray(R)
    mr = ra[..., 3] > 230
    fx0, fy0, fx1, fy1 = bbox(mf); rx0, ry0, rx1, ry1 = bbox(mr)
    s0 = (fx1 - fx0) / (rx1 - rx0)
    W, H = F.size
    def colocar(s, dx, dy, img, modo):
        w, h = int(round(img.size[0] * s)), int(round(img.size[1] * s))
        im = img.resize((w, h), Image.LANCZOS if modo == "RGBA" else Image.NEAREST)
        lienzo = Image.new(modo, (W, H), (0, 0, 0, 0) if modo == "RGBA" else 0)
        ox = int(round(fx0 - rx0 * s + dx)); oy = int(round(fy1 - ry1 * s + dy))
        lienzo.paste(im, (ox, oy)); return lienzo
    mrI = Image.fromarray((mr * 255).astype(np.uint8))
    k = 0.3
    mfS = np.asarray(Image.fromarray((mf * 255).astype(np.uint8)).resize((int(W * k), int(H * k)), Image.BILINEAR)) > 127
    mrS = mrI.resize((int(mrI.size[0] * k), int(mrI.size[1] * k)), Image.BILINEAR)
    def iouS(s, dx, dy):
        w, h = int(round(mrS.size[0] * s)), int(round(mrS.size[1] * s))
        im = mrS.resize((w, h), Image.BILINEAR); L = Image.new("L", mfS.shape[::-1], 0)
        L.paste(im, (int(round((fx0 - rx0 * s + dx) * k)), int(round((fy1 - ry1 * s + dy) * k))))
        m2 = np.asarray(L) > 127; return (m2 & mfS).sum() / (m2 | mfS).sum()
    mejor = (-1, None)
    for s in s0 * np.linspace(0.90, 1.10, 41):
        for dx in range(-40, 41, 5):
            for dy in range(-40, 41, 5):
                v = iouS(s, dx, dy)
                if v > mejor[0]: mejor = (v, (s, dx, dy))
    s, dx, dy = mejor[1]
    mejor = (-1, None)
    for ss in s * np.linspace(0.99, 1.01, 5):
        for ddx in range(-4, 5, 2):
            for ddy in range(-4, 5, 2):
                m2 = np.asarray(colocar(ss, dx + ddx, dy + ddy, mrI, "L")) > 127
                iou = (m2 & mf).sum() / (m2 | mf).sum()
                if iou > mejor[0]: mejor = (iou, (ss, dx + ddx, dy + ddy))
    iou, (s, dx, dy) = mejor
    RA = colocar(s, dx, dy, R, "RGBA")
    fondo = Image.new("RGBA", (W, H), (255, 255, 255, 255)); fondo.alpha_composite(RA)
    rr = np.asarray(fondo.convert("RGB"))
    m2 = np.asarray(colocar(s, dx, dy, mrI, "L")) > 127
    print(f"IoU={iou:.4f} escala={s:.4f} dx={dx} dy={dy} solo_foto={(mf & ~m2).sum()} solo_render={(m2 & ~mf).sum()}")
    # mapa de diferencias de silueta
    dif = np.full((H, W, 3), 255, np.uint8); dif[mf & m2] = (190, 190, 190); dif[mf & ~m2] = (0, 90, 255); dif[m2 & ~mf] = (255, 60, 0)
    res = {"iou": round(float(iou), 4), "parches": {}}
    lienzos = [F.copy(), Image.fromarray(rr)]
    if len(sys.argv) > 4:
        P = json.load(open(sys.argv[4], encoding="utf-8"))
        for nombre, (cx, cy, r) in P.items():
            zf = fa[cy - r:cy + r, cx - r:cx + r].reshape(-1, 3).astype(float)
            zr = rr[cy - r:cy + r, cx - r:cx + r].reshape(-1, 3).astype(float)
            lf, lr = srgb_lab(zf.mean(0)), srgb_lab(zr.mean(0))
            d = de2000(lf, lr)
            res["parches"][nombre] = {"dE": round(d, 1), "foto": [int(x) for x in zf.mean(0)], "render": [int(x) for x in zr.mean(0)]}
            for L in lienzos:
                ImageDraw.Draw(L).rectangle([cx - r, cy - r, cx + r, cy + r], outline=(0, 200, 0), width=2)
                ImageDraw.Draw(L).text((cx + r + 2, cy - r), nombre[:10], fill=(0, 120, 0))
        ok = [k for k, v in res["parches"].items() if v["dE"] <= 5]
        res["color_pct"] = round(100 * len(ok) / len(P), 1)
        for k, v in res["parches"].items(): print(f"  {k:18s} dE={v['dE']:5.1f} foto={v['foto']} render={v['render']}")
        print("color_pct", res["color_pct"])
    json.dump(res, open(pref + ".json", "w"), indent=1)
    x0, y0, x1, y1 = bbox(mf | m2); x0, y0 = max(0, x0 - 10), max(0, y0 - 10)
    caja = (x0, y0, min(W, x1 + 10), min(H, y1 + 10))
    tiras = [L.crop(caja) for L in lienzos] + [Image.fromarray(dif).crop(caja)]
    w = sum(t.size[0] for t in tiras); comp = Image.new("RGB", (w, tiras[0].size[1]), "white"); x = 0
    for t in tiras: comp.paste(t, (x, 0)); x += t.size[0]
    comp.thumbnail((900, 900)); comp.save(pref + "_comp.jpg", quality=82)
    print("caja", caja)
    a, b = lienzos[0].crop(caja), lienzos[1].crop(caja)
    pila = Image.new("RGB", (a.size[0] * 2, a.size[1]), "white"); pila.paste(a, (0, 0)); pila.paste(b, (a.size[0], 0))
    pila.thumbnail((1400, 1400)); pila.save(pref + "_parches.jpg", quality=80)
    np.savez_compressed(pref + "_alin.npz", rr=rr, m2=m2, mf=mf)

main()
