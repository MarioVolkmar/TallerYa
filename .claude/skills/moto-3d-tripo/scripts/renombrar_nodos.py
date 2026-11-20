# Cambia el nombre (y con el, el material: "material.parte") de nodos de un GLB ya exportado, sin tocar la geometria.
#   python -I renombrar_nodos.py archivo.glb "viejo=nuevo,viejo2=nuevo2"
import json, struct, sys
ruta, pares = sys.argv[1], dict(p.split('=') for p in sys.argv[2].split(','))
b = open(ruta, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); resto = b[20 + n:]
hechos = []
for nd in j['nodes']:
    if nd.get('name') in pares:
        hechos.append(nd['name']); nd['name'] = pares[nd['name']]
for m in j.get('meshes', []):
    if m.get('name') in pares: m['name'] = pares[m['name']]
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + len(resto)) + struct.pack('<I4s', len(js), b'JSON') + js + resto
open(ruta, 'wb').write(out); print('renombrados', hechos)
