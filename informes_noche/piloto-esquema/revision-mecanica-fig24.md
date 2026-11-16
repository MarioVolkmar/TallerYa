# Revisión mecánica: fig. 24 de la NMAX 155 BBE4, «Freno trasero»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig24.json`: 15 números, 14 pasos, «Cuándo», 5 cadenas y las fichas. Busqué sobre todo restos del freno delantero (fig. 22). Solo califico lo mecánico.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Los nombres del catálogo son los traseros (DISK, REAR BRAKE 2; CALIPER ASSY, REAR 2; BOLT, FLANGE; SHIM ×2). El disco tiene agujeros ovalados, el soporte va en el brazo trasero y las mangueras son la 34 y la 38 de la fig. 26. **Queda un resto del delantero** en la lámina antirruido (cambio 1). |
| 2 | Exactitud mecánica | **4** | El cáliper flotante, el sello que devuelve el pistón, el ABS, el DOT 4 y la manigueta **izquierda** («en la NMAX la izquierda es el freno trasero») están bien. Lo único que falla es la cantidad y la posición de las láminas 14. |
| 3 | Pedagogía | **5** | Es igual de clara que la fig. 22. La cadena de tornillos flojos después de montar la rueda es muy oportuna para el freno trasero. |
| 4 | Congruencia | **5** | Pastillas a los 1.000 km y cada 6.000 km, líquido y empaques de la bomba y del cáliper cada 2 años (pp. 9-7 y 9-25), mangueras cada 4 años. |
| 6 | Reglas | **5** | El disco de 230 mm, el contorno del brazo y los torques están marcados «aprox.» o «sin dato». Las fuentes están citadas. |

**Promedio: 4,6. Visto bueno: NO, por ahora.** La lámina antirruido quedó como en el delantero. Corregirla toma dos líneas y con eso la nota sube a 4,8.

## Restos del delantero
Busqué «derech», «barra», «horquilla», «suspensión», «LEVER 2», «manigueta derecha» y «pedal»: **0 apariciones**. Las 2 veces que aparece «delantero» son en las fuentes, como comparación o como base del dibujo, y están bien. **El único resto es el de la lámina antirruido:**

1. **Lámina antirruido (14): el catálogo dice 2, una por pastilla, pero el texto todavía describe una sola.**
   - El paso 6 dice: «Va detrás de la pastilla del lado del pistón».
   - La ficha 14 (`que`) dice: «Una lámina delgada detrás de la pastilla, entre ella y el pistón».
   - Debe decir: **«Dos láminas, una detrás de cada pastilla: la de adentro entre la pastilla y el pistón, la de afuera entre la pastilla y el cuerpo del cáliper. Al armar, cada una en su pastilla.»**
   - En el dibujo del despiece se deben ver las dos.

## Dudas de la creadora
- **Pastillas: ¿6.000 u 8.000 km?** Va **6.000 km**, como dice el manual de la NMAX (revisión a los 1.000 km y luego cada 6.000 km), y es lo que ya pone la lámina. Los 8.000 km son de la tarea general «Pastillas de freno traseras» de TallerYa, que no es específica de la NMAX. Hay que anotarlo como contradicción para el equipo: el plan de la NMAX debería usar 6.000.
- **Disco de 230 mm:** que siga como aproximado. El catálogo le da al trasero un código propio (DISK, REAR BRAKE 2), así que la forma es distinta aunque el diámetro pueda coincidir. La medida se confirma con la ficha técnica de la BBE4 o midiéndolo.
- **Brazo trasero:** el contorno es aproximado y está declarado. No lo castigo.

## Para verificar (no lo castigo)
2. **Cadena «Retén de la transmisión final que bota aceite».** Solo es creíble si el retén queda **del mismo lado que el disco**. En las scooters, el disco suele ir del lado contrario a la caja de la transmisión final, y el aceite de ese retén moja el cubo de su lado, no el disco.
   - Confirmar con las fotos de `manual_despiece/yamaha_nmax155/fotos/` de qué lado van el disco y el cáliper.
   - Si están en lados opuestos, reemplazar la cadena por una que sí moje el disco: líquido de frenos de una fuga en el purgador o en la manguera, o un lavado con desengrasante o aceite en spray.
3. **Menor:** en `nombres`, la pieza 1 se llama «disco», en minúscula y sin calificativo. Mejor «Disco de freno trasero».

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| 1 | Dos láminas antirruido | ✔ Hay dos piezas, la 14a y la 14b. El paso 6 y la ficha 14 dicen «dos, una detrás de cada pastilla: la de adentro contra el pistón y la de afuera contra el cuerpo». |
| 2 | Cadena del retén | ✔ Según la grilla, el soporte del cáliper se atornilla a la caja de la transmisión final, del lado izquierdo, que es el mismo del disco. Así, el aceite del retén del eje sí puede llegar al disco y la cadena es creíble. El contexto ahora se llama «Caja de la transmisión final» y el paso 1 dice que los tornillos van a esa caja. En lo que se ve en la página ya no dice «brazo»; solo queda como identificador interno (`brazo`), que no se muestra. |
| 3 | Nombre de la pieza 1 | ✔ «Disco de freno trasero». |

**Nota final: 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **Visto bueno: SÍ.**
