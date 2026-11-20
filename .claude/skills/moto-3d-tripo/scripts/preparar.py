# Uso: preparar.py T <distancia entre ejes en metros, de la ficha de la moto> [giro]
#   giro: grados alrededor de y para dejar la moto con el eje largo en x y el frente en +x (Tripo a veces la entrega
#   a lo largo de z: XTZ 150 con el frente en +z -> giro 90). Sin giro, si el eje largo es z, avisa y se detiene.
# 1) color por vertice desde la textura, 2) soldar por posicion, 3) medir ejes de rueda, 4) llevar a coordenadas de la moto
import sys, numpy as np, os, json
from PIL import Image
d = sys.argv[1]
EJES = float(sys.argv[2])
P = np.load(f'{d}/pos.npy'); N = np.load(f'{d}/nor.npy'); I = np.load(f'{d}/idx.npy')
GIRO = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
ext = P.max(0) - P.min(0)
if GIRO == 0 and ext[2] > ext[0] * 1.3:
    sys.exit(f'El eje largo es z (caja {ext.round(3)}): pasar giro 90 si el frente (manubrio) esta en +z, o 270 si esta en -z')
if GIRO:
    a = np.radians(GIRO); c, s_ = np.cos(a), np.sin(a)
    R = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]], np.float32)  # x' = x cos + z sen ; z' = -x sen + z cos
    P = P @ R.T; N = N @ R.T
CON_COLOR = os.path.exists(f'{d}/uv.npy') and os.path.exists(f'{d}/basecolor.jpg')
uv = np.load(f'{d}/uv.npy') if CON_COLOR else np.zeros((len(P), 2), np.float32)
tex = np.asarray(Image.open(f'{d}/basecolor.jpg').convert('RGB')).astype(np.float32) if CON_COLOR else np.full((2, 2, 3), 150, np.float32)
h, w = tex.shape[:2]
# muestreo bilineal (convencion glTF: v hacia abajo)
x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001); y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
col = (tex[y0, x0] * (1-fx) * (1-fy) + tex[y0, x0+1] * fx * (1-fy) + tex[y0+1, x0] * (1-fx) * fy + tex[y0+1, x0+1] * fx * fy)
# soldar por posicion exacta
_, primero, inv = np.unique(P, axis=0, return_index=True, return_inverse=True)
inv = inv.ravel()
nv = len(primero)
cnt = np.bincount(inv, minlength=nv).astype(np.float32)[:, None]
Pw = P[primero]
Nw = np.zeros((nv, 3), np.float32); np.add.at(Nw, inv, N); Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-9)
Cw = np.zeros((nv, 3), np.float32); np.add.at(Cw, inv, col); Cw /= cnt
Iw = inv[I].astype(np.uint32)
ok = (Iw[:, 0] != Iw[:, 1]) & (Iw[:, 1] != Iw[:, 2]) & (Iw[:, 0] != Iw[:, 2]); Iw = Iw[ok]
print('vertices', len(P), '->', nv, 'caras', len(I), '->', len(Iw))
# ejes: huellas de contacto con el piso
piso = Pw[Pw[:, 1] < 0.012]
xd = piso[piso[:, 0] > 0, 0]; xt = piso[piso[:, 0] < 0, 0]
cxd, cxt = (xd.min() + xd.max()) / 2, (xt.min() + xt.max()) / 2
def radio(cx):
    m = (np.abs(Pw[:, 0] - cx) < 0.01) & (np.abs(Pw[:, 2]) < 0.03) & (Pw[:, 1] < 0.4)
    return Pw[m, 1].max() / 2
rd, rt = radio(cxd), radio(cxt)
esc = EJES / (cxd - cxt)
print('ejes x', cxd, cxt, 'radios', rd, rt, 'escala', esc, '-> radios m', rd*esc, rt*esc)
cx = (cxd + cxt) / 2
Pm = (Pw - np.array([cx, 0, 0], np.float32)) * esc
print('caja moto', Pm.min(0).round(3), Pm.max(0).round(3))
Pm.astype(np.float32).tofile(f'{d}/w_pos.bin'); Nw.tofile(f'{d}/w_nor.bin'); (Cw / 255).astype(np.float32).tofile(f'{d}/w_col.bin'); Iw.tofile(f'{d}/w_idx.bin')
json.dump({'nv': int(nv), 'nt': int(len(Iw)), 'rd': float(rd*esc), 'rt': float(rt*esc), 'con_color': bool(CON_COLOR), 'ejes': EJES,
           'xd': float((cxd - cx) * esc), 'xt': float((cxt - cx) * esc)}, open(f'{d}/w.json', 'w'))
