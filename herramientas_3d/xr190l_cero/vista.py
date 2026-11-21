# Vistas ortográficas con cuadrícula de 5 cm (render workbench + líneas dibujadas como objetos) para ubicar zonas.
import bpy, sys, math
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from comun import cargar
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
ob, s = cargar(a[0])
print("escala", s, "dims", tuple(round(d, 3) for d in ob.dimensions))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (0.8, 0.8, 0.8)
mat = bpy.data.materials.new("g"); mat.diffuse_color = (1, 0, 0, 1)
def linea(p, q, grueso):
    d = q - p; bpy.ops.mesh.primitive_cube_add(size=1, location=(p + q) / 2)
    c = bpy.context.object; c.scale = (max(abs(d.x), grueso), max(abs(d.y), grueso), max(abs(d.z), grueso)); c.data.materials.append(mat)
    c.color = (1, 0, 0, 1)
sc.display.shading.color_type = 'OBJECT'; ob.color = (0.8, 0.8, 0.8, 1)
for i in range(-26, 27):
    x = i * 0.05; g = 0.004 if i % 4 == 0 else 0.0012
    linea(Vector((x, 0.6, 0)), Vector((x, 0.6, 1.3)), g)
for j in range(0, 27):
    z = j * 0.05; g = 0.004 if j % 4 == 0 else 0.0012
    linea(Vector((-1.3, 0.6, z)), Vector((1.3, 0.6, z)), g)
sc.render.resolution_x = 1300; sc.render.resolution_y = 650
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 2.6
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0, -4, 0.65); co.rotation_euler = (math.pi / 2, 0, 0)   # mirando el lado derecho (z<0 del visor)
if len(a) < 3:
    sc.render.filepath = a[1] + "_derecha.png"; bpy.ops.render.render(write_still=True)
else:
    # vistas de frente y de atrás (cuadrícula en el plano x = ±1,2), 1,3 m de lado
    for o in [o for o in sc.objects if o.name.startswith("Cube")]: bpy.data.objects.remove(o)
    for xs, nombre, rot in [(1.25, "frente", (math.pi/2, 0, math.pi/2)), (-1.25, "atras", (math.pi/2, 0, -math.pi/2))]:
        for o in [o for o in sc.objects if o.name.startswith("Cube")]: bpy.data.objects.remove(o)
        for i in range(-13, 14):
            g = 0.004 if i % 4 == 0 else 0.0012
            linea(Vector((-xs, i*0.05, 0)), Vector((-xs, i*0.05, 1.3)), g)
        for j in range(0, 27):
            g = 0.004 if j % 4 == 0 else 0.0012
            linea(Vector((-xs, -0.65, j*0.05)), Vector((-xs, 0.65, j*0.05)), g)
        sc.render.resolution_x = 650; cam.ortho_scale = 1.3
        co.location = (xs * 3, 0, 0.65); co.rotation_euler = rot
        sc.render.filepath = a[1] + "_" + nombre + ".png"; bpy.ops.render.render(write_still=True)
