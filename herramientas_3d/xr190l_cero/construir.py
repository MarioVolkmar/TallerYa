# XR 190L desde cero: parte la malla única de Tripo (sin textura) en piezas con nombre "material.parte" y extras del
# visor, por zonas medidas en la vista lateral, de frente y de atrás (cuadrícula de 5 cm, ver vista.py). Conserva la
# geometría de Tripo (escala uniforme por la distancia entre ejes) y suma piezas internas para Rayos X.
# Uso: blender -b --factory-startup --python construir.py -- entrada.glb salida_sin_cuantizar.glb
# Coordenadas de trabajo (Blender): X adelante, Z arriba, -Y = lado derecho (escape). Al exportar con +Y arriba quedan
# las del visor: (x, z, -y).
import bpy, bmesh, sys, math
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from comun import cargar, DIST_EJES
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ob, s = cargar(a[0])
me = ob.data
V = [v.co.copy() for v in me.vertices]

# ---- Ruedas: centro x = contacto con el piso (±dist/2); radio = extremo horizontal a la altura del eje ----
def radio(xc, signo):
    for zc in (0.31, 0.32, 0.30):
        xs = [c.x for c in V if abs(c.z - zc) < 0.012 and abs(c.y) < 0.03 and (c.x - xc) * signo > 0 and abs(c.x - xc) < 0.45]
        if xs: return max(abs(x - xc) for x in xs)
XD, XT = DIST_EJES / 2, -DIST_EJES / 2
RD, RT = radio(XD, 1), radio(XT, -1)
print("radios", round(RD, 3), round(RT, 3))

# Farola de Tripo vista de frente (y, z): bajo la ceja de la máscara (z 0,982) hasta el arco de abajo (z 0,862),
# medida en vista_farola.py; el marco es la misma figura 7 mm más grande
FAROLA = [(-0.083, 0.982), (0.083, 0.982), (0.06, 0.90), (0.035, 0.862), (-0.035, 0.862), (-0.06, 0.90)]
MARCO = [(-0.091, 0.989), (0.091, 0.989), (0.067, 0.897), (0.039, 0.855), (-0.039, 0.855), (-0.067, 0.897)]
def dentro(pol, y, z):
    d = False
    for (y1, z1), (y2, z2) in zip(pol, pol[1:] + pol[:1]):
        if (z1 > z) != (z2 > z) and y < y1 + (z - z1) * (y2 - y1) / (z2 - z1): d = not d
    return d

def zl(x):  # línea inferior del sillín (lateral): de (-0,82; 0,84) a (-0,05; 0,72)
    t = (x + 0.82) / 0.77
    return 0.84 + (0.72 - 0.84) * min(1, max(0, t))

TOPE_FORK = Vector((0.25, 0, 1.01))
def dist_fork(c):
    a_, b_ = TOPE_FORK, Vector((XD, 0, RD))
    ab = Vector((b_.x - a_.x, b_.z - a_.z)); ap = Vector((c.x - a_.x, c.z - a_.z))
    t = max(0, min(1, ap.dot(ab) / ab.length_squared))
    return (ap - ab * t).length

MEDIO_ANCHO = {"del": 0.090 / 2 + 0.004, "tras": 0.110 / 2 + 0.004}
def rueda(c, n, xc, R, lado):
    r = math.hypot(c.x - xc, c.z - R); ay = abs(c.y)
    if r > R + 0.04: return None
    if r > R - 0.075 and ay < 0.075:
        # (fuera del ancho de la ficha o del radio: costado inflado de Tripo, que el torno del visor ensanchaba;
        # se descarta y la llanta torneada lo cubre)
        if ay > MEDIO_ANCHO[lado] or r > R + 0.004: return "~descartar"
        return "caucho.llanta_" + lado
    if r > R - 0.105 and ay < 0.05: return "metal.aro_" + lado
    if r <= R - 0.105 and ay < 0.07:
        if lado == "del" and c.y < -0.022 and 0.045 < r < 0.135: return "disco.disco_del"
        if lado == "tras" and c.y > 0.022 and 0.04 < r < 0.115: return "oscuro.corona"
        return "metal.rayos_" + lado
    return None

def clasificar(c, n):
    x, y, z, ay = c.x, c.y, c.z, abs(c.y)
    # luces primero (piezas chicas con zona propia)
    if 0.32 < x < 0.47 and 0.95 < z < 1.05 and 0.14 < ay < 0.27: return "ambar.direccional_del_" + ("i" if y > 0 else "d")
    if -1.09 < x < -0.85 and 0.84 < z < 0.95 and 0.11 < ay < 0.24: return "ambar.direccional_tras_" + ("i" if y > 0 else "d")
    if x < -0.965 and 0.875 < z < 1.0 and ay < 0.075 and n.x < -0.25: return "stop.stop"
    if x > 0.42 and 0.84 < z < 1.0 and ay < 0.1 and n.x > 0.0:
        if dentro(FAROLA, y, z): return "luz.farola"
        if dentro(MARCO, y, z): return "plastico.marco_farola"
    # ruedas
    if abs(x - XD) < RD + 0.05 and z < 2 * RD:
        if not (dist_fork(c) < 0.04 and ay > 0.065):
            k = rueda(c, n, XD, RD, "del")
            if k: return k
    if abs(x - XT) < RT + 0.05 and z < 2 * RT:
        k = rueda(c, n, XT, RT, "tras")
        if k: return k
    # horquilla
    if dist_fork(c) < 0.038 and 0.035 < ay < 0.13 and 0.25 < z < 1.04 and x > 0.2:
        if z < 0.47: return "metal.barras_del"
        if z < 0.645: return "caucho.fuelles_del"
        return "oscuro.horquilla_sup"
    # espejos y manubrio
    if z > 1.11:
        return "espejo.luna" if n.x < -0.55 and z > 1.15 else "oscuro.espejos"
    if 0.0 < x < 0.32 and z > 0.97 and ay > 0.05:
        return "caucho.punos" if ay > 0.205 else "oscuro.manubrio"
    # máscara de la farola y guardabarros delantero
    if 0.30 < x < 0.60 and 0.82 < z < 1.13 and ay < 0.145: return "pintura.mascara"
    if x > 0.40 and 0.60 < z < 0.88 and ay < 0.11: return "pintura.guardabarros_del"
    # cola
    if x < -0.80 and z > 0.86: return "pintura.colin"
    if x < -0.80: return "plastico.guardabarros_tras"
    if -0.82 < x < -0.55 and 0.78 < z < 0.95 and ay > 0.115: return "chasis.parrilla"
    # sillín
    if -0.82 < x < -0.04 and z > zl(x) and ay < (0.13 if x < -0.55 else 0.16): return "asiento.sillin"
    # escape (lado derecho = -y)
    if y < -0.06 and -0.88 < x < -0.40 and 0.45 < z < 0.88: return "titanio.silenciador"
    if y < -0.08 and -0.15 < x < 0.26 and 0.45 < z < 0.56 and ay > 0.09: return "titanio.tubo_escape"
    # tapas laterales: blanca adelante, negra atrás
    if -0.56 < x < -0.04 and 0.44 < z < zl(x) + 0.01 and ay > 0.065: return "blanco.tapa_lateral_" + ("i" if y > 0 else "d")
    if -0.85 < x < -0.40 and 0.45 < z < 0.9 and ay > 0.05: return "plastico.tapa_trasera"
    # tanque y aletas
    if -0.10 < x < 0.42 and 0.62 < z < 1.03:
        if ay < 0.075 and z > 0.90: return "plastico.tanque"
        if z < 0.67: return "plastico.aletas_bajo"
        return "pintura.aletas"
    # motor
    if -0.21 < x < 0.26 and 0.17 < z < 0.66 and ay < 0.17: return "motor.motor"
    # basculante y estribos
    if -0.80 < x < -0.15 and 0.20 < z < 0.48: return "metal.basculante"
    if z < 0.40 and ay > 0.15: return "oscuro.estribos"
    return "chasis.chasis"

bm = bmesh.new(); bm.from_mesh(me)
# Cortes rectos antes de clasificar: el borde entre piezas sigue el plano y no los triángulos (sin dientes)
def cortar(co, no, filtro):
    caras = [f for f in bm.faces if filtro(f.calc_center_median())]
    geom = list({e for f in caras for e in f.edges}) + caras + list({v for f in caras for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
farola = lambda c: c.x > 0.40 and 0.83 < c.z < 1.01 and abs(c.y) < 0.11
for pol in (FAROLA, MARCO):
    for (y1, z1), (y2, z2) in zip(pol, pol[1:] + pol[:1]):
        cortar((0, y1, z1), (0, -(z2 - z1), y2 - y1), farola)
panel = lambda c: -0.62 < c.x < 0.02 and 0.38 < c.z < 0.9 and abs(c.y) > 0.05
cortar((-0.43, 0, zl(-0.43)), (0.12, 0, 0.77), panel)
cortar((-0.04, 0, 0), (1, 0, 0), panel); cortar((-0.56, 0, 0), (1, 0, 0), panel); cortar((0, 0, 0.44), (0, 0, 1), panel)
aleta = lambda c: -0.12 < c.x < 0.44 and 0.58 < c.z < 1.04
cortar((0, 0, 0.67), (0, 0, 1), aleta); cortar((0, 0, 0.90), (0, 0, 1), lambda c: aleta(c) and abs(c.y) < 0.1)
cortar((0, 0, 0.47), (0, 0, 1), lambda c: dist_fork(c) < 0.05); cortar((0, 0, 0.645), (0, 0, 1), lambda c: dist_fork(c) < 0.05)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.faces.index_update(); bm.faces.ensure_lookup_table()
etiqueta = [clasificar(f.calc_center_median(), f.normal) for f in bm.faces]
# Suavizado: una cara rodeada por otra pieza (≥2 de 3 vecinas) se pasa a esa (quita dientes y motas sueltas);
# las luces y ruedas no se tocan (sus bordes son geométricos)
fijas = ("luz.", "stop.", "ambar.", "caucho.llanta", "metal.aro", "disco.", "plastico.marco", "~")
for _ in range(3):
    nueva = list(etiqueta)
    for f in bm.faces:
        if etiqueta[f.index].startswith(fijas): continue
        vec = {}
        for e in f.edges:
            for g in e.link_faces:
                if g is not f: vec[etiqueta[g.index]] = vec.get(etiqueta[g.index], 0) + 1
        mejor = max(vec.items(), key=lambda kv: kv[1]) if vec else None
        if mejor and mejor[0] != etiqueta[f.index] and mejor[1] >= 2 and not mejor[0].startswith(fijas): nueva[f.index] = mejor[0]
    etiqueta = nueva

grupos = {}
for i, e in enumerate(etiqueta): grupos.setdefault(e, []).append(i)
print("descartadas", len(grupos.pop("~descartar", [])))
print("piezas", {k: len(v) for k, v in sorted(grupos.items())})

EXTRAS = {
    "caucho.llanta_del": {"pieza": "llanta_del", "eje": [XD, RD], "torno": "redondo"},
    "caucho.llanta_tras": {"pieza": "llanta_tras", "eje": [XT, RT], "torno": "redondo"},
    "metal.aro_del": {"pieza": "llanta_del", "eje": [XD, RD], "aro": True, "doble": True},
    "metal.aro_tras": {"pieza": "llanta_tras", "eje": [XT, RT], "aro": True, "doble": True},
    "metal.rayos_del": {"pieza": "llanta_del", "eje": [XD, RD], "rin": True},
    "metal.rayos_tras": {"pieza": "llanta_tras", "eje": [XT, RT], "rin": True},
    "disco.disco_del": {"pieza": "llanta_del", "eje": [XD, RD]},
    "oscuro.corona": {"pieza": "llanta_tras", "eje": [XT, RT]},
    "luz.farola": {"lampara": {"tipo": "faro"}},
    "stop.stop": {"lampara": {"tipo": "stop"}},
    "metal.barras_del": {"pieza": "suspension_del"}, "caucho.fuelles_del": {"pieza": "suspension_del"},
    "oscuro.horquilla_sup": {"pieza": "suspension_del"},
    "motor.motor": {"pieza": "motor", "tono": "#34383b"},
    "titanio.silenciador": {"padre": "escapeFabrica"}, "titanio.tubo_escape": {"padre": "escapeFabrica"},
    "blanco.tapa_lateral_i": {"tono": "#eef0f2"}, "blanco.tapa_lateral_d": {"tono": "#eef0f2"},
    "plastico.guardabarros_tras": {"doble": True, "placa": {"c": [-1.035, 0.63, 0], "incl": -0.5, "tam": [0.2, 0.15]}},
    "pintura.guardabarros_del": {"doble": True},
    # (los espejos de Tripo hacen de espejos de fábrica: así el genérico no sale encima y Personalizar los cambia)
    "oscuro.espejos": {"padre": "espejos.fabrica"}, "espejo.luna": {"padre": "espejos.fabrica"},
    # (la máscara reemplaza al visor genérico, que salía como una lámina blanca sobre la farola)
    "pintura.mascara": {"rol": "visor_fijo"},
    "chasis.chasis": {"tono": "#1d2023", "sin": ["espejos.puntas"]},
}
for k in [k for k in grupos if k.startswith("ambar.direccional")]: EXTRAS[k] = {"lampara": {"tipo": "direccional"}}

def poner_extras(o, ex):
    for k, v in ex.items(): o[k] = v

objetos = []
for nombre, caras in grupos.items():
    nb = bm.copy(); nb.faces.index_update()
    keep = set(caras)
    nb.faces.ensure_lookup_table()
    bmesh.ops.delete(nb, geom=[f for f in nb.faces if f.index not in keep], context='FACES')
    nm = bpy.data.meshes.new(nombre); nb.to_mesh(nm); nb.free()
    o = bpy.data.objects.new(nombre, nm); bpy.context.scene.collection.objects.link(o)
    poner_extras(o, EXTRAS.get(nombre, {}))
    objetos.append(o)
bpy.data.objects.remove(ob)

# ---- Piezas internas (solo en Rayos X): motor de 190 cc por dentro, inyección, filtro, batería, cableado ----
def caja(nombre, c, d, ex, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot); o = bpy.context.object
    o.scale = d; bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.name = nombre; o.data.name = nombre; poner_extras(o, dict(ex, interno=True)); return o
def cil(nombre, c, r, h, ex, rot=(math.pi / 2, 0, 0), v=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=c, rotation=rot); o = bpy.context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.name = nombre; o.data.name = nombre; poner_extras(o, dict(ex, interno=True)); return o
def tubo(nombre, pts, r, ex):
    cu = bpy.data.curves.new(nombre, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 1
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new(nombre, cu); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.convert(target='MESH'); o.select_set(False)
    o.name = nombre; poner_extras(o, dict(ex, interno=True)); return o
INCL = math.radians(-14)  # (cilindro inclinado hacia adelante)
m = {"pieza": "motor"}
cil("cromo.piston", (0.062, 0, 0.555), 0.031, 0.04, m, rot=(0, INCL, 0))
cil("metal.biela", (0.045, 0, 0.47), 0.008, 0.13, m, rot=(0, INCL, 0), v=8)
cil("metal.ciguenal", (0.03, 0, 0.40), 0.052, 0.05, m)
cil("metal.eje_ciguenal", (0.03, 0, 0.40), 0.012, 0.22, m, v=10)
for i, (dx, dz, r) in enumerate([(-0.07, 0.40, 0.032), (-0.07, 0.40, 0.022), (-0.13, 0.37, 0.036), (-0.13, 0.37, 0.026)]):
    cil(f"metal.caja_engranaje_{i + 1}", (dx, 0.025 * (i % 2 * 2 - 1), dz), r, 0.014, m, v=24)
cil("carter.clutch", (-0.02, -0.105, 0.39), 0.058, 0.03, m, v=24)
cil("carter.magneto", (0.03, 0.10, 0.40), 0.05, 0.025, m, v=24)
caja("aceiteVisible.aceite", (-0.03, 0, 0.255), (0.16, 0.09, 0.03), {"pieza": "aceite"})
cil("bujia.bujia", (0.108, 0.035, 0.655), 0.008, 0.05, {"pieza": "bujia"}, rot=(0.6, INCL, 0), v=8)
caja("oscuro.filtro_aire", (-0.21, 0, 0.68), (0.17, 0.15, 0.13), {"pieza": "filtro_aire"})
cil("metal.cuerpo_aceleracion", (-0.075, 0, 0.62), 0.019, 0.08, m, rot=(0, math.radians(70), 0), v=12)
cil("oscuro.inyector", (-0.06, 0, 0.66), 0.006, 0.04, m, rot=(0, 0.3, 0), v=8)
caja("bateria.bateria", (-0.40, 0, 0.71), (0.11, 0.08, 0.09), {"pieza": "bateria"})
cil("resorte.amortiguador", (-0.26, 0, 0.58), 0.032, 0.30, {"pieza": "suspension_tras"}, rot=(0, math.radians(-25), 0), v=14)
tubo("oscuro.cableado", [(-0.40, 0.03, 0.76), (-0.25, 0.06, 0.80), (0.0, 0.06, 0.82), (0.24, 0.05, 0.92), (0.40, 0.03, 0.96)], 0.006, {})
tubo("oscuro.cableado_cola", [(-0.40, -0.03, 0.76), (-0.70, -0.04, 0.84), (-0.95, -0.03, 0.90)], 0.005, {})
tubo("oscuro.cable_bujia", [(-0.33, 0.02, 0.72), (-0.05, 0.06, 0.70), (0.11, 0.05, 0.67)], 0.004, {})

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB', export_extras=True, export_yup=True, export_materials='NONE',
                          export_apply=True, export_texcoords=False, export_normals=True, use_selection=False)
print("listo", len(bpy.context.scene.objects))
