# Marca (o desmarca) un GLB del visor en modo «modelo completo»: extras.modelo_completo en la escena.
# El visor lo muestra tal cual (solo gira ruedas, luces, Personalizar y Rayos X). Reescribe solo el bloque JSON.
# Uso: python -I marcar_completo.py archivo.glb [--quitar]
import json, struct, sys
ruta = sys.argv[1]; quitar = "--quitar" in sys.argv
b = open(ruta, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
j = json.loads(b[20:20 + n]); resto = b[20 + n:]
esc = j["scenes"][j.get("scene", 0)]
ex = esc.setdefault("extras", {})
if quitar: ex.pop("modelo_completo", None)
else: ex["modelo_completo"] = True
if not ex: esc.pop("extras")
t = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
t += b" " * (-len(t) % 4)
cuerpo = struct.pack("<II", len(t), 0x4E4F534A) + t + resto
open(ruta, "wb").write(b[:8] + struct.pack("<I", 12 + len(cuerpo)) + cuerpo)
print(ruta, "escena:", esc.get("extras"))
