"""Paso 4 (python del sistema): despiece cortado en Blender → xr190l_tripo3.glb con el formato del visor.
Reutiliza construir.py (MAPA de materiales PBR por pieza, luces, piezas internas de Rayos X, cuantización) cambiando
solo la entrada, la salida y la tapa lateral (material pintura2, blanco de fábrica fijo).
Uso: python -I construir3.py DIR   (lee DIR/despiece.npz)"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun  # noqa: E402

comun.TRABAJO = Path(sys.argv[1])
src = (AQUI.parent / "construir.py").read_text(encoding="utf-8")
src = src.replace("xr190l_tripo2.glb", "xr190l_tripo3.glb").replace("método herramientas_3d/xr190l", "Blender, herramientas_3d/xr190l/blender")
src = src.replace('"tapa_lateral": ("blanco",', '"tapa_lateral": ("pintura2",')
exec(compile(src, str(AQUI.parent / "construir.py"), "exec"), {"__name__": "__main__", "__file__": str(AQUI.parent / "construir.py")})
