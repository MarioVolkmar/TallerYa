# Eco Deluxe 100 v5: farola (mica de Tripo + aro + reflector + bombillo), rin a la medida real, direccionales en piezas.
# Uso: python arreglos_v5.py v4.glb v2_respaldo.glb salida.glb   (glbio.py al lado: leer y escribir el formato del visor)
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import mallas, escribir

V4, V2, SAL = sys.argv[1:4]
g, ms = mallas(V4); M = {m["name"]: m for m in ms}
_, ms2 = mallas(V2); M2 = {m["name"]: m for m in ms2}


def normales(pos, idx):
    fn = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]]); n = np.zeros_like(pos)
    for k in range(3): np.add.at(n, idx[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def compactar(pos, nor, idx):
    u, inv = np.unique(idx.ravel(), return_inverse=True)
    return pos[u], nor[u], inv.reshape(-1, 3)


# ---------- 1. Ruedas: aro al rin de 18" (asiento 228,6 mm, pestaña a 236 mm), rayos hasta el aro, talón de la llanta en el aro
R_PESTANA = 0.236
for lado in ("tras", "del"):
    ex, ey = M["caucho.llanta_" + lado]["extras"]["eje"]
    aro = M["metal.aro_" + lado]; pa = aro["pos"]; ra = np.hypot(pa[:, 0] - ex, pa[:, 1] - ey)
    k = R_PESTANA / np.percentile(ra, 99)
    c = np.array([ex, ey, 0.0]); aro["pos"] = c + (pa - c) * k  # escala uniforme alrededor del eje (no estira ejes)
    ry = M["cromo.rayos_" + lado]; p = ry["pos"]; d = p[:, :2] - [ex, ey]; r = np.hypot(*d.T)
    rh, rmax = 0.077, np.percentile(r, 99.5); s = (rmax * k - rh) / (rmax - rh)
    rn = np.where(r > rh, rh + (r - rh) * s, r); p[:, :2] = [ex, ey] + d * (rn / np.maximum(r, 1e-9))[:, None]
    ll = M["caucho.llanta_" + lado]; p = ll["pos"]; d = p[:, :2] - [ex, ey]; r = np.hypot(*d.T)
    rin, rout = np.percentile(r, 1), r.max(); rin2 = rin * k
    rn = np.clip(rin2 + (r - rin) * (rout - rin2) / (rout - rin), rin2 * 0.98, None)
    p[:, :2] = [ex, ey] + d * (rn / np.maximum(r, 1e-9))[:, None]
    ll["nor"] = normales(p, ll["idx"])
    print(f"{lado}: aro x{k:.3f} (pestaña {R_PESTANA}), rayos x{s:.3f}, llanta {rin:.3f}-{rout:.3f} -> {rin2:.3f}-{rout:.3f}")

# ---------- 2. Farola: la mica curva de Tripo (v2; la v4 la cambió por una elipse plana), aro, reflector y bombillo
L = M2["luz.faro"]; lp, li = L["pos"], L["idx"]
cy, cz = (lp[:, 1].min() + lp[:, 1].max()) / 2, (lp[:, 2].min() + lp[:, 2].max()) / 2
ry_, rz_ = (lp[:, 1].max() - lp[:, 1].min()) / 2, (lp[:, 2].max() - lp[:, 2].min()) / 2
rn_v = np.hypot((lp[:, 1] - cy) / ry_, (lp[:, 2] - cz) / rz_)
th_v = np.arctan2((lp[:, 2] - cz) / rz_, (lp[:, 1] - cy) / ry_)
NB = 36; xb = np.full(NB, np.nan); bins = ((th_v + np.pi) / (2 * np.pi) * NB).astype(int) % NB
for b in range(NB):
    s = (bins == b) & (rn_v > 0.85)
    if s.sum(): xb[b] = np.median(lp[s, 0])
ok = ~np.isnan(xb); xb = np.interp(np.arange(NB), np.arange(NB)[ok], xb[ok], period=NB)


def x_borde(th):
    t = (np.asarray(th) + np.pi) / (2 * np.pi) * NB - 0.5
    return np.interp(t, np.arange(NB), xb, period=NB)


keep = (rn_v[li] < 0.975).all(1)  # el borde serrado queda bajo el aro cromado
mp, mn, mi = compactar(lp, L["nor"], li[keep])
mica = {"name": "vidrio.mica_faro", "pos": mp, "nor": mn, "idx": mi, "extras": {}}
print(f"mica: {keep.sum()} de {len(li)} triángulos, elipse {2*ry_:.3f} x {2*rz_:.3f} m, x borde {xb.min():.3f}-{xb.max():.3f}")
NT = 72; TH = np.linspace(-np.pi, np.pi, NT, endpoint=False)


def malla_grilla(P):  # P[anillo, ángulo] -> triángulos (cerrado en el ángulo)
    nr, nt = P.shape[:2]; idx = []
    for i in range(nr - 1):
        for j in range(nt):
            a, b, c, d = i * nt + j, i * nt + (j + 1) % nt, (i + 1) * nt + j, (i + 1) * nt + (j + 1) % nt
            idx += [(a, c, b), (b, c, d)]
    return P.reshape(-1, 3), np.array(idx)


def orientar(pp, ii, ref):  # normales hacia afuera de ref (vector o puntos de referencia)
    nn = normales(pp, ii)
    if (np.sum(nn * ref, 1) < 0).mean() > 0.5: ii = ii[:, [0, 2, 1]]; nn = -nn
    return pp, nn, ii


# aro (bisel cromado) sobre el borde de la mica: tubo elíptico achatado de 6,5 mm
RT, NS = 0.0065, 12; P = np.zeros((NS + 1, NT, 3)); C = np.zeros((NT, 3))
for j, th in enumerate(TH):
    radial = np.array([0, np.cos(th), np.sin(th)])
    C[j] = [x_borde(th) + 0.001, cy + ry_ * np.cos(th), cz + rz_ * np.sin(th)]
    for i in range(NS + 1):
        a = 2 * np.pi * i / NS; P[i, j] = C[j] + RT * (np.cos(a) * np.array([0.8, 0, 0]) + np.sin(a) * radial)
pp, ii = malla_grilla(P)
pp, nn, ii = orientar(pp, ii, pp - np.repeat(C[None], NS + 1, 0).reshape(-1, 3))
bisel = {"name": "cromo.aro_faro", "pos": pp, "nor": nn, "idx": ii, "extras": {}}
# reflector parabólico detrás de la mica (tapa el hueco del carenado)
D, NR = 0.055, 10; P = np.zeros((NR + 1, NT, 3))
for i in range(NR + 1):
    u = 0.97 * i / NR
    for j, th in enumerate(TH):
        P[i, j] = [x_borde(th) - 0.004 - D * (1 - (u / 0.97) ** 2), cy + u * ry_ * np.cos(th), cz + u * rz_ * np.sin(th)]
pp, ii = malla_grilla(P)
pp, nn, ii = orientar(pp, ii, np.array([1.0, 0, 0]))
reflector = {"name": "cromo.reflector_faro", "pos": pp, "nor": nn, "idx": ii, "extras": {}}
# bombillo: media esfera hacia adelante en el foco (la lámpara del visor: haz y halo salen de aquí)
xf = float(np.mean(xb)) - 0.004 - D + 0.024; RB = 0.017; P = np.zeros((9, 24, 3))
for i in range(9):
    a = np.pi / 2 * i / 8
    for j in range(24):
        b = 2 * np.pi * j / 24; P[i, j] = [xf + RB * np.cos(a), cy + RB * np.sin(a) * np.cos(b), cz + RB * np.sin(a) * np.sin(b)]
pp, ii = malla_grilla(P)
pp, nn, ii = orientar(pp, ii, pp - [xf, cy, cz])
bombillo = {"name": "luz.faro", "pos": pp, "nor": nn, "idx": ii, "extras": {"lampara": {"tipo": "faro"}}}


# ---------- 3. Direccionales: vástago (oscuro), carcasa (negro brillante) y mica ámbar (la que se enciende)
def cortar(pos, nor, idx, n, d):
    """Parte la malla por el plano n·x = d: devuelve (lado positivo, lado negativo) con los triángulos del borde partidos."""
    P, N = list(pos), list(nor); lados = ([], []); dist = pos @ n - d; cache = {}

    def medio(a, b):
        key = (min(a, b), max(a, b))
        if key not in cache:
            t = dist[a] / (dist[a] - dist[b]); P.append(pos[a] + (pos[b] - pos[a]) * t); N.append(nor[a] + (nor[b] - nor[a]) * t)
            cache[key] = len(P) - 1
        return cache[key]
    for tri in idx:
        s = dist[tri] >= 0
        if s.all() or (~s).all(): lados[0 if s.all() else 1].append(tuple(tri)); continue
        k = next(k for k in range(3) if s[k] != s[(k + 1) % 3] and s[k] != s[(k + 2) % 3])  # vértice solitario
        a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]; ab, ac = medio(a, b), medio(a, c)
        solo, par = (0, 1) if s[k] else (1, 0)
        lados[solo].append((a, ab, ac)); lados[par].extend([(ab, b, c), (ab, c, ac)])
    P, N = np.array(P), np.array(N)
    return [compactar(P, N, np.array(l)) for l in lados]


def unir(partes):
    pos, nor, idx, o = [], [], [], 0
    for p, n, i in partes: pos.append(p); nor.append(n); idx.append(i + o); o += len(p)
    return np.vstack(pos), np.vstack(nor), np.vstack(idx)


carcasas, vastagos, nuevas = [], [], {}
for nom in ("ambar.direccional_del_a", "ambar.direccional_del_b", "ambar.direccional_tras_a", "ambar.direccional_tras_b"):
    m = M[nom]; p = m["pos"]; sgn = np.sign(p[:, 2].mean())
    zc = 0.133 if "del" in nom else 0.124  # cuello medido entre el cuerpo y la base
    cuerpo, cuello = cortar(p, m["nor"], m["idx"], np.array([0, 0, sgn]), zc)
    vastagos.append(cuello)
    cp = cuerpo[0]; cx = (cp[:, 0].min() + cp[:, 0].max()) / 2; adelante = 1 if "del" in nom else -1
    xcorte = cx + adelante * 0.1 * (cp[:, 0].max() - cp[:, 0].min())  # mica algo menor que media carcasa
    mica_d, carc = cortar(*cuerpo, np.array([adelante, 0, 0]), adelante * xcorte)
    carcasas.append(carc)
    nuevas[nom] = {"name": nom, "pos": mica_d[0], "nor": mica_d[1], "idx": mica_d[2], "extras": m["extras"]}
    print(f"{nom}: mica {len(mica_d[2])}, carcasa {len(carc[2])}, vástago {len(cuello[2])}")
cp_, cn_, ci_ = unir(carcasas); vp_, vn_, vi_ = unir(vastagos)
extra = [{"name": "negro_brillo.carcasa_direccionales", "pos": cp_, "nor": cn_, "idx": ci_, "extras": {}},
         {"name": "oscuro.vastago_direccionales", "pos": vp_, "nor": vn_, "idx": vi_, "extras": {}}]

salida = []
for m in ms:
    if m["name"] == "luz.faro": salida += [mica, bisel, reflector, bombillo]; continue
    salida.append(nuevas.get(m["name"], m))
    if m["name"] == "ambar.direccional_tras_b": salida += extra
escribir(SAL, salida, g["asset"].get("generator", "TallerYa").split("; v5")[0] + "; v5 farola, rin y direccionales")
