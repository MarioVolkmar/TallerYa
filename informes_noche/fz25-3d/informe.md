# FZ25 3D desde Tripo de una sola malla: ronda 1 (21-nov, 1 h, sin commit)

## Hecho
- GLB: `garaje/static/garaje/modelos/fz25_tripo.glb` (1,17 MB, 85 mil triángulos, 44 piezas), `gltf-transform validate` sin errores ni avisos.
- Conectado en `MODELOS_TRIPO` de `moto3d/glb.js`: `"fz[ _-]*25": ".../fz25_tripo.glb?v=1"`. Carga en `/garaje/61/vista-3d/`.
- FZ25 de prueba creada para `usuario@prueba.com` (moto pk 61, línea 18 «Yamaha FZ 25»), solo en la base local.
- Despiece hecho con la skill `moto-3d-tripo` (campos por vértice, no con Blender: el modelo pesa solo 62 mil triángulos y
  no trae textura). Ficha: `.claude/skills/moto-3d-tripo/scripts/fichas/fz25.py`. El GLB de Tripo se leyó de Downloads
  y los intermedios quedaron en el scratchpad. No se tocó `privado/`.
- Escala: las llantas quedan a su medida (R 0,290 y 0,309; 100/80-17 y 140/70-17), 1,36 m entre ejes y 1,99 m de largo
  (la ficha dice 2,015 m). El aro de Tripo ya tenía su medida (talón a r 0,233): no hubo que escalar el rin.
- Luces al estilo de la Eco: `vidrio.mica_faro` (la superficie curva de Tripo, `doble`), `cromo.aro_faro` (tubo que
  sigue el borde de la mica sobre la cara de la máscara), `cromo.reflector_faro` (copa elíptica detrás) y `luz.faro`
  (dos LED de media esfera en el foco, mirando adelante); ojos LED `luz.posicion_a/b`; direccionales delanteras y
  traseras en mica `ambar.*` + `negro_brillo.carcasa_*` + vástago; `stop.stop` en la cara de atrás de la punta del colín.
- Pintura según la foto lateral: tanque y parte alta de las aletas, costados de la máscara, franja bajo el asiento y
  guardabarros delantero (el de Tripo, separado de la llanta por el ancho). Escape con `padre: escapeFabrica`; máscara
  con `rol: visor_fijo`. En la página solo quedan la pata y la placa como mallas genéricas.

## Falta (siguiente ronda)
1. **Bombillo del faro poco visible** al encender: agrandar el emisor o hacer un anillo emisivo (lo que el método de la Eco
   ya propone).
2. **Manchas oscuras en la pintura**: aletas y guardabarros tienen parches que quedaron en `chasis`/`plastico`. Llevar
   los bordes al pliegue con `lado()` y revisar con un color vivo.
3. Las llantas siguen torneadas por el visor (sin perfil fijo `extras.torno`): la integración talón-pestaña del método
   no se hizo.
4. No corrió `revisar.py`, tampoco el paso de limpieza en Blender (`geometria.py`) ni los internos de Rayos X (la ficha
   no tiene `internos`).
5. El color «Azul» de la moto pk 61 sale blanco en el visor: revisar el valor de `color` que espera el garaje.

## Para seguir
```
T=<scratchpad>/w   (extraer.py + preparar.py T 1.36 90; sin textura: copiar w_*.bin a s_*.bin)
venv/Scripts/python.exe -I $S/ciclo.py $S $T $S/fichas/fz25.py $T/salida.glb --ver "der;420;None+frente;1100;(...)"
```
Captura: la copia de `capturar_pagina.py` con `usuario@prueba.com` (el script trae fijo `moto.demo@tallerya.local`).
