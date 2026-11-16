# Autocontrol mecánico antes de entregar una lámina

Responde sí o no a cada pregunta. Si alguna queda en «no», corrígela antes de entregar. **[S]** = se puede revisar con un script (para `validar_esquema.py`).

Sale de los errores reales del freno (v1, v2, v8) y de la CVT (con sus 2 verificaciones).

## 1. Piezas y catálogo
1. ¿Cada número tiene el nombre y la cantidad de la tabla del catálogo, y no los adivinaste por la forma? Si no hubo tabla, ¿está marcado «aprox.»? **[S]** (`cat` contra la tabla, cantidades)
2. ¿Los datos que salen del catálogo (cantidades, lado derecho o izquierdo) están como «Seguro» y no como «aprox.»? En el freno, los 3 tornillos del disco eran seguros y estaban como dudosos. **[S]**
3. ¿Cada pieza tiene **un solo nombre** en la ficha, los pasos, las cadenas, «Cuándo» y los chips («sello» o «retenedor», no los dos)? **[S]** (comparar con `nombres`)
4. ¿Quedó algún nombre viejo después de renombrar (por ejemplo «O-ring», «placa (20)» o «pasadores (9)»)? **[S]** (grep de los «(N)» contra `nombres`)
5. ¿El dibujo corresponde al tipo de pieza (un sello con labio y no un aro fino; un resorte de lámina y no de alambre; la proporción real de una pastilla)?

## 2. Cómo está montado
6. Para cada parte móvil o guía, ¿dices **en qué pieza va fija y sobre cuál corre**, y lo dices igual en todas las fichas? En la CVT, las ranuras de la leva van en la polea móvil y los pasadores en el eje de la fija.
7. Para cada pieza, ¿dices **qué la sujeta** (tuerca, anillo, rodamiento, tornillo, presión) y que eso exista en la lámina con su número? En la CVT, el portazapatas lo sujeta una tuerca, no un rodamiento.
8. ¿Las **superficies de trabajo** están donde son (rampas, pistas, caras de fricción, el sello del pistón)? En la CVT, las rampas están en la polea móvil y no en la placa.
9. ¿El orden del desarme es el real, y cada pieza sale en el paso en que de verdad queda libre (no antes de quitar lo que la sujeta)? **[S, parcial]** (que cada número salga en algún paso, una sola vez, y que lo que la sujeta salga antes)
10. ¿Hay una herramienta especial o un aviso de seguridad donde hace falta (sujetar la polea, el compresor del resorte, la moto en el gato, el motor frío)?

## 3. Cómo funciona
11. ¿Explicas el principio sin inventar piezas? En el freno, el sello devuelve el pistón y no hay ningún resorte.
12. ¿Las cifras sin fuente dicen «aprox.» o «varias veces» en vez de inventar un número exacto? **[S]** (cifras sin la marca)
13. ¿Los síntomas son de moto, no de carro? En el freno estaba «se va hacia un lado», que con un solo disco no aplica.
14. ¿«Cómo funciona», las fichas y los pasos dicen lo mismo sobre la misma pieza? Lee juntos todos los textos que nombran cada «(N)».
14a. ¿Los síntomas y las causas corresponden a la **tecnología de esta moto** (inyección o carburador, ABS o no, CBS, refrigerada por aire o por agua)? Por ejemplo, con inyección un filtro tapado no da mezcla rica: el computador manda menos gasolina. **[S]** («rica», «chiclé», «carburador» o «ahogador» en una moto con inyección; «purga normal» en una con ABS)
14b. ¿Cada **síntoma corresponde a su causa**? Por ejemplo, el silbido es de aire falso, que entra después de la mariposa. Una grieta antes de la mariposa deja entrar aire sin filtrar, no aire falso.
10a. Si el paso toca gasolina (inyector, tubo, bomba, tanque), ¿pide motor frío, nada de chispas ni cigarrillos, un trapo para la gasolina que sale con presión aunque la moto esté apagada, y revisar que no gotee antes de prender? **[S]** (si un paso dice «gasolina», «inyector» o «combustible», que tenga «chispa» y «gotee»)

## 4. Intervalos y fuentes
15. ¿Cada intervalo de «Cuándo» y de las fichas es **igual** al de `garaje/intervalos/<moto>.json` y al del manual (km y tiempo)? En el freno, los empaques eran cada 2 años y faltaba. **[S]** (cruzar los km y años del texto con el JSON)
16. ¿Lo que dice el manual está como «Seguro» y la práctica de taller como «Práctica de taller» o «Aproximado», sin mezclarlos? **[S, parcial]** (que toda fila tenga fuente y certeza)
17. ¿Registraste las contradicciones con las fichas o el glosario de TallerYa (como en el freno: pastillas a 3.000 km contra 6.000)?
18. ¿No inventas torques, medidas ni referencias? Si no hay fuente, ¿dice «sin dato» o «manual de servicio»? **[S]** (grep de «N·m» o «mm» sin la marca «aprox.»)

## 5. Lo que suele fallar en los sistemas que vienen
- **Motor y válvulas:** ¿las holguras son en frío y salen del manual? ¿Distingues admisión de escape? ¿Las marcas de distribución están en el PMS de compresión, no en el de escape? ¿Tensor automático o manual? ¿La cadena de distribución tiene intervalo propio o solo «revisar ruido»? ¿Los empaques de la culata y los retenes se cambian al abrir, no por kilometraje?
- **Refrigeración:** ¿el refrigerante está en tiempo y en km según el manual? ¿El termostato abre a la temperatura del manual (o «aprox.»)? ¿Dices que la tapa del radiador presuriza y nunca se abre en caliente? ¿La bomba de agua tiene sello mecánico y orificio de testigo? ¿No mezclas tipos de refrigerante?
- **Suspensión:** ¿el aceite de la barra tiene su grado y su nivel (altura de aire), no solo el volumen? ¿El retén y el guardapolvo son piezas distintas? ¿La precarga, la compresión y el rebote solo aparecen si la moto los tiene? ¿El amortiguador trasero de una scooter se cambia entero (no se repara) cuando así lo dice el catálogo?
- **Eléctrico:** ¿la batería es del tipo correcto (sellada o con ácido) y la carga y el voltaje salen del manual? ¿El fusible tiene sus amperios? ¿Regulador y estator son piezas distintas? ¿La bujía tiene su referencia y su holgura del manual? ¿Los síntomas no confunden la batería con el regulador?
- **En todos:** ¿el lado (izquierdo o derecho) y la versión de la moto (ABS, CBS, año) salen del catálogo de esa versión? **[S]** (comparar con el sufijo y el título de la lámina)
