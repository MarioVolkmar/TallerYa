# Escribe el GLB para el visor: un nodo por pieza "material.parte", POSITION int16 y NORMAL int8 (KHR_mesh_quantization),
# extras {pieza, padre, rin, eje, placa, manubrio, rol, acomodar}. El visor pone el escape en -z: el modelo se espeja.
import json
import os
import struct
import sys

import numpy as np

LISAS = ("pintura", "pintura2", "stop", "faro", "luz", "negro_brillo", "titanio", "ambar", "asiento", "mica_dir", "reflector")


def exportar(S, d, salida, mezcla=0.75, lisas=None, espejar=True, suave=0, alisar=None, escalar=None, nivelar=False):
    import rend
    ESPEJAR, MEZCLA, LISAS_ = espejar, mezcla, tuple(lisas or LISAS)
    P, N, C, I = rend.cargar(d, "p")
    I = I.astype(np.int64)
    L = np.fromfile(f"{d}/p_lab.bin", np.int32)
    partes = json.load(open(f"{d}/c_partes.json"))["partes"]
    nombres = [p["nombre"] for p in partes]
    extras = {p["nombre"]: dict(p["extras"]) for p in partes}

    # --- normales: en pintura, lentes y visor, la normal de la malla original trae el grano de la malla generada y los
    # reflejos salen arrugados; ahi se mezcla con la normal geometrica de la malla ya simplificada (soldada entre piezas)
    clave = np.round(P / 2e-5).astype(np.int64)
    _, sold = np.unique(clave, axis=0, return_inverse=True)
    sold = sold.ravel()
    # --- alisado de la superficie (ficha: ALISAR = {"pintura.tanque": 8}): quita las arrugas con que llega la malla
    # generada. Solo se mueven los vertices interiores de la pieza (el borde con las vecinas queda fijo, sin rendijas)
    # y se alterna un paso que encoge con otro que hincha (Taubin) para no perder volumen.
    P = P.astype(np.float64)
    for nombre_a, vueltas in (alisar or {}).items():
        k = nombres.index(nombre_a)
        dentro, fuera = np.unique(sold[I[L == k]]), np.unique(sold[I[L != k]])
        libre = np.zeros(sold.max() + 1, bool)
        libre[dentro] = True
        libre[fuera] = False
        tri = sold[I[L == k]]
        ar = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
        Q = np.zeros((sold.max() + 1, 3))
        Q[sold] = P
        grado = np.bincount(ar.ravel(), minlength=len(Q))[:, None].clip(1)
        for paso in range(vueltas * 2):
            s = np.zeros_like(Q)
            np.add.at(s, ar[:, 0], Q[ar[:, 1]])
            np.add.at(s, ar[:, 1], Q[ar[:, 0]])
            Q[libre] += (0.5 if paso % 2 == 0 else -0.53) * (s / grado - Q)[libre]
        P = np.where(libre[sold][:, None], Q[sold], P)
    fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]).astype(np.float64)   # (largo = 2 x area: pondera por area)
    acum = np.zeros((sold.max() + 1, 3))
    for k in range(3):
        np.add.at(acum, sold[I[:, k]], fn)
    geo = acum[sold]
    geo /= np.maximum(np.linalg.norm(geo, axis=1, keepdims=True), 1e-12)

    piezas = []   # (nombre, pos, nor, idx)
    for k, nombre in enumerate(nombres):
        caras = I[L == k]
        if len(caras) < 4:
            continue
        usados, inv = np.unique(caras, return_inverse=True)
        n = N[usados].astype(np.float64)
        if nombre.split(".")[0] in LISAS_:
            g = geo[usados]
            if suave:
                # (alisado dentro de la pieza: cada normal se promedia con las de sus vecinos soldados; quita el grano
                # y las facetas que se notan en los reflejos de un tanque, sin tocar el borde con las otras piezas)
                _, loc = np.unique(sold[usados], return_inverse=True)
                loc = loc.ravel()
                tri = loc[inv.reshape(-1, 3)]
                ar = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
                gs = np.zeros((loc.max() + 1, 3))
                gs[loc] = g
                for _ in range(suave):
                    ac = gs.copy()
                    np.add.at(ac, ar[:, 0], gs[ar[:, 1]])
                    np.add.at(ac, ar[:, 1], gs[ar[:, 0]])
                    gs = ac / np.maximum(np.linalg.norm(ac, axis=1, keepdims=True), 1e-12)
                g = gs[loc]
            n = n * (1 - MEZCLA) + g * MEZCLA
        piezas.append((nombre, P[usados].astype(np.float64), n, inv.reshape(-1, 3)))
    for archivo in ("c_extra.npz", "i_extra.npz"):
        if not os.path.exists(f"{d}/{archivo}"):
            continue
        ex = np.load(f"{d}/{archivo}")
        for nombre in sorted({k.split("|")[0] for k in ex.files}):
            piezas.append((nombre, ex[f"{nombre}|pos"], ex[f"{nombre}|nor"], ex[f"{nombre}|idx"]))
    if os.path.exists(f"{d}/i_extras.json"):
        extras.update(json.load(open(f"{d}/i_extras.json")))

    medidas = json.load(open(f"{d}/c_partes.json")).get("medidas", {})
    # --- ficha ESCALAR = [{"piezas": [...], "eje": "eje_del", "factor": f}]: escala piezas alrededor del eje de la rueda
    # (Tripo a veces hace una rueda mas grande que la otra; la Boxer trae la delantera 10 % grande)
    fac = {"eje_del": 1.0, "eje_tras": 1.0}
    for es in escalar or []:
        fac[es["eje"]] = es["factor"]
        cx, cy = medidas[es["eje"]]
        c3 = np.array([cx, cy, 0.0])
        piezas = [(nm, c3 + (p_ - c3) * es["factor"], n_, ix) if nm.split(".")[-1] in es["piezas"] else (nm, p_, n_, ix) for nm, p_, n_, ix in piezas]
    # --- ficha NIVELAR = True: gira toda la moto en el plano (x, y) alrededor del eje trasero hasta que las dos ruedas
    # toquen el piso (despues de igualarlas); gira tambien los extras con coordenadas
    if nivelar:
        (xd, yd), (xt, yt) = medidas["eje_del"], medidas["eje_tras"]
        a = -np.arctan2((yd - medidas["R_del"] * fac["eje_del"]) - (yt - medidas["R_tras"] * fac["eje_tras"]), xd - xt)
        ca, sa = np.cos(a), np.sin(a)
        print(f"nivelar: giro {np.degrees(a):.2f} grados")
        def gir(v, punto=True):
            v = np.asarray(v, np.float64).copy()
            x0, y0 = (v[..., 0] - xt, v[..., 1] - yt) if punto else (v[..., 0], v[..., 1])
            v[..., 0], v[..., 1] = x0 * ca - y0 * sa + (xt if punto else 0), x0 * sa + y0 * ca + (yt if punto else 0)
            return v
        piezas = [(nm, gir(p_), gir(n_, False), ix) for nm, p_, n_, ix in piezas]
        r4 = lambda v: [round(float(u), 4) for u in v]
        for e in extras.values():
            if "eje" in e:
                e["eje"] = r4(gir(e["eje"]))
            if "placa" in e:
                e["placa"] = {**e["placa"], "c": r4(gir(e["placa"]["c"])), "incl": e["placa"]["incl"] + float(a)}
            if "pantalla" in e:
                lst = e["pantalla"] if isinstance(e["pantalla"], list) else [e["pantalla"]]
                lst = [{**q, "c": r4(gir(q["c"])), "n": r4(gir(q["n"], False))} for q in lst]
                e["pantalla"] = lst if isinstance(e["pantalla"], list) else lst[0]
            if "manubrio" in e:
                xy = gir([e["manubrio"]["x"], e["manubrio"]["y"]])
                e["manubrio"] = {**e["manubrio"], "x": round(float(xy[0]), 4), "y": round(float(xy[1]), 4)}
            for q in e.get("acomodar", []):
                q["a"] = r4(gir(q["a"]))
            for q in e.get("calcas_fabrica", []):
                if "en" in q:
                    q["en"] = r4(gir(q["en"])[:2]) if len(q["en"]) == 2 else r4(gir(q["en"]))

    binario = bytearray()
    vistas, accs, mallas, nodos = [], [], [], []


    def vista(datos, stride=None, destino=34962):
        while len(binario) % 4:
            binario.append(0)
        v = {"buffer": 0, "byteOffset": len(binario), "byteLength": len(datos), "target": destino}
        if stride:
            v["byteStride"] = stride
        binario.extend(datos)
        vistas.append(v)
        return len(vistas) - 1


    tot = 0
    for nombre, p, n, idx in piezas:
        if ESPEJAR:
            p = p * np.array([1, 1, -1.0])
            n = n * np.array([1, 1, -1.0])
            idx = idx[:, [0, 2, 1]]
        c = (p.min(0) + p.max(0)) / 2
        s = float((p.max(0) - p.min(0)).max() / 2) or 1.0
        q = np.zeros((len(p), 4), np.int16)
        q[:, :3] = np.round((p - c) / s * 32767).clip(-32767, 32767)
        qn = np.zeros((len(p), 4), np.int8)
        qn[:, :3] = np.round(n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9) * 127)
        vp, vn = vista(q.tobytes(), 8), vista(qn.tobytes(), 4)
        chico = len(p) < 65536
        vi = vista(idx.astype(np.uint16 if chico else np.uint32).tobytes(), None, 34963)
        a0 = len(accs)
        accs.append({"bufferView": vp, "componentType": 5122, "normalized": True, "count": len(p), "type": "VEC3",
                     "min": q[:, :3].min(0).tolist(), "max": q[:, :3].max(0).tolist()})
        accs.append({"bufferView": vn, "componentType": 5120, "normalized": True, "count": len(p), "type": "VEC3"})
        accs.append({"bufferView": vi, "componentType": 5123 if chico else 5125, "count": int(idx.size), "type": "SCALAR"})
        mallas.append({"name": nombre, "primitives": [{"attributes": {"POSITION": a0, "NORMAL": a0 + 1}, "indices": a0 + 2}]})
        nodo = {"name": nombre, "mesh": len(mallas) - 1, "translation": [round(float(v), 5) for v in c], "scale": [round(s, 5)] * 3}
        e = extras.get(nombre, {})
        if ESPEJAR and "pantalla" in e:
            # (una pantalla o una lista de pantallas: los relojes redondos de una moto de calle son dos)
            varias = isinstance(e["pantalla"], list)
            pp = [{**p, "c": [p["c"][0], p["c"][1], -p["c"][2]], "n": [p["n"][0], p["n"][1], -p["n"][2]]} for p in (e["pantalla"] if varias else [e["pantalla"]])]
            e["pantalla"] = pp if varias else pp[0]
        if "eje" in e:
            e["eje"] = [round(float(v), 4) for v in e["eje"]]
        if e:
            nodo["extras"] = e
        nodos.append(nodo)
        tot += len(idx)
    while len(binario) % 4:
        binario.append(0)
    g = {"asset": {"version": "2.0", "generator": "TallerYa: malla base generada con IA, simplificada y partida en piezas"},
         "extensionsUsed": ["KHR_mesh_quantization"], "extensionsRequired": ["KHR_mesh_quantization"],
         "scene": 0, "scenes": [{"nodes": list(range(len(nodos)))}], "nodes": nodos, "meshes": mallas,
         "accessors": accs, "bufferViews": vistas, "buffers": [{"byteLength": len(binario)}]}
    js = json.dumps(g, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    js += b" " * (-len(js) % 4)
    with open(salida, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(binario)))
        f.write(struct.pack("<I4s", len(js), b"JSON"))
        f.write(js)
        f.write(struct.pack("<I4s", len(binario), b"BIN\0"))
        f.write(binario)
    print("piezas", len(nodos), "triangulos", tot, "MB", round((28 + len(js) + len(binario)) / 1e6, 2))


if __name__ == "__main__":
    sys.path.insert(0, sys.argv[1])
    exportar(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[sys.argv.index("--mezcla") + 1]) if "--mezcla" in sys.argv else 0.75,
             espejar="--sin-espejo" not in sys.argv)
