# Revisión mecánica: piloto CVT de la NMAX 155 BBE4 (fig. 12 «Variador, correa y clutch»)

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig12.json` completo: nombres, 15 pasos, «Cómo funciona», fichas, 5 cadenas, «Cuándo» y fuentes. También miré `motor/prueba-nmax-fig12.html` a 1024 px, en el armado, en el despiece completo y en «Cómo funciona» (paso 5).

Comparé contra `garaje/intervalos/yamaha_nmax_155.json` (que cita el manual B6Y4), `garaje/despiece_fichas.py` y el funcionamiento estándar de una CVT de scooter.

No pude abrir la tabla del catálogo (el PDF de `despiece_local/` ni la base local): el permiso de esta sesión no lo deja. Por eso no castigo nombres ni cantidades. La UX no se califica aquí.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad de las piezas y del armado | **4** | En el armado se ven, sin la tapa, la polea de aletas adelante, la campana atrás y la correa dentada entre las dos. En el despiece están los 6 rodillos en anillo, la rampa de 3 brazos con 3 deslizadores, el portazapatas de 3 lóbulos con 3 zapatas y 3 resortes, la polea trasera fija (con eje largo) y la móvil, y el resorte de torque. Solo hay una forma dudosa: el «rodamiento del portazapatas» (21) con su anillo de seguro (22), ver el cambio 2. |
| 2 | Exactitud mecánica | **4** | El funcionamiento está muy bien. **Un error:** las fichas no coinciden sobre dónde están las ranuras de la leva de torque (cambio 1). Hay además dos precisiones (cambios 2 y 3). |
| 3 | Pedagogía | **5** | Los 7 pasos de «Cómo funciona» son claros: ralentí, enganche, relación corta, los rodillos salen, crucero, «baja el cambio» solo con carga, soltar. Las tres vistas se ayudan entre sí: la correa vista de lado con los radios cambiando, el variador cortado y el clutch de frente, con zapatas naranja cuando agarran. «Campana va con la rueda / zapatas van con la polea» lo deja muy claro. Las analogías «como una primera» y «como una quinta» funcionan. |
| 4 | Congruencia | **5** | La correa cada 18.000 km con el indicador V-BELT y el filtro de la caja cada 6.000 km coinciden con el plan de la NMAX (`correa-cvt`, aproximado:false) y con el manual. Rodillos, zapatas y campana «con la correa» coinciden con las fichas de TallerYa (WEIGHT SET, CLUTCH WEIGHT SHOE). Lo que es guía o práctica de taller está marcado «Aproximado». |
| 6 | Reglas | **5** | El dibujo es propio y no tiene emblemas. Las fuentes están separadas en seguro y aproximado. Las rpm de ralentí y de enganche, la medida de los rodillos y la referencia de la correa van como aproximadas. No inventa torques, sino que remite al manual de servicio. |

**Promedio (sin el criterio visual, que es de UX): 4,6. Visto bueno: NO, todavía**, por el error del cambio 1. Se corrige en dos frases. Con eso, el criterio 2 sube a 5 y el visto bueno queda.

## Lo que está bien (no tocar)

- **Orden del desarme:** tapa → tuerca y polea de aletas → tuerca y campana → conjunto trasero con la correa → correa → polea móvil con su contenido → buje, rampa, rodillos → portazapatas con el compresor → zapatas → resorte → mitades de la polea trasera. Es el orden real.
  - Incluye avisos útiles: sujetar la polea de aletas para que no gire el cigüeñal, y soltar el compresor de a poco.
- **Variador:** los rodillos salen por su peso, suben y empujan la polea móvil hacia la fija. La correa sube adelante y baja atrás, contra el resorte (18).
- **Leva de torque:** con carga, cierra la polea trasera y la moto «baja el cambio» sola (paso 6, con más rpm y menos `rf`). Muy bien explicado.
- **Clutch:** la fuerza centrífuga le gana a los resortes, las zapatas tocan la campana y es en el enganche cuando más se gastan. Al soltar, la campana sigue girando con la rueda.
- **Ficha 23:** el rodamiento de agujas deja girar la polea trasera sobre el eje con el clutch suelto. Correcto.
- **«Si se repara o se cambia»:**
  - rodillos y deslizadores siempre en juego completo y del peso original;
  - zapatas con resortes nuevos y revisión de la campana (escalón);
  - polea trasera con retenedores y O-rings nuevos;
  - reiniciar el indicador V-BELT.
- **Cadenas:** las 5 tienen causa y efecto correctos, incluida la grasa de la polea trasera que llega a la correa y a las zapatas, y la caja tapada que recalienta la correa y los rodillos.

## Cambios pedidos (en orden de prioridad)

1. **Error: dónde están las ranuras de la leva de torque.** Hoy las fichas se contradicen:
   - ficha 12 (`nmax-fig12.json:1638`): «En el eje tiene las ranuras de la leva de torque»;
   - ficha 13: «en su centro tiene tres ranuras inclinadas»;
   - ficha 16 (`:1811`): pasadores que «atraviesan la polea móvil».

   En la CVT de scooter, las **ranuras inclinadas están en el cuello de la polea móvil (13)**, y los **pasadores guía (16) con sus rodillos (17) van fijos en el eje hueco de la polea fija (12)** y corren por esas ranuras.
   - Ficha 12: «En su eje van fijos los pasadores guía (16)».
   - Ficha 16: «Van clavados en el eje de la polea fija (12) y corren por las ranuras de la polea móvil (13)».
   - Verificación: ningún texto dice que las ranuras están en la polea fija.
2. **Qué sujeta el portazapatas (paso 12, `:1009`, y fichas 21-22, `:1997`).** En las CVT Yamaha de este tipo, el portazapatas se sujeta al eje de la polea fija con una **tuerca grande** del portazapatas. Para soltarla se usa el compresor del resorte y una llave especial. No lo sujeta un rodamiento con un anillo de seguro.
   - Cuando se cruce la tabla, revisar si el 21 o el 22 es esa tuerca.
   - Mientras tanto, el paso 12 debería decir «se suelta la tuerca del portazapatas (posición aproximada)».
   - Esto **no se castiga**: depende de la tabla que falta.
3. **Precisión sobre la rampa (fichas 1 y 3, `:1117` y `:1239`).** Las rampas curvas por donde suben los rodillos están sobre todo en los **seis canales de la polea móvil (1)**. La placa (3) es la pared de atrás, casi plana, y los rodillos quedan acuñados entre las dos.
   - Propuesta para la ficha 3: «Placa fija contra la que se apoyan los rodillos; ellos ruedan por las rampas de los canales de la polea móvil y la empujan hacia la fija».
   - En el paso 4, «suben por la rampa» puede quedar si la ficha lo aclara.
4. **Menor: limpieza a los 6.000 km (ficha 1, `:1138`).** «Se limpia el polvo de correa en cada revisión del filtro de la caja» es práctica de taller, no del manual. Marcarla así en la certeza.

## Nota sobre los datos que faltan
Cuando se cruce la tabla del catálogo, revisar primero 20, 21, 22 (la sujeción del portazapatas), 19 (asiento del resorte) y 26, 27 y 33 (las arandelas del variador). Son las que tienen más probabilidad de cambiar de nombre.

## Verificación (16-nov-2026, después de las correcciones)

Revisé `motor/datos/nmax-fig12.json` (y los comentarios de `nmax-fig12-arte.js`):

| # | Punto | Estado |
|---|---|---|
| 1 | Leva de torque | ✔ Las fichas 12, 13, 16 y 17, el paso 15 y el paso 6 de «Cómo funciona» dicen lo mismo: las ranuras están en el cuello de la polea móvil (13) y los pasadores (16) con sus rodillos (17) van fijos en el eje de la polea fija (12). Ya no queda ningún texto con las ranuras en la fija («eje tiene las ranuras» y «atraviesan»: 0 apariciones). |
| 2 | Sujeción del portazapatas | ✔ El paso 12 dice compresor + llave especial + tuerca grande (21) con arandela (22). Las fichas 21 y 22 son coherentes («mantiene comprimido el resorte de torque») y están marcadas «aprox.». |
| 3 | Rampas en la polea móvil | ✔ La ficha 1 habla de canales inclinados que son las rampas. La ficha 2 dice que los rodillos suben por esos canales y empujan porque la placa no se mueve. La ficha 3 describe la placa como casi plana, la pared de atrás. Lo mismo dicen el paso 9, el paso 4 de «Cómo funciona» y la cadena «Rodillos planos» («la placa de atrás también se marca»). |
| 4 | Polea a los 6.000 km | ✔ La ficha 1 dice «Como práctica de taller…» y la certeza está en «ap». |

No encontré errores nuevos en lo que cambió.

**Nota final:** fidelidad 4 · exactitud **5** · pedagogía 5 · congruencia 5 · reglas 5, **promedio 4,8. Visto bueno: SÍ.** Todos los criterios están en 4 o más y no quedan errores mecánicos. Sigue pendiente, aparte, cruzar los nombres y cantidades con la tabla del catálogo.

## Verificación 2 (16-nov-2026, después de cruzar con la tabla del catálogo)

Revisé en `motor/datos/nmax-fig12.json` (y en el arte) que lo mecánico quedara coherente con los nombres nuevos. **No volví a abrir el catálogo**: esta sesión tiene bloqueada esa lectura y el permiso solo lo puede dar el usuario. Tomo como dados los nombres y cantidades que cruzó piloto-esquema.

| # | Cambio | Estado |
|---|---|---|
| a | 9 = amortiguadores de caucho de las zapatas (DAMPER ×3) | ✔ La ficha dice que van en los pasadores del portazapatas, dentro del ojo de cada zapata, y que suavizan el enganche. La causa es el calor (el caucho se endurece) y se cambian con las zapatas. El paso 13 los saca con las zapatas. El dibujo (`arteDamper`) pone uno en cada pasador. Ya no se habla de «pasadores (9)» (0 apariciones). Es correcto para un clutch Yamaha. |
| b | 20 = tuerca del portazapatas | ✔ El paso 12 dice compresor + llave especial + tuerca grande (20). La ficha dice que sujeta el portazapatas y mantiene comprimido el resorte 18, y no da torque. El dibujo es `arteTuerca`. «Placa (20)» ya no aparece. Mi punto 2 queda resuelto con el número correcto. |
| c | 21-22 = rodamiento de bolas del eje de la polea fija y su anillo de seguro | ✔ Salen en el paso 15 con la polea fija y no en el 12. Junto con el de agujas (23), dejan girar la polea trasera sobre el eje con el clutch suelto. Es correcto, y el consejo «se giran con la mano y solo se sacan si suenan» es bueno. |
| d | 15 = segundo par de sellos; 17 = bujes guía | ✔ en el texto: las fichas 13, 14, 15, 16 y 17, el paso 15, «Cuándo» («sellos (14 y 15) nuevos») y la compra. Ya no quedan «O-ring» ni «rodillos (17)». El paso 6 de «Cómo funciona» sigue correcto. |

Detalles menores, que no bloquean el visto bueno:
1. **Dibujo del 15:** todavía usa `arteOrings`, unos aros finos de 2 unidades de sección. Si son sellos, deberían verse como los del 14 (`arteRetenes`): más anchos y con labio.
2. **Nombres:** la cadena «Grasa que se escapa atrás» dice «retenedores» para el 14, y la ficha ahora dice «sellos». Son sinónimos en el taller, pero conviene usar uno solo.

**Nota: se mantiene en 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **El visto bueno se mantiene.** Con los nombres ya del catálogo, la fidelidad podría subir a 5 cuando se arregle el dibujo del 15 y otra revisión con acceso al catálogo confirme el cruce.
