# Piloto de esquema: freno delantero NMAX 155 (lámina 22). Registro de cambios

- **16-nov-2026 · AKT NKD 125 CBS 2025, clutch slipper (fig. E-4)** — segunda prueba de la skill `hacer-lamina` (catálogo no Yamaha): `motor/akt-embrague.html` (+ `datos/akt-embrague*.{json,js}`, `catalogo/akt-nkd125.json`), lista para revisión. Informe en `prueba-skill-akt.md`.
- **16-nov-2026 · Boxer CT100, clutch (fig. 14)** — prueba de la skill `hacer-lamina` en moto de cambios: `motor/boxer-embrague.html` (+ `datos/boxer-embrague*.{json,js}`, `catalogo/boxer-ct100.json`, extraído a mano). Validador OK, medición sin bloqueantes (4,72 medible). Informe de la prueba: `prueba-skill-boxer.md`. Falta revisión mecánica y de UX.
## Regla de dificultad más precisa (16-nov-2026, noche)
- `mas_controles.revisar_orden_y_dificultad`:
  - ahora busca el verbo (drena, drenar, vacía el aceite, el refrigerante o el líquido, quita la tapa) y no el sustantivo «drenaje»: «manguera, tubo o perno de drenaje» daban 22 avisos falsos en la fig. 8;
  - la regla del mando ya no toma «desconecta el cable», que en la fig. 26 es el del interruptor de freno;
  - se sigue mirando toda la secuencia, no solo el grupo: en la AKT vieja el paso que drena es del grupo «mando» y las piezas 10 y 14 están en otros grupos. Las versiones viejas siguen avisando (Boxer 1 aviso, AKT 3).
- Dificultad corregida, porque los avisos eran reales:
  - fig. 10: tornillos de las mitades del cárter (7 y 8) pasan a «taller», porque hay que abrir el motor; la junta de la tapa de la transmisión (20) pasa a «media»;
  - fig. 1: la arandela del tornillo de la culata (5) pasa a «taller» y la del drenaje del refrigerante (28) a «media».
  - A esas cinco piezas se les quitó `hazlo`.

## Pedidos de Auxiliares tras el Refinamiento 2 (16-nov-2026, noche)
- **Pasos del desarme de más de 300 caracteres** (los marca el validador en `chequeo_rapido --todas`): figs. 7, 8, 12, 22, 24 y 26 quedan por debajo de 300. No se quitó ningún aviso ni cierre. Lo de inspección pasó a la ficha: la malla del tamiz a la ficha 4 de la fig. 7, y «MIN TH» y los rodamientos, que ya estaban en sus fichas.
- **Píldoras sin pieza visible:** las piezas sí se ven armadas; el control mira `vis`. Una por grupo pasa a `vis: "arm"`: fig. 11 espuma 23 y sello 13, y fig. 12 rodamiento 30.
- **«La v1 decía nuevo»:**
  - fig. 26: se repuso que la tuerca autoblocante de las maniguetas 7 y 27 va nueva (se había perdido);
  - fig. 22: «pastillas nuevas» si el aceite de la barra las tocó;
  - figs. 12, 22 y 24: «nuevo» dicho de forma explícita (rodamientos 21 y 23, grapas 10).
- **`medir_lamina.py`:**
  - `--final`, también en `autocontrol.py --final`: no repite «Cómo funciona» ni el solape del desarme, que cubre `chequeo_rapido.py`. Fig. 7: 68 s, antes unos 2 min.
  - `cerrar()`: `Browser.close` por DevTools y luego `taskkill /T`. En Windows, `proc.kill()` dejaba vivos los procesos hijos. `chequeo_rapido.py` también lo usa.
- **Alto mínimo de marcas:** una sola constante, `ALTO_MIN_MARCA = 44` en `medir_lamina.py`, que `chequeo_rapido.py` toma de ahí. La diferencia 43/46 era de medida y la quitó el redondeo hacia arriba de la escala.
- **Kits** (`D.kits`): «Se vende en kit: nombre (ref. N)» en la ficha de cada pieza que lo trae y, en la vista general, la lista de kits. El nombre sale del `cat` de las piezas.
- **Alto del dibujo a 1280:** se calculaba antes de que cargara la letra, cuando la fila de controles ocupaba dos renglones, y quedaba en 402 px en vez de 469. Ahora se vuelve a medir con `document.fonts.ready` y cuando cambia el tamaño de la fila.

## Zoom a la vista y Transparente en todas (16-nov-2026, noche)
- `esquema.js` (`ZOOM_HTML`): en las láminas v2, los botones «+», «−» y «⤢ Ajustar» (que vuelve al encuadre completo) van en la fila de controles junto a «Números» y «Transparente». Tienen 44 px, quedan debajo del dibujo y no lo tapan. Funcionan en la vista general y dentro de los grupos (`fijarZoom` con `V2H.vb`), y comparten el estado con el pellizco que ya había. Antes estaban en `.esq-vista-fila`, que en v2 está oculta.
- `carcasas` en la Boxer (placa de los resortes 15 con brillo y manzana 8) y la AKT (portabalinera 9 con brillo y portadiscos 3). La corona no sirve como carcasa porque está detrás y no tapa nada. Así «Transparente» aparece en las 11 láminas; las 9 NMAX ya tenían carcasas. En los datos de la Boxer y la AKT solo se agregó ese campo.

## Correcciones UX, catálogo ↔ panel izquierdo y opciones v3 7, 8, 9 y 12 (16-nov-2026, noche)
- **Correcciones UX:**
  - Fig. 22 y 24: «Pastillas» con `data-xm` (22 px de separación de «Rueda» a 390). Los pasos de «Cómo funciona» quedan en ≤ 250 caracteres; el 3 tenía 397 y el 5 y el 6 también pasaban de 250, sin quitar avisos. El paso 4 ahora se ve: se ilumina el contacto pastilla-disco (`fn-contacto`) y los sellos se tuercen.
  - CVT: los pasos 4 y 6 quedan en ≤ 250.
  - Fig. 26: «Manguera» pasa debajo del tubo, lejos del cáliper.
  - Fig. 7 (y todas): la escala de las píldoras se redondeaba a 1 decimal (`f(sm)`), por eso las marcas medían 43 px. Ahora se redondea hacia arriba a 3 decimales y miden 46 px en todos los anchos. También se reescala con `ResizeObserver` del lienzo.
- **Catálogo → panel izquierdo** (regla en `criterios-del-usuario.md`):
  - `V2H.catalogo`, `centrarDibujo()` (descuenta la cabecera fija y la hoja inferior), filtro de «Si falla» y «Cuándo» con «Ver en el dibujo» y «Ver todo».
  - Abrir un grupo en la lista equivale a tocarlo en el dibujo.
  - En el celular, la ficha muestra la lista cuando no se ve «Piezas».
  - Probado a 1280 y 390 en la CVT, fig. 22, fig. 26, culata y Boxer: 0 errores.
- **Opciones v3:**
  - 7: `rodar` por ficha (sigue|pronto|no), una línea con punto de color bajo el nombre.
  - 8: `hazlo` {herr, min} solo con dificultad «facil», en «¿Se repara o se cambia?».
  - 9: glosario al tocar, hasta 2 términos por ficha, cada uno solo la primera vez, con subrayado punteado. Las definiciones salen de `garaje/despiece_glosario.py`; las marcadas «+» en `GLOSARIO` son nuevas.
  - 12: «Seguir con: *pieza*» en la vista general (localStorage con try/catch).
  - Valores **propuestos**, pendientes de la revisora: reglas en `side-session-notes/…/motor-rodar_hazlo.py`.

## Desarme general por bloques, Transparente en v2 y retoques de la revisora (16-nov-2026, tarde)
- `esquema.js`: «Desarmar todo» en la vista general empieza con un paso «Se separan los grupos»: cada grupo sale como bloque (dirección = desde el centro del sistema hacia el grupo, más hacia donde salen sus piezas) y las cajas de los grupos ya desarmados se empujan entre sí hasta no tocarse (margen `v2.margenGrupos`, 22 por omisión); después cada grupo se abre dentro de su zona. El encuadre crece con la separación y queda fijo en todo lo abierto (no salta en cada paso). `esq-fuera` solo cuenta el desplazamiento de los pasos, no el del bloque.
- `esquema.js` + `esquema.css`: interruptor chico «Transparente» junto a «Números» (en el celular solo el ícono, 44 px, misma fila), en la vista general y dentro de los grupos; usa el campo `carcasas`. Carcasas nuevas: fig. 1 (tapa de la culata, culata, cilindro), 7 (tapón, bomba), 8 (tapa y caja del filtro), 10 (cárter, tapa del respiradero, tapa de la transmisión), 11 (tapa exterior, tapa de la transmisión).
- Control nuevo: `medir_solape.js` (lo usa `medir_lamina.py`): % de cada pieza tapada por otras en el desarme general (rejilla de puntos y `elementsFromPoint`; las piezas atenuadas del otro lado no tapan). En la medición completa, a 1280: > 20 % o una pieza sin verse = bloqueante; 8-20 % = aviso. `medir_lamina.py --solape` lo corre solo (segundos) y dice qué pieza tapa a cuál con sus cajas.
- Solapes que había dentro de los grupos (piezas que ni se veían): corregidos moviendo el último paso de la pieza. Fig. 11: grapa bajo el tubo (100 % → 0). Fig. 10: pasadores y juntas bajo el cárter y las tapas (100 % → 6). Fig. 26: tapa, placa y diafragma del depósito, arandelas y pernos huecos, tope de las mangueras (100 % → 6). Fig. 1: empaque de la tapa y tornillos (20 % → 8). Fig. 7 y 8: 17 % y 10 % → 2 % y 7 %. Números del despiece reacomodados con `separar_numeros.py` en 1, 10 y 26.
- Retoques de la revisora: fig. 1, «(…°, ideal)» en los cuatro tiempos, el cruce de válvulas en el paso 5 y en el dibujo (la admisión abre desde 690° y el escape cierra a 20°: a 700° se ven las dos abiertas y el rótulo dice «Escape · cruce»); fig. 8 paso 6, «gastas más porque tienes que acelerar más»; fig. 11, el tablero dice «aprox. 25 °C» (35, 45, 55, 90). CVT: la correa de «Cómo funciona» va con temporizador, no con requestAnimationFrame.
- Firmas del armado: las 9 idénticas en piezas y capas (solo cambia `guiasG` por la temporización de las guías). Validador 0 errores en las 9; archivos únicos rearmados. Capturas: `capturas-motor-pedidos/fig11-desarme-general.jpg` y `fig11-transparente-grupo.jpg`.

## «Cómo funciona» rehechos al nivel de la CVT (16-nov-2026, 10:47-11:25)
- Fig. 8, 10, 7, 11 y 1: esquemas nuevos en `datos/<lamina>-arte.js` (`FN_SVG` + `fnAplicar`) y pasos en el JSON (`funciona`, `vbCelular` 0 0 480 840/870, columna derecha propia `#fnN-der` que baja con `translate(-480px,430px)` en el celular). Los cinco: medir_lamina «mínimo CUMPLE», sin bloqueantes, validador en 0 y archivo único rearmado.
  - 8: caja y filtro plisado en corte, cuerpo de aceleración con la mariposa y el ralentí, inyector rociando un cono, válvula y pistón; rpm y % de acelerador, aire y gasolina; mariposa y filtro de frente.
  - 10: cárter en corte con el cigüeñal, el aceite y la varilla; medición según el manual (caballete, calentar, esperar, limpiar, meter sin enroscar, leer); engranajes que salpican; retén en corte que gotea al disco; 0,90 L y 0,10 L.
  - 7: bomba trocoidal cortada que gira, cigüeñal con biela y pistón y levas animadas; tamiz con partículas; presión en bar (aprox.) y color del aceite según los km (0-6.000).
  - 11: rejilla, espuma del filtro en corte, aletas del variador, correa y clutch, salida y tubo de drenaje; °C de la correa (aprox.) y % de aire; limpieza del filtro según el manual (disolvente, nunca gasolina; húmedo sin gotear).
  - 1: los cuatro tiempos calculados desde el ángulo del cigüeñal (biela, pistón, levas, válvulas, color del gas, chispa entre 335 y 365°) con línea de 0 a 720°; bujía de cerca con 0,8–0,9 mm.
- Hallazgos: (1) los degradados de la lámina no se ven dentro de `#fn` (su SVG está oculto): cada esquema lleva sus copias `fnN…`; (2) `requestAnimationFrame` no corre con la pestaña oculta ni sin ventana: en las fig. 1 y 7 las animaciones calculadas van con temporizador.
- Fig. 26: el paso 6 de «Cómo funciona» bajó de 272 a 249 caracteres (se conserva «no se rellena hasta arriba con pastillas gastadas»). Queda la alerta de que no tiene indicador físico.
- Capturas a escala 0,5 en `capturas-motor-pedidos/como-funciona/`.

## Pedidos del usuario para el motor (16-nov-2026)
- `esquema.js`: `[[n|texto]]` se renderiza en todos los textos (ficha, «Cómo funciona», pasos, cadenas, «Cuándo», intros); elegir una pieza desde «Cómo funciona», «Si falla» o «Cuándo» pasa a «Piezas» y la muestra; «Desarmar todo» en la vista general (◀ ▶ de a un grupo; al entrar a un grupo o «Armar todo», se arma); con «Números», píldoras de grupo mínimas y apartadas de los números; tornillería más chica, semitransparente y a la zona libre más cercana con línea guía; guía de la píldora de grupo hasta su capa cuando no queda encima de ella; al pasar por un grupo, su píldora se alarga (sin viñeta aparte).
- `esquema.css`: navegación de la ficha fina (versalitas, 44 px invisibles), relacionadas en rejilla pareja con texto recortado (nombre completo en `title`/`aria-label`; `corto` opcional en la ficha), «Fuentes» como chip con ícono de libro; letra de «Cómo funciona» 16 px (≥ 12,2 px a 1280) y 22 px en el celular (≥ 12,3 px a 360).
- `medir_lamina.py`: bloqueante si queda `[[` sin renderizar en la página. Fig. 7: encuadre del armado ceñido a las piezas. Fig. 26: etiquetas de «Cómo funciona» separadas para la letra nueva.
- Firmas: solo cambian por la capa nueva `guiasG` (y el encuadre pedido de la fig. 7). Validador 0 errores en las 9; archivos únicos rearmados. Capturas en `capturas-motor-pedidos/`.

## Mejoras de la skill y del motor tras la fig. 1 (16-nov-2026, 09:47-10:07)
- Motor (`esquema.js`): las marcas de grupo se mantienen dentro del lienzo con su área de toque de 46 px, no solo con la píldora: ya no bajan de 44 px con un encuadre ancho. Firmas: 8 idénticas; en bomba-freno cambia solo `marcasG` (una marca que se salía 14 px por arriba ahora entra), medida igual (4,88, sin bloqueantes).
- `esqueleto_v2.py`: glosario de motor, nombres compuestos desde el catálogo («Empaque de la tapa de la culata»), grupos por función (`FAMILIAS`), repetidos con su grupo entre paréntesis y ids de grupo únicos (antes «Polea 2», «Empaque 4» o ids repetidos). `plantillas_ficha.py`: el lugar sale del grupo («Los tornillos que sujetan la tapa de la culata»).
- `autocontrol.py --previa` y `medir_lamina.py --solo-captura`: validador más captura a 1280 en ~20 s, para poner las notas a ojo antes de la medición final; con `--ojo` ya no sale «faltan… a ojo». Salida UTF-8 en los scripts que se caían con la consola de Windows.
- Skill: manual del propietario con pymupdf (solo texto), decidir la vista según la biblioteca, extrusiones con borde solo atrás, 3D dentro de contenido y segunda captura si hubo corrección visual.

## Fig. 1 de la NMAX: cilindro, culata y bujía (16-nov-2026, 09:27-09:46)
- Nueva: `motor/culata.html`, `motor/datos/nmax-fig1.json` y `nmax-fig1-arte.js` (culata, tapa, cilindro y bujía propios, vistos desde arriba; el resto con la biblioteca). 4 grupos, 10 pasos, 6 de «Cómo funciona» (los 4 tiempos y el refrigerante), 3 cadenas, 3D de la bujía (torno) y del cilindro (prisma con huecos).
- Del manual del propietario: NGK CPR8EA-9, 0,8–0,9 mm, 13 N·m, cambio a los 10.000 km o 12 meses; válvulas en frío cada 6.000 km; refrigerante cada 24.000 km o 2 años; no abrir el radiador en caliente (págs. 9-10, 9-11, 9-16 y 9-37). Los demás torques, «manual de servicio».
- Validador 0 errores; medición sin bloqueantes, 4,88 en lo medible. Pendiente: qué es la varilla 13 (y qué cierran el 3, el 4 y el 27), según el manual de servicio.

## Encuadre por estado, validador de nombres y correcciones de la fig. 10 (16-nov-2026, 08:46-09:25)
- Motor (`esquema.js`): `encuadreGrupo(g,k)` encuadra lo armado al entrar y se amplía con cada paso hasta lo desarmado (con animación; al instante con movimiento reducido). En el drenaje de la fig. 7 el tapón y el resorte pasan de < 24 px a ≥ 24 px a 360 (criterio 6: 4 → 5). `medir_lamina.py`: el socket espera 300 s (la fig. 26 tarda ≈ 200 s y cortaba a los 180 s). Firmas de 7 láminas idénticas (salvo la variación de 4 px del contexto del freno).
- Validador (`mas_controles.py`, `revisar_nombres_unicos`): aviso por nombres repetidos (el texto entre paréntesis distingue), por nombres con número suelto («Tapa 2»; no «DOT 4») y por pasadores o anillos guía con decisión «repara».
- Fig. 10: la 18 es «Tapa de la caja de la transmisión final» y la 24 «Tapa del respiradero» (en la grilla lleva el respiradero 29), con sus juntas, pasadores y tornillos; retén del cigüeñal en la mitad del alternador, se cambia sin abrir el cárter quitando el rotor (aprox., deducido del plano) y sale antes de abrir las mitades; pasadores 2, 6, 21 y 26 «reutiliza»; grapas antes del tubo del respiradero; respiradero más grande. Con el encuadre nuevo, 20 de 20 piezas ≥ 24 px (medible 4,87); no hizo falta partir «Aceite del motor».
- Fig. 11: espumas planas con nombre de lugar (sin números).
- Medido sin bloqueantes: freno 4,8 · CVT 4,72 · fig. 26 4,88 · fig. 8 4,88 · fig. 24 4,8 · fig. 11 4,88 · fig. 7 4,88 · fig. 10 4,87. Las 8 validadas y con archivo único rearmado.

## Motor, fig. 10 «Cárter y tapones del aceite» y retoques de la fig. 7 (16-nov-2026, 08:08-08:30)
- Motor (`esquema.js`): `"oculto":true` en una pieza común la esconde armada (como `esq-oculto-arm`); `minW` de `encuadreGrupo` 380 → 220 (grupos chicos más cerca en el celular); el buscador encuentra también las fichas de contexto (p. ej. «Aceite de motor» con «aceite»). `esquema.css`: las 8 reglas con `"Oswald"` sin respaldo pasan a `"Oswald","Archivo",system-ui,sans-serif`. Poner Archivo también en las reglas `"Oswald",sans-serif` ensanchaba la barra del visor sin red y bajaba el criterio 8 de 4,7 a 4,3 en 5 láminas: por eso solo las 8. Firmas de 7 láminas idénticas (el freno varía 4 px en el contexto, como antes); las 8 láminas validadas, medidas sin bloqueantes y con archivo único rearmado.
- Fig. 10: `M/datos/nmax-fig10.json` (con `armar_nmax-fig10.py`), `M/datos/nmax-fig10-arte.js` (cárter simplificado, varilla, tapón de llenado de la transmisión final, tapas 24 y 18, respiradero), `M/carter.html`, `M/prueba-nmax-fig10.html`, captura `M/nmax-fig10-1280.jpg`. 32 refs en 6 grupos: aceite del motor (10, 11, 14, 15), transmisión final (12, 13, 16, 17), tapa 2 y respiradero, tapa de atrás y retén del eje, soportes, cárter. Del manual: perno A y perno de la transmisión final con junta nueva a 20 N·m, varilla (medir sin enroscar), 0,90 L y 0,10 L de 10W-40, transmisión final a 1.000 km y cada 12.000 km o 1 año, fugas antes de cada uso. Medible 4,8 sin bloqueantes.
- Fig. 7: «Cuándo» separa el tamiz cada 12.000 km (Seguro) de «mirarlo cada vez que sale el tapón B» (práctica de taller); el paso del tamiz pide prender un par de minutos y revisar el nivel con la varilla.

## Retoques UX de la fig. 11 (16-nov-2026, revision-ux-fig11.md)
- Tapas con luz: tapa exterior más clara, borde claro, rejilla y 6 cabezas de tornillo visibles; tapa de aluminio con borde claro.
- Tubo de drenaje (6) propio (`arteTubo`) con área de toque invisible y la grapa antes en el orden: 19 de 19 piezas ≥ 24 px a 360 (criterio 6: 5; medible 4,88) y responde con la tapa armada.
- Espumas 16-23: cada ficha dice dónde va y que se pide por su código (el catálogo no trae juego). Visor: «Tapa y filtro de la correa» (las pestañas caben en una fila a 1280).
- Skill: piezas grandes oscuras con bordes y detalles; piezas comunes sin `esq-oculto-arm`; toque de tubos delgados.

## Fig. 7 NMAX «Bomba de aceite y drenaje» (16-nov-2026, 07:48-07:54, 6 min de reloj)
- `M/datos/nmax-fig7.json` (con `armar_nmax-fig7.py`), `M/datos/nmax-fig7-arte.js` (bomba con piñón, tamiz, tapón B, resorte y junta tórica propios, cárter de contexto con el perno A), `M/aceite.html`, `M/prueba-nmax-fig7.html`, captura `M/nmax-fig7-1280.jpg`. Ficha de contexto «Aceite de motor» (`ctx`).
- Del manual (Seguro): 10W-40 API SG+ JASO MA/MB, 0,90 L; tapones A y B a 20 N·m; junta tórica y junta nuevas; tamiz lavado con disolvente; motor tibio y aviso de quemaduras; cambio a 1.000 y cada 6.000 km; tamiz cada 12.000 km (plan TallerYa).
- Validador 0 errores, 0 avisos; medir sin bloqueantes (4,72 medible). Pendiente: resorte 5 a 20 px a 360.
- Para la skill: resorte y o-ring de la biblioteca no admiten `esq-oculto-arm` (se ven armados); si van dentro de una carcasa, dibujarlos propios.

## Retoques de la fig. 11 (16-nov-2026, visto bueno mecánico 4,8)
- Paso del filtro: «se exprime sin retorcer». Tornillos de la tapa: «aflójalos en cruz, un poco cada uno». Ficha 1: la caja de la correa es seca; aceite en la junta viene de un retén. Validador OK; archivo único rearmado.

## Correcciones de la fig. 24 (16-nov-2026, revision-mecanica-fig24.md)
- Dos láminas antirruido: 14a (contra el pistón) y 14b nueva (contra el cuerpo, detrás de la pastilla de afuera); `arteLamina(dx,dy)` en el arte; paso 6 y ficha 14 hablan de dos; las dos salen en el despiece.
- La grilla muestra el soporte atornillado (15) a la caja de la transmisión final, del lado del disco: el contexto pasa de «brazo trasero» a «Caja de la transmisión final» y la cadena del retén del eje queda (el aceite cae del mismo lado).
- Pieza 1: «Disco de freno trasero». Validador 0 errores; medir sin bloqueantes (4,8 medible); archivo único rearmado.

## Fig. 11 NMAX «Tapa de la transmisión y filtro de la correa» (16-nov-2026, 07:33-07:44, 11 min de reloj)
- `M/datos/nmax-fig11.json` (armado con `armar_nmax-fig11.py` sobre el esqueleto), `M/datos/nmax-fig11-arte.js` (tapa de aluminio con la toma de aire, tapa exterior de plástico con rejilla, filtro de esponja, sellos, respiradero y 4 espumas propias; la silueta de las tapas es la de `arteTapa` de la fig. 12), `M/tapa-transmision.html`, `M/prueba-nmax-fig11.html`, captura `M/nmax-fig11-1280.jpg`.
- 4 grupos: tapa exterior (8 + 12), espumas (14-23), filtro de la correa (9, 10, 11, 13) y tapa de la transmisión (1, 2, 5, 6 + 3, 4, 7). 10 pasos en el orden del manual. 3D del filtro (11).
- Del manual (Seguro): el filtro de la caja de la correa es de esponja, se limpia con disolvente (no gasolina) y se aceita, cada 6.000 km (págs. 9-4, 9-18 y 9-19); el tubo colector se limpia si tiene agua o mugre y entonces se revisa el filtro (pág. 9-18); correa cada 18.000 km.
- Validador 0 errores; medir sin bloqueantes (medible 4,8; con ojo 4,73). Pendientes: siluetas aproximadas, espumas planas genéricas, el 6 a 22 px a 360.

## Fig. 24 NMAX «Freno trasero» (16-nov-2026, 07:25-07:31, 6 min de reloj)
- `M/datos/nmax-fig24.json` (armado con `armar_nmax-fig24.py` desde la fig. 22: misma numeración 1-15), `M/datos/nmax-fig24-arte.js` (arte de la fig. 22 con disco de agujeros ovalados y `arteBrazo`, el brazo trasero como contexto), `M/freno-trasero.html`, `M/prueba-nmax-fig24.html`, captura `M/nmax-fig24-1280.jpg`.
- Cambios de contenido: códigos y `cat` de la fig. 24, manigueta izquierda, mangueras 34 y 38 de la fig. 26, brazo trasero y retén de la transmisión final (en vez de barra y retenedor), tornillos con pestaña (15), dos láminas antirruido (14), pastillas a 6.000 km (manual; el plan general de TallerYa dice 8.000: anotado).
- Validador 0 errores; medir sin bloqueantes (medible 4,8; con ojo 4,73). Pendientes: disco de 230 mm sin confirmar (aprox.), 3D sin `con3d` como la fig. 22, la pieza 4 a 23 px a 360.

## Pulido del motor y de la skill (16-nov-2026, 07:00-07:25, fase mejora_skill)
- `esquema.js`, toque automático (`toquesAuto`): primero las piezas enteras chicas (círculo de 13-15 px de radio, recortado solo entre ellas); después los racimos, recortados contra esos círculos y el dibujo de las piezas enteras (un racimo nunca achica a otra pieza); una pieza con un racimo ≥ 24 px no recibe círculos y, en las de racimos, se para en el primero que llega a 24 px. Nuevo `areaDib()`: las piezas delgadas (resortes, alambres; caja < 48 px y dibujo equivalente < 36 px estimados) cuentan como chicas; si el centro de su caja cae sobre otra pieza (aro), el círculo va al borde.
- Medido a 360 (medir_lamina): freno 2 → 1 pieza < 24 px (4: 22 px; medible 4,72 → 4,8); CVT 4 → 3 (19 y 3: 22 px, 5: 17 px; 4,72); fig. 26 4 → 0 (4,72 → 4,88); fig. 8 9 → 0 (4,88). Aviso nuevo, no baja nota: la 2 del variador no responde armada (su racimo queda de 12 px).
- CVT: los resortes 10 y los seguros 11 llevan `esq-oculto-arm` (ya no asoma su borde con el clutch armado; se ven al desarmar y en Transparente).
- `mas_controles.py`: «rica» como palabra completa con `texto_plano()` (NFC, sin guion suave ni enlaces `[[n|…]]`): nunca dentro de «eléctrica».
- `medir_lamina.py` y `autocontrol.py`: `--pagina` y `--captura` con el mismo formato (nombre solo = en motor/; con carpeta = desde la raíz); `autocontrol.py --captura` hace la captura en la misma medición, y la captura es del armado limpio (recarga la página).
- Skill: paso 3b «armar el JSON con script» (y `separar_numeros.py` después de cada regeneración), contenido + 3D juntos en el plan, una sola medición completa al final (`--rapido` mientras se trabaja), lectura del ejemplo solo de la lámina del mismo sistema.
- Firmas de las 4 láminas: idénticas. Validador OK en las 4; archivos únicos rearmados.

## Ajustes UX del motor y correcciones mecánicas de la fig. 8 (16-nov-2026)
- `esquema.js`: (1) toque mínimo automático en la vista de grupo: pieza o racimo de partes sueltas de menos de 24 px → círculo invisible de 24-30 px, recortado a la mitad de la distancia a la vecina; se crea solo en el grupo, así que las firmas del armado no cambian. (2) La píldora de tornillería se esconde cuando su pieza ya salió en el desarme (CVT: «Tuerca (1)» ya no tapa resortes y seguros). (3) El desarme automático dura como mucho ≈ 4,8 s (paso de 650 a 1300 ms según la cantidad de pasos): el cáliper y el variador ya no tardan 9 s.
- Medido a 360 (criterio 6 / promedio medible): freno 3→4 (4,72, aprueba); CVT 3→3,5 (4,63; quedan 18, 19, 3, 33 y 5); bomba-freno 4 (4,72); admisión 3→4 (4,72). Firmas: cvt, bomba-freno y admisión idénticas; freno solo con la diferencia de fuente ya conocida.
- `mas_controles.py`: `revisar_tecnologia` con las preguntas [S] 14a (carburador en una moto con inyección), 14b (silbido en una pieza antes de la mariposa) y 10a (paso con gasolina sin aviso de incendio). Tecnología por catálogo en `TECNOLOGIA` o `"tecnologia"` en el JSON.
- Fig. 8: «rica» → el computador manda menos gasolina; síntomas de la unión 22 sin silbido; paso del inyector con aviso de incendio; «recta»; tubo de drenaje con intervalo del manual (1.000 km y cada 6.000 km o 6 meses, pág. 9-4, «Seguro»); 27 pasa a «Tubo de drenaje de la tapa»; sin `toqueExtra` manual. Archivos únicos de las 4 láminas rearmados.

## Biblioteca de formas de lámina y fig. 8 «Admisión y filtro de aire» (16-nov-2026)
- `motor/piezas-comunes.js`: tipos nuevos `manguera`, `abrazadera` (orejas o tornillo), `caja` (con tapa, tornillos y bocas), `ducto` y `placa` (empaques, placas, espumas), con arte 2D y maqueta 3D. Los tipos viejos no cambian: firmas de cvt.html y bomba-freno.html idénticas; freno.html difiere 4 px en el ancho de una capa de contexto, pero igual con la biblioteca vieja (ancho del texto según la carga de la fuente).
- `mas_controles.py` reconoce los tipos nuevos; `esqueleto_v2.py` los propone (CLIP/HOSE CLAMP, PIPE/HOSE, DUCT, CASE, GASKET/PLATE) y se arregló «PIN», que tenía retrocesos literales en vez de `` y nunca calzaba. En la fig. 8 la biblioteca cubre 29 de 37 piezas (antes 15). Tabla en `anexo-formato.md`.
- Fig. 8 NMAX: `datos/nmax-fig8.json`, `datos/nmax-fig8-arte.js`, `admision.html` y `prueba-nmax-fig8.html`. 7 grupos, 9 pasos, 3 cadenas, «Cómo funciona» de 5 pasos (camino del aire, mariposa, ralentí, inyector, filtro tapado), 3D en 16, 33 y 19. El JSON es la fuente (se edita directo). Validador OK, medir sin bloqueantes, 4,55 medible (criterio 6 en 3, como la fig. 22 y la CVT).

## Adopción del modelo v2 en las 3 láminas (16-nov-2026, 33 min)
- Motor único: `motor/esquema.js` + `esquema.css` ya traen el v2 (lo de `esquema2.*`). Un JSON sin «v2» sigue viéndose con el modelo viejo (firmas v1 idénticas). Respaldo de los archivos viejos en `capturas-rediseno/respaldo-v2/`.
- Fig. 26: la v2 es la oficial (`datos/nmax-fig26.json`, `bomba-freno.html`); la vieja queda en `nmax-fig26-v1.json` y `bomba-freno-v1.html`. `armar26v2.py` queda retirado (la v2 se edita directo).
- Fig. 22 (3 grupos: disco, cáliper, pastillas) y fig. 12 (5: tapa, variador, correa, campana, clutch) migradas con `capturas-rediseno/armar_v2.py` desde sus `…-v1.json` y textos v2 (`v2-textos-*.json`, borrador de subagentes sonnet con `brief-textos-v2.md`, revisado). Lados opcionales: sin selector cuando hay uno solo.
- Ajustes del usuario: (a) píldoras chicas (11 px, borde fino) con etiqueta corta en reposo y completa al pasar/enfocar, toque invisible de 46 px; (b) enlaces en línea crema con subrayado punteado, sin romper el renglón; (c) «Pedir repuesto» y «Talleres» como enlaces chicos con ícono junto a «Para pedirla», toque de 44 px; (d) celular: hoja inferior que asoma con nombre y «Qué es», se sube para la ficha completa, se baja o ✕ para cerrar, y sube la página si taparía el dibujo; (e) marcas «✓ manual» / «≈ aprox.» al final de cada dato (`certezaDe`) con su explicación al tocarlas, y un solo enlace «Fuentes».
- En un grupo, el contexto (barra, manguera, tapa) se atenúa y deja pasar los toques. Validador: `revisar_estructura_v2` (grupos, tornillería, pasos, lados, `certezaDe`, `con3d`).

## Rediseño de prueba de la fig. 26 (16-nov-2026): menos números y menos botones
- Nuevo, sin tocar lo aprobado: `motor/bomba-freno-v2.html`, `motor/esquema2.js` (copia de `esquema.js` con el modo v2), `motor/esquema2.css`, `motor/datos/nmax-fig26-v2.json` (lo arma `capturas-rediseno/armar26v2.py` desde `nmax-fig26.json`).
- Dibujo: selector Delantera | Trasera para todo el sistema; 4 grupos por lado (5 atrás) con marca con nombre; al tocar uno se acerca y solo ahí se tocan sus piezas (silueta resaltada y nombre al pasar). Tornillería por punto en una marca («Unión (3)»). Números solo con «Números». Desarme por grupo (1 a 3 pasos).
- Lista plegable por grupos con la tornillería plegada y buscador; en computador va en el panel de la ficha. Ficha en el orden pedido, con ‹ anterior | siguiente ›, causas con ícono que se explican al tocarlas, «Para pedirla» con código del catálogo.
- 49 fichas reescritas (segunda persona, enlaces en vez de «(N)», sin nombres de catálogo). Validador: `revisar_estilo_v2` en `mas_controles.py` (solo para JSON con «v2»).
- 3D solo en bomba y kit (4 números); 3D de la bomba armada en el panel del grupo.
- Firmas de CVT, freno y fig. 26 actual: idénticas. Capturas en `capturas-rediseno/`.

## Lámina 26 de la NMAX (16-nov-2026): bombas de freno, mangueras y líquido. Prueba de la skill `hacer-lamina`
- Archivos: `motor/datos/nmax-fig26.json`, `motor/datos/nmax-fig26-arte.js`, `motor/bomba-freno.html` y el archivo único `motor/prueba-nmax-fig26.html`. El motor no se tocó.
- Son 49 números y 57 piezas (los pernos de unión y las arandelas se dibujan en las dos puntas), 17 pasos, 7 de «Cómo funciona» (la bomba cortada con el orificio de compensación, las copas, el resorte, el interruptor de la luz y el nivel con el diafragma), 4 cadenas y 3D en la bomba y el kit (más las comunes de la biblioteca).
- Vista desde el asiento: la bomba delantera a la derecha y la trasera a la izquierda. La unidad ABS y el manubrio son contexto.
- `validar_esquema.py` da OK. `medir_lamina.py` no tiene bloqueantes y da UX 4,58. Faltan la revisión mecánica y la de UX.

## v9 del motor (16-nov-2026): revisión UX de la CVT (`revision-ux-cvt.md`, 4,3) — afecta al freno y a la CVT
- **Computador (≥960 px):** el dibujo usa el alto que deja la pantalla (`--esq-alto` = alto de la ventana − borde superior del lienzo − 76 px, mínimo 340; lo calcula `esquema.js` y se recalcula al cambiar el tamaño) y los controles van en UNA fila (`display:contents` sobre `.esq-vista-fila` y `.esq-herr`, como `integracion/plantilla_integrado.html`): Normal|Transparente, Desarmar, ◀ ▶ y Números; la pista pasa a la línea del paso. Resultado (`medir_distribucion.js`): dibujo de 453 px de alto a 1280×800, 421 a 1024×768 y 530 a 1440×900, siempre completo y con «Desarmar» a la vista; sin desborde; botones de 44 px o más.
- **Celular (≤700 px):** la lista de piezas pasa de carrusel a rejilla de números de 44 px (6 columnas a 360): 296 px de alto en la CVT y 200 en el freno. El nombre va en `title` y `aria-label`; las piezas de otras láminas (·) ocupan 3 celdas y conservan su nombre. Tocar un número hace lo mismo que el chip. En computador la lista sigue igual.
- **Freno idéntico salvo eso:** con las dos reglas nuevas desactivadas en el navegador, la firma (posición y estilo de todos los elementos, 8 estados) da exactamente la de antes a 1280 y a 360.
- **CVT:** el sello 15 se dibuja como el 14, en otra medida (`arteRetenes` con radio 17), y la cadena «Grasa que se escapa atrás» dice «sellos (14 y 15)».
- **Verificación:** validador en OK en las dos láminas. Toques 100 % y 0 roces: freno 7/7 y 18/18, CVT 8/8 y 33/33, a 360 y 1280. Sin errores de consola. El punto 3 (texto de «Cómo funciona» junto al dibujo en el celular) quedó sin hacer.

## CVT (16-nov-2026), `motor/cvt.html`: segundo piloto, lámina 12 «Variador, correa y clutch» (NMAX BBE4)
- **Archivos:** `motor/datos/nmax-fig12.json`, `motor/datos/nmax-fig12-arte.js`, `motor/cvt.html` (copia de `freno.html` con las rutas cambiadas) y `motor/prueba-nmax-fig12.html` (archivo único). No se tocó `esquema.js`, `esquema.css`, `diagramas.py`, `v8.html`, `integrado*` ni `integracion/`.
- **Dibujo propio, desde cero, en el estilo de la v8** (fondo oscuro, degradados, sombras, forro de fricción). Vista «caballera»: las caras de las poleas son círculos y la profundidad del eje va arriba a la derecha, así cada pieza se dibuja en su `z` y el despiece es solo traslación. De `_cvt` se tomaron la disposición (variador adelante, polea trasera con clutch atrás) y el orden de armado.
- **33 números con pieza y ficha**, más la tapa como contexto (línea punteada, ficha `ctx`). La tornillería que va en anillo (pasadores 9, resortes 10, seguros 11, deslizadores 4) se junta hacia su centro al salir, para que el despiece se lea por grupos.
- **Armado:** 8 números visibles (28, 6, 1, 25, 24, 29, 13, 12). **Transparente:** campana 24 y polea de aletas 6 al 24 %, polea móvil 1 y portazapatas 7 al 42 %.
- **Desarme en 15 pasos:** tapa (30-32 quedan en ella) → tuerca 28/arandela 27 → polea de aletas 6/arandela 33 → tuerca 29 y campana 24 → conjunto trasero → correa 25 → polea móvil 1 con todo → buje 5 → rampa 3 → rodillos 2 → arandela 26 y deslizadores 4 → portazapatas 7 (21, 22, 20) → zapatas 8, resortes 10, seguros 11, pasadores 9 → resorte 18 y asiento 19 → mitades 13/12 con 14-17 y 23.
- **«Cómo funciona» en 7 pasos** (ralentí, enganche, relación corta, rodillos que salen, crucero, «baja el cambio» con carga, soltar). Tres vistas: la correa de lado (los radios cambian), el variador cortado (mitad móvil, rodillo en la rampa, correa que sube) y el clutch de frente (zapatas que salen y se ponen naranja al agarrar; la campana gira solo cuando agarra). Tacómetro con las rpm. En el celular la columna derecha baja debajo de la vista lateral.
- **Fichas, cadenas (5) y «Cuándo» (5)** con certeza por dato. Seguro: correa cada 18.000 km (indicador V-BELT) y filtro de la caja cada 6.000 km (manual del propietario NMAX 2022, plan de TallerYa); clutch centrífugo y potencia máxima a 8.000 rpm (1000PS). Aproximado y marcado: rpm de ralentí y de enganche, rodillos 20×12 mm/13 g y correa 2DP-E7641-00 (vendedores, NMAX 2019-2022), y sin torques ni ancho mínimo de correa (no está el manual de servicio).
- **Pendiente importante:** los **nombres y cantidades de cada número** se reconocieron por la forma en el plano, porque la tabla de partes (base local y PDF) no se pudo leer en esta sesión. Están marcados «aprox.» en `cat` y en la certeza de cada ficha. Falta cruzarlos con la tabla, sobre todo la tornillería 9-11, 14-17, 19-23 y 26-33.
- **Carcasas en el JSON (motor, 16-nov):** nuevo campo `carcasas` (`[{"id","transparente","rayosx","brillo"}]`); `esquema.js` genera con él las reglas de Transparente y rayos X en un `<style id="esq-carcasas">` del `<head>`, y se quitaron de `esquema.css` las reglas fijas del freno (`#pz-3/13/6/7`). El freno tiene su campo equivalente (3: 0,26 con brillo; 13, 6 y 7: 0,45; rayos X 0,22) y la CVT el suyo (24 y 6: 0,24 con brillo; 1 y 7: 0,42; rayos X 0,2). Se quitó el `<style>` de `montar()` en la CVT; las piezas que se juntan al salir usan ahora la clase genérica `esq-junta` del motor. `validar_esquema.py` revisa que cada carcasa sea una pieza y que las opacidades estén entre 0 y 1. Firma (posición y estilo de todos los elementos, 8 estados): el freno da idéntico a 1280 y, a 360, idéntico en estilo (solo cambia el ancho del dibujo). La CVT da idéntica en armado, Transparente y despiece; con una pieza elegida, la rampa 3 y la polea 13 ahora se atenúan como las demás (antes la regla propia las dejaba enteras por error).
- **Revisión mecánica (`revision-mecanica-cvt.md`, 4,6), corregido el 16-nov:** (1) leva de torque: las ranuras inclinadas van en el cuello de la polea móvil (13) y los pasadores guía (16) con sus rodillos (17) van fijos en el eje de la polea fija (12); se corrigieron las fichas 12, 13, 16 y 17, el paso 15, el paso 6 de «Cómo funciona» y el dibujo (el eje de la 12 ya no muestra ranuras sino las cabezas de los pasadores). (2) El portazapatas va sujeto con una tuerca grande (21) con su arandela (22), que se suelta con compresor y llave especial: paso 12 y fichas 21-22 reescritos, dibujo de tuerca y arandela, todo «aprox.». (3) Las rampas de los rodillos están en los canales de la polea móvil y la placa (3) es la pared de atrás, casi plana: fichas 1, 2 y 3, paso 9, cadena «Rodillos planos», paso 4 de «Cómo funciona» y su corte (placa plana, cara inclinada en la polea móvil, el rodillo sube pegado a la placa). (4) Limpiar el polvo a los 6.000 km quedó como práctica de taller, con su certeza «Aproximado». Validador en OK; toques 8/8 y 33/33 a 360, 390 y 1280, 0 roces.
- **Cruce con la tabla de partes (16-nov):** los 33 nombres y cantidades quedaron confirmados con el catálogo de la BBE4 (`cat` con la descripción del catálogo y certeza «Seguro»). Tres números eran otra pieza: **9** son amortiguadores de caucho de las zapatas (no pasadores; dibujo nuevo `arteDamper`); **20** es la tuerca del portazapatas (antes «placa»; ahora tuerca); **21 y 22** son el rodamiento de bolas del eje de la polea fija y su anillo de seguro (vuelven a su dibujo y salen en el paso 15, no en el 12). **15** es un segundo par de sellos, no O-rings; **17** son bujes guía. Código de la correa en el catálogo: B8R-E7641-00. Siguen aproximados: el tipo de cada rodamiento, el peso de los rodillos y las cifras de rpm. Validador en OK; toques 8/8 y 33/33 a 360, 390 y 1280, 0 roces.
- **Verificación:** `validar_esquema.py` en OK. Toques al centro y a ±9 px, armado y despiece, Normal y Transparente: 360 → 8/8 y 33/33; 390 → 8/8 y 33/33; 1280 → 8/8 y 33/33; 0 roces en todos los casos. Distribución (360, 390, 1024, 1280): sin desborde, botones de 44 px o más. Sin errores de consola. **Alto a 360 (motor):** `.esq-visor` pasa a 10 px de margen lateral por debajo de 420 px; el dibujo mide 236 px a 360 (antes 234) y 260 a 390, sin cambiar el encuadre. Toques después del cambio: freno 7/7 y 18/18, CVT 8/8 y 33/33 a 360, 390 y 1280, 0 roces.

## v8 (15-nov-2026), `v8.html` = `index.html`: toques sin roces, margen del 1 y zoom en el celular (`revision-ux-v7.md`)
- **Números del despiece separados** (`et` en `PIEZAS`): 9b `[36,50]`, 14 `[54,34]`, 4 `[-22,76]`, 5a `[36,86]` y 5b `[29,-20]`. El 5b quedaba sobre el brazo inferior del soporte (13), que se dibuja después y le robaba el toque. Ahora queda arriba, fuera del soporte.
- **Área de toque limitada** (`radiosToque()`, se llama desde `escalarEtiquetas()`): el círculo invisible de cada número mide como mucho la mitad de la distancia a su vecino tocable más cercano (y nunca más de los 25 de antes). Se recalcula al desarmar, al cambiar Normal/Transparente y con el zoom. Radio mínimo en pantalla: 11,2 px a 360, 12,8 px a 390 y 22,2 px a 1280.
- **Margen del 1 en el armado**: `VB_ARM=[223,140,613,477]` (10 unidades más abajo; el ancho crece lo mismo en proporción para no cambiar la relación 900:700, así el encuadre no salta). El número 1 queda a 4,9 px del borde inferior a 360 (antes, pegado), a 5,9 px a 390 y a 22 px a 1280.
- **Zoom del dibujo en el celular (≤ 700 px)**: botones + − ⤢ de 44 px en la fila «Dibujo», debajo del lienzo, así no tapan números. Cada toque acerca o aleja ×1,6 (hasta ×4) y ⤢ vuelve al encuadre completo. Pellizco con dos dedos (el punto bajo los dedos se queda quieto). Con zoom, un dedo arrastra el dibujo (`touch-action:none` solo mientras hay zoom; sin zoom la página se desplaza como siempre). Un arrastre no cuenta como toque de número. Al pasar de armado a despiece (o al revés) el zoom vuelve a ×1. Clases nuevas: `esq-zoom`, `esq-zoom-b` y `esq-ampliado`, que no existen en `tallerya.css`.
- A ≤ 440 px la pista «Toca una pieza» va más apretada para que el zoom quepa en su misma línea (la fila mide 103 px a 360 y 390).
- **Comprobado** con `elementFromPoint` en el centro de cada número visible (armado y despiece, Normal y Transparente): **50/50** a 360, 390 y 1280. A ±9 px del centro (4 direcciones), **0 roces** en los tres anchos (en la v7 había 3 a 360). Con zoom ×2 en el despiece: 4/4, sin roces. Botones de 44 px como mínimo, sin desborde y sin errores en la consola.
- `medir_distribucion.js`: dibujo de 301×234 a 360×740, de 331×258 a 390×844 (completo, con «Desarmar» y las pestañas a la vista) y de 682×531 a 1280×800. A 1280×800 el dibujo termina en 801 px (le falta 1 px) y «Desarmar» queda abajo. En la v7 pasa lo mismo en este navegador (servido como `data:`), así que no lo trae la v8. Apoyo: 14 % a 360, 13 % a 390 y 11 % a 1280. Hueco de columnas: 1 % y 0 % (fija) a 1280.

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
