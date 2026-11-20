# Revision automatica de un GLB ya exportado, ANTES de entregar: luces, pintura, cortes, ruedas y lado.
#   python -I revisar.py S salida.glb [--fotos "ruta/*.jpg;otra/*.webp"] [--hoja hoja.png] [--json res.json] [--nombre "XTZ 150"]
# Saca una sola hoja PNG (resumen + luces encendidas/apagadas + pintura con color de prueba al lado de las fotos +
# cortes marcados + ruedas giradas) y un JSON con cada hallazgo. Tarda ~10-20 s. Nivel por hallazgo: ERROR (no entregar),
# AVISO (mirar en la hoja y decidir), OK. Las coordenadas que imprime son las de la PAGINA: x adelante, y arriba,
# +z = DERECHA del piloto (el GLB guarda +z = izquierda; el visor lo espeja con raiz.scale.z = -1).
import glob
import json
import os
import re
import struct
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

S = sys.argv[1]
sys.path.insert(0, S)
import rend  # noqa: E402

t0 = time.time()


def opcion(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


RUTA = sys.argv[2]
HOJA = opcion("--hoja", os.path.splitext(RUTA)[0] + "_revision.png")
NOMBRE = opcion("--nombre", os.path.basename(RUTA))
hallazgos = []


def anotar(seccion, nivel, texto):
    hallazgos.append({"seccion": seccion, "nivel": nivel, "texto": texto})


def f3(v):
    return "(" + ", ".join(f"{a:.2f}" for a in v) + ")"


# ---------- lectura del GLB (cuantizado, como lo deja exportar.py) -> coordenadas de la pagina ----------
b = open(RUTA, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
j = json.loads(b[20:20 + n])
binb = b[20 + n + 8:]
TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC3": 3, "VEC4": 4, "VEC2": 2}


def acc(i):
    a = j["accessors"][i]
    v = j["bufferViews"][a["bufferView"]]
    t = np.dtype(TIPOS[a["componentType"]])
    nc = NC[a["type"]]
    paso = v.get("byteStride", t.itemsize * nc)
    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    filas = np.ndarray((a["count"], paso // t.itemsize), t, binb, off)[:, :nc].astype(np.float64)
    if a.get("normalized"):
        filas /= {np.int8: 127, np.int16: 32767, np.uint8: 255, np.uint16: 65535}[t.type]
    return filas


nodos = []
for nd in j["nodes"]:
    if "mesh" not in nd:
        continue
    pr = j["meshes"][nd["mesh"]]["primitives"][0]
    P = acc(pr["attributes"]["POSITION"]) * np.array(nd.get("scale", [1, 1, 1])) + np.array(nd.get("translation", [0, 0, 0]))
    N = acc(pr["attributes"]["NORMAL"])
    I = acc(pr["indices"]).astype(np.int64).reshape(-1, 3)
    P[:, 2] *= -1
    N[:, 2] *= -1
    I = I[:, [0, 2, 1]]  # (espejo a la pagina: +z = derecha)
    nombre = nd["name"]
    mat, _, parte = nombre.partition(".")
    ex = nd.get("extras", {})
    nodos.append({"nombre": nombre, "mat": mat, "parte": parte, "ex": ex, "P": P, "N": N, "I": I, "interno": bool(ex.get("interno"))})
vis = [d for d in nodos if not d["interno"]]
todo = np.concatenate([d["P"] for d in vis])
MN, MX = todo.min(0), todo.max(0)
LARGO, ALTO = MX[0] - MN[0], MX[1] - MN[1]


def area_de(d):
    P, I = d["P"], d["I"]
    return float(np.linalg.norm(np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]), axis=1).sum() / 2)


for d in vis:
    d["area"] = area_de(d)


# ---------- rejilla de vecinos (sin scipy): celdas de lado h con la etiqueta del nodo ----------
class Rejilla:
    def __init__(self, P, etiquetas, h):
        self.h = h
        c = np.floor(P / h).astype(np.int64)
        self.cod = self._cod(c)
        orden = np.lexsort((etiquetas, self.cod))
        self.cod, self.et = self.cod[orden], etiquetas[orden]
        u = np.ones(len(self.cod), bool)
        u[1:] = (self.cod[1:] != self.cod[:-1]) | (self.et[1:] != self.et[:-1])
        self.cod, self.et = self.cod[u], self.et[u]

    @staticmethod
    def _cod(c):
        c = c + (1 << 20)
        return (c[:, 0] << 42) | (c[:, 1] << 21) | c[:, 2]

    def etiquetas_cerca(self, Q, excluir=None):
        """Para cada punto, conjunto de etiquetas en las 27 celdas vecinas (distancia < ~2h)."""
        c0 = np.floor(Q / self.h).astype(np.int64)
        res = [set() for _ in range(len(Q))]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cod = self._cod(c0 + np.array([dx, dy, dz]))
                    a = np.searchsorted(self.cod, cod, "left")
                    z = np.searchsorted(self.cod, cod, "right")
                    for i in np.nonzero(z > a)[0]:
                        res[i].update(self.et[a[i]:z[i]].tolist())
        if excluir is not None:
            for i, s in enumerate(res):
                s.discard(excluir)
        return res

    def hay(self, Q, excluir=-1):
        """Booleano: hay alguna etiqueta distinta de `excluir` cerca (vectorizado)."""
        c0 = np.floor(Q / self.h).astype(np.int64)
        si = np.zeros(len(Q), bool)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cod = self._cod(c0 + np.array([dx, dy, dz]))
                    a = np.searchsorted(self.cod, cod, "left")
                    z = np.searchsorted(self.cod, cod, "right")
                    # (en cada celda las etiquetas estan ordenadas y sin repetir: hay otra si son 2+ o la unica no es `excluir`)
                    a_ = np.minimum(a, len(self.et) - 1)
                    si |= (z - a > 1) | ((z > a) & (self.et[a_] != excluir))
        return si


et_todo = np.concatenate([np.full(len(d["P"]), k) for k, d in enumerate(vis)])
REJ = Rejilla(todo, et_todo, 0.0015)  # costuras (los cortes dejan vertices iguales a ambos lados)
REJ_G = Rejilla(todo, et_todo, 0.008)  # vecindad gruesa (lamparas, flotantes)
REJ_M = Rejilla(todo, et_todo, 0.004)  # copias simetricas (~1 cm)


def soldar(P, tol=3e-4):
    q = np.round(P / tol).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    return inv.ravel()


def bordes(d):
    """Aristas de borde (usadas por una sola cara) del nodo, con los vertices soldados."""
    w = soldar(d["P"])
    I = w[d["I"]]
    e = np.sort(np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]), axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    rep = np.zeros(w.max() + 1, np.int64)
    rep[w] = np.arange(len(w))
    return rep[u[c == 1]]  # indices de vertices originales


def componentes(nv, aristas):
    """Etiqueta de componente conexa por vertice (union por enganche y salto de punteros, vectorizado)."""
    e = np.asarray(aristas, np.int64).reshape(-1, 2)
    lab = np.arange(nv)
    while len(e):
        la, lc = lab[e[:, 0]], lab[e[:, 1]]
        if np.array_equal(la, lc):
            break
        m = np.minimum(la, lc)
        np.minimum.at(lab, la, m)
        np.minimum.at(lab, lc, m)
        while True:
            sig = lab[lab]
            if np.array_equal(sig, lab):
                break
            lab = sig
    return lab


# ================= 1) LADO =================
def centro(d):
    return (d["P"].min(0) + d["P"].max(0)) / 2


esc_ = [d for d in vis if re.search(r"escape|silenciador|mofle", d["parte"]) or d["ex"].get("padre") == "escapeFabrica"]
if not esc_:
    anotar("lado", "AVISO", "no hay nodo de escape (escape/silenciador o padre escapeFabrica): no se pudo revisar el lado")
for d in esc_:
    z = centro(d)[2]
    anotar("lado", "OK" if z > 0 else "ERROR", f"{d['nombre']}: centro z pagina {z:+.3f} ({'derecha' if z > 0 else 'IZQUIERDA'}); en el GLB z {-z:+.3f}")
for d in vis:
    if re.search(r"corona|cadena|cvt|transmision|pinon", d["parte"]):
        z = centro(d)[2]
        anotar("lado", "OK" if z < 0 else "ERROR", f"{d['nombre']}: z pagina {z:+.3f} (debe ir a la izquierda, lado contrario al escape)")
    if re.search(r"^disco_", d["parte"]):
        anotar("lado", "INFO", f"{d['nombre']}: a la {'derecha' if centro(d)[2] > 0 else 'izquierda'} (comparar con la foto)")
js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "garaje", "static", "garaje", "js", "moto3d.js")
if os.path.exists(js):
    ok = "raiz.scale.z = -1" in open(js, encoding="utf-8").read()
    anotar("lado", "OK" if ok else "ERROR", "moto3d.js espeja la raiz (scale.z = -1)" if ok else "moto3d.js ya no tiene moto.raiz.scale.z = -1: todo el visor sale en espejo")

# ================= 2) CORTES =================
for d in nodos:
    if "_quitar" in d["nombre"] or d["mat"] == "_quitar":
        anotar("cortes", "ERROR", f"nodo {d['nombre']} exportado: los _quitar no deben llegar al GLB ({len(d['I'])} triangulos)")
huecos_pts, flot_pts, copia_pts = [], [], []
RUEDAS_ = [(d["ex"]["eje"], np.percentile(np.hypot(d["P"][:, 0] - d["ex"]["eje"][0], d["P"][:, 1] - d["ex"]["eje"][1]), 97))
           for d in vis if d["parte"].startswith("llanta") and "eje" in d["ex"]]


def en_rueda(c):
    """Dentro del cilindro de una rueda (lo tapan la llanta torneada y el rin: hueco poco visible)."""
    return any(np.hypot(c[0] - e[0], c[1] - e[1]) < R_ and abs(c[2]) < 0.13 for e, R_ in RUEDAS_)


for k, d in enumerate(vis):
    be = bordes(d)
    if len(be) == 0:
        continue
    ab = ~REJ.hay(d["P"][np.unique(be)], k)
    if ab.mean() > 0.95:
        continue  # (pieza hecha aparte, no cortada de la malla: disco nuevo, carcasa, pantalla; sus bordes son de diseno)
    abiertos = np.unique(be)[ab]
    ea = be[np.isin(be[:, 0], abiertos) & np.isin(be[:, 1], abiertos)]
    if len(ea) == 0:
        continue
    idx = np.unique(ea)
    comp = componentes(len(idx), np.searchsorted(idx, ea))
    ce = comp[np.searchsorted(idx, ea[:, 0])]
    le = np.linalg.norm(d["P"][ea[:, 0]] - d["P"][ea[:, 1]], axis=1)
    lista = []
    for r in np.unique(comp):
        vs = idx[comp == r]
        lon = float(le[ce == r].sum())
        if lon < 0.06:
            continue
        c = d["P"][vs].mean(0)
        huecos_pts.append(d["P"][vs])
        lista.append((lon, c, en_rueda(c)))
    if lista:
        # (un borde abierto chico, o dentro de la rueda, suele ser de Tripo o no se ve; uno grande y a la vista, del corte)
        fuera = [t for t in lista if not t[2]]
        lon, c, _ = max(fuera or lista, key=lambda t: t[0])
        nivel = "ERROR" if fuera and lon >= 0.4 else "AVISO"
        donde = f"{len(fuera)} a la vista" + (f", {len(lista) - len(fuera)} dentro de la rueda" if len(lista) > len(fuera) else "")
        anotar("cortes", nivel, f"{d['nombre']}: {len(lista)} bordes abiertos ({donde}), {sum(t[0] for t in lista) * 100:.0f} cm en total; "
               f"el mayor{' a la vista' if fuera else ''} de {lon * 100:.0f} cm cerca de {f3(c)} (rojo en la hoja)")
# piezas flotantes: componentes conectadas de cada nodo lejos de todo lo demas
for k, d in enumerate(vis):
    w = soldar(d["P"])
    I = w[d["I"]]
    e = np.concatenate([I[:, [0, 1]], I[:, [1, 2]]])
    comp = componentes(w.max() + 1, e)
    cv = comp[w]
    raices, cuenta = np.unique(cv, return_counts=True)
    if len(raices) == 1 and d["parte"].startswith(("disco", "pantalla")):
        continue
    for r, nv in zip(raices, cuenta):
        m = cv == r
        Q = d["P"][m]
        if REJ_G.hay(Q[:: max(1, len(Q) // 400)], k).any():
            continue
        flot_pts.append(Q)
        anotar("cortes", "ERROR" if nv > 30 else "AVISO", f"{'pieza' if nv > 30 else 'astilla'} flotante en {d['nombre']} ({nv} vertices) en {f3(Q.mean(0))}: a mas de ~1,5 cm de todo")
# lo que motor.sobrantes() quito solo al construir (T/quitados.json junto al GLB de la carpeta de trabajo)
rq = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "quitados.json")
if os.path.exists(rq) and os.path.getmtime(rq) <= os.path.getmtime(RUTA) + 600:
    qs = json.load(open(rq, encoding="utf-8"))
    for e in qs:
        anotar("cortes", "INFO", f"quitado solo al construir: {e['motivo']} de {e['pieza']} ({e['caras']} caras) en {f3(e['centro'])} (coord. de la ficha); si sobraba de verdad, nada; si no, CONSERVAR en la ficha")
    if not qs:
        anotar("cortes", "INFO", "limpieza automatica: no habia sobrantes sueltos ni copias del otro lado")
# copias simetricas falsas de Tripo (pieza de un solo lado repetida del otro: el mofle doble de la XTZ)
UN_LADO = r"escape|silenciador|mofle|disco_|mordaza|corona|cadena|cvt|pinon"
for k, d in enumerate(vis):
    if not re.search(UN_LADO, d["parte"]):
        continue
    Q = d["P"][:: max(1, len(d["P"]) // 1500)].copy()
    Q = Q[np.abs(Q[:, 2]) > 0.07]
    if len(Q) < 20:
        continue
    Q[:, 2] *= -1
    cerca = REJ_M.etiquetas_cerca(Q, k)
    frac = np.mean([len(s) > 0 for s in cerca])
    if frac > 0.75:
        quien = {}
        for s in cerca:
            for e in s:
                quien[vis[e]["nombre"]] = quien.get(vis[e]["nombre"], 0) + 1
        top = sorted(quien.items(), key=lambda t: -t[1])[:3]
        copia_pts.append(Q[[len(s) > 0 for s in cerca]])
        anotar("cortes", "AVISO" if frac < 0.92 else "ERROR",
               f"{d['nombre']}: el {frac * 100:.0f} % de su reflejo al otro lado cae sobre otra malla ({', '.join(f'{a} {b}' for a, b in top)}): ¿copia simetrica de Tripo? mirar los dos lados con la foto")

# ================= 3) RUEDAS =================
ROTAN = r"llanta|aro_|rin_|rayos|disco_|tambor|manzana"
for d in vis:
    if not d["parte"].startswith("llanta") or "eje" not in d["ex"]:
        if d["parte"].startswith("llanta"):
            anotar("ruedas", "ERROR", f"{d['nombre']} sin extra eje: no gira ni se tornea")
        continue
    ex, ey = d["ex"]["eje"]
    P = d["P"]
    r = np.hypot(P[:, 0] - ex, P[:, 1] - ey)
    R = np.percentile(r, 97)
    zc = np.median(P[:, 2])
    ancho = np.percentile(np.abs(P[:, 2] - zc), 97)
    cc = (P[r > 0.8 * R].min(0) + P[r > 0.8 * R].max(0)) / 2
    off = np.hypot(cc[0] - ex, cc[1] - ey)
    anotar("ruedas", "OK" if off < 0.015 else "AVISO", f"{d['nombre']}: R {R:.3f}, eje ({ex:.3f}, {ey:.3f}), centro de la banda a {off * 1000:.0f} mm del eje")
    lado = d["parte"].split("_")[-1]
    for o in vis:
        if o is d or not re.search(ROTAN, o["parte"]) or not o["parte"].endswith(lado):
            continue
        Po = o["P"]
        ro = np.hypot(Po[:, 0] - ex, Po[:, 1] - ey)
        lejos = Po[ro > 0.7 * ro.max()]
        ang = np.degrees(np.arctan2(lejos[:, 1] - ey, lejos[:, 0] - ex))
        cub = len(np.unique(np.floor((ang + 180) / 10))) / 36
        if o["parte"].startswith(("aro", "rin", "disco", "tambor")) and cub < 0.97:
            anotar("ruedas", "ERROR", f"{o['nombre']}: cubre solo el {cub * 100:.0f} % de la vuelta: al girar se ve el hueco (lo que falta quedo en otra pieza fija)")
    for k, o in enumerate(vis):
        if o["mat"] not in ("pintura", "pintura2"):
            continue
        Po = o["P"]
        ro = np.hypot(Po[:, 0] - ex, Po[:, 1] - ey)
        dentro = (ro > 0.8 * R) & (ro < 0.985 * R) & (np.abs(Po[:, 2] - zc) < ancho * 0.8)
        if dentro.sum() > 8:
            anotar("ruedas", "ERROR", f"{o['nombre']}: {dentro.sum()} vertices dentro de la llanta {lado}: Personalizar pinta un pedazo de llanta (NKD ronda 2)")

# ================= 4) LUCES =================
lamparas = [d for d in vis if d["ex"].get("lampara")]
MAXIMO = {"faro": (0.04, 0.24), "stop": (0.045, 0.30), "direccional": (0.018, 0.14)}  # (area m2, lado mayor m; NMAX y NKD reales)
MAL_VECINO = r"guardabarros|portaplaca|llanta|placa|basculante|rin_|aro_(del|tras)|escape"
if not lamparas:
    anotar("luces", "ERROR", "ningun nodo con extras.lampara: Encender usa las luces de la moto generica")
tipos = [d["ex"]["lampara"]["tipo"] for d in lamparas]
for t in ("faro", "stop"):
    if t not in tipos:
        anotar("luces", "ERROR", f"falta lampara tipo {t}")
if tipos.count("direccional") not in (0, 4):
    anotar("luces", "AVISO", f"{tipos.count('direccional')} direccionales (lo normal: 4, una por lente y por lado)")
for k0, d in enumerate(lamparas):
    k = vis.index(d)
    t = d["ex"]["lampara"]["tipo"]
    P, I = d["P"], d["I"]
    cr = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
    ar = np.linalg.norm(cr, axis=1) / 2
    pos = (P[I].mean(1) * ar[:, None]).sum(0) / ar.sum()
    dn = cr.sum(0)
    dn /= np.linalg.norm(dn) + 1e-12
    caja = np.ptp(P, axis=0)
    d["pos"], d["dir"] = pos, dn
    txt = f"{d['nombre']} ({t}) en {f3(pos)}, mira {f3(dn)}, {caja[0] * 100:.0f}x{caja[1] * 100:.0f}x{caja[2] * 100:.0f} cm"
    probs = []
    amax, lmax = MAXIMO[t]
    if d["area"] > amax or caja.max() > lmax:
        probs.append(f"demasiado grande para un {t} ({d['area'] * 1e4:.0f} cm2, lado {caja.max() * 100:.0f} cm; tope {amax * 1e4:.0f} cm2 / {lmax * 100:.0f} cm)")
    if t == "faro" and pos[0] < MX[0] - 0.3 * LARGO or t == "stop" and pos[0] > MN[0] + 0.25 * LARGO:
        probs.append("lejos de su sitio (fuera del extremo de la moto)")
    if t == "direccional" and abs(pos[2]) < 0.04:
        probs.append("direccional en el centro (debe ir a un lado)")
    if t == "faro" and dn[0] < 0.4 or t == "stop" and dn[0] > -0.4:
        probs.append(f"no mira {'adelante' if t == 'faro' else 'atras'} (dir x {dn[0]:+.2f}): el haz y el halo salen torcidos")
    if dn[1] < -0.55:
        probs.append(f"mira al piso (dir y {dn[1]:+.2f}): incluye la cara de abajo y la luz cae sobre lo de debajo (stop MT-03)")
    # vecinos por el borde: carcasa e invasiones
    be = np.unique(bordes(d)) if len(P) else []
    cerca = REJ.etiquetas_cerca(P[be], k) if len(be) else []
    cuenta = {}
    for s in cerca:
        for e in s:
            cuenta[e] = cuenta.get(e, 0) + 1
    tot = max(1, len(be))
    if not cuenta:
        probs.append("suelta: no toca ninguna pieza por el borde")
    else:
        e0 = max(cuenta, key=cuenta.get)
        carc = vis[e0]
        txt += f"; carcasa {carc['nombre']} ({cuenta[e0] * 100 // tot} % del borde)"
        if carc["mat"] not in ("luz", "stop", "ambar", "mica_dir") and not carc["parte"].startswith("aro") and d["area"] > 0.8 * carc["area"]:
            probs.append(f"mas grande que su carcasa {carc['nombre']} ({d['area'] * 1e4:.0f} contra {carc['area'] * 1e4:.0f} cm2)")
        for e, c in cuenta.items():
            if re.search(MAL_VECINO, vis[e]["parte"]) and c / tot > 0.2:
                probs.append(f"invade {vis[e]['nombre']} ({c * 100 // tot} % del borde la toca)")
    # a donde cae la luz: punto a 8 cm por la normal (alli el visor pone la luz y el halo)
    foco = pos + dn * 0.08
    s = REJ_G.etiquetas_cerca(foco[None], k)[0]
    s = {vis[e]["nombre"] for e in s if vis[e] not in lamparas}
    if s:
        probs.append(f"la luz (8 cm por su normal) cae sobre {', '.join(sorted(s))}")
    d["probs"] = probs
    anotar("luces", "AVISO" if probs else "OK", txt + ("; " + "; ".join(probs) if probs else ""))

# ================= 4b) SITIO Y PARES (cada pieza donde va segun las fotos; piezas pares completas) =================
# Referencias medidas en el propio GLB: ejes de las ruedas (extras.eje de las llantas) y alto del manubrio.
# Zonas por tipo (x adelante, y arriba, metros de la pagina); --ficha F.py con SITIOS = {regex: (xmin, xmax, ymin, ymax)}
# las reemplaza o suma para una moto (la ficha manda: es lo que el usuario aprobo con las fotos).
ejes = {d["parte"].split("_")[-1]: (d["ex"]["eje"], np.percentile(np.hypot(d["P"][:, 0] - d["ex"]["eje"][0], d["P"][:, 1] - d["ex"]["eje"][1]), 97))
        for d in vis if d["parte"].startswith("llanta") and "eje" in d["ex"]}
if "del" in ejes and "tras" in ejes:
    (xd, yd), Rd = ejes["del"]
    (xt, yt), Rt = ejes["tras"]
    manu = [d for d in vis if re.search(r"manubrio|manillar|punos", d["parte"])]
    y_manu = max(d["P"][:, 1].max() for d in manu) if manu else MN[1] + 0.85 * ALTO
    ZONAS = {  # tipo: (regex sobre "mat.parte", xmin, xmax, ymin, ymax)
        "direccional delantera": (r"direccional_del", xd - 0.30, xd + 0.45, yd + 0.6 * Rd, y_manu + 0.05),
        "direccional trasera": (r"direccional_tras", MN[0] - 0.05, xt - 0.05, yt + 0.5 * Rt, y_manu),
        "faro": (r"luz\.faro", xd - 0.15, MX[0] + 0.02, yd + 0.7 * Rd, y_manu + 0.05),
        "stop": (r"stop|luz\.trasera", MN[0] - 0.02, xt, yt + 0.8 * Rt, y_manu),
        "espejo": (r"espejo", xd - 0.65, xd + 0.25, y_manu - 0.10, MX[1] + 0.02),
        "reposapies": (r"reposapies|estribo|posapie", xt + 0.05, xd - 0.15, MN[1], yd + Rd + 0.10),  # (scooter: piso alto)
    }
    rf = opcion("--ficha")
    if rf:
        import importlib.util
        sp = importlib.util.spec_from_file_location("ficha_rev", rf)
        fm = importlib.util.module_from_spec(sp)
        sys.path.insert(0, os.path.dirname(os.path.abspath(rf)))
        sp.loader.exec_module(fm)
        for k_, z4 in getattr(fm, "SITIOS", {}).items():   # clave = tipo de ZONAS (cambia su caja) o regex nueva
            ZONAS[k_] = (ZONAS[k_][0], *z4) if k_ in ZONAS else (k_, *z4)
    for tipo, (rx, x0, x1, y0, y1) in ZONAS.items():
        for d in vis:
            if not re.search(rx, d["nombre"]) or re.search(r"_base|tallo|soporte", d["parte"]):
                continue
            c = centro(d)
            fuera = []
            if not x0 <= c[0] <= x1:
                fuera.append(f"x {c[0]:+.2f} fuera de {x0:+.2f}..{x1:+.2f}")
            if not y0 <= c[1] <= y1:
                fuera.append(f"y {c[1]:.2f} fuera de {y0:.2f}..{y1:.2f}")
            anotar("sitio", "AVISO" if fuera else "OK", f"{d['nombre']} ({tipo}) en {f3(c)}" + (": " + ", ".join(fuera) + " (comparar con la foto; si esta bien, SITIOS en la ficha)" if fuera else ""))
    # pares: cada pieza de un lado necesita su reflejo (centro reflejado a < 5 cm, mismo tipo)
    PAR = r"direccional|espejo|reposapies|estribo|posapie|posicion|retrovisor"   # (mordaza no: con un disco va sola)
    pares = [d for d in vis if re.search(PAR, d["parte"])]
    for d in pares:
        c = centro(d)
        if abs(c[2]) < 0.04 or np.ptp(d["P"][:, 2]) > 2 * abs(c[2]):
            continue  # (en el centro o una sola malla con los dos lados)
        tipo = re.search(PAR, d["parte"]).group(0)
        otro = [o for o in pares if o is not d and tipo in o["parte"] and np.linalg.norm(centro(o) * [1, 1, -1] - c) < 0.05]
        if otro:
            continue
        lado_ = "derecha" if c[2] > 0 else "izquierda"
        anotar("sitio", "AVISO", f"{d['nombre']} ({lado_}) sin pareja del otro lado a menos de 5 cm: si falta, en la ficha "
               f"m.espejar(\"{d['nombre']}\", \"<nombre del otro lado>\") (copia reflejada en z = 0; si la otra existe pero corrida, mirar la foto)")
else:
    anotar("sitio", "AVISO", "sin llantas con extras.eje: no se pudo revisar el sitio de las piezas")

# ================= 5) PINTURA (tabla) =================
GRUPO = {"pintura": "Color de la moto", "pintura2": "Segundo tono", "chasis": "Color del chasis", "rin": "Color de rines"}
tabla = {}
for d in vis:
    g = GRUPO.get(d["mat"])
    if d["ex"].get("aro"):
        g = "Color de rines"
    tabla.setdefault(g or "fijo", []).append(d["parte"])
for g in GRUPO.values():
    if g in tabla:
        anotar("pintura", "INFO", f"{g}: {', '.join(sorted(tabla[g]))}")
if "Color de la moto" not in tabla:
    anotar("pintura", "ERROR", "ningun nodo pintura.*: Personalizar no cambia el color")

# ================= HOJA =================
PRUEBA = {"pintura": (1.0, 0.0, 0.85), "pintura2": (0.0, 0.85, 1.0), "chasis": (0.1, 0.9, 0.1), "rin": (1.0, 0.85, 0.0)}
BASE = {"caucho": .12, "oscuro": .2, "asiento": .15, "plastico": .22, "motor": .45, "metal": .62, "cromo": .8, "disco": .65,
        "espejo": .75, "luz": .85, "stop": .55, "ambar": .7, "vidrio_oscuro": .3}
ENCENDIDA = {"faro": (3, 3, 2.6), "stop": (3, 0.1, 0.1), "direccional": (3, 1.4, 0)}


def colores(modo, resaltar=None):
    cols = []
    for d in vis:
        nt = len(d["I"])
        if modo == "pintura":
            c = PRUEBA.get("rin" if d["ex"].get("aro") else d["mat"])
            c = c or (BASE.get(d["mat"], .5),) * 3
        else:
            c = (BASE.get(d["mat"], .5),) * 3
            if d["mat"] == "stop":
                c = (.45, .1, .1)
            if d["mat"] == "ambar":
                c = (.6, .4, .1)
            if modo == "encendida" and d["ex"].get("lampara"):
                c = ENCENDIDA[d["ex"]["lampara"]["tipo"]]
        cols.append(np.tile(np.array(c, np.float32), (nt, 1)))
    return np.concatenate(cols)


OFF = np.cumsum([0] + [len(d["P"]) for d in vis])
PT = todo
NT = np.concatenate([d["N"] for d in vis])
IT = np.concatenate([d["I"] + OFF[k] for k, d in enumerate(vis)])


def render(vista_, esc, caja=None, modo="normal", marcas=(), color_marca=(1, 0, 0)):
    cc = colores(modo)
    I = IT
    if caja is not None:
        cen = PT[IT].mean(1)
        m = np.all((cen >= np.array(caja[0]) - 0.02) & (cen <= np.array(caja[1]) + 0.02), axis=1)
        I, cc = IT[m], cc[m]
    if len(I) == 0:
        return Image.new("RGB", (60, 60), (250, 250, 250))
    # marcas (huecos, flotantes, copias): puntos grandes encima, como triangulos chiquitos
    PP, NN, II, CC = PT, NT, I, cc
    extra = [q for q in marcas if len(q)]
    if extra:
        Q = np.concatenate(extra)
        if caja is not None:
            Q = Q[np.all((Q >= np.array(caja[0])) & (Q <= np.array(caja[1])), axis=1)]
        if len(Q):
            r = 1.5 / esc * 3
            tri = np.stack([Q + [r, 0, 0], Q + [0, r, 0], Q + [0, 0, r], Q - [r, 0, 0], Q - [0, r, 0], Q - [0, 0, r]], 1).reshape(-1, 3)
            base = len(PP)
            k = np.arange(len(Q)) * 6 + base
            caras = np.concatenate([np.stack([k, k + 1, k + 2], 1), np.stack([k + 3, k + 4, k + 5], 1), np.stack([k, k + 2, k + 1], 1),
                                    np.stack([k + 3, k + 5, k + 4], 1), np.stack([k + 1, k + 3, k + 2], 1), np.stack([k + 1, k + 2, k + 3], 1)])
            PP = np.concatenate([PP, tri])
            NN = np.concatenate([NN, np.tile([[0, 0, 1.0]], (len(tri), 1))])
            II = np.concatenate([II, caras])
            CC = np.concatenate([CC, np.tile(np.array(color_marca, np.float32) * 2, (len(caras), 1))])
            # (el render descarta las caras de espaldas: se agregan en los dos sentidos)
    if caja is None:
        caja = (MN - 0.03, MX + 0.03)
    return rend.vista(PP, NN, II, CC, vista_, esc, caja, rejilla=False, densidad=0.6)  # (la hoja se achica: 0,6 basta)


def titulo(im, txt, alto=22):
    out = Image.new("RGB", (im.width, im.height + alto), (255, 255, 255))
    out.paste(im, (0, alto))
    ImageDraw.Draw(out).text((4, 5), txt, fill=(20, 20, 20))
    return out


def fila(ims, ancho=1500, alto_max=420):
    ims = [i for i in ims if i is not None]
    if not ims:
        return None
    h = min(alto_max, max(i.height for i in ims))
    ims = [i.resize((max(1, int(i.width * h / i.height)), h)) for i in ims]
    tot = sum(i.width for i in ims)
    if tot > ancho:
        f = ancho / tot
        ims = [i.resize((max(1, int(i.width * f)), max(1, int(i.height * f)))) for i in ims]
    out = Image.new("RGB", (ancho, max(i.height for i in ims)), (255, 255, 255))
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + 4
    return out


secciones = []
# --- luces: grupo delantero y trasero, apagada y encendida, de frente/atras, de lado y desde arriba
for nom, sel in (("delanteras", lambda d: d["pos"][0] > 0), ("traseras", lambda d: d["pos"][0] <= 0)):
    ls = [d for d in lamparas if sel(d)]
    if not ls:
        continue
    pts = np.concatenate([d["P"] for d in ls])
    lo, hi = pts.min(0) - 0.07, pts.max(0) + 0.07
    lo[2], hi[2] = min(lo[2], -hi[2]), max(hi[2], -lo[2])
    fr = "frente" if nom == "delanteras" else "atras"
    tiles = []
    for v in (fr, "der", "arriba"):
        cj = (lo, hi) if v != "der" else (np.array([lo[0], lo[1], -1]), np.array([hi[0], hi[1], 1]))
        span = max(np.ptp(np.array(cj), axis=0)[[2 if v == fr else 0, 1 if v != "arriba" else 2]])
        esc = min(1400, 330 / max(span, 0.05))
        focos = [np.array([d["pos"] + d["dir"] * 0.08]).repeat(3, 0) for d in ls]
        tiles.append(titulo(render(v, esc, cj, "apagada"), f"{nom} {v} apagada"))
        tiles.append(titulo(render(v, esc, cj, "encendida", focos, (0, 0.4, 1)), f"{nom} {v} encendida (azul: a donde cae la luz)"))
    secciones.append(("Luces " + nom, [fila(tiles[:4]), fila(tiles[4:])]))
# --- pintura: color de prueba en cada grupo + fotos reales
vistas_p = [titulo(render(v, 260, None, "pintura"), v) for v in ("der", "izq")]
vistas_p2 = [titulo(render(v, 260, None, "pintura"), v) for v in ("frente", "atras", "arriba")]
fotos = []
for patron in (opcion("--fotos") or "").split(";"):
    if patron.strip():
        fotos += sorted(glob.glob(patron.strip()))
fims = []
for f in fotos[:8]:
    try:
        fims.append(titulo(Image.open(f).convert("RGB"), os.path.basename(f)[:40]))
    except OSError:
        pass
if len(fims) < 3:
    anotar("pintura", "ERROR", f"solo {len(fims)} fotos reales en la hoja (minimo 3, de varios colores o angulos): --fotos")
leyenda = Image.new("RGB", (330, 150), (255, 255, 255))
dr = ImageDraw.Draw(leyenda)
for i, (g, c) in enumerate(PRUEBA.items()):
    dr.rectangle([6, 8 + i * 26, 30, 28 + i * 26], fill=tuple(int(v * 255) for v in c))
    dr.text((38, 12 + i * 26), {"pintura": "Color de la moto (pintura)", "pintura2": "Segundo tono (pintura2)", "chasis": "Color del chasis",
                                "rin": "Color de rines (rin.* y aro)"}[g], fill=(0, 0, 0))
dr.text((6, 118), "gris: no cambia con Personalizar", fill=(0, 0, 0))
secciones.append(("Pintura: color de prueba contra fotos reales", [fila(vistas_p + [leyenda]), fila(vistas_p2), fila(fims[:4], alto_max=300), fila(fims[4:8], alto_max=300)]))
# --- cortes: huecos (rojo), flotantes (azul), copias simetricas (naranja)
marc = [titulo(render(v, 260, None, "normal", huecos_pts + flot_pts + copia_pts, (1, 0, 0)), f"{v} (rojo: bordes abiertos, flotantes y reflejos sospechosos)") for v in ("der", "izq", "abajo")]
secciones.append(("Cortes", [fila(marc[:2]), fila(marc[2:])]))
# --- ruedas giradas 45 grados (sin la llanta, que glb.js tornea): lo que no gire entero se ve como hueco
tiles = []
for d in vis:
    if not d["parte"].startswith("llanta") or "eje" not in d["ex"]:
        continue
    ex, ey = d["ex"]["eje"]
    lado = d["parte"].split("_")[-1]
    R = np.percentile(np.hypot(d["P"][:, 0] - ex, d["P"][:, 1] - ey), 97)
    cj = (np.array([ex - R - .03, ey - R - .03, -1]), np.array([ex + R + .03, ey + R + .03, 1]))
    for ang in (0, 45):
        a = np.radians(ang)
        guard = PT.copy()
        for k, o in enumerate(vis):
            if re.search(ROTAN, o["parte"]) and o["parte"].endswith(lado):
                sl = slice(OFF[k], OFF[k + 1])
                x, y = PT[sl, 0] - ex, PT[sl, 1] - ey
                PT[sl, 0] = ex + x * np.cos(a) - y * np.sin(a)
                PT[sl, 1] = ey + x * np.sin(a) + y * np.cos(a)
        tiles.append(titulo(render("der", 330 / (2 * R + .06), cj), f"rueda {lado} girada {ang} grados"))
        PT[:] = guard
secciones.append(("Ruedas", [fila(tiles)]))

# --- resumen arriba
niveles = {s: max((h["nivel"] for h in hallazgos if h["seccion"] == s), key=["INFO", "OK", "AVISO", "ERROR"].index, default="OK")
           for s in ("luces", "sitio", "pintura", "cortes", "ruedas", "lado")}
for s in niveles:
    if niveles[s] == "INFO":
        niveles[s] = "OK"
lineas = [f"Revision de {NOMBRE}  -  {time.strftime('%Y-%m-%d %H:%M')}  -  {len(vis)} piezas visibles",
          "   ".join(f"{s.upper()}: {v}" for s, v in niveles.items()), ""]
def a_la_vista(h):   # errores, avisos y lo que la limpieza automatica quito (para poder pedir CONSERVAR)
    return h["nivel"] in ("ERROR", "AVISO") or h["texto"].startswith(("quitado solo", "limpieza"))


for h in hallazgos:
    if a_la_vista(h):
        lineas.append(f"[{h['nivel']}] {h['seccion']}: {h['texto']}"[:230])
res = Image.new("RGB", (1500, 16 * len(lineas) + 16), (255, 255, 255))
dr = ImageDraw.Draw(res)
for i, l in enumerate(lineas):
    dr.text((8, 8 + i * 16), l, fill=(180, 0, 0) if l.startswith("[ERROR") else (150, 90, 0) if l.startswith("[AVISO") else (0, 0, 0))
bloques = [res]
for t, fs in secciones:
    cab = Image.new("RGB", (1500, 26), (40, 60, 90))
    ImageDraw.Draw(cab).text((8, 7), t.upper() + f"  -  {niveles.get(t.split()[0].lower().rstrip(':'), '')}", fill=(255, 255, 255))
    bloques += [cab] + [f for f in fs if f is not None]
H = sum(i.height for i in bloques)
hoja = Image.new("RGB", (1500, H), (255, 255, 255))
y = 0
for i in bloques:
    hoja.paste(i, (0, y))
    y += i.height
os.makedirs(os.path.dirname(os.path.abspath(HOJA)), exist_ok=True)
hoja.save(HOJA, quality=85)
salida_json = opcion("--json", os.path.splitext(HOJA)[0] + ".json")
json.dump({"glb": RUTA, "niveles": niveles, "hallazgos": hallazgos, "pintura": tabla}, open(salida_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{NOMBRE}: " + "  ".join(f"{s} {v}" for s, v in niveles.items()) + f"   ({time.time() - t0:.1f} s)")
for h in hallazgos:
    if a_la_vista(h):
        print(f"  [{h['nivel']}] {h['seccion']}: {h['texto']}"[:260])
print("hoja", HOJA, hoja.size)
