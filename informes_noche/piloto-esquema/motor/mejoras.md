# Meta del usuario: 15 min de reloj por lámina, sin paralelo (16-nov-2026)
Va del catálogo a «lista para revisión», con la verificación incluida. Las revisiones van aparte, con meta de una ronda. Prioridad: economía de tokens y coherencia de estilo.
- **`metricas.json`:** `creacion_meta_min: 15`, `sin_paralelo: true` y `meta_fases`. Las metas por fase son catálogo+esqueleto 1, dibujo 7, contenido 5, 3D 1 y verificación 1 (validación + mediciones).
  - `metricas.py fin` compara cada fase con su meta.
  - El `informe` dice «CREACIÓN: n min · meta 15 → sobró/faltó» y da el real contra la meta por fase.
  - Fig. 26 como referencia: 22 min, faltaron 7 (dibujo +6, contenido +10, verificación +4).
- **Sin subagentes en paralelo.** El de borradores se quitó; el brief que queda es solo para extraer un catálogo que falte, en serie.
- **`esqueleto_v2.py` dibuja la biblioteca:** tornillos, O-rings, resortes, bujes y cauchos salen dibujados con medidas por omisión. Las anclas van en una franja por grupo.
  - En la fig. 8 son 12 de 37 piezas ya dibujadas; quedan 26 de arte propio.
  - Ese arte propio es el cuello de botella para llegar a dibujo 7.
- **Plan por minuto en `SKILL.md`:**
  - 0-1: esqueleto y plantillas;
  - 1-8: arte propio;
  - 8-13: fichas propias, «Cómo funciona», cadenas y textos;
  - 13-14: 3D;
  - 14-15: `autocontrol`.
- **Para llegar a 15 sin bajar la calidad falta todavía** una biblioteca de formas propias reutilizables entre láminas: manguera, abrazadera, caja con tapa, ducto, placa con agujeros.
  - Hoy se copian por rangos de otras láminas (`extruir` y `manguera()` de la fig. 26).
  - Llevarlas a `piezas-comunes.js` como tipos nuevos (`manguera`, `abrazadera`, `caja`) bajaría el dibujo de forma estable. Queda propuesto: es un cambio del motor y se hace con las firmas.

# Skill más rápida (E), 16-nov-2026, después de adoptar el v2

Pedido del usuario: `hacer-lamina` más rápida, sin gastar más tokens y sin bajar las notas. Base: fig. 26, 37 min de reloj (contenido 15, dibujo 13 solapados, correcciones 6, validación 4). Se mide de verdad con la fig. 8 en una sesión limpia; aquí van las ganancias de cada pieza medidas por separado.

| Pieza | Antes | Después (medido) | Ataca |
|---|---|---|---|
| `esqueleto_v2.py`: catálogo → campos de página, fichas con `cat`/`codigo`/certeza, piezas con `comun_sugerido`, `v2.grupos` por conjunto «ASSY» con `torn`, un paso por grupo y «Cuándo» desde intervalos | subagente sonnet 3-5 min y ~100 mil tokens suyos; después, armar los grupos v2 a mano | **0,7 s**, 0 tokens. Fig. 8: 37 refs → 9 grupos y 12 piezas de biblioteca propuestos | contenido |
| `plantillas_ficha.py`: borrador v2 por tipo de pieza (17 tipos) con la regla de seguridad puesta; solo campos vacíos | cada ficha de tornillería, sello o manguera escrita desde cero | **< 1 s** para todas. En la fig. 8, 21 de 37 fichas son tornillería, sellos, grapas o mangueras: quedan casi listas (dónde va y enlaces) | contenido |
| Subagente de borradores en paralelo (`anexo-esqueleto.md`): solo nombres de TallerYa, orden real, torques y contradicciones, en un JSON de ≤ 60 líneas | el subagente armaba el esqueleto entero y traía texto que no servía (22 de 49 fichas, nada en `sirve`) | corre mientras se dibuja; no escribe archivos | contenido, correcciones |
| `autocontrol.py`: validador + `mas_controles` + `medir_lamina` + métricas, salida de ~15 líneas, código 1 si falta algo | 3-4 comandos con salidas de 40-60 líneas | `--rapido` **1,8 s**; completo ≈ 1,5 min | validación, mediciones (y tokens por turno) |
| `revisar_estructura_v2` en el validador: grupos, `torn`, pasos que no mueven el grupo, piezas sin grupo, `certezaDe`, `con3d` | estos errores salían en el navegador o en la revisión UX | en el validador, en segundos | correcciones |
| `metricas.py fin` avisa si la fase pasó del 125 % del promedio | se veía solo en el informe final | aviso en el momento: se anota por qué y se sigue | tope de tiempo |
| La skill dice qué rangos leer (arte: fig26-arte 12-34 y 105-145, fig12-arte 96-158; JSON de ejemplo con Python) y ninguna captura hasta la entrega | lecturas de exploración y capturas intermedias | 0 lecturas exploratorias y 1 captura | tokens, dibujo |

Hoy ya se midió una de estas ideas: en la adopción del v2, dos subagentes sonnet en paralelo redactaron los textos v2 de las fig. 22 y 12 (53 fichas, 29 pasos) en **3 min de reloj**, mientras yo fundía el motor. Para la fig. 26 eso me había tomado 17 min (49 fichas). Validador y revisión: 2 errores de estilo y 2 avisos de seguridad, corregidos en 2 min.
Estimado para la fig. 8 (se confirma al hacerla): contenido de 15 a ~8 min, validación y mediciones de 5 a ~2, correcciones de 6 a ~3. **Meta: < 37 min de reloj**, con mecánica ≥ 4,8 y UX ≥ la base v2.

# Mejoras del motor para producir láminas más rápido y barato (A-D), 16-nov-2026

Todo dentro de `motor/`, sin commit. Reloj: de 02:26 a 02:41 (~15 min de pared). Hubo ~5 min de esperas porque el clasificador de permisos no respondía.

| Parte | Tiempo | Qué quedó |
|---|---|---|
| A. Catálogo | ~1 min (subagente sonnet en paralelo, 80 mil tokens suyos y ~1 mil míos) | `catalogo/extraer_catalogo.py` y `catalogo/nmax-bbe4.json`: 38 figuras y 835 filas (ref, descripción, cantidad, código y nota). Se extrae solo el texto con pymupdf; el PDF no se tocó. |
| B. Biblioteca y migración | ~8 min | `piezas-comunes.js` con 11 tipos que dan arte 2D y forma3d desde las mismas medidas. La tornillería de la CVT (18 piezas) y del freno (15 y 12) pasó a una línea por pieza. |
| C. Validador | ~4 min | `mas_controles.py`, que llama `validar_esquema.py`. Corre en 0,4 s por lámina. |
| D. 3D a escala | ~3 min | Perfiles compartidos `@nombre`, `prisma` con agujeros reales, `esfera` y `resorte` en el visor, `regla-3d.md` y el título del archivo único. |

## A. Catálogo, una vez por moto
- Uso: `python catalogo/extraer_catalogo.py <pdf> catalogo/<moto>.json`, en un par de segundos.
- La lámina dice `"catalogo":"nmax-bbe4"` y `"figura":12`. El validador saca de ahí los números de la figura; `refsFigura` queda solo como respaldo.

## B. Biblioteca de piezas comunes
- Tipos: tornillo (hexagonal o Allen, con o sin brida), tuerca, arandela (acero o plástico), anillo de seguro, retén, O-ring, rodamiento (bolas o agujas), buje (liso o estriado), resorte, pasador (de punta o lateral) y pieza de revolución por perfil.
- Cada lámina declara una vez `"comun":{"atras":[dx,dy],"colores":{...},"sombra":"url(#…)"}`. Después, una línea por pieza: `{"id":"28","comun":"tuerca","p":{"x":278,"y":414.1,"r":14}}`. También acepta `p.copias` (varias iguales), `marco` (dibujar en un plano que exporta el arte, como `LOC` del cáliper) y `sin3d`.
- **Las piezas comunes tienen 3D gratis:** el motor arma su forma3d al cargar.
- Se quitaron del arte de cada lámina las funciones migradas: 12 de la CVT y 3 del freno.
- **Firma** (caja de cada pieza y cantidad de elementos): **idéntica** en las 33 piezas de la CVT y las 18 del freno. Diferencias pequeñas, aceptadas por consistencia:
  1. Retenes 14 y 15: las dos copias usan el mismo gris (antes #202020 y #262626). Además, el círculo del labio de la primera queda debajo del segundo retén, en vez de encima.
  2. Pasador del freno (12): se perdió la ranura fina en el vástago, que solo se veía desarmado.
  3. Rodamiento de la tapa (30): el dibujo 2D sigue sin bolas, pero su 3D sí las muestra.
- **No migrado:** los tornillos del disco (2 del freno). Están dibujados en el plano inclinado del disco, con elipses que no son una transformación limpia; pasarlos cambiaría el dibujo a simple vista.
- El freno ahora carga el visor 3D, así que sus fichas 12 y 15 traen modelo. El archivo único del freno pasa de 124 a 819 KB porque trae three.js.

## C. Validador más listo (`mas_controles.py`, 0,4 s)
1. **Un solo nombre por pieza:** en pasos, cadenas, «Cuándo» y fichas, la palabra junto a «(n)» no puede ser un sinónimo ni el nombre de otra familia (retén/retenedor/sello, empaque/junta, rodamiento/balinera, buje/casquillo...). Probado con un texto de ejemplo: «retenes (5)» y «balinera (8)» salen como error.
2. **Referencias:** conecta, efectos, cadenas, chips y pasos apuntan a piezas que existen y están en el catálogo.
3. **Catálogo:** la descripción en inglés y la cantidad de `cat` coinciden con el catálogo. Encontró un error real: freno 9 decía «2 pastillas», pero el catálogo trae 1 juego; ahora dice «1 juego (2 pastillas)». A cuatro fichas del freno les faltaba la cantidad.
4. **Intervalos:** las filas de «Cuándo» llevan `"tarea"` y se comparan km y años con `garaje/intervalos/<intervalos>.json`. La lámina dice `"intervalos":"yamaha_nmax_155"`.
5. **forma3d y piezas comunes:** tipos conocidos, medidas necesarias, perfiles `@` que existan, marcos exportados y pieza común conocida.

## D. 3D a escala
- **Perfil una sola vez:** `perfiles` en el JSON y `"perfil":"@polea13"` en forma3d. Para piezas nuevas de revolución, la pieza común `revolucion` con ese mismo `@perfil` dibuja también el arte 2D (discos apilados en el estilo de la lámina). Las poleas de la CVT conservan su arte propio, para no cambiar el dibujo aprobado.
- **Cortes reales:** `prisma` con `huecos` (círculos, polígonos y óvalos, con `repetir`). Las 5 ventanas de la campana ya son agujeros de verdad, sin subir el costo: 2 líneas de JSON. Las ranuras helicoidales del cuello de la 13 siguen como calcomanía: cortarlas en una superficie curva exigiría CSG.
- **Regla escrita:** `regla-3d.md`.
- **Título del archivo único:** sale del JSON («Piloto Transmisión CVT: variador, correa y clutch»), y la descripción también. `armar_un_archivo.py` ahora reconoce cualquier `*-arte.js` y mete la biblioteca y el visor.

## Comprobado
Validador OK en fig12 y fig22. Firma idéntica. Montaje 3D de 12 piezas (comunes y propias), sin errores. Sin errores de consola en cvt.html, freno.html y los dos archivos únicos.

## Agregado después (02:43-02:48, ~6 min)

### C+. Preguntas [S] de `autocontrol-mecanico.md` en el validador (`mas_controles.py`; 0,6-0,8 s por lámina)
- **1** (nombres y cantidades contra el catálogo), **3** (un solo nombre) y **15** (km y años contra intervalos) ya estaban.
- **2:** una certeza «aprox.» que habla del catálogo, la cantidad o el lado da error: va como «Seguro».
- **4:** la palabra pegada a «(N)» tiene que ser del nombre de N. Si no, sale un aviso de «¿nombre viejo?». En la CVT encontró «placa (3)» en la ficha 2, cuando la 3 es la rampa. Va como aviso porque puede haber frases legítimas, como «caucho (9)».
- **9 (parcial):** avisa si una pieza no se mueve en ningún paso. Con el campo nuevo `"sujeta":{"28":["27","6","33"],...}`, comprueba que lo que sujeta salga antes o en el mismo paso; ya está puesto en las dos láminas.
- **12:** una cifra con unidad (km, rpm, %, °C...) sin «aprox.» ni fuente da aviso. Cuenta como fuente si el número aparece en `fuentes.seguro`, en las certezas «ok» o en «Cuándo». En el freno avisa «100 a 200 km» (ficha 9).
- **16 (parcial):** cada fila de «Cuándo» tiene que decir «Seguro» o «Aproximado», y cada ficha tiene que traer su certeza.
- **18:** torques y medidas (N·m, kgf, mm) sin fuente ni «aprox.» o «sin dato» dan **error**.
- **Sistemas:** la versión de la moto (BBE4) contra el catálogo; el lado (RIGHT/LEFT) contra el texto de la ficha; ABS o CBS en el título solo si la figura del catálogo los trae.
- Probado con casos malos: certeza aprox. del catálogo, 60 N·m sin fuente, fila sin certeza, versión distinta y orden de desarme invertido. Todos salen.

### Métricas (`metricas.py` y `metricas.json`)
- Uso: `python metricas.py inicio|fin <lamina> <fase>`, `dato <lamina> <clave> '<json>'` e `informe <lamina>`. Las fases son catalogo, dibujo2d, contenido, 3d, validacion, mediciones, revision_mecanica, revision_ux y correcciones.
- El informe compara cada fase con la línea base y con el promedio de las demás láminas. Marca «tardó más de lo esperado» si pasa del 125 %, y marca las notas que quedan por debajo de la base. **Terminado** = todas las notas ≥ la base; si no, hay que llenar «explicacion».
- Línea base de la CVT, reconstruida con cambios.md, el relevo y las horas de los archivos; las horas están marcadas «estimado».
  - Unos 120 minutos: dibujo 2D 40, contenido 20, 3D 16, revisiones 17 y correcciones 8.
  - Mecánica 4,8 por criterio y UX 4,5, con 8 de sus 12 criterios.
  - 100 % «Seguro» en nombres y cantidades; 5 pendientes; 3 rondas de revisión y 2 de corrección (estimado).
  - `uso_plan` lo llena Auxiliares.

### D+. Pendientes de UX de la CVT, arreglados en el motor (valen para todas las láminas)
- **Alto del dibujo a 1280×800:** pasa de 453 a **461 px**. `medirAlto` reserva lo que mide de verdad la fila de controles, en vez de 76 px fijos, y los botones siguen dentro de la pantalla (borde inferior en 796 de 800).
- **«Cómo funciona» en el celular:** el texto del paso queda pegado bajo el dibujo, a 5 px (antes estaba después de los botones); los botones van debajo.
- **Números a menos de 24 px a 360:** en el despiece, el botón + se resalta con tres latidos, sin animación si se pide reducir movimiento, y su etiqueta dice «hay números muy juntos». Es `sugerirZoom` en esquema.js. En la CVT se activa y en el freno no (sus números están más separados).
- **3D con cortes reales:** ya estaba en la parte D (`prisma` con `huecos`).
- Comprobado: sin errores de consola, sin scroll horizontal a 360 y validador OK en las dos láminas.

## E. Skill «hacer-lamina» (02:49-02:53, ~5 min de pared, más ~80 s de mediciones)
- `.claude/skills/hacer-lamina/SKILL.md` lleva a una sesión limpia por los pasos en orden, cada fase con su `metricas.py inicio/fin`: catálogo, esqueleto del JSON (subagente sonnet), dibujo con la biblioteca, contenido, 3D, validar, autocontrol, medir y entregar. Incluye las reglas fijas, qué leer y qué no, y la definición de terminado (notas ≥ la base, o explicación).
- Anexos:
  - `anexo-autocontrol.md`: las preguntas mecánicas no automatizadas y la UX a ojo, con el orden de `--ojo`;
  - `anexo-formato.md`: campos nuevos, tabla de la biblioteca y tipos de forma3d;
  - `anexo-esqueleto.md`: el brief listo para el subagente.
- Los comandos van con la ruta desde la raíz: validar_esquema.py, medir_lamina.py y metricas.py.
- Comprobado: `medir_lamina.py` en la CVT da 4,62 con el ojo en 4,5, sin bloqueantes y con el dibujo de 461 px a 1280. El freno, sin bloqueantes. El validador da OK en las dos.
- Motor: los chips de las cadenas pasan a 44 px de alto en todos los anchos (antes, 36 desde 701 px).
- Contenido: «placa (3)» pasa a «rampa (3)» (ficha 2 de la CVT) y el rodaje de pastillas queda como «aprox. … práctica de taller» (freno, ficha 9). El validador ya no parte la frase en «aprox.» e ignora adjetivos como «trasero» al buscar nombres viejos.
