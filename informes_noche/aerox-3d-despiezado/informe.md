# Aerox 155 desde Tripo despiezado (método Eco Deluxe) — 21-nov

Resultado: `garaje/static/garaje/modelos/aerox155_tripo3.glb` (1,38 MB, 102 mil triángulos, 65 nodos, `gltf-transform validate` sin errores),
conectado en `MODELOS_TRIPO.aerox` con `?v=4`. No se borraron `aerox155_tripo.glb` ni `aerox155_tripo2.glb`. Sin commit.
Entrada en `privado/tripo/aerox155_despiece/`. Scripts en `herramientas_3d/aerox155/`: `armar.py` (numpy) → `geometria.py` (Blender) → `final.py`.
Capturas: `final_lateral.png`, `final_tres_cuartos.png` y `final_luces.png` (noche, luces encendidas).

## Qué funcionó igual que en la Eco
- **Ejes y reflexión**: Tripo trae z adelante y -x del lado del escape, igual que la Eco: (x,y,z)visor = s·(z, y, x) con los índices invertidos.
- **Escala uniforme por entre ejes** (1,35 m): s = 1,977; el largo sale 1,977 m (ficha 1,99) sin estirar nada.
- **Una parte de Tripo = una isla = casi una pieza**: 75 partes; se agrupan por pieza real con nombre `material.pieza` (50 nodos) y la parte 0 (piso) se quita.
- **Mapa de partes**: render plano por parte con su número en 4 vistas (`vistas.py` del scratchpad, PIL puro) y comparación con la foto.
- `glbio.py` de la Eco sirve tal cual para leer y escribir el formato del visor; `geometria.py` también, con otras razones.
- Extras del visor iguales: `eje`/`pieza`/`torno` en ruedas, `rin`, `doble`, `rol: visor_fijo`, `padre: escapeFabrica` y `espejos.fabrica`, `manubrio`, `pantalla`, `placa`, `lampara`.
- **Direccionales y stop por planos** con `cortar()` (parte los triángulos del borde): mica adelante/atrás, vástago y carcasa aparte.
- Internos de Rayos X: copiados de `aerox155_tripo2.glb` (mismo origen y ejes ±0,675): Rayos X los muestra.

## Qué hubo que adaptar
- **Llanta y rin delantero venían en una sola parte**: se separan por radio (0,098 en unidades Tripo). Atrás venían separados.
- **Rin chico de la Eco no aparece**: el talón de la llanta (r 3 %) y la pestaña del rin ya coinciden (0,196 vs 0,200 m); `ajustar_rin()` solo
  escala si hace falta (factor 1,00). La llanta queda 1-1,5 cm más grande que la ficha (140/70 y 110/80-14): no se tocó, es la altura del eje.
- **Direccional delantera izquierda no vino**: se refleja la derecha (parte 71). Las traseras sí vinieron (55 y 58).
- **Faros dobles** (43 y 52): la mica curva de Tripo + reflector y bombillo como copias encogidas detrás. Con 6 mm atrás el bombillo quedaba
  dentro de la carrocería (la mica va pegada encima, sin hueco): quedó a 2 mm. Encienden (haz y halo), pero la mica se ve gris y el bombillo poco.
- **Carrocería arrugada**: el despiezado trae ruido fino que la pintura metalizada delata. Se agregó a `geometria.py` un Laplaciano con borde fijo
  y volumen conservado (pintura 18 pasadas, plástico 8) y suavizado a 50°. Mejoró mucho; quedan abolladuras grandes propias de Tripo.
- Decimate más fuerte que en la Eco (240 mil → 100 mil): pintura 0,42, llantas 0,2 (el visor las tornea).
- El stop es la cara de atrás (5 cm) de la pieza roja bajo el colín (7).

## Pendiente (no alcanzó la hora)
- Faros: mica más transparente o bombillo más grande/visible; aro de cromo si el borde se ve serrado de cerca.
- Personalizar: no se probó en vivo con rojo vivo ni el secundario (rin.* va al secundario por prefijo, pintura.* al principal).
- Revisión en 375 px no hecha (solo 1280). Placa: `incl` calculada por la pendiente del portaplaca, sin revisar de cerca.
- Las partes pequeñas sin identificar (13, 35, 39, 47, 53, 54, 61, 63, 66, 68, 69) van juntas en `oscuro.piezas`.
