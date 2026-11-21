# Acercamiento a la máscara: de frente y de lado (cuadrícula de 1 cm en el fondo) para ubicar la farola de Tripo.
import bpy, sys, math
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from comun import cargar
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
ob, s = cargar(a[0])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
sc.display.shading.cavity_ridge_factor = 2; sc.display.shading.cavity_valley_factor = 2
sc.display.shading.color_type = 'OBJECT'; ob.color = (0.8, 0.8, 0.8, 1)
mat = bpy.data.materials.new("g")
def linea(p, q, g):
    d = q - p; bpy.ops.mesh.primitive_cube_add(size=1, location=(p + q) / 2); c = bpy.context.object
    c.scale = (max(abs(d.x), g), max(abs(d.y), g), max(abs(d.z), g)); c.color = (1, 0, 0, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 0.4
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
sc.render.resolution_x = 640; sc.render.resolution_y = 640
# de frente: cuadrícula en x = 0.2 (detrás de la máscara), y de -0.2 a 0.2, z de 0.77 a 1.17
for i in range(-20, 21):
    g = 0.0012 if i % 5 else 0.0025
    linea(Vector((0.2, i * 0.01, 0.77)), Vector((0.2, i * 0.01, 1.17)), g)
for j in range(0, 41):
    g = 0.0012 if j % 5 else 0.0025
    linea(Vector((0.2, -0.2, 0.77 + j * 0.01)), Vector((0.2, 0.2, 0.77 + j * 0.01)), g)
co.location = (3, 0, 0.97); co.rotation_euler = (math.pi / 2, 0, math.pi / 2)
sc.render.filepath = a[1] + "_farola_frente.png"; bpy.ops.render.render(write_still=True)
