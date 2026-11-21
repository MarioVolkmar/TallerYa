"""Paso 1 (Blender, sin ventana): GLB de Tripo de la XR 190L → malla limpia, aligerada y con el color de la textura
horneada por cara, en un .npz para el despiece.
Uso: blender -b --factory-startup --python preparar.py -- ENTRADA.glb SALIDA.npz [CARAS_META]
- une todo en una malla, funde vértices repetidos (el GLB parte los vértices en las costuras de UV)
- borra islas sueltas (< 20 caras) y caras degeneradas, tapa huecos chicos, recalcula normales hacia afuera
- Decimate (colapso) hasta CARAS_META sin tocar la silueta (las costuras de UV se respetan para muestrear bien)
Ejes: Blender importa glTF con z arriba; se devuelven en ejes glTF (x, y arriba, z), como lee comun.leer_glb."""
import sys

import bmesh
import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
entrada, salida = args[0], args[1]
meta = int(args[2]) if len(args) > 2 else 110000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=entrada)
mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects:
    o.select_set(o in mallas)
bpy.context.view_layer.objects.active = mallas[0]
if len(mallas) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
rep = {"caras_tripo": len(me.polygons), "vertices_tripo": len(me.vertices)}

bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
largo = max(ob.dimensions)
r = bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=largo * 2e-6)
rep["vertices_fundidos"] = len(r.get("targetmap", {})) if isinstance(r, dict) else None
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=largo * 1e-7)
# islas sueltas
bm.faces.ensure_lookup_table()
visto, sueltas = set(), []
for f in bm.faces:
    if f.index in visto:
        continue
    pila, isla = [f], []
    visto.add(f.index)
    while pila:
        g = pila.pop()
        isla.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in visto:
                    visto.add(h.index)
                    pila.append(h)
    if len(isla) < 20:
        sueltas += isla
rep["caras_sueltas_quitadas"] = len(sueltas)
bmesh.ops.delete(bm, geom=sueltas, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
# huecos chicos (lazos de borde de hasta 40 aristas)
borde = [e for e in bm.edges if e.is_boundary]
rep["aristas_borde_antes"] = len(borde)
hp = bmesh.ops.holes_fill(bm, edges=borde, sides=40)
rep["huecos_tapados"] = len(hp["faces"])
bmesh.ops.triangulate(bm, faces=hp["faces"])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me)
bm.free()

# Decimate: colapso con triangulación, respetando costuras de UV (delimit) para muestrear la textura sin mezclar islas
n0 = len(me.polygons)
if n0 > meta:
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = meta / n0
    mod.use_collapse_triangulate = True
    mod.delimit = {"UV"}
    bpy.ops.object.modifier_apply(modifier=mod.name)
me = ob.data
rep["caras_final"] = len(me.polygons)

# (este GLB de Tripo no trae textura: se guarda la geometría limpia; el color sale de los materiales por pieza)
nv, nf = len(me.vertices), len(me.polygons)
V = np.empty(nv * 3, np.float64); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
F = np.empty(nf * 3, np.int64); me.polygons.foreach_get("vertices", F); F = F.reshape(-1, 3)
Vg = np.stack([V[:, 0], V[:, 2], -V[:, 1]], 1)  # Blender (z arriba) -> glTF (y arriba)
np.savez_compressed(salida, V=Vg, F=F)
print("REPORTE", rep, "imagenes", len(bpy.data.images))
