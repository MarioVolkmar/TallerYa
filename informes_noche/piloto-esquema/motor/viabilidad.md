# Viabilidad: ¿de dónde sale la CVT (fig. 12)? · 16-nov-2026

## (a) ¿Puede el motor dibujar desde `garaje/diagramas.py`?

**Sí, con un adaptador, pero queda lejos del nivel del freno de la v8.** Lo leí sin tocarlo (`P()`, `_cvt`, `_freno_disco`, `dibujar_lamina`, `isometrico.componer`).

Lo que ya trae:
- **Piezas por «puesto»** (`polea_fija`, `rodillos`, `correa`, `zapatas`, `campana`…): 15 en `_cvt`, cada una dibujada en `<g class="pieza" data-puesto>`, en orden de pintura.
- **Ancla y punto del número** de cada pieza (`dibujar_lamina` devuelve `anclas` y `puestos`, en 0..1).
- Líneas de eje y la franja de tornillería sin número.
- **Asignación catálogo → puesto por palabras** (`REGLAS`, `puesto_para`): da gratis la regla «cada número tiene pieza».

El adaptador sería un script de Python que llame a `dibujar_lamina("cvt")` y escriba el JSON del motor:
- el `<g>` de cada puesto como arte, en SVG literal;
- `anc` y `et` a partir de `anclas` y `puestos`, escalados al encuadre.

Unas 150 líneas, sin tocar `diagramas.py`.

Lo que no trae, y el freno de la v8 sí tiene:
1. **No hay posición armada.** Las piezas ya están dibujadas separadas a lo largo del eje («explotadas»). La v8 necesita las dos posiciones y los pasos del desarme.
   - Arreglo barato: dar a cada pieza un corrimiento 3D (cuánto se separó). En isométrico, un corrimiento 3D es una traslación 2D, así que los `pasos` del motor salen de ahí.
   - Esos corrimientos hay que escribirlos a mano: unos 15 vectores.
2. **Es genérico, no de la NMAX.** Es un dibujo «por tipo de sistema, para cualquier marca».
   - Ejemplo: `_freno_disco` tiene **dos pistones** y el caliper de la NMAX tiene uno.
   - En `_cvt`, el número y la forma de rodillos, deslizadores y resortes no salen de la lámina 12. Haría falta revisar cada pieza contra el plano.
3. **Otro estilo.** Isométrico plano de manual técnico (papel claro, colores lisos y sombra suave). La v8 usa un fondo oscuro con degradados, brillos, texturas de fricción y el modo **Transparente**, con carcasas semitransparentes.
   - El motor aguanta los dos estilos, pero dentro del sitio la lámina CVT se vería distinta a la del freno.
   - El modo Transparente con el arte isométrico solo sirve si la campana o la tapa se dibujan aparte.
4. **No trae «Cómo funciona»** (el esquema animado con sus estados), ni las piezas de contexto, ni el dibujo cortado. Eso es arte nuevo en cualquier caso.

**Qué tan cerca queda:** del 100 % de trabajo de dibujo de la v8, `diagramas.py` ahorra cerca del **35-40 %**: piezas con forma razonable, anclas, orden y asignación de números. Falta la fidelidad a la NMAX, la posición armada, el estilo y «Cómo funciona».

## (b) ¿Cuánto de las fichas de la fig. 12 ya existe?

La fig. 12 tiene **33 números** (según `despiece_local/marcas_nmax_bbe4.py`). Las descripciones del catálogo no las pude cruzar: están en la base local y en el PDF, y la lectura de `db.sqlite3` me fue denegada. Por eso la cuenta va por tipo de pieza:
- unas **14 piezas que funcionan** (poleas, rodillos, deslizadores, rampa, buje, correa, polea trasera, resorte de torque, portazapatas, zapatas, resortes, campana, pasadores y retenedor);
- unas **19 de tornillería** (tuercas, arandelas, pines de seguridad, rodamientos, O-rings).

| Campo de la ficha de la v8 | ¿Existe? | De dónde |
|---|---|---|
| nombre | sí | `despiece_glosario.traducir` |
| cat (código, cantidad) | sí | catálogo importado (base) |
| qué es / para qué sirve | sí, en una frase | `despiece_fichas.FICHAS` (unas 10 claves de CVT) y `despiece_guia_mecanica` (los 15 puestos de `_cvt`) |
| síntomas | sí | `senales` |
| cuándo | parcial | `cada_cuanto` y `intervalos/yamaha_nmax_155.json` (solo la tarea `correa-cvt`; rodillos y clutch van «con la correa») |
| dificultad | sí | `dificultad` |
| fallas por causa (desgaste, calor…) | parcial | hay señales y «qué pasa si no se atiende», pero sin causa ni explicación |
| repara o cambia, qué se compra | poco | algunos consejos («se cambian todos») |
| conecta, efectos (cadenas) | poco | «si no se atiende» da una pista |
| certeza y fuentes | no | — |
| datos de la NMAX (peso de rodillos, ancho mínimo de la correa, torques) | no | — |

**Estimado: alrededor del 45 %** del contenido de las fichas de la fig. 12 ya existe, medido por campos y por profundidad.
- En las piezas que funcionan está cerca del 40 %: hay una frase base por campo, pero la v8 escribe de 3 a 5 frases propias de la NMAX y de Medellín.
- En la tornillería, cerca del 70 %, porque `guia_herraje` y el glosario alcanzan.
- Falta escribir de cero lo que hace pedagógica a la v8: causas de falla, la decisión de reparar o cambiar, las cadenas de «Si falla», la certeza con fuentes y «Cómo funciona».

## Recomendación para la CVT

**Mezclar, con el arte nuevo hecho desde cero:**
- **Del código existente:** el inventario de puestos y las palabras clave de `REGLAS` (qué número va con qué pieza); la geometría de `_cvt` solo como boceto de proporciones y orden de armado; y como borrador de cada ficha, `despiece_fichas`, `despiece_guia_mecanica` y `despiece_glosario` (que el validador obligue a completar los campos que faltan).
- **Desde cero, en el estilo de la v8:** el arte de la lámina (de 12 a 15 piezas dibujadas y la tornillería agrupada), las posiciones armadas, los pasos del desarme, «Cómo funciona» (polea que se abre con los rodillos, correa que sube, clutch que agarra la campana) y la parte de las fichas propia de la NMAX.
- **Por qué no solo con `diagramas.py`:** sale más rápido, pero queda genérico, sin posición armada y con otro estilo que el freno. La meta pedida es «el mismo nivel de calidad que el freno».
- **Por qué no todo de cero:** se perderían la asignación automática de números y los textos base, que ahorran tiempo en 33 números.

Además, `diagramas.py` es de la sesión de dibujos: si el motor depende de su salida, cada cambio allá movería esta lámina. Conviene copiar los datos una vez a `datos/nmax-fig12.json` y no leerlo en vivo.
