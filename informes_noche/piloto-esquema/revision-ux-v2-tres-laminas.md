# Revisión UX: las tres láminas migradas al modelo v2 (rúbrica v3)

Revisora UX · 16-nov-2026 (05:40–06:04). Revisé `motor/freno.html` (fig. 22), `motor/cvt.html` (fig. 12) y `motor/bomba-freno.html` (fig. 26). Las medí con `medir_lamina.py`, en los 6 anchos y con el modelo v2 detectado solo. Además comprobé a mano lo dudoso y miré las capturas de `capturas-rediseno/`.

## Veredicto
| Lámina | Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Criterio más bajo | **¿Aprueba?** |
|---|---|---|---|---|---|
| **Fig. 26 bombas** | 4 · 4,7 · 5 · 5 · 4,8 · 4,8 = 4,72 | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,61** | 4 | **SÍ** |
| Fig. 22 freno | **3** · 4,7 · 5 · 5 · 4,8 · 4,8 = 4,55 | 4,5 · 4,5 · 5 · 4 · 4 · 4,5 | 4,47 | **3 (pulgar)** | no, todavía |
| Fig. 12 CVT | **3** · 4,7 · 5 · 5 · 4,8 · 4,8 = 4,55 | 4,5 · 4,5 · 5 · 4 · 4 · 4,5 | 4,47 | **3 (pulgar)** | no, todavía |

**Lo que funciona en las tres:**
- Marcas de grupo de 45 a 46 px, sin fallas ni solapes; la tornillería recibe el toque.
- Dibujo completo y «Desarmar» a la vista al entrar a un grupo, en los 6 anchos.
- Hoja inferior al 12 % de la pantalla, con el nombre de la pieza y botón de cerrar. No tapa la pieza y sus botones miden 44 px.
- «¿Se repara o se cambia?» queda a entre 0,3 y 0,7 pantallas del inicio de la ficha.
- No hay desborde ni errores de consola, y el 3D de la fig. 26 abre.
- En la captura de la ficha a 390 (hoja expandida): navegación ‹ Lista ›, la certeza dentro del texto («manual») y «Se cambia» arriba. Se ve ordenado y encaja con el sitio.

**Lo que falta en el freno y la CVT:** piezas chicas dentro de su grupo. A 360, solo 8 de 16 piezas del freno y 9 de 29 de la CVT tienen 24 px de área tocable (la rúbrica pide el 75 % para un 4). Se pueden elegir desde la lista, así que no es bloqueante, pero tocarlas en el dibujo es difícil.

## Lo que era del medidor (corregido)
Piloto-esquema tenía razón en dos puntos:
- **«Tornillos del disco» sin toque (fig. 22):** era del medidor. Medía la tornillería después de que la página se había movido y con la hoja inferior expandida por el propio medidor encima del dibujo. Ya re-centra el dibujo y cierra la hoja. Hoy toda la tornillería da bien en las tres láminas.
- **«Cuenta las piezas en la vista general»:** no las cuenta. El medidor solo mide piezas dentro de cada grupo (`.esq-engr`), armado y desarmado. El 3 del criterio 6 sale de la vista de grupo a 360, no de la vista general.

Otras trampas del medidor que encontré y corregí en esta ronda:
- **Piezas con varias siluetas (10a, 10b):** al tocar la segunda se desmarcaba la pieza, porque tocar la pieza elegida la desmarca. Salía «no se selecciona»; ahora se prueba una vez por pieza.
- **Grupos que se desarman solos** al elegir una pieza interna (Pastillas, Clutch): «Desarmar» ya estaba agotado y no se medía el estado desarmado, así que las piezas internas salían en 0 px. Ahora se miden.
- **El globito con el nombre** que sale 1,8 s después de un toque de dedo tapaba lo siguiente. Se oculta mientras se mide.

## Hallazgos reales (comprobados a mano)
1. **CVT, Clutch desarmado:** la píldora «Tuerca (1)» queda encima de los resortes de las zapatas (10) y de sus seguros (11), que quedan con unos 7 px tocables a 360. Se seleccionan, pero solo tocando un borde.
2. **Piezas chicas en su grupo, a 360:**
   - **freno:** grapa 10b (10 px), pasador y guardapolvos 5a, 5b, 6 y 7 (16 a 18 px), purgador 8 (17 px), resorte 11 (21 px) y 4 (22 px);
   - **CVT:** resortes y seguros 10 y 11 (7 px), 16 (8 px), 17 (11 px), 21 (13 px), 2 (16 px), 15 y 18 (17 px), 14 (20 px), 19 (22 px) y otras;
   - **fig. 26:** 2 (22), 4 (21), 24 (21) y 44 (16).
3. **Desarme largo:** el cáliper del freno y el variador de la CVT tienen 7 pasos. A 1,3 s por paso son 9,1 s, y la subnota de «toques hasta la ficha» queda en 3. No es grave, porque ◀ ▶ deja ir paso a paso, pero quien quiere ver una pieza de adentro espera.
4. **Ver la ficha completa en el celular cuesta 3 toques** en las tres láminas: grupo, pieza y «Ver ficha» en la hoja.

## Qué corregir
**Para que el freno y la CVT aprueben (criterio 6 a 4):**
1. **Área de toque mínima automática en el motor.** En la vista de grupo, a cada pieza cuya área tocable quede por debajo de 24 px de diámetro, sumarle un círculo invisible de toque de 24 a 30 px. Es lo que se hizo a mano con las piezas 37, 41 y 45 de la fig. 26. El círculo va debajo de las píldoras y se recorta a la mitad de la distancia a la pieza vecina, para no robarle toques. Cuesta 0 por lámina y arregla las tres.
   - **Verificación:** `medir_lamina.py` debe dar 75 % o más de piezas a ≥ 24 px a 360 y seguir sin fallas en las marcas.
2. **CVT, Clutch:** mover la píldora «Tuerca (1)» fuera de los resortes y seguros desarmados, u ocultar en el estado desarmado las píldoras de tornillería de piezas que ya se movieron.

**Recomendadas:**
3. Grupos de más de 4 pasos: desarmar a unos 0,8 s por paso, o abrir directo en «desarmado completo» al elegir una pieza de adentro (el motor ya lo hace al elegirla por la lista). Así la subnota del criterio 1 vuelve a 4.
4. Pasar el criterio 1 a ≤ 2 toques en el celular: que tocar la pieza ya muestre en la hoja «Qué es» y «¿Se repara?» en dos líneas, sin tener que tocar «Ver ficha». El prototipo v3 ya lo hace con el resumen de una línea.

## Cómo se midió
```
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/medir_lamina.py informes_noche/piloto-esquema/motor/<lamina>.html --ojo 4.5,4.5,5,4,4,4.5
```
Las notas a ojo de la fig. 26 son las de la verificación anterior. El freno y la CVT bajan a 4,5 en el criterio 1 por el desarme de 9 s.
