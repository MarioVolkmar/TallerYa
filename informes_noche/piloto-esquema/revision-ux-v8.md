# Revisión UX v8 y del integrado (rúbrica v2)

Revisora UX · 15-nov-2026 · revisé `v8.html` (= `index.html`, comprobado con `cmp`) e `integrado.html` (armado sobre la v8). Los dos se sirvieron por HTTP local, con la pestaña al frente, en los 6 anchos de `criterios-ux.md`: 360×740, 390×844, 768×1024, 1024×768, 1280×800 y 1440×900. Herramientas: `integracion/medir_distribucion.js` y una prueba de toques más estricta, nueva, en `integracion/medir_toques_estricto.js`. Esa prueba pide que el elemento tocado sea **el número mismo** (`.bola`), no su pieza ni otro control; desplaza el dibujo a la vista y mide también el radio de toque.

## Veredicto
| | Promedio | Criterio más bajo | Bloqueantes | **¿Aprobado?** |
|---|---|---|---|---|
| **`integrado.html` (v8)** | **4,4** | 4 | ninguno | **SÍ** |
| `v8.html` sola | 4,3 | 3,7 (primer pantallazo) | 1: a 1280×800 el dibujo queda cortado por 2 px | no |

Lo que se integra en el sitio es la maqueta de `integrado.html`, y esa **pasa**. La v8 sola tiene un bloqueante de forma en el criterio 9 que no afecta la integración, porque en el integrado el alto del dibujo se ajusta a la pantalla. Se arregla en una línea (ver «Para piloto-esquema»).

## Medidas

### Distribución (`medir_distribucion.js`)
| Ancho | Integrado: dibujo (w×h, % ancho) | Completo / Desarmar a la vista | Apoyo | Columnas (top, w) | v8 sola: dibujo | v8: completo / Desarmar |
|---|---|---|---|---|---|---|
| 360×740 | 300×233, 83 % | sí / sí | 18 % | 1 col, 328 | 300×233 | sí / sí |
| 390×844 | 330×257, 85 % | sí / sí | 16 % | 1 col, 358 | 330×257 | sí / sí |
| 768×1024 | 693×539, 92 % | sí / sí | 14 % | 1 col, 721 | 693×539 | sí / sí |
| 1024×768 | 563×436, 56 % | sí / sí | 16 % | 183/183 · 591 y 370 (ficha fija) | 563×438 | sí / **no** |
| 1280×800 | 651×460, 57 % | sí / sí | 16 % | 183/183 · 679 y 425 (fija) | 681×530 | **cortado 2 px** / **no** |
| 1440×900 | 651×507, 57 % | sí / sí | 14 % | 183/183 · 679 y 425 (fija) | 681×530 | sí / no |

Hueco bajo las columnas a ≥ 1024 px: 1 % (visor) y 0 % (ficha fija) en los dos archivos. No hay desborde horizontal en ningún ancho. El script marca un hueco del 29 al 46 % en la columna del visor a ≤ 768 px, pero ahí hay una sola columna apilada y la rúbrica mide el hueco solo a ≥ 1024. Revisé el DOM: el panel de piezas llena el visor, no hay espacio muerto real.

### Toques (prueba estricta, en el integrado y en la v8 sola)
| Ancho | Armado N | Armado T | Despiece T | Despiece N | Roces a ±9 px | Radio mínimo |
|---|---|---|---|---|---|---|
| 360 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 11,1 px (armado T) |
| 390 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 12,7 px (armado T) |
| 768 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 22,6 px |
| 1024 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 21,7 px |
| 1280 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 19,3 px (integrado) / 22,2 (v8) |
| 1440 | 7/7 | 7/7 | 18/18 | 18/18 | 0 | 21,3 px |

**50/50 en el centro y 0 roces en los 6 anchos**, en los dos archivos.

### Zoom (360×740, integrado)
- Los botones + − ⤢ miden 44 px y van **debajo** del dibujo (su borde superior queda bajo el SVG), así que no tapan números.
- «+» lleva el `viewBox` de 613×477 a 383×298 (×1,6). Con zoom, el SVG toma `esq-ampliado` y `touch-action: none`; sin zoom vuelve a `pan-x pan-y`, y la página se desplaza normal.
- **Arrastre con un dedo** (eventos `pointer` táctiles, 60 px): el encuadre se corre 77 unidades del SVG. **Pellizco con dos dedos**: llega hasta ×4. «⤢» vuelve exacto a `223 140 613 477`.
- Toques con zoom: armado ×1,6 3/3; despiece ×1,6 5/5 y ×2,6 5/5 (solo los números dentro del lienzo), sin roces. Tocar un número con zoom abre su ficha (9 → «Pastillas de freno (juego)»). Al desarmar, el zoom vuelve a ×1 (comprobado).

### El radio mínimo de 11,1 px a 360, ¿baja el criterio 6?
**No, pero queda anotado.** Pasa solo con «Transparente» en el armado, donde dos números internos quedan a unos 22 px uno del otro. Eso es menos que el objetivo de 24 px de WCAG 2.5.8 (AA). Aun así, el criterio 2.5.8 se cumple por la excepción de «control equivalente»: la lista de piezas (chips de 44 px) abre la misma ficha. Además, el zoom ×1,6 lleva ese radio a unos 18 px, y la prueba estricta no encontró ni un roce. En el despiece, el mínimo es de 13,8 px a 360.

## Puntajes (rúbrica v2)

| # | Criterio | Integrado | v8 sola | Base |
|---|---|---|---|---|
| 1 | Claridad del recorrido | 4,5 | 4,5 | Pestañas; dibujo y ficha en el primer pantallazo en computador |
| 2 | Descubribilidad | 4 | 4 | Pista «Toca una pieza», selector «Dibujo» y zoom a la vista |
| 3 | Carga cognitiva | 4 | 4 | Igual que la v7 |
| 4 | Accesibilidad | 4 | 4 | Igual que la v7, más zoom por botones (no solo por pellizco) con `aria-label` |
| 5 | Rendimiento y peso | 4 | 4 | 131 KB el integrado y 108 KB la v8, sin errores de consola |
| 6 | Uso con el pulgar | **4,5** | **4,5** | 50/50, 0 roces en 6 anchos, zoom, barra fija, 44 px (ver la nota del radio) |
| 7 | Consistencia con TallerYa | 4,5 | 4,5 | Cabecera, `.papel`, `.btn`, `.visor-modo`, prefijo `esq-` |
| 8 | Protagonismo del dibujo | 4,3 | 4,3 | Ancho 57 % (5) · alto a 1280: 460 / 530 px (5) · alto a 360: 233 px (3, < 235) |
| 9 | Primer pantallazo | 4,7 | **3,7 ⚠** | Integrado: dibujo y Desarmar a 1280 y a 1024 (5), 390 completo con controles (5), apoyo en el peor caso 16 % (4). v8: **dibujo cortado 2 px a 1280 = bloqueante** (1), 390 (5), apoyo 13 % (5) |
| 10 | Espacio muerto | 5 | 4,7 | Hueco 1 % / 0 %. La ficha vacía del integrado muestra el estado del sistema (5); en la v8, solo instrucciones (4) |
| 11 | Proximidad control–efecto | 4,7 | 4,7 | Ficha fija en computador (5), barra fija en el celular (5), controles en dos filas pegadas al dibujo (4) |
| 12 | Ritmo y alineación | 4,8 | 4,8 | Bordes superiores 183/183 (5), columna mínima 328 px (5), sin desborde (5), espaciados: casi todos de la escala (4) |
| | **Promedio** | **4,4** | **4,3** | |

## Para piloto-esquema (no bloquea la integración)
1. **v8 sola a 1280×800:** el dibujo termina en 802 px y «Desarmar» queda fuera de la pantalla, tanto a 1024 como a 1280. Hay que limitar el alto del lienzo a la pantalla, como en el integrado: `max-height: calc(100vh - <alto de cabecera + pestañas + fila de controles>)`, con el ancho siguiendo la proporción. Para verificarlo, en `medir_distribucion.js` a 1280×800 y 1024×768 debe salir `completo:true` y `desarmarVisible:true`.
2. **Alto del dibujo a 360:** mide 233 px y el 4 del criterio 8 pide 235. Se gana con 2 px menos de relleno del lienzo, o encuadrando `VB_ARM` un poco más apretado a los lados.
3. Opcional: a 360, con «Transparente» en el armado, separar unos px los dos números internos más cercanos para que el radio llegue a 12 px (24 px de diámetro, el objetivo de WCAG 2.5.8).

## Qué mostrarle al usuario
`integrado.html` abierto desde la carpeta del proyecto, a 1280 px y en el celular (360/390). En computador: el dibujo grande con la ficha fija al lado, que sin pieza elegida muestra el estado del freno en el plan. En el celular: tocar un número muestra la barra fija «Ver ficha»; probar + − ⤢, el arrastre con un dedo y el pellizco.
