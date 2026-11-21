# Render de revisión (Eevee, 800 px) del GLB del visor con materiales PBR aproximados por prefijo de nodo.
# Uso: blender -b --factory-startup --python render.py -- modelo.glb carpeta_salida
import bpy, sys, math, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
MODELO, SAL = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MODELO)
# (color, metálico, rugosidad, capa transparente, emisión)
PBR = {"pintura": ((0.012, 0.013, 0.014), 0.45, 0.32, 1.0, 0), "negro_brillo": ((0.006, 0.007, 0.007), 0.1, 0.22, 1.0, 0),
       "plastico": ((0.015, 0.016, 0.017), 0, 0.88, 0, 0), "chasis": ((0.01, 0.01, 0.01), 0.3, 0.45, 0.5, 0),
       "metal": ((0.7, 0.71, 0.72), 0.9, 0.3, 0, 0), "cromo": ((0.9, 0.9, 0.9), 1, 0.08, 0, 0),
       "motor": ((0.55, 0.56, 0.57), 0.85, 0.35, 0, 0), "carter": ((0.5, 0.5, 0.5), 0.8, 0.4, 0, 0),
       "caucho": ((0.02, 0.02, 0.02), 0, 0.92, 0, 0), "asiento": ((0.012, 0.013, 0.014), 0, 0.62, 0.12, 0),
       "oscuro": ((0.02, 0.02, 0.02), 0.2, 0.5, 0, 0), "luz": ((1, 1, 0.95), 0, 0.1, 1, 3), "stop": ((0.8, 0.03, 0.02), 0, 0.2, 1, 1),
       "ambar": ((1, 0.45, 0.05), 0, 0.2, 1, 1), "reflector": ((1, 0.4, 0.05), 0.1, 0.25, 0.8, 0)}
mats = {}
for ob in list(bpy.context.scene.objects):
    if ob.type != "MESH": continue
    if ob.get("interno"): ob.hide_render = True; continue
    pre = ob.name.split(".")[0]
    if pre not in mats:
        c, me, ro, cc, em = PBR.get(pre, ((0.03, 0.03, 0.03), 0.2, 0.5, 0, 0))
        m = bpy.data.materials.new(pre); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Metallic"].default_value = me
        b.inputs["Roughness"].default_value = ro; b.inputs["Coat Weight"].default_value = cc
        if em: b.inputs["Emission Color"].default_value = (*c, 1); b.inputs["Emission Strength"].default_value = em
        mats[pre] = m
    ob.data.materials.clear(); ob.data.materials.append(mats[pre])
sc = bpy.context.scene
for motor in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: sc.render.engine = motor; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 800, 560
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.86, 0.88, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
for rot, en in (((50, 0, 30), 3.0), ((60, 0, 200), 1.5)):
    l = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN")); l.data.energy = en
    l.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(l)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 70
objetivo = Vector((0, 0, 0.6))
for nombre, pos in (("lateral", (0, 6.5, 0.65)), ("tres_cuartos", (4.6, 4.2, 1.9))):
    cam.location = pos
    cam.rotation_euler = (objetivo - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(SAL, f"render_{nombre}.png")
    bpy.ops.render.render(write_still=True)
print("LISTO")
