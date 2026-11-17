# Revisión rápida · cb125f-clutch

Clutch · Honda CB 125F · catálogo honda-cb125f fig. E6-1 · página `motor/cb125f-clutch.html` · hermana `boxer-embrague` (lo heredado sin cambio ya se revisó allá y va resumido)

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 1 avisos.
  - aviso: armado transparente: 4·4 y 8·8 muy juntos (7.9 px de radio); solo se ven al tocar la pieza
- Medición: Bloqueantes: ninguno · Medible NO APRUEBA · Notas estimadas (criterios medibles): 6: 3.5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.63

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Campana del clutch ×1 · 2 Guía de la campana ×1 · 3 Manzana del clutch ×1 · 4 Discos de fricción ×2 · 5 Discos de fricción (tipo B) ×2 · 6 Discos separadores ×3 · 7 Placa de presión ×1 · 8 Placa elevadora ×1 · 9 Varilla del clutch ×1 · 10 Resortes del clutch ×4 · 11 Tornillos de los resortes ×4 · 12 Tuerca de la manzana ×1 · 13 Arandela del eje ×1 · 14 Arandela de la tuerca ×1 · 15 Balinera de la placa elevadora ×1

## Grupos
- **Varilla y balinera**: Varilla del clutch, Balinera de la placa elevadora
- **Resortes y placa elevadora**: Placa elevadora, Resortes del clutch
- **Manzana, discos y placa de presión**: Manzana del clutch, Discos de fricción, Discos de fricción (tipo B), Discos separadores, Placa de presión
- **Campana del clutch**: Campana del clutch, Guía de la campana

## Desarme
1. Cable, tapa y varilla. Afloja el cable y suéltalo del brazo del clutch. Con el motor frío, drena el aceite y quita la tapa derecha (fig. E-5; antes el pedal de freno si estorba). Saca la varilla (9). Al armar: empaque nuevo, 0,9 L y revisa el nivel.
2. Resortes y placa elevadora. Afloja los tornillos (11) en cruz, media vuelta cada uno, hasta soltar los resortes (10). Saca la placa elevadora (8) con su balinera (15). Al armar: en cruz y parejo (torque: manual de servicio).
3. Tuerca de la manzana. Traba la manzana (3) con una herramienta de sujeción y afloja la tuerca (12); saca la arandela (14). Al armar: arandela en su lugar y tuerca al torque del manual de servicio.
4. Manzana y discos. Saca la manzana (3), los discos de fricción (4) de los dos tipos, los separadores (6) y la placa de presión (7). Anota o fotografía el orden en que salen los discos. Al armar: discos de fricción remojados en aceite del motor.
5. Campana. Saca la arandela (13) que quedó en el eje, la campana (1) y su guía (2). Revisa las ventanas y los dientes: si las ventanas tienen escalones, los discos se traban.

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **1 · Campana del clutch** · reutiliza · taller · OUTER COMP., CLUTCH(67T) · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La canasta con la corona de 67 dientes atrás: la mueve el piñón del cigüeñal y en sus ventanas entran las orejas de los discos de fricción (4).
  - sirve: Recibe la fuerza del motor y se la pasa a los discos de fricción.
  - porque: Si las ventanas no tienen escalones, se vuelve a poner; con escalones hondos, campana nueva.
  - cuando: (heredado)
  - fallas: desgaste: Las orejas de los discos marcan escalones en las ventanas.; golpe: Dientes de la corona picados por golpes al cambiar.
  - sintomas: Golpeteo o «clac» al soltar la palanca.; La palanca se siente a saltos al soltarla despacio.
  - arrastra: Ventanas con escalones → los discos de fricción (4) se traban y el clutch arrastra.
  - conecta: 2, 4, 5, 13 · efectos: 0
- **2 · Guía de la campana** · cambia · taller · GUIDE, CLUTCH OUTER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El buje de acero que va en el eje de la caja, dentro de la campana (1).
  - sirve: Deja que la campana gire suelta sobre el eje cuando aprietas la palanca.
  - porque: Si tiene rayas o juego, va nueva; es barata frente a la campana.
  - cuando: Revísala cada vez que saques la campana.
  - fallas: desgaste: Se raya si el aceite está sucio o falta aceite.
  - sintomas: Campana con juego o que cabecea.; Ruido de roce con la palanca apretada.
  - arrastra: Guía gastada → la campana (1) cabecea y gasta los discos de fricción (4) disparejo.
  - conecta: 1, 13 · efectos: 0
- **3 · Manzana del clutch** · reutiliza · taller · CENTER, CLUTCH · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El disco con estrías por fuera y por dentro: por fuera engranan los separadores (6) y por dentro el eje de la caja.
  - sirve: Pasa la fuerza de los discos al eje de la caja.
  - porque: Si las estrías están lisas, se vuelve a poner.
  - cuando: Revísala cada vez que abras el clutch.
  - fallas: desgaste: Las estrías de afuera se marcan con escalones.
  - sintomas: Clutch que arrastra aunque los discos estén buenos.
  - arrastra: Estrías con escalones → los separadores (6) no se deslizan y el clutch arrastra.
  - conecta: 6, 7, 12, 14 · efectos: 0
- **4 · Discos de fricción** · cambia · taller · DISK, CLUTCH FRICTION · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los discos con forro y orejas por fuera. El catálogo trae dos tipos con código distinto: este y el otro tipo (5), dos de cada uno.
  - sirve: Al apretarse contra los separadores (6) pasan la fuerza de la campana (1) a la manzana (3).
  - porque: Gastados, o brillantes y duros (vitrificados), van nuevos, el juego completo de los dos tipos.
  - cuando: Revísalos cuando patine con el juego libre bien ajustado.
  - fallas: desgaste: El forro se gasta con el uso y más si usas mucho la palanca a medias.; calor: Aceite para carro o viejo: se vitrifican y resbalan.
  - sintomas: El motor sube de vueltas y la moto no avanza igual (patina), sobre todo en subida.; Olor a quemado después de mucho clutch.
  - arrastra: Discos gastados → los resortes (10) se calientan y se cansan.
  - conecta: 1, 5, 6 · efectos: 0
- **5 · Discos de fricción (tipo B)** · cambia · taller · DISK, CLUTCH FRICTION · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El segundo tipo de disco de fricción que trae el catálogo, con otro código; van dos.
  - sirve: Trabaja igual que los discos de fricción (4) del otro tipo; va en el lugar que indica el manual de servicio.
  - porque: Va nuevo junto con los del otro tipo.
  - cuando: Revísalo con los demás discos.
  - fallas: armado: Ponerlo en el lugar del otro tipo cambia cómo agarra el clutch.
  - sintomas: Puede agarrar a saltos si quedó en el puesto equivocado.
  - arrastra: Disco en el puesto equivocado → el clutch agarra a saltos y los discos se gastan disparejo.
  - conecta: 4, 6 · efectos: 0
- **6 · Discos separadores** · reutiliza · taller · PLATE, CLUTCH · 3 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los discos lisos de acero con estrías por dentro; van tres, entre los de fricción.
  - sirve: Hacen de cara de apoyo para los discos de fricción y giran con la manzana (3).
  - porque: Si están planos y sin color azul, se vuelven a poner.
  - cuando: Revísalos cada vez que cambies los discos de fricción.
  - fallas: calor: Se azulan y se tuercen cuando el clutch patina mucho.
  - sintomas: Clutch que arrastra: la moto se mueve con la palanca apretada.
  - arrastra: Separador torcido → los discos de fricción (4) siguen rozando con la palanca apretada.
  - conecta: 3, 4, 5 · efectos: 0
- **7 · Placa de presión** · reutiliza · taller · PLATE, CLUTCH PRESSURE · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La placa de adentro con cuatro torres: ahí roscan los tornillos (11) que comprimen los resortes (10).
  - sirve: Aprieta el paquete de discos contra la manzana (3) con la fuerza de los resortes.
  - porque: Si la cara está plana y las roscas sanas, se vuelve a poner.
  - cuando: Revísala cada vez que abras el clutch.
  - fallas: calor: Se azula y se tuerce cuando el clutch patina mucho.
  - sintomas: Patina aunque los discos sean nuevos.; Agarra disparejo.
  - arrastra: Placa torcida → aprieta disparejo y los discos de fricción (4) patinan.
  - conecta: 3, 10, 11, 4 · efectos: 0
- **8 · Placa elevadora** · reutiliza · taller · PLATE, CLUTCH LIFTER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La placa de afuera con cuatro orejas: lleva la balinera (15) en el centro y los cuatro tornillos (11).
  - sirve: Recibe el empuje de la varilla (9) y aleja la placa de presión (7) para soltar los discos.
  - porque: Si no está torcida ni rajada, se vuelve a poner.
  - cuando: Revísala cada vez que abras el clutch.
  - fallas: desgaste: El alojamiento de la balinera se agranda.
  - sintomas: Clutch que no suelta parejo.
  - arrastra: Placa torcida → la placa de presión (7) se va de lado y el clutch arrastra.
  - conecta: 15, 11, 10, 9 · efectos: 0
- **9 · Varilla del clutch** · reutiliza · taller · ROD, CLUTCH LIFTER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La varilla corta de acero que va entre el brazo del clutch, en la tapa, y la balinera (15).
  - sirve: Pasa el movimiento del cable a la placa elevadora (8).
  - porque: Si está recta y con la punta sana, se vuelve a poner.
  - cuando: Revísala cada vez que quites la tapa derecha.
  - fallas: desgaste: La punta se gasta o se dobla.
  - sintomas: Palanca dura o que no suelta del todo.
  - arrastra: Varilla gastada → falta recorrido y el clutch arrastra.
  - conecta: 8, 15 · efectos: 0
- **10 · Resortes del clutch** · cambia · taller · SPRING, CLUTCH · 4 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los cuatro resortes que van entre la placa elevadora (8) y la manzana (3); por dentro de cada uno pasa una torre de la placa de presión (7).
  - sirve: Aprietan los discos para que el clutch no patine.
  - porque: Si están más cortos que el límite del manual de servicio, van nuevos los cuatro.
  - cuando: (heredado)
  - fallas: calor: Se cansan (pierden largo) con el calor de patinar.
  - sintomas: Patina con discos buenos.; Palanca muy blanda.
  - arrastra: Resortes cansados → los discos de fricción (4) patinan y se queman.
  - conecta: 7, 8, 11 · efectos: 0
- **11 · Tornillos de los resortes** · reutiliza · basico · BOLT, FLANGE, 6X25 · 4 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los cuatro tornillos con brida que sujetan la placa elevadora (8) y comprimen los resortes (10).
  - sirve: Aprietan la placa elevadora contra las torres de la placa de presión (7).
  - porque: Si la rosca está sana, se vuelven a poner.
  - cuando: Revísalos cada vez que abras el clutch.
  - fallas: armado: Apretados de un solo lado o pasados de torque, tuercen la placa o dañan la rosca.
  - sintomas: Clutch que agarra disparejo si uno quedó flojo.
  - arrastra: Tornillo flojo → la placa elevadora (8) se tuerce.
  - conecta: 8, 10, 7 · efectos: 0
- **12 · Tuerca de la manzana** · reutiliza · taller · NUT, SPECIAL FLANGE, 14MM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tuerca de 14 mm con brida que sujeta la manzana (3) en el eje de la caja.
  - sirve: Impide que la manzana se salga del eje.
  - porque: Si la rosca está sana, se vuelve a poner al torque del manual de servicio.
  - cuando: Revísala cada vez que saques la manzana.
  - fallas: armado: Floja o sin su arandela, se suelta con el uso.
  - sintomas: Ruido metálico en el clutch si quedó floja.
  - arrastra: Tuerca floja → la manzana (3) golpea y daña las estrías del eje.
  - conecta: 3, 14 · efectos: 0
- **13 · Arandela del eje** · reutiliza · taller · WASHER, PLAIN, 17MM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela plana de 17 mm que va en el eje de la caja, entre la campana (1) y la manzana (3) (posición aprox.).
  - sirve: Hace de apoyo para que la manzana no roce contra la campana.
  - porque: Si está plana y sin marcas, se vuelve a poner.
  - cuando: Revísala cada vez que saques la campana.
  - fallas: desgaste: Se gasta y deja juego.
  - sintomas: Campana con juego hacia adentro y hacia afuera.
  - arrastra: Arandela gastada → la manzana (3) roza la campana (1) y se calienta.
  - conecta: 1, 2 · efectos: 0
- **14 · Arandela de la tuerca** · reutiliza · taller · WASHER, 14.1X29X2.8 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela de 14,1 × 29 × 2,8 mm que va debajo de la tuerca (12).
  - sirve: Reparte el apriete de la tuerca sobre la manzana (3).
  - porque: Si está plana y sin grietas, se vuelve a poner.
  - cuando: Revísala cada vez que quites la tuerca.
  - fallas: armado: Si falta o va al revés, la tuerca no queda firme.
  - sintomas: Tuerca que se afloja.
  - arrastra: Sin arandela → la tuerca (12) se afloja.
  - conecta: 12, 3 · efectos: 0
- **15 · Balinera de la placa elevadora** · cambia · taller · BEARING, RADIAL BALL, 6003 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La balinera 6003 que va en el centro de la placa elevadora (8).
  - sirve: Deja que la placa elevadora gire con el clutch mientras la varilla (9) la empuja sin girar.
  - porque: Si suena o gira áspera, va nueva.
  - cuando: Revísala cada vez que abras el clutch.
  - fallas: desgaste: Se seca o se le mete mugre del aceite viejo.
  - sintomas: (heredado); Palanca áspera.
  - arrastra: Balinera trabada → la varilla (9) se gasta en la punta.
  - conecta: 8, 9 · efectos: 0

## Cómo funciona
1. 1 · Ralentí en neutro. Con la palanca suelta, los resortes aprietan los discos. El cigüeñal mueve la campana y esta mueve el eje de la caja; en neutro, la rueda no se mueve.
2. 2 · Aprietas la palanca. El cable gira el brazo del clutch en la tapa, la varilla empuja la placa elevadora y la placa de presión se aleja: los discos se separan y el eje de la caja se queda quieto.
3. 3 · Metes primera. Con los discos sueltos el eje está quieto y el cambio entra sin golpe. Si suena «clac» fuerte, el clutch está arrastrando.
4. 4 · Sueltas despacio. En el punto de fricción los discos se rozan y patinan un poco: el eje arranca despacio y la moto sale suave. Aquí es donde más se gastan.
5. 5 · Palanca suelta. Los resortes aprietan del todo: el eje gira con la campana y toda la fuerza va a la rueda.

## Si falla
- **Cable sin juego libre**: Varilla del clutch: El cable queda tenso y la varilla sigue empujando la placa elevadora. → Placa de presión: La placa de presión no aprieta del todo los discos. → Discos de fricción: Los discos patinan en subida y se queman. → Discos separadores: Los separadores se recalientan, se azulan y se tuercen.
- **Aceite viejo o equivocado**: Discos de fricción: Con aceite para carro o muy viejo, los discos resbalan y se vitrifican. → Resortes del clutch: El calor de patinar cansa los resortes. → Placa de presión: La placa de presión se azula y aprieta disparejo: patina aunque cambies los discos.
- **Campana con escalones**: Campana del clutch: Las orejas de los discos marcan escalones en las ventanas de la campana. → Discos de fricción: Los discos se traban en los escalones y no se separan bien. → Discos separadores: Los separadores siguen arrastrando: la moto se mueve con la palanca apretada. → Manzana del clutch: Los separadores, al trabarse, también marcan escalones en las estrías de la manzana.

## Cuándo
- Cambiar el aceite del motor (baña el clutch): Cada 4.000 km o cada 1 año (el primero, a los 1.000 km). Aceite para moto 10W-30, 0,9 L (JASO MA, API SG o superior). · Manual del propietario Honda CB125F Twister (español), copia entregada por el usuario, cuadro de mantenimiento (pág. 35-36 del manual; columnas 1.000 / 4.000 … 24.000 km, anual y sustitución normal; círculo gris = revisar, figura oscura = cambiar), fila 'Aceite del motor' (cambiar a los 1.000 km, en cada columna desde los 4.000 y en la anual); consultado el 14-nov-2026 Seguro
- Revisar el juego libre de la palanca: 10 - 20 mm en la punta de la palanca; ajústalo con la tuerca del cable si se sale de ahí. · Manual del propietario Honda CB125F (español), pp. 74-75. Seguro
- Revisar discos y resortes: Cuando patine con el juego libre bien ajustado. · Práctica de taller. Aproximado

## Fuentes y certezas
- Seguro: Números, nombres, códigos y cantidades de las 15 piezas: catálogo de partes Honda CB 125F GLH125SH, fig. E-6-1 «Clutch» (p. 15).
- Seguro: Medidas de las arandelas (17 mm; 14,1 × 29 × 2,8 mm), de la tuerca (14 mm) y de la balinera (6003): descripción del catálogo, fig. E-6-1.
- Seguro: Aceite SAE 10W-30, JASO MA, 0,9 L, cada 4.000 km o un año, y juego libre de la palanca de 10 - 20 mm: manual del propietario Honda CB125F (español), pp. 35-36 y 74-75.
- Aprox.: Proporciones, vista y orden del dibujo: deducidos del plano del catálogo, en vista caballera con el eje de la caja hacia ti, como los otros clutch.
- Aprox.: Orden interno (placa de presión adentro, manzana y placa elevadora afuera, guía y arandela de 17 mm detrás de la campana): deducido del plano y de la práctica de taller.
- Aprox.: Torques, largo libre de los resortes, espesor de los discos y en qué puesto va cada tipo de disco: no están en el manual del propietario; van como «manual de servicio».

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-cb125f.pdf` (122 págs.): págs. del PDF 71 (impresa ?, 2 piezas), 76 (impresa ?, 2 piezas), 95 (impresa ?, 3 piezas), 96 (impresa ?, 2 piezas), 101 (impresa ?, 2 piezas), 117 (impresa 109, 2 piezas)
- `manual-usuario-cb125f.pdf` (123 págs.): págs. del PDF 75 (impresa ?, 2 piezas), 92 (impresa ?, 2 piezas), 94 (impresa ?, 3 piezas), 95 (impresa ?, 2 piezas), 100 (impresa ?, 2 piezas), 116 (impresa 107, 2 piezas)
  claves buscadas: arandela, balinera, campana, clutch, discos, manzana, placa, resortes, tornillos, tuerca, varilla

## Pendientes de la creadora
- Confirmar con el manual de servicio el orden interno y en qué puesto van los discos de fricción de los dos tipos (refs. 4 y 5).
- Torques de los tornillos de los resortes y de la tuerca de la manzana, largo libre de los resortes y espesor mínimo de los discos: manual de servicio.
- La tapa derecha del motor (fig. E-5) y el brazo del clutch quedan para otra lámina.
- Posición de la arandela de 17 mm (ref. 13): el texto la pone entre campana y manzana (aprox.), pero el dibujo del despiece la saca detrás de la campana; confirmar con el manual de servicio y mover su despiece.
- Medición a 1024: botones de enlace «Varilla del clutch» de 22 px de alto (menos de 44): el CSS del motor solo da 44 px a .esq-enlaces/.esq-efecto bajo 700 px; aviso a Auxiliares.
