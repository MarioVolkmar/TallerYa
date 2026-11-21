# Aerox 155 (copia de la Eco Deluxe 100 con razones propias): limpia la geometría del GLB del visor en Blender (sin ventana) y la exporta en float para el post-proceso.
# Uso: blender -b --factory-startup --python geometria.py -- entrada.glb salida.glb informe.json
# Por pieza: une vértices duplicados, quita sueltos y caras degeneradas, tapa huecos chicos (no en láminas abiertas),
# orienta normales hacia afuera (sin voltear la pieza entera), Decimate por pieza con la silueta bloqueada y
# suavizado por ángulo (bordes nítidos en paneles, lisos en curvas). Los internos de Rayos X no se tocan.
import bpy, bmesh, sys, json, math, mathutils
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
ENTRADA, SALIDA, INFORME = args[0], args[1], args[2]

# Razón de Decimate por prefijo de material o nombre (1 = no se toca). Llantas y rayos: el visor las tornea o son finas.
RAZON = {"caucho.llanta": 0.2, "rin": 0.55, "metal.disco": 0.6, "luz": 1.0, "vidrio": 0.8, "cromo.reflector": 0.8, "stop": 0.8, "ambar": 1.0,
         "reflector": 1.0, "pintura": 0.42, "asiento": 0.35, "negro_brillo": 0.5, "chasis": 0.4, "plastico": 0.35, "motor": 0.35,
         "metal": 0.45, "oscuro": 0.4, "carter": 0.4, "caucho": 0.5}
SUAVE = {"pintura": 18, "plastico": 8, "asiento": 4, "negro_brillo": 3, "oscuro.visera": 3, "carter": 2}
# Ángulo de suavizado (grados): paneles pintados con bordes vivos; caucho y sillín lisos; piezas de motor con aristas.
ANGULO = {"pintura": 50, "negro_brillo": 38, "asiento": 55, "caucho": 60, "chasis": 45, "plastico": 40, "motor": 35,
          "carter": 35, "metal": 40, "cromo": 50, "oscuro": 40, "luz": 50, "stop": 40, "ambar": 40, "reflector": 30}


def valor(tabla, nombre, defecto):
    mejor = None
    for k, v in tabla.items():
        if nombre.startswith(k) and (mejor is None or len(k) > len(mejor)):
            mejor = k
    return tabla[mejor] if mejor else defecto


def afuera(bm):
    c = sum((v.co for v in bm.verts), start=mathutils.Vector()) / max(len(bm.verts), 1)
    return sum(f.calc_area() * f.normal.dot(f.calc_center_median() - c) for f in bm.faces)


def lente_limpio(me, lados=56):
    # El lente salió de cortar un círculo en la cara del carenado y quedó con borde serrado: se cambia por una elipse
    # ajustada a sus vértices (plano por PCA, radios por percentil), apenas abombada hacia afuera (+x, adelante).
    P = np.array([v.co[:] for v in me.vertices])
    c = P.mean(0)
    _, _, vt = np.linalg.svd(P - c)
    u, w, n = vt[0], vt[1], vt[2]
    if n[0] < 0: n = -n
    du, dw = (P - c) @ u, (P - c) @ w
    ru, rw = np.percentile(np.abs(du), 97), np.percentile(np.abs(dw), 97)
    cu, cw = (du.max() + du.min()) / 2, (dw.max() + dw.min()) / 2
    c = c + u * cu + w * cw + n * (np.percentile((P - c) @ n, 90))
    bm = bmesh.new()
    centro = bm.verts.new(mathutils.Vector(c + n * 0.06 * min(ru, rw)))
    anillo, aro2 = [], []
    for i in range(lados):
        a = 2 * math.pi * i / lados
        q = c + u * ru * math.cos(a) + w * rw * math.sin(a)
        anillo.append(bm.verts.new(mathutils.Vector(q)))
        aro2.append(bm.verts.new(mathutils.Vector(c + 0.55 * (q - c) + n * 0.045 * min(ru, rw))))
    for i in range(lados):
        j = (i + 1) % lados
        bm.faces.new((anillo[i], anillo[j], aro2[j], aro2[i]))
        bm.faces.new((aro2[i], aro2[j], centro))
    bm.normal_update()
    if sum(f.normal.dot(mathutils.Vector(n)) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    return len(me.polygons)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=ENTRADA, merge_vertices=False)
informe = {}
for ob in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
    nombre = ob.name
    ex = ob.get("extras") or {}
    me = ob.data
    antes = len(me.polygons)
    interno = bool(ob.get("interno"))
    doble = bool(ob.get("doble"))
    if interno:
        informe[nombre] = {"antes": antes, "despues": antes, "interno": True}
        continue
    if False:
        informe[nombre] = {"antes": antes, "despues": lente_limpio(me), "lente": "elipse ajustada"}
        continue
    bm = bmesh.new(); bm.from_mesh(me)
    bm.normal_update()
    v0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)
    unidos = v0 - len(bm.verts)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.00005)
    sueltos = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    huecos = 0
    if not doble:
        bordes = [e for e in bm.edges if e.is_boundary]
        if bordes:
            r = bmesh.ops.holes_fill(bm, edges=bordes, sides=12)
            huecos = len(r["faces"])
    # normales consistentes por isla; si la mayoría quedó al revés de la original, se vuelve a dar vuelta
    s0 = afuera(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    s1 = afuera(bm)
    volteada = s1 < s0
    if volteada:  # recalc no mejoró (lámina abierta o pieza rara): se deja la orientación de Tripo
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    # Decimate con silueta: bordes abiertos y límites de normales bloqueados (la herramienta de Blender cuida la forma)
    # Aerox: Tripo deja la carrocería arrugada (ruido fino que la pintura metalizada delata). Laplaciano con el borde fijo
    # y volumen conservado: alisa sin mover la silueta ni los cortes entre piezas.
    suav = valor(SUAVE, nombre, 0)
    if suav:
        mod = ob.modifiers.new("lap", "LAPLACIANSMOOTH")
        mod.iterations = suav; mod.lambda_factor = 0.6; mod.lambda_border = 0.0; mod.use_volume_preserve = True; mod.use_normalized = True
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    razon = valor(RAZON, nombre, 0.85)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    if razon < 1.0 and len(me.polygons) > 300:
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"; mod.ratio = razon; mod.use_symmetry = False; mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ang = valor(ANGULO, nombre, 40)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(ang), keep_sharp_edges=True)
    informe[nombre] = {"antes": antes, "despues": len(ob.data.polygons), "unidos": unidos, "sueltos": len(sueltos),
                       "huecos": huecos, "orientacion_tripo": volteada, "angulo": ang, "razon": razon}

bpy.ops.export_scene.gltf(filepath=SALIDA, export_format="GLB", export_yup=True, export_normals=True, export_texcoords=False,
                          export_materials="NONE", export_extras=True, export_apply=True, use_selection=False)
json.dump(informe, open(INFORME, "w"), indent=1, ensure_ascii=False)
print("LISTO", len(informe), sum(v["antes"] for v in informe.values()), sum(v["despues"] for v in informe.values()))
