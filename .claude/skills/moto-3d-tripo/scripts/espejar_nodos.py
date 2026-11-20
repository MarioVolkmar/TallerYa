# Espeja en z (plano medio) los nodos nombrados de un GLB cuantizado: posiciones y normales con z negada y triangulos al reves.
import json, struct, sys, numpy as np
ruta, nombres = sys.argv[1], sys.argv[2].split(',')
b = bytearray(open(ruta, 'rb').read()); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); base = 20 + n + 8
T = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
C = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def vista(i):
    a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; t = np.dtype(T[a['componentType']]); c = C[a['type']]
    st = v.get('byteStride', t.itemsize * c); off = base + v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return a, t, c, st, off
hechos = []
for nd in j['nodes']:
    if nd.get('name') not in nombres: continue
    pr = j['meshes'][nd['mesh']]['primitives'][0]
    for atr in ('POSITION', 'NORMAL'):
        if atr not in pr['attributes']: continue
        a, t, c, st, off = vista(pr['attributes'][atr])
        for k in range(a['count']):
            o = off + k * st + 2 * t.itemsize
            val = np.frombuffer(b, t, 1, o)[0]
            b[o:o + t.itemsize] = np.array([-val], t).tobytes()
        if 'min' in a and 'max' in a:
            a['min'][2], a['max'][2] = -a['max'][2], -a['min'][2]
    a, t, c, st, off = vista(pr['indices'])
    idx = np.frombuffer(bytes(b[off:off + a['count'] * t.itemsize]), t).reshape(-1, 3)[:, [0, 2, 1]].copy()
    b[off:off + a['count'] * t.itemsize] = idx.tobytes()
    tr = nd.get('translation');
    if tr: tr[2] = -tr[2]
    if 'rotation' in nd: raise SystemExit('nodo con rotacion: no soportado')
    hechos.append(nd['name'])
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
if len(js) != n: raise SystemExit(f'el JSON cambio de largo ({n} -> {len(js)}): rehacer con relleno')
b[20:20 + n] = js
open(ruta, 'wb').write(b); print('espejados', hechos)
