"""Reescribe un GLB con un bufferView propio por accessor (byteOffset 0): el lector del visor (glb.js) no suma
accessor.byteOffset, y gltf-transform deja varios accessors en un mismo bufferView. Uso: python separar_vistas.py glb"""
import json, struct, sys
ruta = sys.argv[1]
b = open(ruta, "rb").read()
nj = struct.unpack("<I", b[12:16])[0]
g = json.loads(b[20:20 + nj]); base = 20 + nj + 8
bin_ = b[base: base + struct.unpack("<I", b[20 + nj:24 + nj])[0]]
TAM = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}; COMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
nuevo, vistas = bytearray(), []
for a in g["accessors"]:
    bv = g["bufferViews"][a["bufferView"]]
    elem = TAM[a["componentType"]] * COMP[a["type"]]
    paso = bv.get("byteStride", elem)
    ini = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    # (entrelazado: se copia solo este atributo, ya sin paso; el visor lee sin entrelazar igual)
    relleno = bytes(1) * ((4 - elem % 4) % 4 if a["type"] != "SCALAR" else 0)
    datos = b"".join(bin_[ini + i * paso: ini + i * paso + elem] + relleno for i in range(a["count"]))
    while len(nuevo) % 4: nuevo.append(0)
    v = {"buffer": 0, "byteOffset": len(nuevo), "byteLength": len(datos)}
    if relleno: v["byteStride"] = elem + len(relleno)  # (glTF pide paso múltiplo de 4)
    if "target" in bv: v["target"] = bv["target"]
    nuevo += datos; a["bufferView"] = len(vistas); a.pop("byteOffset", None); vistas.append(v)
while len(nuevo) % 4: nuevo.append(0)
g["bufferViews"] = vistas; g["buffers"] = [{"byteLength": len(nuevo)}]
js = json.dumps(g, separators=(",", ":")).encode()
js += b" " * ((4 - len(js) % 4) % 4)
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(nuevo)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(nuevo), 0x004E4942) + nuevo
open(ruta, "wb").write(out)
print("bufferViews", len(vistas), "bytes", len(out))
