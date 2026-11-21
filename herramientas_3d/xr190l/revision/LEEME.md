# Revisora XR 190L: cómo se mide (ronda 1, 20-nov)
- proxy.py (127.0.0.1:8767 → localhost:8001, sin CSP, POST /__guardar/<n> guarda en caps/). Abrir http://localhost:8766/garaje/38/vista-3d/ (misma cookie).
- En la página, definir __cap(nombre, az, el, {fov:14}) (cámara a 12 m, oculta piso y sombra, guarda PNG). Lateral = az 0, el 2.
- Pasada de ID: materiales planos por pieza (ids.json, con codificación sRGB), luces apagadas → id_lat_2.png.
- medir.py foto render pref → IoU + pref_alin.npz; parches.py → parches automáticos; color_piezas.py render id foto parches_lat_fijos.json → ΔE por pieza.
- R1: IoU lateral 0,760, color 25 %. Revisión en informes_noche/xr190l-3d-nuevo/revision.md
- R2 (v3): IoU lateral sin sombra 0,817 (iou_lleno.py), color 8 %, 3/4 0,60. ids_v3.json = nombres de v3. /garaje/38/ no carga el visor en el panel (sw.js): Rayos X sin verificar.
- R3 (v5): color 33 %, IoU lateral 0,836 (relleno 0,924); Rayos X ok con http://localhost:8767/garaje/38/vista-3d/?rayos=1 (proxy cambia data-modo).
- R4 (revisora nueva): copia en herramientas_3d/xr190l/revision/. Proxy en 8767 (python -I proxy.py; sirve /__js/<archivo> de esta carpeta). En la página: eval(await (await fetch('/__js/cap.js')).text()); idsMapa = await (await fetch('/__js/ids_v3.json')).json(); __cap('vN_lat',0,2); __cap('vN_lat_id',0,2,{ids:true}); luego sh medir_todo.sh vN. Calibración v5: IoU sin sombra 0,838, color 5/12.
