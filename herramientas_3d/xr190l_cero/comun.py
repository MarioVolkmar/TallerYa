# Común: importa el GLB de Tripo y lo deja en coordenadas del visor (en Blender: X adelante, Z arriba, -Y = z del visor),
# escala uniforme por la distancia entre ejes de la ficha (1,355 m), piso en z=0 y punto medio entre ejes en x=0.
import bpy, math
from mathutils import Vector, Matrix
DIST_EJES = 1.355
def cargar(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    # (adelante de Tripo, -Y de Blender, pasa a +X; rotación, sin espejo; se aplica a la malla con la del padre)
    ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z') @ ob.matrix_world)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4)
    for o in list(bpy.context.scene.objects):
        if o is not ob: bpy.data.objects.remove(o)
    me = ob.data
    zs = [v.co.z for v in me.vertices]; zmin = min(zs)
    # Centros de rueda: punto más bajo de cada mitad = contacto con el piso
    def contacto(sel):
        vs = [v.co for v in me.vertices if sel(v.co.x)]
        lo = min(c.z for c in vs)
        xs = [c.x for c in vs if c.z < lo + 0.004]
        return sum(xs) / len(xs)
    xd = contacto(lambda x: x > 0.15); xt = contacto(lambda x: x < -0.15)
    s = DIST_EJES / (xd - xt)
    for v in me.vertices:
        v.co = Vector(((v.co.x - (xd + xt) / 2) * s, v.co.y * s, (v.co.z - zmin) * s))
    me.update()
    return ob, s
