# Formas basicas para modelar piezas internas: revolucion, tubo, extrusion con bisel; normales con pliegue.
import numpy as np


def _base(eje):
    a = np.asarray(eje, float)
    a = a / np.linalg.norm(a)
    t = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, t)
    u /= np.linalg.norm(u)
    return a, u, np.cross(a, u)


def revolucion(perfil, base, eje, n=20):
    """perfil: [(radio, avance)] a lo largo del eje desde base."""
    a, u, v = _base(eje)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    P, I = [], []
    for r, t in perfil:
        P.append(np.asarray(base, float) + a * t + r * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v))
    P = np.concatenate(P)
    for k in range(len(perfil) - 1):
        if perfil[k][0] == 0 and perfil[k + 1][0] == 0:
            continue
        for j in range(n):
            j2 = (j + 1) % n
            p0, p1, q0, q1 = k * n + j, k * n + j2, (k + 1) * n + j, (k + 1) * n + j2
            if perfil[k][0] > 0:
                I.append((p0, p1, q1))
            if perfil[k + 1][0] > 0:
                I.append((p0, q1, q0))
    return P, np.array(I)


def tubo(puntos, r, n=10, cerrado=False):
    pts = np.asarray(puntos, float)
    m = len(pts)
    tang = np.zeros_like(pts)
    for i in range(m):
        a = pts[(i - 1) % m] if (cerrado or i > 0) else pts[i]
        b = pts[(i + 1) % m] if (cerrado or i < m - 1) else pts[i]
        tang[i] = b - a
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    _, u, _ = _base(tang[0])
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    P = []
    for i in range(m):
        u = u - tang[i] * (u @ tang[i])
        u /= np.linalg.norm(u)
        v = np.cross(tang[i], u)
        P.append(pts[i] + r * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v))
    P = np.concatenate(P)
    I = []
    for i in range(m if cerrado else m - 1):
        i2 = (i + 1) % m
        for j in range(n):
            j2 = (j + 1) % n
            I += [(i * n + j, i * n + j2, i2 * n + j2), (i * n + j, i2 * n + j2, i2 * n + j)]
    if not cerrado:
        c0, c1 = len(P), len(P) + 1
        P = np.concatenate([P, pts[[0, -1]]])
        for j in range(n):
            j2 = (j + 1) % n
            I += [(c0, j2, j), (c1, (m - 1) * n + j, (m - 1) * n + j2)]
    return P, np.array(I)


def rect_redondo(w, h, r, n=5):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n)
            pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return np.array(pts)


def suave(pol, vueltas=2):
    """Redondea un poligono cerrado cortando esquinas (Chaikin)."""
    p = np.asarray(pol, float)
    for _ in range(vueltas):
        q = np.roll(p, -1, axis=0)
        p = np.stack([p * 0.75 + q * 0.25, p * 0.25 + q * 0.75], 1).reshape(-1, 2)
    return p


def extrusion(pol, z0, z1, bisel=0.0):
    """Poligono (x, y) en sentido antihorario, estrellado respecto a su centro; se extruye en z con bisel en los cantos."""
    pol = np.asarray(pol, float)
    c = pol.mean(0)
    n = len(pol)
    chico = pol if bisel <= 0 else c + (pol - c) * (1 - bisel / np.maximum(np.linalg.norm(pol - c, axis=1, keepdims=True), 1e-9))
    anillos = [(chico, z0), (pol, z0 + bisel), (pol, z1 - bisel), (chico, z1)] if bisel > 0 else [(pol, z0), (pol, z1)]
    P = np.concatenate([np.column_stack([a, np.full(n, zz)]) for a, zz in anillos])
    I = []
    for k in range(len(anillos) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            I += [(k * n + j, k * n + j2, (k + 1) * n + j2), (k * n + j, (k + 1) * n + j2, (k + 1) * n + j)]
    c0, c1 = len(P), len(P) + 1
    P = np.concatenate([P, [[c[0], c[1], z0], [c[0], c[1], z1]]])
    ult = (len(anillos) - 1) * n
    for j in range(n):
        j2 = (j + 1) % n
        I += [(c0, j2, j), (c1, ult + j, ult + j2)]
    return P, np.array(I)


def mover(forma, d=(0, 0, 0), ejes=None):
    """ejes: columnas = a donde van x, y, z locales (para extruir a lo largo de otro eje)."""
    P, I = forma
    if ejes is not None:
        M = np.asarray(ejes, float)
        P = P @ M.T
        if np.linalg.det(M) < 0:
            I = I[:, [0, 2, 1]]
    return P + np.asarray(d, float), I


EJE_X = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]   # extrusion a lo largo de x
EJE_Y = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]   # extrusion a lo largo de y


def unir(*formas):
    P, I, n = [], [], 0
    for p, i in formas:
        P.append(p)
        I.append(np.asarray(i) + n)
        n += len(p)
    return np.concatenate(P), np.concatenate(I)


def con_normales(forma, pliegue=38):
    """Devuelve (P, N, I) con normales suaves salvo donde las caras forman un angulo mayor al pliegue."""
    P, I = forma
    _, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    W = inv.ravel()[I]
    fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
    area = np.linalg.norm(fn, axis=1)
    ok = area > 1e-14
    I, W, fn, area = I[ok], W[ok], fn[ok], area[ok]
    un = fn / area[:, None]
    cos = np.cos(np.radians(pliegue))
    caras_de = {}
    for f, tri in enumerate(W.tolist()):
        for v in tri:
            caras_de.setdefault(v, []).append(f)
    N = np.zeros((len(I), 3, 3))
    for v, fs in caras_de.items():
        fs = np.array(fs)
        m = (un[fs] @ un[fs].T) > cos
        nn = m.astype(float) @ fn[fs]
        for k, f in enumerate(fs):
            N[f, np.where(W[f] == v)[0]] = nn[k]
    N = N.reshape(-1, 3)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    Pc = P[I].reshape(-1, 3)
    clave = np.round(np.column_stack([Pc / 1e-6, N * 100])).astype(np.int64)
    _, prim, inv2 = np.unique(clave, axis=0, return_index=True, return_inverse=True)
    return Pc[prim], N[prim], inv2.ravel().reshape(-1, 3)
