# Revisión UX v6: piloto del freno delantero NMAX 155

Revisora UX · 15-nov-2026 · revisé `index.html` (idéntico a `v6.html`, comprobado con `cmp`) servido por HTTP local, a 1280×800, 390×844 y 360×740, con el almacenamiento local vacío al empezar. Uso la misma rúbrica que en `revision-ux.md` (v3: 3,4).

## Puntajes

| # | Criterio | v3 | **v6** | Evidencia |
|---|---|---|---|---|
| 1 | Claridad del recorrido | 3 | **4,5** | Pestañas Piezas · Cómo funciona · Si falla · Cuándo dentro de un visor `.papel`. A 1280×800 el primer pantallazo ya muestra el dibujo (empieza a 270 px) y la ficha fija al lado. A 360 px la página mide 1.213 px en Piezas y 2.597 px en Cómo funciona (antes, 10.239). «Contradicciones» salió y las fuentes van plegadas. |
| 2 | Descubribilidad | 3 | **4** | La pista «Toca una pieza» se va con la primera selección (comprobado). Los números están al 80 %. «Normal \| Transparente» se ve sobre el dibujo y el texto del armado lo menciona. Las pestañas se ven de un vistazo. |
| 3 | Carga cognitiva | 3,5 | **4** | «Desarmar» va a 1,3 s por paso (16,5 s en total, medido) con «Pausa», así que el texto de cada paso se alcanza a leer. Las etiquetas de causa tienen leyenda. Las fichas siguen plegadas. |
| 4 | Accesibilidad | 3 | **4** | Durante «Desarmar», `#textoPaso` pasa a `aria-live="off"` y vuelve a `polite` al terminar (comprobado). `#ficha` ya no tiene `aria-live`. El SVG es `role="group"`. Las pestañas se navegan con las flechas (ArrowRight → «Cómo funciona», comprobado). Los interruptores tienen `aria-pressed` y los botones miden 44 px en los tres anchos. Los textos de «Cómo funciona» miden 12,7 px como mínimo a 360 px. |
| 5 | Rendimiento y peso | 4 | **4** | 108 KB, sin imágenes y sin errores de consola. «Transparente» se guarda en `localStorage` (`esqVista`) con try/catch. |
| 6 | Uso con el pulgar | 3 | **3** | Mejoró mucho: controles en una sola fila (Desarmar · ◀ · ▶ · Números), sin desborde (scrollWidth = ancho en los tres), y la barra fija «3 Caliper (cuerpo) · Ver ficha» aparece al tocar una pieza. **Pero hay un bloqueante:** el selector «Normal \| Transparente» (179×51 px a 360) va encima del dibujo y **se queda con el toque de algunos números**, que activan el selector en vez de abrir la ficha (`elementFromPoint` en el centro del número devuelve el `<button>` del selector). Lo medí: a 360 px, en armado se tapan los números 8 y 15, y en el despiece el 8 y el 10 (el 7 y el 12 quedan rozados). A 390 px, en armado el 8 y en el despiece el 8 y el 10. A 1280 px, en el despiece el 10. |
| 7 | Consistencia con TallerYa | 3 | **4,5** | Ahora usa los tokens del sitio (crema `#ede3cc`, mostaza `#e3a72f`), `.titulo`, `.btn .btn-lava`, `.visor-modo` con `aria-pressed`, pestañas en Oswald en mayúsculas y `.papel` de 18 px. Encaja con el despiece real sin retoques grandes. |

**Promedio: 4,0 / 5. ¿Pasa como diseño aprobado para integrar? NO, todavía.** Falla el criterio 6 (3 < 4) y hay un bloqueante: el selector tapa números tocables en los tres anchos.

## Cambio mínimo para que pase
1. **Sacar el selector «Normal | Transparente» de encima del dibujo.** Recomendado: ponerlo en la fila de herramientas, en vez del interruptor «Números» o a su lado; a 360 px puede ir en una segunda fila o como icono con `aria-label`. Otra opción es la barra del visor, junto al título. Una alternativa menor es reservar un margen superior en `VB_ARM` y `VB_EXP` (unas 60 unidades del SVG a 360 px) para que ningún número quede bajo el selector, pero es más frágil porque depende del ancho.
   - **Verificación:** a 360, 390 y 1280 px, en armado y en despiece completo (con «Normal» y con «Transparente»), `document.elementFromPoint` en el centro de cada número visible debe devolver ese número (`.bola`) y nunca un `<button>`. Hoy falla con los números 8, 10 y 15.

Con eso, el criterio 6 sube a 4 (todo lo demás del celular está bien), el promedio queda en unos 4,1 y todos los criterios en 4 o más: **pasa**.

## Opcionales (no bloquean)
- El segundo número de 10 (y de 9 y 5) sigue siendo tocable en el despiece aunque ya no sea tabulable. Está bien, solo es redundante.
- A 360 px el dibujo armado mide 235 px de alto. Más adelante, el zoom del visor del sitio (+ − ⤢) ayudaría con las piezas chicas.
- `integrado.html` se armó sobre la v3: cuando se integre, conviene partir de la v6.
