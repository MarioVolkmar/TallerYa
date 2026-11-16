# Prueba 3D en la ficha (CVT, lámina 12), 16-nov-2026

**Respuesta corta: sí es viable.** El visor está en `esquema3d.js` (un motor de ~170 líneas, compartido). Cada pieza de revolución cuesta unas pocas líneas de JSON. Sin commit.

## Qué se hizo
- `esquema3d.js` es el visor. Usa una cámara ortográfica en ángulo isométrico (35,26°) y tiene 4 vistas (45°, 135°, 225° y 315°) con ◀ ▶. La transición dura 650 ms; con «reducir movimiento» el cambio es instantáneo. Se puede arrastrar: de lado gira; arriba y abajo solo con el mouse, para que en el celular el dedo siga moviendo la página.
- La iluminación va pegada a la cámara, así que el sombreado se ve igual en las 4 vistas. Lleva contorno oscuro en las aristas y la paleta de los dibujos. Hay un solo renderer para toda la página: no se acumulan contextos WebGL.
- three.js 0.160 se toma de los estáticos del sitio y se importa **solo al abrir una ficha con `forma3d`**. En el archivo único va como texto y se importa desde un Blob.
- Cambios en `esquema.js` (2 líneas en `pintarFicha`): si la ficha trae `forma3d` y la página cargó el visor, se agrega el visor bajo la cabecera.
- `cvt.html` suma `<script src="esquema3d.js">`. `armar_un_archivo.py` mete el visor y three solo si la lámina tiene `forma3d`.
- Hay clases `esq-v3d*` nuevas al final de `esquema.css`.
- Datos: `fichas[k].forma3d = {partes:[...]}`. Los tipos son `torno` (perfil r,z cerrado), `sector`, `cilindro` (con `esc` para óvalos), `caja` y `correa` (barrido de la sección por las dos poleas, con dientes). Todas las partes aceptan `color`, `giro` y `repetir`. Es el mismo vocabulario de `isometrico.py` (cilindro, prisma).
- `diagramas.py` (solo leído) no sirve directo para esto: `_cvt()` es conceptual (polea = cono simple, zapatas de r36-52) y sus medidas no cuadran con el arte de esta lámina. Las medidas se tomaron del arte (`nmax-fig12-arte.js`). Como el arte es frontal, no hay perfiles 2D que reutilizar tal cual; sí se reutilizan los radios y los ángulos (zapata ri58/ro82 a ±46°, campana r92 × 36 con 5 ventanas a r50, correa r48/r100 a 310).

## Pieza por pieza
Tokens de datos = largo del `forma3d` en el JSON. El contexto total de la sesión fue de unos ~95 mil tokens, la mitad en leer el relevo, el motor y el arte. El trabajo por pieza fue ~5-10 mil cada una, más ~25 mil del visor.

| Pieza | Tiempo aprox. | Costo | Fidelidad |
|---|---|---|---|
| Rodillo (2) | 2 min | 231 caracteres; 2 tornos | Alta: funda con chaflanes y buje metálico. Pieza trivial. |
| Polea móvil trasera (13) | 5 min | 364 caracteres; 2 tornos y 3 cajas | Buena: cono de ~14°, cuello y agujero. Las 3 ranuras inclinadas de la leva de torque son «calcomanías» oscuras, no cortes reales: en 2 de las 4 vistas casi no se ven. |
| Correa (25) | 10 min (generador de ~25 líneas, una vez) | 192 caracteres | Buena: sección trapezoidal (36/26 × 14) y 72 dientes por dentro. Recorrido real del armado. Con 220 px los dientes apenas se notan. |
| Campana y una zapata (24) | 8 min | 901 caracteres; 3 tornos, 2 sectores, 3 cilindros y 1 caja con repetición | Buena: tambor, dos nervios, 5 ventanas ovaladas, 5 nervios radiales y cubo. La zapata (cuerpo, forro y pasador) va adentro, a 4 de la pared, como en reposo. Ventanas y pasador también son calcomanías. |

La pieza 13 es la polea móvil **trasera**, porque así la numera esta lámina. Si se quería la del variador (1, con canales para los rodillos), hay que tallar canales: es lo mismo que las ranuras, calcomanía o geometría a mano.

## Peso y rendimiento
- Peso: `esquema3d.js` pesa 11,3 KB (5,1 KB con gzip) y siempre se carga. three.js pesa 670 KB (166 KB con gzip), solo al abrir una ficha 3D. En el sitio ya lo usa moto3d, con la misma copia y la misma caché. Los datos suman ~1,7 KB por 4 piezas.
- El archivo único pasa de 135 KB a 819 KB, porque trae three adentro.
- Medido en este PC con el visor a 360 px (lienzo de 289 × 220, pixelRatio ≤ 2):

| Pieza | Llamadas de dibujo | Triángulos | ms por cuadro | Armar |
|---|---|---|---|---|
| Rodillo | 20 | 1.280 | 0,9 | ~47 ms |
| Polea 13 | 26 | 1.572 | 2,0 | ~195 ms (incluye la carga de three) |
| Correa | 3 | 2.496 | 0,5 | ~38 ms |
| Campana | 64 | 4.228 | 2,1 | ~67 ms |

- Se dibuja solo cuando algo cambia (transición, arrastre o cambio de tamaño); en reposo no consume. En un celular de gama media, estimo 4 a 6 veces más lento: menos de 12 ms por cuadro, holgado para 60 fps en la transición. **No se probó en un celular real.** Las llamadas de la campana se pueden bajar uniendo las geometrías, si hiciera falta.
- A 360 px: el visor ocupa 289 × 220, los botones miden 45 × 44, no hay scroll horizontal y no hay errores de consola (cvt, archivo único y freno).
- El freno no cambia: no carga el visor y su ficha sigue igual. La CVT solo cambia en las 4 fichas con modelo. El validador da OK en las dos láminas.

## Recomendación
- **Sí vale la pena, pero no para todas las piezas.** Conviene en las de forma que cuesta imaginar desde el dibujo plano: poleas, campana, correa, rampa, zapatas, bujes con estrías. Sobra en tornillos, arandelas, clips y sellos: un anillo girando no enseña nada.
- **Baratas** (2-5 min, menos de 400 caracteres): todo lo de revolución (poleas, rodillos, bujes, rodamientos, arandelas, discos de freno, tuercas), extrusiones planas (rampa de 3 brazos, zapatas, pastillas, placas) y correas o cadenas (el generador ya existe).
- **Caras** (15-40 min o más): formas irregulares fundidas, como el cáliper, la tapa de la CVT, el carrier con sus torres o un soporte. Piden cortes de verdad (CSG) o una malla hecha a mano. Las ranuras, los canales y las ventanas como calcomanías salen baratos y se ven bien de lejos; cortes reales serían caros.
- Si se adopta: unir geometrías por material (menos llamadas), una regla en el validador para `forma3d` y quizás un botón «Ver en 3D» que cargue three solo cuando el usuario lo pida, en vez de al abrir la ficha.

## Archivos
`esquema3d.js` (nuevo), `esquema.js` (2 líneas), `esquema.css` (bloque al final), `cvt.html` (1 línea), `armar_un_archivo.py` (bloque 3D), `datos/nmax-fig12.json` (forma3d en 13, 2, 25 y 24), `prueba-nmax-fig12.html` y `prueba-nmax-fig22.html` (regenerados), `prueba-3d-ficha-360.jpg` (captura).
