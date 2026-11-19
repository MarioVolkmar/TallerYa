# Extrae del GLB de entrada: posiciones, normales, uv, indices (npy) y las 3 texturas
import sys, json, struct, numpy as np, os
p, sal = sys.argv[1], sys.argv[2]
b = open(p, 'rb').read()
ln = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20+ln]); base = 20 + ln + 8
acc, bv = j['accessors'], j['bufferViews']
T = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
C = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def leer(i):
    a = acc[i]; v = bv[a['bufferView']]; t = np.dtype(T[a['componentType']]); c = C[a['type']]
    off = base + v.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = v.get('byteStride')
    if st and st != t.itemsize * c:
        raw = np.frombuffer(b, np.uint8, a['count'] * st, off).reshape(-1, st)[:, :t.itemsize * c]
        return np.ascontiguousarray(raw).view(t).reshape(-1, c)
    return np.frombuffer(b, t, a['count'] * c, off).reshape(-1, c)
pr = j['meshes'][0]['primitives'][0]
print('atributos', pr['attributes'], 'nodo', {k: v for k, v in j['nodes'][0].items() if k != 'name'})
np.save(os.path.join(sal, 'pos.npy'), leer(pr['attributes']['POSITION']).astype(np.float32))
np.save(os.path.join(sal, 'nor.npy'), leer(pr['attributes']['NORMAL']).astype(np.float32))
np.save(os.path.join(sal, 'uv.npy'), leer(pr['attributes']['TEXCOORD_0']).astype(np.float32))
np.save(os.path.join(sal, 'idx.npy'), leer(pr['indices']).astype(np.uint32).reshape(-1, 3))
for im in j['images']:
    v = bv[im['bufferView']]
    open(os.path.join(sal, im['name'].split('_')[-1] + '.jpg'), 'wb').write(b[base + v['byteOffset']: base + v['byteOffset'] + v['byteLength']])
print('materiales', json.dumps(j['materials'])[:400])
