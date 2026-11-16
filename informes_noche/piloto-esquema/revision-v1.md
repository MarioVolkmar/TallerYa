# Revisión v1: piloto del freno delantero NMAX 155 (lámina 22)

Revisora · 15-nov-2026 · revisé `index.html` (= `v1.html`) abriéndolo a 1024 px y a 360 px, con despiece completo, ida y vuelta,
fichas, «Cómo funciona» reproducido, y el texto completo contra el catálogo BBE4 (fig. 22 y 26), el manual B6Y4
y las fichas, el glosario y el plan de TallerYa.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad al plano y a las fotos | **3** | Están las 15 referencias, con su número y cantidad, y el orden de desarme es lógico. Pero: la cantidad de tornillos del disco (2) está marcada como «no confirmada» y el catálogo sí la trae (**3**). La forma del resorte (11) no corresponde, las pastillas y la lámina 14 están mal proporcionadas y el soporte (13) está muy simplificado. |
| 2 | Exactitud mecánica | **4** | Muy buena: el cáliper flotante, el sello que devuelve el pistón, el nivel que baja con las pastillas, el DOT 4 que absorbe agua, la manigueta que palpita por un disco torcido y el ABS en la línea están bien explicados. **Un error de intervalo**: el manual manda cambiar los empaques del cáliper (y de la bomba) **cada 2 años**, y el piloto dice «cada vez que se abre el caliper» y lo marca «Coherente». |
| 3 | Pedagogía | **4** | El lenguaje es claro y local (Las Palmas, Santa Elena) y las causas van etiquetadas. «Cómo funciona» se entiende muy bien en computador. En el celular, en cambio, la animación pasa fuera de pantalla (ver 5). Las fichas son largas: 11 bloques por pieza. |
| 4 | Congruencia | **4** | Las cadenas de falla y los «se conecta con» están bien. La lista de 8 contradicciones es valiosa y acertada (la manigueta que «llega al puño», la moto que «se va hacia un lado», los dos pistones del dibujo genérico). Faltan contradicciones: el intervalo de los empaques, la ficha HOSE («revísala cada año» contra «en cada servicio») y la ficha BRAKE PAD («cada 3.000 km» contra 6.000 del plan y del manual). |
| 5 | Calidad visual y celular | **3** | Sin errores de consola y sin desborde horizontal a 360 px (scrollWidth = 360). El estilo es TallerYa (mostaza y crema, Oswald). Pero en el despiece las piezas quedan pequeñas y sobra espacio vacío. A 360 px, en «Cómo funciona» solo se ve la bomba y el cáliper queda a la derecha, fuera de pantalla, mientras corre la animación. Las áreas táctiles son chicas: los chips de la lista miden 22–34 px de alto y los números 19 px. |
| 6 | Reglas | **4** | El dibujo es propio (no es un calco del encuadre del plano), no hay emblemas, cita fuentes con enlaces y distingue lo seguro de lo aproximado. Un dato está mal clasificado: la cantidad de tornillos del disco es segura (sale del catálogo). |

**Promedio: 3,67. Visto bueno: NO** (dos criterios en 3 y un error de intervalo frente al manual).

## Lo que está bien (no tocar)
- El funcionamiento del cáliper flotante, paso 5: «el cuerpo se corre hacia el otro lado y trae la otra pastilla».
- El sello que se tuerce y devuelve el pistón, sin inventar un resorte.
- El nivel del depósito que baja con el desgaste («si alguien lo rellena, al poner pastillas nuevas se rebosa»). Es exacto y muy útil.
- El ABS en la línea (bomba → ABS → cáliper) y la barra derecha (el catálogo dice RIGHT y las fotos lo confirman).
- DOT 4 con 230/155 °C (FMVSS 116), sin mezclarlo con DOT 5, y el cambio cada 2 años.
- «Qué se compra de verdad»: kit de empaques antes que un cáliper entero, disco siempre con pastillas nuevas, purgador con inserto de rosca.
- Las 8 contradicciones y la sección de seguro contra aproximado.
- Sin desborde horizontal a 360 px y sin errores de consola. Respeta `prefers-reduced-motion`.

## Cambios pedidos (en orden de prioridad, todos verificables)

1. **Intervalo de los empaques (error mecánico).** El manual B6Y4 dice en la p. 9-7 «Cada dos años cambie los componentes internos de las bombas de freno y de las pinzas y cambie el líquido de frenos», y en la p. 9-25 «Juntas de freno: cada 2 años».
   - En la tabla 4, la fila «Empaques del caliper (5)» debe quedar: **«Cada 2 años, junto con el líquido (manual), o antes si hay fuga o el freno queda pegado»**, con la marca «Seguro».
   - Corregir igual la ficha 5 (`cuando`), la ficha 4 si menciona el intervalo y la cadena «Líquido de más de 2 años».
   - Añadir esto como contradicción n.º 9: la ficha CALIPER SEAL KIT de TallerYa no da intervalo.
2. **Tornillos del disco (2): son 3, seguro.** El catálogo, en la fig. 22, ref. 2, dice `90109-08232 BOLT` con cantidad **3** (la columna BBE4 sí se lee con `pdftotext -layout`).
   - Cambiar `cat` a «BOLT · 3 piezas».
   - Mover la `certeza` a «ok» con la fuente «catálogo».
   - Quitar «Tres tornillos: no está confirmado» de la lista de aproximados.
3. **«Cómo funciona» en el celular.** A 360 y 390 px, el cáliper (que es la parte principal) debe verse sin deslizar. Propuesta: debajo de 700 px, apilar en vertical (bomba y manguera arriba, cáliper cortado abajo) o dibujar un segundo encuadre solo del cáliper. Así se puede quitar `min-width:680px`.
   - Cambiar también el texto «A la derecha, el caliper…», que en el celular no es cierto.
   - Verificación: a 360 px, durante los pasos 4 a 7, el pistón, las pastillas y el disco se ven completos en la pantalla sin desplazar.
4. **Forma del resorte de las pastillas (11).** Hoy está dibujado como un alambre en zigzag. En el plano es una **lámina estampada** con pestañas dobladas, y así lo describe la propia ficha («una lámina de acero doblada»). Hay que redibujarla como lámina.
5. **Proporciones de las pastillas (9) y de la lámina antirruido (14).** Hoy se ven como tiras de unos 3,5:1. En el plano y en las fotos son casi 2:1, con esquinas redondeadas, una oreja con el agujero del pasador (12) y la ranura indicadora a la vista. La lámina 14 debe tener la silueta de la placa de la pastilla, no la de una tira.
6. **Soporte (13).** Hoy es un rectángulo gris. Debe mostrar la forma en C del plano, con las dos orejas de los tornillos (15) y **los dos pasadores deslizantes salientes** donde van los guardapolvos 6 y 7. Es lo que hace «flotar» el cáliper y la ficha insiste en eso, así que el dibujo debe dejarlo ver.
7. **Tamaño del despiece.** Con el despiece completo a 1024 px, las piezas chicas (grapas 10, sellos 5, purgador 8) miden menos de 20 px y la mitad del lienzo queda vacía.
   - Ajustar `VB_EXP` al contenido o agrandar las piezas pequeñas.
   - A 360 px separar el 10 y el 12, que hoy se tocan arriba a la izquierda, y los dos «5».
8. **Áreas táctiles en el celular.** Chips de la lista y botones de las cadenas de ≥ 44 px de alto: hoy `.cadena button` tiene `min-height:28px` y los chips 22–34 px. Las bolas numeradas también deberían medir ≥ 28 px a 360 px, o la pieza entera debe ser el área de toque.
9. **Precisiones mecánicas menores:**
   - a) Paso 3: «8 a 10 veces» mezcla la palanca con la parte hidráulica. Basta con decir «la palanca y la diferencia de tamaño de los pistones multiplican tu fuerza varias veces (aprox.)».
   - b) Cadena 1, paso 4: el sello se raya sobre todo **al empujar el pistón hacia adentro para meter pastillas nuevas** con la parte expuesta sucia. Conviene decirlo y añadir el consejo de limpiar el pistón antes de empujarlo.
   - c) Ficha «manguera»: en la NMAX son **dos mangueras** (1: bomba→ABS; 2: ABS→cáliper; fig. 26, ref. 15 y 18) con tornillos banjo y **arandelas nuevas**. Al cáliper llega la 2.
   - d) Una línea sobre el ABS en «Cómo funciona» o en la ficha de la manguera: qué hace (afloja y vuelve a dar presión si la rueda se va a bloquear) y que con ABS la purga es trabajo de taller.
10. **Legibilidad del corte.** En «Cómo funciona», la etiqueta «Sello (lo devuelve)» queda atravesada por el disco: hay que moverla. La manigueta está dibujada colgando hacia abajo y lejos del puño; debe ir **delante del puño y casi paralela**, como en la moto.
11. **Contradicciones que faltan** (añadir a la sección 5):
    - ficha BRAKE PAD «revísalas cada 3.000 km» contra 6.000 km del plan y del manual;
    - ficha HOSE «revísala cada año» contra «en cada servicio» del manual;
    - el punto 1 de esta lista.
12. **Opcional, si sobra tiempo:** acortar las fichas. Mostrar de entrada «qué es / síntomas / qué se compra» y plegar el resto («ver más»), sobre todo en el celular.

## Para la v2
Lo bloqueante son los puntos 1 a 6. Con 1 y 2 el criterio 2 sube a 5 y el 6 a 5; con 3, 7 y 8 el 5 sube a 4; con 4 a 6 el 1 sube a 4 o 5.
