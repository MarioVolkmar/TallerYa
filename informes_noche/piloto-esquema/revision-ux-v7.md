# Revisión UX v7: piloto del freno delantero NMAX 155

Revisora UX · 15-nov-2026 · revisé `index.html` (idéntico a `v7.html`, comprobado con `cmp`) servido por HTTP local, con la pestaña al frente y el almacenamiento local vacío al empezar, a 360×740, 390×844 y 1280×800. Uso la misma rúbrica que en `revision-ux.md` y `revision-ux-v6.md`.

## Verificación del bloqueante de la v6
Prueba: en cada ancho, en armado y en despiece completo, con «Normal» y con «Transparente», tomé el centro de cada número visible y miré qué elemento recibe el toque (`document.elementFromPoint`).

| Ancho | Armado N | Armado T | Despiece T | Despiece N | **Centros** | Botones |
|---|---|---|---|---|---|---|
| 360 | 7/7 | 7/7 | 18/18 | 18/18 | **50/50** | mín. 44 px, scrollWidth 360 |
| 390 | 7/7 | 7/7 | 18/18 | 18/18 | **50/50** | mín. 44 px, scrollWidth 390 |
| 1280 | 7/7 | 7/7 | 18/18 | 18/18 | **50/50** | mín. 44 px, sin desborde |

**Confirmado lo que dice la creadora: 50 de 50 en los tres anchos.** El selector «Dibujo: Normal | Transparente» y la pista ahora van en una fila bajo el dibujo (comprobado: su borde superior queda debajo del borde inferior del SVG). La barra fija sigue funcionando: «13 Soporte del caliper · Ver ficha» al tocar el número 13 a 360 px.

Nota de método: también probé cuatro puntos fuera del centro, al 30 % y al 70 % del círculo. Ahí hay roces menores, que van en los pendientes de abajo.

## Puntajes

| # | Criterio | v3 | v6 | **v7** | Evidencia |
|---|---|---|---|---|---|
| 1 | Claridad del recorrido | 3 | 4,5 | **4,5** | Sin cambios respecto a la v6: pestañas, dibujo y ficha en el primer pantallazo en computador, y 1.265 px de página a 360 px. |
| 2 | Descubribilidad | 3 | 4 | **4** | La pista «Toca una pieza» queda pegada al dibujo, sin tapar nada, y se oculta con la primera selección. |
| 3 | Carga cognitiva | 3,5 | 4 | **4** | Igual que la v6. |
| 4 | Accesibilidad | 3 | 4 | **4** | Igual que la v6. El selector ahora tiene la etiqueta visible «Dibujo» (`aria-labelledby`). |
| 5 | Rendimiento y peso | 4 | 4 | **4** | 108 KB, sin errores de consola. |
| 6 | Uso con el pulgar | 3 | 3 | **4** | Ningún control tapa números (50/50 en el centro). Los botones miden 44 px y no hay desborde en los tres anchos. La barra fija y la fila de controles caben en una línea. |
| 7 | Consistencia con TallerYa | 3 | 4,5 | **4,5** | Igual que la v6. |

**Promedio: 4,1 / 5 (29/7). ¿Pasa como diseño aprobado para integrar en TallerYa? SÍ.** Todos los criterios están en 4 o más y no hay bloqueantes.

## Pendientes no bloqueantes (para la integración o una v8)
1. **Áreas de toque que se rozan** en el despiece: tocando un poco fuera del centro (a unos 9 px), el 9 toma el toque del 14 y el 4 el del 5 a 360 px. A 390 px pasa con el 9, y el 5 roza una pieza a 360, 390 y 1280 px. Solución: separar un poco esas posiciones finales, o dar a cada número un área de toque circular que no supere la mitad de la distancia a su vecino.
2. **El número 1 en el borde inferior del dibujo armado a 360 px**: su parte de abajo queda fuera del SVG, así que un toque bajo el centro no lo agarra. Basta con unas 10 unidades más de margen abajo en `VB_ARM`.
3. A 360 px el dibujo armado mide 235 px de alto. Cuando se integre, conviene sumar el zoom del visor del sitio (+ − ⤢).
4. `integrado.html` se armó sobre la v3: para la integración real hay que partir de la v7 (el generador de `integracion/` se puede volver a correr, pero la v7 ya trae sus propias pestañas, barra fija y selector, así que la capa de integración se reduce a cabecera, barra lateral y acciones del plan).
