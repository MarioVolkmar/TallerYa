"""Compatibilidad: la medición del modelo v2 ahora está en medir_lamina.py (es el modelo por omisión).

Equivale a:
    venv/Scripts/python.exe informes_noche/piloto-esquema/motor/medir_lamina.py <lámina> --modelo v2 [opciones]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medir_lamina  # noqa: E402

if __name__ == "__main__":
    if "--modelo" not in sys.argv:
        sys.argv += ["--modelo", "v2"]
    medir_lamina.main()
