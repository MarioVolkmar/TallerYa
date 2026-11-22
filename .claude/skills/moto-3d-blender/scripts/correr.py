# Un comando para todo el ciclo: armar -> revisar -> imagen-resumen (Blender sin ventana, uno solo a la vez).
# Uso (desde la raíz del proyecto): python -I .claude/skills/moto-3d-blender/scripts/correr.py fichas/<moto>.json carpeta_informe
import sys, os, json, subprocess
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
ficha = sys.argv[1] if os.path.exists(sys.argv[1]) else os.path.join(AQUI, "..", sys.argv[1])
informe = os.path.join(RAIZ, sys.argv[2]); os.makedirs(informe, exist_ok=True)
F = json.load(open(ficha, encoding="utf-8")); glb = os.path.join(RAIZ, F["salida"])
py = [sys.executable, "-I"]
subprocess.run(py + [os.path.join(AQUI, "armar.py"), ficha], check=True)
rev = subprocess.run(py + [os.path.join(AQUI, "revisar.py"), glb], cwd=RAIZ)
log = os.path.join(informe, "blender_resumen.log")
with open(log, "w") as fl:
    subprocess.run([BLENDER, "-b", "--factory-startup", "--gpu-backend", "opengl", "--python", os.path.join(AQUI, "resumen.py"), "--",
                    glb, os.path.join(RAIZ, F["fotos"]), os.path.join(informe, "resumen.png")], stdout=fl, stderr=subprocess.STDOUT, check=True)
print("resumen:", os.path.join(informe, "resumen.png"), "| revisión:", "OK" if rev.returncode == 0 else "CON FALLAS")
sys.exit(rev.returncode)
