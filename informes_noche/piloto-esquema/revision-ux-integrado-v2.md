# Revisión UX: integrado v2 (distribución)

15-nov-2026 · se califica con la rúbrica v2 (`criterios-ux.md`), que suma 5 criterios de distribución. Las medidas salen de `integracion/medir_distribucion.js`, con `integrado.html` servido por HTTP local.

## Qué cambió
- **Base nueva:** el integrado se arma ahora sobre la **v7** aprobada. Antes se armaba sobre la v3. El generador (`integracion/armar_integrado.py`) toma el escenario, las fuentes y la barra fija de `v7.html` sin editarla. La versión anterior queda en `integrado-v3.html`.
- **Sistemas en un desplegable** («Sistema: Frenos › Caliper delantero · Esquema ▾») junto al título, en vez de una columna de 256 px. Es la misma lista de la barra lateral del sitio. Se cierra con Escape o al tocar fuera.
- **Dos columnas en vez de tres:** el dibujo y la ficha, con la ficha fija bajo la cabecera del sitio. El alto de la ficha nunca se sale de la pantalla.
- **El dibujo usa el alto disponible** (lo calcula el JS): queda completo y con sus controles a la vista en 1024×768, 1280×800 y 1440×900.
- **Los controles del dibujo van en una sola fila** en computador: Normal | Transparente, Desarmar, ◀ ▶ y Números. La pista «Toca una pieza» pasa a la línea del paso. En el celular queda como en la v7.
- **La ficha vacía muestra el estado del freno en el plan** (pastillas, líquido y mangueras), una invitación a tocar un número y «Talleres que hacen frenos». Antes era un párrafo solo en una columna alta.
- **Menos texto arriba:** las migas y la marca «Muestra local» van en una sola línea, y la explicación completa se movió al pie. En el celular y hasta 1199 px se oculta el título del visor, porque repetía lo que ya dice el selector (sigue disponible para lectores de pantalla).
- **Choques de nombres con el sitio, corregidos.** Cuatro clases del piloto ya existen en `tallerya.css` con otro uso, y rompían el esquema:
  - `.visor`: en el sitio es la caja del 3D, de alto fijo. Cortaba el dibujo.
  - `.interruptor`: en el sitio es un switch de 41 px. Aplastaba «Números».
  - `.paso`: en el sitio es un circulito de 1,2 rem.
  - `.leyenda`: en el sitio es una fila flex.

  El generador las renombra con el prefijo `esq-` y acota al esquema la regla `button{}` del piloto. **Para la integración real:** todo lo del esquema debe llevar el prefijo `esq-`.

## Medidas: antes y después

| Medida | Antes (v3, 1280×800) | **v2 · 1280×800** | **1024×768** | **1440×900** | **768×1024** | **390×844** | **360×740** |
|---|---|---|---|---|---|---|---|
| Dibujo (ancho × alto) | 481 × 374 | **653 × 461** | 565 × 438 | 653 × 508 | 694 × 540 | 331 × 258 | 301 × 235 |
| Ancho del dibujo / contenido | 42 % | **57 %** | 56 % | 57 % | 92 % | 85 % | 84 % |
| Dibujo completo en el primer pantallazo | no (corta en 832) | **sí** | sí | sí | sí | sí | sí |
| «Desarmar» a la vista sin bajar | no | **sí** | sí | sí | sí | sí | sí |
| Alto de los textos de apoyo | 41 % | **16 %** | 15 % | 14 % | 13 % | 16 % | 18 % |
| Hueco por columna | sistemas 55 %, ficha 87 % | **visor 1 %, ficha fija** | 1 %, fija | 1 %, fija | — (una columna) | — | — |
| Columna más angosta | 256 px (tres columnas) | **425 px** | 369 px | 425 px | 721 px | 358 px | 328 px |
| Bordes superiores de las columnas | 331 / 331 / 331 | **182 / 182** | 182 / 182 | 182 / 182 | — | — | — |
| Desborde horizontal | no | **no** | no | no | no | no | no |
| Alto total de la página | 1.584 px | **1.505 px** | 1.548 px | 1.508 px | 2.092 px | 1.625 px | 1.621 px |

**Toques al centro de cada número** (la prueba del bloqueante de la v6), en armado y despiece, con Normal y con Transparente: **50/50 a 1280 y 50/50 a 390**. A 390 px los botones miden 44 px como mínimo y no hay desborde. Sin errores de consola.

**Interacción comprobada:**
- Al tocar una pieza en computador, la ficha aparece al lado sin desplazar la página, con «Ver guía / Pedir repuesto / Talleres» justo bajo el nombre.
- En el celular aparece la barra fija «3 Caliper (cuerpo) · Ver ficha».
- El desplegable de sistemas abre (340 × 400 px) y se cierra al tocar fuera.

## Puntajes (rúbrica v2)

| # | Criterio | Antes | **v2** | Evidencia |
|---|---|---|---|---|
| 1 | Claridad del recorrido | 4,5 | **4,5** | Igual que la v7: pestañas, dibujo y ficha en el primer pantallazo. |
| 2 | Descubribilidad | 4 | **4** | La pista va pegada a los controles. La ficha vacía también invita a tocar. |
| 3 | Carga cognitiva | 4 | **4** | Igual que la v7. |
| 4 | Accesibilidad | 4 | **4** | El título del visor oculto sigue disponible para lectores de pantalla. El desplegable se maneja con teclado (Escape). |
| 5 | Rendimiento y peso | 4 | **4** | 126 KB, sin errores. |
| 6 | Uso con el pulgar | 4 | **4** | 50/50 centros y botones de 44 px. |
| 7 | Consistencia con TallerYa | 4,5 | **4,5** | Cabecera, lista de sistemas, estados del plan y botones del sitio. |
| 8 | Protagonismo del dibujo | 3 | **4,5** | 57 % del ancho y 461 px de alto a 1280; 235 px a 360. |
| 9 | Primer pantallazo | bloqueante | **4,5** | Dibujo completo y «Desarmar» a 1024 y 1280. Apoyo entre 13 % y 18 %. |
| 10 | Espacio muerto | bloqueante | **5** | Hueco del 1 %, ficha fija y estado vacío útil. |
| 11 | Proximidad control-efecto | 3 | **5** | Ficha al lado y controles en una fila pegada al dibujo. Barra fija en el celular. |
| 12 | Ritmo, alineación y adaptación | 3 | **4,5** | Columnas alineadas a ± 0 px, la más angosta de 328 px y sin desborde en los 6 anchos. |

**Promedio: 4,4 / 5 (52,5/12). Ningún criterio por debajo de 4 y sin bloqueantes: pasa.**

## Pendientes (no bloquean)
1. Del piloto, no de la integración: dar áreas de toque que no se rocen en el despiece (el 9 y el 14, el 4 y el 5) y sumar margen abajo al número 1 en el armado a 360 px (pendientes 1 y 2 de `revision-ux-v7.md`).
2. Zoom (+ − ⤢) del visor del sitio para el dibujo en el celular, donde mide 235–258 px de alto.
3. En el celular la lista de piezas sigue debajo del paso. Si se quiere que el dibujo y «Desarmar» quepan siempre a 360×640, se puede plegar la lista.
