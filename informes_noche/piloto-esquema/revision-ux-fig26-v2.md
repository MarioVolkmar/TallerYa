# Revisión UX: rediseño de la lámina 26 (v2, `motor/bomba-freno-v2.html`) frente a la actual

Revisora UX · 16-nov-2026. Medí las dos versiones en los 6 anchos:
- la actual con `medir_lamina.py`;
- la v2 con `medir_lamina_v2.py`, nuevo, en `motor/`.

Además revisé a 360 px, a ojo, la vista general, los grupos, la lista y la ficha. No edité la lámina.

## Veredicto
| | Medible (6, 8–12) | A ojo (1, 2, 3, 4, 5, 7) | Promedio de los 12 | Criterio más bajo | **¿Aprobada?** |
|---|---|---|---|---|---|
| Actual (v1) | 4,73 | 4,5 · 4 · 4 · 4 · 4 · 4,5 | 4,45 | 4 | sí |
| **v2** | 4,53 | 5 · 4 · 5 · 4 · 4 · 4,5 | **4,48** | **3 (pulgar)** | **no, todavía** |
| v2 con los 2 arreglos de marcas | ≈ 4,7 | igual | **≈ 4,56** | 4 | sí |

**La v2 es mejor diseño:** es más clara, tiene mucha menos carga y la ficha es mejor. Pero hoy no aprueba por dos fallas de toque en las marcas. Son arreglos de posición, no de modelo. Con eso arreglado queda por encima de la actual.

## 1. Comparación

### Claridad y carga cognitiva (a ojo, 360 px)
| | Actual | v2 |
|---|---|---|
| Lo primero que ves | 57 números sobre el despiece; las bombas quedan tapadas | El dibujo armado con **4 marcas con nombre** (5 en la trasera) |
| Para orientarte | Números del catálogo y lista de 49 | «Bomba», «Manigueta e interruptor», «Manguera a la ABS», «Manguera al cáliper» (+ «Soportes») |
| Dentro de un grupo | — | De 1 a 6 piezas, con silueta resaltada y nombre, y de 2 a 3 píldoras de tornillería |
| Delantera y trasera | Mezcladas en el mismo dibujo | Selector Delantera \| Trasera, siempre a la vista |
| Controles bajo el dibujo | Dibujo N/T, zoom, Armar ◀ ▶, Números | Delantera \| Trasera, Números; Desarmar ◀ ▶ solo dentro de un grupo |

La v2 resuelve lo que molestaba al usuario. Lo que se ve al llegar se entiende sin leer un número, y la nube de números desaparece.

### Toques hasta la ficha de una pieza
| Caso | Actual | v2 |
|---|---|---|
| Pieza visible, por el dibujo | **1** (el número) | **2** (grupo → pieza) |
| Pieza de adentro (kit, pistón…) | Desarmar (17 pasos, unos 22 s, o ▶ varias veces) + número: **2 toques y una espera larga** | grupo → Desarmar (1 a 3 pasos, ≤ 4 s) → pieza: **3 toques y una espera corta** |
| Pieza de la trasera | igual que la delantera | +1 (Trasera), o tocar la pieza con el lado ya puesto |
| Por la lista | 1 (rejilla de números, hay que saber el número) | 2 (abrir el grupo → pieza), o escribir 2 a 3 letras → pieza |
| Ir a la pieza vecina | volver al dibujo y buscarla | **1** (‹ anterior \| siguiente ›) |

**El toque de más existe, pero se paga solo.** Para una pieza visible cuesta 1 toque más, y a cambio:
- el blanco es una marca grande con nombre y no un número de 18 px;
- llegar a las piezas de adentro tarda segundos y no 22 s;
- recorrer piezas cuesta 1 toque.

Solo pierde quien ya sabe el número del catálogo, y para eso está el modo «Números» y el buscador (que acepta el número).

### La ficha nueva
| | Actual | v2 |
|---|---|---|
| Alto a 360 («Bomba delantera») | 1.575 px | **1.798 px** |
| Secciones | Qué es · Cómo falla · Síntomas · Cuándo · ¿Se repara? · (plegado) Para qué sirve · Se conecta · Qué arrastra | Qué es · Para qué sirve · Señales · Por qué falla · ¿Se repara o se cambia? · Cuándo + Pedir/Talleres · (plegado) Relacionadas · Qué arrastra · Fuentes |
| Navegación | — | ‹ anterior \| Lista \| siguiente › (funciona) |
| Tono | Con nombres de catálogo y «(N)» | En segunda persona, sin códigos en el texto |

**Mejor contenido y mejor orden:**
- «Señales» va antes que «Por qué falla».
- La decisión trae quién lo hace.
- «Pedir repuesto» y «Talleres» quedan junto al «Cuándo».

**Es 14 % más larga a 360.** Hay que bajar dos pantallas y media para llegar a «Pedir repuesto».

## 2. `medir_lamina_v2.py`
```
venv/Scripts/python.exe informes_noche/piloto-esquema/motor/medir_lamina_v2.py informes_noche/piloto-esquema/motor/bomba-freno-v2.html --ojo 5,4,5,4,4,4.5
```
Reutiliza el servidor, el cliente de DevTools y el lanzador de `medir_lamina.py`, y tarda unos 2 min. Mide:
- **marcas de grupo de cada lado:** tamaño, toque al centro y a ±9 px, solapes y si quedan dentro del lienzo;
- **dentro de cada grupo, armado y desarmado:**
  - el **área tocable real** de cada pieza: muestrea con `elementFromPoint` y calcula el diámetro equivalente;
  - que tocarla la seleccione;
  - las píldoras de tornillería (las piezas de tornillería no cuentan como silueta, porque se tocan por su píldora);
- **al entrar a un grupo:** dibujo completo y «Desarmar» a la vista; ficha visible (≥ 960) o barra fija (celular) al tocar;
- **lista:** grupos, plegados, buscador;
- **ficha:** secciones, ‹ › y alto;
- además: distribución, botones < 44 px, desborde, errores y 3D.

### Resultados de la v2
| Ancho | Dibujo | Marcas (alto mín.) | Fallas de marca | En grupo: Desarmar | Apoyo |
|---|---|---|---|---|---|
| 360 | 304×236 | 47 px | **Bomba → Manigueta** (se solapan); «Tornillo (1)» fuera del lienzo | sí | 12 % |
| 390 | 334×260 | 47 px | **Bomba → Manigueta** | sí | 10 % |
| 768 | 708×551 | 47 px | 0 | sí | 4 % |
| 1024 | 573×340 | **35 px** | «Tornillo (1)» | sí | 12 % |
| 1280 | 681×465 | **42 px** | «Tornillo (1)» | sí | 5 % |
| 1440 | 681×530 | 48 px | «Tornillo (1)» | sí | 4 % |

Más resultados:
- **Piezas (sin tornillería) a 360:** 21 de 28 tienen un área tocable de 24 px de diámetro o más. Las chicas son las arandelas y abrazaderas de los soportes (37: 9 px, 44: 12, 45: 13, 41: 13) y el kit y el pistón al desarmar (2: 22, 4: 21, 24: 21). Todas se seleccionan al tocarlas y todas están en la lista.
- **Lista:** 4 grupos plegados, 232 px a 360. «bomba» da 12 resultados.
- **Ficha:** 10 secciones, 776 px a 1280. ‹ › funcionan y el 3D abre (Bomba delantera). No hay errores de consola.
- **Notas medibles:** 6: **3** · 8: 4,7 · 9: 5 · 10: 5 · 11: 4,7 · 12: 4,8.

## 3. Ajustes a la rúbrica para el modelo por grupos
1. **Criterio 6, modelo por grupos** (reemplaza toques/roces sobre números):
   - **Marcas de grupo y de tornillería:** ≥ 44 px de alto en los 6 anchos, 0 fallas al centro y a ±9 px, sin solapes y dentro del lienzo. Cualquier falla vale 3.
   - **Piezas, en la vista de grupo:** % con área tocable de ≥ 24 px de diámetro a 360. **5** = 100 % · **4** = ≥ 75 % · **3** = ≥ 50 %.
   - **Siempre:** toda pieza seleccionable en el dibujo o, si no, en la lista.
2. **Medida nueva, toques hasta la ficha** (en el criterio 1):
   - **5** = pieza visible en ≤ 2 toques, pieza de adentro en ≤ 3 y sin esperas de más de 5 s;
   - **4** = un toque más;
   - **3** = esperas largas (desarme completo).

   La actual saca 4 (1 toque, pero 22 s para las de adentro); la v2 saca 5.
3. **Criterio 9:** «Desarmar a la vista» se mide **al entrar a un grupo**. En la vista general cuenta el selector de lado.
4. **Criterio 10, ficha vacía:** si muestra la lista con buscador, vale 5.
5. **Medida nueva, largo de la ficha a 360** (en el criterio 3): llegar a «¿Se repara o se cambia?» en ≤ 1,5 pantallas vale 5; en ≤ 2,5 pantallas, 4.
6. **Sigue valiendo:** la regla de densidad de números (≥ 19 px; 24 px con zoom si hay más de 20) se aplica solo al modo «Números».

## Correcciones para la v2
**Para aprobar:**
1. **Marcas «Bomba» y «Manigueta e interruptor» a 360 y 390:** se solapan, y al tocar «Bomba» entras a «Manigueta». Además, «Bomba» queda pegada al borde superior y «Manigueta e interruptor» se sale por la derecha del lienzo. Hay que separarlas, por ejemplo con «Manigueta» abajo o a la izquierda de su pieza, o usar posiciones de marca propias para el celular.
2. **Píldora «Tornillo (1)» en Manigueta e interruptor:** queda fuera del lienzo en 5 de los 6 anchos y su centro no recibe el toque. Hay que moverla adentro.

**Recomendadas:**
3. **Marcas a 44 px de alto en computador:** hoy miden 35 px a 1024 y 42 px a 1280. El área de toque mide 52 unidades del SVG y se encoge con el lienzo; hay que escalarla como las de celular.
4. **Piezas chicas de «Soportes de la manguera»** (37, 41, 44, 45, de 9 a 13 px a 360): agrandar su área de toque con un trazo invisible más grueso, o encuadrar ese grupo más apretado.
5. **Ficha a 360:** subir «¿Se repara o se cambia?» y «Pedir repuesto» antes de «Por qué falla», o plegar «Por qué falla» y «Para qué sirve» en el celular. Hoy hay que bajar unos 1.000 px para llegar a pedir.
6. **Accesibilidad:** las piezas dentro del grupo no tienen foco de teclado. Hoy se llega por la lista, que es un equivalente válido, pero conviene que el grupo, al abrirse, deje el foco en su primera pieza de la lista.

## Verificación de las correcciones (16-nov-2026, 04:43)
Volví a medir con `medir_lamina_v2.py`, en los 6 anchos, y revisé a ojo a 360 y a 1280.

| Corrección | Resultado |
|---|---|
| U1: marcas sin solaparse y dentro del lienzo | **Resuelto.** 0 fallas, 0 roces, 0 solapes y 0 marcas fuera, en los 6 anchos y en los dos lados. A 390 se leen «Bomba», «Manigueta», «Manguera ABS» y «Manguera cáliper». |
| U2: tornillería dentro del lienzo | **Resuelto.** Todas las píldoras reciben su toque en los 6 anchos. |
| Marcas de 44 px o más | **Resuelto.** Miden de 51 a 54 px de alto en todos los anchos (antes, 35 a 1024). |
| Piezas chicas de «Soportes» | 37, 41 y 45 pasan a 24 px o más. Queda **la 44 con 6 px** (la tapa la abrazadera), igual que dice piloto-esquema; se toca por la lista. |
| Orden de la ficha en el celular | **Resuelto** (por CSS). A 360: Qué es → ¿Se repara o se cambia? (a 522 px del inicio de la ficha) → Cuándo → **Pedir/Talleres a 853 px** (antes, unos 1.000) → Para qué sirve → Señales → Por qué falla → plegados. El visor 3D de la bomba ocupa los primeros 420 px. |

**Piezas (sin tornillería) a 360:** 23 de 28 tienen 24 px o más de área tocable. Las que no llegan son el kit, el pistón y las del lado trasero al desarmar (2, 4 y 24: 21-22 px), la 48 (22 px) y la 44 (6 px). Todas se seleccionan al tocarlas y todas están en la lista. No hay errores de consola y el 3D abre.

### Nota final de la v2
| Medible | A ojo (1, 2, 3, 4, 5, 7) | **Promedio de los 12** | Criterio más bajo | Bloqueantes | **¿Aprobada?** |
|---|---|---|---|---|---|
| 6: 4 · 8: 4,7 · 9: 5 · 10: 5 · 11: 4,7 · 12: 4,8 | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,6** | 4 | ninguno | **SÍ** |

La descubribilidad sube de 4 a 4,5 porque ahora las marcas se leen enteras en el celular. **La v2 queda por encima de la actual (4,45).**

Pendiente menor (no bloquea):
- La 44, que hoy se elige por la lista.
- En el celular, la ficha queda debajo de la lista de grupos. Se llega con la barra fija «Ver ficha», que funciona.
- El foco de teclado al entrar a un grupo.

### Capturas (escala 0,5) en `capturas-rediseno/`
- `fig26-v2b-general-1280.jpg` y `fig26-v2b-general-390.jpg`: vista general.
- `fig26-v2b-grupo-ficha-1280.jpg` y `fig26-v2b-grupo-ficha-390.jpg`: dentro del grupo «Bomba» con la ficha de «Bomba delantera». La de 390 es una tira de 1.250 px desde el dibujo: muestra el grupo, la barra «Ver ficha», la lista y el inicio de la ficha.
