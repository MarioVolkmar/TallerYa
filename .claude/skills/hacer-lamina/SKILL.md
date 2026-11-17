---
name: hacer-lamina
description: Hace una lámina del esquema pedagógico del despiece de TallerYa (dibujo propio armado y desarmado, fichas por pieza, «Cómo funciona», «Si falla», «Cuándo» y 3D), desde «hacer la fig. N de la moto X» hasta lista para revisión, con la calidad de la CVT (fig. 12 de la NMAX) o mejor. Úsala cuando pidan una lámina nueva del esquema, otra figura del despiece de una moto o rehacer una lámina sobre el motor de informes_noche/piloto-esquema/motor/.
---

# Hacer una lámina del esquema

Sirve para una sesión **limpia**: no hace falta leer el historial ni los relevos viejos; esta skill y sus anexos bastan.
Las rutas son relativas a la raíz del proyecto. `M` = `informes_noche/piloto-esquema/motor`.
**Modelo:** v2 (grupos, tornillería agrupada, ficha nueva y hoja inferior en el celular). El JSON lleva `"v2"`: ver «Modelo v2» y «Estilo v2» en `anexo-formato.md`.
**Meta:** **10 min de reloj para todo**, del catálogo a revisada y corregida (creación + revisión integrada, paso 9), **sin trabajo en paralelo** salvo la revisora; calidad igual o mejor que la base (mecánica 4,8, UX la del v2). Prioridad: economía de tokens y coherencia de estilo.

## Reglas fijas
- **El motor no se toca** (`esquema.js`, `esquema.css`, `esquema3d.js`, `piezas-comunes.js`, `validar_esquema.py`, `mas_controles.py`, `medir_lamina.py`, `metricas.py`, `separar_numeros.py`, `firma_lamina.py`, `esqueleto_v2.py`, `plantillas_ficha.py`, `autocontrol.py`, `remapear_hermana.py`, `buscar_manual.py`). Si le falta algo, avisar a Auxiliares con un solo mensaje concreto y seguir con lo demás.
  - Después de cambiar la skill o el motor: `M/regresion.py` (decide qué revisar); antes de un commit grande: `M/regresion.py --todas` (en segundo plano, ≤ 3 min). Detalle en `anexo-autocontrol.md`.
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
  - **Para ver la lámina:** `Read`, una vez, de la imagen que `esqueleto_v2.py` imprime en «plano:» (la grilla de `despiece_local/grillas/` o, si no hay, la página del plano que genera a 900 px). El `Read` del PDF falla (falta pdftoppm). Comprueba con ella el orden de las piezas.
  - **Manuales de taller y del propietario** (torques, avisos, bujía, aceite): **solo lectura, sin imágenes y sin volcar páginas.** Primero `garaje/intervalos/<moto>.json` (km, meses y especificación con su página). Después `M/buscar_manual.py <catalogo> --indice --cual taller` (secciones con su página, ~2 k caracteres) y `M/buscar_manual.py <catalogo> "pastilla,purg,N·m" --paginas 101-110` (una línea por hallazgo, con página del PDF e impresa; tope 12). Nunca `get_text()` de páginas enteras. Manual escaneado (sin texto): `garaje/intervalos` y las notas del auditor; lo que falte va «sin dato» y a `pendientes`.
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
Fases: `catalogo`, `dibujo_contenido` (o `dibujo2d`, `contenido` y `3d`: cuentan contra el mismo presupuesto), `validacion`, `mediciones`, `revision` (solo las correcciones) y `revision_espera` (la revisora corre en paralelo con `--final`; no suma). El autocontrol se cuenta dentro de `validacion`.
- Presupuestos (`meta_fases`): catálogo 1,5 · dibujo + contenido 4 · verificación 2,5 · revisión 1,5 · margen 0,5. Marca olvidada: `metricas.py inicio|fin … --hora HH:MM`.
- A la 5.ª lámina sin auditoría, `metricas.py` escribe `informes_noche/piloto-esquema/auditoria-pendiente.md` y avisa: pídesela a Auxiliares (sesión independiente, `guia-auditoria-externa.md`).
- **Tokens:** al empezar y al terminar, `get_usage` de la sesión (o el % de contexto): `… metricas.py dato <lamina> tokens '{"inicio":N,"fin":N}'`. `uso_plan` lo anota Auxiliares.
- Trabajo fuera de la lámina (p. ej. mejorar esta skill): fase `mejora_skill`, que no suma al total.
- **Tope por fase** (`meta_fases`): `metricas.py fin` marca ⚠ si la fase pasó su presupuesto (una línea en `explicacion` y sigue) y ✋ **CORTE** si pasó del doble: se para ahí, la causa va a `pendientes` del JSON y se pasa a la siguiente fase.

## Plan de 10 min (en serie, una sola sesión)
| min | fase | qué |
|---|---|---|
| 0-1 | `catalogo` | `esqueleto_v2.py` (resumen → ajustar grupos → `--escribir`) y `plantillas_ficha.py --escribir` (con `--hermana <lámina>` si partes de una hermana). Si falta el catálogo de la moto, antes un subagente sonnet **en serie** con `anexo-esqueleto.md` (no cuenta en los 10). |
| 1-5 | `dibujo_contenido` | **parte de una lámina hermana o del mismo sistema si existe** (copia su `-arte.js` y adapta con un script; paso 3b), aunque la numeración cambie. Sin hermana: biblioteca de ruedas y transmisión. Solo el arte propio que falta; anclas, `et` separados, pasos con movimientos. |
| 5-7 | `contenido` (el 3D va adentro) | en el mismo script del JSON: fichas propias del sistema sobre la plantilla (que, sirve, síntomas propios, enlaces `[[n|…]]`), grupos con `nombre`, «Cómo funciona» de 5 pasos, 3 cadenas, textos de la página, `pendientes`, y `con3d` para 1-3 formas difíciles (propias con `torno`/`prisma` si caben; si no, a `pendientes`). Cronómetro: solo `contenido` (no hace falta abrir `3d` aparte). |
| 5-7,5 | `validacion` + `mediciones` | `autocontrol.py --rapido` hasta 0 errores (segundos; también entre fases); `--previa` (una sola corrida de Chrome, ~30 s: validador, captura, «Cómo funciona» a 360/390/1280, marcas y solape) **sin bloqueantes**; si arreglas un solape, `--previa --solo-solape --grupo <ids>`; y **una sola** medición completa con `--final`, en segundo plano (~2 min). |
| 7,5-9,5 | `revision` | `--informe` y la revisora (paso 9) lanzada junto con la medición `--final`; `revision` cuenta solo las correcciones. |
| 9-10 | margen | entrega. |
- Salidas cortas: `autocontrol.py` sin `-v` da el resumen (hasta 8 errores y avisos agrupados); `-v` solo si hace falta el detalle. Nunca volcar el JSON ni el arte enteros.
- **Sin subagentes en la creación** (economía y estilo; solo la revisora del paso 9): lo que dicen los borradores de TallerYa se busca con un Grep por palabra clave, solo si una ficha lo necesita.

## Pasos

### 1. Catálogo (`catalogo`)
- Si existe `M/catalogo/<moto>.json`, se usa la figura N tal cual.
- Si no, se extrae una vez por moto: `venv/Scripts/python.exe M/catalogo/extraer_catalogo.py <pdf> M/catalogo/<moto>.json --moto <moto>` (Yamaha Colombia bilingüe: `descripcion` en español y `descripcion_en`). El script lee solo el texto de las páginas de tabla; si el layout sale raro, se mira **una** página. Catálogo que no es Yamaha (Auteco/Bajaj, en español): `… extraer_catalogo.py <pdf> M/catalogo/<moto>.json --figura N --columna <versión>` (sin `--columna` lista las versiones; agrega la figura al archivo). AKT (figuras «E- 4»/«F- 4»): `--figura E4`, y en la lámina `"figura":"E4"`. Honda (inglés, «F-10»): `--figura F10 --columna C --saltar 2U` (columna de versión; `--saltar` quita mercados, p. ej. la versión Nissin), y en la lámina `"figura":"F10"`.
- **Variantes** (tambor o disco, con o sin ABS): elige la que nombre el pedido (si no la nombra, la más común en Colombia) y dilo en `cabeza.aviso`.
- En el JSON de la lámina: `"catalogo":"<moto>"`, `"figura":N` e `"intervalos":"<archivo de garaje/intervalos sin .json>"`.

### 2. Esqueleto del JSON (dentro de `catalogo`): un comando, segundos
```
venv/Scripts/python.exe M/esqueleto_v2.py <moto> <N> <lamina> --intervalos <archivo> --tareas <t1,t2>            # revisa la propuesta
venv/Scripts/python.exe M/esqueleto_v2.py <moto> <N> <lamina> --intervalos <archivo> --tareas <t1,t2> --escribir
venv/Scripts/python.exe M/plantillas_ficha.py M/datos/<lamina>.json --escribir    # borrador v2 de cada ficha por tipo de pieza
```
- `esqueleto_v2.py` arma desde el catálogo: campos de página, `fichas` (nombre sugerido, `cat`, `codigo`, certeza de catálogo), `piezas` con anclas en una franja por grupo y la tornillería, sellos y bujes **ya dibujados con la biblioteca** (medidas por omisión: ajústalas), `v2.grupos` (un grupo por conjunto «ASSY» con sus hijas «.X» y la tornillería agrupada en `torn`), un paso por grupo y las filas de «Cuándo» con km, años y fuente de intervalos.
  - Agrupa por función (`FAMILIAS`; en ruedas: eje, freno, arrastre y rueda): lo que no nombra lugar (empaque, buje, retén) y la tornillería van con la pieza de antes (revísalo: tuercas y espárragos suelen ser del grupo siguiente). Un kit repetido («20A» junto a «20») va solo en `kits`. Los repetidos se distinguen por su grupo («Tornillo (culata)»), nunca con un número suelto. Si avisa de CBS/ABS en el modelo, no lo nombres como sistema de la figura.
  - Revisa los grupos en el resumen que imprime: júntalos o pártelos por criterio mecánico (lo que se desarma junto) y ponles un `nombre` corto y claro. Las tareas de intervalos están en `garaje/intervalos/<archivo>.json`, clave `tareas`.
- `plantillas_ficha.py` llena solo los campos vacíos con la plantilla de su tipo (por sistema: chiclé, flota, bandas, cadena…; si no, por tipo), con el estilo v2 y la regla de seguridad. `--tipo 23=filtro` fuerza un tipo. Nombra el lugar con el grupo de la pieza («Los tornillos que sujetan la tapa de la culata», «Revísalos cuando desarmes el cilindro»), así que corre después de ajustar los grupos. **La plantilla es un borrador:** lo propio de esta lámina lo escribes tú en el paso 4.
- Los nombres en español que ya usa TallerYa: `Grep` de la palabra clave en `garaje/despiece_glosario.py` y `garaje/despiece_mapas/<moto>.json`, solo si dudas del sugerido. Un solo nombre por pieza.

### 3. Dibujo 2D (`dibujo2d`)
- **Primero decide la vista**, antes de dibujar: la biblioteca dibuja cada pieza **de frente, con su eje hacia el lector** (tornillos y tuercas por la cabeza, empaques y placas planos de cara, espesor hacia `comun.atras`). Elige la vista en la que los ejes de la mayoría de las piezas miran al lector y sigue el sentido del despiece del plano (`comun.atras` se puede invertir, p. ej. `[-0.5,-0.32]`): frenos y CVT, de lado. **En motores (cilindro, culata, tapas apiladas), de lado o de tres cuartos**, para que se vea la pila y las capas no se tapen: desde arriba, la tapa cubre la culata y el cilindro y sus píldoras caen en el mismo punto (le pasó a la fig. 1). Si una capa queda tapada igual, pon su píldora (`marca`) en el borde que se ve y aclárala. Si una pieza propia va de lado (la bujía), dibújala así en el arte. Anótalo en `fuentes.aproximado`.
- **Primero la biblioteca:** tornillos, tuercas, arandelas, seguros, retenes, O-rings, rodamientos, bujes, resortes y pasadores van con una línea por pieza (con el eje en el plano del dibujo, como en una horquilla: `"eje":"vertical"` u `"horizontal"` en `p`): `{"id":"28","n":"28","comun":"tuerca","p":{"x":278,"y":414,"r":14},"anc":[…],"et":[…],"vis":"exp"}`.
  - Se declara una vez por lámina: `"comun":{"atras":[dx,dy],"colores":{…},"sombra":"url(#…)"}`.
  - Los tipos y sus medidas están en `anexo-formato.md`.
  - Las piezas comunes traen 3D sin trabajo extra.
- **Las piezas propias** van en `<lamina>-arte.js`, en el estilo de la v8: fondo oscuro, degradados sobrios, sombra y caras de frente con el espesor hacia «atrás».
  - Las de revolución se describen con su perfil una sola vez, en `perfiles` (ver paso 5).
  - Como modelo para copiar el estilo, leer por rangos el arte de **una lámina del mismo sistema** si existe (frenos: `M/datos/nmax-fig22-arte.js`, que trae el cáliper y la bomba en su «Cómo funciona»). Si no hay, `M/datos/nmax-fig12-arte.js`, de `artePoleaMovTr` a `arteCampana`.
  - Piezas internas que no se ven armadas (kit, diafragma): clase `esq-oculto-arm` en su `<g>` (ver `anexo-formato.md`).
  - **Kits** (clutch completo, juego de discos, conjunto armado sin cuerpo propio): sin dibujo, sin grupo y sin ficha. Van en `"kits":{"<ref>":[refs que trae]}` y en el `cat` de cada pieza que traen («… · también en el kit ref. N (nombre, código)»). El validador lo comprueba y avisa si una píldora apunta a piezas que no se ven armadas.
- **Pasos del desarme:** en el orden real, y lo que sujeta sale antes (campo `sujeta`). Cada número sale en algún paso. Lo primero es aflojar el cable o soltar el mando; si para llegar a una pieza hay que drenar aceite o quitar una tapa, su `dif` es «taller» (el validador avisa). Orden y seguridad por tipo de moto y sistema: `anexo-desarme.md`.
  - **Cada paso, 250 caracteres como máximo** (el validador avisa desde ahí y `aplicar_hallazgos` no aplica lo que lo pase): qué haces, el aviso y el cierre («Al armar: NGK CPR8EA-9 · 0,8–0,9 mm · 13 N·m», en una línea compacta). Lo que sale antes (escape, mangueras, otras láminas) va a la ficha de la pieza. Los avisos de seguridad y los cierres nunca se acortan.
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
  - extrusiones, marcas de grupo, piezas grandes y oscuras y tubos delgados: `anexo-formato.md`, «Detalles del dibujo».
  - **piezas comunes escondidas armadas** (resorte, o-ring dentro de una carcasa): `"oculto":true` en la pieza (equivale a `esq-oculto-arm`);

### 4. Contenido (`contenido`)
- Fallas con su causa, síntomas de moto (no de carro), «¿se repara o se cambia?», `conecta`, `efectos`, «Cómo funciona» (5 a 8 pasos que mueven el esquema), «Si falla» (cadenas de 3 a 5 eslabones) y «Cuándo».
- **«Cómo funciona»:** parte del esqueleto de tu sistema en `anexo-funciona.md` (solo esa sección). Criterio mínimo (lo mide `medir_lamina.py`):
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
- **Lámina hermana con la misma numeración** (p. ej. freno trasero fig. 24 = delantero fig. 22, refs 1-15 iguales): el script parte del JSON de la hermana, copia su `-arte.js` cambiando solo lo distinto (contexto, forma del disco) y reemplaza códigos y `cat` del catálogo, lado, mandos e intervalos. Pon `"hermana":"<lámina>"` en el JSON: `--rapido` busca sus rastros (figura, cadenas, enlaces). La fig. 24 salió así en 6 min.
- **Hermana con otra numeración** (otra marca, mismo sistema): **primero** `M/remapear_hermana.py <lamina> --desde <hermana> --mapa '{"1":"3","8":"8",…}' --arte --escribir` (lado repetido: `--espejo <x> --mapa-lado '{…}'`). Cambia los números **una sola vez** en todo el JSON (enlaces, cadenas, sujeta, grupos, chips…), anota `hermana` y `remapeo` (otra corrida igual no hace nada; con otro mapa se niega), copia el arte y lista sus funciones y rótulos con su línea: cambia solo esos, sin leer el arte ni los textos de la hermana. Corrige lo que liste como «heredado sin respaldo» (o-ring donde dice GASKET, equipo que esta moto no tiene) antes de la revisora. Tu script de armado parte de ese JSON y **no remapea**; deja como texto los enlaces sin destino, quita `v2.deriva` y cambia `ESQ_ARTE[...]`. `--rapido` avisa de números y figuras que quedaron de la hermana. Fichas: `plantillas_ficha.py --hermana <lámina> --escribir` le pone a cada pieza nueva la ficha de la hermana del mismo tipo con el nombre nuevo (enlaces como texto); edítalas, no las escribas de cero.
- Escribe un solo script en el scratchpad (`armar_<lamina>.py`) que cargue `M/datos/<lamina>.esqueleto.json` (la copia limpia de `esqueleto_v2.py`; **nunca su propia salida**), ajuste piezas, `et`, pasos, grupos, fichas, «Cómo funciona», cadenas y `con3d`, y lo guarde (UTF-8, `ensure_ascii=False`). Se edita el script y se vuelve a correr; nunca el JSON a mano.
- **Después de cada regeneración:** `separar_numeros.py M/datos/<lamina>.json --escribir` (el script pisa las anclas separadas) y `autocontrol.py <lamina> --rapido`. O ponlos al final del propio script.

### 6-7. Validar y medir (`validacion`, `mediciones`): un comando
```
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/autocontrol.py <lamina> --rapido                 # segundos: solo el validador
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/autocontrol.py <lamina> --pagina <pagina>.html --captura <lamina>-1280.jpg --ojo a,b,c,d,e,f   # al final: validador + medir_lamina + captura + métricas (≈ 1,5 min)
```
- `--pagina` y `--captura` tienen el mismo formato: nombre solo = en `M`; con carpeta = desde la raíz; o ruta absoluta.
- **Antes de cada corrección** (revisión, pedido o acortar textos): `autocontrol.py <lamina> --antes` guarda `datos/<lamina>.antes.json`; después, `--rapido` avisa con «regresión:» si desapareció una palabra de seguridad o de procedimiento (PMS, marcas, jeringa, purgar, probar, nuevo, apriete, frío, caliente, radiador…), en total o de un paso concreto. Al acortar, esas palabras se quedan; si de verdad se mueven a la ficha, que sea a propósito.
- **Las notas a ojo van después de mirar:** `--previa` hace en una corrida el validador, la captura del armado a 1280 y el chequeo rápido con el solape (lo que bloquearía la medición; ~30 s; no corras `chequeo_rapido.py` suelto); mírala una vez a escala 0,5, pon las notas y pásalas en `--ojo` a la medición final. Con `--ojo`, el informe ya no dice «faltan… a ojo».
- **El tiempo de verificación tiene tope:** mientras trabajas, solo `--rapido`; **una sola** medición completa al final (con `--captura` y `--ojo`; tarda ~2 min: córrela en segundo plano). Si esa medición da un bloqueante, corriges y repites solo esa; nada de medir entre fases.
- La captura es del **armado limpio** (la página recargada): mírala una vez, a escala 0,5, para juzgar el dibujo. Sale con código 1 mientras haya errores o bloqueantes.
- Qué revisa el validador y cómo arreglar toques y píldoras encimadas: `anexo-autocontrol.md`, «Validador y toques».
- Después, el **autocontrol manual** de `anexo-autocontrol.md`, pregunta por pregunta. `--ojo a,b,c,d,e,f` lleva tus notas a ojo (criterios UX 1, 2, 3, 4, 5 y 7). `autocontrol.py` usa `medir_lamina.py` (detecta v2 solo; mide la hoja inferior, los toques hasta la ficha y el largo de la ficha a 360; rúbrica v3 en `informes_noche/piloto-esquema/criterios-ux.md`). La única captura sale de la medición final con `--captura`.
- Anotar las notas: `… metricas.py dato <lamina> notas_ux '{…por criterio…,"promedio":x}'`.

### 8. Entregar
1. `venv/Scripts/python.exe M/armar_un_archivo.py M/datos/<lamina>.json`: el archivo único para el panel.
2. Anotar en métricas:
   - `piezas_3d`, `pct_seguro` (% de números, nombres y cantidades que cuadran con el catálogo, como en la CVT), `pct_certeza_total` (% de «Seguro» sobre todas las marcas de certeza de fichas y «Cuándo»), `pendientes`, `errores_revisoras` (después de las revisiones) y el contexto al terminar;
   - después, `… metricas.py informe <lamina>`.
3. Nota arriba en `informes_noche/piloto-esquema/cambios.md`.
4. Revisión integrada (paso 9) y después `metricas.py informe`.
5. Un solo mensaje a Auxiliares con el informe de métricas y la ruta del resumen.

### 9. Revisión integrada (`revision`, 2 min)
0. Antes, `--rapido` en 0 errores: ya atrapa cantidad, rastros de la hermana, jerga y relleno, y una pieza con dos nombres. Lo que la máquina ve no se le pide a la revisora.
1. `M/revision/<lamina>.md` (todos los campos de cada ficha, cantidades, fuentes, certezas, lo heredado y las páginas del manual): lo rehace `--final`, y cualquier `autocontrol` si el JSON cambió (huella en la 1.ª línea). Lánzala después del último `--rapido`; a mano: `--informe`.
2. **Una sola revisora** (Agent, modelo de la sesión, en segundo plano, sin contexto; no edita). Recibe la ruta de la página, el resumen y `informes_noche/piloto-esquema/guia-revision-rapida.md`, y revisa en una pasada:
   - mecánica: corrección técnica, seguridad y datos (del manual, solo las páginas del resumen, con pymupdf);
   - UX: claridad, textos y orden.
   Devuelve `{"nota":{"mecanica":x,"ux":y},"hallazgos":[…]}`: **máximo 15**, graves primero, cada uno `{gravedad, lado, categoria, campo, reemplazar, por, texto}` (formato en `M/aplicar_hallazgos.py`). La calidad la vigila la auditoría externa cada 5 láminas.
3. `aplicar_hallazgos.py <lamina> integrada <archivo>`: aplica los reemplazos (guarda `.antes.json`), anota la nota en métricas y registra todo en `M/revision/hallazgos.jsonl`; lo que no es texto va a mano. Graves siempre; menores si toman < 1 min, si no a `pendientes`. Quedan en `datos/<lamina>.hallazgos.json`: el script de armado los vuelve a aplicar al final con `aplicar_hallazgos.py --reaplicar <lamina>`.
4. `--rapido` (atento a «regresión:»). `--final` otra vez solo si hubo graves de dibujo o se tocó el arte o el layout. `aplicar_hallazgos.py --candidatas`: lo repetido en 2 o más láminas es candidato a control automático (avisar a Auxiliares).

## Terminado quiere decir
- [ ] `autocontrol.py` sale con código 0 (validador **OK**, avisos leídos, medir **sin bloqueantes**), y cada nota UX ≥ la de la línea base (CVT: promedio 4,5; por criterio en `M/metricas.json`).
- [ ] Autocontrol completo (`anexo-autocontrol.md`): mecánico y UX a ojo, todo en «sí».
- [ ] La nota mecánica de la revisora ≥ 4,8, la de la línea base. Si alguna nota baja, se explica en `explicacion` (`metricas.py dato …`); sin explicación no está terminada.
- [ ] Métricas anotadas en cada fase y `informe` comparado contra la CVT y el promedio, diciendo qué fase tardó más de lo esperado y por qué.
- [ ] Sin errores de consola. Funciona sin red, salvo las fuentes de Google.
