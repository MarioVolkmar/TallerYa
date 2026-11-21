#!/bin/sh
# Uso: sh medir_todo.sh <pref>   (antes: en el navegador __cap('<pref>_lat',0,2) y __cap('<pref>_lat_id',0,2,{ids:true}))
cd "$(dirname "$0")"; P=$1; F=../../../FOTOS_MODELADO_TRIPO/honda_xr_190l/1_lateral.jpg; O=caps/$P
python -I medir.py $F caps/${P}_lat.png $O | head -1
python -I iou_lleno.py $F $O
python -I color_piezas.py caps/${P}_lat.png caps/${P}_lat_id.png $F parches_lat_fijos.json ${IDS:-ids_v3.json} | tail -13
