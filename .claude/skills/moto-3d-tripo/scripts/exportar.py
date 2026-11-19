# Escribe el GLB para el visor: un nodo por pieza "material.parte", POSITION int16 y NORMAL int8 (KHR_mesh_quantization),
# extras {pieza, padre, rin, eje, placa, manubrio, rol, acomodar}. El visor pone el escape en -z: el modelo se espeja.
import sys
sys.path.insert(0, sys.argv[1])
import rend, numpy as np, json, struct
d, salida = sys.argv[2], sys.argv[3]
ESPEJAR = "--sin-espejo" not in sys.argv
P, N, C, I = rend.cargar(d, "p")
I = I.astype(np.int64)
L = np.fromfile(f"{d}/p_lab.bin", np.int32)
partes = json.load(open(f"{d}/c_partes.json"))["partes"]
nombres = [p["nombre"] for p in partes]
extras = {p["nombre"]: dict(p["extras"]) for p in partes}

# --- normales: en pintura, lentes y visor, la normal de la malla original trae el grano de la malla generada y los
# reflejos salen arrugados; ahi se mezcla con la normal geometrica de la malla ya simplificada (soldada entre piezas)
LISAS = ("pintura", "pintura2", "stop", "faro", "luz", "negro_brillo", "titanio", "ambar", "asiento", "mica_dir", "reflector")
clave = np.round(P / 2e-5).astype(np.int64)
_, sold = np.unique(clave, axis=0, return_inverse=True)
sold = sold.ravel()
fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]).astype(np.float64)   # (largo = 2 x area: pondera por area)
acum = np.zeros((sold.max() + 1, 3))
for k in range(3):
    np.add.at(acum, sold[I[:, k]], fn)
geo = acum[sold]
geo /= np.maximum(np.linalg.norm(geo, axis=1, keepdims=True), 1e-12)
MEZCLA = float(sys.argv[sys.argv.index("--mezcla") + 1]) if "--mezcla" in sys.argv else 0.75

piezas = []   # (nombre, pos, nor, idx)
for k, nombre in enumerate(nombres):
    caras = I[L == k]
    if len(caras) < 4:
        continue
    usados, inv = np.unique(caras, return_inverse=True)
    n = N[usados].astype(np.float64)
    if nombre.split(".")[0] in LISAS:
        n = n * (1 - MEZCLA) + geo[usados] * MEZCLA
    piezas.append((nombre, P[usados].astype(np.float64), n, inv.reshape(-1, 3)))
import os
for archivo in ("c_extra.npz", "i_extra.npz"):
    if not os.path.exists(f"{d}/{archivo}"):
        continue
    ex = np.load(f"{d}/{archivo}")
    for nombre in sorted({k.split("|")[0] for k in ex.files}):
        piezas.append((nombre, ex[f"{nombre}|pos"], ex[f"{nombre}|nor"], ex[f"{nombre}|idx"]))
if os.path.exists(f"{d}/i_extras.json"):
    extras.update(json.load(open(f"{d}/i_extras.json")))

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
        e["pantalla"] = {**e["pantalla"], "c": [e["pantalla"]["c"][0], e["pantalla"]["c"][1], -e["pantalla"]["c"][2]],
                         "n": [e["pantalla"]["n"][0], e["pantalla"]["n"][1], -e["pantalla"]["n"][2]]}
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
