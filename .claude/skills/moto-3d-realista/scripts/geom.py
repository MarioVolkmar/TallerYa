"""Primitivas de geometría para armar motos (solo numpy).

Convención del visor de TallerYa (moto3d.js): metros, Y arriba, frente hacia +X,
Z a lo ancho (Z+ = lado izquierdo del piloto), suelo en y=0, eje delantero en
x=+wb/2 y trasero en x=-wb/2.

Primitivas (todas devuelven Malla):
- loft(estaciones, eje="x"): secciones de superelipse interpoladas suavemente.
- barrido(camino, secciones): una sección de superelipse que recorre una polilínea.
- torno(perfil, centro, eje="z"): perfil (r, a) girado (llantas, rines, discos).
- radios(...): brazos de rin (rectos o en Y).
- caja(...): bloque redondeado.
"""
import math
import numpy as np


class Malla:
    def __init__(self, v=None, f=None):
        self.v = np.zeros((0, 3)) if v is None else np.asarray(v, float)
        self.f = np.zeros((0, 3), np.int64) if f is None else np.asarray(f, np.int64)

    def __add__(self, o):
        return Malla(np.vstack([self.v, o.v]), np.vstack([self.f, o.f + len(self.v)]))

    def espejo_z(self):
        v = self.v.copy(); v[:, 2] *= -1
        return Malla(v, self.f[:, ::-1].copy())

    def mover(self, d):
        return Malla(self.v + np.asarray(d, float), self.f)

    def girar(self, eje, grados, centro=(0, 0, 0)):
        a = math.radians(grados); c, s = math.cos(a), math.sin(a)
        i, j = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[eje]
        v = self.v - centro; w = v.copy()
        w[:, i] = c * v[:, i] - s * v[:, j]
        w[:, j] = s * v[:, i] + c * v[:, j]
        return Malla(w + centro, self.f)

    def normales(self):
        """Normales suaves ponderadas por área (los bordes duros se logran duplicando vértices)."""
        n = np.zeros_like(self.v)
        a, b, c = (self.v[self.f[:, k]] for k in range(3))
        fn = np.cross(b - a, c - a)
        for k in range(3):
            np.add.at(n, self.f[:, k], fn)
        l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
        return n / l


def unir(mallas):
    m = Malla()
    for x in mallas:
        m = m + x
    return m


# ---------- interpolación suave (Catmull-Rom centrípeta simplificada) ----------
def _suave(ts, vals, muestras):
    """Interpola vals(ts) con Hermite monótono (sin sobrepasos) en 'muestras'."""
    ts = np.asarray(ts, float); vals = np.asarray(vals, float); muestras = np.asarray(muestras, float)
    if len(ts) == 1:
        return np.full_like(muestras, vals[0])
    h = np.diff(ts); d = np.diff(vals) / h
    m = np.zeros_like(vals)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(vals) - 1):
        m[k] = 0 if d[k - 1] * d[k] <= 0 else 2 / (1 / d[k - 1] + 1 / d[k])
    idx = np.clip(np.searchsorted(ts, muestras) - 1, 0, len(ts) - 2)
    t = (muestras - ts[idx]) / h[idx]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    return h00 * vals[idx] + h10 * h[idx] * m[idx] + h01 * vals[idx + 1] + h11 * h[idx] * m[idx + 1]


def _superelipse(nseg, a0, a1, w, n, kt=1.0, c=0.0, nb=None):
    """Contorno cerrado: eje 1 entre a0 y a1, eje 2 con semiancho w (kt = factor del ancho arriba)."""
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    co, si = np.cos(th), np.sin(th)
    nb = n if nb is None else nb
    ex = np.where(si >= 0, 2 / n, 2 / nb)
    am, ah = (a0 + a1) / 2, (a1 - a0) / 2
    ancho = np.where(si > 0, w * (1 + (kt - 1) * si), w)
    b = c + ancho * np.sign(co) * np.abs(co) ** ex
    a = am + ah * np.sign(si) * np.abs(si) ** ex
    return a, b


def _tapas(m_anillos, nseg, v, f, tapa_ini=True, tapa_fin=True):
    """Tapas planas con vértices propios (borde duro)."""
    v = list(v); f = list(f)
    for k, activa in ((0, tapa_ini), (m_anillos - 1, tapa_fin)):
        if not activa:
            continue
        anillo = np.array(v[k * nseg:(k + 1) * nseg])
        base = len(v)
        v.extend(anillo); v.append(anillo.mean(0))
        cen = base + nseg
        for i in range(nseg):
            a, b = base + i, base + (i + 1) % nseg
            f.append((cen, b, a) if k == 0 else (cen, a, b))
    return v, f


def _anillos_a_malla(anillos, tapas=(True, True)):
    m, nseg = len(anillos), len(anillos[0])
    v = [p for r in anillos for p in r]
    f = []
    for k in range(m - 1):
        for i in range(nseg):
            a = k * nseg + i; b = k * nseg + (i + 1) % nseg
            c = a + nseg; d = b + nseg
            f += [(a, c, b), (b, c, d)]
    v, f = _tapas(m, nseg, v, f, *tapas)
    return Malla(np.array(v), np.array(f))


def _plantilla(media, mezcla=None, media2=None):
    """Media sección [(u, v, duro)] de abajo-centro (0,-1) a arriba-centro (0,1), u en [0,1].
    Devuelve el contorno completo (simétrico) con los vértices de arista viva duplicados."""
    M = np.asarray([p[:2] for p in media], float)
    if media2 is not None and mezcla:
        M = (1 - mezcla) * M + mezcla * np.asarray([p[:2] for p in media2], float)
    duro = [bool(p[2]) if len(p) > 2 else False for p in media]
    puntos = []
    for i, (u, v) in enumerate(M):  # lado +u, de abajo hacia arriba
        puntos.append((u, v))
        if duro[i] and i > 0:  # (también el extremo de arriba: lomo o punta en V)
            puntos.append((u, v))
    for i in range(len(M) - 2, 0, -1):  # lado -u, de arriba hacia abajo
        u, v = M[i]
        puntos.append((-u, v))
        if duro[i]:
            puntos.append((-u, v))
    if duro[0]:  # quilla abajo: se cierra con una copia propia
        puntos.append(tuple(M[0]))
    return np.asarray(puntos)


def loft(estaciones, eje="x", nseg=28, pasos=24, tapas=(True, True), seccion=None, seccion2=None):
    """Estaciones (dicts). eje x: {x, ys, yt, w, n?, kt?, zc?, nb?}; eje y: {y, x0, x1, w, n?, kt?, zc?}.
    Los parámetros se interpolan suavemente entre estaciones."""
    t_clave, a0_clave, a1_clave = ("x", "ys", "yt") if eje == "x" else ("y", "x0", "x1")
    est = sorted(estaciones, key=lambda e: e[t_clave])
    ts = [e[t_clave] for e in est]
    S = np.linspace(ts[0], ts[-1], pasos)
    S = np.unique(np.concatenate([S, ts]))
    campo = lambda k, d: _suave(ts, [e.get(k, d) for e in est], S)
    A0, A1, W = campo(a0_clave, 0), campo(a1_clave, 0), campo("w", 0.1)
    N, KT, ZC, NB = campo("n", 2.5), campo("kt", 1.0), campo("zc", 0.0), campo("nb", np.nan)
    MZ, DY = campo("mezcla", 0.0), campo("dy", 0.0)
    anillos = []
    for i, t in enumerate(S):
        nb = None if np.isnan(NB[i]) else NB[i]
        if seccion is not None:  # panel: sección poligonal con aristas vivas
            C = _plantilla(seccion, float(np.clip(MZ[i], 0, 1)), seccion2)
            am, ah = (A0[i] + A1[i]) / 2, (A1[i] - A0[i]) / 2
            a = am + ah * C[:, 1]
            b = ZC[i] + max(W[i], 1e-4) * C[:, 0] * np.where(C[:, 1] > 0, 1 + (KT[i] - 1) * C[:, 1], 1)
            nseg = len(a)
        else:
            a, b = _superelipse(nseg, A0[i], A1[i], max(W[i], 1e-4), N[i], KT[i], ZC[i], nb)
        if eje == "x":
            anillos.append(np.stack([np.full(nseg, t), a, b], 1))
        else:
            anillos.append(np.stack([a, np.full(nseg, t), b], 1)[:, [0, 1, 2]])
    m = _anillos_a_malla(anillos, tapas)
    if eje == "y":  # (el orden de los vértices queda invertido respecto de x)
        m.f = m.f[:, ::-1]
    return m


def barrido(camino, h, w, n=2.0, nseg=16, pasos_por_tramo=4, arriba=(0, 1, 0), tapas=(True, True), kt=1.0):
    """Sección superelipse (semi-alto h, semi-ancho w; escalares o listas por punto) a lo largo de una polilínea.
    El semi-alto va hacia 'arriba' (proyectado), el semi-ancho perpendicular."""
    P = np.asarray(camino, float)
    k = len(P)
    hs = np.broadcast_to(np.asarray(h, float), (k,)); ws = np.broadcast_to(np.asarray(w, float), (k,))
    if k > 2 and pasos_por_tramo > 1:  # suavizado: Catmull-Rom uniforme
        Q, H, Wl = [], [], []
        for i in range(k - 1):
            p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, k - 1)]
            for s in np.linspace(0, 1, pasos_por_tramo, endpoint=False):
                Q.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s**3))
                H.append(hs[i] + (hs[i + 1] - hs[i]) * s); Wl.append(ws[i] + (ws[i + 1] - ws[i]) * s)
        Q.append(P[-1]); H.append(hs[-1]); Wl.append(ws[-1])
        P, hs, ws = np.array(Q), np.array(H), np.array(Wl)
    up = np.asarray(arriba, float)
    anillos = []
    for i in range(len(P)):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        t = t / (np.linalg.norm(t) or 1)
        u = up - t * up.dot(t)
        if np.linalg.norm(u) < 1e-6:
            u = np.array([1.0, 0, 0]) - t * t[0]
        u /= np.linalg.norm(u)
        s = np.cross(t, u)
        a, b = _superelipse(nseg, -hs[i], hs[i], ws[i], n, kt)
        anillos.append(P[i] + np.outer(a, u) + np.outer(b, s))
    return _anillos_a_malla(anillos, tapas)


def torno(perfil, centro, eje="z", nseg=48, cerrado=False):
    """perfil: [(r, a)] con a a lo largo del eje. Gira alrededor de 'eje' que pasa por 'centro'."""
    pr = np.asarray(perfil, float)
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    v = []
    for r, a in pr:
        c, s = r * np.cos(th), r * np.sin(th)
        if eje == "z":
            v.append(np.stack([c, s, np.full(nseg, a)], 1))
        elif eje == "x":
            v.append(np.stack([np.full(nseg, a), c, s], 1))
        else:
            v.append(np.stack([c, np.full(nseg, a), s], 1))
    m = len(pr); f = []
    for k in range(m - 1 + (1 if cerrado else 0)):
        k2 = (k + 1) % m
        for i in range(nseg):
            a = k * nseg + i; b = k * nseg + (i + 1) % nseg
            c = k2 * nseg + i; d = k2 * nseg + (i + 1) % nseg
            f += [(a, b, c), (b, d, c)]
    return Malla(np.concatenate(v) + np.asarray(centro, float), np.array(f))


def caja(c, tam, n=6.0, nseg=20, pasos=6):
    """Bloque casi rectangular (superelipse de exponente n) centrado en c con tamaño (dx, dy, dz)."""
    (x, y, z), (dx, dy, dz) = c, tam
    est = [{"x": x - dx / 2 + dx * t, "ys": y - dy / 2, "yt": y + dy / 2, "w": dz / 2, "n": n, "zc": z}
           for t in (0, 1)]
    return loft(est, nseg=nseg, pasos=pasos)


def radios(centro, z, r0, r1, cantidad, ancho, grueso, en_y=False, giro=0.0, nseg=8, abre=0.5, apertura=0.16):
    """Brazos del rin entre los radios r0 (cubo) y r1 (aro). en_y: tallo común hasta abre·(r1-r0) y luego dos
    ramas que se separan 'apertura' rad a cada lado al llegar al aro (como el rin de la NMAX). Las palas se afinan."""
    cx, cy = centro
    mallas = []
    P = lambda r, a: (cx + r * math.cos(a), cy + r * math.sin(a), z)
    for k in range(cantidad):
        a = math.radians(giro) + 2 * math.pi * k / cantidad
        if not en_y:
            mallas.append(barrido([P(r0, a), P((r0 + r1) / 2, a), P(r1, a)], [grueso / 2, grueso * 0.4, grueso * 0.3],
                                  [ancho / 2, ancho * 0.42, ancho * 0.36], n=3, nseg=nseg, pasos_por_tramo=2, arriba=(0, 0, 1)))
            continue
        rm = r0 + abre * (r1 - r0)
        mallas.append(barrido([P(r0, a), P(rm, a)], [grueso / 2, grueso * 0.45], [ancho / 2, ancho * 0.5], n=3,
                              nseg=nseg, pasos_por_tramo=1, arriba=(0, 0, 1)))
        for sg in (-1, 1):
            b = a + sg * apertura
            mallas.append(barrido([P(rm - 0.004, a), P((rm + r1) / 2, (a + b) / 2 + sg * 0.02), P(r1 + 0.004, b)],
                                  [grueso * 0.42, grueso * 0.34, grueso * 0.3], [ancho * 0.32, ancho * 0.27, ancho * 0.24],
                                  n=3, nseg=nseg, pasos_por_tramo=2, arriba=(0, 0, 1)))
    return unir(mallas)
