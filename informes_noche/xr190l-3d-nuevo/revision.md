# Revisión exigente: XR 190L (`xr190l_tripo2.glb`)

Revisora independiente. La única vara son las fotos de `FOTOS_MODELADO_TRIPO/honda_xr_190l/` y los criterios del encargo. Medido en el visor real (`/garaje/38/vista-3d/`), con la cámara alineada a cada foto.

## Cómo se mide
- Capturas del lienzo del visor (`__visor`, cámara a 12 m, fov 14°, sin piso ni sombra), lado derecho (+z), igual que las dos fotos.
- **IoU**: la silueta del render (alfa > 230) se alinea a la de la foto (escala y traslado buscando el máximo); la foto se recorta del fondo blanco (umbral 28).
- **Color**: pasada de ID (cada pieza con su color plano) para tener la máscara de cada pieza en el render; color medio de la pieza en el cuartil medio de luminancia (sin brillos ni sombras) contra un parche de 5 a 10 px de la misma pieza en la foto (zona iluminada, sin reflejo, buscada por clase de color dentro de una caja). ΔE2000; cumple si ≤ 5.
- Scripts (fuera del repo): `medir.py`, `parches.py` y `color_piezas.py` en el scratchpad de la revisora. Si hace falta, se copian a `herramientas_3d/xr190l/revision/`.

## Ronda 1 (20-nov)

### Medidas
| # | Criterio | Meta | R1 | ¿Cumple? |
|---|---|---|---|---|
| 1a | Color: piezas con ΔE ≤ 5 (lateral) | ≥ 95 % | **25 %** (3/12) | no |
| 1b | Luces: faro, stop y 4 direccionales separados, nítidos, que se encienden | todas | faro dentado; stop 11 tri; direc. traseras 21 tri; **sin direccionales delanteras** | no |
| 1c | IoU de silueta lateral | ≥ 0,95 | **0,760** | no |
| 1c' | IoU tres cuartos | ≥ 0,95 | 0,59 (cámara aún sin afinar; se repite en R2) | no |
| 2 | Geometría: nada flotando, sin huecos ni caras negras | 0 | panel translúcido flotando sobre la máscara; escape del lado equivocado (ver B3) | no |
| 3 | Despiece: piezas correctas, bordes que siguen las líneas reales | sí | tapa lateral invade el costado del asiento y el chasis; manchas negras y rojas en aletas y colín; sin placa, estribos ni pedales separados | no |
| 4 | Personalizar y calcas | sí | colores por pieza sí; tapa lateral blanca sí; **calcas «XR 190L»: 0 vértices (no se ven)** | no |
| 5 | Rayos X | creíble | carrocería translúcida sí; internos se ven, falta revisar de cerca escala y sitio | parcial |
| 6 | Carga: consola, peso, 1280/375 | sin errores, ≤ 1,5 MB | 0 errores en vista-3d; 1.013 KB; 375 px según el informe (se verifica en R2) | sí (provisional) |

### ΔE por pieza (lateral)
| Pieza | Foto (RGB) | Render (RGB) | ΔE | Nota |
|---|---|---|---|---|
| aletas | 200,17,22 | 209,11,41 | 4,5 | ok |
| máscara | 207,33,33 | 212,25,50 | 4,8 | ok (justo) |
| chasis | 54,55,59 | 48,50,52 | 3,1 | ok |
| guardabarros del. | 205,11,18 | 231,44,65 | 10,6 | rojo rosado: le sobra azul y brillo |
| colín | 162,12,24 | 228,50,68 | 16,3 | ídem, además manchado de negro |
| tapa lateral | 196,197,202 | 240,240,238 | 10,1 | blanco demasiado claro y cálido; en la foto es blanco frío algo gris |
| tanque (tapa negra) | 85,79,85 | 92,90,87 | 7,6 | casi |
| asiento | 47,49,53 | 92,87,82 | 14,3 | asiento gris parduzco: debe ser negro mate |
| basculante | 213,212,217 | 108,111,112 | 31,4 | debe ser plateado claro (aluminio) |
| rines (aros) | 184,185,190 | 97,101,102 | 29,5 | deben ser plateados |
| motor | 49,50,54 | 97,90,84 | 15,5 | en la foto el motor es negro (tapas negras), no titanio |
| escape | 57,58,63 | (11 px visibles) | — | del lado derecho casi no hay pieza «escape» (ver B3) |

### Hallazgos y arreglos
**Bloqueantes**
- **B1. Ruedas grandes (IoU).** En la silueta, las dos llantas sobresalen en todo el contorno (el mayor aporte al 0,76). La ficha de la moto dice rin 19" adelante y 17" atrás (90/90-19 y 110/90-17); el informe dice que puso 21" y 18". Arreglo: radios de rin y llanta según 19/17 y el balón real de cada llanta, medidos contra la foto lateral. Hecho: el anillo de diferencia de silueta alrededor de las ruedas ≤ 3 px (en la foto de 1000 px) y el IoU lateral ≥ 0,90 solo con este cambio.
- **B2. Pintado por zonas (color y despiece).** La tapa lateral blanca cubre todo el costado del asiento y baja hasta el chasis; en la foto el blanco es una pieza en forma de bumerán bajo la parte delantera del asiento, y encima va el costado negro del asiento. Aletas y colín tienen manchas negras y blancas en camuflaje (bordes dentados). Arreglo: delimitar tapa lateral, asiento, aletas y colín con los contornos de la foto lateral (polígonos en coordenadas de la moto, proyectados de lado), no con reglas de caja; después el voto por vecinos. Hecho: en la pasada de ID, cada pieza cae dentro de su contorno de la foto en ≥ 95 % de sus píxeles, y en aletas y colín no quedan islas de otra pieza de más de 1 cm.
- **B3. Escape espejado.** La pieza `escape` está del lado izquierdo (z −0,24 a −0,07) y del lado derecho no se ve (11 px). En la XR 190L el silenciador con su cubierta negra va a la **derecha**, como en las dos fotos. Si Tripo generó la moto espejada, espejar todo el modelo en z (y voltear las caras); si no, separar como `escape` la cubierta negra derecha que hoy está en `cubierta_trasera`. Hecho: desde la derecha, el escape ocupa la zona negra bajo el colín de la foto.
- **B4. Luces.** Faro: mancha blanca de bordes dentados pegada a la máscara, sin mica ni aro. Stop de 11 triángulos y direccionales traseras de 21: no se leen como luces y casi no brillan. **No hay direccionales delanteras** (quedaron en la máscara o en el manubrio). Arreglo: faro, stop y 4 direccionales como piezas propias de forma limpia (mica y borde, que se pueden modelar nuevos en el sitio de Tripo si la malla está horneada); direccionales delanteras fuera de la máscara, en su soporte, como en la foto. Hecho: 6 piezas separadas con su nombre; encendidas en el visor (`__visor.vivo(true)`), cada una se ve como un borde nítido.
- **B5. Calcas.** `__visor.fabrica()` da `vertices: 0`: las calcas «XR 190L» no se dibujan. En la foto las aletas llevan el gráfico grande «XR 190L» blanco y negro con rayas, y el costado trasero dice «HONDA». Hecho: el gráfico se ve en la vista lateral, en su sitio y a su tamaño.

**Importantes**
- **I1. Colores de fábrica.** Asiento negro mate (≈ 47,49,53 bajo la luz del visor); motor negro (no titanio); basculante y aros plateados claros (≈ 205–215); rojo de pintura sin tono rosado (≈ 200–205, 10–20, 15–25: bajar brillo o reflejo, o el tono base); tapa lateral blanco frío (≈ 196–200, algo azulado). Hecho: ΔE ≤ 5 en las 12 piezas.
- **I2. Panel translúcido flotando** sobre la máscara (material a9bec7, opacidad 0,45; caja x 0,25–0,44, y 1,07–1,29). La XR no lleva visera: quitarlo (extras `sin`) o, si es el tablero, bajarlo a su sitio. Desde el frente también se ve una placa gris clara suelta sobre el manubrio izquierdo.
- **I3. Disco trasero.** El modelo trae `disco_tras`, pero la XR 190L lleva **tambor** atrás (ficha: freno trasero tambor). Quitar el disco o convertirlo en tapa de tambor.
- **I4. Horquilla.** En la foto, la barra baja es plateada y la alta, negra; en el modelo, `horquilla_baja` va de la tijera al eje y se ve oscura. Partir donde está el retén.
- **I5. Placa, estribos y pedales.** Separarlos (hoy los estribos y pedales están en `chasis` y la placa la pone el visor, fuera del guardabarros).

**Detalles**
- D1. Rayos X: se ven los internos; en R2 reviso de cerca la escala del filtro (debe ir bajo el asiento, detrás del carburador) y que nada atraviese la tapa lateral.
- D2. Pata lateral: la pone el visor, no cuenta en el IoU.

### Pendiente para R2
Repetir IoU en tres cuartos con la cámara afinada, 375 px, `pintura2` y Rayos X de cerca.

## Ronda 2 (20-nov, `?v=3`)

Medido igual que en R1. Además: en la foto lateral se quita la sombra del piso (gris claro en el 6 % inferior), que en R1 se contaba como moto. Con esa corrección, R1 daría 0,793. También se informa un IoU con los huecos rellenos (sin rayos, solo el contorno), como dato de apoyo.

### Medidas
| # | Criterio | Meta | R1 | R2 | ¿Cumple? |
|---|---|---|---|---|---|
| 1a | Color: piezas con ΔE ≤ 5 | ≥ 95 % | 25 % | **8 %** (1/12; ver tabla) | no |
| 1b | Luces separadas, nítidas y que se encienden | 6 | 1 dentada + 2 mínimas | **6 separadas** con aro; faro y direccionales nítidos y encendidos; **el stop encendido sale salmón, no rojo** | casi |
| 1c | IoU lateral (sin sombra) | ≥ 0,95 | 0,793 | **0,817** (relleno 0,895) | no |
| 1c' | IoU tres cuartos | ≥ 0,95 | 0,59 | 0,60 (la foto se tomó con lente corto: falta igualar fov y distancia; no es comparable aún) | no |
| 2 | Geometría | 0 defectos | panel flotante, escape espejado | ya no flota el panel; escape a la derecha | sí, salvo B2 |
| 3 | Despiece | sí | mal | escape, corona, portaplaca, estribos, horquilla partida y luces sí; **los bordes de tapa lateral, aletas y colín siguen dentados** | no |
| 4 | Personalizar y calcas | sí | calcas 0 vértices | la calca se dibuja (1.533 vértices), pero **chica: «XR190» sin la L ni las rayas**; `pintura2` no verificado | no |
| 5 | Rayos X | creíble | parcial | **no verificado**: `/garaje/38/` no carga el visor en el panel (falla conocida del service worker, ajena al modelo) | pendiente |
| 6 | Carga | sin errores, ≤ 1,5 MB | sí | 1.054 KB en disco; vista-3d sin errores | sí |

### ΔE por pieza (R2)
| Pieza | Foto | Render | ΔE |
|---|---|---|---|
| aletas | 200,17,22 | 169,0,20 | 6,9 |
| máscara | 207,33,33 | 181,0,23 | 6,7 |
| guardabarros del. | 205,11,18 | 198,2,31 | **3,9 ok** |
| colín | 162,12,24 | 103,13,22 | 12,2 (sale negro) |
| tapa lateral | 196,197,202 | 228,224,217 | 8,6 |
| tanque | 85,79,85 | 56,50,41 | 13,5 |
| asiento | 47,49,53 | 47,41,34 | 7,9 |
| chasis | 54,55,59 | 17,18,17 | 12,1 |
| basculante | 213,212,217 | 153,151,142 | 18,5 |
| rines | 184,185,190 | 160,157,147 | 11,2 |
| motor | 49,50,54 | 18,18,16 | 10,6 |
| escape | 57,58,63 | 18,19,17 | 13,2 |

**Lectura:** el error ya no es de zona sino de tono, y es sistemático.
1. **Los negros salen casi puros** (17 a 18) y en la foto son gris carbón (≈ 50 a 57): subirles el color base o la rugosidad hasta que rindan ≈ 50,52,56.
2. **Todo neutro sale cálido** (azul 5 a 10 puntos por debajo del rojo) por la luz cálida del visor: dar a blancos, plateados y negros un tono base levemente azulado.
3. **Rojos 30 puntos oscuros:** subir la luminosidad del rojo base (meta ≈ 200,15,22 en render).
4. **Plateados oscuros:** basculante y aros con base más clara o menos metálica (meta ≈ 205 a 213).

### Arreglos R2 (para `xr190l-3d-relevo`)
**Bloqueantes**
- **R2-B1. Tonos** (arriba). Hecho: ΔE ≤ 5 en ≥ 12 de 12 piezas, medido con `color_piezas.py`.
- **R2-B2. Bordes de pintura** (ya los tenía pendientes): colín rojo arriba y negro abajo como en la foto; quitar las manchas negras en zigzag de aletas y tanque (se ven también desde atrás); tapa lateral con borde liso en forma de bumerán, sin la isla negra del centro. Hecho: ninguna isla de otra pieza > 1 cm y bordes sin escalones visibles a 1280 px.
- **R2-B3. Rueda delantera:** sigue grande y adelantada; la diferencia de silueta deja un anillo de 6 a 10 px por fuera y por debajo. De tres cuartos la llanta se ve de globo, muy ancha: una 90/90-19 mide ≈ 9 cm de ancho. Hecho: anillo ≤ 3 px y ancho de llanta ≈ 90 mm adelante y ≈ 110 mm atrás.

**Importantes**
- **R2-I1. Calca:** el gráfico de la foto es grande y en diagonal sobre la aleta («XR 190L» blanco con borde negro y rayas). Hoy dice «XR190», es chico y va recto. Hecho: se lee «XR 190L» completo, a ≈ 60 % del largo de la aleta.
- **R2-I2. Stop:** mica roja; encendido debe verse rojo, no salmón.
- **R2-I3. Espejos:** en la foto son más altos y quedan más atrás (diferencia de silueta en la cabeza).

**Pendiente de la revisora:** Rayos X, `pintura2` y 375 px, cuando la página de la moto cargue el visor.

## Medición intermedia (`?v=4`, hecha antes de que leyera la R2; la reemplaza la R3 de abajo)

La v4 se hizo sobre la ronda 1, antes de leer la ronda 2: casi no cambia frente a la v3. Mejoró el blanco de la tapa lateral (ΔE de 8,6 a 5,6). El colín sigue negro (ΔE 23,6). Con esta se llega al tope de 3 rondas y 1 h 30 min.

### Tabla con la v4 (reemplazada)
| # | Criterio | Meta | R1 (v2) | R2 (v3) | R3 (v4) | ¿Cumple? |
|---|---|---|---|---|---|---|
| 1a | Color: piezas con ΔE ≤ 5 | ≥ 95 % | 25 % | 8 % | **8 %** (1/12; tapa lateral 5,6, casi) | no |
| 1b | Luces: 6 separadas, nítidas, encendidas | 6 | 1 dentada | 6 | **6**; stop encendido salmón | casi |
| 1c | IoU lateral (sin sombra) | ≥ 0,95 | 0,793 | 0,817 | **0,817** (relleno 0,896) | no |
| 1c' | IoU tres cuartos | ≥ 0,95 | 0,59 | 0,60 | sin medir (cámara de la foto sin igualar) | no |
| 2 | Geometría | 0 defectos | panel flotante, escape espejado | ok | **ok** | sí |
| 3 | Despiece | sí | mal | piezas sí, bordes dentados | **piezas sí, bordes dentados** (tapa lateral, aletas, colín) | no |
| 4 | Personalizar y calcas | sí | calcas 0 vértices | calca chica «XR190» | **igual**; `pintura2` sin verificar | no |
| 5 | Rayos X | creíble | parcial | sin verificar | **sin verificar** (la página de la moto no carga el visor en el panel) | pendiente |
| 6 | Carga | sin errores, ≤ 1,5 MB | sí | sí | **sí** (1.052 KB, 0 errores en vista-3d) | sí |

### Pendiente (para la sesión de modelado)
1. Tonos (R2-B1): negros a ≈ 50,52,56; neutros con base algo azulada; rojo más claro (≈ 200,15,22 en render, sin tono rosado); basculante y aros ≈ 205 a 213.
2. Colín rojo arriba; aletas y tanque sin zigzag negro; tapa lateral con borde liso en bumerán (R2-B2).
3. Rueda delantera más chica, en su sitio, y llantas de 90 y 110 mm de ancho (R2-B3).
4. Calca «XR 190L» grande, en diagonal y con rayas (R2-I1); stop rojo al encenderse (R2-I2); espejos más altos y más atrás (R2-I3).
5. Revisora: Rayos X, `pintura2`, 375 px y tres cuartos con la cámara igualada, cuando `/garaje/38/` cargue el visor (falla del service worker).

### Cómo volver a medir
Scripts y pasos en la carpeta de notas compartidas `revisora-xr190l/` (LEEME.md): proxy local sin CSP, `__cap` y `__capId` en la página, y luego `medir.py`, `iou_lleno.py` y `color_piezas.py`.

## Ronda 3 (20-nov, `?v=5`): cierre definitivo

La v5 sí recoge la ronda 2. Medido igual que antes. Rayos X se verificó por fin: el proxy de medición carga `vista-3d` en modo rayos. Quitar el service worker no arregló `/garaje/38/`.

### ΔE por pieza (v5)
| Pieza | Foto | Render | ΔE |
|---|---|---|---|
| aletas | 200,17,22 | 170,0,20 | 6,8 |
| máscara | 207,33,33 | 182,0,24 | 6,6 |
| guardabarros del. | 205,11,18 | 200,4,33 | **4,0 ok** |
| colín | 162,12,24 | 56,22,24 | 23,1 (la parte visible de lado sigue casi negra) |
| tapa lateral | 196,197,202 | 214,212,207 | 5,6 (casi) |
| tanque | 85,79,85 | 84,79,88 | **1,7 ok** |
| asiento | 47,49,53 | 49,45,41 | 5,7 (casi; algo cálido) |
| chasis | 54,55,59 | 18,19,18 | 11,9 (sin cambio: Personalizar lo recolorea) |
| basculante | 213,212,217 | 215,213,208 | 5,3 (casi; algo cálido) |
| rines | 184,185,190 | 158,156,147 | 11,3 (sin cambio) |
| motor | 49,50,54 | 57,60,64 | **3,3 ok** |
| escape | 57,58,63 | 63,66,72 | **2,9 ok** |

### Tabla final
| # | Criterio | Meta | R1 (v2) | R2 (v3) | R3 (v5) | ¿Cumple? |
|---|---|---|---|---|---|---|
| 1a | Color: piezas con ΔE ≤ 5 | ≥ 95 % | 25 % | 8 % | **33 %** (4/12; otras 3 entre 5,3 y 5,7) | no |
| 1b | Luces: 6 separadas, nítidas, encendidas | 6 | 1 dentada | 6, stop salmón | **6, stop rojo** | sí |
| 1c | IoU lateral (sin sombra de piso) | ≥ 0,95 | 0,793 | 0,817 | **0,836** (relleno 0,924) | no |
| 1c' | IoU tres cuartos | ≥ 0,95 | 0,59 | 0,60 | sin igualar la cámara de la foto | no medible aún |
| 2 | Geometría | sin defectos | panel flotante, escape espejado | ok | **ok** | sí |
| 3 | Despiece | piezas y bordes | mal | piezas ok, bordes dentados | **piezas ok; bordes dentados** en tapa lateral y colín | no |
| 4 | Personalizar y calcas | sí | calcas 0 vértices | calca chica | **calca chica «XR190»**; `pintura2` sin verificar | no |
| 5 | Rayos X | creíble | parcial | sin verificar | **creíble**: carrocería en malla translúcida; motor con aletas, en su sitio y en escala | sí |
| 6 | Carga | sin errores, ≤ 1,5 MB | sí | sí | **sí** (1.037 KB, 0 errores en vista-3d) | sí |

### Pendiente
1. **Colín**: la zona roja bajo el asiento de la foto (costado trasero) sale negra en el render. Es el error de color más grande (ΔE 23).
2. **Chasis y aros**: ΔE 12 y 11. Si Personalizar los recolorea, darles en `glb.js` un tono de fábrica propio de la XR (chasis ≈ 54,55,59 en render; aros ≈ 184,185,190).
3. **Rojo**: le falta luz (170 contra 200). Sale de `M.pintura` con el color de la moto 38; subir la luminosidad del rojo de fábrica de la XR.
4. **Afinar tapa lateral, asiento y basculante**: quitarles el tono cálido. Con 1 a 2 puntos más de azul, los tres pasan de ΔE 5,3–5,7 a ≤ 5.
5. **Tono de los grises oscuros**: escape, motor y cubierta pasan el ΔE, pero a la vista quedan gris pizarra azulado; vigilar que no se pasen.
6. **Bordes**: tapa lateral en bumerán liso, sin la isla oscura del centro.
7. **Calca** «XR 190L» grande, en diagonal y con rayas; **espejos** más altos y más atrás.
8. **IoU**: lo que más falta está en la rueda delantera, los espejos y la diferencia de rayos (con los huecos rellenos da 0,924).
9. **Sin verificar**: `pintura2`, 375 px e IoU de tres cuartos con la cámara de la foto. `/garaje/38/` no carga el visor en el panel ni aun sin service worker.

## Ronda 4 (20-nov, revisora nueva): encargo sobre la v5
Metas vigentes (todas): color ≥ 95 % (con 12 piezas son **12/12**), IoU lateral ≥ **0,85** (bajada por el usuario; se conserva la geometría de Tripo), luces, geometría, Rayos X y carga como ya están, despiece con bordes limpios, tapa lateral blanca en la página y calca «XR 190L» a escala real.

### Arreglos por impacto
1. **R4-1 Colín (ΔE 23,1).** Qué: de lado, la banda bajo el asiento hasta la cola sale casi negra (render 56,22,24; foto 162,12,24). Dónde: costado trasero, bajo el asiento, y cara superior de la cola; la regla `parrilla` (y > 0,93, no rojo) se lo come. Arreglo: forzar `colin` en esa banda (polígono lateral de la foto) antes de la regla de parrilla, y luego borde liso. Hecho: ΔE ≤ 5 y en la pasada de ID el colín ocupa la banda roja de la foto (≥ 95 % de sus píxeles dentro de ella), sin islas negras > 1 cm.
2. **R4-2 Rines (ΔE 11,3) y chasis (ΔE 11,9).** Qué: aros 158,156,147 (meta 184,185,190); chasis 18,19,18 (meta 54,55,59). Personalizar los recolorea. Arreglo: tono de fábrica propio de la XR que Personalizar use como valor inicial (y respete mientras el usuario no lo cambie), con base algo azulada. Hecho: ΔE ≤ 5 en ambos con la moto recién cargada.
3. **R4-3 Rojo de pintura (aletas 6,8, máscara 6,6).** Qué: 170,0,20 contra 200,17,22: le falta luz. Sale del color de la moto 38 (`M.pintura`). Arreglo: rojo de fábrica de la XR más claro (que rinda ≈ 200,15,22), sin tono rosado; vigilar que el guardabarros (hoy 4,0) no se pase. Hecho: aletas, máscara y guardabarros ≤ 5.
4. **R4-4 Neutros cálidos (tapa lateral 5,6, asiento 5,7, basculante 5,3).** Arreglo: +2 puntos de azul (o −1 de rojo) en su tono. Hecho: los tres ≤ 5.
5. **R4-5 IoU 0,836 → ≥ 0,85.** Lo que falta está en la rueda delantera (anillo por fuera y por debajo), los espejos (en la foto más altos y más atrás) y los rayos. Arreglo sin rehacer la geometría de Tripo: llevar la rueda delantera a su radio y sitio de la foto (escala y traslado del conjunto rueda + horquilla baja), espejos con tallo más alto e inclinado hacia atrás. Hecho: IoU lateral ≥ 0,85 medido por la revisora.
6. **R4-6 Bordes del despiece.** Tapa lateral en bumerán con borde liso y sin la isla oscura del centro; borde colín/cubierta sin escalones. Hecho: sin escalones visibles a 1280 px de cerca y ninguna isla > 1 cm.
7. **R4-7 Calca y Personalizar.** «XR 190L» completa (hoy «XR190»), blanca con borde negro y rayas, en diagonal sobre la aleta a ≈ 60 % de su largo (escala real). La tapa lateral debe verse blanca en la página de la moto (Personalizar). Hecho: se lee completa en la vista lateral; `fabrica()` con vértices > 0.

### Calibración de la revisora nueva (v5)
Scripts copiados y completados en `herramientas_3d/xr190l/revision/` (`cap.js` para capturar desde la consola, `medir_todo.sh` para medir de una vez; ver `LEEME.md`). La pasada de ID ahora usa las mallas originales de las pinturas (el visor las dibuja con mallas unidas). Sobre la v5 da **IoU sin sombra 0,838** (relleno 0,925) y **color 5/12**: el asiento ya pasa (4,8) y el colín da 6,9 medido sobre sus 197 px visibles (render 197,1,32 contra 162,12,24 en la foto: le sobran saturación y azul). Así que la banda negra del costado trasero no es `colin` sino otra pieza oscura, y se cuenta en el IoU, no en el color. Desde la R4, esta medición es la base.

### Medición intermedia v6 (`?v=6`)
IoU sin sombra 0,838 (relleno 0,925), sin cambio. Color **8/12**: ya pasan rines 1,6, tapa lateral 2,9, asiento 2,2 y basculante 3,4. No pasan el chasis, que se pasó de claro y azul (7,5; render 71,76,85), el colín (7,4; 199,7,34 contra 162,12,24: más oscuro y sin azul), las aletas (6,6) ni la máscara (6,4). Se le mandó a la sesión de modelado.

### Medición v7 (`?v=7`)
| Pieza | ΔE |
|---|---|
| aletas | 2,0 |
| máscara | 2,0 |
| guardabarros del. | 3,6 |
| colín | 0,5 |
| tapa lateral | 2,9 |
| tanque | 1,8 |
| asiento | 2,2 |
| chasis | 1,9 |
| basculante | 3,4 |
| rines | 1,6 |
| motor | 3,4 |
| escape | 1,9 |

**Color 12/12 (100 %): cumple.** IoU sin sombra **0,838** (relleno 0,925): no cumple. Cuánto subiría el IoU si cada zona quedara perfecta (`zonas_iou.py`): rueda delantera 0,892, resto 0,887, rueda trasera 0,872, espejos 0,855. Se le mandó a la sesión de modelado: rueda delantera y espejos primero.

### Tabla por ronda (revisora nueva)
| # | Criterio | Meta | v5 (base) | v6 | v7 | ¿Cumple? |
|---|---|---|---|---|---|---|
| 1a | Color ΔE ≤ 5 | ≥ 95 % | 42 % (5/12) | 67 % (8/12) | **100 %** | sí |
| 1c | IoU lateral sin sombra | ≥ 0,85 | 0,838 | 0,838 | 0,838 | no |
| 1b | Luces | 6 | sí | sí | sí (sin cambio de luces) | sí |
| 3 | Bordes del despiece (tapa lateral, colín) | limpios | dentados | sin revisar | sin revisar | pendiente |
| 4 | Calca «XR 190L» a escala y tapa blanca en la página | sí | «XR190» chica | igual | igual (`fabrica()` 1.533 vértices) | no |
| 2, 5, 6 | Geometría, Rayos X, carga | — | sí | — | sin volver a medir | revisar en la final |

### RELEVO de la revisora (20-nov): tope de contexto alcanzado
- **Cómo medir:** ver `herramientas_3d/xr190l/revision/LEEME.md`. Proxy: `python -I proxy.py` (puerto 8767; si no responde, reiniciarlo); abrir `http://localhost:8767/garaje/38/vista-3d/` en el Browser pane; capturar con `cap.js` (`__cap('vN_lat',0,2)` y `__cap('vN_lat_id',0,2,{ids:true})`); medir con `sh medir_todo.sh vN` y `python -I zonas_iou.py <foto> caps/vN`. Para esperar una versión nueva, usar un `until` en segundo plano sobre `xr190l_tripo2.glb?v=N` en `glb.js` (la sesión de modelado no avisa al terminar).
- **Falta:** (1) IoU ≥ 0,85: rueda delantera y espejos (ya encargado). (2) Revisar de cerca los bordes de tapa lateral y colín. (3) Calca «XR 190L» completa, con rayas y a escala, y tapa lateral blanca en la página. (4) En la versión final, volver a verificar luces, Rayos X (`?rayos=1`), carga y tres cuartos (`__cap(..., az≈35)`, solo como dato). (5) Capturas finales sin fotos (`__cap` lateral y tres cuartos, ≤ 900 px) en `informes_noche/xr190l-3d-nuevo/final_lateral.png` y `final_tres_cuartos.png`.
- **Rondas usadas:** R4 (con dos mediciones intermedias). Quedan como máximo 4.

### Aviso de la sesión de modelado: v10 (sin medir por esta revisora)
Según la sesión de modelado, con estos mismos scripts la v10 da IoU sin sombra **0,8505** (relleno 0,935) y color 12/12. Lo que cambió: (1) `ALTO = 1,03` en `construir.py`, un estiramiento vertical del 3 %; (2) espejos 4,5 cm más altos y 5 cm más adelante. La rueda no se movió. La calca «XR 190L» quedó completa, pero de 15 cm (la zona `tanque` la recorta). Bordes sin tocar. La sesión de modelado llegó a su tope: hace falta una de relevo.
**Para la revisora de relevo:**
- Medir la v10 por su cuenta: el 0,8505 queda justo en el borde de la meta.
- Juzgar si el estiramiento vertical del 3 % respeta la regla de «conservar la geometría de Tripo». Puede estar compensando el lente de la foto: comprobar con la altura del asiento y la distancia entre ejes de la ficha.
- Faltan los bordes, la calca a escala real y las capturas finales.

### Verificación de la v10 (revisora)
- **Medido por la revisora:** IoU lateral sin sombra **0,854** (relleno 0,937) y color **12/12**; ΔE máximo 3,7, en el guardabarros. Coincide con lo que reportó la sesión de modelado. Si cada zona quedara perfecta, el IoU llegaría a: espejos 0,866, rueda trasera 0,888, rueda delantera 0,898, resto 0,903.
- **Estiramiento vertical `ALTO = 1,03`: no es una corrección de escala legítima.** Medidas en el visor contra la ficha oficial (Honda Ecuador y Sudáfrica: 2.075 × 812 × 1.124 mm, asiento 835 mm, entre ejes 1.351 mm):

| Medida | v10 | Sin el 1,03 (÷1,03) | Ficha |
|---|---|---|---|
| Largo | 2.069 | 2.069 | 2.075 |
| Entre ejes | 1.353 | 1.353 | 1.351 |
| Manubrio (alto total) | 1.159 | 1.125 | 1.124 |
| Asiento, en el medio | 872 | 847 | 835 |

  Sin estirar, el Tripo ya coincide con la ficha (alto 1.125 contra 1.124). Con el estiramiento queda 3 % más alto que la moto real: compensa la perspectiva o el lente de la foto, no un error de escala. Las ruedas no se estiraron (siguen redondas, de 638 mm). **Veredicto:** sin el estiramiento, el IoU queda en ≈ 0,84 (la sesión de modelado midió 0,846 con 1,015) y **no cumple** la meta con la regla de conservar la geometría. Decide el usuario: aceptar el 1,03 como ajuste a la foto o quitarlo y quedarse en ≈ 0,84.
- **Capturas finales de la v10, sin fotos:** `final_lateral.png` y `final_tres_cuartos.png`. De tres cuartos todavía se ven los bordes dentados entre el rojo, el blanco y el gris en la tapa lateral y bajo el tanque, y la calca chica («XR 190L» de 15 cm).
- **Siguen pendientes:** los bordes de la tapa lateral y el colín, la calca a escala real, la tapa blanca en la página, y volver a verificar luces, Rayos X y carga en la versión final.
