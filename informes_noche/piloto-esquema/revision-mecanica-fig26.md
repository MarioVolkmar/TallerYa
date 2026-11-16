# Revisión mecánica: fig. 26 de la NMAX 155 BBE4, «Bombas de freno y líquido»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig26.json` entero: 49 números, 17 pasos, 7 de «Cómo funciona», 4 cadenas, «Cuándo», `sujeta` y los pendientes. Lo comparé con mi rúbrica del freno (fig. 26: dos mangueras por rueda con ABS, banjo con 4 arandelas por manguera), con `garaje/intervalos/yamaha_nmax_155.json`, con `despiece_fichas.py` y con `autocontrol-mecanico.md`. La UX no se califica aquí. No releí el catálogo.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad de las piezas y del armado | **4** | La línea tiene la forma correcta: bomba → manguera 1 o 3 → ABS → manguera 2 o 4 → cáliper. Cada manguera lleva 2 pernos banjo y 4 arandelas. La manigueta delantera es la LEVER 2, a la derecha, y la trasera la LEVER 1, a la izquierda. `sujeta` es coherente con el desarme. Las posiciones de los soportes 44 a 48 son aproximadas, y está declarado. |
| 2 | Exactitud mecánica | **4** | «Cómo funciona» es excelente. **Hay un error de intervalo** (cambio 1), el mismo que tuvo la v1 del freno. |
| 3 | Pedagogía | **5** | Explica el orificio de compensación (al primer milímetro el líquido vuelve al depósito y luego la copa primaria lo encierra), las copas primaria y secundaria, el resorte, el interruptor (émbolo hundido con la manigueta suelta), el nivel que baja con las pastillas y el diafragma, y el aire que se comprime. Las 4 cadenas son reales y útiles, en especial la del orificio tapado que deja el freno pegado. |
| 4 | Congruencia | **4** | El líquido cada 2 años y las mangueras cada 4 coinciden con el plan. Pero la fila «Nivel del líquido» de «Cuándo» **está repetida 5 veces** (cambio 2), y el intervalo de los kits no coincide con el manual. |
| 6 | Reglas | **5** | Ningún torque inventado: todos dicen «manual de servicio», con 0 apariciones de «N·m». Separa bien lo seguro de lo aproximado y los pendientes están declarados. |

**Promedio: 4,4. Visto bueno: NO, por ahora.** Hay un error de intervalo frente al manual. Con los cambios 1 y 2, los criterios 2 y 4 suben a 5 y el promedio queda en 4,8.

## Cambios pedidos

1. **Error de intervalo: kits de las bombas (2 y 22).** El manual B6Y4, en la p. 9-7, dice «cada dos años cambie los componentes internos de las bombas de freno y de las pinzas», y en la p. 9-25 dice «Juntas de freno: cada 2 años».
   - Hoy `cuando` de los kits (`nmax-fig26.json:1858` y `:2608`) dice «Cuando la manigueta se hunde sin fuga visible…».
   - Debe decir: **«Cada 2 años, junto con el cambio de líquido (manual), o antes si la manigueta se hunde sin fuga visible»**, con certeza «Seguro».
   - Agregar esa fila a «Cuándo».
   - En la ficha de las bombas 1 y 21, «se revisa cada vez que se cambia el líquido» puede quedar.
2. **«Cuándo» con la fila repetida.** «Nivel del líquido en los dos depósitos: mirar» aparece 5 veces (`:4425` y siguientes). Debe quedar una sola. Es un dato para el validador (autocontrol, pregunta 3 [S]: sin filas duplicadas).
3. **Verificar con la tabla.** Las fichas 1 y 21 (`:1714` y `:2464`) dicen que la bomba completa «ya trae el kit, la manigueta y la abrazadera». La manigueta (7 y 27) y la abrazadera (10 y 30) tienen número propio. Solo vienen incluidas si en la tabla del catálogo aparecen con punto (·) debajo del MASTER CYLINDER ASSY. Si no, la frase debe decir «trae el kit; manigueta y abrazadera van aparte».
4. **Menor.** La ficha 7 (`:2164`) dice «perno (8) y tuerca (9) nuevos». La tuerca autoblocante sí va nueva, pero el perno se reutiliza si no tiene desgaste. Así queda alineado con la ficha 8.

## Pendientes de la creadora: qué es lo correcto

- **Nivel del líquido, ¿cada semana o cada mes?** Ninguna de las dos.
  - El manual del propietario de Yamaha pone el nivel del líquido de frenos en las **comprobaciones previas a cada uso**, es decir, antes de salir.
  - Lo que pone la lámina («antes de salir, por el visor con el manubrio recto») es lo correcto. Debe citarse como **manual (comprobaciones previas)**, no como «práctica de taller».
  - Hay que confirmar la página del B6Y4 al poder abrirlo.
  - El error está en los borradores: `garaje/despiece_fichas.py:62` y `:68` dicen «cada semana», y `despiece_guia_mecanica.py` dice «cada mes». Hay que unificarlos en «antes de salir».
- **«Pedal» trasero.** `despiece_fichas.py:67` dice: «cuando pisas el pedal (o aprietas la manigueta izquierda, en las scooter)». Es una ficha **genérica**, para todas las motos, y ya cubre la scooter, así que **no es un error** para la NMAX. En la lámina de la NMAX debe decir solo «manigueta izquierda». No hay ningún «pedal» en `nmax-fig26.json`: la única mención está en los pendientes.
- **Torques:** están todos marcados como faltantes. ✔
- **Soportes 44 a 48:** la posición es aproximada y está declarada. No lo castigo. Se confirma con una foto de la moto o con el manual de servicio.

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| 1 | Kits 2 y 22 cada 2 años | ✔ El campo `cuando` de las dos fichas dice «Cada 2 años, con el cambio del líquido (pp. 9-7 y 9-25), o antes si la manigueta se hunde», con certeza «ok». También tienen su propia fila en «Cuándo», marcada «Seguro». |
| 2 | Fila del nivel | ✔ Ahora hay una sola: «Antes de cada salida…», citando las comprobaciones previas del manual. «Cuándo» quedó con 4 filas y ninguna se repite. |
| 3 | Contenido de la bomba completa | ✔ Las fichas 1 y 21 enumeran lo que lleva punto en el catálogo (refs. 2-13 y 22-33, según el cruce de piloto-esquema): kit, tapa, placa, diafragma, tornillos, manigueta con perno y tuerca, abrazadera e interruptor. |
| 4 | Manigueta | ✔ Las fichas 7 y 27 dicen: tuerca autoblocante nueva, y el perno se reutiliza si no está gastado. |
| + | Borradores del sitio | ✔ `despiece_fichas.py:62` y `:68`, y `despiece_guia_mecanica.py:66` y `:70`, dicen «antes de cada salida». Los otros «cada semana» que quedan en esos archivos son de otros sistemas (refrigerante, presión de llantas), no del líquido de frenos. |

**Nota final: 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **Visto bueno: SÍ.**
