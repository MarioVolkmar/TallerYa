# Rondas de la skill `hacer-lamina` (encargo nocturno)

## Ronda 5 (después de la lámina 1: freno Crypton FI 115, fig. 25)

Sin commit. `M` = `informes_noche/piloto-esquema/motor`.

### 1. Extractor Yamaha Colombia (bilingüe)
- `M/catalogo/extraer_catalogo.py` detecta la cabecera «DESCRIPCION / DESCRIPTION». En cada fila, el renglón de arriba va a `descripcion` (español) y el de abajo a `descripcion_en` (inglés). Antes juntaba los dos: «PLACA ACCESORIA PLATE, FITTING».
- Se agregó `--moto`. Antes el campo `moto` del archivo decía «nmax-bbe4» aunque el catálogo fuera de otra moto.
- `M/catalogo/crypton-bf24.json` se regeneró: 39 figuras, 630 filas, ninguna descripción vacía. El arreglo a mano de la fig. 25 (el inglés en `descripcion` y el español en `es`) queda reemplazado por los campos estándar, los mismos de Honda y Boxer, que ya leen `esqueleto_v2.py`, `plantillas_ficha.py` y `claves_es.py`.
- El validador compara el nombre de la ficha contra el español y contra el inglés, y mira los lados (RIGHT/LEFT) y los nombres de catálogo en la prosa sobre `descripcion_en`. `crypton-freno` sigue con 0 errores.
- La NMAX salió idéntica byte a byte (`regresion.py`). El Crypton bilingüe entró a la regresión del extractor, con su referencia guardada.

### 2. Receta 3b: `M/remapear_hermana.py` (nuevo)
- Uso: `remapear_hermana.py <lamina> --desde <hermana> --mapa '{…}' --arte --escribir`.
- Cambia los números una sola vez y todos a la vez, así que 3→1 y 1→3 no se pisan. Abarca:
  - piezas, incluidas las de sufijo («5a»→«3a»);
  - pasos, fichas (claves, `conecta` y `efectos`) y enlaces `[[n|…]]`;
  - **ids de las cadenas**;
  - `sujeta`, `ocultas`, `carcasas`, `ordenChips`, `nombres`, `kits`, `refsFigura`, `contexto` y `v2` (grupos, `torn`, `con3d` y `toqueExtra`).
- **Idempotente:** anota `hermana` y `remapeo` en el JSON. Si se corre otra vez con el mismo mapa, no hace nada. Con otro mapa se niega y explica por qué. Se niega también si un número viejo sin mapa choca con uno nuevo.
- `--arte` copia el arte de la hermana y lista sus funciones y rótulos de texto con su línea. También avisa de las funciones que ninguna pieza usa. Así no hace falta leer el arte ni los textos de la hermana.
- **Control nuevo en `--rapido`** (`mas_controles.revisar_rastros`, cuando hay `hermana` y `remapeo`): error si un enlace o un eslabón de «Si falla» copiado de la hermana no tiene el número remapeado, sea porque quedó el viejo o porque se remapeó dos veces. Las cadenas con refs que no existen ya daban error en el validador (`validar_esquema.py`).
- **Prueba** con la fig. 22 remapeada:
  - remapeada bien: 0 errores;
  - remapeada dos veces: 10 errores;
  - cadenas de la hermana sin remapear: 7 errores.

### 3. Validador
- **Falsos positivos quitados** (probados sobre `crypton-freno`):
  - la marca propia: «Yamaha» en una lámina Yamaha, detectada por el catálogo y su PDF;
  - «sin ABS» o «no tiene ABS» ya no cuentan como mención de ABS;
  - «junta» como verbo («la grasa junta polvo»): solo cuenta como sinónimo de empaque si va con artículo («una junta nueva» sí avisa).
- **Rastros en `cabeza.cinta` y en los rótulos del arte:**
  - con `hermana` en el JSON, nombrar la figura de la hermana es error. La cinta «TallerYa · lámina 22» ahora se atrapa;
  - una «fig./lámina N» igual a la de una hermana de otro catálogo da aviso («verifícala»). Esto cubre «(lámina 18/26)» copiado al arte.
- Se agregó «Crypton/BF24» a las marcas.

### 4. Tokens de creación (~175 mil)
**Medición en la transcripción de la lámina 1:**
- La sesión además escribió fichas de NMAX: unos 15 mil caracteres de otra tarea.
- De la lámina en sí:
  - unos 95 mil caracteres en resultados de herramientas y 4 imágenes;
  - unos 72 mil caracteres que escribió el modelo, de ellos 23 mil en el script de armado.
- **Lo más grande que dependía de la skill:**
  - **Manual de taller: unos 12 mil caracteres.** Volcaba el texto entero de 24 páginas (88-112) para buscar el procedimiento. Ahora `M/buscar_manual.py`:
    - `--indice` da las secciones con su página del PDF y la impresa en ~1,8 mil caracteres;
    - las palabras salen en una línea por hallazgo, con tope de 12 (≈ 1,2 mil).
    - SKILL.md manda usarlo y prohíbe `get_text()` de páginas enteras.
  - **Pasos, «Cómo funciona» y fichas de la hermana: unos 9 mil caracteres. Arte de la hermana por rangos: unos 13 mil.** Ahora `remapear_hermana.py --arte` copia todo y lista solo funciones y rótulos (~1,5 mil caracteres).
  - **Páginas del manual en el informe de la revisora:** dice «págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1])» con la página impresa real. Antes decía «impresa ?» en el manual de taller y la revisora corría el índice en uno. Al final trae la línea de `buscar_manual.py` para buscar más.
- **Lo que no se puede recortar desde la skill:**
  - el script de armado, que es el trabajo en sí;
  - las 4 imágenes;
  - la carga de la skill (unos 26 mil caracteres más los anexos que se leen).
- Ahorro estimado en una lámina con hermana de otra numeración: 25-30 mil caracteres (~8-10 mil tokens) de resultados. Como cada resultado se vuelve a pagar en los turnos siguientes, el ahorro de contexto es mayor.

### Archivos
- **Nuevos:** `M/remapear_hermana.py` y `M/buscar_manual.py`.
- **Cambiados:**
  - `M/catalogo/extraer_catalogo.py` y `M/catalogo/crypton-bf24.json` (regenerado);
  - `M/mas_controles.py`;
  - `M/informe_revision.py`, que toma `MANUALES` de `buscar_manual.py` (una sola lista, ya con el Crypton);
  - `M/regresion.py` (Crypton en el extractor) y `M/regresion/ref/ext-crypton.json`;
  - SKILL.md: paso 1 (`--moto` y bilingüe), «leer poco» (manuales con `buscar_manual.py`), receta 3b con `remapear_hermana.py` y `"hermana"` también con la misma numeración, y la lista del motor. Quedó en 26.268 caracteres (antes 26.310);
  - `anexo-autocontrol.md`: controles de rastros y Crypton en la regresión.

### Verificación
- `regresion.py`:
  - validador en las 16 láminas: 0 errores;
  - extractor y esqueleto idénticos;
  - `crypton-freno` en el navegador sin bloqueantes.
- El motor de dibujo (JS/CSS) no se tocó, así que las firmas no cambian.
- Pruebas puntuales de los falsos positivos, del remapeo (idempotencia, rechazo con otro mapa y control de enlaces y cadenas) y de `--arte`.

## Ronda 6 (después de la lámina 2: rueda trasera y transmisión AKT NKD 125, fig. F-8, sin hermana)

Sin commit. `M` = `informes_noche/piloto-esquema/motor`.

### 1. Validador (`M/mas_controles.py`)
- **`v2.grupos[].torn`:** es error si no es una lista de objetos `{nombre, corto, ids:[…], cant}`. Ahora pide también `corto`. Un `torn` malo no corta el grupo: se sigue revisando con la tornillería que sí tiene formato.
- **Cada grupo en su propio `try`:** si un grupo falla, sale como error con el nombre del grupo y siguen los demás. Prueba con `torn:["1","2"]` en un grupo y un id inexistente en otro: salen los 3 errores (el formato, el id y la pieza sin grupo). Antes no salía ninguno.
- **Cada control de `revisar()` en su propio `try`:** una excepción sale como «`control` no terminó (…)» y los demás controles corren igual. Prueba con `cuando: 5`: 12 errores reportados y ningún corte.
- **Pasos desde 250 caracteres:** el aviso de pasos largos salta desde 250 (antes 300) y ahora incluye «Cómo funciona».

### 2. `M/esqueleto_v2.py` y `M/catalogo/claves_es.py`
- **Kits repetidos:** «20A» junto a «20», los dos kit o juego, es el mismo repuesto en otra versión. El repetido no lleva ficha, dibujo ni grupo: va en `kits` (`{"20A":["20"]}`) y en el `cat` de la 20 («también en el kit ref. 20A (…, código)»). El validador ya acepta ese formato.
  - «Kit Tornillos Sprocket» queda como tornillería del grupo.
  - Un kit de arrastre se marca como `cadena`, con una línea que dice cómo partirlo (cadena + piñón y corona, en un solo grupo).
- **«Jgo Caucho Campana»:** pasa a ser amortiguador de la campana (`DAMPER, HUB`), no un caucho de montaje ni tornillería. Tiene una plantilla de ficha propia, `caucho-campana`: el tirón de la cadena, el juego al acelerar, cuándo mirarlo.
- **Figuras de rueda** (título con RUEDA o WHEEL): se agrupan por eje, freno, arrastre y rueda. Las piezas sin lugar propio (buje, balinera, retén, arandela) van con la de antes, salvo que digan «rueda».
  - La F-8 da 4 grupos (antes 10): eje 1, 2, 23 + tuerca 24 · freno 3-9 · rueda 10-14, 25, 26 · arrastre 15-20, 22 + kit de tornillos 21.
  - Coincide con lo que dejó la creadora, salvo el buje 22, que ella movió al eje.
- **Aviso de CBS o ABS:** si el modelo del catálogo los trae («AKT NKD 125 CBS»), el esqueleto avisa que es parte del nombre de la moto y que no se nombre como sistema de la figura.
- **Nombres de llantas:** quedan limpios («Neumatico», «Llanta»; antes «Llanta 3.-»).
- La F-8 entró a la regresión del esqueleto (`esq-akt-rueda`). Las otras referencias siguen idénticas byte a byte.

### 3. Paso 9: el resumen de la revisora nunca queda viejo
- `informe_revision.py` escribe la huella del JSON en la primera línea de `revision/<lamina>.md`.
- `autocontrol.py` rehace el resumen:
  - siempre con `--final`;
  - con cualquier corrida (también `--rapido`) si el JSON cambió desde el anterior.
  - Lo dice en una línea: «INFORME: … rehecho».
- Si el validador tiene errores, `--informe` avisa que no se lance todavía la revisora.
- Ya no depende de la memoria de la sesión: después de la última corrección, cualquier `autocontrol` lo deja al día.

### 4. `M/aplicar_hallazgos.py`
- Un reemplazo que deja un paso (`pasos.N.t` o `funciona.pasos.N.t`) en más de 250 caracteres visibles no se aplica. Va «a mano», con el largo que tendría.
- Si el texto ya pasaba de 250, se aplica siempre que no lo alargue.
- Probado con `--probar`: uno largo rechazado (347) y uno corto aplicado.

### 5. Biblioteca (`M/piezas-comunes.js`): rueda y transmisión final
- **Formas nuevas, de frente, con 2D y 3D** (la cadena solo 2D):
  - `rin`: radios cruzados, o `tipo:"aleacion"` con brazos;
  - `llanta`: con tacos;
  - `pinon`: dientes, huecos de aligerado y pernos; sirve para piñón y corona;
  - `cadena`: un tramo por puntos, o la vuelta a dos piñones con `c1, r1, c2, r2`, que calcula las tangentes;
  - `eje`: cabeza hexagonal; el vástago solo se ve desarmado;
  - `tensor`: placa con ranura, marcas, perno y tuerca.
- Están registradas en el validador (`COMUNES`) y en el esqueleto (reconoce rin, llanta, piñón o corona, cadena o kit de arrastre, eje y tensor, con medidas por omisión). Las medidas están en `anexo-formato.md`.
- **Cobertura en la F-8:** de 11 a **16 de 26 piezas (62 %)** salen de la biblioteca desde el esqueleto. Quedan propias: portabandas, leva, eje abrebandas, indicador, bandas, campana, radios sueltos, cauchos, porta sprocket y neumático.
- **Verificación:**
  - una página de prueba con las seis formas juntas, revisada con una captura y borrada;
  - `regresion.py` del motor: firmas iguales en la CVT, la culata y la transmisión de AKT, y navegador sin bloqueantes;
  - `regresion.py --todas`: 14 de 14 láminas sin bloqueantes (107 s).
- La firma de la culata oscilaba 1 px de redondeo entre corridas. Ahora `regresion.py` tolera ±1 px y lo informa aparte.
- **Meta de 10 min (no se cambió):**
  - En la lámina 2, dibujo + contenido tomó 7 min contra 4, con 15 piezas de arte propio.
  - Con 62 % de biblioteca quedan unas 10 piezas propias.
  - Estimo que dibujo + contenido baja a 5,5-6 min y una lámina sin hermana queda en unos **11-12 min con revisión**, todavía sobre la meta.
  - Lo que falta para llegar a 10 son las fichas desde cero (26 en la F-8). La palanca siguiente serían plantillas por sistema (rueda, freno de tambor), no solo por tipo de pieza.

### Archivos
- **Cambiados:**
  - `M/mas_controles.py`, `M/esqueleto_v2.py`, `M/catalogo/claves_es.py` y `M/plantillas_ficha.py` (`caucho-campana`);
  - `M/informe_revision.py` y `M/autocontrol.py`;
  - `M/aplicar_hallazgos.py`;
  - `M/piezas-comunes.js`;
  - `M/regresion.py` (F-8 en el esqueleto y tolerancia de ±1 px) y `M/regresion/ref/` (referencias nuevas).
- **Skill:**
  - SKILL.md: grupos de rueda, kits y CBS en el paso 2, biblioteca de ruedas en el plan, resumen automático en el paso 9 y aviso de 250. Quedó en 26.243 caracteres (antes 26.268).
  - `anexo-formato.md`: tabla de las seis formas.

## Ronda 7 (después de la lámina 3: horquilla y dirección NMAX, fig. 18, hermana `cb125f-horquilla`)

Sin commit. `M` = `informes_noche/piloto-esquema/motor`.

### 1. `M/remapear_hermana.py`
- **Mapa con identidad:** `"8":"8"` ya no da «queda sin mapa y choca». Un número del mapa no cuenta como «sin mapa» aunque vaya a sí mismo.
- **`--espejo X --mapa-lado '{…}'`, para el lado repetido.** Duplica, reflejado en x = X:
  - las piezas: anclas, `et`, las de biblioteca con `p.x` y sus puntos, y las de arte propio con `tr`, una transformación que el motor ahora acepta;
  - las fichas, los nombres, los enlaces, los movimientos de los pasos, `sujeta`, `ocultas`, chips y carcasas;
  - los grupos: si todo el grupo es de un lado, crea un grupo gemelo `<id>-2`; si está mezclado, las copias entran al mismo grupo.
  - En la copia se cambia «izquierda» por «derecha» (si no hay lado, el nombre lleva «(otro lado)»).
- **«Heredado sin respaldo»:** al terminar, contra el catálogo nuevo (`--catalogo`/`--figura`, o los del `.esqueleto.json`), lista:
  - las fichas cuyo nombre empieza por una pieza que su descripción no dice («O-ring» donde dice GASKET, «Asiento» donde dice CYLINDER COMP.);
  - el equipo que la figura nueva no trae («tija de arriba», ABS, CBS, carburador, cadena o correa, tambor…).
  - Probado con la horquilla Honda contra la fig. 18: salen el asiento, la arandela→GASKET y el o-ring→GASKET, los mismos graves de la revisora.

### 2. Falso positivo de «¿remapeado dos veces?» (`M/mas_controles.py`)
- Ya no se comparan enlaces ni cadenas de fichas nuevas ni de piezas sin equivalente en el mapa (el lado espejado, los «seguro» o «tapón» propios). Solo se comparan los que vienen de una pieza mapeada y van a otra mapeada.
- `nmax-horquilla`: 0 errores (antes más de 10). Las pruebas de remapeo doble y de cadenas sin remapear siguen atrapándolos: 10 y 7 errores.

### 3. Rastros de la hermana también en `visor` y `pie`
- Ahora se revisan `visor.titulo`, `visor.sub` y `pie`. Además «Fig.» con mayúscula ya cuenta como referencia a figura; antes solo «fig.».
- Probado: «Fig. F-8 · 19 números» da error (es la figura de la hermana) y «horquilla CB 125F» da el rastro de otra moto.

### 4. Plano sin grilla: lo genera `M/esqueleto_v2.py`
- Imprime «plano: <ruta>»: la grilla de `despiece_local/grillas/` si existe. Si no, genera con pymupdf la página del plano (entre la página de la tabla y la anterior, la de menos palabras), a 900 px.
- La imagen va a la **carpeta temporal del sistema** (`%TEMP%/tallerya-grillas/`), fuera del repo. Escribir en `despiece_local/` me lo bloqueó el permiso de la sesión: es la carpeta de fuentes, y ahí no escribí nada.
- Probado con la fig. 25 del Crypton: sale el plano completo con la tabla. Y con la F-8 de AKT. El PDF solo se lee.
- SKILL.md («Para ver la lámina») ahora dice que se mire la imagen de «plano:».

### 5. `anexo-desarme.md`: reglas por tipo de moto
- Sección nueva antes de los sistemas, con cuatro tipos:
  - scooter: el gato central levanta solo la trasera; la delantera, con calzo o elevador; carenajes;
  - cub o semiautomática: cubrecadena cerrado;
  - calle sin gato central;
  - con CBS o ABS: el orden de ajuste y purga.
- Control nuevo `revisar_gato` (aviso): un paso que pone la rueda delantera en el aire con el gato central, sin calzo ni elevador.
  - **Ya avisa en 4 láminas hechas**, que heredan el mismo paso 0 de la fig. 22: `nmax-fig22`, `crypton-freno`, `cb125f-freno` y `cb125f-horquilla`. **Quedan para corregir:** es contenido y no lo toqué.

### 6. `M/aplicar_hallazgos.py`: varios hallazgos sobre el mismo campo
- Se ubican todos en el texto original y se aplican juntos, de atrás hacia adelante («en cadena: N hallazgos sobre …»).
- Si dos se enciman, el segundo va a mano y el aviso dice con cuál. Si juntos pasan los 250 caracteres, van a mano diciendo el largo.
- Probado: dos que no se enciman se aplican, y el que se encima va a mano con el motivo.

### 7. Motor: «Desarmar» a la vista al entrar a un grupo (`M/esquema.js`)
- Al entrar y al salir de un grupo, el motor vuelve a calcular el alto del dibujo, porque la fila de controles cambia («‹ Vista general»).
- Con la medición completa de `nmax-horquilla`, «Desarmar» queda a la vista en los 6 anchos (antes «no» a 1024 y 1280).
- A 1280×800 queda con poco margen: termina en 796 de 800.

### 8. Motor: toque mínimo sin `toqueExtra`
- **Diagnóstico** en el navegador, a 360: las piezas 6, 10 y 26 sí tenían círculo de toque, pero los tapaban vecinas pintadas después (pz-4, pz-5, pz-17, pz-20), que en el desarme quedan a menos de 24 px.
- **Dos cambios:**
  - dentro del grupo, las piezas con círculo se pintan encima de las demás, de mayor a menor (la más chica arriba), y al salir vuelven a su orden, así que la vista general no cambia;
  - los círculos que se enciman, los puestos a mano y los automáticos, se separan entre sí sin que su centro salga de la caja de la pieza.
- **Medición de `nmax-horquilla`:** piezas con 24 px o más a 360, de 37 a **39 de 40**; queda la 50, con 23 px. Criterio 6 en 4,5 y **medible de 4,57 a 4,73**, sin bloqueantes.
- Cuando dos piezas quedan demasiado juntas en el desarme, el motor solo puede repartir el espacio: hace falta separarlas más en los pasos de la lámina.

### Verificación
- `regresion.py` del motor: firmas iguales en la CVT, la culata y la horquilla NMAX (referencia nueva para esta última, que no tenía).
- `regresion.py --todas`: 15 de 15 láminas sin bloqueantes (114 s).
- Validador: 18 láminas con 0 errores. Extractor y esqueleto idénticos byte a byte.

### Archivos
- **Cambiados:**
  - `M/remapear_hermana.py`, `M/mas_controles.py`, `M/esqueleto_v2.py` y `M/aplicar_hallazgos.py`;
  - `M/esquema.js`: soporte de `tr`, subir las piezas chicas dentro del grupo, separar los círculos encimados y recalcular el alto al entrar y salir del grupo;
  - `M/regresion/ref/` (firmas).
- **Skill:**
  - SKILL.md: plano desde el esqueleto, identidad, `--espejo` y lo heredado en la receta 3b, y desarme por tipo de moto. Quedó en 26.232 caracteres (antes 26.243).
  - `anexo-desarme.md`: la sección nueva por tipo de moto.

## Ronda 8 (después de la lámina 4: carburador Boxer CT100, fig. 16, compleja y sin hermana)

Sin commit. `M` = `informes_noche/piloto-esquema/motor`. No toqué el motor de dibujo (esquema.js y la biblioteca).

### 1. Extractor (`M/catalogo/extraer_catalogo.py`, `figura_generica`)
- **El título acepta un paréntesis de letras:** «FIGURA Nº 16 : CARBURADOR (TEC-S1D)».
- **«16A» y «16B» son otras figuras:** pedir la 16 ya no toma las páginas 44-46.
- Probado:
  - `--figura 16` da la página 43 sola, con 21 piezas en la columna TEC;
  - las referencias de Boxer y AKT siguen idénticas byte a byte.

### 2. Plano: la página de la tabla (`M/esqueleto_v2.py`)
- **Comprobado en los cinco formatos:** Yamaha NMAX, Yamaha Colombia, Auteco/Bajaj, AKT y Honda. En todos, el plano va en la **misma página que la tabla**; la regla «la página de antes» estaba mal.
- Ahora «plano:» usa siempre esa página.
  - Revisado a ojo: el Crypton fig. 25 y la Honda F-10 salen con su plano.
  - La AKT F-8 tenía antes la página de la F-7.
- **Borré los planos generados con la regla vieja** en `%TEMP%/tallerya-grillas` (AKT, Boxer y Honda); se vuelven a generar solos.

### 3. Un número en dos grupos (`M/mas_controles.py`, `revisar_n_dos_grupos`)
- **Error** si el mismo `n` está en dos grupos del mismo lado: tocarlo cambia de grupo y rompe el toque a 1024/1280. Lo da `--rapido`, y por lo tanto también `--previa`, antes de medir.
- **Aviso, no error,** si el catálogo trae esa pieza con cantidad ≥ 2 (las dos barras de la horquilla Honda).
- Probado: forzando la 16 en dos grupos sale el error; la horquilla Honda queda en aviso y el carburador, limpio.

### 4. Piezas internas que se ven armadas (`M/chequeo_rapido.py`, en `--previa`)
- No lo puse en el motor. Las «ocultas» de la CVT de referencia se ven bien sin la clase porque otras piezas las tapan, así que ocultarlas a la fuerza habría cambiado láminas ya aprobadas.
- **Lo mide la previa**, en el armado a 1280: el área visible de cada pieza de `ocultas` que no esté escondida.
  - **Desde 600 px² bloquea:** «pon class="esq-oculto-arm" en el <g> de su arte».
  - **Menos de 600 px²:** aviso de que asoma.
- Probado con una copia del carburador sin la clase: bloquea por el 12 (2.259 px²) y el 21 (810). La lámina real sale limpia.
- **En las láminas hechas** solo salen avisos: `crypton-freno` 11 (135), `nmax-fig24` 10 (135) y `nmax-fig11` 18 (477).

### 5. Mensaje de `encuadreArmado` (`M/validar_esquema.py`)
- Ahora dice el formato `[x, y, ancho, alto]` con ancho:alto = 900:700.
- Si parece `[x0, y0, x1, y1]` (la resta sí da 9:7), da la conversión: «como [x, y, ancho, alto] sería [100, 50, 450, 350]».

### 6. Revisora: solo ids que existen
- `guia-revision-rapida.md`: un hallazgo de dibujo o de grupos nombra solo ids que existen; hay que mirar la lista antes de sugerir uno («1-taza» cuando ya estaba `1t`).
- El resumen (`informe_revision.py`) lista los grupos como «nombre (id)», con la tornillería y sus ids. Ejemplo: «Cuerpo del carburador (1), Cuerpo del carburador (1t)».

### 7. Láminas complejas sin hermana
- **«Cómo funciona» por sistema:** `anexo-funciona.md` (nuevo) tiene 8 sistemas: carburador, inyección, freno de disco, freno de tambor, clutch, suspensión, transmisión final y culata. Para cada uno:
  - el corte o la transparencia que conviene;
  - el indicador;
  - 5-6 pasos con lo que cambia a la vista y estados sugeridos.
  - La creadora lee solo la sección de su sistema. SKILL.md lo enlaza en el paso 4.
- **Fichas por sistema** (`M/plantillas_ficha.py`): 17 plantillas que mandan sobre las de tipo cuando la descripción nombra la pieza, en inglés o en español.
  - Carburador: chiclé de alta y de baja, aguja de la cortina, cortina, flota, aguja de corte, cuba, tornillo de mezcla, tornillo de ralentí, ahogador y aislador.
  - Freno de tambor: bandas y leva.
  - Rueda y transmisión: cadena, piñón o corona, rin y llanta.
  - Las de gasolina llevan el aviso de motor frío y sin chispas.
  - En el carburador Boxer acierta en 6 de 19 fichas (aislador, cortina, aguja de la cortina, boquerel de baja, aguja de corte, flota). El catálogo Bajaj dice «Difusor» o «Tornillo Carburador» para el chiclé y los tornillos de ajuste; esos no los adivino.
- **Estimación (la meta de 10 min no se cambió):** en la lámina 4 se perdieron unos 4 min en 2 mediciones por el número en dos grupos, una imagen por el plano equivocado y el tiempo de inventar la animación y 19 fichas.
  - Con el error del número antes de medir, el plano correcto, el esqueleto de «Cómo funciona» y las fichas del sistema, estimo que una lámina compleja sin hermana baja de 23 a **unos 15-17 min**.
  - Sigue lejos de 10. El resto es dibujar 15 funciones de arte propias.
  - La palanca siguiente sería una biblioteca de carburación (cuerpo, cortina, aguja, chiclé, flota) en `piezas-comunes.js`, que es el motor y por eso no la toqué en esta ronda.

### Verificación
- `regresion.py --todas`: 19 de 19 láminas sin bloqueantes (122 s). Los avisos nuevos son los de piezas que asoman.
- El validador da 0 errores en las 19 láminas. Extractor y esqueleto idénticos.
- Firmas guardadas para la lámina nueva del carburador.

### Archivos
- **Cambiados:**
  - `M/catalogo/extraer_catalogo.py` y `M/esqueleto_v2.py`;
  - `M/mas_controles.py` y `M/validar_esquema.py`;
  - `M/chequeo_rapido.py`, `M/informe_revision.py` y `M/plantillas_ficha.py`;
  - `guia-revision-rapida.md`;
  - `M/regresion/ref/`.
- **Skill:**
  - `anexo-funciona.md` (nuevo);
  - SKILL.md: enlace al anexo y plantillas por sistema. Quedó en 26.211 caracteres (antes 26.232).
- **Nota:** el árbol de trabajo usa CRLF (`core.autocrlf=true`). Los tamaños de SKILL.md están medidos con LF, como en las rondas anteriores.

## Ronda 9 (después de la lámina 5: suspensión trasera CB 125F, fig. F-22-1, sin hermana)

Sin commit. `M` = `informes_noche/piloto-esquema/motor`.

### 1. Extractor Honda (`M/catalogo/extraer_catalogo.py`)
- **Tres arreglos:**
  - acepta códigos sin sufijo («92812-20000», «94101-08000») y sufijos de 5 letras («52200-KPN-A00ZA»), con `COD_HONDA` = `\d{5}-[A-Z0-9]{3,5}(-[A-Z0-9]{2,5})?`;
  - lee la descripción que sigue en la misma línea del código (ref. 7, la tijera);
  - quita el color de la segunda línea («*NH303M* MAT AXIS GRAY METALLIC»).
- **F-22-1:** de 9 a **14 de 14 refs**, iguales a las que la creadora puso a mano.
- **F10, E-1-2, E6, E6-1 y F8:** idénticas a la salida anterior; solo cambia el campo `moto`, que sale del nombre del archivo.
- La F-22-1 entró a la regresión del extractor (`ext-honda-f22`).

### 2. `M/buscar_manual.py` sin lista fija
- **Carpeta de la moto:** `carpeta(catalogo)` busca en `manual_despiece/` la carpeta que tiene el PDF fuente del catálogo, o un catálogo con el código de la versión en el nombre. `MANUALES` ya no existe, y `informe_revision.py` usa la misma función.
- **Tipo de manual:** `tipo(pdf)` dice «servicio» (taller) o «propietario», por el nombre o, si no, por las 3 primeras páginas.
  - `manual-cb125f.pdf` sale como propietario.
  - Con el índice de un manual del propietario avisa «sin torques de chasis ni motor».
  - El resumen de la revisora también dice el tipo de cada manual.
- Probado en las 5 motos de la noche: todas encuentran su carpeta. Solo el Crypton tiene manual de servicio.

### 3. `anexo-funciona.md`: los sistemas que faltaban
- **Suspensión trasera (tijera y amortiguadores):** la tijera gira sobre el pivote, el amortiguador se acorta, la cadena se tensa, el rebote y los bujes gastados.
- **También, en corto:** dirección, arranque eléctrico, encendido (CDI o ECU, bobina y bujía), escape, y tanque y bomba de combustible.
- «Suspensión» quedó como «Suspensión delantera (horquilla)». Ahora son 14 sistemas.

### 4. `--previa`: roce de las marcas de grupo (`M/chequeo_rapido.py`)
- Mide lo mismo que la medición final, en cada lado y en cada ancho (360, 390 y 1280):
  - el centro de la píldora que no recibe su toque;
  - la vecina a ±9 px;
  - las píldoras encimadas.
- Bloquea con «sepáralas (v2.grupos[].marca)».
- Probado:
  - con las 4 marcas en el mismo punto, bloquea a 360;
  - con marcas solo cercanas, el motor ya las separa y no bloquea;
  - las 20 láminas hechas salen sin roces.

### 5. Motor: «Seguir con» solo después de elegir algo (`M/esquema.js`)
- «Seguir con: …» venía de la última pieza guardada en una visita anterior, y salía apenas cargaba la página. Ahora solo aparece si en esta visita ya se eligió una pieza o se entró a un grupo.
- Probado en el navegador, con una pieza guardada de antes: al cargar no sale; después de elegir una pieza y volver, sí («Seguir con: Guardacadena»).

### Verificación
- `regresion.py --todas`: 17 de 17 láminas en el navegador sin bloqueantes (360 s).
- Validador: 20 láminas con 0 errores.
- Firmas iguales en la CVT, la culata y la suspensión trasera (referencia nueva para esta última; 1 capa con ±1 px de redondeo).
- Extractor y esqueleto idénticos, con la F-22-1 agregada.

### Archivos
- **Cambiados:**
  - `M/catalogo/extraer_catalogo.py`, `M/buscar_manual.py` e `M/informe_revision.py`;
  - `M/chequeo_rapido.py` y `M/esquema.js`;
  - `M/regresion.py` y `M/regresion/ref/`.
- **Skill:** `anexo-funciona.md`. SKILL.md no cambió en esta ronda: sigue en 26.211 caracteres.

---

## Resumen de la noche: 5 láminas

| # | lámina | hermana | tiempo con revisión | mediciones | tokens creación / revisora | medible | revisora (mec. / UX, antes de corregir) | graves |
|---|---|---|---|---|---|---|---|---|
| 1 | Crypton FI 115 · freno delantero (fig. 25) | `nmax-fig22` (otra numeración) | 13 min | 1 | ~175 k / 104 k | 4,80 | 3,9 / 3,6 | 3 (de 7) |
| 2 | AKT NKD 125 · rueda trasera y transmisión (F-8) | no | 14 min | 2 | ~98 k / 91 k | 4,88 | 4,0 / 4,0 | 4 (de 13) |
| 3 | NMAX · horquilla y dirección (fig. 18) | `cb125f-horquilla` (otra marca) | 13 min de fases (16 de reloj) | 1 | ~98 k / 108 k | 4,57 → 4,73* | 3,5 / 3,9 | 9 (de 15) |
| 4 | Boxer CT100 · carburador (fig. 16) | no (compleja) | 23 min | 4 | ~128 k / 91 k | 4,82 | 4,0 / 4,3 | 5 (de 15) |
| 5 | CB 125F · suspensión trasera (F-22-1) | no | 13 min | 2 | ~140 k / 96 k | 4,88 | 4,0 / 4,3 | 3 (de 15) |

\* 4,73: la medición de la lámina 3 repetida con el motor de la ronda 7.

**Lectura:**
- La meta de 10 min no se alcanzó en ninguna. Las que tienen hermana o un sistema conocido quedaron en 13-14 min; la compleja sin hermana, en 23.
- Las notas de la revisora quedaron entre 3,5 y 4,3 antes de corregir. No hubo segunda revisión, así que la nota después de corregir no está medida.
- Los graves bajaron de «restos de la hermana» (láminas 1 y 3) a errores de contenido sin manual de servicio (láminas 4 y 5).
- Las mediciones de más vinieron de defectos que ahora atrapan `--rapido` y `--previa`: `torn` mal formado, un número en dos grupos y marcas que se rozan.

**Rondas de la skill (una línea cada una):**
- **Ronda 5:** extractor Yamaha bilingüe; `remapear_hermana.py` (una sola vez, cadenas incluidas); validador sin falsos positivos y con rastros en la cinta y el arte; `buscar_manual.py` para no volcar el manual.
- **Ronda 6:** validador que no se corta y `torn` con formato; esqueleto con kits, cauchos y grupos de rueda; informe con huella que se rehace solo; tope de 250 en los hallazgos; biblioteca de ruedas (rin, llanta, piñón, cadena, eje, tensor).
- **Ronda 7:** remapeo con identidad, espejo y lista de lo heredado; rastros en `visor` y `pie`; plano automático; desarme por tipo de moto con control del gato central; hallazgos en cadena; motor con «Desarmar» visible y toque mínimo sin `toqueExtra`.
- **Ronda 8:** extractor con títulos entre paréntesis; plano desde la página de la tabla; error de un número en dos grupos; piezas internas visibles en la previa; mensaje de `encuadreArmado`; revisora con ids que existen; `anexo-funciona.md` y fichas por sistema.
- **Ronda 9:** extractor Honda con 14 de 14 refs; `buscar_manual.py` sin lista fija y con el tipo de manual; 6 sistemas más en `anexo-funciona.md`; roce de las marcas en la previa; «Seguir con» solo después de elegir algo.
- **Ronda 10** (tras NKD freno y Apache clutch, la primera TVS): extractor TVS y error claro (sin escribir) si no reconoce la tabla; `remapear_hermana.py` con % de cobertura, cifras heredadas sin respaldo (dientes, mm, balineras, «cuatro resortes») y `--arte-extra`; plantillas aro-retén, bomba de freno, manigueta, interruptor y cable del CBS; el control del líquido ya no pide 2 años a manigueta, tornillos ni piezas que solo están «en el kit»; pregunta del camino de la fuerza en la guía de la revisora y en el autocontrol. `regresion.py --todas`: 22 láminas con 0 errores y sin bloqueantes.
