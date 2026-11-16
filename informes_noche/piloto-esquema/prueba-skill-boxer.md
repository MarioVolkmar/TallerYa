# Prueba de la skill `hacer-lamina`: clutch de la Bajaj Boxer CT100 (fig. 14)

Sesión limpia, sin historial, siguiendo `SKILL.md` y sus anexos. La lámina queda en `informes_noche/piloto-esquema/motor/boxer-embrague.html` (datos en `motor/datos/boxer-embrague.json` y `boxer-embrague-arte.js`, catálogo en `motor/catalogo/boxer-ct100.json`).
Figura: **fig. 14 «Clutch»** del catálogo Auteco (pp. 39-40), columna **TEC** (CT 100 desde marzo de 2006). Sí era aprovechable: 15 refs en la TEC. Las refs 16-23 (piezas sueltas de la corona) son de otras versiones y la 24 es el clutch completo, así que no entran.

## Tiempos por fase (reloj, `metricas.py`)
| fase | esta lámina | meta del plan de 15 min | referencia fig. 26 |
|---|---|---|---|
| catalogo | 5 min | 1 | 0 |
| dibujo2d | 5 min | 7 | 13 |
| contenido (+3D) | 1 min de reloj anotado (el texto se escribió dentro de `dibujo2d`, ver abajo) | 6 | 15 + 2 |
| validacion | 1 min | 1 | 4 |
| mediciones | 8 min (2 mediciones completas de ~2 min + 1 bloqueante corregido) | 1 | 1 |
| **total creación** | **20 min** (sin revisiones) | 15 | 37 |

- La división dibujo/contenido no es real: escribí `contenido_boxer.py` (fichas, «Cómo funciona», cadenas, «Cuándo») antes de cerrar `dibujo2d`, porque el validador no deja hacer la `--previa` con `textos.intro*` vacíos. Lo justo es leer dibujo + contenido juntos: unos 6 min.
- El catálogo se pasó de la meta (5 contra 1) porque el extractor no sirve para Bajaj (ver abajo).
- Las mediciones se pasaron (8 contra 1): la medición completa tarda 1,5-2 min, más de los 120 s que aguanta el Bash en primer plano, así que hay que correrla en segundo plano. Además la primera dio un bloqueante (en «Cómo funciona», «Corona» montada sobre «Luz entre discos»).
- No hubo revisión mecánica ni de UX (las hacen las revisoras), así que faltan `revision_*` y `correcciones`.

## Dónde la skill no sirvió, quedó ambigua o daba por hecha la NMAX
1. **Paso 1 «Catálogo» y `anexo-esqueleto.md`:** `extraer_catalogo.py` es solo para Yamaha (busca la cabecera `PART NO.` y `FIG. N`). Con el catálogo Auteco/Bajaj saca «0 figuras, 0 filas». La skill no dice qué hacer en ese caso: el anexo manda un subagente que correría el mismo script y fallaría igual.
2. **El catálogo Bajaj tiene 5 columnas de versión** (TEC, S1D, K-TEC, UG, 4T), con un código distinto por versión en filas de continuación. La skill no menciona variantes por columna. Además, el texto extraído sale con las columnas desordenadas: tuve que mirar la tabla en imagen para saber que la primera columna es TEC.
3. **`esqueleto_v2.py` depende de descripciones en inglés de Yamaha** (`ASSY`, hijas con «.», `BOLT|NUT|WASHER…` en `TORN`/`COMUN`, nombres en `TRAD`). Con descripciones en español no habría reconocido ni la tornillería ni la biblioteca. Lo resolví con una `descripcion_en` hecha a mano para el script.
4. **El validador compara `fichas[n].cat` con `descripcion` del catálogo:** tuve que cambiar el catálogo para que `descripcion` sea el texto en español del PDF y la equivalencia en inglés quede en `descripcion_en`. Ni la skill ni el anexo explican de dónde sale el texto de `cat`.
5. **`plantillas_ficha.py` no detectó ningún tipo** (todas salieron como «conjunto» con textos de relleno: «El conjunto de los resortes y su placa» en el tornillo 10). La detección también depende del inglés. Terminé escribiendo las 15 fichas a mano.
6. **«Para ver la lámina: `despiece_local/grillas/<Marca-Moto>-figNN.png`»:** no hay grillas de la Boxer. Rendericé la página con pymupdf (`get_pixmap` con `clip`) a ≤ 900 px. La skill no da esa salida, y la primera captura me la gasté en la tabla porque no sabía en qué lado de la página va el plano.
7. **Formato de `forma3d` en `anexo-formato.md`:** la tabla escribe `torno {perfil}`, `cilindro {r, z, pos}`, lo que se lee como `{"torno":{…}}`. El motor espera `{"tipo":"torno","perfil":…}` y el validador lo marca como «tipo None». Lo saqué del ejemplo `nmax-fig12` y de la cabecera de `esquema3d.js`.
8. **Intervalos:** `garaje/intervalos/auteco_bajaj_boxer_ct_100.json` no tiene tareas de aceite ni de clutch. La skill supone que la tarea existe (`--tareas`, `cuando[i].tarea`) y no dice qué hacer si falta. Las filas de «Cuándo» quedaron sin `tarea` y salen del manual del propietario. Ese manual es además el indio (BS VI), no el colombiano 2017.
9. **Supuestos de scooter/NMAX en la guía de vistas y ejemplos:** «frenos y CVT, de lado; motores, de lado o de tres cuartos». Para un clutch de discos no hay ejemplo del mismo sistema. El más parecido es la CVT, que es un clutch centrífugo seco, con otra mecánica. Faltan criterios para clutch/caja: sentido de la explosión según el plano y la palanca con su juego libre como indicador.
10. **`cvt.html` como plantilla:** la skill dice «dos rutas cambiadas», pero `<title>` y `meta description` dicen «CVT NMAX». También los cambié (no era evidente si estaba permitido).
11. **Fases y cronómetro:** el plan pone el contenido después del dibujo, pero la `--previa` exige textos completos. En la práctica hay que escribir el contenido antes de poder mirar el dibujo.
12. **`comun.atras`:** solo se da `[0.5,-0.32]` (la profundidad hacia arriba a la derecha). Para que el despiece bajara a la derecha como en el plano Bajaj usé `[-0.5,-0.32]`. Funciona, pero la skill no dice que se pueda cambiar.

## Lo que improvisé
- Extraje a mano las 15 filas de la fig. 14 a `motor/catalogo/boxer-ct100.json` (columna TEC, nota de las refs que no aplican, `descripcion_en` para el esqueleto).
- Rendericé el plano y la tabla con pymupdf (2 imágenes).
- Rehíce los grupos a mano, por criterio de desarme: mando (leva, impulsor, soporte, balinera), resortes con sus tornillos, manzana y discos con la tuerca del cigüeñal, y corona con buje y arandelas. El esqueleto proponía «Holder, Bearing», «Placa» y «Varilla», mezclados.
- Cambié los tipos de biblioteca que el esqueleto adivinó mal: la placa de los resortes como `resorte` y los discos como `placa` rectangular. Los discos y las placas quedaron como `placa` con contorno circular hecho en el script.
- El funcionamiento del mando (los resortes jalan la placa de presión a través de los tornillos, y la leva empuja la placa de los resortes) lo deduje del plano. Va como «Aproximado».

## Cambios que propongo (sin aplicar)
1. **`SKILL.md`, paso 1:** añadir «Si `extraer_catalogo.py` da 0 figuras (catálogo que no es Yamaha), extrae a mano solo la figura N con pymupdf `get_text('words')`, escoge la columna de la versión (año/modelo) y guarda `descripcion` = texto del PDF y `descripcion_en` = equivalente Yamaha (`… ASSY`, `BOLT`, `NUT`, `WASHER`, `SPRING`, `BEARING`, `PLATE`) para el esqueleto». Mejor aún: que `esqueleto_v2.py` y `plantillas_ficha.py` lean `descripcion_en` si existe, y una tabla mínima en español (tornillo, tuerca, arandela, resorte, balinera/rodamiento, buje, retén, empaque).
2. **`anexo-esqueleto.md`:** para catálogos que no son Yamaha, que el subagente no corra el script sino la extracción por palabras de una sola figura, con la columna de versión como parámetro.
3. **`SKILL.md`, «Para ver la lámina»:** si no hay grilla, `pymupdf … page.get_pixmap(clip=Rect(…), matrix=Matrix(2.4,2.4))` solo del lado del plano (en Auteco el plano va a la izquierda y la tabla a la derecha, y cada figura ocupa dos páginas).
4. **`anexo-formato.md`, forma3d:** escribir los ejemplos en el formato real: `{"tipo":"torno","perfil":"@x","color":"acero"}`, `{"tipo":"cilindro","r":9,"z":[0,6],"pos":[32,0],"repetir":6}`, `{"tipo":"caja","tam":[x,y,z],"pos":[x,y,z]}`.
5. **`SKILL.md`, plan de 15 min:** decir que «Cómo funciona» y los `textos.intro*` deben existir antes de `--previa`, o que el validador acepte `--previa` con esos campos vacíos (que pase a aviso).
6. **`SKILL.md`, «Cuándo»:** «Si `garaje/intervalos/<moto>.json` no tiene la tarea, la fila va sin `tarea`, con la fuente del manual del propietario, y se anota en `pendientes`. Si el manual es de otra versión o de otro país, dilo en la fuente».
7. **`SKILL.md`, paso 3 (vista):** una línea para clutch de discos y caja: «Vista caballera con el eje hacia el lector (como la CVT). `comun.atras` puede invertirse (`[-0.5,-0.32]`) para que el despiece siga el sentido del plano». Y en «Cómo funciona», un indicador típico por sistema: clutch → % de palanca y luz entre discos.
8. **`SKILL.md`, reglas fijas:** «La página es una copia de `cvt.html`: cambia las dos rutas, el `<title>` y la `meta description`».
9. **Ejemplo por sistema:** después de revisar esta lámina, citarla como ejemplo de «clutch de discos / transmisión de moto de cambios».

## Estado
- `autocontrol.py`: validador **OK** (1 aviso solo de la vista transparente) y medición **sin bloqueantes**, nota medible de 4,72. Notas a ojo: 4, 4, 4, 4, 5 y 4. El promedio UX es 4,4, por debajo de la base de 4,5 de la CVT; está explicado en `metricas.py`.
- 15 piezas en 4 grupos, 6 pasos de desarme, 15 fichas propias, «Cómo funciona» de 6 pasos (palanca en %, luz entre discos, corona y caja girando, discos que patinan), 3 cadenas, 4 filas de «Cuándo» y 3 piezas con 3D (corona, manzana y leva).
- `pct_seguro` 100 % (números, nombres y cantidades del catálogo). `pct_certeza_total` solo 20 %: sin manual de servicio, casi todo lo funcional va como «Aproximado».
- Archivo único: `motor/prueba-boxer-embrague.html`. Pendientes (4) en el JSON: torques, número de discos del kit, intervalo de aceite colombiano y tareas que faltan en los intervalos.
- **Veredicto de la prueba:** la skill funciona sola en lo que es motor (dibujo, validador, medición y estilo v2), y el resultado salió en 20 min. Pero las herramientas del paso 1-2 (`extraer_catalogo.py`, `esqueleto_v2.py`, `plantillas_ficha.py`) asumen un catálogo Yamaha en inglés: con otra marca, la mitad del ahorro de tiempo se pierde y hay que improvisar.

## Cambios aplicados a la skill (16-nov-2026, pedido de Auxiliares con aprobación del usuario)
Criterio: lo que se podía resolver en código fue a los scripts; `SKILL.md` creció una línea (159 → 160).

**Scripts** (en `motor/`):
- `catalogo/extraer_catalogo.py`: ruta nueva `--figura N --columna <versión> [--moto]` para catálogos que no son Yamaha (cabecera PARTE/CÓDIGO + DESCRIPCIÓN + columnas de versión o cantidad). Extrae solo esa figura por palabras, une las páginas (1/2, 2/2), hereda ref y descripción en las filas de continuación, deja en `fuera` las refs que no aplican a la columna y en `conjuntos` los «… Completo». Agrega la figura al JSON si ya existe y conserva `descripcion_en` y otros campos hechos a mano. Sin `--columna`, si hay varias versiones, las lista y no escribe nada. Sin `--figura`, hace lo de antes (Yamaha).
- `catalogo/claves_es.py` (nuevo): convierte la descripción en una clave en inglés de estilo Yamaha. Usa `descripcion_en` si existe. Si no, clasifica el español por la **primera palabra** (tornillo, tuerca, arandela, resorte, balinera/rodamiento, buje, retén, empaque, placa/disco, pasador, seguro, abrazadera, manguera, tapa…), suma los lugares que nombre (cigüeñal, culata, cilindro…) y toma «Kit/Juego/Conjunto/Completo» como ASSY. Las descripciones Yamaha pasan sin cambio, y las palabras que Yamaha también usa en inglés (CIRCLIP, O-RING, PIN, SENSOR…) no cuentan como español.
- `esqueleto_v2.py`: clasifica con `claves_es`. Con descripción en español, el nombre sugerido sale de ella («Tornillo resorte clutch») y `cat` usa el texto del catálogo.
- `plantillas_ficha.py`: el tipo sale de `claves_es`, con `descripcion_en` leída del catálogo de la lámina.
- `validar_esquema.py --previa` (y `autocontrol.py --previa` se lo pasa): `textos.intro*` vacíos y «Cómo funciona» sin pasos salen como aviso y no como error.

**Texto** (una línea cada uno): `SKILL.md` lleva la copia de `cvt.html` con `<title>` y `meta description`, ver el plano sin grilla con pymupdf y clip, el extractor para catálogos que no son Yamaha, la regla general de la vista (seguir el sentido del plano; `comun.atras` se puede invertir) y «Cuándo» sin tarea de intervalos. `anexo-formato.md` muestra forma3d con el formato real (`tipo` plano). `anexo-esqueleto.md`: para catálogos que no son Yamaha, el extractor nuevo, sin subagente. La Boxer no se cita como ejemplo.

**Verificación** (salidas guardadas antes y después en el scratchpad, comparadas byte a byte):
- NMAX sin cambios: `extraer_catalogo.py` sobre `N-MAX-BBE4-2024.pdf` sale idéntico a `catalogo/nmax-bbe4.json` (38 figuras, 835 filas). `esqueleto_v2.py` y `plantillas_ficha.py` de las figs. 1, 8, 12 y 26 salen idénticos. Ninguna de las 835 descripciones de la NMAX cambia de clave. Un primer intento cambiaba «CIRCLIP» por «Circlip» en la fig. 12; lo corregí con la lista de palabras ambiguas.
- Boxer: el extractor nuevo, fig. 14 columna TEC, da las mismas 15 partes que mi extracción a mano (refs, códigos, cantidades y `descripcion_en` conservada), con 16-23 en `fuera` y 24 en `conjuntos`. También extrae bien las figs. 2, 13 y 30 (esta de 3 páginas). Con descripciones solo en español, el esqueleto reconoce la biblioteca (arandela, buje, placa, resorte, tornillo, tuerca, rodamiento) y las plantillas ponen tornillos, tuerca, arandela, resorte, rodamiento, buje y conjunto. Antes salía todo «conjunto» con relleno.
- Validador: `autocontrol --rapido` da 0 errores en `nmax-fig12`, `nmax-fig26` y `boxer-embrague`, y la salida del validador de la Boxer quedó idéntica. Las diferencias en `nmax-fig1` y `nmax-fig26` entre las dos corridas vienen de que piloto-esquema editó esos JSON a las 12:18, entre una corrida y otra; el código sin `--previa` no cambió. Con `--previa`, un esqueleto recién hecho muestra los 3 `intro*` y «Cómo funciona» como avisos; `autocontrol --previa` de la Boxer corre bien (23 s).
- No toqué datos ni arte de otras láminas ni `esquema*.js`. Sin commit.
