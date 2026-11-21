"""Despiece de la malla única de Tripo por reglas geométricas en coordenadas de la moto.
Cada cara recibe una etiqueta (pieza); el orden de las reglas importa (la primera que acierta gana).
Uso: python -I segmentar.py  → privado/tripo/xr190l/despiece.npz y renders de control en el scratchpad."""
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.csgraph as cg

sys.path.insert(0, os.path.dirname(__file__))
from comun import ORIGEN, RAIZ, TRABAJO, a_moto, leer_glb, normales_cara  # noqa: E402
from PIL import Image  # noqa: E402

PULG = 0.0254


def limpiar(V, F):
    """Defectos de Tripo: triángulos sueltos (componentes de < 20 caras), caras degeneradas y huecos chicos."""
    rep = {}
    n = len(V)
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    A = sp.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n))
    k, lab = cg.connected_components(A, directed=False)
    cnt = np.bincount(lab[F[:, 0]], minlength=k)
    sueltas = cnt[lab[F[:, 0]]] < 20
    _, area = normales_cara(V, F)
    deg = area < 1e-12
    rep["caras_sueltas_quitadas"] = int(sueltas.sum())
    rep["caras_degeneradas_quitadas"] = int(deg.sum())
    F = F[~sueltas & ~deg]
    # Huecos: lazos de aristas de borde; los de hasta 40 aristas se tapan con un abanico desde su centro
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    clave = np.sort(E, 1)
    u, inv, c = np.unique(clave, axis=0, return_inverse=True, return_counts=True)
    borde = E[c[inv.ravel()] == 1]  # (con su sentido original)
    sig = {}
    for a, b in borde:
        sig.setdefault(b, []).append(a)  # (el tapón recorre el lazo al revés para quedar con la misma orientación)
    usados, lazos = set(), []
    for v0 in list(sig):
        if v0 in usados:
            continue
        lazo, v = [v0], v0
        while True:
            usados.add(v)
            nx = [w for w in sig.get(v, []) if w not in usados]
            if not nx:
                break
            v = nx[0]
            lazo.append(v)
            if len(lazo) > 200:
                break
        if v0 in sig.get(lazo[-1], []) and 3 <= len(lazo) <= 40:
            lazos.append(lazo)
    nuevasV, nuevasF = [], []
    for lazo in lazos:
        ci = len(V) + len(nuevasV)
        nuevasV.append(V[lazo].mean(0))
        for i in range(len(lazo)):
            nuevasF.append([lazo[i], lazo[(i + 1) % len(lazo)], ci])
    rep["huecos_tapados"] = len(lazos)
    rep["aristas_borde_antes"] = int(len(borde))
    if nuevasV:
        V = np.vstack([V, nuevasV])
        F = np.vstack([F, nuevasF])
    # Caras invertidas: la normal de la cara contra la de sus vecinas (promedio de normales de vértice por área)
    nC, area = normales_cara(V, F)
    nV = np.zeros_like(V)
    for k in range(3):
        np.add.at(nV, F[:, k], nC * area[:, None])
    nV /= np.maximum(np.linalg.norm(nV, axis=1), 1e-12)[:, None]
    acuerdo = (nC * nV[F].mean(1)).sum(1)
    inv = acuerdo < -0.3
    F[inv] = F[inv][:, [0, 2, 1]]
    rep["caras_invertidas_corregidas"] = int(inv.sum())
    return V, F, rep


def ruedas(W):
    out = {}
    # Rines según la ficha: 90/90-19 adelante y 110/90-17 atrás
    for nombre, lado, rin in (("del", 1, 19), ("tras", -1, 17)):
        P = W[W[:, 0] * lado > 0.3]
        xc = P[P[:, 1] < 0.012][:, 0].mean()
        R = 0.32
        for _ in range(6):
            b = P[(np.abs(P[:, 1] - R) < 0.02) & (np.abs(P[:, 2]) < 0.07)]
            R = abs((b[:, 0].max() if lado > 0 else b[:, 0].min()) - xc)
        out[nombre] = dict(c=np.array([xc, R]), R=R, rin=rin * PULG / 2)
    return out


def eje_horquilla(W, rd):
    """Recta de las barras de la horquilla (PCA de los puntos a los lados de la rueda delantera, sobre el eje)."""
    cx, cy = rd["c"]
    m = (W[:, 1] > cy + 0.12) & (W[:, 1] < cy + 0.45) & (np.abs(W[:, 2]) > 0.07) & (np.abs(W[:, 2]) < 0.13) & \
        (W[:, 0] > cx - 0.35) & (W[:, 0] < cx + 0.05)
    P = W[m][:, :2]
    c = P.mean(0)
    d = np.linalg.svd(P - c)[2][0]
    if d[1] < 0:
        d = -d
    return c, d


# --- Foto lateral (lado derecho, 1000 px): los ejes de las ruedas sirven de calce entre la moto y la foto ---
FOTO = RAIZ / "FOTOS_MODELADO_TRIPO/honda_xr_190l/1_lateral.jpg"
EJES_FOTO = {"tras": (214.0, 670.0), "del": (826.0, 671.0)}  # (px, medidos en la foto)


def clase_foto(C, rd):
    """Clase de color de la foto en la proyección lateral de cada centro de cara: 'r' rojo, 'b' blanco, 'n' negro, '' fondo."""
    im = np.asarray(Image.open(FOTO).convert("RGB")).astype(int)
    (xa, ya), (xb, yb) = EJES_FOTO["tras"], EJES_FOTO["del"]
    ma, mb = rd["tras"]["c"], rd["del"]["c"]
    esc = (xb - xa) / (mb[0] - ma[0])
    px = np.clip((xa + (C[:, 0] - ma[0]) * esc).astype(int), 0, im.shape[1] - 1)
    py = np.clip((ya - (C[:, 1] - ma[1]) * esc).astype(int), 0, im.shape[0] - 1)
    # (promedio de un parche de 5×5 para no caer en un borde)
    acc = np.zeros((len(C), 3))
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            acc += im[np.clip(py + dy, 0, im.shape[0] - 1), np.clip(px + dx, 0, im.shape[1] - 1)]
    rgb = acc / 9
    r, g, b = rgb.T
    cl = np.full(len(C), "n", dtype=object)
    # (rojo por tono, no por brillo: el rojo en sombra de la foto sigue siendo rojo y no deja manchas negras)
    cl[(r > 55) & (r > 1.7 * g) & (r > 1.5 * b)] = "r"
    cl[(rgb.min(1) > 150) & (rgb.max(1) - rgb.min(1) < 40)] = "b"
    cl[(rgb.min(1) > 238)] = ""
    return cl, px, py


def clase_visible(C, F, rd):
    """Clase de la foto solo para las caras que se ven de lado (z-buffer por celdas de 4 px; la foto es del lado
    derecho = z < 0, y el lado izquierdo se toma como espejo). Las caras ocultas (lo de adentro, tapado por una
    cubierta) heredan la clase de la cara visible más cercana sobre la malla, así no copian el color de lo que las tapa."""
    cl, px, py = clase_foto(C, rd)
    celda = (py // 4) * 1000 + (px // 4)
    vis = np.zeros(len(C), bool)
    for lado in (-1, 1):
        m = np.nonzero(C[:, 2] * lado >= 0)[0]
        prof = -C[m, 2] * lado  # (menor = más cerca de la cámara de ese lado)
        orden = np.lexsort((prof, celda[m]))
        cm, pm = celda[m][orden], prof[orden]
        primero = np.r_[True, cm[1:] != cm[:-1]]
        idx_grupo = np.cumsum(primero) - 1
        minimo = pm[primero][idx_grupo]
        vis[m[orden]] = pm <= minimo + 0.025
    vis &= cl != ""
    a, b = vecinos(F)
    L = np.linalg.norm(C[a] - C[b], axis=1) + 1e-6
    G = sp.coo_matrix((np.r_[L, L], (np.r_[a, b], np.r_[b, a])), shape=(len(C), len(C))).tocsr()
    fuentes = np.nonzero(vis)[0]
    _, _, src = cg.dijkstra(G, indices=fuentes, min_only=True, return_predecessors=True)
    out = cl.copy()
    oc = ~vis & (src >= 0)
    out[oc] = cl[src[oc]]
    return out


def segmentar(W, F):
    C = W[F].mean(1)
    nC, _ = normales_cara(W, F)
    x, y, z = C[:, 0], C[:, 1], C[:, 2]
    az = np.abs(z)
    lab = np.full(len(F), "", dtype=object)
    rd = ruedas(W)
    fc, fd = eje_horquilla(W, rd["del"])
    cl = clase_visible(C, F, rd)

    def pon(nombre, m):
        m = m & (lab == "")
        lab[m] = nombre

    rel = C[:, :2] - fc
    t = rel @ fd
    dperp = np.abs(rel[:, 0] * fd[1] - rel[:, 1] * fd[0])
    # (t = 0 cae a y ≈ 0,61: ahí va el retén; abajo la barra plateada, arriba la negra)
    en_horquilla = (dperp < 0.05) & (az > 0.05)
    pon("horquilla_baja", en_horquilla & (t > -0.42) & (t < 0.0))

    for nombre, w in rd.items():
        cx, cy = w["c"]
        r = np.hypot(x - cx, y - cy)
        R, rr = w["R"], w["rin"]
        dentro = r < R + 0.004  # (sin pedazos de guardabarros u horquilla que inflen la llanta torneada)
        if nombre == "del":
            pon("disco_del", dentro & (r < 0.14) & (r > 0.04) & (az > 0.03) & (az < 0.075) & (np.abs(nC[:, 2]) > 0.85))
        else:
            # (atrás la XR lleva tambor: lo plano a la izquierda es la corona de la cadena)
            pon("corona", dentro & (r < 0.12) & (r > 0.04) & (z > 0.04) & (z < 0.09) & (np.abs(nC[:, 2]) > 0.85))
        # (ancho real de la llanta: 90 mm adelante y 110 atrás; más ancha, el torneado del visor la vuelve un globo.
        # Adelante, 6 mm menos de radio: en la silueta sobraba un anillo de 6 a 10 px)
        media = 0.045 if nombre == "del" else 0.055
        dentro_ll = dentro & ((r < R - 0.006) if nombre == "del" else True)
        pon(f"llanta_{nombre}", dentro_ll & (r > rr + 0.006) & (az < media))
        # (el balón de Tripo que sobra a los lados se descarta: la llanta la vuelve a tornear el visor)
        pon("_balon", dentro & (r > rr + 0.006) & (az < 0.085))
        pon(f"aro_{nombre}", dentro & (r > rr - 0.02) & (r <= rr + 0.006) & (az < 0.06))
        pon(f"rayos_{nombre}", dentro & (r <= rr - 0.02) & (az < 0.075) & ~((nombre == "tras") & (az > 0.05) & (x > cx)))

    cxr, cyr = rd["tras"]["c"]
    cxf, cyf = rd["del"]["c"]
    pon("horquilla_alta", en_horquilla & (t >= 0.0) & (t < 0.62))
    xh = fc[0] + fd[0] * 0.62
    pon("espejos", (y > 1.12) & (x > 0.0) & (x < 0.45))
    pon("punos", (y > 0.98) & (az > 0.30) & (x > 0.05) & (x < 0.45))
    pon("manubrio", (y > 0.98) & (x > 0.05) & (x < 0.45) & (az > 0.03))
    pon("mascara", (x > xh - 0.02) & (y > 0.80) & (y < 1.12) & (az < 0.16))
    pon("guardabarros_del", (x > cxf - 0.42) & (y > cyf + 0.22) & (y < 0.86) & (az < 0.13) & (x > fc[0] - 0.1 + (y - fc[1]) * fd[0] / fd[1] - 0.25))
    # Cola: parrilla negra arriba, portaplaca abajo atrás, guardabarros
    pon("parrilla", (x < -0.55) & (y > 0.93) & (cl != "r"))
    pon("portaplaca", (x < -0.86) & (y > 0.35) & (y < 0.75))
    # Carrocería por la foto: rojo, blanco y negro dentro de la región de cada pieza
    cuerpo = (lab == "") & (y > 0.45) & (x > -1.05) & (x < xh + 0.02)
    roja = cuerpo & (cl == "r")
    pon("aletas", roja & (x >= -0.25) & (y > 0.55))
    pon("colin", roja & (x < -0.25) & (y > 0.70))
    pon("tapa_lateral", cuerpo & (cl == "b") & (x > -0.62) & (x < -0.02) & (y > 0.5) & (y < 0.9) & (az > 0.07))
    # (blanco de las calcas de la aleta: es aleta)
    pon("aletas", cuerpo & (cl == "b") & (x >= -0.02) & (y > 0.6) & (az > 0.06))
    pon("asiento", cuerpo & (x > -0.8) & (x < 0.02) & (y > 0.80) & (nC[:, 1] > 0.2) & (az < 0.17) & (cl != "r"))
    pon("tanque", cuerpo & (x >= -0.05) & (x < xh - 0.02) & (y > 0.78) & (az < 0.11) & (nC[:, 1] > 0.3))
    # Escape: cubierta negra del lado derecho bajo el colín (la XR lo lleva a la derecha)
    pon("escape", cuerpo & (z < -0.06) & (x > -0.82) & (x < -0.3) & (y < 0.86) & (cl != "r") & (cl != "b"))
    pon("cubierta_trasera", cuerpo & (x > -0.85) & (x < -0.3) & (y < 0.9) & (az > 0.06) & (cl != "r") & (cl != "b"))
    pon("guardabarros_tras", (x < -0.78) & (y > 0.35))
    pon("escape", (z < -0.09) & (x > -0.75) & (x < -0.05) & (y > 0.30) & (y < 0.62))
    pon("basculante", (x > cxr - 0.05) & (x < -0.10) & (y > 0.18) & (y < 0.50) & (az < 0.14))
    pon("amortiguador", (x > -0.45) & (x < -0.05) & (y >= 0.45) & (y < 0.85) & (az < 0.07))
    # Estribos (piloto y pasajero) y pedales: lo que sale a los lados abajo
    pon("estribos", (y < 0.44) & (y > 0.15) & (az > 0.12) & (x > -0.5) & (x < 0.32))
    pon("motor", (x > -0.2) & (x < 0.36) & (y > 0.12) & (y < 0.72) & (az < 0.20))
    pon("aletas", (lab == "") & (x >= -0.12) & (x < xh + 0.02) & (y > 0.62) & (y < 1.02) & (az >= 0.07))
    pon("chasis", lab == "")
    lab = suavizar_etiquetas(F, lab, 4)
    lab = quitar_islas(F, lab, ("aletas", "colin", "tapa_lateral", "asiento", "cubierta_trasera", "escape", "tanque"))
    lab = quitar_encerradas(F, lab)
    # (manchas de «chasis» en la cara de afuera de las aletas y de la tapa lateral: son sombras de la foto; el tubo del
    # chasis queda detrás del plástico, así que lo que mira hacia afuera en esa zona es panel)
    afuera = (lab == "chasis") & (np.abs(nC[:, 2]) > 0.45)
    lab[afuera & (x >= -0.12) & (x < xh) & (y > 0.68) & (y < 1.0) & (az > 0.06)] = "aletas"
    lab[afuera & (x > -0.6) & (x < -0.12) & (y > 0.58) & (y < 0.88) & (az > 0.09)] = "tapa_lateral"
    return lab, rd, (fc, fd)


def quitar_encerradas(F, lab, paneles=("tapa_lateral", "aletas", "colin"), oscuras=("chasis", "cubierta_trasera", "escape", "tanque"),
                      maximo=2500, parte=0.8):
    """Manchas negras dentro de un panel de plástico (sombras de la foto que se pintaron como chasis o cubierta): una tapa
    lateral o una aleta real es una sola pieza inyectada, así que la mancha rodeada en ≥ 80 % por el panel pasa a ser panel."""
    a, b = vecinos(F)
    mismo = lab[a] == lab[b]
    G = sp.coo_matrix((np.ones(mismo.sum()), (a[mismo], b[mismo])), shape=(len(F), len(F)))
    k, comp = cg.connected_components(G, directed=False)
    tam = np.bincount(comp, minlength=k)
    cand = np.isin(lab, oscuras) & (tam[comp] < maximo)
    borde = (comp[a] != comp[b])
    votos = {}
    for i, j in zip(a[borde], b[borde]):
        if cand[i]:
            votos.setdefault(comp[i], []).append(lab[j])
        if cand[j]:
            votos.setdefault(comp[j], []).append(lab[i])
    cambio = {}
    for c, v in votos.items():
        top = max(set(v), key=v.count)
        if top in paneles and v.count(top) >= parte * len(v):
            cambio[c] = top
    for f in np.nonzero(cand)[0]:
        if comp[f] in cambio:
            lab[f] = cambio[comp[f]]
    print("encerradas:", len(cambio), "manchas,", int(sum(tam[c] for c in cambio)), "caras")
    return lab


def vecinos(F):
    E = np.concatenate([np.sort(F[:, [0, 1]], 1), np.sort(F[:, [1, 2]], 1), np.sort(F[:, [2, 0]], 1)])
    cara = np.tile(np.arange(len(F)), 3)
    o = np.lexsort((E[:, 1], E[:, 0]))
    E, cara = E[o], cara[o]
    igual = np.all(E[1:] == E[:-1], 1)
    return cara[:-1][igual], cara[1:][igual]


def suavizar_etiquetas(F, lab, vueltas=3):
    """Bordes de pieza menos dentados: cada cara toma la etiqueta de la mayoría de sus 3 vecinas (si 2 o 3 coinciden)."""
    a, b = vecinos(F)
    vec = [[] for _ in range(len(F))]
    for i, j in zip(a, b):
        vec[i].append(j); vec[j].append(i)
    lab = lab.copy()
    for _ in range(vueltas):
        nuevo = lab.copy()
        for f, vs in enumerate(vec):
            if len(vs) < 3:
                continue
            l = [lab[v] for v in vs]
            for cand in set(l):
                if cand != lab[f] and l.count(cand) >= 2:
                    nuevo[f] = cand
        lab = nuevo
    return lab


def quitar_islas(F, lab, piezas, minimo=150):
    """Islas de una pieza de carrocería dentro de otra (manchas de camuflaje): las de < minimo caras pasan a la
    pieza vecina más común."""
    a, b = vecinos(F)
    for _ in range(2):
        mismo = lab[a] == lab[b]
        G = sp.coo_matrix((np.ones(mismo.sum()), (a[mismo], b[mismo])), shape=(len(F), len(F)))
        k, comp = cg.connected_components(G, directed=False)
        tam = np.bincount(comp, minlength=k)
        chica = (tam[comp] < minimo) & np.isin(lab, piezas)
        if not chica.any():
            break
        # vecina más común fuera de la isla
        borde = comp[a] != comp[b]
        votos = {}
        for i, j in zip(a[borde], b[borde]):
            if chica[i]:
                votos.setdefault(comp[i], []).append(lab[j])
            if chica[j]:
                votos.setdefault(comp[j], []).append(lab[i])
        nuevo = {c: max(set(v), key=v.count) for c, v in votos.items()}
        for f in np.nonzero(chica)[0]:
            if comp[f] in nuevo:
                lab[f] = nuevo[comp[f]]
    return lab


if __name__ == "__main__":
    V, F = leer_glb(ORIGEN)
    W = a_moto(V, 1)
    # Tripo dejó la moto espejada (cadena a la derecha): en el visor +z es la izquierda. Se espeja en z y se
    # voltean las caras para que la cadena quede a la izquierda y el escape a la derecha, como la XR real.
    W[:, 2] *= -1
    F = F[:, [0, 2, 1]]
    W, F, rep = limpiar(W, F)
    lab, rd, fork = segmentar(W, F)
    np.savez_compressed(TRABAJO / "despiece.npz", W=W, F=F, lab=lab.astype(str))
    print(rep)
    print({k: (round(float(v["c"][0]), 3), round(float(v["R"]), 3)) for k, v in rd.items()}, "horquilla", fork[0].round(3), fork[1].round(3))
    u, c = np.unique(lab.astype(str), return_counts=True)
    print(dict(zip(u, c.tolist())))
