# Aerox 155: luces al nivel de la Eco Deluxe (mica de Tripo + aro + reflector + LED), stop con marco, direccionales
# traseras en mica y carcasa, rin a la medida de la llanta y acabados PBR. Parte de la geometría limpiada en Blender.
# Uso: python arreglos.py original.glb blender.glb salida.glb   (extras del original, geometría de Blender)
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import mallas, escribir

ORIG, BLEND, SAL = sys.argv[1:4]
g, mo = mallas(ORIG); EX = {m["name"]: m["extras"] for m in mo}; ORDEN = [m["name"] for m in mo]
_, mb = mallas(BLEND); M = {m["name"]: m for m in mb}
for k, m in M.items(): m["extras"] = EX.get(k, {})


def hacia_afuera(m):  # fracción de caras que miran lejos del centro de la pieza
    p, i = m["pos"], m["idx"]; fn = np.cross(p[i[:, 1]] - p[i[:, 0]], p[i[:, 2]] - p[i[:, 0]])
    return float(((fn * (p[i].mean(1) - p.mean(0))).sum(1) > 0).mean())


# Blender (recalc_face_normals) a veces da vuelta una pieza entera (sillín, carrocería): se vuelve a la orientación de Tripo
for mo_ in mo:
    m = M[mo_["name"]]
    if (hacia_afuera(mo_) - 0.5) * (hacia_afuera(m) - 0.5) < 0 and abs(hacia_afuera(mo_) - 0.5) > 0.08:
        m["idx"] = m["idx"][:, [0, 2, 1]]; m["nor"] = -m["nor"]; print(mo_["name"], "orientación restituida")


def normales(pos, idx):
    fn = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]]); n = np.zeros_like(pos)
    for k in range(3): np.add.at(n, idx[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def compactar(pos, nor, idx):
    u, inv = np.unique(idx.ravel(), return_inverse=True)
    return pos[u], nor[u], inv.reshape(-1, 3)


def soldar(pos, idx, tol=1e-4):  # Blender exporta vértices partidos por normal: se unen para hallar el borde real
    q = np.round(pos / tol).astype(np.int64); _, u, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return pos[u], inv.ravel()[idx]


def bordes(idx):
    e = np.sort(np.vstack([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return u[c == 1]


def lazos(be):  # aristas de borde -> lazos ordenados de vértices
    vec = {}
    for a, b in be: vec.setdefault(a, []).append(b); vec.setdefault(b, []).append(a)
    vistos, out = set(), []
    for s in list(vec):
        if s in vistos: continue
        lazo, prev, cur = [s], None, s; vistos.add(s)
        while True:
            sig = [v for v in vec[cur] if v != prev and v not in vistos]
            if not sig: break
            prev, cur = cur, sig[0]; lazo.append(cur); vistos.add(cur)
        if len(lazo) >= 6: out.append(lazo)
    return out


def recortar(pos, idx, anillos=1):  # quita el borde serrado (uno o más anillos de triángulos del borde)
    ps, ii = soldar(pos, idx)
    for _ in range(anillos):
        bv = np.unique(bordes(ii)); keep = ~np.isin(ii, bv).any(1)
        if keep.sum() < 0.4 * len(ii): break
        ii = ii[keep]
    u, inv = np.unique(ii.ravel(), return_inverse=True)
    p = ps[u]; i = inv.reshape(-1, 3)
    return p, normales(p, i), i


def orientar(pp, ii, ref):
    nn = normales(pp, ii)
    if (np.sum(nn * ref, 1) < 0).mean() > 0.5: ii = ii[:, [0, 2, 1]]; nn = -nn
    return pp, nn, ii


def tubo(P, nref, r=0.004, ns=8, achate=0.8):  # tubo cerrado a lo largo del lazo P (n,3); nref: normal de la superficie
    n = len(P); T = np.roll(P, -1, 0) - np.roll(P, 1, 0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = nref - (nref * T).sum(1, keepdims=True) * T; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    Bn = np.cross(T, N); Q = np.zeros((ns, n, 3))
    for i in range(ns):
        a = 2 * np.pi * i / ns; Q[i] = P + r * (np.cos(a) * N * achate + np.sin(a) * Bn)
    idx = []
    for i in range(ns):
        for j in range(n):
            a, b, c, d = i * n + j, i * n + (j + 1) % n, ((i + 1) % ns) * n + j, ((i + 1) % ns) * n + (j + 1) % n
            idx += [(a, c, b), (b, c, d)]
    pp = Q.reshape(-1, 3); ii = np.array(idx)
    return orientar(pp, ii, pp - np.tile(P, (ns, 1)))


def unir(partes):
    pos, nor, idx, o = [], [], [], 0
    for p, n, i in partes: pos.append(p); nor.append(n); idx.append(i + o); o += len(p)
    return np.vstack(pos), np.vstack(nor), np.vstack(idx)


def nodo(nombre, pni, extras=None):
    return {"name": nombre, "pos": pni[0], "nor": pni[1], "idx": pni[2], "extras": extras or {}}


def lazo_borde(p, i):
    L = lazos(bordes(i)); return max(L, key=len) if L else None


def lampara_completa(nom, sufijo, prof=0.028, r_aro=0.0035, mat_aro="cromo", foco=0.55):
    """Mica de Tripo sin el borde serrado + aro sobre el corte + reflector en copa detrás + emisor interior."""
    m = M[nom]; nm = m["nor"].mean(0); nm /= np.linalg.norm(nm)
    mp, mn, mi = recortar(m["pos"], m["idx"], 1)
    lazo = lazo_borde(mp, mi); P = mp[lazo]; nP = mn[lazo]; c = mp.mean(0)
    # aro (bisel) sobre el borde recortado, un poco hacia afuera para tapar el corte del carenado
    aro = tubo(P + nP * 0.0008, nP, r=r_aro)
    # reflector: pared del borde hacia atrás y fondo parabólico (tapa el hueco del carenado)
    anillos = []
    for k, t in enumerate(np.linspace(0, 1, 7)):
        enc = 1 - 0.55 * t ** 1.6
        anillos.append(c + (P - c) * enc - nm * (0.002 + prof * t ** 0.8))
    A = np.array(anillos); nr, nt = A.shape[:2]; idx = []
    for a_ in range(nr - 1):
        for j in range(nt):
            a, b, cc, d = a_ * nt + j, a_ * nt + (j + 1) % nt, (a_ + 1) * nt + j, (a_ + 1) * nt + (j + 1) % nt
            idx += [(a, cc, b), (b, cc, d)]
    fondo = c - nm * (prof + 0.006); base = (nr - 1) * nt
    pp = np.vstack([A.reshape(-1, 3), fondo]); idx += [(base + j, nr * nt, base + (j + 1) % nt) for j in range(nt)]
    refl = orientar(pp, np.array(idx), nm)  # la cara brillante mira hacia la mica
    # emisor: la mica encogida hacia su centro, metida detrás (forma real del LED, mira adelante)
    ep = c + (mp - c) * foco - nm * 0.009
    emis = (ep, mn.copy(), mi.copy())
    mica = (mp, mn, mi)
    return mica, aro, refl, emis


def lampara_ajustada(nom, prof=0.03, r_aro=0.0035, foco=0.62, NT=72):
    """Para micas astilladas (varias islas serradas): superficie cuadrática ajustada a los vértices de Tripo (conserva la
    curva), contorno polar con el máximo por sector y suavizado; encima aro, copa reflectora y emisor interior."""
    m = M[nom]; p = m["pos"]; nm = m["nor"].mean(0); nm /= np.linalg.norm(nm)
    e1 = np.cross(nm, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(nm, e1)
    c0 = p.mean(0); U, V, H = (p - c0) @ e1, (p - c0) @ e2, (p - c0) @ nm
    X = np.c_[np.ones_like(U), U, V, U * U, U * V, V * V]; co = np.linalg.lstsq(X, H, rcond=None)[0]
    alto = lambda u, v: np.c_[np.ones_like(u), u, v, u * u, u * v, v * v] @ co
    uc, vc = (U.min() + U.max()) / 2, (V.min() + V.max()) / 2; th = np.arctan2(V - vc, U - uc); r = np.hypot(U - uc, V - vc)
    b = ((th + np.pi) / (2 * np.pi) * NT).astype(int) % NT; R = np.full(NT, np.nan)
    for k in range(NT):
        if (b == k).any(): R[k] = r[b == k].max()
    ok = ~np.isnan(R); R = np.interp(np.arange(NT), np.arange(NT)[ok], R[ok], period=NT)
    R = np.maximum.reduce([np.roll(R, s) for s in (-2, -1, 0, 1, 2)])                # cubre los dientes
    for _ in range(2): R = (np.roll(R, -1) + 2 * R + np.roll(R, 1)) / 4                                    # contorno liso, esquinas vivas
    TH = (np.arange(NT) + 0.5) / NT * 2 * np.pi - np.pi
    def punto(fr, dz=0.0):
        uu, vv = uc + fr * R * np.cos(TH), vc + fr * R * np.sin(TH)
        return c0 + np.outer(uu, e1) + np.outer(vv, e2) + np.outer(alto(uu, vv) + dz, nm)
    def disco(fracs, dz):  # anillos + centro -> malla
        A = np.array([punto(f, dz) for f in fracs]); cen = c0 + (uc * e1 + vc * e2) + (alto(np.array([uc]), np.array([vc]))[0] + dz) * nm
        pp = np.vstack([cen, A.reshape(-1, 3)]); idx = [(0, 1 + j, 1 + (j + 1) % NT) for j in range(NT)]
        for a_ in range(len(fracs) - 1):
            for j in range(NT):
                a, bb, cc, d = 1 + a_ * NT + j, 1 + a_ * NT + (j + 1) % NT, 1 + (a_ + 1) * NT + j, 1 + (a_ + 1) * NT + (j + 1) % NT
                idx += [(a, cc, bb), (bb, cc, d)]
        return orientar(pp, np.array(idx), nm)
    mica = disco([0.25, 0.5, 0.7, 0.85, 0.95, 1.0], 0.0015)
    P = punto(1.0, 0.0015); aro = tubo(punto(1.0, 0.004), np.tile(nm, (NT, 1)), r=r_aro)
    anillos = [punto(1.0 - 0.5 * t ** 1.5, 0.0005 - prof * t ** 0.8) for t in np.linspace(0, 1, 7)]
    A = np.array(anillos); nr = len(A); idx = []
    for a_ in range(nr - 1):
        for j in range(NT):
            a, bb, cc, d = a_ * NT + j, a_ * NT + (j + 1) % NT, (a_ + 1) * NT + j, (a_ + 1) * NT + (j + 1) % NT
            idx += [(a, cc, bb), (bb, cc, d)]
    fondo = A[-1].mean(0) - nm * 0.004; base = (nr - 1) * NT
    pp = np.vstack([A.reshape(-1, 3), fondo]); idx += [(base + j, nr * NT, base + (j + 1) % NT) for j in range(NT)]
    refl = orientar(pp, np.array(idx), nm)
    emis = disco([0.3 * foco, 0.6 * foco, foco], -0.008)
    def dentro(q):  # puntos dentro del contorno (97 %) y cerca de la superficie: carenado que asomaría tras la mica
        uu, vv, hh = (q - c0) @ e1, (q - c0) @ e2, (q - c0) @ nm
        t = np.arctan2(vv - vc, uu - uc); k = ((t + np.pi) / (2 * np.pi) * NT).astype(int) % NT
        return (np.hypot(uu - uc, vv - vc) < 1.04 * R[k]) & (np.abs(hh - alto(uu, vv)) < 0.035)
    # carcasa negra alrededor de la mica (como el ojo real): tapa el borde serrado del hueco en el carenado
    F_ = [punto(f, dz) for f, dz in ((0.99, 0.004), (1.07, 0.0045), (1.15, 0.0015), (1.2, -0.002))]; A = np.array(F_); idx = []
    for a_ in range(len(A) - 1):
        for j in range(NT):
            a, bb, cc, d = a_ * NT + j, a_ * NT + (j + 1) % NT, (a_ + 1) * NT + j, (a_ + 1) * NT + (j + 1) % NT
            idx += [(a, cc, bb), (bb, cc, d)]
    carcasa = orientar(A.reshape(-1, 3), np.array(idx), nm)
    return mica, aro, refl, emis, dentro, carcasa


salida, hecho, DENTRO = [], set(), []
# ---------- 1. Faros (ojos LED): 4 piezas cada uno
for suf in ("a", "b"):
    nom = "luz.faro_" + suf; mica, aro, refl, emis, dentro, carc = lampara_ajustada(nom); DENTRO.append(dentro)
    salida += [nodo("vidrio.mica_faro_" + suf, mica), nodo("cromo.aro_faro_" + suf, aro), nodo("negro_brillo.carcasa_faro_" + suf, carc, {"doble": True}),
               nodo("cromo.reflector_faro_" + suf, refl, {"doble": True}), nodo(nom, emis, M[nom]["extras"])]
    hecho.add(nom); print(nom, "mica", len(mica[2]), "aro", len(aro[2]), "reflector", len(refl[2]))

# ---------- 2. Stop: emisor recortado, marco negro brillante y copa oscura detrás
m = M["stop.stop"]; nm = m["nor"].mean(0); nm /= np.linalg.norm(nm)
sp, sn, si = recortar(m["pos"], m["idx"], 1); lazo = lazo_borde(sp, si)
marco = tubo(sp[lazo] + sn[lazo] * 0.0008, sn[lazo], r=0.004)
salida += [nodo("stop.stop", (sp, sn, si), m["extras"]), nodo("negro_brillo.marco_stop", marco)]; hecho.add("stop.stop")
print("stop", len(si), "marco", len(marco[2]))


# ---------- 3. Direccionales traseras: mica ámbar atrás (la que se enciende) y carcasa negra brillante
def cortar(pos, nor, idx, n, d):
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
        k = next(k for k in range(3) if s[k] != s[(k + 1) % 3] and s[k] != s[(k + 2) % 3])
        a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]; ab, ac = medio(a, b), medio(a, c)
        solo, par = (0, 1) if s[k] else (1, 0)
        lados[solo].append((a, ab, ac)); lados[par].extend([(ab, b, c), (ab, c, ac)])
    P, N = np.array(P), np.array(N)
    return [compactar(P, N, np.array(l)) for l in lados]


carcasas = []
for suf in ("a", "b"):
    nom = "ambar.direccional_tras_" + suf; m = M[nom]; p = m["pos"]
    x0, x1 = p[:, 0].min(), p[:, 0].max(); xc = x0 + 0.42 * (x1 - x0)
    carc, mica = cortar(p, m["nor"], m["idx"], np.array([1.0, 0, 0]), xc)  # positivo = adelante (carcasa)
    salida.append(nodo(nom, mica, m["extras"])); carcasas.append(carc); hecho.add(nom)
    print(nom, "mica", len(mica[2]), "carcasa", len(carc[2]))
salida.append(nodo("negro_brillo.carcasa_direccionales_tras", unir(carcasas)))

# ---------- 4. Direccionales delanteras: aro cromado fino sobre el borde (tapa el diente del corte)
aros = []
for suf in ("a", "b"):
    m = M["ambar.direccional_del_" + suf]; ps, ii = soldar(m["pos"], m["idx"]); nn = normales(ps, ii)
    lz = lazo_borde(ps, ii)
    if lz: aros.append(tubo(ps[lz] + nn[lz] * 0.0006, nn[lz], r=0.0025))
if aros: salida.append(nodo("cromo.aro_direccionales_del", unir(aros)))

# ---------- 5. Ruedas: pestaña del rin a la medida del talón de la llanta (sin franja), llanta 4 mm dentro de la pestaña
for lado in ("del", "tras"):
    ll = M["caucho.llanta_" + lado]; ex, ey = ll["extras"]["eje"]; rin = M["rin.rin_" + lado]
    p = rin["pos"]; d = p[:, :2] - [ex, ey]; r = np.hypot(*d.T); rmax = np.percentile(r, 99.5)
    lp = ll["pos"]; dl = lp[:, :2] - [ex, ey]; rl = np.hypot(*dl.T); rin_ll, rout = np.percentile(rl, 1), rl.max()
    objetivo = max(rmax, 0.1855)  # 14": asiento 177,8 mm, pestaña ~185 mm
    rh = 0.045; s = (objetivo - rh) / (rmax - rh)
    rn = np.where(r > rh, rh + (r - rh) * s, r); p[:, :2] = [ex, ey] + d * (rn / np.maximum(r, 1e-9))[:, None]
    rin["nor"] = normales(p, rin["idx"]) if False else rin["nor"]
    talon = objetivo - 0.004
    rn2 = np.clip(talon + (rl - rin_ll) * (rout - talon) / (rout - rin_ll), talon * 0.98, None)
    lp[:, :2] = [ex, ey] + dl * (rn2 / np.maximum(rl, 1e-9))[:, None]
    print(f"{lado}: pestaña {rmax:.4f} -> {objetivo:.4f} (x{s:.3f} desde la maza), llanta talón {rin_ll:.4f} -> {talon:.4f}, exterior {rout:.4f}")

# ---------- 6. Acabados PBR propios (Personalizar sigue dando el color)
ACABADOS = {
    "asiento.asiento": {"roughness": 0.62, "sheen": 0.35, "sheenRoughness": 0.5, "clearcoat": 0.12, "clearcoatRoughness": 0.6},
    "plastico.carroceria": {"roughness": 0.78, "metalness": 0},
    "plastico.nariz": {"roughness": 0.7, "metalness": 0},
    "plastico.guardabarros_del": {"roughness": 0.8, "metalness": 0},
    "plastico.portaplaca": {"roughness": 0.85, "metalness": 0},
    "caucho.punos": {"roughness": 0.95, "metalness": 0},
    "oscuro.espejos": {"roughness": 0.35, "metalness": 0.1, "clearcoat": 0.6},
    "rin.rin_del": {"roughness": 0.3, "metalness": 0.7, "clearcoat": 0.5},
    "rin.rin_tras": {"roughness": 0.3, "metalness": 0.7, "clearcoat": 0.5},
}
for nom in ORDEN:
    if nom in hecho: continue
    m = M[nom]
    if nom.split(".")[0] in ("pintura", "plastico", "oscuro") and not m["extras"].get("interno"):
        cen = m["pos"][m["idx"]].mean(1); fuera = ~np.logical_or.reduce([f(cen) for f in DENTRO])
        if (~fuera).any():
            print(nom, "quita", int((~fuera).sum()), "triangulos tras las micas"); m["pos"], m["nor"], m["idx"] = compactar(m["pos"], m["nor"], m["idx"][fuera])
    if nom in ACABADOS and not os.environ.get("SIN_ACABADOS"): m["extras"] = {**m["extras"], "acabado": ACABADOS[nom]}
    salida.append(m)
escribir(SAL, salida, "TallerYa: malla base de IA, limpiada en Blender; luces, rin y acabados (aerox155_tripo2)")
