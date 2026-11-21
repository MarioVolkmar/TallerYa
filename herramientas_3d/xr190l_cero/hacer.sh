#!/bin/sh
# Construye xr190l_tripo4.glb de punta a punta: Blender (piezas) → cuantizar → un bufferView por accessor → validar
S=${1:?carpeta temporal}
cd "$(dirname "$0")/../.."
"/c/Program Files/Blender Foundation/Blender 5.3/blender.exe" -b --factory-startup --python herramientas_3d/xr190l_cero/construir.py -- privado/tripo/xr190l_cero/modelo-3d-xr190l.glb "$S/xr_raw.glb" > "$S/construir.log" 2>&1
grep -E "radios|rror" "$S/construir.log" | head -5
npx gltf-transform quantize "$S/xr_raw.glb" garaje/static/garaje/modelos/xr190l_tripo4.glb --quantize-position 16 --quantize-normal 8 > "$S/q.log" 2>&1
venv/Scripts/python.exe -I herramientas_3d/xr190l_cero/separar_vistas.py garaje/static/garaje/modelos/xr190l_tripo4.glb
npx gltf-transform validate garaje/static/garaje/modelos/xr190l_tripo4.glb 2>&1 | grep -iE "no errors|no warnings"
