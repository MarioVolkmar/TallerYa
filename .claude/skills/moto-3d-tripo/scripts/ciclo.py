# Una vuelta completa en un solo comando: cortar -> (aligerar por pieza) -> internos -> exportar, con cronometro.
#   python -I ciclo.py S T fichas/<moto>.py salida.glb [--ver "der;900;None+atras;1500;((..),(..))"] [--solo stop,faro]
#                                                      [--hasta cortar] [--N carpeta_con_meshoptimizer]
# La ficha es un modulo con:  cortar(m)  (reglas sobre un motor.Corte)  y, opcional,  internos(k)  (motor.Internos),
# ALISAR ({pieza: vueltas} de alisado de la superficie), SUAVE (vueltas de alisado de normales en las piezas lisas), RAZON (lista [expresion regular, razon] para por_pieza.mjs; sin ella no se aligera: sirve cuando el modelo ya llega
# liviano) y MEZCLA (cuanto pesa la normal geometrica en las piezas lisas al exportar).
import importlib.util
import json
import os
import shutil
import subprocess
import sys

S, T, ruta_ficha, salida = sys.argv[1:5]
sys.path.insert(0, S)
import motor  # noqa: E402


def opcion(nombre, defecto=None):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


reloj = motor.Reloj(T)
spec = importlib.util.spec_from_file_location("ficha", ruta_ficha)
ficha = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ficha)
m = motor.Corte(T)
reloj.paso("cargar")
ficha.cortar(m)
reloj.paso("reglas")
m.cortar(**getattr(ficha, "ISLAS", {}))
reloj.paso("repartir")
m.resumen()
if opcion("--ver"):
    solo = opcion("--solo")
    m.ver(opcion("--ver"), f"{T}/corte.png", solo.split(",") if solo else None)
    reloj.paso("ver")
if opcion("--hasta") == "cortar":
    reloj.cerrar(ficha=os.path.basename(ruta_ficha))
    sys.exit()

razon = getattr(ficha, "RAZON", None)
if razon:
    json.dump(razon, open(f"{T}/razon.json", "w"))
    N = opcion("--N")
    subprocess.run(["node", os.path.join(N, "por_pieza.mjs"), T], check=True, stdout=subprocess.DEVNULL)
else:
    for a in ("pos", "nor", "col", "idx", "lab"):
        shutil.copyfile(f"{T}/c_{a}.bin", f"{T}/p_{a}.bin")
reloj.paso("aligerar")

if hasattr(ficha, "internos"):
    k = motor.Internos(T)
    ficha.internos(k)
    n, tot = k.guardar()
    print("piezas internas", n, "triangulos", tot)
else:
    for a in ("i_extra.npz", "i_extras.json"):
        if os.path.exists(f"{T}/{a}"):
            os.remove(f"{T}/{a}")
reloj.paso("internos")

import exportar  # noqa: E402
exportar.exportar(S, T, salida, mezcla=getattr(ficha, "MEZCLA", 0.75), lisas=getattr(ficha, "LISAS", None), suave=getattr(ficha, "SUAVE", 0), alisar=getattr(ficha, "ALISAR", None))
reloj.paso("exportar")
reloj.cerrar(ficha=os.path.basename(ruta_ficha))
