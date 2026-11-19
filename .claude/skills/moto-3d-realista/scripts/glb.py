"""GLB liviano con KHR_mesh_quantization (posiciones int16, normales int8), sin dependencias aparte de numpy.

Cada pieza es un nodo con nombre "material.parte" y extras opcionales:
  pieza  -> grupo de mantenimiento del visor (moto.piezas[pieza]) donde va la malla
  padre  -> ruta en el objeto moto del visor ("espejos.fabrica", "escapeFabrica", ...)
  rin    -> true: es el rin de fábrica (se oculta si la persona elige otro estilo de rin)
  rol    -> "visor" (parabrisas de fábrica)
La escala de cuantización es uniforme por malla (las normales no se deforman).
"""
import json
import struct
import numpy as np

COLORES = {  # solo para ver el GLB fuera de TallerYa; el visor usa sus propios materiales (moto.M[material])
    "pintura": (0.85, 0.86, 0.88, 0.35, 0.3), "pintura2": (0.85, 0.86, 0.88, 0.35, 0.3),
    "oscuro": (0.07, 0.08, 0.09, 0.25, 0.6), "chasis": (0.1, 0.11, 0.12, 0.6, 0.4),
    "asiento": (0.06, 0.06, 0.07, 0.0, 0.7), "rin": (0.12, 0.13, 0.14, 0.7, 0.3),
    "caucho": (0.05, 0.05, 0.05, 0.0, 0.9), "metal": (0.7, 0.72, 0.74, 0.95, 0.22),
    "cromo": (0.9, 0.9, 0.9, 1.0, 0.05), "motor": (0.55, 0.57, 0.6, 0.85, 0.38),
    "carter": (0.4, 0.42, 0.44, 0.8, 0.45), "luz": (1.0, 0.97, 0.85, 0.0, 0.1),
    "stop": (1.0, 0.2, 0.15, 0.0, 0.2), "ambar": (1.0, 0.6, 0.2, 0.0, 0.25),
    "vidrio": (0.2, 0.22, 0.24, 0.0, 0.05), "tablero": (0.03, 0.04, 0.05, 0.2, 0.1),
    "plastico": (0.06, 0.065, 0.07, 0.0, 0.88), "negro_brillo": (0.03, 0.035, 0.04, 0.2, 0.2),
    "acento": (0.04, 0.045, 0.05, 0.15, 0.4), "vidrio_oscuro": (0.08, 0.1, 0.11, 0.0, 0.04),
}


def _pad(b, c=b"\x00"):
    return b + c * ((4 - len(b) % 4) % 4)


def escribir(ruta, piezas, generador="moto-3d-realista"):
    """piezas: lista de dicts {nombre, material, malla (geom.Malla), extras?}."""
    gltf = {"asset": {"version": "2.0", "generator": generador}, "scene": 0, "scenes": [{"nodes": []}],
            "nodes": [], "meshes": [], "accessors": [], "bufferViews": [], "materials": [], "buffers": [],
            "extensionsUsed": ["KHR_mesh_quantization"], "extensionsRequired": ["KHR_mesh_quantization"]}
    binario = bytearray()
    mats = {}

    def vista(datos, destino):
        off = len(binario); binario.extend(_pad(datos))
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(datos), "target": destino})
        return len(gltf["bufferViews"]) - 1

    for p in piezas:
        m = p["malla"]
        if len(m.f) == 0:
            continue
        v = m.v.astype(np.float64); n = m.normales()
        lo, hi = v.min(0), v.max(0); c = (lo + hi) / 2
        s = float(max((hi - lo).max() / 2, 1e-6))
        q = np.round((v - c) / s * 32767).clip(-32767, 32767).astype(np.int16)
        q4 = np.zeros((len(q), 4), np.int16); q4[:, :3] = q  # (alineado a 4 bytes por vértice: 8 bytes)
        nq = np.zeros((len(n), 4), np.int8); nq[:, :3] = np.round(n * 127).clip(-127, 127)
        idx = m.f.astype(np.uint16 if len(v) < 65536 else np.uint32).ravel()
        bv_p = vista(q4.tobytes(), 34962); bv_p_stride = 8
        gltf["bufferViews"][bv_p]["byteStride"] = bv_p_stride
        bv_n = vista(nq.tobytes(), 34962); gltf["bufferViews"][bv_n]["byteStride"] = 4
        bv_i = vista(idx.tobytes(), 34963)
        qlo, qhi = q.min(0).tolist(), q.max(0).tolist()
        acc = gltf["accessors"]
        acc.append({"bufferView": bv_p, "componentType": 5122, "normalized": True, "count": len(q), "type": "VEC3",
                    "min": [x / 32767 for x in qlo], "max": [x / 32767 for x in qhi]})
        acc.append({"bufferView": bv_n, "componentType": 5120, "normalized": True, "count": len(n), "type": "VEC3"})
        acc.append({"bufferView": bv_i, "componentType": 5123 if idx.dtype == np.uint16 else 5125,
                    "count": len(idx), "type": "SCALAR"})
        mat = p["material"]
        if mat not in mats:
            r, g, b, met, rug = COLORES.get(mat, (0.5, 0.5, 0.5, 0.0, 0.5))
            pbr = {"baseColorFactor": [r, g, b, 0.5 if mat.startswith("vidrio") else 1.0], "metallicFactor": met, "roughnessFactor": rug}
            mdef = {"name": mat, "pbrMetallicRoughness": pbr}
            if mat in ("luz", "stop", "ambar"):
                mdef["emissiveFactor"] = [r, g, b]
            if mat.startswith("vidrio"):
                mdef["alphaMode"] = "BLEND"
            gltf["materials"].append(mdef); mats[mat] = len(gltf["materials"]) - 1
        k = len(acc)
        gltf["meshes"].append({"name": p["nombre"], "primitives": [
            {"attributes": {"POSITION": k - 3, "NORMAL": k - 2}, "indices": k - 1, "material": mats[mat]}]})
        nodo = {"name": f'{mat}.{p["nombre"]}', "mesh": len(gltf["meshes"]) - 1,
                "translation": c.tolist(), "scale": [s, s, s]}
        if p.get("extras"):
            nodo["extras"] = p["extras"]
        gltf["nodes"].append(nodo)
        gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)
    gltf["buffers"].append({"byteLength": len(binario)})
    js = _pad(json.dumps(gltf, separators=(",", ":")).encode(), b" ")
    bi = _pad(bytes(binario))
    total = 12 + 8 + len(js) + 8 + len(bi)
    with open(ruta, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A)); fh.write(js)
        fh.write(struct.pack("<II", len(bi), 0x004E4942)); fh.write(bi)
    return total


def leer(ruta):
    """Devuelve [(nombre_nodo, vertices_mundo (N,3), caras (M,3), extras)] de un GLB escrito por escribir()."""
    d = open(ruta, "rb").read()
    ljs = struct.unpack_from("<I", d, 12)[0]
    g = json.loads(d[20:20 + ljs]); b0 = 20 + ljs + 8
    def acc(i, comps):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]
        dt = {5122: np.int16, 5120: np.int8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a["componentType"]]
        stride = bv.get("byteStride", 0) or np.dtype(dt).itemsize * comps
        crudo = np.frombuffer(d, np.uint8, a["count"] * stride, b0 + bv["byteOffset"]).reshape(a["count"], stride)
        x = crudo[:, :np.dtype(dt).itemsize * comps].copy().view(dt).reshape(a["count"], comps).astype(float)
        if a.get("normalized"):
            x /= {np.int16: 32767, np.int8: 127}.get(dt, 1)
        return x
    salida = []
    for nodo in g["nodes"]:
        pr = g["meshes"][nodo["mesh"]]["primitives"][0]
        v = acc(pr["attributes"]["POSITION"], 3) * np.array(nodo.get("scale", [1, 1, 1])) + np.array(nodo.get("translation", [0, 0, 0]))
        f = acc(pr["indices"], 1).astype(np.int64).reshape(-1, 3)
        salida.append((nodo["name"], v, f, nodo.get("extras", {})))
    return salida
