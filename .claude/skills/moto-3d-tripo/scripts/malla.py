# Utilidades de malla: suavizado por vecinos, recorte por campo implicito (bordes lisos), distancia a poligono, islas
import numpy as np


def aristas(I):
    e = np.sort(np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]), axis=1)
    return np.unique(e, axis=0)


def suavizar(valores, I, vueltas=2, peso=0.6):
    """Promedia cada vertice con sus vecinos (valores: n o n x k)."""
    e = aristas(I)
    v = valores.astype(np.float64).copy()
    grado = np.bincount(e.ravel(), minlength=len(v)).astype(np.float64)
    grado = np.maximum(grado, 1)
    for _ in range(vueltas):
        s = np.zeros_like(v)
        np.add.at(s, e[:, 0], v[e[:, 1]])
        np.add.at(s, e[:, 1], v[e[:, 0]])
        v = v * (1 - peso) + (s / (grado[:, None] if v.ndim > 1 else grado)) * peso
    return v


def dist_poligono(px, py, pol):
    """Distancia con signo (positiva adentro) de los puntos al poligono pol (m x 2)."""
    pol = np.asarray(pol, np.float64)
    a = pol
    b = np.roll(pol, -1, axis=0)
    d2 = np.full(len(px), np.inf)
    dentro = np.zeros(len(px), bool)
    for (ax, ay), (bx, by) in zip(a, b):
        ex, ey = bx - ax, by - ay
        wx, wy = px - ax, py - ay
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        d2 = np.minimum(d2, (wx - ex * t) ** 2 + (wy - ey * t) ** 2)
        cruza = ((ay > py) != (by > py)) & (px < (bx - ax) * (py - ay) / (by - ay + 1e-30) + ax)
        dentro ^= cruza
    return np.where(dentro, 1, -1) * np.sqrt(d2)


def espejo(mitad):
    """Poligono completo a partir de la mitad (|z|, y): refleja en z."""
    mitad = [tuple(p) for p in mitad]
    otra = [(-z, y) for z, y in reversed(mitad) if z > 1e-9]
    return np.array(mitad + otra)


class Recortador:
    """Reparte las caras entre piezas por orden de prioridad. Cada pieza es un campo por vertice (positivo = adentro);
    las caras que el borde atraviesa se parten por donde el campo vale cero, asi el borde sale liso."""

    def __init__(self, V, I):
        self.V = V.astype(np.float64)          # n x k: posicion, normal, color y todos los campos como columnas
        self.libres = I.astype(np.int64)        # caras sin pieza
        self.caras, self.etiquetas = [], []

    def cortar(self, col, etiqueta):
        V, F = self.V, self.libres
        if not len(F):
            return
        f = V[:, col]
        s = f[F] > 0
        n = s.sum(1)
        dentro, fuera, mixta = F[n == 3], F[n == 0], F[(n > 0) & (n < 3)]
        nuevas_d, nuevas_f = [dentro], [fuera]
        if len(mixta):
            sm = f[mixta] > 0
            uno = sm.sum(1) == 1                       # un vertice adentro (si no, uno afuera)
            solo = np.where(uno[:, None], sm, ~sm)     # marca el vertice "solitario"
            k = solo.argmax(1)
            fila = np.arange(len(mixta))
            a, b, c = mixta[fila, k], mixta[fila, (k + 1) % 3], mixta[fila, (k + 2) % 3]
            # vertices nuevos sobre las aristas a-b y a-c, compartidos entre caras vecinas
            pares = np.concatenate([np.stack([a, b], 1), np.stack([a, c], 1)])
            orden = np.sort(pares, axis=1)
            unicos, inv = np.unique(orden, axis=0, return_inverse=True)
            inv = inv.ravel()
            fa, fb = f[unicos[:, 0]], f[unicos[:, 1]]
            t = np.clip(fa / (fa - fb), 0.03, 0.97)[:, None]
            nuevos = V[unicos[:, 0]] * (1 - t) + V[unicos[:, 1]] * t
            nuevos[:, col] = 0
            base = len(V)
            self.V = V = np.concatenate([V, nuevos])
            p, q = base + inv[:len(a)], base + inv[len(a):]
            t1 = np.stack([a, p, q], 1)                # lado del solitario
            t2 = np.concatenate([np.stack([p, b, c], 1), np.stack([p, c, q], 1)])
            uno2 = np.concatenate([uno, uno])
            nuevas_d += [t1[uno], t2[~uno2]]
            nuevas_f += [t1[~uno], t2[uno2]]
        d = np.concatenate(nuevas_d)
        self.libres = np.concatenate(nuevas_f)
        if len(d):
            self.caras.append(d)
            self.etiquetas.append(np.full(len(d), etiqueta))

    def resultado(self, etiqueta_resto):
        if len(self.libres):
            self.caras.append(self.libres)
            self.etiquetas.append(np.full(len(self.libres), etiqueta_resto))
        return self.V, np.concatenate(self.caras), np.concatenate(self.etiquetas)


def vecinas(I):
    e = np.sort(np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]), axis=1)
    f = np.tile(np.arange(len(I)), 3)
    clave = e[:, 0].astype(np.int64) * (int(I.max()) + 1) + e[:, 1]
    o = np.argsort(clave)
    clave, f = clave[o], f[o]
    ig = clave[1:] == clave[:-1]
    return f[:-1][ig], f[1:][ig]


def quitar_islas(I, L, minimo, fijas=()):
    """Las manchas de menos de `minimo` caras pasan a la pieza vecina mas comun."""
    fa, fb = vecinas(I)
    for _ in range(2):
        padre = np.arange(len(I))

        def raiz(a):
            while padre[a] != a:
                padre[a] = padre[padre[a]]
                a = padre[a]
            return a
        igual = L[fa] == L[fb]
        for a, b in zip(fa[igual].tolist(), fb[igual].tolist()):
            ra, rb = raiz(a), raiz(b)
            if ra != rb:
                padre[max(ra, rb)] = min(ra, rb)
        r = np.array([raiz(i) for i in range(len(I))])
        _, comp, cuenta = np.unique(r, return_inverse=True, return_counts=True)
        chica = (cuenta[comp] < minimo) & ~np.isin(L, fijas)
        if not chica.any():
            break
        # voto de las vecinas que no son de la misma isla
        nl = int(L.max()) + 1
        votos = np.zeros((comp.max() + 1, nl), np.int32)
        dif = comp[fa] != comp[fb]
        np.add.at(votos, (comp[fa[dif]], L[fb[dif]]), 1)
        np.add.at(votos, (comp[fb[dif]], L[fa[dif]]), 1)
        gana = votos.argmax(1)
        hay = votos.max(1) > 0
        cambia = chica & hay[comp]
        L = L.copy()
        L[cambia] = gana[comp[cambia]]
    return L


def _extremo(v, e, vueltas, op):
    v = v.copy()
    for _ in range(vueltas):
        w = v.copy()
        op.at(w, e[:, 0], v[e[:, 1]])
        op.at(w, e[:, 1], v[e[:, 0]])
        v = w
    return v


def cerrar(campo, I, anillos=3):
    """Rellena las rendijas finas (campo negativo) dentro de una zona positiva: dilata y luego erosiona."""
    e = aristas(I)
    return _extremo(_extremo(campo.astype(np.float64), e, anillos, np.maximum), e, anillos, np.minimum)


def abrir(campo, I, anillos=2):
    """Quita las astillas finas positivas dentro de una zona negativa: erosiona y luego dilata."""
    e = aristas(I)
    return _extremo(_extremo(campo.astype(np.float64), e, anillos, np.minimum), e, anillos, np.maximum)


def a_pliegues(P, I, N, lum, d, valido, banda=0.012, k_pliegue=90.0, k_color=60.0):
    """Lleva el borde de una plantilla al pliegue (o al cambio de color) mas cercano del modelo.
    d: distancia con signo a la plantilla (positiva adentro); valido: vertices que pueden ser de la pieza.
    Dentro de la franja |d| < banda, cada vertice se queda con el lado al que llega mas barato: cruzar un pliegue o un
    cambio de tono cuesta caro, asi que la frontera se asienta sobre el. Sin pliegue, queda donde la plantilla."""
    import heapq
    e = aristas(I)
    local = np.where((np.abs(d) < banda * 2.5) & valido)[0]
    pos = np.full(len(P), -1)
    pos[local] = np.arange(len(local))
    e = e[(pos[e[:, 0]] >= 0) & (pos[e[:, 1]] >= 0)]
    # curvatura: cuanto se aparta la normal de un vertice de la de sus vecinos
    Nn = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    suma = np.zeros((len(P), 3))
    grado = np.zeros(len(P))
    np.add.at(suma, e[:, 0], Nn[e[:, 1]]); np.add.at(suma, e[:, 1], Nn[e[:, 0]])
    np.add.at(grado, e[:, 0], 1); np.add.at(grado, e[:, 1], 1)
    curv = np.linalg.norm(Nn - suma / np.maximum(grado, 1)[:, None], axis=1)
    largo = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1)
    costo = largo * (1 + k_pliegue * np.maximum(curv[e[:, 0]], curv[e[:, 1]]) ** 2 + k_color * np.abs(lum[e[:, 0]] - lum[e[:, 1]]))
    vec = [[] for _ in range(len(local))]
    for (a, b), c in zip(pos[e].tolist(), costo.tolist()):
        vec[a].append((b, c)); vec[b].append((a, c))

    def tiempos(semillas):
        t = np.full(len(local), np.inf)
        cola = [(0.0, int(i)) for i in pos[semillas]]
        for _, i in cola:
            t[i] = 0.0
        heapq.heapify(cola)
        while cola:
            ta, a = heapq.heappop(cola)
            if ta > t[a]:
                continue
            for b, c in vec[a]:
                if ta + c < t[b]:
                    t[b] = ta + c
                    heapq.heappush(cola, (ta + c, b))
        return t
    dl = d[local]
    t_in, t_out = tiempos(local[dl > banda]), tiempos(local[dl < -banda])
    campo = d.astype(np.float64).copy()
    franja = np.abs(dl) <= banda
    dif = np.where(np.isfinite(t_out - t_in), t_out - t_in, dl)
    campo[local[franja]] = np.clip(dif[franja], -banda, banda)
    return suavizar(campo, I, 1, 0.5)
