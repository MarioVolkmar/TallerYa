# Revisión v2: piloto del freno delantero NMAX 155 (lámina 22)

Revisora · 15-nov-2026 · revisé `index.html` (es idéntico a `v2.html`, comprobado con `cmp`) a 1024 px y a 360 px. Probé el despiece completo, «Cómo funciona» reproducido y las fichas. Comprobé en el código cada punto de `revision-v1.md`.

## Puntajes

| # | Criterio | v1 | **v2** | Evidencia breve |
|---|---|---|---|---|
| 1 | Fidelidad al plano y a las fotos | 3 | **4** | El soporte 13 ya está en C, con orejas y los dos pasadores cromados. El resorte 11 es una lámina estampada. Las pastillas y la lámina 14 tienen proporción de placa, oreja y ranura. Los tornillos del disco son 3 y van como dato seguro. Queda esquemático el cuerpo del caliper (3): no muestra la ventana de las pastillas ni el puente sobre el disco, como en el plano. |
| 2 | Exactitud mecánica | 4 | **5** | Los empaques se cambian cada 2 años con el líquido, en la tabla, las fichas 3, 4, 5 y del líquido, y la cadena, con la cita de las pp. 9-7 y 9-25. El ABS está bien explicado. Hay dos mangueras con banjo y arandelas nuevas. El sello se raya al meter el pistón sucio. Ya dice «varias veces» y no da una cifra. No encontré errores. |
| 3 | Pedagogía | 4 | **5** | Las fichas están plegadas: a la vista queda lo esencial y el resto va en un desplegable, cerrado en el celular (comprobado: `details.open = false` a 360 px). En el celular, el corte del caliper ahora queda debajo de la bomba, se ve completo y la explicación del ABS se entiende. |
| 4 | Congruencia | 4 | **5** | Hay 11 contradicciones, incluidas las de los empaques, las pastillas «cada 3.000 km» y la manguera «cada año». Los nombres y las cadenas son coherentes con el plan de la NMAX y con el manual. |
| 5 | Calidad visual y celular | 3 | **4** | Sin errores de consola. Sin desborde: scrollWidth 360 a 360 px. El encuadre del despiece se ajusta al contenido. Los números miden 28 px y no se pisan (el par más cercano está a 31 px entre centros). Los botones miden 42 px. **Queda una cosa:** a 360 px los textos del dibujo de «Cómo funciona» miden unos 7 px (su caja mide 8,7 px de alto), y «Sello (lo devuelve)» o «Disco (gira con la rueda)» casi no se leen. |
| 6 | Reglas | 4 | **5** | El dibujo es propio y no tiene emblemas. Las fuentes están citadas. Lo seguro y lo aproximado están bien clasificados (los 3 tornillos ya son seguros; el espesor de 4 mm, el diámetro del pistón y los torques quedan como aproximados o sin dato). |

**Promedio: 4,67. Visto bueno: SÍ.** Todos los criterios están en 4 o más, el promedio pasa de 4,5 y no hay errores mecánicos.

## Verificación de los 12 puntos de la v1

| # | Punto | Estado |
|---|---|---|
| 1 | Empaques cada 2 años (manual) | ✔ En la tabla («Seguro», pp. 9-7 y 9-25), las fichas 3, 4, 5 y del líquido, la cadena y la contradicción 9 |
| 2 | Tornillos del disco: 3, seguro | ✔ `cat:"BOLT · 3 piezas"`, certeza «ok», fuera de los aproximados |
| 3 | «Cómo funciona» en el celular | ✔ El caliper queda debajo de la bomba y el pistón, las pastillas, el disco y la rueda se ven sin deslizar. El texto ya no dice «a la derecha». (Los textos siguen pequeños: ver abajo.) |
| 4 | Resorte 11 como lámina | ✔ |
| 5 | Pastillas 9 y lámina 14 en proporción | ✔ |
| 6 | Soporte 13 en C con pasadores | ✔ |
| 7 | Tamaño del despiece | ✔ El encuadre se calcula con las posiciones finales y las piezas chicas crecen al salir (a 1024 px: grapa de 24 px y sello de 25×52 px) |
| 8 | Áreas táctiles | ✔ con un detalle: los botones miden 42 px (casi 44) y los números 28 px |
| 9 | Precisiones mecánicas a–d | ✔ las cuatro |
| 10 | Etiqueta del sello y manigueta | ✔ en computador. En el celular la etiqueta ya no se cruza con el disco, pero es diminuta |
| 11 | Contradicciones 9 a 11 | ✔ |
| 12 | Fichas plegadas | ✔ abiertas en computador, cerradas en el celular |

## Retoques recomendados antes de mostrárselo al usuario (no bloquean el visto bueno)
1. **Textos del dibujo de «Cómo funciona» en el celular.** Por debajo de 700 px, subir el `font-size` de `.fn-et` para que se vean de al menos 11 px en pantalla. Con el `viewBox` de 500 de ancho a 307 px, eso es más o menos 18 unidades del SVG. Si alguno no cabe, acortarlo («Sello: lo devuelve»).
   - Verificación: a 360 px, la altura mínima de las cajas de `#funciona svg text` debe ser de 13 px o más.
2. Botones a `min-height: 44px` (hoy miden 42).
3. Opcional: darle al cuerpo del caliper (3) la ventana superior por donde se ven las pastillas. Ayuda a reconocerlo en la moto real.
