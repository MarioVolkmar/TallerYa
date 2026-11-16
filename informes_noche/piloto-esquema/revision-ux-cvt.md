# Revisión UX: piloto de la CVT NMAX (lámina 12, motor nuevo) · rúbrica v2

Revisora UX · 16-nov-2026 · revisé `motor/cvt.html` (motor `esquema.js`/`esquema.css` + `datos/nmax-fig12.json` y `-arte.js`), servido por HTTP en el puerto 8010, en los 6 anchos de `criterios-ux.md`. El motor y los datos cambiaron mientras revisaba (`esquema.js` 01:33, `esquema.css` 01:35, JSON y arte 01:45). **Volví a medir todo con esa versión** y los números no cambiaron. Para comparar, también abrí `motor/freno.html` a 1280×800.

Para medir usé los scripts adaptados a las clases `esq-` (nuevos, en `integracion/`):
- `medir_distribucion_motor.js`;
- `medir_toques_motor.js`: la prueba estricta pide que el toque caiga en **el número mismo** y revisa los roces a ±9 px;
- `medir_densidad_motor.js`: distancia entre números en el despiece completo;
- `medir_lamina_motor.js`: corre los tres.

## Veredicto
| Promedio | Criterio más bajo | Bloqueantes | **¿Aprobado?** |
|---|---|---|---|
| **4,3** | 3,7 (primer pantallazo) | 1: a 1280×800 el dibujo se corta (termina en 801 px) | **NO** |

El bloqueante viene del **motor**, no de la lámina: `freno.html` tiene el mismo dibujo de 682×531 que termina en 801 px. El motor heredó el alto de la v8 sola y no el arreglo del integrado. Con ese arreglo, la CVT queda en 4,4 y aprobaría. Todo lo que pidieron revisar con cuidado pasa: la densidad, los toques y «Cómo funciona». La lista de 33 chips en el celular es lo más flojo, pero no es bloqueante.

## Medidas

### Distribución
| Ancho | Dibujo (w×h) | % ancho (sobre las columnas) | Completo / Desarmar a la vista | Apoyo | Columnas (top / w / hueco) |
|---|---|---|---|---|---|
| 360×740 | 305×237 | 85 % | sí / no (llega a 741 px) | 14 % | 1 col, 328 |
| 390×844 | 335×261 | 86 % | sí / sí | 13 % | 1 col, 358 |
| 768×1024 | 694×540 | 90 % | sí / sí | 9 % | 1 col, 721 |
| 1024×768 | 565×439 | 58 % | sí / **no** | 11 % | 145/145 · 591 (1 %) y 369 (fija, 0 %) |
| 1280×800 | 682×531 | 58 % | **cortado 1 px** / **no** | 11 % | 145/145 · 709 (1 %) y 443 (fija, 0 %) |
| 1440×900 | 682×531 | 58 % | sí / no («Desarmar» en 873–917) | 10 % | igual que a 1280 |

No hay desborde horizontal en ningún ancho y la consola no muestra errores.

Sobre el % de ancho: el script lo calcula sobre el ancho de la ventana (47–55 %) porque la página no tiene `main`. Lo recalculé sobre el ancho real del contenido, que es la suma de las columnas.

### Toques (prueba estricta, en los 6 anchos)
| Ancho | Armado N | Armado T | Despiece T | Despiece N | Roces a ±9 px | Radio mínimo |
|---|---|---|---|---|---|---|
| 360 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 9,6 px (despiece) · 9,8 (armado T) |
| 390 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 10,6 px |
| 768 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 21,3 px |
| 1024 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 17,2 px |
| 1280 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 21,3 px |
| 1440 | 8/8 | 8/8 | 33/33 | 33/33 | 0 | 21,3 px |

**82/82 en el centro y 0 roces en los 6 anchos.**

### Densidad de números en el despiece (33 números)
| Ancho | Distancia mínima entre centros | Pares a < 24 px | Disco / número |
|---|---|---|---|
| 360 | **19,0 px** (21–20) | **9**: 2-1, 14-15, 15-16, 19-22, 22-21, 21-20, 8-29, 30-31, 31-32 | 18 px / 16 px |
| 390 | 20,9 px | 6 | 18,3 / 16,7 |
| 768 | 43,3 px | 0 | 18,4 / 16,7 |
| 1024 | 35,2 px | 0 | 17,6 / 16 |
| 1280 / 1440 | 42,5 px | 0 | 18 / 16 |

A 360 los discos de 18 px quedan casi tocándose en tres grupos: 20-21-22 (y el 19), 30-31-32 y 14-15-16. Se leen, pero apretados. Ningún número queda fuera del lienzo.

Con zoom, ese apretón desaparece:
- **×1,6:** 16/16 números tocables dentro del lienzo, 0 roces, mínimo de 34 px entre centros.
- **×2,6:** 4/4, a 91 px.

El zoom funciona igual que en la v8:
- Los botones van debajo del dibujo y la página se desplaza normal sin zoom (`touch-action: none` solo con zoom).
- Un dedo arrastra (60 px corren el encuadre 158 unidades).
- «⤢» vuelve al encuadre completo.
- Tocar el 12 con zoom abre «Polea fija trasera» y muestra la barra fija «12 Polea fija trasera · Ver ficha».

### Lista de piezas (34 chips: 33 y la tapa, que va en otra lámina)
- **360 px:** es un **carrusel de una sola fila de 6.775 px**, con **un solo chip entero a la vista** (307 px de ancho útil). No hay degradado, contador ni pista de que la lista sigue. Para llegar al 28 hay que deslizar unas 20 pantallas. Los chips miden 44 px de alto, así que se tocan bien.
- **1280 px:** la lista se reparte en varias filas y forma un bloque de 658 px bajo el dibujo (empieza a 1.003 px). Es largo, pero se recorre con la vista.

### «Cómo funciona» en el celular (360×740)
**Se entiende.** Hay un tacómetro (1.600 rpm), las dos poleas con la correa y la leyenda «Relación corta», un corte del variador (fija 6, móvil 1, placa 3, rodillo 2, correa, cigüeñal) y el clutch visto de frente (campana 24 y zapatas 8). Abajo dice «Suelto: la rueda no gira».
- Son 6 pasos: ralentí → engancha → relación corta → salen los rodillos → crucero → subida o acelerón.
- La letra mínima del dibujo mide 12,1 px y el texto del paso 16 px, con `aria-live="polite"`.
- Los botones Reproducir ◀ ▶ miden 44 px.

El problema es que no cabe todo junto: el dibujo mide 573 px de alto, los controles 44 px y el texto entre 136 y 210 px. Eso suma más que los 740 de la pantalla, así que en los pasos 4 y 6, que son los de texto largo, el texto queda cortado y hay que bajar para leerlo mientras el dibujo sale de la vista. Además, la marca naranja de la campana roza el título «El clutch, de frente».

### Otros
- **Peso:** 147 KB repartidos en 5 archivos (página, motor y datos); el archivo único `prueba-nmax-fig12.html` pesa 131 KB.
- **Desarmar:** 15 pasos a 1,3 s (≈ 20 s), con pausa.
- **Largo de las pestañas a 360:** Piezas 1.333 px, Si falla 3.044 px, Cuándo 1.886 px.
- **Ficha abierta («Rodillos del variador»):** 1.093 px, con el bloque «Para qué sirve…» plegado.
- **Sin pieza elegida, la ficha** solo da instrucciones: «Toca una pieza del dibujo…».

## Puntajes (rúbrica v2)
| # | Criterio | CVT | Base |
|---|---|---|---|
| 1 | Claridad del recorrido | 4,5 | Igual que la v8: pestañas, y dibujo y ficha en el primer pantallazo en computador |
| 2 | Descubribilidad | 4 | Pista «Toca una pieza», selector «Dibujo», zoom a la vista. En el celular, la lista de 33 no deja ver que sigue |
| 3 | Carga cognitiva | 4 | «Cómo funciona» en 6 pasos claros; desarme de 15 pasos con pausa. Lo resta la densidad a 360 |
| 4 | Accesibilidad | 4 | `aria-label` en cada número, Enter/Espacio, `aria-live`, botones de 44 px, zoom por botones |
| 5 | Rendimiento y peso | 4 | 147 KB, sin errores de consola |
| 6 | Uso con el pulgar | **4** | 82/82 y 0 roces en 6 anchos, zoom, barra fija. Baja de 4,5 a 4 porque el radio a 360 es de 9,6 px, hay 9 pares a < 24 px, y el control equivalente (la lista) cuesta mucho en el celular |
| 7 | Consistencia con TallerYa | 4,5 | Igual que la v8 (`esq-`, tokens, Oswald/Archivo, `.visor-modo`) |
| 8 | Protagonismo del dibujo | 4,7 | Ancho 58 % (5) · alto a 1280: 531 px (5) · alto a 360: 237 px (4) |
| 9 | Primer pantallazo | **3,7 ⚠** | **Dibujo cortado a 1280 = bloqueante (1)** · 390 completo, con «Desarmar» (5) · apoyo en el peor caso 13 % (5) |
| 10 | Espacio muerto | 4,7 | Hueco 1 % / 0 % (5) · ficha vacía con solo instrucciones (4) · sin navegación secundaria ancha (5) |
| 11 | Proximidad control–efecto | 4,7 | Ficha fija en computador (5) · barra fija en el celular (5) · controles en 2 filas pegadas al dibujo (4) |
| 12 | Ritmo y alineación | 4,8 | Bordes superiores 145/145 (5) · columna mínima 328 px (5) · sin desborde (5) · espaciados casi todos de la escala (4) |
| | **Promedio** | **4,3** | Con el P1 arreglado, el criterio 9 pasa a 5 y el promedio a **4,4** |

## Qué corregir

### P1. Bloqueante, en el motor (`esquema.css`), y arregla también el freno
A ≥ 960 px hay que limitar el alto del lienzo a la pantalla, como en el integrado, para que se vean el dibujo completo y «Desarmar».
- **Cuidado con el criterio 8:** hoy el dibujo empieza a 270 px y los controles ocupan 116 px debajo. Si solo se limita el alto, a 1280×800 el dibujo queda en unos 405 px y baja a 3 en «alto a 1280» (pide 420 o más).
- **Recomendado:** en computador, juntar las dos filas de controles en una sola (selector «Dibujo» + zoom + Armar ◀ ▶ + Números, unos 60 px) y usar `max-height: calc(100vh - 270px - 72px)`. A 1280×800 eso da unos 458 px.
- **Otra opción:** subir el dibujo recortando la cabecera.
- **Para verificarlo,** `medir_lamina_motor.js` a 1280×800 y 1024×768 tiene que dar `completo:true`, `desarmar:true` y un alto de 420 o más a 1280.

### P2. Lista de 33 piezas en el celular
Hoy es un carrusel de 6.775 px con un solo chip a la vista. Hay tres opciones, de mejor a mínima:
- **(a)** A < 768 px, una rejilla de números: chips de 44×44 solo con el número, 7 por fila, que dan 5 filas y unos 260 px. Al tocar uno, el nombre sale en la barra fija y la ficha se abre como hoy.
- **(b)** Agrupar por conjunto (variador, correa, clutch, transmisión final), cada grupo con su título y su carrusel corto.
- **(c)** Como mínimo, un degradado en el borde derecho y un contador («1–2 de 34»).

### P3. Densidad del despiece a 360 (no bloquea)
Hay que separar las posiciones finales en el celular de los grupos 20-21-22 (y el 19), 30-31-32, 14-15-16, el 1-2 y el 8-29, para llegar a una distancia mínima de 24 px entre centros (hoy 19). La prueba estricta no encontró roces y el zoom lo resuelve, así que es solo para que se lea mejor.

### P4. «Cómo funciona» a 360 (no bloquea)
- Que el texto del paso se vea junto al dibujo: o el texto arriba del dibujo, o los cortes del variador y del clutch más bajos (hoy el dibujo mide 573 px), para que dibujo, controles y texto quepan en 740 px.
- Separar la marca naranja de la campana del título «El clutch, de frente».

### Opcional
- A 360 «Desarmar» queda 1 px bajo el borde al llegar (741/740). No lo mide la rúbrica, pero se arregla solo si el P4 o el ajuste de alto que está en curso ganan unos px.
- La ficha vacía podría mostrar el estado de la CVT en el plan (la correa a los 18.000 km, el indicador V-BELT), como hace el integrado del freno, y subiría a 5.
- Si piloto-esquema cambia el alto a 360, hay que volver a medir solo el criterio 8 (hoy 237 px = 4) y el 9 a 390.

## Verificación de los arreglos (16-nov-2026)
Volví a medir `cvt.html` y `freno.html` sobre el motor corregido (`--esq-alto` y una sola fila de controles desde 960 px; rejilla de números hasta 700 px), en los 6 anchos, con `medir_lamina_motor.js`. La consola no muestra errores.

### P1: primer pantallazo en computador (antes bloqueante), **resuelto**
| Ancho | CVT: dibujo (w×h) · completo · Desarmar | Freno: dibujo (w×h) · completo · Desarmar |
|---|---|---|
| 1024×768 | 563×379 · sí · **sí** | 563×421 · sí · **sí** |
| 1280×800 | 681×**453** · sí (termina en 725) · **sí** | 681×453 · sí · **sí** |
| 1440×900 | 681×530 · sí · **sí** | 681×530 · sí · **sí** |

A 1280 px, «Dibujo», «Desarmar», ◀ ▶ y «Números» quedan en una sola fila a 740 px, pegada al dibujo. En computador el zoom no aparece; en el celular sigue (44 px, bajo el dibujo). A 1024 px la CVT mide 379 px de alto porque su lámina es más apaisada, y la rúbrica no mide el alto a ese ancho.

### P2: lista de piezas en el celular, **resuelta**
Ahora es una rejilla de 6 columnas: 296 px de alto en la CVT y 200 px en el freno a 360. No tiene desplazamiento horizontal (`scrollWidth` 306 = ancho útil), los botones miden 46×44 px como mínimo y cada uno tiene `aria-label` con número y nombre. Al tocar el 21 aparece la barra fija «21 Rodamiento del eje de la polea fija · Ver ficha» a la vista. A partir de 768 px la lista vuelve a los chips con nombre.

### Pasada de toques (prueba estricta)
| Ancho | CVT (armado N/T · despiece T/N) | Radio mín. | Freno | Radio mín. |
|---|---|---|---|---|
| 360 | 8/8 · 8/8 · 33/33 · 33/33 | 9,4 px | 7/7 · 7/7 · 18/18 · 18/18 | 11,4 px |
| 390 | 8/8 · 8/8 · 33/33 · 33/33 | 10,5 | 7/7 · 7/7 · 18/18 · 18/18 | 13 |
| 768 | 8/8 · 8/8 · 33/33 · 33/33 | 21,3 | 7/7 · 7/7 · 18/18 · 18/18 | 22,6 |
| 1024 | 8/8 · 8/8 · 33/33 · 33/33 | 15,2 | 7/7 · 7/7 · 18/18 · 18/18 | 20,9 |
| 1280 | 8/8 · 8/8 · 33/33 · 33/33 | 18,2 | 7/7 · 7/7 · 18/18 · 18/18 | 19 |
| 1440 | 8/8 · 8/8 · 33/33 · 33/33 | 21,2 | 7/7 · 7/7 · 18/18 · 18/18 | 22,2 |

**0 roces a ±9 px en los dos y en los 6 anchos, y ningún número fuera del lienzo.**

En el despiece de la CVT a 360 sigue habiendo 9 pares de números a menos de 24 px (el mínimo, 19 px). Ahora pesa menos, porque el control equivalente (la rejilla) es cómodo. En el freno el mínimo es de 27,6 px y no hay pares a menos de 24.

Los nombres de los sellos ahora son «14: Sellos de la polea móvil trasera» y «15: … (segundo par)».

### Puntajes que cambian (CVT)
| # | Criterio | Antes | Ahora | Por qué |
|---|---|---|---|---|
| 2 | Descubribilidad | 4 | 4,5 | Las 33 piezas se ven de un vistazo en el celular |
| 6 | Uso con el pulgar | 4 | 4,5 | El control equivalente ahora es una rejilla de 44 px, toda a la vista |
| 8 | Protagonismo del dibujo | 4,7 | 4,3 | Ancho 58 % (5) · alto a 1280: 453 px (4: pide 460 para el 5) · alto a 360: 236 px (4) |
| 9 | Primer pantallazo | 3,7 ⚠ | **5** | Dibujo y «Desarmar» a 1280 y a 1024 (5) · 390 completo (5) · apoyo en el peor caso 13 % (5) |
| 11 | Proximidad control–efecto | 4,7 | 4,8 | Una fila en computador (5); en el celular sigue en varias filas |

**Promedio de la CVT: 4,5 (53,6/12). Todos los criterios están en 4 o más y no hay bloqueantes: APROBADA.**

**Freno sobre el motor:** las mismas medidas de distribución que la CVT, con toques más holgados (radio mínimo de 11,4 px y ningún par a menos de 24 px). Recalculé con la rúbrica v2 solo lo que cambió y da **4,5: APROBADO**. No volví a revisar su «Cómo funciona» ni sus fichas, que vienen de la v8 ya revisada.

### Queda pendiente (no bloquea)
- **«Cómo funciona» de la CVT a 360:** el dibujo (573 px), los controles y el texto del paso no caben juntos en la pantalla. Además, la marca naranja de la campana roza el título «El clutch, de frente». Era opcional y no se hizo.
- **Densidad del despiece de la CVT a 360:** grupos 20-21-22, 30-31-32 y 14-15-16.
- **Alto a 1280:** el dibujo mide 453 px y le faltan 7 px para el 5 del criterio 8.
- **«Desarmar» a 360:** sigue bajo el borde al llegar, en los dos. La rúbrica no lo mide.
