# Lámina 1 de 5 · Crypton FI 115 (BF24) · freno delantero (fig. 25)

Página: `motor/crypton-freno.html` · archivo único: `motor/prueba-crypton-freno.html` · hermana: `nmax-fig22` (receta 3b, otra numeración). El freno es de disco y no tiene ABS.

## Tiempo (metricas.py, minutos de reloj)
| fase | real | presupuesto |
|---|---|---|
| catálogo | 2,0 | 1,5 ⚠ |
| dibujo + contenido | 5,0 | 4 ⚠ |
| verificación (validación 1 + mediciones 2) | 3,0 | 2,5 ⚠ |
| revisión (correcciones) | 1,0 | 1,5 |
| espera de la revisora (aparte) | 3 | — |
| **Total con revisión** | **13** | 10 (faltaron 3) |

- Mediciones completas: **1** (`--final`): sin bloqueantes, medible 4,8.
- Previa: 1. `regresion.py`: OK (32 s).
- Ninguna fase llegó al corte (✋).

## Tokens
- Creación: unos 175 k de contexto (de ~45 k a 220 k; 22 % de la ventana). Es una estimación, porque la sesión venía de otra tarea.
- Revisora: 103,6 k.

## Notas
- **Medible:** 4,8 (6: 4,5 · 8: 4,7 · 9: 5 · 10: 5 · 11: 4,8 · 12: 4,8).
- **A ojo** (criterios UX 1, 2, 3, 4, 5 y 7): 5, 4, 5, 4, 4, 5, promedio 4,5.
- **Criterio 6** (toques): aprueba. Hay un aviso: 1 pieza con área de toque de 23 px a 360.
- **Revisora:** mecánica 3,9 y UX 3,6, **antes de corregir**. Las dos fallas graves eran de remapeo y ya están corregidas. No hubo segunda revisión.

## Hallazgos (7)
- **Graves (3):**
  1. Los enlaces `[[n|…]]` se remapearon dos veces y abrían la ficha equivocada.
  2. Los ids de las cadenas «Si falla» seguían con la numeración de la NMAX.
  3. El paso de cambio de pastillas no traía el torque ni el aviso de bombear la manigueta.
- **Menores (4):**
  - meter el pistón con el purgador abierto (p. 6-26);
  - dos fichas con doble nombre («soporte» / «guía» de las pastillas);
  - la palabra «racor» (jerga).
- **Cómo se corrigieron:** 5 por script (`aplicar_hallazgos.py`) y 2 a mano, en el script de armado (los dos graves de remapeo).
- **Falsos positivos de los controles automáticos (3):**
  - el validador marca «Yamaha» como rastro de otra moto en una lámina Yamaha;
  - marca «la lámina dice ABS» aunque el texto dice «sin ABS»;
  - marca «junta» como sinónimo de «empaques» cuando es el verbo («la grasa junta polvo»).
- **Rastros que ningún script atrapó:** «lámina 22» en `cabeza.cinta` y «(lámina 18/26)» en los rótulos del arte. Los encontré mirando la captura de la previa.

## Qué falló (con su sección de la skill)
1. **Paso 1, extractor:** en el catálogo Yamaha Colombia (bilingüe), `extraer_catalogo.py` junta las columnas en español y en inglés en `descripcion` («PLACA ACCESORIA PLATE, FITTING»), y los nombres sugeridos salieron mal. Los separé a mano solo en la fig. 25, con el inglés en `descripcion` y el español en `es`.
2. **Paso 3b, receta con otra numeración:** no avisa que el mapa `N` no debe aplicarse dos veces. Yo remapeé las fichas y después todo el JSON otra vez. Tampoco dice que los ids de `cadenas[].p[][0]` son texto suelto y no enlaces, así que hay que remapearlos aparte.
3. **Paso 3b, búsqueda de rastros:** el patrón `lámina \d+` falla con `grep -E`, que no entiende `\d`. Hay que usar `[0-9]`. Además la skill no dice que se busque también en el `-arte.js` (los rótulos del contexto) y en `cabeza.cinta`.
4. **Reglas fijas, leer poco:** `Read` no puede abrir PDF (falta pdftoppm), cosa que la skill ya dice. Además `pymupdf.open` con rutas `/c/...` falla desde Python en Windows: hay que usar `C:/...`.

## Cambios que propongo (no aplicados)
- `extraer_catalogo.py`: detectar las tablas bilingües (dos columnas de descripción) y guardar `descripcion` en inglés y `es` en español.
- Paso 3b: agregar «aplica `N` una sola vez por campo; los ids de `cadenas[].p[][0]`, `sujeta`, `ocultas`, `carcasas` y `v2.grupos` se remapean aparte» y usar el patrón `l[aá]mina [0-9]+|NMAX|ABS` sobre el JSON y el arte.
- Validador:
  - no tratar la marca de la propia moto como rastro;
  - no tomar «sin ABS» como mención de ABS;
  - revisar `cabeza.cinta` y los rótulos `esq-ctx-txt` del arte contra la figura del catálogo;
  - comprobar que cada `[[n|texto]]` nombre a su pieza: la primera palabra larga del texto debe aparecer en `fichas[n].nombre`. Ese chequeo habría atrapado los dos graves sin la revisora.
- La regla de la revisora en la skill da los índices de página del PDF corridos en uno: la página impresa N está en el índice N−1. Conviene aclararlo en la plantilla del encargo.
