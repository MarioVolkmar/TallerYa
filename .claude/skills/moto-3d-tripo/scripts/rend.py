# Render de depuracion: muestrea puntos en los triangulos y los salpica con z-buffer; con cuadricula en metros
import numpy as np
from PIL import Image, ImageDraw
def cargar(d, pref='s'):
    P = np.fromfile(f'{d}/{pref}_pos.bin', np.float32).reshape(-1, 3); N = np.fromfile(f'{d}/{pref}_nor.bin', np.float32).reshape(-1, 3)
    C = np.fromfile(f'{d}/{pref}_col.bin', np.float32).reshape(-1, 3); I = np.fromfile(f'{d}/{pref}_idx.bin', np.uint32).reshape(-1, 3)
    return P, N, C, I
def muestras(P, I, paso):
    a, b, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    k = np.maximum(1, np.ceil(area / (paso * paso) * 2.5)).astype(int)
    f = np.repeat(np.arange(len(I)), k)
    rng = np.random.default_rng(1)
    u = rng.random(len(f)); v = rng.random(len(f)); m = u + v > 1; u[m] = 1 - u[m]; v[m] = 1 - v[m]
    return f, np.stack([1 - u - v, u, v], 1)
# vista: (eje pantalla x, signo), (eje pantalla y), (eje profundidad, signo)
VISTAS = {'der': (0, 1, 2, 1), 'izq': (0, -1, 2, -1), 'arriba': (0, 1, 1, 1), 'frente': (2, -1, 0, 1), 'atras': (2, 1, 0, -1), 'abajo': (0, 1, 1, -1)}
def vista(P, N, I, colcara, nombre, esc=600, caja=None, rejilla=True, colvert=None):
    ax, sx, az, sz = VISTAS[nombre]; ay = 2 if az == 1 else 1
    f, bar = muestras(P, I, 1 / esc)
    tri = I[f]
    Q = (P[tri] * bar[:, :, None]).sum(1); Nn = (N[tri] * bar[:, :, None]).sum(1)
    Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
    col = colcara[f] if colvert is None else (colvert[tri] * bar[:, :, None]).sum(1)
    mn, mx = (P.min(0), P.max(0)) if caja is None else (np.array(caja[0], float), np.array(caja[1], float))
    dentro = np.all((Q >= mn) & (Q <= mx), axis=1); Q, Nn, col = Q[dentro], Nn[dentro], col[dentro]
    W = int((mx[ax] - mn[ax]) * esc) + 1; H = int((mx[ay] - mn[ay]) * esc) + 1
    px = (Q[:, ax] - mn[ax]) * esc if sx > 0 else (mx[ax] - Q[:, ax]) * esc
    py = (mx[ay] - Q[:, ay]) * esc
    if az == 1 and sz > 0: py = (Q[:, ay] - mn[ay]) * esc
    L = np.zeros(3); L[az] = sz * 0.75; L[ay if az != 1 else 0] = 0.5; L[ax] += 0.35; L /= np.linalg.norm(L)
    luz = np.clip(0.35 + 0.75 * np.clip(Nn @ L, 0, 1), 0, 1.15)[:, None]
    orden = np.argsort(Q[:, az] * sz)
    img = np.full((H, W, 3), 250, np.uint8)
    img[np.clip(py[orden].astype(int), 0, H-1), np.clip(px[orden].astype(int), 0, W-1)] = np.clip(col[orden] * luz[orden] * 255, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    if rejilla:
        dr = ImageDraw.Draw(im)
        for v in np.arange(np.ceil(mn[ax] * 10) / 10, mx[ax], 0.1):
            x = (v - mn[ax]) * esc if sx > 0 else (mx[ax] - v) * esc
            dr.line([(x, 0), (x, 6)], fill=(255, 0, 0)); dr.text((x + 1, 6), f'{v:.1f}', fill=(255, 0, 0))
        for v in np.arange(np.ceil(mn[ay] * 10) / 10, mx[ay], 0.1):
            y = (mx[ay] - v) * esc if not (az == 1 and sz > 0) else (v - mn[ay]) * esc
            dr.line([(0, y), (6, y)], fill=(255, 0, 0)); dr.text((8, y - 5), f'{v:.1f}', fill=(255, 0, 0))
    return im
def lamina(ims, salida, cols=2):
    filas = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    W = max(sum(i.width for i in f) for f in filas); H = sum(max(i.height for i in f) for f in filas)
    out = Image.new('RGB', (W, H), (250, 250, 250)); y = 0
    for f in filas:
        x = 0
        for i in f: out.paste(i, (x, y)); x += i.width
        y += max(i.height for i in f)
    out.save(salida); print('guardado', salida, out.size)
