"""Del despiece (despiece.npz) al GLB del visor: materiales «material.parte», extras, piezas internas de Rayos X
(construidas aquí: Tripo no las trae) y cuantización KHR_mesh_quantization (posiciones int16, normales int8).
Uso: python -I construir.py  → garaje/static/garaje/modelos/xr190l_tripo2.glb y privado/tripo/xr190l/final.npz"""
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from comun import RAIZ, TRABAJO, normales_cara  # noqa: E402

SALIDA = RAIZ / "garaje/static/garaje/modelos/xr190l_tripo2.glb"

# pieza → (material del visor, color aproximado para el render de control, extras)
ROJO, BLANCO, NEGRO, PLATA, GRIS = (200, 30, 35), (236, 236, 232), (30, 32, 34), (190, 195, 198), (95, 92, 90)
# Materiales por lo que es cada superficie en una XR 190L real (no por el color de la foto): color base limpio de fábrica,
# roughness y metalness propios. Las piezas rojas siguen el color de Personalizar (acabado sin tono).
PLASTICO_INY = {"metalness": 0.0, "roughness": 0.36, "clearcoat": 0.35, "clearcoatRoughness": 0.22}  # PP inyectado brillante
NEGRO_MATE = {"metalness": 0.0, "roughness": 0.78}  # plástico negro texturizado
PINTURA_NEGRA = {"metalness": 0.05, "roughness": 0.28, "clearcoat": 0.8, "clearcoatRoughness": 0.12}  # pintura sobre acero
ALUMINIO = {"metalness": 0.85, "roughness": 0.34}
MAPA = {
    "llanta_del": ("caucho", (25, 25, 25), {"pieza": "llanta_del"}),
    "llanta_tras": ("caucho", (25, 25, 25), {"pieza": "llanta_tras"}),
    "aro_del": ("disco", PLATA, {"pieza": "llanta_del", "tono": "#c6cacd", "acabado": ALUMINIO}),
    "aro_tras": ("disco", PLATA, {"pieza": "llanta_tras", "tono": "#c6cacd", "acabado": ALUMINIO}),
    "rayos_del": ("cromo", (215, 218, 220), {"pieza": "llanta_del", "rin": True}),
    "rayos_tras": ("cromo", (215, 218, 220), {"pieza": "llanta_tras", "rin": True}),
    "disco_del": ("disco", (185, 190, 193), {"pieza": "freno_del", "tono": "#9da2a6", "acabado": {"metalness": 0.9, "roughness": 0.42}}),
    "corona": ("metal", PLATA, {"pieza": "cadena", "tono": "#8f9498", "acabado": {"metalness": 0.9, "roughness": 0.45}}),
    "horquilla_baja": ("metal", PLATA, {"pieza": "suspension_del", "tono": "#b9bdc0", "acabado": {"metalness": 0.75, "roughness": 0.4}}),
    "horquilla_alta": ("oscuro", NEGRO, {"pieza": "suspension_del", "tono": "#1b1c1e", "acabado": {"metalness": 0.0, "roughness": 0.72}}),
    "mascara": ("pintura", ROJO, {"rol": "visor_fijo", "acabado": PLASTICO_INY}),
    "espejos": ("oscuro", NEGRO, {"padre": "espejos.fabrica", "tono": "#18191b", "acabado": {"metalness": 0.0, "roughness": 0.45}}),
    "punos": ("caucho", (25, 25, 25), {}),
    "manubrio": ("oscuro", NEGRO, {"tono": "#1d1f22", "acabado": PINTURA_NEGRA}),
    "guardabarros_del": ("pintura", ROJO, {"acabado": PLASTICO_INY}),
    "parrilla": ("oscuro", NEGRO, {"tono": "#1d1f22", "acabado": PINTURA_NEGRA}),
    "colin": ("pintura", ROJO, {"acabado": PLASTICO_INY}),
    "guardabarros_tras": ("plastico", NEGRO, {"tono": "#1c1d1f", "acabado": NEGRO_MATE}),
    "portaplaca": ("plastico", NEGRO, {"tono": "#1c1d1f", "acabado": NEGRO_MATE}),
    "asiento": ("asiento", (22, 24, 25), {"tono": "#151617", "acabado": {"roughness": 0.62, "clearcoat": 0.2, "clearcoatRoughness": 0.5}}),
    "tanque": ("pintura", NEGRO, {"tono": "#141518", "acabado": PINTURA_NEGRA}),
    "aletas": ("pintura", ROJO, {"zonas": ["tanque"], "acabado": PLASTICO_INY}),
    "tapa_lateral": ("blanco", (198, 200, 205), {"zonas": ["lateral"], "tono": "#e2e3df", "acabado": {"metalness": 0.0, "roughness": 0.38, "clearcoat": 0.3, "clearcoatRoughness": 0.22}}),
    "cubierta_trasera": ("plastico", NEGRO, {"tono": "#1c1d1f", "acabado": NEGRO_MATE}),
    # (padre escapeFabrica: reemplaza al escape genérico del visor, que quedaba encima del colín)
    "escape": ("oscuro", (45, 45, 45), {"tono": "#202124", "padre": "escapeFabrica", "acabado": {"metalness": 0.25, "roughness": 0.62}}),
    "basculante": ("disco", PLATA, {"tono": "#b4b8bc", "acabado": {"metalness": 0.6, "roughness": 0.36}}),
    "amortiguador": ("oscuro", NEGRO, {"pieza": "suspension_tras", "tono": "#1f2023", "acabado": {"metalness": 0.3, "roughness": 0.5}}),
    "estribos": ("oscuro", NEGRO, {"tono": "#1d1f22", "acabado": {"metalness": 0.3, "roughness": 0.6}}),
    "motor": ("oscuro", (48, 50, 54), {"pieza": "motor", "tono": "#2b2d30", "acabado": {"metalness": 0.45, "roughness": 0.48}}),
    # (tono en chasis: el visor lo vuelve «chasis a la vista» de fábrica, que Personalizar respeta)
    "chasis": ("chasis", NEGRO, {"tono": "#1e2023", "acabado": PINTURA_NEGRA}),
}


# ---------- Primitivas para las piezas internas (formas reales, no cajas) ----------
def torno(perfil, n=28):
    """Sólido de revolución alrededor de y: perfil [(r, y)]. Devuelve V, F."""
    perfil = np.asarray(perfil, float)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    V = np.array([[r * np.cos(t), yy, r * np.sin(t)] for r, yy in perfil for t in a])
    F = []
    m = len(perfil)
    for i in range(m - 1):
        for j in range(n):
            p, q = i * n + j, i * n + (j + 1) % n
            F += [[p, p + n, q], [q, p + n, q + n]]
    # tapas
    V = np.vstack([V, [[0, perfil[0, 1], 0], [0, perfil[-1, 1], 0]]])
    c0, c1 = len(V) - 2, len(V) - 1
    for j in range(n):
        F += [[c0, (j + 1) % n, j], [c1, (m - 1) * n + j, (m - 1) * n + (j + 1) % n]]
    return V, np.array(F)


def superelipsoide(sx, sy, sz, e=0.25, n=20):
    """Bloque redondeado (cajas de filtro, batería, culata): esquinas suaves, no una caja."""
    u = np.linspace(-np.pi / 2, np.pi / 2, n)
    v = np.linspace(-np.pi, np.pi, 2 * n, endpoint=False)
    f = lambda w, p: np.sign(w) * np.abs(w) ** p  # noqa: E731
    V = []
    for a in u:
        for b in v:
            V.append([sx * f(np.cos(a), e) * f(np.cos(b), e), sy * f(np.sin(a), e), sz * f(np.cos(a), e) * f(np.sin(b), e)])
    F = []
    m = 2 * n
    for i in range(n - 1):
        for j in range(m):
            p, q = i * m + j, i * m + (j + 1) % m
            F += [[p, q, p + m], [q, q + m, p + m]]
    return np.array(V), np.array(F)


def engranaje(r, ancho, dientes, n_sub=3):
    """Piñón extruido en z con dientes."""
    k = dientes * n_sub * 2
    t = np.linspace(0, 2 * np.pi, k, endpoint=False)
    rr = np.where((np.arange(k) // n_sub) % 2 == 0, r, r * 0.88)
    anillo = np.stack([rr * np.cos(t), rr * np.sin(t)], 1)
    V = np.vstack([np.c_[anillo, np.full(k, -ancho / 2)], np.c_[anillo, np.full(k, ancho / 2)], [[0, 0, -ancho / 2], [0, 0, ancho / 2]]])
    F = []
    for j in range(k):
        a, b = j, (j + 1) % k
        F += [[a, b, a + k], [b, b + k, a + k], [2 * k, b, a], [2 * k + 1, a + k, b + k]]
    return V, np.array(F)


def tubo(puntos, r, n=8):
    """Barrido de un círculo por una polilínea (cables, ductos)."""
    P = np.asarray(puntos, float)
    V, F = [], []
    for i, p in enumerate(P):
        d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        a = np.cross(d, [0, 1, 0]) if abs(d[1]) < 0.9 else np.cross(d, [1, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(d, a)
        for t in np.linspace(0, 2 * np.pi, n, endpoint=False):
            V.append(p + r * (np.cos(t) * a + np.sin(t) * b))
    for i in range(len(P) - 1):
        for j in range(n):
            p, q = i * n + j, i * n + (j + 1) % n
            F += [[p, q, p + n], [q, q + n, p + n]]
    return np.array(V), np.array(F)


def colocar(VF, centro, giro_z=0.0, giro_x=0.0):
    V, F = VF
    cz, sz, cx, sx = np.cos(giro_z), np.sin(giro_z), np.cos(giro_x), np.sin(giro_x)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return V @ (Rz @ Rx).T + np.asarray(centro), F


def unir(*partes):
    Vs, Fs, o = [], [], 0
    for V, F in partes:
        Vs.append(V); Fs.append(F + o); o += len(V)
    return np.vstack(Vs), np.vstack(Fs)


def internos():
    """Componentes internos de la XR 190L (monocilíndrico OHC enfriado por aire, 184 cc, inclinado ~15° adelante)."""
    inc = -np.radians(15)  # (cilindro inclinado hacia adelante: giro en z negativo lleva +y hacia +x)
    base = np.array([0.075, 0.43, 0.0])
    eje = np.array([np.sin(-inc), np.cos(inc), 0])
    # Cilindro con aletas: perfil de dientes de sierra (aletas) alrededor de la camisa
    perfil = [(0.034, 0.0)]
    for i in range(9):
        y0 = 0.012 + i * 0.019
        perfil += [(0.040, y0), (0.068, y0 + 0.002), (0.068, y0 + 0.008), (0.040, y0 + 0.010)]
    perfil += [(0.040, 0.185), (0.034, 0.19)]
    out = {
        "motor.motor_cilindro": colocar(torno(perfil, 32), base, inc),
        "cromo.motor_piston": colocar(torno([(0.0315, 0.0), (0.0315, 0.045), (0.028, 0.05)], 24), base + eje * 0.07, inc),
        "metal.motor_biela": colocar(tubo([[0, 0, 0], [0, 0.11, 0]], 0.009, 8), base + eje * -0.04, inc),
        "motor.motor_culata": colocar(superelipsoide(0.075, 0.038, 0.072, 0.3), base + eje * 0.225, inc),
        "oscuro.motor_tapa_valvulas": colocar(superelipsoide(0.05, 0.022, 0.05, 0.35), base + eje * 0.27, inc),
        "metal.motor_ciguenal": unir(colocar(engranaje(0.058, 0.014, 1, 1), [0.06, 0.36, 0.022]),
                                      colocar(engranaje(0.058, 0.014, 1, 1), [0.06, 0.36, -0.022]),
                                      colocar(tubo([[0.06, 0.36, -0.07], [0.06, 0.36, 0.07]], 0.012), [0, 0, 0])),
        "metal.transmision": unir(*[colocar(engranaje(r, 0.012, d), [x, yy, zz]) for r, d, x, yy, zz in (
            (0.040, 22, -0.06, 0.33, 0.035), (0.028, 16, -0.06, 0.33, 0.0), (0.034, 19, -0.06, 0.33, -0.035),
            (0.030, 17, -0.125, 0.30, 0.035), (0.042, 24, -0.125, 0.30, 0.0), (0.036, 20, -0.125, 0.30, -0.035))]),
        "carter.embrague": colocar(engranaje(0.055, 0.02, 30), [0.0, 0.34, 0.085]),
        "bujia.bujia_aislador": colocar(torno([(0.006, 0), (0.007, 0.03), (0.005, 0.045)], 12), base + eje * 0.2 + [0.05, 0.0, 0.0], inc - 1.2),
        "oscuro.bujia_capuchon": colocar(tubo([[0, 0, 0], [0.02, 0.04, 0], [0.0, 0.10, 0]], 0.011), base + eje * 0.2 + [0.07, 0.02, 0], 0),
        # Admisión: carburador, ducto y caja del filtro bajo el asiento
        "oscuro.filtro_caja": colocar(superelipsoide(0.12, 0.085, 0.085, 0.35), [-0.33, 0.68, 0.0]),
        "bujia.filtro_elemento": colocar(torno([(0.05, 0), (0.055, 0.012)] + [(0.055 if i % 2 else 0.047, 0.012 + i * 0.006) for i in range(16)] + [(0.05, 0.11)], 24), [-0.27, 0.68, -0.055], 0, np.pi / 2),
        "caucho.filtro_ducto": tubo([[-0.21, 0.66, 0.0], [-0.14, 0.62, 0.0], [-0.06, 0.60, 0.0], [0.02, 0.59, 0.0]], 0.024, 12),
        "metal.carburador": colocar(torno([(0.026, 0), (0.03, 0.02), (0.03, 0.05), (0.022, 0.06)], 16), [0.03, 0.585, 0.0], np.pi / 2 - 0.15),
        # Batería (YTX5L: 113 × 70 × 105 mm) con bornes, tras la tapa lateral derecha
        "bateria.bat_cuerpo": colocar(superelipsoide(0.035, 0.052, 0.056, 0.12), [-0.18, 0.66, 0.07]),
        "metal.bat_bornes": unir(colocar(torno([(0.008, 0), (0.008, 0.014)], 10), [-0.18, 0.712, 0.10]),
                                 colocar(torno([(0.008, 0), (0.008, 0.014)], 10), [-0.18, 0.712, 0.04])),
        # Cableado básico: del faro por la espina del chasis a la batería, y a la bobina/bujía
        "rojo.cableado": unir(tubo([[0.42, 0.92, 0.02], [0.30, 0.88, 0.03], [0.12, 0.84, 0.03], [-0.05, 0.78, 0.04], [-0.15, 0.73, 0.06], [-0.18, 0.72, 0.10]], 0.005),
                              tubo([[-0.18, 0.72, 0.04], [-0.10, 0.72, -0.02], [0.05, 0.74, -0.04], [0.14, 0.70, -0.03], [0.17, 0.64, 0.0]], 0.004)),
        "oscuro.cableado_tras": tubo([[-0.18, 0.72, 0.07], [-0.45, 0.80, 0.05], [-0.75, 0.86, 0.03], [-0.92, 0.86, 0.0]], 0.005),
    }
    return out


def suavizar_normales(V, F):
    nC, a = normales_cara(V, F)
    nV = np.zeros_like(V)
    for k in range(3):
        np.add.at(nV, F[:, k], nC * a[:, None])
    return nV / np.maximum(np.linalg.norm(nV, axis=1), 1e-12)[:, None]


# Alto: el Tripo sale ~3 % más bajo que la foto lateral a igual largo (borde de tanque, máscara, parrilla y llantas
# quedan cortos arriba y abajo); se estira solo en y al escribir, piezas internas y luces incluidas.
ALTO = 1.0  # (sin estirar: así la moto coincide con la ficha, 1.125 contra 1.124 mm de alto)


def estirar_alto(nodos):
    out = []
    for nombre, V, N, F, ex in nodos:
        V = V * [1, ALTO, 1]
        N = N * [ALTO, 1, ALTO]  # (normales: inversa transpuesta del estiramiento)
        N = N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
        ex = json.loads(json.dumps(ex))
        if "eje" in ex:
            ex["eje"][1] = round(ex["eje"][1] * ALTO, 4)
        if "manubrio" in ex:
            ex["manubrio"]["y"] = round(ex["manubrio"]["y"] * ALTO, 3)
        if "placa" in ex:
            ex["placa"]["c"][1] = round(ex["placa"]["c"][1] * ALTO, 3)
        out.append((nombre, V, N, F, ex))
    return out


def escribir_glb(nodos, ruta):
    """nodos: [(nombre, V, N, F, extras)] en coordenadas de la moto → GLB cuantizado."""
    nodos = estirar_alto(nodos)
    blob, vistas, accs, gn, gm = bytearray(), [], [], [], []

    def agregar(datos, objetivo, stride=None):
        while len(blob) % 4:
            blob.append(0)
        vistas.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(datos), **({"target": objetivo} if objetivo else {}),
                       **({"byteStride": stride} if stride else {})})
        blob.extend(datos)
        return len(vistas) - 1

    for nombre, V, N, F, extras in nodos:
        lo, hi = V.min(0), V.max(0)
        t = (lo + hi) / 2
        s = max(float((hi - lo).max() / 2), 1e-6)
        q = np.round((V - t) / s * 32767).clip(-32767, 32767).astype(np.int16)
        pos = np.zeros((len(V), 4), np.int16); pos[:, :3] = q
        nq = np.zeros((len(V), 4), np.int8); nq[:, :3] = np.round(N * 127).clip(-127, 127)
        ind = F.astype(np.uint16 if len(V) < 65536 else np.uint32).ravel()
        bp = agregar(pos.tobytes(), 34962, 8)
        bn = agregar(nq.tobytes(), 34962, 4)
        bi = agregar(ind.tobytes(), 34963)
        accs += [{"bufferView": bp, "componentType": 5122, "normalized": True, "count": len(V), "type": "VEC3",
                  "min": q.min(0).tolist(), "max": q.max(0).tolist()},
                 {"bufferView": bn, "componentType": 5120, "normalized": True, "count": len(V), "type": "VEC3"},
                 {"bufferView": bi, "componentType": 5123 if len(V) < 65536 else 5125, "count": len(ind), "type": "SCALAR"}]
        k = len(accs) - 3
        gm.append({"name": nombre, "primitives": [{"attributes": {"POSITION": k, "NORMAL": k + 1}, "indices": k + 2}]})
        gn.append({"name": nombre, "mesh": len(gm) - 1, "translation": t.round(5).tolist(), "scale": [s, s, s], "extras": extras})
    g = {"asset": {"version": "2.0", "generator": "TallerYa: XR 190L desde Tripo (método herramientas_3d/xr190l)"},
         "extensionsUsed": ["KHR_mesh_quantization"], "extensionsRequired": ["KHR_mesh_quantization"],
         "scene": 0, "scenes": [{"nodes": list(range(len(gn)))}], "nodes": gn, "meshes": gm,
         "accessors": accs, "bufferViews": vistas, "buffers": [{"byteLength": len(blob)}]}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    while len(blob) % 4:
        blob.append(0)
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(ruta, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(blob), 0x004E4942)); f.write(bytes(blob))
    return total


def domo(R, h, d, centro, sy=1.0, n=24):
    """Lente abombado sin tapa trasera (así la suma de normales mira hacia d, que es lo que lee lamparaDe).
    R radio, h abombado, sy aplasta el lente en y (lentes ovalados)."""
    perfil = [(R, 0.0), (R * 0.97, h * 0.3), (R * 0.85, h * 0.6), (R * 0.6, h * 0.85), (R * 0.3, h * 0.97), (0.0, h)]
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    V = np.array([[r * np.cos(t), yy, r * np.sin(t)] for r, yy in perfil for t in a])
    F = []
    for i in range(len(perfil) - 1):
        for j in range(n):
            p, q = i * n + j, i * n + (j + 1) % n
            F += [[p, p + n, q], [q, p + n, q + n]]
    V[:, 0] *= 1.0
    V[:, 2] *= sy  # (z local: alto del lente después de girar)
    return alinear(V, d, centro), np.array(F)


def anillo(R, ancho, grosor, d, centro, sy=1.0, n=24):
    """Aro del lente (borde): tubo corto alrededor del eje d."""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    perfil = [(R, -ancho), (R + grosor, -ancho), (R + grosor, 0.002), (R, 0.002)]
    V = np.array([[r * np.cos(t), yy, r * np.sin(t)] for r, yy in perfil for t in a])
    F = []
    for i in range(4):
        for j in range(n):
            p, q = i * n + j, i * n + (j + 1) % n
            pp, qq = ((i + 1) % 4) * n + j, ((i + 1) % 4) * n + (j + 1) % n
            F += [[p, pp, q], [q, pp, qq]]
    V[:, 2] *= sy
    return alinear(V, d, centro), np.array(F)


def alinear(V, d, centro):
    """Lleva el eje y local a la dirección d (el z local queda vertical cuando se puede)."""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    arriba = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    ex = np.cross(arriba, d); ex /= np.linalg.norm(ex)
    ez = np.cross(ex, d)
    return V[:, [0]] * ex + V[:, [1]] * d + V[:, [2]] * ez + np.asarray(centro)


def placa_de(Vp, Fp):
    """Placa sobre la cara trasera del portaplaca: centro, inclinación (rad) y tamaño de la placa colombiana de moto."""
    nC, a = normales_cara(Vp, Fp)
    atras = nC[:, 0] < -0.5
    c = (Vp[Fp[atras]].mean(1) * a[atras, None]).sum(0) / a[atras].sum()
    n = (nC[atras] * a[atras, None]).sum(0)
    incl = float(np.arctan2(-n[1], -n[0]))
    return {"c": [round(float(c[0]) - 0.006, 3), round(float(c[1]), 3), 0], "incl": round(-abs(incl), 3), "tam": [0.17, 0.12]}


def luces(W, F, lab):
    """Faro, stop y 4 direccionales como piezas limpias (lente abombado y aro), en el sitio de la malla de Tripo."""
    nC, _ = normales_cara(W, F)
    C = W[F].mean(1)
    out = {}
    # Faro: frente de la máscara que mira adelante
    m = (lab == "mascara") & (nC[:, 0] > 0.6) & (C[:, 1] > 0.86) & (C[:, 1] < 1.02) & (np.abs(C[:, 2]) < 0.07)
    cf = C[m].mean(0); cf[2] = 0.0
    xf = C[m][:, 0].max()
    d = np.array([1.0, -0.12, 0.0])
    out["luz.faro"] = (domo(0.05, 0.016, d, [xf - 0.004, cf[1], 0], sy=0.8), {"lampara": {"tipo": "faro"}})
    out["faro.faro_aro"] = (anillo(0.05, 0.02, 0.008, d, [xf - 0.004, cf[1], 0], sy=0.8), {})
    # Stop: punta trasera del colín
    m = (W[:, 0] < -0.85) & (W[:, 1] > 0.78) & (W[:, 1] < 0.98) & (np.abs(W[:, 2]) < 0.06)
    xs = W[m][:, 0].min(); ys = W[m][W[m][:, 0] < xs + 0.03][:, 1].mean()
    out["stop.stop"] = (domo(0.034, 0.012, [-1, 0.05, 0], [xs + 0.004, ys - 0.01, 0], sy=0.55), {"lampara": {"tipo": "stop"}, "tono": "#b3121a", "emisivo": "#ff0a0a"})
    out["plastico.stop_aro"] = (anillo(0.034, 0.018, 0.006, [-1, 0.05, 0], [xs + 0.004, ys - 0.01, 0], sy=0.55), {})
    # Direccionales: cuerpo con tallo, lente ámbar mirando adelante (las de adelante) o atrás
    mk = lab == "mascara"
    zmask = np.abs(W[F[mk]].reshape(-1, 3)[:, 2]).max()
    xmask = W[F[mk]].reshape(-1, 3)[:, 0].min()
    for nombre, x0, y0, z0, dx in (("del", xmask + 0.05, 0.90, zmask + 0.035, 1), ("tras", xs + 0.06, ys - 0.03, 0.115, -1)):
        for lado in (1, -1):
            c = np.array([x0, y0, lado * z0])
            d = np.array([dx, 0, lado * 0.25])
            out[f"ambar.direccional_{nombre}_{'i' if lado > 0 else 'd'}"] = (domo(0.018, 0.02, d, c + 0.012 * d / np.linalg.norm(d), sy=0.75), {"lampara": {"tipo": "direccional"}})
            cuerpo = torno([(0.0, -0.035), (0.016, -0.03), (0.019, -0.012), (0.019, 0.0)], 16)
            out[f"oscuro.direccional_{nombre}_{'i' if lado > 0 else 'd'}_cuerpo"] = ((alinear(cuerpo[0], d, c + 0.012 * d / np.linalg.norm(d)), cuerpo[1]), {})
            out[f"oscuro.direccional_{nombre}_{'i' if lado > 0 else 'd'}_tallo"] = (tubo([c - np.array([0, 0, lado * 0.045]), c - 0.02 * d / np.linalg.norm(d)], 0.006), {})
    return out


if __name__ == "__main__":
    d = np.load(TRABAJO / "despiece.npz", allow_pickle=True)
    W, F, lab = d["W"], d["F"], d["lab"]
    N = suavizar_normales(W, F)  # (normales de toda la malla: las piezas empalman sin costura de luz)
    rd = {k: v for k, v in zip(("del", "tras"), (None, None))}
    nodos, todasF, todasCol, todasA, todasLab, Vtot = [], [], [], [], [], [W]
    for pieza in MAPA:
        m = lab == pieza
        if not m.any():
            continue
        Fp = F[m]
        usados, inv = np.unique(Fp, return_inverse=True)
        mat, col, ex = MAPA[pieza]
        ex = dict(ex)
        Vp = W[usados]
        if pieza.startswith(("llanta", "aro", "rayos")):
            lado = pieza.split("_")[1]
            sel = W[F[lab == f"llanta_{lado}"]].reshape(-1, 3)
            # eje: centro del círculo de la llanta (punto medio de los extremos en x; y = altura al piso)
            ex["eje"] = [round(float((sel[:, 0].max() + sel[:, 0].min()) / 2), 4), round(float((sel[:, 1].max() + sel[:, 1].min()) / 2), 4)]
        if pieza == "manubrio":
            pu = W[F[lab == "punos"]].reshape(-1, 3)
            ex["manubrio"] = {"x": round(float(pu[:, 0].mean()), 3), "y": round(float(pu[:, 1].mean()), 3), "extremo": round(float(np.abs(pu[:, 2]).max()), 3)}
            ex["sin"] = ["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"]
        if pieza == "espejos":
            # (en la foto los espejos quedan 4,5 cm más altos, además del estiramiento ALTO, y 5 cm más adelante: se corren las cabezas y el tallo se
            # estira desde su base en el manubrio, que no se mueve)
            y0, h = Vp[:, 1].min(), np.ptp(Vp[:, 1])
            w = np.clip((Vp[:, 1] - y0) / (0.6 * h), 0, 1)[:, None]
            Vp = Vp + w * np.array([0.05, 0.045, 0.0])
        if pieza == "portaplaca":
            ex["placa"] = placa_de(Vp, inv.reshape(-1, 3))
        if pieza in ("guardabarros_del", "colin", "mascara"):
            ex["doble"] = True
        nodos.append((f"{mat}.{pieza}", Vp, N[usados], inv.reshape(-1, 3), ex))
        todasF.append(Fp); todasCol.append(np.tile(col, (len(Fp), 1))); todasA.append(np.full(len(Fp), 0.18 if pieza not in ("chasis", "llanta_del", "llanta_tras", "rayos_del", "rayos_tras", "aro_del", "aro_tras") else 1.0)); todasLab += [pieza] * len(Fp)
    COLI = {"motor": GRIS, "cromo": (225, 228, 230), "metal": PLATA, "oscuro": (40, 40, 42), "bujia": (240, 236, 228), "caucho": (25, 25, 25),
            "carter": (112, 119, 123), "bateria": (34, 38, 40), "rojo": (200, 40, 30)}
    o = len(W)
    for nombre, (Vi, Fi) in internos().items():
        mat, parte = nombre.split(".")
        pz = "motor" if parte.startswith(("motor", "transmision", "embrague", "carburador")) else "bateria" if parte.startswith(("bat", "cableado")) else \
             "filtro_aire" if parte.startswith("filtro") else "bujia" if parte.startswith("bujia") else "motor"
        ex = {"pieza": pz, "interno": True}
        nodos.append((nombre, Vi, suavizar_normales(Vi, Fi), Fi, ex))
        Vtot.append(Vi); todasF.append(Fi + o); o += len(Vi)
        todasCol.append(np.tile(COLI.get(mat, (120, 120, 120)), (len(Fi), 1))); todasA.append(np.ones(len(Fi))); todasLab += [parte] * len(Fi)
    for nombre, ((Vi, Fi), ex) in luces(W, F, lab).items():
        nodos.append((nombre, Vi, suavizar_normales(Vi, Fi), Fi, ex))
        Vtot.append(Vi); todasF.append(Fi + o); o += len(Vi)
        mat = nombre.split(".")[0]
        todasCol.append(np.tile({"luz": (250, 246, 225), "stop": (220, 40, 35), "ambar": (255, 165, 50), "faro": (170, 175, 180)}.get(mat, NEGRO), (len(Fi), 1)))
        todasA.append(np.ones(len(Fi))); todasLab += [nombre.split(".")[1]] * len(Fi)
    peso = escribir_glb(nodos, SALIDA)
    tri = sum(len(n[3]) for n in nodos)
    np.savez_compressed(TRABAJO / "final.npz", W=np.vstack(Vtot), F=np.vstack(todasF), col=np.vstack(todasCol), alfa=np.concatenate(todasA), lab=np.array(todasLab))
    print(f"GLB {peso/1024:.0f} KB, {len(nodos)} nodos, {tri} triángulos")
