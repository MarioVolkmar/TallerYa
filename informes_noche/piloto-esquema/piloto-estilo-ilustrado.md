# Piloto: estilo ilustrado en una lámina del esquema (freno delantero AKT NKD 125)

17-nov-2026 · Sesión de piloto, sin commit. La lámina original, la skill `hacer-lamina` y los archivos comunes del motor (`esquema.js`, `esquema.css`, `piezas-comunes.js`) **no se tocaron**.

## Qué se hizo
Copia de la lámina `nkd-freno` (aprobada con 4,88) con los mismos datos, fichas, pasos y comportamiento. Solo cambian el arte y la presentación:

| Archivo nuevo | Qué es |
|---|---|
| `motor/prueba-nkd-freno-estilo.html` | **Entrega**: archivo único (abre sin servidor) |
| `motor/nkd-freno-estilo.html` | Página normal (enlaza el CSS del motor + el del estilo) |
| `motor/datos/nkd-freno-estilo-arte.js` | Arte: mismas formas y medidas, `DEFS` nuevos, rótulos y «Cómo funciona» nuevo |
| `motor/datos/nkd-freno-estilo.json` | Igual al original salvo `arte`, un contexto más (rótulos) y el color de la manguera |
| `motor/estilo-ilustrado.css` | 22 líneas: lienzo claro, números con tinta, rótulos, leyenda |
| `motor/piloto-estilo-antes-despues.jpg` | Captura antes/después a 900 px |
| `motor/nkd-freno-estilo-1280.jpg`, `motor/revision/nkd-freno-estilo.md` | Salidas de `autocontrol` |

Lenguaje visual probado (dibujo propio, sin calcar ni incrustar las referencias):
- **Fondo claro con grilla sutil** (patrón SVG de 40 px) en el lienzo y en «Cómo funciona». El resto de la página sigue oscuro.
- **Metal con volumen**: degradados más abiertos (blanco → gris → brillo → sombra), franjas especulares (`gBrilloV`) en cáliper y bomba, sombras suaves azuladas (opacidad 0,26 en vez de 0,55).
- **Color por sistema**, con leyenda en el dibujo: mando = naranja (manigueta, palanca y cable del CBS), hidráulico = azul (bomba, manguera, cáliper), fricción = cobre (pastillas), eléctrico = violeta (interruptor), otra lámina = acero neutro (disco, barra, manubrio).
- **Rótulos con línea guía** y texto corto («MANIGUETA · inicia la presión», «CÁLIPER · aprieta las pastillas», 7 rótulos). Solo con el dibujo armado: se ocultan al desarmar, en transparente, al ampliar y al entrar a un grupo.
- **Flechas del flujo en «Cómo funciona»**: rojas = fuerza (mano, pistón, dedo del cáliper), azules = presión del líquido (bomba, manguera). Aparecen paso a paso (comprobado: 11000 → 11100 → 11110 → 11111). Hay una leyenda en PC y otra en el celular.

## Mediciones (antes → después)

| | Antes | Después | Diferencia |
|---|---|---|---|
| Arte (`*-arte.js`) | 35.002 B (9,8 KB gzip) | 43.380 B (12,0 KB gzip) | +8,4 KB (+24 %) |
| Página de un archivo | 915.968 B (241,8 KB gzip) | 923.661 B (244,6 KB gzip) | +7,7 KB (+0,8 %) |
| CSS propio | — | 1.599 B | |
| Nodos SVG de la lámina | 494 | 568 | +74 (rótulos y leyenda) |
| Lámina pintada, 1280 px | 443–475 ms | 490–585 ms | +50 a +100 ms |
| Lámina pintada, 360 px con CPU ×4 | 4,9–7,2 s | 7,2–7,8 s | dentro del ruido (ver nota) |
| `validar_esquema.py` | OK | OK, 0 errores · 0 avisos | |
| `autocontrol.py --previa` | — | sin problemas (chequeo rápido 21 s) | |
| `autocontrol.py --final` | 4,88 | **4,88**, sin bloqueantes (mismas notas por criterio) | igual |

Nota sobre el tiempo: medido con Chrome sin ventana (cliente CDP de `medir_lamina.py`, mediana de 5 cargas; script en el scratchpad de la sesión). La máquina estaba cargada por otras sesiones: la **misma** página original dio 4,9 s en una corrida y 7,2 s en otra. Quité aparte el patrón de grilla y las sombras para ver si alguno pesaba: ninguno movió el tiempo más que el ruido. Conclusión honesta: en PC cuesta unos 50–100 ms; en celular no se puede afirmar una diferencia con esta máquina. Lo que pesa de verdad en las dos es three.js incrustado (~670 KB), no el arte.

**Celular 360 px**: sin desborde horizontal (scrollWidth = 360). El dibujo queda en 304×236 px, así que los rótulos saldrían de ~5 px: **se ocultan bajo 700 px** y quedan los nombres de grupo del motor (igual que antes). Los textos de contexto siguen en ~6 px, como en la original (es del motor, no del estilo). «Cómo funciona» en el celular se lee bien: etiquetas y leyenda de 15 px, flechas visibles sobre la manguera vertical.

**Tiempo que me tomó**: ~30 min de reloj (14:50 → 15:20), con ~8 min perdidos en tropiezos de herramientas (choque de nombre `ROT`, prefijo `esq-` que exige el validador, saltos de línea CRLF de Python en Windows, el panel del navegador que no abre archivos locales: se usó el servidor `estatico-dev`). De esos 30 min, el arte en sí fueron ~15.

## Qué se ganó
- Se lee **qué hace cada pieza sin tocar nada**: los rótulos responden «¿para qué sirve?» de un vistazo, como los afiches de referencia.
- El **color por sistema** deja ver el recorrido: el azul va de la bomba a la manguera y al cáliper; el naranja muestra que el pedal (CBS) también entra a la bomba. En la versión oscura todo era gris y negro.
- «Cómo funciona» ganó mucho con las **flechas**: la cadena mano → presión → pistón → apriete se ve en orden, paso a paso, sin leer el texto.
- Las mediciones automáticas (toque, solape, despiece, pasos) **no cambiaron**: el estilo no rompe lo que ya funcionaba.

## Qué costó
- +24 % de arte (+2 KB comprimido): despreciable frente a la página.
- Rótulos colocados **a mano** (punto en la pieza y posición del texto): unos 5–7 min por lámina y un ajuste tras la primera captura (tapaban la bomba y el cable del CBS).
- Tres colores fijos del arte original estaban pensados para fondo oscuro (crema de la barra, puente del cáliper, cable del CBS) y hubo que cambiarlos uno por uno. En otras láminas habrá más: cada `#2c3135` o `#c9bfa7` escrito a mano es un posible problema sobre fondo claro.

## Qué no funcionó o queda flojo
- **Rótulos y nombres de grupo del modelo v2 se repiten** («Bomba y manigueta» encima de «BOMBA · crea la presión»). Habría que elegir uno: o rótulos con función (y los nombres de grupo solo al pasar el dedo), o dejar los grupos y poner la función en la ficha.
- **Lienzo claro dentro de una página oscura**: se ve como una lámina pegada en la pizarra. A mí me parece aceptable y hasta bonito, pero no es el afiche claro de las referencias. Pasar toda la página a claro sería otro trabajo (CSS del motor) y no entraba en este piloto.
- **En el celular los rótulos no caben**: se pierden justo donde más se usaría la app. Haría falta otra forma (lista con color debajo del dibujo, o rótulos dentro del zoom de cada grupo).
- El metal se ve **más plástico que fotográfico**: con degradados lineales no se llega al realismo de las referencias (que son renders). Para más volumen harían falta degradados radiales por cara y reflejos curvos, lo que sube mucho el tiempo por pieza.

## Cómo se llevaría a la skill si se aprueba
1. **Paleta y `DEFS` comunes** en un archivo nuevo del motor (p. ej. `estilo-ilustrado.js` con `gAcero`, `gCromoV`, `gHidraulico`, `gMando`, `gFriccion`, `gElec`, sombras y grilla). Las láminas los referencian en vez de copiar sus defs: así el costo por lámina baja y todas comparten color por sistema.
2. **Campo `sistema` por pieza en el JSON** (`mando`, `hidraulico`, `friccion`, `electrico`, `motor`, `transmision`…) y que el motor pinte la leyenda solo. Un control del validador avisaría de colores fijos oscuros (`#1x–#3x`) sobre fondo claro.
3. **Rótulos como dato, no como arte**: `rotulo: {t: "inicia la presión", pos: [x, y]}` en cada pieza; el motor dibuja caja, línea guía y los oculta en celular, desarmado y zoom. Resolver antes la repetición con los nombres de grupo v2.
4. **Flechas de flujo en «Cómo funciona»** como regla de la plantilla: azul = presión/fluido, rojo = fuerza, (opcional) verde = aire/admisión, naranja = calor. Es la parte que más rinde por minuto invertido.
5. En `anexo-autocontrol.md`: comprobar contraste de números y textos sobre fondo claro y una captura de «Cómo funciona» en el paso de máxima acción.

**Estimado por lámina**: +15–20 min hoy (a mano, como este piloto); +5–8 min con los pasos 1–3 hechos en el motor (rótulos y elección de sistema por pieza). Rehacer las láminas ya aprobadas: unos 10 min cada una con el motor preparado, sobre todo revisar colores fijos y ubicar rótulos.

Recomendación: adoptar primero **solo las flechas en «Cómo funciona» y el color por sistema** (poco costo, mucha ganancia), y decidir los rótulos y el fondo claro de toda la página después de verlos con un usuario en el celular.
