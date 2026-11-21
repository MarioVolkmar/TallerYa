"""Utilidades comunes del método nuevo para la XR 190L: leer el GLB de Tripo, pasarlo a coordenadas de la moto
(x adelante, y arriba, z a la izquierda, metros, piso en y = 0) y un rasterizador mínimo en numpy para renders."""
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN = RAIZ / "privado/tripo/xr190l/modelo-3d-xr190l.glb"
TRABAJO = RAIZ / "privado/tripo/xr190l"
LARGO_REAL = 2.13 * 1.353 / 1.398  # m: escala tal que la distancia entre ejes sea la real (1.353 mm, ficha Honda)

TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}


def leer_glb(ruta):
    b = Path(ruta).read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + n])
    base = 20 + n + 8

    def acc(i):
        a = g["accessors"][i]
        bv = g["bufferViews"][a["bufferView"]]
        T = TIPOS[a["componentType"]]
        c = COMP[a["type"]]
        arr = np.frombuffer(b, T, count=a["count"] * c, offset=base + bv.get("byteOffset", 0) + a.get("byteOffset", 0))
        return arr.reshape(-1, c) if c > 1 else arr

    pr = g["meshes"][0]["primitives"][0]
    return acc(pr["attributes"]["POSITION"]).astype(np.float64), acc(pr["indices"]).astype(np.int64).reshape(-1, 3)


def a_moto(V, adelante=-1):
    """Tripo: x lateral, y arriba, z largo (adelante = signo de z del frente). Devuelve x adelante, y arriba, z lateral."""
    largo = V[:, 2].max() - V[:, 2].min()
    s = LARGO_REAL / largo
    W = np.stack([adelante * V[:, 2], V[:, 1], -adelante * V[:, 0]], 1) * s  # (mano derecha: z = x_tripo girado)
    W[:, 0] -= (W[:, 0].max() + W[:, 0].min()) / 2
    W[:, 1] -= W[:, 1].min()
    return W


def normales_cara(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-12)[:, None], a / 2


def vista(V, az, el):
    """Gira para la cámara: az alrededor de y (0 = lado izquierdo, z hacia la cámara), el hacia abajo."""
    a, e = np.radians(az), np.radians(el)
    Ry = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return V @ (Rx @ Ry).T, Rx @ Ry


def render(V, F, colores, ruta, az=0, el=0, ancho=900, fondo=(245, 245, 245), alfa=None):
    """Raster ortográfico con sombreado Lambert por cara. colores: (nF,3) 0-255. alfa: (nF,) opcional (rayos X)."""
    P, R = vista(V, az, el)
    nC, _ = normales_cara(V, F)
    nC = nC @ R.T
    luz = np.array([-0.35, 0.55, 0.75]); luz /= np.linalg.norm(luz)
    sh = 0.35 + 0.65 * np.abs(nC @ luz)
    lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    esc = (ancho - 40) / (hi[0] - lo[0])
    alto = int((hi[1] - lo[1]) * esc) + 40
    X = (P[:, 0] - lo[0]) * esc + 20
    Y = alto - ((P[:, 1] - lo[1]) * esc + 20)
    Z = P[:, 2]
    img = np.zeros((alto, ancho, 3)); img[:] = fondo
    zb = np.full((alto, ancho), -1e9)
    col = np.asarray(colores, float) * sh[:, None]
    orden = np.argsort(Z[F].mean(1)) if alfa is not None else np.arange(len(F))
    for f in orden:
        i, j, k = F[f]
        xs, ys = np.array([X[i], X[j], X[k]]), np.array([Y[i], Y[j], Y[k]])
        x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, ancho - 1)
        y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, alto - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not m.any():
            continue
        z = w0 * Z[i] + w1 * Z[j] + w2 * Z[k]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        if alfa is None:
            m &= z > sub
            sub[m] = z[m]
            img[y0:y1 + 1, x0:x1 + 1][m] = col[f]
        else:
            a = alfa[f]
            img[y0:y1 + 1, x0:x1 + 1][m] = img[y0:y1 + 1, x0:x1 + 1][m] * (1 - a) + col[f] * a
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(ruta)


def render_rapido(V, F, colores, ruta, az=0, el=0, ancho=900, fondo=(245, 245, 245), alfa=None, devolver=False):
    """Igual que render, pero por muestras: cada cara se dibuja como puntos baricéntricos (más si es grande).
    alfa (nF,): las caras con alfa < 1 se mezclan encima de las opacas (rayos X aproximado)."""
    P, R = vista(V, az, el)
    nC, _ = normales_cara(V, F)
    nC = nC @ R.T
    luz = np.array([-0.35, 0.55, 0.75]); luz /= np.linalg.norm(luz)
    sh = 0.35 + 0.65 * np.abs(nC @ luz)
    lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    esc = (ancho - 40) / (hi[0] - lo[0])
    alto = int((hi[1] - lo[1]) * esc) + 40
    Q = np.stack([(P[:, 0] - lo[0]) * esc + 20, alto - ((P[:, 1] - lo[1]) * esc + 20), P[:, 2]], 1)
    T = Q[F]
    area = 0.5 * np.abs(np.cross(T[:, 1, :2] - T[:, 0, :2], T[:, 2, :2] - T[:, 0, :2]))
    col = np.asarray(colores, float) * sh[:, None]
    img = np.zeros((alto, ancho, 3)); img[:] = fondo
    zb = np.full(alto * ancho, -1e9)
    capas = [(np.ones(len(F), bool) if alfa is None else alfa >= 0.999)]
    if alfa is not None:
        capas.append(alfa < 0.999)
    for ci, sel in enumerate(capas):
        pts, cs, ids = [], [], []
        for nivel, m in ((6, area <= 4), (14, (area > 4) & (area <= 40)), (30, area > 40)):
            m = m & sel
            if not m.any():
                continue
            u = np.linspace(0, 1, nivel + 1)
            a, b = np.meshgrid(u, u)
            k = (a + b) <= 1
            w = np.stack([a[k], b[k], 1 - a[k] - b[k]], 1)
            idx = np.nonzero(m)[0]
            # (caras muy grandes: más muestras por lotes para no dejar huecos)
            p = np.einsum("sk,fkd->fsd", w, T[idx])
            pts.append(p.reshape(-1, 3)); ids.append(np.repeat(idx, len(w)))
        if not pts:
            continue
        p = np.concatenate(pts); ids = np.concatenate(ids)
        xi = np.clip(p[:, 0].astype(int), 0, ancho - 1); yi = np.clip(p[:, 1].astype(int), 0, alto - 1)
        lin = yi * ancho + xi
        if ci == 0:
            o = np.argsort(p[:, 2])
            lin, ids, z = lin[o], ids[o], p[o, 2]
            flat = img.reshape(-1, 3)
            flat[lin] = col[ids]  # (la última escritura gana: la más cercana)
            np.maximum.at(zb, lin, z)
        else:
            o = np.argsort(p[:, 2])
            lin, ids, z = lin[o], ids[o], p[o, 2]
            # una sola mezcla por píxel y cara transparente más cercana delante del z-buffer
            delante = z > zb[lin]
            lin, ids = lin[delante], ids[delante]
            flat = img.reshape(-1, 3)
            u, primero = np.unique(lin[::-1], return_index=True)
            ids_u = ids[::-1][primero]
            a = alfa[ids_u][:, None]
            flat[u] = flat[u] * (1 - a) + col[ids_u] * a
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if devolver:
        return out
    out.save(ruta)
