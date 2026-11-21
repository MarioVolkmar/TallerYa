# Analiza el GLB de Tripo: componentes sueltos y render lateral/frontal (workbench) para ubicar piezas.
import bpy, bmesh, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]
src, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
print("verts", len(me.vertices), "tris", len(me.polygons), "dims", tuple(round(d,3) for d in ob.dimensions))
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st=[v]; seen.add(v.index); ids=[]
    while st:
        a=st.pop(); ids.append(a.index)
        for e in a.link_edges:
            b=e.other_vert(a)
            if b.index not in seen: seen.add(b.index); st.append(b)
    co=[bm.verts[i].co for i in ids]
    mn=Vector((min(c.x for c in co),min(c.y for c in co),min(c.z for c in co)))
    mx=Vector((max(c.x for c in co),max(c.y for c in co),max(c.z for c in co)))
    comps.append((len(ids),mn,mx))
comps.sort(key=lambda c:-c[0])
print("componentes", len(comps))
for n,mn,mx in comps[:25]: print(n, [round(x,3) for x in mn], [round(x,3) for x in mx])
# render
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='SINGLE'
sc.render.resolution_x=900; sc.render.resolution_y=560
cam=bpy.data.cameras.new("c"); cam.type='ORTHO'; cam.ortho_scale=1.1
co=bpy.data.objects.new("c",cam); sc.collection.objects.link(co); sc.camera=co
c=ob.matrix_world @ (sum((Vector(b) for b in ob.bound_box),Vector())/8)
for nombre,pos,rot in [("lado_x",(3,0,0),(math.pi/2,0,math.pi/2)),("frente",(0,-3,0),(math.pi/2,0,0))]:
    co.location=c+Vector(pos); co.rotation_euler=rot
    sc.render.filepath=out+"_"+nombre+".png"; bpy.ops.render.render(write_still=True)
