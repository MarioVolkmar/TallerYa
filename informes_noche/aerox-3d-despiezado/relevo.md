# Relevo Aerox 155 despiezado: ronda 2 HECHA (21-nov, tripo3 ?v=7); ver «Ronda 2» en informe.md

Pendiente para una ronda 3: faros poco vivos (bombillo 2 mm detrás de la mica); bordes de Tripo serrados en las micas de los faros; partes sin identificar en oscuro.piezas; pasar Eco Deluxe y XR 190L a extras.rueda (no tocadas).

## Lo que pedía la ronda 2 (ya hecho)

Estado: `garaje/static/garaje/modelos/aerox155_tripo3.glb` en `?v=4` (`MODELOS_TRIPO.aerox` en `moto3d/glb.js`). Sin commit. NO cambiar de rama (la carpeta está en `piloto` y otra sesión trabaja ahí): nada de `git checkout`; tocar solo el GLB de la Aerox, su entrada en `glb.js`, `herramientas_3d/aerox155/` y los informes de esta carpeta.
Leer primero `informe.md` (en esta carpeta) y `herramientas_3d/aerox155/armar.py`. No hace falta releer el método de la Eco.

## Flujo (un comando por paso; intermedios en el scratchpad)
1. `venv/Scripts/python.exe -I herramientas_3d/aerox155/armar.py privado/tripo/aerox155_despiece/modelo-3d-despiece-aerox155.glb <scratch>/armado.glb`
2. `"/c/Program Files/Blender Foundation/Blender 5.3/blender.exe" -b --factory-startup --python herramientas_3d/aerox155/geometria.py -- <scratch>/armado.glb <scratch>/blender.glb <scratch>/geo.json > log`
3. `venv/Scripts/python.exe -I herramientas_3d/aerox155/final.py <scratch>/armado.glb <scratch>/blender.glb garaje/static/garaje/modelos/aerox155_tripo2.glb garaje/static/garaje/modelos/aerox155_tripo3.glb`
4. `npx gltf-transform validate` y subir `?v=` en glb.js.
Moto de prueba: pk 59 (`usuario@prueba.com`, ya logueado en el preview «tallerya»). En `/garaje/59/` están los botones Rayos X/Moto, Personalizar, Encender, Noche.
Captura: `__visor.vista(x,y,z)`, esperar 1,5 s, `__visor.cuadro()`, `zoom` de la región; el PNG que deja la herramienta en tool-results se copia con PIL.

## Correcciones pedidas por el usuario (en orden)
1. **Pintura solo en la carrocería pintada.** Hoy en `pintura.*` van las partes 12, 32, 42 (carenado), 34+8 (frente), 45+37 y 40 (escudos), 74 y 16 (tapas laterales), 27+19 (colín) y 14 (guardabarros del.). Revisar contra `FOTOS_MODELADO_TRIPO/yamaha_aerox_155/` (la foto 2 es negra mate): pisaderas, bajos, guardabarros interno, tapas, interior del escudo, a `plastico` negro mate o texturizado. Mapa de partes: `vistas.py` del scratchpad anterior (render plano por parte con su número; rehacerlo si no está: PIL puro, unas 40 líneas).
2. **Tonos parejos:** quitar `extras.acabado` de las piezas pintadas y dejar un solo acabado por material (hoy `acabado` crea material propio por nodo; ver glb.js ~l. 396).
3. **Transparencias:** solo micas (`vidrio.*`) y visor. Hoy `doble=True` va en casi todo; revisar en el visor qué mallas quedan `transparent`/`opacity<1` (en v4 había varias) y por qué.
4. **Llantas de Tripo, sin torneado:** el visor tornea toda `caucho.*llanta*` con `eje` (glb.js `tornearLlanta`, ~l. 274 y ~l. 393). Agregar un extra, p. ej. `torno: "no"`, que el visor respete solo en los GLB que lo pidan, y no cambiar el resto de las motos. Llanta de Tripo integrada con el rin (talón 0,196 contra pestaña 0,200 m: ya calzan) y sin restos sueltos. Hoy la llanta lleva Decimate 0,2: subirlo (unos 0,6) porque ahora se ve.
5. **Bordes aserrados:** los cortes por triángulo (llanta/rin delantero por radio, `por_tri`) y los bordes de Tripo. Usar `cortar()` por planos o bisect, unir vértices y suavizado por ángulo.
6. **Placa** en su soporte trasero (parte 2, `plastico.portaplaca`), con su tamaño y su inclinación reales: hoy `incl` sale de la pendiente de la caja y no se revisó.
7. **Tablero:** la `pantalla` está en el `oscuro.manubrio` con un punto inventado. Según las fotos va en el carenado frontal, detrás del visor (parte 30): medir el punto y la normal.

## Trampas
- Un solo Blender a la vez (8 GB). Límite 1 h, sin commit. Capturas nuevas: `arreglo_lateral.png`, `arreglo_tres_cuartos.png`, `arreglo_luces.png`.
- Verificar a 1280 y a 375 px, Personalizar con rojo vivo (no debe pasar a ruedas ni a plásticos) y Rayos X.
- La página pública corre desde `C:\dev\TallerYa-produccion`: no tocarla.
- Faros: siguen poco vivos (mica gris; el bombillo va 2 mm detrás de la mica porque la carrocería no tiene hueco).
