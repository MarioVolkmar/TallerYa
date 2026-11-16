# Revisión mecánica: fig. 1 de la NMAX 155 BBE4, «Cilindro, culata y bujía»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig1.json`: 28 números, 10 pasos con `sujeta`, «Cómo funciona» de 6 pasos, 3 cadenas, «Cuándo» y las fichas. Lo comparé con el manual B6Y4 (p. 9-10, bujía, PDF 72, ya leída), con `yamaha_nmax_155.json` y con el catálogo BBE4. Del catálogo solo busqué texto con pymupdf en las figs. 1 y 4 y en la eléctrica, sin modificar nada. Tecnología: inyección y refrigeración líquida. Solo califico lo mecánico.

## Datos «Seguro»
- **Bujía:** NGK CPR8EA-9, separación 0,8–0,9 mm, 13 N·m o 1/4–1/2 vuelta (p. 9-10). ✔ Cambio cada 10.000 km o 12 meses y revisión cada 6.000 km, como en el plan. ✔
- **Tapón del radiador en caliente:** aparece en el paso 5, en «Cómo funciona» y en «Cuándo». ✔
- **Refrigerante** cada 24.000 km o 2 años, y **holgura de válvulas** cada 6.000 km o 6 meses: igual que el plan. ✔

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Hay 28 números con nombre y cantidad del catálogo. `sujeta` es coherente: las tuercas 16 y los allen 24 sujetan la culata, la culata sujeta el empaque y los pasadores, y el empaque va sobre el cilindro. Los pasadores 12, 22 y 23 están marcados como aproximados. |
| 2 | Exactitud mecánica | **4** | El desarme es el correcto: el refrigerante se vacía en frío; escape, admisión y mangueras salen antes de la culata; PMS de compresión con las marcas alineadas; tuercas en cruz y de a poco; la culata sale sin hacer palanca; empaque metálico siempre nuevo; se sostiene el pistón y se tapa el cárter. «Cómo funciona» explica bien los 4 tiempos y la refrigeración. **Hay un error en la ficha del cilindro** (cambio 1). |
| 3 | Pedagogía | **5** | Los 4 tiempos y la refrigeración se entienden. Las cadenas son reales: el empaque de culata soplado da humo blanco y baja el refrigerante, y el aceite de la tapa llega al pozo de la bujía. |
| 4 | Congruencia | **5** | Los intervalos y la bujía coinciden con el plan. |
| 6 | Reglas | **5** | Los torques de la culata y de la tapa remiten al manual de servicio. Los pasadores y las piezas dudosas están marcados como aproximados. |

**Promedio: 4,6. Visto bueno: NO, por ahora**, por el error del cambio 1. Con eso la nota sube a 4,8.

## Cambios pedidos
1. **Error: el cilindro (25) no se rectifica.** La ficha dice «la camisa por donde sube y baja el pistón» y «Rayado u ovalado… se rectifica con pistón de sobremedida o va nuevo».
   - El motor Blue Core de la NMAX usa un cilindro de aluminio **sin camisa**, con la pared tratada (DiASil).
   - El catálogo BBE4 solo trae **PISTON (STD)** y **PISTON RING SET (STD)**, sin sobremedidas (O/S).
   - Debe decir: **«Es de aluminio con la pared tratada, sin camisa: no se rectifica. Si está rayado u ovalado, va nuevo (con pistón y anillos estándar).»**
   - Hay que quitar «camisa» del campo `que`.
2. **Holgura de válvulas:** agregar la **primera revisión a los 1.000 km**. El plan dice «Yamaha pide revisarla en cada servicio, desde los 1.000 km». Hoy solo dice «cada 6.000 km o 6 meses».

## Dudas de la creadora (hipótesis para confirmar, no las castigo)
- **Tornillo 27 con arandela de sello, al costado del cilindro.** En los motores con refrigeración líquida, ese tornillo suele ser el **tornillo de drenaje del refrigerante del cilindro**. Si se confirma, el paso 5 («vacía el refrigerante») debería nombrarlo.
- **Tapón 3 y tornillo 4 con arandela, en la culata.** Lo más probable es que tapen conductos de aceite o de agua hechos en fábrica, o un punto para medir. Que sigan como aproximados.
- **Varilla 13 con retén 14, en la tapa de la culata.** No la pude identificar con el catálogo. La NMAX tiene **VVA** (un solenoide en el catálogo eléctrico, BK6-H6110). Una varilla que atraviesa la tapa con su retén podría ser parte de ese mecanismo o un eje de mando, pero es solo una hipótesis. Que siga como «el catálogo no dice para qué sirve».

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| 1 | Cilindro 25 | ✔ Ya no dice «camisa», «sobremedida» ni «rectifica»: dice «pared tratada de fábrica», `decision: "cambia"`, y que va nuevo con el pistón y los anillos. En la certeza, «catálogo solo STD» está como seguro y «Blue Core sin camisa» como aproximado. Dice «chaqueta de refrigerante» y no menciona aletas: es correcto para una moto refrigerada por agua. |
| 2 | Válvulas | ✔ A los 1.000 km y después cada 6.000 km o 6 meses. |
| 3 | Drenaje del refrigerante | ✔ La 27 y la 28 se llaman ahora «Tornillo de drenaje del refrigerante» y «Arandela del drenaje», con la función marcada «ap». El paso 5 vacía el refrigerante por ahí. |
| ✘ | **Regresión en el paso 5** | Al reescribirlo se perdió lo que tenía antes: «Antes salen el escape, la admisión y las mangueras del refrigerante, y con el pistón en el **PMS de compresión y las marcas alineadas**, el árbol de levas y la cadena (otras láminas)». Ningún otro paso dice ahora «PMS», «marcas», «cadena» ni «admisión». Sin eso, el paso pasa directo a aflojar las tuercas de la culata con el árbol de levas montado. **Hay que restituir esa frase en el paso 5.** |

**Nota: 4,6. Visto bueno: NO, todavía**, por la regresión del paso 5. Los puntos 1 a 3 quedaron bien. Al restituir la frase, la nota final es 4,8 y queda con visto bueno.

## Verificación 2 (16-nov-2026)

✔ El paso 5 volvió a tener el procedimiento previo: escape, admisión y mangueras; PMS de compresión con las marcas alineadas; levas y cadena; vaciar el refrigerante por el drenaje sin abrir el radiador en caliente; aflojar en cruz; y orden y torque del manual de servicio.

**Nota final: 4,8. Visto bueno: SÍ.**
