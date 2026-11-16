# Revisión de «Cómo funciona» en las 9 láminas

Revisora UX · 16-nov-2026. Pedido del usuario: algunos «Cómo funciona» se sienten esquemáticos y vagos (ejemplo: fig. 8, con cajas grises, un triángulo como inyector, una línea punteada y etiquetas montadas).

**Cómo lo revisé:** abrí cada lámina en un Chrome propio, a 390×844 y a 1280×800, y recorrí todos los pasos de «Cómo funciona». Medí:
- etiquetas que se montan y letra mínima en pantalla;
- cuántos elementos del dibujo cambian en cada paso (si la animación muestra algo);
- si hay indicadores (rpm, presión, nivel…);
- el detalle del dibujo: cuántas formas y degradados tiene.

Además miré un mosaico con las 9 a 1280, en el paso del medio. No edité nada.

## Calificación (1 a 5)
Criterios: **R** piezas reconocibles (¿se parecen al dibujo de la lámina?) · **C** corte o transparencia que muestre lo de adentro · **A** la animación explica causa y efecto · **E** etiquetas sin montarse · **L** legible en el celular.

| Lámina | R | C | A | E | L | **Nota** | Medidas |
|---|---|---|---|---|---|---|---|
| Fig. 12 CVT | 5 | 5 | 5 | 5 | 5 | **5** | 36 formas, 8 degradados, de 7 a 18 cambios por paso, indicador de **rpm**. Es la referencia |
| Fig. 22 freno | 5 | 5 | 4 | 5 | 5 | **4,8** | 56 formas, 16 degradados, cáliper y bomba en corte; de 1 a 3 cambios por paso (10 en el último), sin indicador |
| Fig. 26 bombas | 5 | 5 | 4,5 | 5 | 5 | **4,9** | bomba cortada (depósito, diafragma, resorte, pistón y copas, interruptor), de 4 a 14 cambios por paso |
| Fig. 24 freno trasero | 5 | 5 | 4 | 5 | 5 | **4,8 con un error** | Es el mismo esquema del freno delantero, y **la etiqueta dice «Puño derecho»**: el freno trasero de la NMAX va en el puño **izquierdo** (el texto del paso sí dice izquierda). |
| Fig. 1 culata | 3,5 | 4 | 3 | 5 | 4,5 | **3,5** | corte del cilindro con pistón, válvulas y bujía, pero plano (0 degradados); 3 a 4 cambios por paso |
| Fig. 11 tapa de transmisión | 2 | 1 | 2,5 | 5 | 4,5 | **2,5** | contorno de la tapa, línea punteada y un cuadro con un círculo como filtro; de 0 a 6 cambios por paso |
| Fig. 7 aceite | 2,5 | 2 | 2,5 | 5 | 4,5 | **2,5** | contorno del cárter con nivel, un engranaje y un cuadro vacío («Cigüeñal y culata»); de 1 a 6 cambios |
| Fig. 8 admisión | 2 | 1 | 2 | **2** | 4,5 | **2** | cajas, un triángulo como inyector y línea punteada. **«Mariposa y ralentí» se monta sobre «Inyector»** (lo encontró el script). De 1 a 4 cambios por paso |
| Fig. 10 cárter | 1,5 | 2 | 2 | 5 | 4,5 | **2** | apenas 12 formas: contorno, varilla, dos etiquetas de litros y un cuadro vacío como «Retén» |

**En todas, a 1280 la letra mínima del esquema mide 9,9 px:** en computador el esquema se encoge a 683 px de ancho. A 390 mide de 12,5 a 13,6 px, que está bien. Hay que corregirlo en el motor.

## Mejoras para las que están por debajo de 4
### Fig. 8 admisión (2): prioridad 1
1. **Dibujar las piezas reales en corte:**
   - la caja del filtro abierta, con el filtro de papel plisado;
   - el cuerpo de aceleración cortado, con la **mariposa que gira** según el acelerador;
   - el inyector con su forma (cuerpo, conector, punta) **rociando un cono** de gasolina en el múltiple;
   - el cilindro con la válvula de admisión abriéndose.
2. **Animar la causa y el efecto:**
   - al acelerar, la mariposa abre, entra más aire (flechas más gruesas o más rápidas) y el inyector rocía más;
   - con el filtro tapado, las flechas se adelgazan y el papel se oscurece.
3. **Indicadores:** apertura del acelerador en %, flujo de aire (una barra) y rpm. Separar «Mariposa y ralentí» de «Inyector» (ralentí por debajo del cuerpo e inyector por encima del múltiple).

### Fig. 10 cárter (2): prioridad 2
1. **Corte del cárter con el aceite adentro** y **la varilla con sus marcas mín./máx.** Animar lo que hace el motero: sacar la varilla, limpiarla, meterla, leerla. Es el «cómo funciona» más útil de esta lámina.
2. **Transmisión final en corte:** engranajes que salpican su aceite, para mostrar por qué tiene el suyo (0,10 L) aparte del motor (0,90 L).
3. **Retén del eje en corte:** el labio de goma sobre el eje. Animar cómo, endurecido, deja pasar una gota. Indicador: nivel en litros y en la varilla.

### Fig. 7 aceite (2,5): prioridad 3
1. **Bomba trocoidal en corte:** rotor interior y exterior girando, con las cámaras que crecen y se achican. Hoy es un engranaje genérico.
2. **Recorrido completo y reconocible:** tamiz (con partículas atrapadas), bomba, conductos, cigüeñal y árbol de levas dibujados, no un cuadro vacío. Flechas que avanzan.
3. **Indicadores:** presión de aceite, que sube con las rpm, y el color del aceite, que se oscurece con los kilómetros: el «por qué se cambia».

### Fig. 11 tapa de la transmisión (2,5): prioridad 4
1. **Filtro de la correa en corte:** espuma o malla con el polvo que se acumula. Hoy es un círculo en un cuadro.
2. **La polea con aletas girando y aspirando:** el aire entra por la rejilla, pasa el filtro, enfría la correa y sale. Es la causa que hoy no se ve.
3. **Indicadores:** temperatura de la correa (°C), que sube cuando el filtro se tapa, y el flujo de aire en %.

### Fig. 1 culata (3,5): prioridad 5
1. **Los 4 tiempos animados:** pistón que sube y baja sincronizado con las válvulas y la chispa, con colores (aire azul, mezcla ámbar, combustión roja, escape gris).
2. **Indicador:** ángulo del cigüeñal y el nombre del tiempo (admisión, compresión, explosión, escape).
3. **Volumen:** degradados como los del dibujo de la lámina; hoy es plano (0 degradados) y no se parece a la culata de «Piezas».

**Otros:**
- **Fig. 24:** cambiar «Puño derecho» por «Puño izquierdo» en el esquema. Revisar con mecánica que no queden otros datos copiados del delantero; ya se pidió confirmar el disco de 230 mm.
- **Motor:** letra mínima de 12 px en el esquema también a 1280, con letra fija o un esquema más alto en computador.

## Criterio mínimo propuesto (skill y rúbrica)
Un «Cómo funciona» aprueba si cumple las 6 condiciones:
1. **Reconocible:** al menos 3 piezas de la lámina dibujadas con su forma y color, no como cajas, triángulos ni círculos genéricos.
2. **Lo de adentro:** al menos un corte o transparencia de la pieza donde pasa la acción (bomba, cilindro, filtro, cárter).
3. **Causa → efecto:** cada paso cambia algo visible que corresponde a su texto: algo se mueve, fluye o cambia de color. Que no sea solo resaltar.
4. **Un indicador físico** cuando aplica: rpm, presión, flujo, temperatura o nivel, con un número que cambie entre pasos.
5. **Etiquetas:** sin montarse y con letra de 12 px o más, a 360 y a 1280.
6. **Texto del paso:** 250 caracteres como máximo.

| Qué se puede revisar con script (sumarlo a `medir_lamina.py`) | Umbral |
|---|---|
| Etiquetas que se montan (cajas de `<text>` en `#fn`) | 0 |
| Letra mínima del esquema a 360 y a 1280 | ≥ 12 px |
| Elementos que cambian en cada paso | ≥ 3 en cada paso (alerta si algún paso cambia 0 o 1) |
| Indicador físico (texto con rpm, bar, °C, %, L, km/h…) | al menos 1, o «no aplica» declarado en el JSON |
| Detalle del esquema | alerta si tiene menos de 30 formas y menos de 3 degradados (en fig. 8, 10, 11, 7 y 1 salta) |
| Largo del texto del paso | ≤ 250 caracteres |

Siguen a ojo: si las piezas se parecen de verdad al dibujo, si el corte muestra lo correcto y si la animación explica la causa.
