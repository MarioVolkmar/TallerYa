# Eco Deluxe 100: toma la geometría que exportó Blender (float) y escribe el GLB del visor como el original:
# nodos "material.parte" en el orden original, posiciones int16 y normales int8 (KHR_mesh_quantization), índices
# uint16, extras del original más los acabados PBR y las calcas de fábrica de esta versión.
# Uso: python postproceso.py original.glb blender.glb salida.glb
import json, struct, sys
import numpy as np

ORIGINAL, BLENDER, SALIDA = sys.argv[1:4]


def leer(ruta):
    b = open(ruta, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + n])
    base = 20 + n + 8
    return g, b, base


TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMP = {"SCALAR": 1, "VEC3": 3}


def atributo(g, b, base, i):
    a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; T = TIPOS[a["componentType"]]; c = COMP[a["type"]]
    tam = np.dtype(T).itemsize
    paso = bv.get("byteStride", tam * c) // tam
    arr = np.frombuffer(b, T, a["count"] * paso, base + bv.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(a["count"], paso)[:, :c]
    arr = arr.astype(np.float64)
    if a.get("normalized"):
        arr /= {np.int16: 32767, np.int8: 127}.get(T, 1)
    return arr if c > 1 else arr[:, 0]


# Acabados PBR propios (extras.acabado: se aplican sobre el material compartido, Personalizar sigue dando el color)
ACABADOS = {
    "metal.aro_tras": {"roughness": 0.24, "metalness": 0.95},          # aro de aluminio pulido
    "metal.aro_del": {"roughness": 0.24, "metalness": 0.95},
    "asiento.asiento": {"roughness": 0.62, "sheen": 0.35, "sheenRoughness": 0.5, "clearcoat": 0.12, "clearcoatRoughness": 0.6},  # vinilo
    "plastico.guardabarros_tras": {"roughness": 0.86, "metalness": 0},   # plástico inyectado mate
    "plastico.guardabarros_int": {"roughness": 0.9, "metalness": 0},
    "plastico.cubre_horquilla": {"roughness": 0.84, "metalness": 0},
    "caucho.punos": {"roughness": 0.95, "metalness": 0},
    "oscuro.espejos": {"roughness": 0.35, "metalness": 0.1, "clearcoat": 0.6},
}
# Calcas de fábrica medidas sobre la foto lateral (1,9 mm por píxel, ejes a ±0,6175 m): cuña plateada y blanca en el
# costado del tanque con la punta adelante, trazos grises y el nombre en la tapa lateral bajo el sillín
CALCAS = [
    {"id": "cuna", "nombre": "Cuña del tanque", "tipo": "franja", "zona": ["tanque"], "cara": "lado", "angosto": 0.2,
     "en": [0.11, 0.715], "ancho": 0.30, "giro": 4, "color": "#c9cdd1", "color2": "#eef0f2"},
    {"id": "cuna_lateral", "nombre": "Trazos de la tapa lateral", "tipo": "franja", "forma": "trazos", "zona": ["lateral"],
     "cara": "lado", "angosto": 0.6, "en": [-0.2, 0.66], "ancho": 0.16, "giro": 6, "color": "#c9cdd1"},
    {"id": "nombre", "nombre": "Nombre ECO DELUXE", "tipo": "texto", "texto": "ECO DELUXE", "zona": ["lateral"], "cara": "lado",
     "en": [-0.235, 0.6], "ancho": 0.17, "giro": 6, "color": "gris"},
]

go, bo, baseo = leer(ORIGINAL)
gb, bb, baseb = leer(BLENDER)
por_nombre = {n["name"]: n for n in gb["nodes"] if "mesh" in n}

nodos, mallas, accs, vistas, datos = [], [], [], [], bytearray()


def agregar(arr, comp, tipo, objetivo, paso=None, minmax=False):
    while len(datos) % 4: datos.append(0)
    off = len(datos)
    c = arr.shape[1] if arr.ndim > 1 else 1
    if paso:  # atributo entrelazado con relleno a múltiplo de 4
        rell = np.zeros((arr.shape[0], paso // arr.itemsize), arr.dtype); rell[:, :c] = arr; datos.extend(rell.tobytes())
    else:
        datos.extend(arr.tobytes())
    bv = {"buffer": 0, "byteOffset": off, "byteLength": len(datos) - off, "target": objetivo}
    if paso: bv["byteStride"] = paso
    vistas.append(bv)
    a = {"bufferView": len(vistas) - 1, "componentType": comp, "count": int(arr.shape[0]), "type": tipo}
    if comp in (5120, 5122): a["normalized"] = True
    if minmax: a["min"] = arr.min(0).astype(int).tolist(); a["max"] = arr.max(0).astype(int).tolist()
    accs.append(a)
    return len(accs) - 1


resumen = {"tri": 0, "vert": 0}
for no in go["nodes"]:
    nb = por_nombre[no["name"]]
    pr = gb["meshes"][nb["mesh"]]["primitives"][0]
    pos = atributo(gb, bb, baseb, pr["attributes"]["POSITION"])
    nor = atributo(gb, bb, baseb, pr["attributes"]["NORMAL"])
    idx = atributo(gb, bb, baseb, pr["indices"]).astype(np.int64)
    # Blender exporta las mismas traslación y escala del nodo (la malla queda en ±1): se recuantiza igual que el original
    t = np.array(nb.get("translation", [0, 0, 0])); s = np.array(nb.get("scale", [1, 1, 1]))
    mundo = pos * s + t
    centro = (mundo.min(0) + mundo.max(0)) / 2
    esc = float(np.abs(mundo - centro).max()) or 1.0
    q = np.clip(np.round((mundo - centro) / esc * 32767), -32767, 32767).astype(np.int16)
    nn = nor / np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
    qn = np.clip(np.round(nn * 127), -127, 127).astype(np.int8)
    assert idx.max() < 65535, no["name"]
    ip = agregar(q, 5122, "VEC3", 34962, paso=8, minmax=True)
    inn = agregar(qn, 5120, "VEC3", 34962, paso=4)
    ii = agregar(idx.astype(np.uint16), 5123, "SCALAR", 34963)
    mallas.append({"name": no["name"], "primitives": [{"attributes": {"POSITION": ip, "NORMAL": inn}, "indices": ii}]})
    ex = dict(no.get("extras", {}))
    if no["name"] in ACABADOS: ex["acabado"] = ACABADOS[no["name"]]
    if no["name"] == "pintura.tanque": ex["calcas_fabrica"] = CALCAS
    nd = {"name": no["name"], "mesh": len(mallas) - 1, "translation": [round(float(v), 5) for v in centro],
          "scale": [round(esc, 5)] * 3}
    if ex: nd["extras"] = ex
    nodos.append(nd)
    resumen["tri"] += len(idx) // 3; resumen["vert"] += len(q)

while len(datos) % 4: datos.append(0)
g = {"asset": {"version": "2.0", "generator": go["asset"].get("generator", "TallerYa") + "; geometría limpiada en Blender"},
     "extensionsUsed": ["KHR_mesh_quantization"], "extensionsRequired": ["KHR_mesh_quantization"],
     "scene": 0, "scenes": [{"nodes": list(range(len(nodos)))}], "nodes": nodos, "meshes": mallas,
     "accessors": accs, "bufferViews": vistas, "buffers": [{"byteLength": len(datos)}]}
js = json.dumps(g, separators=(",", ":"), ensure_ascii=False).encode()
js += b" " * (-len(js) % 4)
glb = struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(datos)) + struct.pack("<II", len(js), 0x4E4F534A) + js + \
      struct.pack("<II", len(datos), 0x004E4942) + bytes(datos)
open(SALIDA, "wb").write(glb)
print(f"{SALIDA}: {len(glb)/1e6:.3f} MB, {resumen['tri']} triángulos, {resumen['vert']} vértices, {len(nodos)} nodos")
