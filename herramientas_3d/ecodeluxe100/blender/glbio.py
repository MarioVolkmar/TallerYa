import json, struct, numpy as np
TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMP = {"SCALAR": 1, "VEC3": 3}
def leer(ruta):
    b = open(ruta, "rb").read(); n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20+n]), b, 20+n+8
def atributo(g, b, base, i):
    a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; T = TIPOS[a["componentType"]]; c = COMP[a["type"]]
    tam = np.dtype(T).itemsize; paso = bv.get("byteStride", tam*c)//tam
    arr = np.frombuffer(b, T, a["count"]*paso, base+bv.get("byteOffset",0)+a.get("byteOffset",0)).reshape(a["count"], paso)[:, :c].astype(np.float64)
    if a.get("normalized"): arr /= {np.int16: 32767, np.int8: 127}.get(T, 1)
    return arr if c > 1 else arr[:, 0]
def mallas(ruta):
    g, b, base = leer(ruta); out = []
    for n in g["nodes"]:
        pr = g["meshes"][n["mesh"]]["primitives"][0]
        t = np.array(n.get("translation",[0,0,0])); s = np.array(n.get("scale",[1,1,1]))
        pos = atributo(g,b,base,pr["attributes"]["POSITION"])*s+t
        nor = atributo(g,b,base,pr["attributes"]["NORMAL"])
        idx = atributo(g,b,base,pr["indices"]).astype(np.int64).reshape(-1,3)
        out.append({"name": n["name"], "pos": pos, "nor": nor, "idx": idx, "extras": n.get("extras", {})})
    return g, out
def escribir(salida, nodos_in, generador="TallerYa"):
    nodos, ms, accs, vistas, datos = [], [], [], [], bytearray()
    def agregar(arr, comp, tipo, obj, paso=None, minmax=False):
        while len(datos) % 4: datos.append(0)
        off = len(datos); c = arr.shape[1] if arr.ndim > 1 else 1
        if paso:
            r = np.zeros((arr.shape[0], paso//arr.itemsize), arr.dtype); r[:, :c] = arr; datos.extend(r.tobytes())
        else: datos.extend(arr.tobytes())
        bv = {"buffer":0,"byteOffset":off,"byteLength":len(datos)-off,"target":obj}
        if paso: bv["byteStride"] = paso
        vistas.append(bv)
        a = {"bufferView":len(vistas)-1,"componentType":comp,"count":int(arr.shape[0]),"type":tipo}
        if comp in (5120,5122): a["normalized"] = True
        if minmax: a["min"] = arr.min(0).astype(int).tolist(); a["max"] = arr.max(0).astype(int).tolist()
        accs.append(a); return len(accs)-1
    tri = 0
    for m in nodos_in:
        mundo = m["pos"]; centro = (mundo.min(0)+mundo.max(0))/2; esc = float(np.abs(mundo-centro).max()) or 1.0
        q = np.clip(np.round((mundo-centro)/esc*32767), -32767, 32767).astype(np.int16)
        nn = m["nor"]/np.maximum(np.linalg.norm(m["nor"],axis=1,keepdims=True),1e-9)
        qn = np.clip(np.round(nn*127), -127, 127).astype(np.int8)
        idx = m["idx"].reshape(-1); assert idx.max() < 65535, m["name"]
        ip = agregar(q,5122,"VEC3",34962,paso=8,minmax=True); inn = agregar(qn,5120,"VEC3",34962,paso=4)
        ii = agregar(idx.astype(np.uint16),5123,"SCALAR",34963)
        ms.append({"name":m["name"],"primitives":[{"attributes":{"POSITION":ip,"NORMAL":inn},"indices":ii}]})
        nd = {"name":m["name"],"mesh":len(ms)-1,"translation":[round(float(v),5) for v in centro],"scale":[round(esc,5)]*3}
        if m["extras"]: nd["extras"] = m["extras"]
        nodos.append(nd); tri += len(idx)//3
    while len(datos) % 4: datos.append(0)
    g = {"asset":{"version":"2.0","generator":generador},"extensionsUsed":["KHR_mesh_quantization"],"extensionsRequired":["KHR_mesh_quantization"],
         "scene":0,"scenes":[{"nodes":list(range(len(nodos)))}],"nodes":nodos,"meshes":ms,"accessors":accs,"bufferViews":vistas,"buffers":[{"byteLength":len(datos)}]}
    js = json.dumps(g,separators=(",",":"),ensure_ascii=False).encode(); js += b" "*(-len(js)%4)
    glb = struct.pack("<III",0x46546C67,2,28+len(js)+len(datos))+struct.pack("<II",len(js),0x4E4F534A)+js+struct.pack("<II",len(datos),0x004E4942)+bytes(datos)
    open(salida,"wb").write(glb); print(f"{salida}: {len(glb)/1e6:.3f} MB, {tri} tri, {len(nodos)} nodos")
