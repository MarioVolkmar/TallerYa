# Revisión mecánica: fig. 10 de la NMAX 155 BBE4, «Cárter y tapones del aceite»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig10.json`: 32 números, 15 pasos con `sujeta`, «Cómo funciona» de 5 pasos, 3 cadenas, «Cuándo» y las fichas. Comparé los datos marcados «Seguro» con el manual B6Y4. Solo leí el texto de las páginas necesarias con pymupdf, sin modificar nada: 9-12 y 9-13 (PDF 73-74), 9-14 y 9-15 (PDF 75-76), especificaciones 11-1 (PDF 105) y `yamaha_nmax_155.json`.

## Datos «Seguro» comparados con el manual

| Dato | Manual | Estado |
|---|---|---|
| Perno A con junta nueva, a 20 N·m | p. 9-13 | ✔ |
| Perno de la transmisión final con junta nueva **aceitada**, a 20 N·m | p. 9-15: «junta nueva… aplíqueles aceite»; p. 9-14: «20 N·m» | ✔ |
| Varilla sin enroscar | p. 9-12: «introdúzcala… (sin enroscarla)» | ✔ |
| 0,90 L de aceite de motor y 0,10 L de la transmisión final | p. 11-1: «Cambio de aceite: 0.90 L»; transmisión final: «Aceite de motor SAE 10W-40 tipo SG o superior, 0.10 L» | ✔ |
| Transmisión final: a los 1.000 km, luego cada 12.000 km o 1 año | plan `aceite-caja` (cuadro, pp. 9-2 a 9-6): 12.000 km o 365 días, primer cambio a los 1.000 km | ✔ |
| Fugas de la caja antes de cada uso | p. 9-14: «Antes de cada utilización debe comprobar si la caja… pierde aceite» | ✔ |
| Calentar rodando y no ensuciar la llanta ni el freno | p. 9-14, paso 1, y p. 9-15: «no caiga aceite en el neumático o en la rueda» | ✔ (paso 4) |

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Hay 32 números con nombre y cantidad del catálogo. `sujeta` es coherente. Las tapas 18 y 24 y la silueta del cárter son aproximadas, y está declarado. |
| 2 | Exactitud mecánica | **5** | Los dos aceites están separados (motor y transmisión final), la medición con la varilla es la del manual, el retén del eje trasero bota aceite hacia el disco (coherente con la fig. 24) y el respiradero tapado empuja aceite por el retén. Abrir el cárter es trabajo de taller. |
| 3 | Pedagogía | **5** | «Dos aceites que no se mezclan» es el mensaje justo para el dueño. |
| 4 | Congruencia | **4** | Los intervalos coinciden con el plan. **Pero hay dos piezas con «tapa 2» en el nombre** (cambio 1). |
| 6 | Reglas | **5** | Los torques solo están donde el manual los da. Las tapas de los tornillos van sin dato. |

**Promedio: 4,6. Visto bueno: SÍ.** No hay errores mecánicos, y el cambio 1 es de nombres. Con los cambios 1 y 2, la nota sube a 4,8.

## Cambios recomendados
1. **Un solo nombre por pieza** (autocontrol, pregunta 3 [S]). La 18 se llama «Tapa de atrás (tapa 2)» (`nmax-fig10.json:142` y paso 11, `:1028`) y la 24 «Tapa 2 del cárter» (`:148`). Las dos dicen «tapa 2».
   - Por lo que lleva la 18 (el retén del eje trasero, y que hay que vaciar el aceite de la transmisión final antes de sacarla), es la **tapa de la caja de la transmisión final**. Llamarla así y dejar «tapa 2 del cárter» solo para la 24.
2. **Retén del cigüeñal (9), paso 15** (`:1088`). Hoy sale después de abrir el cárter (pasos 14 y 15) y figura como «difícil». En los motores de scooter con CVT, el retén del lado del variador se puede cambiar **sin abrir el cárter**, quitando el variador (fig. 12).
   - Si la grilla lo confirma, decir: «se cambia desde el lado de la CVT, sin abrir el motor (trabajo de taller)».
   - Si no, marcarlo como aproximado. Esto cambia el costo que se le dice al dueño.
3. **Menor:** los pasadores 2, 6, 21 y 26 tienen `decision: "repara"`. Un pasador de centrado no se repara: se reutiliza. Cambiar la etiqueta a «reutiliza».

## Fig. 7: los dos retoques
✔ En «Cuándo», el tamiz quedó separado: «Cada 12.000 km», marcado «Seguro», y «Siempre que saques el tapón B», marcado «Práctica de taller». ✔ El paso 3 termina con «Prende el motor un par de minutos, mira que no gotee, apágalo y revisa el nivel con la varilla».

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| F1 | Nombres de las tapas | ✔ La 18 es la «Tapa de la caja de la transmisión final» y la 24 la «Tapa del respiradero». Las juntas, los pasadores y los tornillos de cada una llevan el nombre de su tapa, y «tapa 2» ya no aparece. |
| F2 | Retén del cigüeñal (9) | ✔ Se acepta que vaya del lado del **alternador**. Lo que importaba de mi sugerencia era que se cambia sin abrir el cárter, y eso queda igual: la creadora lo ubicó con la grilla. Del lado del alternador, el retén queda detrás del rotor, que sale con un extractor y es trabajo de taller. Está marcado «ap» en la certeza, y el paso 14 sale **antes** de abrir las mitades. |
| F3 | Pasadores | ✔ Los pasadores 2, 6, 21 y 26 tienen `decision: "reutiliza"`. |

Retoque que no bloquea: la ficha 9 tiene `dif: "media"`, pero el texto dice «trabajo de taller», porque el rotor sale con un extractor. Cambiar `dif` a «taller» y agregar «con extractor» en el paso 14.

**Nota final: 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **Visto bueno: SÍ.**
