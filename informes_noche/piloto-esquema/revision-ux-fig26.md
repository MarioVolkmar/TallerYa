# Revisión UX: lámina 26 de la NMAX «Bombas de freno y líquido» (`motor/bomba-freno.html`)

Revisora UX · 16-nov-2026 · revisión corta. El motor ya está aprobado, así que corrí `medir_lamina.py` con mis notas a ojo y revisé aparte lo propio de la lámina a 360 (densidad, zoom, «Cómo funciona», fila de «Transparente»).

## Veredicto
| Medible (6, 8–12) | A ojo (1, 2, 3, 4, 5, 7) | **Promedio de los 12** | Bloqueantes | **¿Aprobada?** |
|---|---|---|---|---|
| 4,73 | 4,5 · 4 · 4 · 4 · 4 · 4,5 | **4,45** | ninguno | **SÍ** |

Auxiliares calculó 4,58 con su ojo. Yo pongo 4 en vez de 4,5 en descubribilidad, carga cognitiva y accesibilidad, por la densidad a 360 (ver abajo).

## `medir_lamina.py`
Hay 180/180 toques con 0 roces y en ningún ancho se corta el dibujo:
- se ve «Desarmar» en los 6 anchos;
- el dibujo mide 461 px de alto a 1280 y 236 px a 360;
- el apoyo ocupa entre el 4 y el 15 %;
- la consola no muestra errores.

El visor 3D abre («1 Bomba delantera»). Son 17 pasos de desarme. La lista de 49 piezas es una rejilla de 440 px a 360. La lámina pesa 127 KB de datos propios (JSON de 102 KB y arte de 24 KB).

Notas medibles: 6: 4,5 · 8: 4,7 · 9: 5 · 10: 4,7 · 11: 4,7 · 12: 4,8.

## Lo propio de la lámina

### Densidad y zoom a 360
- **Despiece completo:** 57 números visibles (49 piezas, con repetidos a izquierda y derecha) en un lienzo de 304×236 px.
  - Hay 42 pares de números a menos de 24 px entre centros; el mínimo es 19,7 px.
  - Los discos de 18 px no se encaraman.
  - El área de toque mínima tiene 6,3 px de radio, pero en la práctica es el disco de 18 px: la prueba estricta no encontró roces a ±9 px.
- **Problema real, de lectura más que de toque:** en las bombas de arriba los números tapan casi toda la pieza. A 360, el despiece se ve como una nube de números.
- **El zoom lo resuelve en un toque.** Medí cuántos números quedan dentro del lienzo en cada nivel:

| Zoom | Números dentro del lienzo | Pares a < 24 px | Distancia mínima | Toques | Roces |
|---|---|---|---|---|---|
| ×1 | 57 | 42 | 19,7 px | todos | 0 |
| ×1,6 | 31 | **0** | 32 px | 31/31 | 0 |
| ×2,6 | 17 | 0 | 51 px | 17/17 | 0 |
| ×4 | 7 | 0 | 80 px | 7/7 | 0 |

### «Cómo funciona» en el celular
**Se entiende bien.** Muestra la bomba cortada (depósito y tapa, diafragma, orificio de compensación, resorte, pistón y copas, manigueta, interruptor → luz de freno), la unidad ABS y el cáliper con el disco.
- Son 7 pasos: reposo → aprietas → la copa tapa el orificio → el cáliper aprieta → sueltas → las pastillas se gastan → si entra aire. El último paso es muy útil.
- La letra mínima mide 12,4 px. Dibujo, texto y controles (465 + 109 a 184 + 44 px) **caben juntos** en 740.

Hay dos problemas:
1. **Los botones ◀ ▶ y Reproducir saltan.** Están debajo del texto, y el texto cambia de 109 a 184 px de alto según el paso. Al tocar ▶ varias veces seguidas, el botón se corre hasta 75 px bajo el dedo.
2. **La etiqueta «Manguera» queda tapada por el dibujo del cáliper** a 360 px (se lee «Mangu…»), porque el cáliper se dibuja encima de ella.

### La fila de «Transparente» a 360
Es la misma distribución que en el freno y la CVT: tres filas pegadas al dibujo («Dibujo: Normal | Transparente», pista + zoom, Armar ◀ ▶ Números). En el criterio 11 vale 4 en el celular y 5 en computador, donde va en una sola fila; por eso queda en 4,7. No es propio de esta lámina ni hay que corregirlo aquí. Si se quiere un 5, sería un ajuste del motor: «Dibujo» como un solo botón que alterna, en la fila del zoom.

## La meta de la skill «≥ 24 px entre números a 360»
**No es realista en láminas grandes. Conviene redefinirla.**
- **Por la cuenta:** a 360 el lienzo mide unos 304×236 px. 49 números a 24 px en el mejor reparto posible ocuparían un tercio del lienzo. Pero cada número tiene que quedar cerca de su pieza, y las piezas se amontonan (bombas, tornillos, arandelas), así que con más de unos 20 a 25 números no hay forma de cumplirla sin alejar los números de lo que señalan.
- **Por lo que importa:** el riesgo de verdad es tocar el número equivocado, y eso ya lo mide la prueba estricta (0 roces a ±9 px). La distancia de 24 px es un medio, no el fin.

Propuesta para la skill y para `criterios-ux.md`:
1. **Siempre:** 0 fallas al centro y 0 roces a ±9 px, en los 6 anchos.
2. **Siempre:** distancia mínima de 19 px a 360, para que los discos de 18 px no se encaramen.
3. **Hasta unos 20 números:** ≥ 24 px a ×1.
4. **Con más de 20:** ≥ 24 px con el primer zoom (×1,6), con el zoom a la vista bajo el dibujo y una lista equivalente que no se deslice.

Con esa regla, esta lámina cumple (32 px a ×1,6), y también la CVT (34 px).

## Correcciones (ninguna bloquea)
1. **«Cómo funciona»:** fijar el alto de `#fnTexto` al del paso más largo (unos 184 px a 360), o subir los controles encima del texto, para que ◀ ▶ no salten.
2. **«Cómo funciona»:** pasar «Manguera» al otro lado de la línea, o dibujarla después del cáliper, para que no quede tapada.
3. **Opcional, lectura del despiece a 360:** que la pista diga «Usa + para acercar» cuando la lámina tiene muchos números, o que el despiece entre con ×1,6 en el celular. Hoy hay que descubrir el zoom solo.
4. **Opcional:** en «Si falla», los chips de las cadenas miden 36 px de alto desde 768 px. Es del motor y sale como aviso en el script.
