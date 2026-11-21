# Aerox 155: toma la geometría limpia de Blender (float) y escribe el GLB del visor (int16/int8, KHR_mesh_quantization)
# con los extras del armado y los internos de Rayos X del modelo anterior de la Aerox (aerox155_tripo2.glb).
# Uso: python -I final.py armado.glb blender.glb internos_de.glb salida.glb
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ecodeluxe100", "blender"))
import glbio

ARMADO, BLENDER, INTERNOS, SALIDA = sys.argv[1:5]
_, armado = glbio.mallas(ARMADO)
extras = {m["name"]: m["extras"] for m in armado}
orden = [m["name"] for m in armado]
g, b, base = glbio.leer(BLENDER)
geo = {}
for n in g["nodes"]:
    if "mesh" not in n: continue
    assert "rotation" not in n and "matrix" not in n, n["name"]
    pr = g["meshes"][n["mesh"]]["primitives"]
    pos, nor, idx, o = [], [], [], 0
    for p in pr:
        a = glbio.atributo(g, b, base, p["attributes"]["POSITION"]) * np.array(n.get("scale", [1, 1, 1])) + np.array(n.get("translation", [0, 0, 0]))
        pos.append(a); nor.append(glbio.atributo(g, b, base, p["attributes"]["NORMAL"]))
        idx.append(glbio.atributo(g, b, base, p["indices"]).astype(np.int64).reshape(-1, 3) + o); o += len(a)
    geo[n["name"]] = {"pos": np.vstack(pos), "nor": np.vstack(nor), "idx": np.vstack(idx)}
faltan = [k for k in orden if k not in geo]
assert not faltan, faltan
nodos = [dict(geo[k], name=k, extras=extras[k]) for k in orden]
_, viejos = glbio.mallas(INTERNOS)
nodos += [m for m in viejos if m["extras"].get("interno")]
glbio.escribir(SALIDA, nodos, "TallerYa: Aerox 155 desde Tripo despiezado (método Eco Deluxe): piezas con nombre, acabado por material, luces separadas; geometría limpiada en Blender")
