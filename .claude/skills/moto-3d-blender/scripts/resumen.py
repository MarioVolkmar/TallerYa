# Imagen-resumen para revisar de un vistazo: 6 vistas fijas del GLB del visor (Blender, Eevee) al lado de las fotos de
# referencia, en una sola imagen (2 pares por fila: render | foto). La 6.ª vista es con las luces encendidas.
# Uso: blender -b --factory-startup --gpu-backend opengl --python resumen.py -- modelo.glb carpeta_fotos salida.png
# Colores aproximados del visor por prefijo del nodo; los internos (Rayos X) van ocultos.
import bpy, sys, os, math, numpy as np
from mathutils import Vector
glb, fotos, salida = [os.path.abspath(p) for p in sys.argv[sys.argv.index("--") + 1:][:3]]
tmp = os.path.splitext(salida)[0] + "_vistas"; os.makedirs(tmp, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
COL = {  # (color, rugosidad, metal, emisión, alfa)
    "pintura": ((0.03, 0.12, 0.42), 0.35, 0.3, 0, 1), "blanco": ((0.7, 0.72, 0.78), 0.45, 0, 0, 1),
    "plastico": ((0.035, 0.037, 0.04), 0.85, 0, 0, 1), "negro_brillo": ((0.012, 0.013, 0.014), 0.2, 0.1, 0, 1),
    "chasis": ((0.03, 0.03, 0.03), 0.5, 0.3, 0, 1), "oscuro": ((0.05, 0.05, 0.05), 0.5, 0.45, 0, 1),
    "metal": ((0.55, 0.56, 0.57), 0.35, 0.85, 0, 1), "cromo": ((0.8, 0.8, 0.8), 0.12, 1, 0, 1),
    "rin": ((0.45, 0.46, 0.48), 0.3, 0.7, 0, 1), "carter": ((0.35, 0.35, 0.34), 0.5, 0.4, 0, 1),
    "motor": ((0.2, 0.2, 0.2), 0.5, 0.4, 0, 1), "caucho": ((0.02, 0.02, 0.02), 0.95, 0, 0, 1),
    "asiento": ((0.025, 0.025, 0.025), 0.6, 0, 0, 1), "vidrio_oscuro": ((0.05, 0.07, 0.08), 0.03, 0, 0, 0.75),
    "vidrio": ((0.5, 0.6, 0.65), 0.02, 0, 0, 0.45), "luz": ((1, 0.96, 0.85), 0.1, 0, 1, 1),
    "stop": ((0.9, 0.08, 0.05), 0.2, 0, 1, 1), "ambar": ((1, 0.55, 0.12), 0.25, 0, 1, 1)}
mats, emisores = {}, []
def mat(p):
    if p in mats: return mats[p]
    c, r, me, em, a = COL.get(p, ((0.1, 0.1, 0.1), 0.6, 0, 0, 1))
    m = bpy.data.materials.new(p); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*c, 1); bs.inputs["Roughness"].default_value = r; bs.inputs["Metallic"].default_value = me
    if a < 1: bs.inputs["Alpha"].default_value = a; m.surface_render_method = "BLENDED"
    if em: bs.inputs["Emission Color"].default_value = (*c, 1); emisores.append(bs)
    m.use_backface_culling = False; mats[p] = m; return m
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in objs:
    if o.get("interno") or (o.parent and o.parent.get("interno")): o.hide_render = True; continue
    o.data.materials.clear(); o.data.materials.append(mat(o.name.split(".")[0]))
vis = [o for o in objs if not o.hide_render]
pts = np.array([list(o.matrix_world @ Vector(c)) for o in vis for c in o.bound_box])
lo, hi = pts.min(0), pts.max(0); cen = Vector(((lo + hi) / 2).tolist()); tam = hi - lo

sc = bpy.context.scene; sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 24
sc.render.resolution_x, sc.render.resolution_y = 660, 440; sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.82, 0.84, 0.86, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.9; sc.world = w
for rot, e in (((0.8, 0.2, 0.6), 3.0), ((-0.9, 0, -2.4), 1.2)):
    l = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN")); l.data.energy = e; l.rotation_euler = rot; sc.collection.objects.link(l)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"
# El visor usa x adelante y el escape en -z (glTF): en un sistema diestro eso es la moto reflejada. Por eso cada render se
# voltea en horizontal al componer: así el lado de la CVT, el del escape y el frente quedan como en las fotos.
VISTAS = [("lateral_izq", (0, -1, 0.05), "lateral_izq.png"), ("lateral_der", (0, 1, 0.05), "lateral_der.png"),
          ("frente", (1, 0, 0.12), "frente.png"), ("atras", (-1, 0, 0.12), "atras.png"),
          ("tres_cuartos", (0.75, -0.65, 0.3), "tres_cuartos.png"), ("luces", (0.8, 0.45, 0.15), "farola.jpg")]
rutas = []
for nombre, d, _ in VISTAS:
    d = Vector(d).normalized(); cam.location = cen + d * 6
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = float(max(tam)) * 1.08
    for bs in emisores: bs.inputs["Emission Strength"].default_value = 6.0 if nombre == "luces" else 0.4
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.25 if nombre == "luces" else 0.9
    sc.render.filepath = os.path.join(tmp, nombre + ".png"); bpy.ops.render.render(write_still=True); rutas.append(sc.render.filepath)

# Composición: 3 filas x 2 pares (render | foto), celdas de 440x293
CW, CH = 440, 293
lienzo = np.ones((CH * 3, CW * 4, 4), np.float32)
def celda(ruta_img, voltear=False):
    im = bpy.data.images.load(ruta_img); iw, ih = im.size; f = min(CW / iw, CH / ih); nw, nh = max(1, int(iw * f)), max(1, int(ih * f))
    im.scale(nw, nh); a = np.array(im.pixels[:], np.float32).reshape(nh, nw, 4)
    a = a[:, ::-1] if voltear else a
    c = np.ones((CH, CW, 4), np.float32); y0, x0 = (CH - nh) // 2, (CW - nw) // 2; c[y0:y0 + nh, x0:x0 + nw] = a; return c
for i, ((nombre, _, foto), r) in enumerate(zip(VISTAS, rutas)):
    fila, col = 2 - i // 2, (i % 2) * 2   # (los píxeles de Blender van de abajo hacia arriba)
    lienzo[fila * CH:(fila + 1) * CH, col * CW:(col + 1) * CW] = celda(r, voltear=True)
    fp = os.path.join(fotos, foto)
    if os.path.exists(fp): lienzo[fila * CH:(fila + 1) * CH, (col + 1) * CW:(col + 2) * CW] = celda(fp)
lienzo[:, CW * 2 - 2:CW * 2 + 2] = (0.2, 0.2, 0.2, 1)
out = bpy.data.images.new("resumen", CW * 4, CH * 3, alpha=True); out.pixels.foreach_set(lienzo.ravel())
out.filepath_raw = salida; out.file_format = "PNG"; out.save()
print("resumen:", salida)
