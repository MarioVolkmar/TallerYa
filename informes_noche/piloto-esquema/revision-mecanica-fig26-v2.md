# Revisión mecánica: fig. 26 v2 (textos con la guía de estilo nueva)

Revisora · 16-nov-2026 · Comparé `motor/datos/nmax-fig26-v2.json` con la versión aprobada (`nmax-fig26.json`, 4,8). Revisé las 49 fichas, los 17 pasos, «Cuándo» y «Cómo funciona». Solo califico la exactitud mecánica, no el estilo.

**Nota: 4,4. Visto bueno: NO, por ahora.** Las fichas y «Cuándo» están bien. Lo que falla son los **pasos del desarme**: al acortarlos se perdieron instrucciones de seguridad. Con los cambios 1 a 3, la nota vuelve a 4,8.

## Lo que está bien
- **Intervalos:**
  - kits cada 2 años con el líquido, o antes si la manigueta se hunde (ficha y «Cuándo», manual pp. 9-7 y 9-25);
  - líquido cada 2 años;
  - mangueras cada 4 años;
  - nivel antes de cada salida, según las comprobaciones previas del manual.
- **Decisiones y quién lo hace:**
  - la bomba se repara con el kit si el cilindro está liso, y se cambia si está rayado;
  - el kit se cambia entero, nunca una copa suelta;
  - las arandelas van siempre nuevas, y la tuerca autoblocante también;
  - la manigueta doblada no se endereza;
  - el interruptor no se abre;
  - mangueras, kits y uniones son trabajo de taller, por la purga con ABS. La tapa y los pernos de los soportes los puede hacer el dueño. Es correcto.
- **Nombres nuevos:** «de la bomba a la ABS» y «de la ABS al cáliper», delantera y trasera (15, 18, 34 y 38), son correctos para la línea con ABS. Los pernos huecos y las arandelas tienen el nombre de su manguera. La posición de los soportes 42 a 48 sigue marcada «ap» en la certeza.
- No queda ningún «(N)» en la prosa y no aparece ningún torque.

## Cambios pedidos
1. **Paso 2 (y paso 8): falta vaciar el depósito.** La v1 decía que el líquido se saca con una jeringa antes de soltar el perno hueco. Ahora solo dice «Con un trapo debajo». Si se suelta con el depósito lleno, todo el líquido sale por la unión.
   - Que el paso 1 o el 2 diga **«saca el líquido con una jeringa antes de soltar el perno hueco»**.
   - Volver a poner **«tapa la pintura: el líquido de frenos la mancha»**, que se perdió.
2. **Paso 17: se perdió el cierre de seguridad.** Hay que recuperar: **al armar, arandelas nuevas, líquido DOT 4 nuevo, purgar hasta que la manigueta quede firme (con ABS, en taller) y probar los dos frenos con la moto quieta antes de rodar.** Es lo más importante de toda la lámina.
3. **Los pasos 7 a 12 son idénticos a los pasos 1 a 6.** Ninguno dice que es la bomba trasera, en la manigueta izquierda. Agregar «trasera» o «izquierda» en el título de cada uno, como en los pasos 13 a 17, que dicen «Igual atrás».
4. **Menor:** el perno hueco (16, 19, 35 y 39) tiene `decision: "cambia"`, pero el texto dice que se reutiliza si está sano. Corregir la etiqueta para que coincida con el texto.
5. **Menor:** las fichas 44 (soporte de la abrazadera) y 46 (soporte de la bobina) dicen «el caucho del ojo se reseca», copiado de las 42 y 48. Esas dos piezas no tienen ojo de caucho: hay que quitarlo.
6. **Menor:** los pasos 1 y 7 dicen «manubrio derecho», que se puede leer como el lado derecho. Mejor «manubrio recto», como decía la v1.
7. **Menor:** el paso 5 perdió la indicación de montar la abrazadera con su marca como estaba, con el orden de apriete y el torque del manual de servicio. Conviene recuperarla.

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| 1 | Pasos 1, 2, 7 y 8 | ✔ Manubrio recto, pintura tapada, líquido sacado con jeringa **antes** de soltar el perno hueco («si no, todo sale por la unión») y bolsa en la punta de la manguera. |
| 2 | Cierre del paso 17 | ✔ Arandelas nuevas en cada unión, DOT 4 nuevo, purga hasta que la manigueta quede firme (con ABS, en el taller) y prueba de los dos frenos con la moto quieta. |
| 3 | Lado en el título | ✔ Los pasos 1 a 6 dicen «Bomba delantera (derecha)», los 7 a 12 «Bomba trasera (izquierda)» y los 13 a 17 llevan delantera o trasera. |
| 4 | Perno hueco | ✔ Los pernos 16, 19, 35 y 39 tienen `decision: "reutiliza"`, y el texto dice que se reutiliza si está sano y que las arandelas van siempre nuevas. |
| 5 | Fichas 44 y 46 | ✔ Ya no hablan de un ojo de caucho: ahora dicen golpe y óxido. Las dos menciones que quedan son de las fichas 42 y 48, que sí tienen ese ojo. |
| 6 | Pasos 5 y 11 | ✔ La marca de la abrazadera va como estaba, y el orden de apriete y el torque remiten al manual de servicio. |
| + | Extras | ✔ Tuerca de la manigueta nueva (pasos 4 y 10), kit completo y nuevo (pasos 6 y 12) y puntas tapadas (paso 13). |

Detalle de estilo, que no bloquea: el paso 2 repite «tapa la pintura» del paso 1.

**Nota final: 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **Visto bueno: SÍ.**
