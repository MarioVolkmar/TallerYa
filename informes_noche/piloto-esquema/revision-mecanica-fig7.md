# Revisión mecánica: fig. 7 de la NMAX 155 BBE4, «Bomba de aceite y drenaje»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig7.json`: 6 números, 5 pasos con `sujeta`, «Cómo funciona» de 5 pasos, 3 cadenas, «Cuándo» y las fichas. Comparé los datos marcados «Seguro» con el **manual B6Y4**. Solo leí el texto de las páginas necesarias con pymupdf, sin modificar nada: páginas impresas 9-12 y 9-13 (PDF 73-74), el cuadro de mantenimiento (PDF 67) y `yamaha_nmax_155.json`.

## Datos «Seguro» comparados con el manual

| Dato | Manual | Estado |
|---|---|---|
| Tapones A y B a 20 N·m | p. 9-13: «Perno de drenaje… A: 20 N·m» y «B: 20 N·m» | ✔ |
| 0,90 L | p. 9-13: «Cantidad de aceite: 0.90 L» | ✔ Es la cantidad del cambio. La NMAX no lleva filtro de papel, solo el tamiz, así que no hay un dato «con filtro» que se pueda confundir. |
| 10W-40, API SG o superior, JASO MA o MB | p. 11-1 (`yamaha_nmax_155.json`: «SAE 10W-40, API SG o superior, JASO MA o MB; 0,90 L») | ✔ |
| Junta tórica nueva en B y junta nueva en A | p. 9-13: «una junta tórica nueva y el perno… B» y «perno… A y su junta nueva» | ✔ |
| Tamiz lavado con disolvente | p. 9-13: «Limpie el tamiz… con disolvente y… compruebe si está dañado» | ✔ |
| Al sacar B caen la junta, el resorte y el tamiz | p. 9-12: «la junta tórica, el muelle de compresión y el tamiz… se soltarán» | ✔ Lo dice el paso 1. |
| Cambio a los 1.000 km y luego cada 6.000 km | cuadro e indicador de cambio de aceite; plan de la NMAX | ✔ |
| Tamiz cada 12.000 km | cuadro, fila 21: «Tamiz de aceite del motor · Limpiar», en 3 columnas; plan: cada 12.000 km | ✔ |
| Aviso de quemaduras | paso 1 y «Cómo funciona», paso 5 | ✔ |

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Hay 6 piezas y `sujeta` es correcto: el tapón B sujeta la junta tórica, el resorte y el tamiz, y los tornillos 2 sujetan la bomba. El dibujo de la bomba interna es aproximado. |
| 2 | Exactitud mecánica | **5** | El desarme sigue el procedimiento del manual: tapón de llenado, B, resorte, tamiz, perno A, y al armar juntas nuevas, 20 N·m y 0,90 L. La bomba como trabajo de taller, porque hay que abrir el motor, y que se cambia completa, es correcto. «Cómo funciona» está bien (tamiz → bomba → cigüeñal, biela, culata → cárter). |
| 3 | Pedagogía | **5** | Es corta y clara. Las 3 cadenas son reales: aceite viejo y tamiz tapado, junta reutilizada, tapón apretado de más y rosca barrida. |
| 4 | Congruencia | **5** | Coincide con el plan de la NMAX y con el manual. |
| 6 | Reglas | **5** | Los torques son del manual (no inventados), las fuentes tienen página y la tecnología es la correcta (sin filtro de papel). |

**Promedio: 4,8. Visto bueno: SÍ.** No hay errores mecánicos.

## Retoques que no bloquean
1. **«Cuándo», fila del tamiz:** «Cada 12.000 km, y siempre que saques el tapón B». La primera parte es del manual. La segunda es práctica de taller, aunque buena: el tamiz sale solo con el tapón. Separarlas o marcar la segunda como práctica.
2. **Paso 3:** mezcla el perno A, que es de la lámina 10, con lo de esta lámina. Está bien que lo diga, porque el manual los pide juntos. Basta con aclarar que **el aceite se echa después de montar los dos y se revisa el nivel con la varilla tras prender un par de minutos** (p. 9-13, pasos 8 y 9). Así no se queda solo con «0,90 L».
