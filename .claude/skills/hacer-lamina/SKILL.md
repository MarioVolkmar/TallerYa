---
name: hacer-lamina
description: Hace una lámina del esquema pedagógico del despiece de TallerYa (dibujo propio armado y desarmado, fichas por pieza, «Cómo funciona», «Si falla», «Cuándo» y 3D), desde «hacer la fig. N de la moto X» hasta lista para revisión, con la calidad de la CVT (fig. 12 de la NMAX) o mejor. Úsala cuando pidan una lámina nueva del esquema, otra figura del despiece de una moto o rehacer una lámina sobre el motor de informes_noche/piloto-esquema/motor/.
---

# Hacer una lámina del esquema

Sirve para una sesión **limpia**: no hace falta leer el historial ni los relevos viejos; esta skill y sus anexos bastan.
Las rutas son relativas a la raíz del proyecto. `M` = `informes_noche/piloto-esquema/motor`.
**Modelo:** v2 (grupos, tornillería agrupada, ficha nueva y hoja inferior en el celular). El JSON lleva `"v2"`: ver «Modelo v2» y «Estilo v2» en `anexo-formato.md`.
**Meta:** **10 min de reloj** del catálogo a «lista para revisión», **sin trabajo en paralelo** y con la verificación incluida; calidad igual o mejor que la base (mecánica 4,8, UX la del v2) y una sola ronda de revisión. Prioridad: economía de tokens y coherencia de estilo.

## Reglas fijas
- **El motor no se toca** (`esquema.js`, `esquema.css`, `esquema3d.js`, `piezas-comunes.js`, `validar_esquema.py`, `mas_controles.py`, `medir_lamina.py`, `metricas.py`, `separar_numeros.py`, `firma_lamina.py`, `esqueleto_v2.py`, `plantillas_ficha.py`, `autocontrol.py`). Si le falta algo, avisar a Auxiliares con un solo mensaje concreto y seguir con lo demás.
  - Si Auxiliares pide un cambio del motor: antes `M/firma_lamina.py M/cvt.html M/freno.html M/bomba-freno.html M/admision.html --guardar <scratchpad>/firmas.json`, y después `--comparar` con el mismo archivo. Tiene que salir «idéntica» (si una capa de contexto difiere en 1-4 px, repetir esa página: a veces varía).
- Se crea solo esto:
  - `M/datos/<lamina>.json` (la fuente de todo);
  - `M/datos/<lamina>-arte.js` (solo las piezas propias);
  - `M/<pagina>.html`, una copia de `M/cvt.html` con dos rutas cambiadas: el `<script src="datos/…-arte.js">` y el `fetch("datos/….json")`, más el `<title>` y la `meta description`.
- **Los PDF solo se leen**, nunca se editan, mueven ni borran: `despiece_local/`, `manual_despiece/`. Nada de eso va al repo ni a servicios externos.
- **Sin commit.** No tocar `v8`, `integrado*`, `integracion/` ni `garaje/diagramas.py`, que solo se lee.
- **Relevo** en `informes_noche/relevos/<lamina>.md` si el contexto pasa del 50 %.
- **Leer poco:**
  - Grep antes que Read, y Read con `offset`/`limit`.
  - Nunca un PDF entero: primero el índice y después solo las páginas de la tabla o la lámina.
  - **Para ver la lámina:** `Read` de `despiece_local/grillas/<Marca-Moto>-figNN.png` (p. ej. `Yamaha-NMAX_155-BBE4-fig26.png`), una vez, reducida a ≤ 900 px. El `Read` del PDF falla en esta máquina porque falta pdftoppm. Sin grilla: pymupdf `page.get_pixmap(clip=Rect(…), matrix=Matrix(2.4,2.4))` solo de la zona del plano, a ≤ 900 px (en Auteco el plano va a la izquierda y la tabla a la derecha).
  - **Manual del propietario** (datos «Seguro»: bujía, aceite, refrigerante, torques que trae, avisos de seguridad): `manual_despiece/<moto>/…-manual-propietario.pdf`. **Solo lectura y sin páginas en imagen:** buscar texto con pymupdf (pypdf no está), p. ej. `venv/Scripts/python.exe -c "import pymupdf,re; d=pymupdf.open(r'<pdf>'); [print(i+1, m.group(0)) for i,p in enumerate(d) for m in re.finditer(r'.{0,120}(N·m|[Bb]uj[ií]a|fr[ií]o).{0,120}', p.get_text().replace('\n',' '))]" | head -30`. El número de página impreso (9-11) sale con `re.findall(r'\b\d+-\d+\b', d[i].get_text())`. En `garaje/intervalos/<moto>.json` ya están km, meses y la especificación de cada tarea con su página: mirar ahí primero. Manual escaneado (sin texto): `garaje/intervalos` y las notas del auditor; lo que falte va «sin dato» y a `pendientes`.
  - **Imágenes: 3 por lámina como máximo**, siempre a escala ≤ 0,5 o ≤ 900 px: el plano (una vez), la `--previa` y la de la medición final. Lo demás se mide con scripts.
  - **Qué leer, exacto** (nada más):
    - estilo del arte: solo el de **una** lámina del mismo sistema (paso 3), por rangos; para piezas de revolución, `M/datos/nmax-fig12-arte.js` líneas 96-158;
    - JSON v2 de ejemplo: con Python, una ficha, un grupo y un paso de esa misma lámina; nunca el archivo entero;
    - `M/esquema.js` no se lee: lo que hace falta está en `anexo-formato.md`.
  - Del ejemplo basta con un par de piezas, un paso y una ficha. Ejemplo: **una lámina del mismo sistema si existe** (frenos → `nmax-fig22` para el arte y el JSON, o `nmax-fig26` si hay lados; mangueras, ductos y cajas → `nmax-fig8`); si no, la CVT (`nmax-fig12`). Las tres ya son v2; sus `…-v1.json` son respaldos viejos: no copiarlos.

## Cronómetro: en cada fase, al empezar y al terminar
```
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/metricas.py inicio <lamina> <fase>
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/metricas.py fin <lamina> <fase>
```
Fases: `catalogo`, `dibujo2d`, `contenido`, `3d`, `validacion`, `mediciones`, `revision_mecanica`, `revision_ux` y `correcciones`. El autocontrol se cuenta dentro de `validacion`.
- Las revisoras cronometran `revision_mecanica` y `revision_ux` con el mismo script; la creadora no.
- **Tokens:** al empezar y al terminar, `get_usage` de la sesión (o el % de contexto): `… metricas.py dato <lamina> tokens '{"inicio":N,"fin":N}'`. `uso_plan` lo anota Auxiliares.
- Trabajo fuera de la lámina (p. ej. mejorar esta skill): fase `mejora_skill`, que no suma al total.
- **Tope por fase** (`meta_fases`): `metricas.py fin` marca ⚠ si la fase pasó su presupuesto (una línea en `explicacion` y sigue) y ✋ **CORTE** si pasó del doble: se para ahí, la causa va a `pendientes` del JSON y se pasa a la siguiente fase.

## Plan de 10 min (en serie, una sola sesión)
| min | fase | qué |
|---|---|---|
| 0-1 | `catalogo` | `esqueleto_v2.py` (resumen → ajustar grupos → `--escribir`) y `plantillas_ficha.py --escribir`. Si falta el catálogo de la moto, antes un subagente sonnet **en serie** con `anexo-esqueleto.md` (no cuenta en los 10). |
| 1-5 | `dibujo2d` | **parte de una lámina hermana o del mismo sistema si existe** (copia su `-arte.js` y adapta con un script; paso 3b), aunque la numeración cambie. Solo el arte propio que falta; anclas, `et` separados, pasos con movimientos. |
| 5-7 | `contenido` (el 3D va adentro) | en el mismo script del JSON: fichas propias del sistema sobre la plantilla (que, sirve, síntomas propios, enlaces `[[n|…]]`), grupos con `nombre`, «Cómo funciona» de 5 pasos, 3 cadenas, textos de la página, `pendientes`, y `con3d` para 1-3 formas difíciles (propias con `torno`/`prisma` si caben; si no, a `pendientes`). Cronómetro: solo `contenido` (no hace falta abrir `3d` aparte). |
| 7-9 | `validacion` + `mediciones` | `autocontrol.py --rapido` hasta 0 errores (segundos; también entre fases); `--previa` (validador + captura + `chequeo_rapido.py`: etiquetas montadas, pasos sin cambio o largos, marcas, solape; ~1 min) **sin bloqueantes**; y **una sola** medición completa, en segundo plano (~2 min). |
| 9-10 | margen | `autocontrol.py <lamina> --informe` (resumen para las revisoras) y entrega. |
- Salidas cortas: `autocontrol.py` sin `-v` da el resumen (hasta 8 errores y avisos agrupados); `-v` solo si hace falta el detalle. Nunca volcar el JSON ni el arte enteros.
- **Sin subagentes** (economía y estilo): lo que dicen los borradores de TallerYa se busca con un Grep por palabra clave, solo si una ficha lo necesita.

## Pasos

### 1. Catálogo (`catalogo`)
- Si existe `M/catalogo/<moto>.json`, se usa la figura N tal cual.
- Si no, se extrae una vez por moto: `venv/Scripts/python.exe M/catalogo/extraer_catalogo.py <pdf> M/catalogo/<moto>.json`. El script lee solo el texto de las páginas de tabla; si el layout sale raro, se mira **una** página. Catálogo que no es Yamaha (Auteco/Bajaj, en español): `… extraer_catalogo.py <pdf> M/catalogo/<moto>.json --figura N --columna <versión>` (sin `--columna` lista las versiones; agrega la figura al archivo). AKT (figuras «E- 4»/«F- 4»): `--figura E4`, y en la lámina `"figura":"E4"`.
- En el JSON de la lámina: `"catalogo":"<moto>"`, `"figura":N` e `"intervalos":"<archivo de garaje/intervalos sin .json>"`.

### 2. Esqueleto del JSON (dentro de `catalogo`): un comando, segundos
```
venv/Scripts/python.exe M/esqueleto_v2.py <moto> <N> <lamina> --intervalos <archivo> --tareas <t1,t2>            # revisa la propuesta
venv/Scripts/python.exe M/esqueleto_v2.py <moto> <N> <lamina> --intervalos <archivo> --tareas <t1,t2> --escribir
venv/Scripts/python.exe M/plantillas_ficha.py M/datos/<lamina>.json --escribir    # borrador v2 de cada ficha por tipo de pieza
```
- `esqueleto_v2.py` arma desde el catálogo: campos de página, `fichas` (nombre sugerido, `cat`, `codigo`, certeza de catálogo), `piezas` con anclas en una franja por grupo y la tornillería, sellos y bujes **ya dibujados con la biblioteca** (medidas por omisión: ajústalas), `v2.grupos` (un grupo por conjunto «ASSY» con sus hijas «.X» y la tornillería agrupada en `torn`), un paso por grupo y las filas de «Cuándo» con km, años y fuente de intervalos.
  - Agrupa por función: las piezas que nombran un lugar (culata, tapa de la culata, cilindro, bujía, pistón, levas, cadena, refrigeración; lista `FAMILIAS`) van a su grupo aunque el catálogo las separe; las que no nombran lugar (un empaque, una varilla) van con la pieza de antes, y la tornillería con la pieza anterior (revísala: tuercas y espárragos suelen ser del grupo siguiente). Los nombres compuestos salen del catálogo («GASKET, HEAD COVER» → «Empaque de la tapa de la culata») y los repetidos se distinguen por su grupo entre paréntesis («Tornillo (culata)»), nunca con un número suelto.
  - Revisa los grupos en el resumen que imprime: júntalos o pártelos por criterio mecánico (lo que se desarma junto) y ponles un `nombre` corto y claro. Las tareas de intervalos están en `garaje/intervalos/<archivo>.json`, clave `tareas`.
- `plantillas_ficha.py` llena solo los campos vacíos con la plantilla de su tipo (tornillos, oring, empaque, sello, retén, rodamiento, buje, resorte, seguro, grapa, abrazadera, caucho, manguera, filtro, tapa, caja, conjunto), con el estilo v2 y la regla de seguridad. `--tipo 23=filtro` fuerza un tipo. Nombra el lugar con el grupo de la pieza («Los tornillos que sujetan la tapa de la culata», «Revísalos cuando desarmes el cilindro»), así que corre después de ajustar los grupos. **La plantilla es un borrador:** lo propio de esta lámina lo escribes tú en el paso 4.
- Los nombres en español que ya usa TallerYa: `Grep` de la palabra clave en `garaje/despiece_glosario.py` y `garaje/despiece_mapas/<moto>.json`, solo si dudas del sugerido. Un solo nombre por pieza.

### 3. Dibujo 2D (`dibujo2d`)
- **Primero decide la vista**, antes de dibujar: la biblioteca dibuja cada pieza **de frente, con su eje hacia el lector** (tornillos y tuercas por la cabeza, empaques y placas planos de cara, espesor hacia `comun.atras`). Elige la vista en la que los ejes de la mayoría de las piezas miran al lector y sigue el sentido del despiece del plano (`comun.atras` se puede invertir, p. ej. `[-0.5,-0.32]`): frenos y CVT, de lado. **En motores (cilindro, culata, tapas apiladas), de lado o de tres cuartos**, para que se vea la pila y las capas no se tapen: desde arriba, la tapa cubre la culata y el cilindro y sus píldoras caen en el mismo punto (le pasó a la fig. 1). Si una capa queda tapada igual, pon su píldora (`marca`) en el borde que se ve y aclárala. Si una pieza propia va de lado (la bujía), dibújala así en el arte. Anótalo en `fuentes.aproximado`.
- **Primero la biblioteca:** tornillos, tuercas, arandelas, seguros, retenes, O-rings, rodamientos, bujes, resortes y pasadores van con una línea por pieza: `{"id":"28","n":"28","comun":"tuerca","p":{"x":278,"y":414,"r":14},"anc":[…],"et":[…],"vis":"exp"}`.
  - Se declara una vez por lámina: `"comun":{"atras":[dx,dy],"colores":{…},"sombra":"url(#…)"}`.
  - Los tipos y sus medidas están en `anexo-formato.md`.
  - Las piezas comunes traen 3D sin trabajo extra.
- **Las piezas propias** van en `<lamina>-arte.js`, en el estilo de la v8: fondo oscuro, degradados sobrios, sombra y caras de frente con el espesor hacia «atrás».
  - Las de revolución se describen con su perfil una sola vez, en `perfiles` (ver paso 5).
  - Como modelo para copiar el estilo, leer por rangos el arte de **una lámina del mismo sistema** si existe (frenos: `M/datos/nmax-fig22-arte.js`, que trae el cáliper y la bomba en su «Cómo funciona»). Si no hay, `M/datos/nmax-fig12-arte.js`, de `artePoleaMovTr` a `arteCampana`.
  - Piezas internas que no se ven armadas (kit, diafragma): clase `esq-oculto-arm` en su `<g>` (ver `anexo-formato.md`).
  - **Kits** (clutch completo, juego de discos, conjunto armado sin cuerpo propio): sin dibujo, sin grupo y sin ficha. Van en `"kits":{"<ref>":[refs que trae]}` y en el `cat` de cada pieza que traen («… · también en el kit ref. N (nombre, código)»). El validador lo comprueba y avisa si una píldora apunta a piezas que no se ven armadas.
- **Pasos del desarme:** en el orden real, y lo que sujeta sale antes (campo `sujeta`). Cada número sale en algún paso. Lo primero es aflojar el cable o soltar el mando; si para llegar a una pieza hay que drenar aceite o quitar una tapa, su `dif` es «taller» (el validador avisa).
  - **Cada paso, 250 caracteres como máximo** (el validador avisa sobre 300): qué haces, el aviso y el cierre («Al armar: NGK CPR8EA-9 · 0,8–0,9 mm · 13 N·m», en una línea compacta). Lo que sale antes (escape, mangueras, otras láminas) va a la ficha de la pieza. Los avisos de seguridad y los cierres nunca se acortan.
  - **Rectificar y sobremedidas:** solo si el catálogo trae piezas de sobremedida (el validador avisa si una ficha dice «sobremedida», «rectificar el cilindro» o «camisa» y no las hay). Un cilindro con pared tratada (sin camisa) no se rectifica: va nuevo.
- **De entrada, para no repetir pendientes:**
  - **densidad de números** (regla de ux-piloto, también en `criterios-ux.md`):
    - siempre: 0 números sin su toque (`→rect`), 0 roces a ±9 px y **≥ 19 px** entre números a 360 (el validador exige además un radio ≥ 9 px);
    - con 20 números o menos: ≥ 24 px sin zoom;
    - con más de 20: ≥ 24 px con el primer zoom (×1,6). El motor muestra el zoom (+ resaltado y la pista «Usa + para acercar») y la lista va en rejilla; tú cuidas los 19 px;
  - en el armado, separar los `et`; en el despiece, `separar_numeros.py` (paso 6);
  - el contexto (manubrio, carcasa de otra lámina) con `"alPrincipio":true`, para que no tape números ni su área de toque;
  - encuadre del armado con proporción 900:700 y margen para el número más bajo;
  - el dibujo ya llega a ≥ 460 px a 1280 por el motor; no achicar el encuadre sin necesidad.
  - **extrusiones** (el espesor hacia «atrás»): borde solo en la copia del fondo (la cara de atrás) y las intermedias sin borde, con un paso cada ~4 unidades; con borde en cada copia se ve como una pila de láminas;
  - **marcas de grupo**: el motor las mantiene enteras dentro del lienzo con su área de toque de 46 px; un encuadre ancho no las achica;
  - **piezas grandes y oscuras** (tapas, carcasas de plástico): borde claro, brillo y detalles (rejilla, tornillos) que se vean sobre el fondo oscuro; si no, en la vista general son una mancha;
  - **piezas comunes escondidas armadas** (resorte, o-ring dentro de una carcasa): `"oculto":true` en la pieza (equivale a `esq-oculto-arm`);
  - **tubo delgado**: área de toque con un `rect` invisible (`fill-opacity="0" pointer-events="all"`) dentro de su arte, y su abrazadera antes en `piezas` (si va después, su círculo automático le tapa el toque).

### 4. Contenido (`contenido`)
- Fallas con su causa, síntomas de moto (no de carro), «¿se repara o se cambia?», `conecta`, `efectos`, «Cómo funciona» (5 a 8 pasos que mueven el esquema), «Si falla» (cadenas de 3 a 5 eslabones) y «Cuándo».
- **«Cómo funciona», criterio mínimo** (referencia: la CVT, nota 5; ux-piloto lo mide con `medir_lamina.py`):
  - al menos 3 piezas reconocibles por su forma (no cajas ni rectángulos con nombre);
  - un corte o una transparencia que muestre lo de adentro;
  - cada paso cambia algo visible que corresponde a su texto (lo que gira, abre, fluye o se enciende);
  - un indicador físico que cambia, cuando aplica (rpm, % de acelerador, presión, °C, litros, ángulo del cigüeñal);
  - etiquetas sin montarse y de 12 px o más a 1280 y a 360 (en el SVG, ~20 unidades: `#fn .esq-fn-et{font-size:20px}`);
  - pasos de 250 caracteres como máximo.
- **Estilo v2** (`anexo-formato.md`): segunda persona, sin «(N)» ni nombres de catálogo en la prosa (enlaces `[[n|texto]]`), `decision` + `porque`, `arrastra`. Se acorta la explicación, nunca la seguridad.
- **Cada dato con su certeza:** `certezaDe` por campo (`ok` = catálogo o manual; `ap` = práctica de taller y proporciones) y la lista `certeza` para «Fuentes».
- **Cifras sin fuente:** «aprox.». **Torques y medidas sin fuente:** «sin dato» o «manual de servicio».
- **«Cuándo» sin tarea en `garaje/intervalos/`:** la fila va sin `tarea`, con la fuente del manual del propietario (di si es de otra versión o país), y se anota en `pendientes`.

### 5. 3D (`3d`), según `M/regla-3d.md`
- Solo las fichas de `v2.con3d` muestran el visor: formas difíciles de imaginar. Las piezas comunes traen la forma lista, pero sin `con3d` no salen.
- A las propias que cumplan la regla, se les pone `fichas[n].forma3d`:
  - de revolución: `torno` con `"perfil":"@nombre"`, con el perfil en `perfiles`;
  - **cortes reales** con `prisma` + `huecos`;
  - ranuras sobre superficies curvas: `caja` oscura.
- Si una propia pasa de 30 minutos, se deja sin 3D y se anota en `pendientes`.

### 3b. Armar el JSON con un script (recomendado: lo más rápido)
- **Lámina hermana con la misma numeración** (p. ej. freno trasero fig. 24 = delantero fig. 22, refs 1-15 iguales): el script parte del JSON de la hermana, copia su `-arte.js` cambiando solo lo distinto (contexto, forma del disco) y reemplaza códigos y `cat` del catálogo, lado, mandos e intervalos. Al final, una búsqueda de rastros de la hermana («delanter», «fig. 22»). La fig. 24 salió así en 6 min.
- Escribe un solo script en el scratchpad (`armar_<lamina>.py`) que cargue `M/datos/<lamina>.json` (el que dejó `esqueleto_v2.py`), ajuste piezas, `et`, pasos, grupos, fichas, «Cómo funciona», cadenas y `con3d`, y lo guarde (UTF-8, `ensure_ascii=False`). Se edita el script y se vuelve a correr; nunca el JSON a mano.
- **Después de cada regeneración:** `separar_numeros.py M/datos/<lamina>.json --escribir` (el script pisa las anclas separadas) y `autocontrol.py <lamina> --rapido`. O ponlos al final del propio script.

### 6-7. Validar y medir (`validacion`, `mediciones`): un comando
```
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/autocontrol.py <lamina> --rapido                 # segundos: solo el validador
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/autocontrol.py <lamina> --pagina <pagina>.html --captura <lamina>-1280.jpg --ojo a,b,c,d,e,f   # al final: validador + medir_lamina + captura + métricas (≈ 1,5 min)
```
- `--pagina` y `--captura` tienen el mismo formato: nombre solo = en `M`; con carpeta = desde la raíz; o ruta absoluta.
- **Antes de cada corrección** (revisión, pedido o acortar textos): `autocontrol.py <lamina> --antes` guarda `datos/<lamina>.antes.json`; después, `--rapido` avisa con «regresión:» si desapareció una palabra de seguridad o de procedimiento (PMS, marcas, jeringa, purgar, probar, nuevo, apriete, frío, caliente, radiador…), en total o de un paso concreto. Al acortar, esas palabras se quedan; si de verdad se mueven a la ficha, que sea a propósito.
- **Las notas a ojo van después de mirar:** `--previa` hace el validador, la captura del armado a 1280 y el chequeo rápido (lo que bloquearía la medición; ~1 min); mírala una vez a escala 0,5, pon las notas y pásalas en `--ojo` a la medición final. Con `--ojo`, el informe ya no dice «faltan… a ojo».
- **El tiempo de verificación tiene tope:** mientras trabajas, solo `--rapido`; **una sola** medición completa al final (con `--captura` y `--ojo`; tarda ~2 min: córrela en segundo plano). Si esa medición da un bloqueante, corriges y repites solo esa; nada de medir entre fases.
- La captura es del **armado limpio** (la página recargada): mírala una vez, a escala 0,5, para juzgar el dibujo. Sale con código 1 mientras haya errores o bloqueantes.
- El validador revisa campos, catálogo, nombres, desarme, cifras y torques sin fuente, intervalos, certeza, estilo y seguridad v2, y la estructura v2 (grupos, `torn`, pasos, `certezaDe`, `con3d`, piezas sin grupo). Los **avisos** se leen todos: «¿nombre viejo?» casi siempre es un error de verdad.
- Errores de toque en el despiece: `--separar` corre antes `separar_numeros.py --escribir`. Si armas el JSON con un script propio, córrelo después de cada regeneración.
- Una pieza que no recibe el toque dentro de su grupo: píntala después (orden de `piezas`) o ponla en `v2.toqueExtra` (pocas: tapan a las vecinas). Dos píldoras de grupo encimadas: `marca` a mano.
- Después, el **autocontrol manual** de `anexo-autocontrol.md`, pregunta por pregunta. `--ojo a,b,c,d,e,f` lleva tus notas a ojo (criterios UX 1, 2, 3, 4, 5 y 7). `autocontrol.py` usa `medir_lamina.py` (detecta v2 solo; mide la hoja inferior, los toques hasta la ficha y el largo de la ficha a 360; rúbrica v3 en `informes_noche/piloto-esquema/criterios-ux.md`). La única captura sale de la medición final con `--captura`.
- Anotar las notas: `… metricas.py dato <lamina> notas_ux '{…por criterio…,"promedio":x}'`.

### 8. Entregar
1. `venv/Scripts/python.exe M/armar_un_archivo.py M/datos/<lamina>.json`: el archivo único para el panel.
2. Anotar en métricas:
   - `piezas_3d`, `pct_seguro` (% de números, nombres y cantidades que cuadran con el catálogo, como en la CVT), `pct_certeza_total` (% de «Seguro» sobre todas las marcas de certeza de fichas y «Cuándo»), `pendientes`, `errores_revisoras` (después de las revisiones) y el contexto al terminar;
   - después, `… metricas.py informe <lamina>`.
3. Nota arriba en `informes_noche/piloto-esquema/cambios.md`.
4. `autocontrol.py <lamina> --informe` → `M/revision/<lamina>.md`: las revisoras (mecánica y UX, en paralelo, 10 min cada una) trabajan sobre ese resumen con `informes_noche/piloto-esquema/guia-revision-rapida.md`.
5. Un solo mensaje a Auxiliares con el informe de métricas y la ruta del resumen.

## Terminado quiere decir
- [ ] `autocontrol.py` sale con código 0 (validador **OK**, avisos leídos, medir **sin bloqueantes**), y cada nota UX ≥ la de la línea base (CVT: promedio 4,5; por criterio en `M/metricas.json`).
- [ ] Autocontrol completo (`anexo-autocontrol.md`): mecánico y UX a ojo, todo en «sí».
- [ ] La nota mecánica de la revisora ≥ 4,8, la de la línea base. Si alguna nota baja, se explica en `explicacion` (`metricas.py dato …`); sin explicación no está terminada.
- [ ] Métricas anotadas en cada fase y `informe` comparado contra la CVT y el promedio, diciendo qué fase tardó más de lo esperado y por qué.
- [ ] Sin errores de consola. Funciona sin red, salvo las fuentes de Google.
