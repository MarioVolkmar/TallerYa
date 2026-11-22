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

# Ronda 2 (21-nov): correcciones del usuario, `aerox155_tripo3.glb?v=6`

## Ruedas de Tripo que giran tal cual (sin llanta torneada)
Antes el visor cambiaba la llanta de cada GLB por una suya (`tornearLlanta` en `glb.js`). Ahora un GLB puede marcar sus ruedas
y el visor las hace girar con la geometría de Tripo, sin reemplazarla. Los GLB sin la marca siguen como antes (Eco Deluxe,
XR 190L y las demás no cambian).

**Cómo marcar una rueda (para la futura skill):**
- Cada pieza que gira con la rueda (llanta, rin, disco o corona/tambor) lleva `extras.rueda: "del" | "tras"` y `extras.eje: [x, y]`.
  El freno (mordaza), la horquilla y el basculante NO llevan la marca: quedan fijos.
- La **traslación del nodo** es el centro del eje `[eje_x, eje_y, z_medio]`: es el pivote. `glbio.escribir` acepta ahora
  `centro` por nodo (opcional; sin él usa el centro de la caja como siempre) y `final.py` lo pone en los nodos con `rueda`.
- El centro se calcula con **ajuste de círculo** (mínimos cuadrados) a la banda de rodadura en el plano xy (`centro_rueda` en
  `armar.py`), no con la caja de Tripo. Comprobado en el visor: al girar 0, 1,1 y 2,3 rad el centro de la llanta queda fijo a ±1 mm.
- En el visor (`glb.js`): con `rueda` no se tornea ni se labra la llanta; la pieza cuelga del `pivoteRueda` de `llanta_<rueda>`
  y el pivote se lleva a la traslación del nodo. La animación de giro de `moto3d.js` no cambió.
- Si Tripo trae llanta y rin juntos, se separan con `cortar(m, None, None, s=radio - r0)` (corte por cilindro partiendo los
  triángulos del borde, sin dientes). La llanta ya no se diezma al 0,2 sino al 0,6, porque ahora se ve.

## Las otras correcciones
- **Plásticos negros**: bajos y pisaderas (parte 12 bajo y = 0,45 m, cortada por plano), franja de pisadera (32), tapa del túnel
  (42) y escudo interior (37, 40) pasan a `plastico`. Pintura: frente, escudo exterior, túnel, tapas laterales, colín y guardabarros.
- **Tonos parejos**: todas las piezas `pintura.*` comparten un solo material (sin `acabado` propio); los plásticos también.
- **Translúcidos**: solo `vidrio.*` (micas) y el visor (`vidrio_oscuro.visor`, antes `oscuro.visera` opaco). Comprobado en el
  visor: ninguna otra malla queda `transparent`.
- **Placa**: la parte 62 (que iba como «reflector» naranja) es el soporte de la placa que modeló Tripo; ahora es parte del
  portaplaca y la placa (17 × 12 cm) va sobre su cara trasera, con el plano medido (incl −0,60 rad).
- **Tablero**: sobre el carenado frontal, debajo del visor (entre su borde de atrás y 7 cm hacia adelante), punto y normal medidos.
- **Bordes**: el corte llanta/rin delantero ya no es por triángulo.

## Verificado
- `npx gltf-transform validate`: sin errores ni avisos. 1,49 MB, 111 mil triángulos, 66 nodos.
- Personalizar con rojo: solo la carrocería pintada; ruedas, plásticos y negro quedan iguales. Rayos X muestra los internos.
- 375 px: sin desborde. Eco Deluxe (/garaje/60/) y XR 190L (/garaje/38/) se ven igual (siguen con la llanta torneada).
- Capturas: `arreglo_lateral.png`, `arreglo_tres_cuartos.png`, `arreglo_luces.png`. `capturar.py` acepta ahora `PRE="js"` (pasos antes de capturar, p. ej. Rayos X).

## Pendiente
- Faros poco vivos; borde serrado de las micas de Tripo en los faros (no alcanzó la hora).
