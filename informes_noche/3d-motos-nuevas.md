# 3D de las líneas nuevas: 7 + Hunk 150 (15-11-2026, sin commit)

Cada línea tiene ahora rasgos propios en `moto3d/rasgos.js`, calcas de fábrica en `moto3d/calcas_fabrica.js` y,
donde hacía falta, geometría nueva en `moto3d/construir.js`. Fotos de referencia (solo locales):
`manual_despiece/<moto>/fotos/` con `fuentes.txt` y `_hoja.jpg` (Galgo Colombia; FZ 2.0 de Wikimedia Commons).
Capturas: `informes_noche/relevos/3d-motos-nuevas.jpg` (día, 3/4) y `3d-motos-nuevas-noche.jpg` (de noche, encendida).

| Moto | Base | Rasgos | Luces | Calcas de fábrica | Alta: tri / calls | Baja: tri |
|---|---|---|---|---|---|---|
| Honda XR 190L | carrocería enduro propia, modelo nuevo `xr` | aletas grandes que bajan hasta el frente del motor (estilo CRF), tanque bajo, colín largo y alto, guardabarros alto | máscara alta del color de la moto (`faro.forma: "mascara"`), faro rectangular con marco negro y visera ahumada; stop en la punta del colín; direccionales comunes | cuña blanca y negra en la aleta + "XR190L" blanco con borde negro | 39,6k / 40 | 23,2k |
| Suzuki DR 150 | carrocería enduro propia, modelo nuevo `dr` | tanque más ancho arriba en el color de la versión, mitad baja de la aleta negra, tapas laterales y colín negros (`enduro.tapas: "oscuro"`) | máscara negra angulosa con faro rectangular; stop en la punta | filete del color de la versión (lima por defecto) en la tapa lateral + "DR150" claro | 39,6k / 39 | 23,1k |
| Yamaha XTZ 150 | la XTZ ya existente (`/xtz/`), rin delantero de 19" por la ficha | sin cambios de geometría | las de la XTZ | "XTZ150" (la regla de la XTZ ya toma el cc) | 39,7k / 40 | 23,6k |
| TVS Raider 125 | familia naked (antes caía en clásica) | tanque anguloso con aletas, escalón al parrillero, colín afilado, mofle corto, rines de aleación | faro nuevo `raider`: máscara en flecha, proyector al centro y luces diurnas en "Y"; stop LED; direccionales LED | rayas en la aleta, "125" con borde, "RAIDER" en la tapa | 41,6k / 40 | 23,9k |
| Yamaha FZ 2.0 (FZ-S FI V2) | familia naked (antes caía en clásica) | tanque ancho y bajo con aletas, colín largo, mofle corto, aleación | faro `fz` (trapecio con las dos luces de posición arriba, como su sucesora la FZ25) | "FZ-S" plateado, barra azul en la aleta, "FI" chico | 43,8k / 40 | 25,3k |
| Hero Hunk 125R | familia naked (antes caía en clásica) | tanque musculoso, aletas grandes hasta la horquilla, guardabarros delantero pintado (`guardaPintado`), colín alto | faro nuevo `hunk`: LED rectangular ancho con dos cejas diurnas; stop LED | flecha roja sobre negro en la aleta, "HUNK", "125R" en la cola | 41,8k / 40 | 23,7k |
| Bajaj Boxer CT 125 | clásica, regla propia antes de la de la CT 100 | tanque anguloso, tapa lateral grande, colín largo con stop en la punta, parrilla, guardabarros pintado, rines de aleación | faro dentro de carenado en trapecio con visera; direccionales redondas | cuña lima y negra, "CT125" lima, "BOXER" en la tapa | 34,5k / 40 | 20,5k |
| Hero Hunk 150 (2012) | familia naked, regla propia antes de la de la Hunk 125R | tanque grande con aletas, escalón corto, colín medio, mofle subido, amortiguadores dobles (ficha), aleación 18" | faro nuevo `bikini`: carenado del color de la moto con visera, faro ancho anguloso y dos luces de posición; stop común | "Hunk" cursivo en el tanque, franja roja en la aleta, "150" en la tapa | 42,8k / 40 | 24,3k |

Presupuesto (8 motos): todas ≤43,8k tri en alta (tope 60k), ≤25,3k en baja (tope 35k), 38–40 calls (tope 60).
Primer cuadro del 3D (desde que arranca el módulo, Chrome sin ventana): 0,43–0,49 s con la caché caliente y
~2,1 s en frío, igual que las líneas de referencia (CR4, XR 150L) medidas igual. La medida oficial (desde la
navegación) es la del Auditor 3D.

Pruebas locales (arneses de `media/`): piezas flotantes ok, llantas sin choques (sin y con todos los accesorios),
luces visibles desde 3 ángulos y anclas de faro en la lente: 7/7. De noche y encendida: cono del faro adelante y
stop atrás (captura de noche).

## Cambios de código
- `rasgos.js`: reglas para Raider, Hunk, FZ 2.0 (familia naked), XR 190L y DR 150 (`enduro.modelo`, faro
  `mascara`) y Boxer CT 125 (antes de `/boxer/`). Rasgos nuevos: `guardaPintado`, `enduro: { modelo, tapas }`,
  `faro: { forma: "mascara", color, alto }`.
- `construir.js`: `carroceriaEnduro` pasa a una tabla de contornos por modelo (xtz y tt idénticas a antes, más xr y
  dr) y se usa también cuando la línea declara `enduro.modelo`; faro enduro `mascara` inclinado con la horquilla y
  por delante de las barras (no las atraviesa) y justo encima del guardabarros alto; faros naked `raider` y `hunk`;
  guardabarros delantero pintado con `guardaPintado`.
- `calcas_fabrica.js`: calcas de XR 190L, DR 150, Raider, Hunk, FZ 2.0 y Boxer CT 125 (la XTZ 150 ya la cubría).

## Segunda ronda (pedidos del usuario)
- **Guardafango delantero**: el de las enduro (XR 190L, DR 150, XTZ 150, y también XTZ 125, TT 125 y XR 150L, que
  comparten el código) estaba metido en el chasís, detrás de la horquilla, y no se veía. Ahora es una hoja alta unos
  7 cm sobre la llanta, con la punta levantada, que pasa entre las barras y se sujeta a ellas con dos platinas
  (negra en la DR 150 con `enduro.guarda: "oscuro"`, del color de la moto en las demás). Naked: Raider negro (como la
  foto), Hunk 125R, FZ 2.0 y CT 125 del color de la moto (`guardaPintado`). Pruebas de llantas y flotantes: ok.
- **Hunk 150**: fotos en `manual_despiece/hero-hunk-150/fotos/` (5 de Wikimedia Commons, Hero Honda Hunk 2007–2015).
- **Colores de fábrica por línea** (patrón nuevo, no había uno para las 25): `garaje/colores_fabrica.py`, una lista
  (hex, nombre) por línea buscada por nombre; el primero es el más común. Personalizar muestra primero los de fábrica
  ("… (de fábrica)") y luego la paleta general sin repetir. Al registrar la moto ya no hay color preseleccionado: si
  el usuario no elige, queda el de fábrica más común (líneas sin lista: el rojo de siempre). Pruebas:
  `garaje/tests_colores_fabrica.py` (6). Las otras 25 líneas se pueden ir sumando a la lista.

| Línea | Colores (el primero es el de por defecto) | Fuente |
|---|---|---|
| XR 190L | Rojo, Blanco, Beige | fotos Galgo Colombia (rojo); ficha Honda Ecuador 2025 (blanco, rojo, beige) y Perú (beige, rojo); Colombia no publica la lista |
| DR 150 | Gris, Amarillo, Negro | fotos Galgo Colombia DR150 2025 (las tres versiones) |
| XTZ 150 | Azul, Negro | fotos Galgo Colombia XTZ150 |
| Raider 125 | Gris California, Negro y plata, Azul Forza, Rojo racing, Amarillo racing | FI 2026: El Carro Colombiano/demotos (Forza Blue, California Grey, Black and Silver) y fotos Galgo; 2022: Valora Analitik (negro, azul, rojo racing, amarillo racing) |
| FZ 2.0 | Azul, Negro, Rojo y negro | fotos de Commons de la FZ-S V2 (azul, negro/rojo); aproximado |
| Hunk 125R | Negro, Rojo y gris, Azul y gris | fotos Galgo Colombia; ficha Hero Perú (negro, azul/gris, rojo/gris) |
| Boxer CT 125 | Blanco, Gris, Negro | fotos Galgo Colombia (blanco con lima, gris); negro aproximado |
| Hunk 150 | Negro, Rojo | fotos de Commons (negra y roja) |

Las otras 25 líneas (3.ª ronda). "Galgo" = filtro de colores de la ficha del modelo en galgo.com/co (lista
alfabética, no dice cuál es el más común); el predeterminado (primero) se eligió por las fotos oficiales y lo que más
circula. *Aprox.* = sin lista oficial encontrada.

| Línea | Colores (el primero es el de por defecto) | Fuente |
|---|---|---|
| NKD 125 | Negro, Gris, Blanco | Galgo CO928 (blanco, gris, negro); fotos AKT 2026 |
| CR4 125 | Negro con lima, Gris | fotos AKT 2026; *aprox.* (aktmotos.com no deja leer la lista) |
| TT 125 DS | Negro, Blanco, Rojo | *aprox.*, sin fotos ni ficha |
| Dynamic Pro 125 | Negro con lima, Gris, Blanco | fotos AKT 2026; *aprox.* |
| Boxer CT 100 | Negro y azul, Rojo, Azul, Verde | Galgo CO1032 (azul, negro, rojo, verde); fotos |
| Discover 125 | Negro, Rojo, Azul, Gris, Amarillo | Galgo CO1039 (amarillo, azul, gris, negro); fotos (roja, negra) |
| Pulsar NS 200 | Negro, Azul, Gris | Galgo CO3108 |
| Pulsar RS 200 | Negro, Gris, Rojo | Galgo CO1052 (gris, negro); foto roja |
| CB 125F | Rojo, Negro, Gris | Galgo CO721 (gris, rojo); fotos Honda (roja, negra, gris) |
| XR 150L | Rojo, Blanco, Negro | Galgo CO2796; fotos |
| Dio 110 | Gris, Azul, Rojo | Galgo CO771 (azul, rojo); fotos (gris) |
| Wave 110S | Rojo, Blanco, Negro, Gris | Galgo CO2952; fotos (roja, blanca) |
| GN 125 | Negro, Cobre, Azul | Galgo CO3013 (azul, negro); fotos Suzuki (cobre, negra) |
| Gixxer 150 | Azul, Negro, Rojo, Blanco | suzuki.com.co (negra, azul, roja, blanca); fotos (azul) |
| Best 125 | Rojo y negro, Negro | fotos suzuki.com.co (afiche "New Best FI") |
| NMAX 155 | Gris, Negro, Blanco, Rojo | Galgo CO2995 |
| XTZ 125 | Azul, Blanco, Negro | fotos Incolmotos; *aprox.* |
| FZ 25 | Azul y negro, Negro mate, Verde y negro | incolmotos-yamaha.com.co (nombres de las imágenes) y Galgo CO1027 |
| Crypton FI 115 | Gris, Blanco, Verde, Amarillo | Galgo CO3158 (amarillo, gris, verde); fotos Incolmotos (blanca, gris) |
| MT-03 | Gris, Azul, Negro | Galgo CO1366; Incolmotos 2026 (gris) |
| Apache RTR 160 | Gris, Azul, Negro | Galgo CO736 (azul, gris); negro *aprox.* |
| Duke 200 | Blanco y naranja, Naranja, Negro | fotos KTM 2024–2026; *aprox.* |
| RC 200 | Negro y naranja, Blanco y naranja | fotos KTM; *aprox.* |
| Eco Deluxe 100 | Negro, Gris | Galgo CO1119 (negro); fotos |
| Aerox 155 | Gris, Azul, Negro | Galgo CO1388 (gris); fotos Incolmotos 2021–2025 (azul, negra) |

También con lo de Galgo se completaron XR 190L (+ negro), DR 150 (+ azul, rojo), XTZ 150 (+ blanco) y Boxer CT 125
(+ azul, rojo). Prueba nueva: las 33 líneas del catálogo tienen su propia lista (sin choques entre reglas).
Registro: bajo el campo de color, «Si no eliges, usamos el color de fábrica más común.»

## Pendiente / para decidir
- Confirmar con concesionarios los colores marcados *aprox.* (TT 125, CR4, Dynamic, XTZ 125, Duke, RC).
- XR 190L: las tapas laterales blancas de la moto real van en el color de la pintura (un material más = 1 call).
- XTZ 150: misma geometría que la XTZ 125; la máscara de la 150 es algo más grande (no tocada).
- Scripts de medición: `informes_noche/relevos/scripts-3d-nuevas/` (Chrome sin ventana con una sesión local).
