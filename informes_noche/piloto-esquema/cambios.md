# Piloto de esquema: freno delantero NMAX 155 (lámina 22). Registro de cambios

## v7 (15-nov-2026), `v7.html` = `index.html`: nada tapa los números (`revision-ux-v6.md`)
- El selector **«Normal | Transparente»** salió de encima del dibujo. Ahora va en una fila propia, justo debajo, con la etiqueta «Dibujo» (`aria-labelledby`). Mantiene el estilo `.visor-modo`, los 44 px de alto y la sola fila a 360 px.
- La pista **«Toca una pieza»** tampoco va sobre el dibujo: pasó a esa misma fila, a la derecha (antes tapaba el número 2 armado y el 1 en el despiece).
- La **barra fantasma** (lámina 18) ya no se queda con el toque (`pointer-events="none"`). Su círculo tapaba el número 13. Su ficha sigue en la lista de piezas.
- Comprobado con `document.elementFromPoint` en el centro de cada número visible: **50 de 50** devuelven su propio número, en armado y en despiece, con «Normal» y con «Transparente», a 360, 390 y 1280 px. Sin desborde horizontal y con botones de 44 px.

## v6 (15-nov-2026), `v6.html` = `index.html`: dos versiones del dibujo
- **Selector «Normal | Transparente»** sobre la esquina superior izquierda del dibujo, con el estilo de `.visor-modo` del sitio (`role="group"`, `aria-pressed`, 44 px de alto, en una sola fila a 360 px). «Transparente» deja las carcasas semitransparentes (el caliper al 26 % con contorno lava; el soporte y los guardapolvos al 45 %), y las piezas internas se ven y se pueden tocar.
- Vale en la vista armada y en la explosionada. Se mantiene al cambiar de pestaña y al desarmar, y se recuerda en el navegador (`localStorage`, protegido con try/catch). El cambio es suave: transición de opacidad de 0,5 s.
- **«Números» pasa a ser un interruptor aparte** en la fila de controles (Desarmar · ◀ · ▶ · Números), independiente de la versión del dibujo. La fila cabe en una línea a 360 px.
- Las etiquetas «Barra derecha / Manguera» pasaron a la parte de arriba a la derecha para que el selector no las tape. El texto del armado ahora menciona «Transparente».
- Comprobado a 360 px: sin desborde, botones de 44 px y sin errores de consola. La transparencia sigue activa al ir a «Cómo funciona» y volver, y en el despiece.

## v5 (15-nov-2026), `v5.html` = `index.html`: P1 y P2 de `revision-ux.md`
- **Recorrido en pestañas** (`role="tablist"`, se navegan con las flechas, Inicio y Fin): Piezas · Cómo funciona · Si falla · Cuándo, dentro de un visor `.papel` con la barra de título del sitio. La ficha queda al lado, fija en computador. A 360 px la página bajó de unos 10.200 px a **2.540 px**. «Si falla → número» vuelve a la pestaña Piezas y elige la pieza.
- **Celular**: barra fija abajo con el número, el nombre y «Ver ficha». Lleva a la ficha y le pasa el foco al título; se esconde cuando la ficha está a la vista. La página no baja sola.
- **«Desarmar»** a 1,3 s por paso (armar de vuelta a 0,5 s), con «Pausa». Con `prefers-reduced-motion` salta directo al despiece completo o al armado. Durante la reproducción `#textoPaso` pasa a `aria-live="off"` y al pausar o terminar se anuncia solo el paso donde quedó.
- **Pista «Toca una pieza»** sobre el dibujo: late 3 veces (solo sin reducción de movimiento) y se va con la primera selección. Los números pasan del 55 % al 80 % de opacidad (contraste).
- **«Contradicciones» salió de la página** (está al final de este archivo). «Qué es seguro, qué es aproximado y fuentes» queda plegado al final: «De dónde sale esta información».
- **Accesibilidad**: `#ficha` sin `aria-live` (solo el foco al `h3`); el SVG pasa a `role="group"` con `aria-label`; un solo número tabulable por pieza (el segundo de 9, 5 y 10 queda con `tabindex="-1"` y `aria-hidden`).
- **Controles en una fila**: «Desarmar» (`.btn .btn-lava`) + ◀ ▶ redondos de 44 px + el selector «Números / Por dentro» con el estilo de `.visor-modo` (`aria-pressed`).
- **Leyenda de causas**: cada etiqueta tiene un `title` y, bajo «Cómo falla y por qué», un desplegable «Qué significa cada etiqueta» con las causas de esa pieza.
- **Consistencia con TallerYa**: crema `#ede3cc`, mostaza `#e3a72f`, botones y pestañas en Oswald en mayúsculas (`.btn`, `.visor-modo`), título `.titulo`, tarjetas `.papel` con radio de 18 px.
- Se mantiene: números discretos que abren la ficha con clic o teclado, el modo «Por dentro», textos del corte de 11,2 px a 360 px y botones de 44 px. Sin desborde ni errores de consola.

## v4 (15-nov-2026), `v4.html`: ajustes pedidos por el usuario
1. **Numeración discreta.** Los números son círculos pequeños (~18 px en pantalla), semitransparentes, de borde fino, y van fuera de la pieza con una guía corta punteada. Se resaltan al pasar el cursor sobre la pieza, al elegirla (lava), al tener el foco del teclado o con el interruptor **«Mostrar números»**.
2. **Modo «Ver por dentro»** (interruptor): el cuerpo del caliper queda al 26 % con un contorno lava suave, y el soporte y los guardapolvos al 45 %. Se ven, y se pueden tocar, el pistón, los sellos, las pastillas, el resorte, la lámina y el pasador. En armado, los números de esas piezas solo aparecen al pasar el cursor, al elegirlas o con el foco, para que no se amontonen sobre el caliper. (Esta lámina no tiene bomba ni tapa: van en la lámina 26.)
3. **Clic en el número abre la ficha.** Cada número es un botón (`role="button"`, `tabindex="0"`, `aria-label` «Ver la ficha de la pieza N: …») con un área de toque invisible de ~44 px. Con Enter o Espacio abre la ficha y pasa el foco al título. Los números ocultos (piezas internas, con el caliper armado) salen del orden de tabulación. Las piezas ya no son paradas de foco aparte: el teclado entra por los números y por la lista.
- Se mantiene: textos del corte de 11,4 px a 360 px, botones y chips de 44 px, sin desborde horizontal ni errores de consola.

## v3 final (15-nov-2026), `v3.html`: retoques de `revision-v2.md` (visto bueno, 4,67)
- «Cómo funciona» en el celular: los textos del dibujo miden 11,4 px en pantalla a 360 px (`#fn .fn-et` de 19 unidades; antes la regla perdía por especificidad). Las etiquetas que chocaban se reacomodan solo en el celular (`data-ym`/`data-xm`), y la «Manguera 2» baja por el borde derecho sin cruzar textos. Comprobado por código: ningún texto se cruza con otro ni se sale.
- Botones de 44 px de alto.
- Cuerpo del caliper (3) con la ventana del puente, por donde se ven los cantos de las pastillas y el borde del disco.

## v2 (15-nov-2026), `v2.html`: responde a `revision-v1.md` (3,67, sin visto bueno)
1. **Empaques cada 2 años con el líquido** (manual, pp. 9-7 y 9-25). Se corrigió en la tabla (ahora marcada «Seguro»), en la ficha 5, en la ficha 4, en la del caliper, en la del líquido y en la cadena «Líquido y empaques de más de 2 años». En la fila de limpieza, «Coherente» pasó a «Práctica de taller».
2. **Tornillos del disco: 3, seguro** (catálogo, fig. 22, ref. 2). Cambiados en `cat` y en la certeza, y quitados de los aproximados.
3. **«Cómo funciona» en el celular**: por debajo de 700 px el corte del caliper baja debajo de la bomba (`#fnCorte` corrido y `viewBox` 500×700), con su propia «Manguera 2». Ya no hay que deslizar: a 360 px el pistón, las pastillas, el disco y la rueda caben en pantalla (medido con `getBoundingClientRect`). El texto ya no dice «a la derecha».
4. **Resorte 11**: ahora es una lámina estampada, con ventana, pestañas dobladas y lengüeta.
5. **Pastillas 9 y lámina 14** en proporción ~2:1, con esquinas redondeadas, oreja con el agujero del pasador y ranura indicadora. La lámina tiene la misma silueta que la placa, con una pestaña.
6. **Soporte 13 en C**: espina con las orejas de los tornillos 15, dos brazos y los dos pasadores deslizantes cromados a la vista. Los guardapolvos 6 y 7 quedan sobre los pasadores.
7. **Despiece**: el encuadre se calcula con las posiciones finales (`calcularVBExp`). Las piezas chicas (grapas, sellos, purgador, pasador, guardapolvos) crecen 1,5× al salir. La zona baja se compactó.
8. **Áreas táctiles**: chips y botones de 44 px en el celular. Los números miden 28 px a 360 px sin taparse entre sí (se comprobó que no se cruzan), y la pieza entera también se puede tocar.
9. **Precisiones**: «varias veces (aprox.)» en vez de «8 a 10»; el sello se raya al meter el pistón sucio (con el consejo de limpiarlo); dos mangueras con banjo y arandelas nuevas (fig. 26, ref. 15 y 18); qué hace el ABS y que la purga con ABS es de taller.
10. **Legibilidad del corte**: la etiqueta del sello ya no la cruza el disco, y la manigueta va delante del puño, casi paralela.
11. **Contradicciones 9 a 11**: empaques sin intervalo en TallerYa, pastillas «cada 3.000 km» y manguera «cada año».
12. **Fichas más cortas**: a la vista quedan qué es, cómo falla, síntomas, cuándo y qué se compra. Para qué sirve, con qué se conecta, qué arrastra y la certeza van en un desplegable, abierto en computador y cerrado en el celular.

## v1 (15-nov-2026), `v1.html`
- **Vista armada** en SVG propio. Disco de 230 mm proyectado en 3/4, con canto, huecos que dejan ver el grosor y marcas de maquinado en la pista. Caliper flotante de un pistón, con volumen, rim light y grano de fundición. Soporte atornillado a la barra (la barra y la manguera van como fantasmas de otras láminas).
- **Despiece animado en 14 pasos**, en el orden real de desarme: tornillos 15 → caliper fuera de la barra → grapas 10 → pasador 12 → pastillas 9 → lámina 14 → resorte 11 → cuerpo/soporte 3/13 → guardapolvos 6/7 → purgador 8 → pistón 4 → empaques 5 → tornillos 2 → disco 1. Se puede desarmar todo, ir paso a paso o volver a armar. Al desarmar, el encuadre se abre y los números de la lámina aparecen.
- **Rayos X**: si estando armado se elige una pieza interna (pistón, pastillas, resorte…), el cuerpo se vuelve transparente.
- **Cómo funciona**: caliper cortado y animado en 7 pasos (manigueta → bomba → presión por la manguera y el ABS → pistón → el caliper flota → fricción y calor → el sello devuelve el pistón). Lleva una rueda que se frena.
- **Ficha por pieza** (15 + barra, manguera y líquido): qué es, para qué sirve, cómo falla y por qué (con etiquetas de causa), síntomas, cuándo revisar, si se repara o se cambia, qué se compra de verdad, con qué se conecta, qué les pasa a las demás si falla, y qué es seguro y qué aproximado.
- **5 cadenas de falla** clicables (pastilla al metal, líquido viejo, guardapolvo roto, retenedor de la barra, tornillos sin torque).
- Tabla de intervalos coherente con el plan (6.000 km pastillas; DOT 4 cada 2 años; mangueras cada 4 años).
- 8 contradicciones encontradas en TallerYa, y la lista de fuentes.
- Celular: el encuadre se acerca en la vista armada, los números se agrandan según el ancho, la lista de piezas se desliza en una fila y el corte de «Cómo funciona» se desliza a los lados. Revisado a 360 px sin desborde horizontal.

## Contradicciones encontradas en TallerYa (sacadas de la página en la v5; son para el equipo)
1. **El dibujo genérico no es el de la NMAX.** La lámina 22 usa el dibujo `freno_disco` de `garaje/diagramas.py`, que trae **dos pistones**, caliper rojo y disco tipo pétalo. El catálogo de la NMAX trae **un solo pistón** (un «PISTON ASSY» y un kit de dos sellos) y un disco **redondo**.
1. **Pastillas: «la manigueta llega más cerca del puño».** La ficha `BRAKE PAD KIT` lo pone como señal de pastillas gastadas. En un freno hidráulico el pistón se ajusta solo: con pastillas gastadas lo que baja es el **nivel del depósito** (manual, p. 9-24). Una manigueta que llega al puño o se siente esponjosa indica aire, líquido viejo o una fuga.
1. **Caliper: «la moto se va hacia un lado al frenar».** La ficha `CALIPER ASSY` trae un síntoma de carro. En una moto con un solo disco delantero no aplica. Mejor: «la rueda queda frenada o caliente», «olor a quemado», «una pastilla se gasta más que la otra».
1. **Pastillas: criterio de desgaste.** La guía dice «más de 2 mm». El manual de la NMAX usa las **ranuras indicadoras**. No se contradicen, pero conviene poner primero el criterio de Yamaha.
1. **Nombres repetidos.** El glosario traduce `BOLT` y `SCREW` como «Tornillo». En esta lámina son dos piezas distintas: el tornillo del disco (2) y los del soporte del caliper (15). Conviene nombrarlos por su lugar.
1. **Guardapolvos.** `BOOT, CALIPER` = «Guardapolvo del caliper» se confunde con el guardapolvo del pistón, que viene en el kit de empaques (5). Mejor: «Guardapolvo del pasador del caliper».
1. **Plan de la NMAX.** No tiene tarea propia de pastillas: usa la general de 6.000 km, que coincide con el manual salvo la revisión de los 1.000 km. Las mangueras (cada 4 años) no tienen tarea.
1. **«SUPPORT, PAD».** El glosario dice «Lámina soporte de las pastillas» y la ficha dice «lámina-resorte». Es lo mismo; «Resorte de las pastillas» se entiende mejor en el taller.
1. **Empaques del caliper sin intervalo.** La ficha `CALIPER SEAL KIT` dice «cada vez que se repara o se limpia a fondo el caliper». El manual de la NMAX manda cambiar los componentes internos de la bomba y del caliper **cada 2 años, junto con el líquido** (pp. 9-7 y 9-25). Este piloto, en su v1, también lo tenía mal.
1. **Pastillas: «revísalas cada 3.000 km».** Lo dice la ficha `BRAKE PAD KIT`, pero el plan de TallerYa y el manual dicen **6.000 km** (y la primera revisión a los 1.000 km).
1. **Manguera: «revísala cada año».** Lo dice la ficha `HOSE` del freno, pero el manual pide revisarla **en cada servicio** y cambiarla cada 4 años.
