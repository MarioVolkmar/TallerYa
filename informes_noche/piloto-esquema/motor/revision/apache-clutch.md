<!-- json ca8bd654246c -->
# Revisión rápida · apache-clutch

Clutch · TVS Apache RTR 160 4V · catálogo tvs-apache160-4v fig. 8 · página `motor/apache-clutch.html` · hermana `cb125f-clutch` (lo heredado sin cambio ya se revisó allá y va resumido)

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 1 avisos.
  - aviso: armado transparente: 21·21 y 1·1 muy juntos (0.0 px de radio); solo se ven al tocar la pieza
- Medición: Bloqueantes: ninguno · Medible APRUEBA · Notas estimadas (criterios medibles): 6: 5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.88

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Retén de la campana ×1 · 2 Campana del clutch ×1 · 3 Buje de la campana ×1 · 4 Placa de presión ×1 · 5 Discos de fricción ×2 · 6 Discos de fricción (tipo B) ×3 · 7 Discos separadores ×5 · 8 Asiento del resorte antibrinco ×1 · 9 Resorte antibrinco ×1 · 10 Resortes del clutch ×3 · 11 Arandela espaciadora ×1 · 12 Manzana del clutch ×1 · 13 Placa de los resortes ×1 · 14 Tornillos de los resortes ×3 · 15 Arandela de la tuerca ×1 · 16 Tuerca de la manzana ×1 · 17 Balinera de la placa de los resortes ×1 · 18 Pin adaptador ×1 · 19 Balín ×1 · 20 Pin empujador ×1 · 21 Arandela de atrás de la campana ×1 · 22 KIT CLUTCH COMPL. Fig.4,5,6,7,8,9,10,12,13,14) ×1

## Grupos (nombre (id); tornillería aparte)
- **Pines, balín y balinera** [mando]: Pin empujador (20), Balín (19), Pin adaptador (18), Balinera de la placa de los resortes (17)
- **Resortes y placa de los resortes** [resortes]: Placa de los resortes (13), Resortes del clutch (10) · Tornillos de los resortes (14)
- **Manzana, discos y placa de presión** [discos]: Manzana del clutch (12), Discos de fricción (5), Discos de fricción (tipo B) (6), Discos separadores (7), Resorte antibrinco (9), Asiento del resorte antibrinco (8), Placa de presión (4) · Tuerca y arandela de la manzana (16, 15)
- **Campana del clutch** [campana]: Campana del clutch (2), Buje de la campana (3), Retén de la campana (1) · Arandelas del eje (11, 21)

## Desarme
1. Cable, tapa y pines. Afloja el cable y suéltalo del brazo del clutch. Con el motor frío, drena el aceite y quita la tapa del clutch (fig. 6). Saca el pin empujador (20), el balín (19) y el pin adaptador (18). Al armar: empaque nuevo y 1,2 L de 10W-30 JASO MA2.
2. Resortes y placa. Afloja los tres tornillos (14) en cruz, media vuelta cada uno, hasta soltar los resortes (10). Saca la placa de los resortes (13) con su balinera (17). Al armar: en cruz y parejo (torque: manual de servicio).
3. (heredado)
4. Manzana y discos. Saca la manzana (12), los discos de fricción (5) de los dos tipos, los separadores (7), el resorte antibrinco (9) con su asiento (8) y la placa de presión (4). Fotografía el orden. Al armar: discos remojados en aceite del motor.
5. Campana. Saca la arandela (11) que quedó en el eje, la campana (2), su buje (3), el retén (1) y la arandela (21) de atrás. Revisa las ventanas y los dientes: si las ventanas tienen escalones, los discos se traban.

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **1 · Retén de la campana** · cambia · taller · RETEN CORONA CLUTCH · 1 pieza · aprox.: que, sirve, sintomas, fallas, porque, cuando
  - que: El aro que va junto al cubo de la campana (2) (posición aprox.).
  - sirve: Mantiene la campana y su buje (3) en su sitio sobre el eje (posición aprox.).
  - porque: Es barato: si está gastado, marcado o deformado, va nuevo.
  - cuando: Revísalo cada vez que saques la campana.
  - fallas: calor: Se gasta o se deforma y deja juego a la campana.
  - sintomas: Campana con juego o que suena al soltar la palanca.
  - arrastra: — falta
  - conecta: 2, 3 · efectos: 0
- **2 · Campana del clutch** · reutiliza · taller · CORONA CLUTCH · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La canasta con la corona dentada atrás: la mueve el piñón del cigüeñal y en sus ventanas entran las orejas de los discos de fricción (5).
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado); (heredado)
  - sintomas: (heredado); (heredado)
  - arrastra: (heredado)
  - conecta: 3, 1, 5, 11 · efectos: 0
- **3 · Buje de la campana** · cambia · taller · BUJE · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: (heredado)
  - sirve: (heredado)
  - porque: Si tiene rayas o juego, va nuevo; es barato frente a la campana.
  - cuando: Revísalo cada vez que saques la campana.
  - fallas: (heredado)
  - sintomas: (heredado); (heredado)
  - arrastra: Buje gastado → la campana (2) cabecea y gasta los discos de fricción (5) disparejo.
  - conecta: 2, 11 · efectos: 0
- **4 · Placa de presión** · reutiliza · taller · PORTA RESORTES · 1 pieza · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La placa de adentro, con tres torres que pasan por la manzana (12) y por dentro de los resortes (10); en ellas enroscan los tornillos (14). Entre ella y la manzana van las rampas del slipper.
  - sirve: Aprieta los discos con la fuerza de los resortes; sus rampas ayudan a apretar al acelerar y la sueltan un poco cuando reduces de golpe.
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado); desgaste: Las rampas se marcan o se pican: el slipper deja de trabajar parejo.
  - sintomas: (heredado); Agarra disparejo.; La rueda de atrás brinca al reducir de golpe.
  - arrastra: (heredado)
  - conecta: 12, 10, 14, 5 · efectos: 0
- **5 · Discos de fricción** · cambia · taller · DISCOS CLUTCH (LLEGA 2 UNDS X EMPAQUE) · 2 piezas · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los discos con forro y orejas por fuera. El catálogo trae dos tipos con código distinto: dos de este y tres del otro tipo (6).
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: Revísalos cada 24.000 km, o antes si patina con el juego libre bien ajustado.
  - fallas: (heredado); (heredado)
  - sintomas: (heredado); (heredado)
  - arrastra: (heredado)
  - conecta: 2, 6, 7 · efectos: 0
- **6 · Discos de fricción (tipo B)** · cambia · taller · DISCOS CLUTCH (LLEGA 3 UNDS X EMPAQUE) · 3 piezas · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El otro tipo de disco de fricción; van tres, en los puestos que indica el manual de servicio.
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 5, 7 · efectos: 0
- **7 · Discos separadores** · reutiliza · taller · DISCO SEPARADOR CLUTCH · 5 piezas · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los discos lisos de acero con estrías por dentro; van cinco, entre los de fricción.
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 12, 5, 6 · efectos: 0
- **8 · Asiento del resorte antibrinco** · reutiliza · taller · ARANDELA ANTIBRINCO · 1 pieza · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El aro plano que va en la manzana (12), debajo del resorte antibrinco (9).
  - sirve: Le da un apoyo parejo al resorte para que no marque la manzana.
  - porque: Si no está torcido ni marcado, se vuelve a poner.
  - cuando: Revísalo cada vez que cambies los discos.
  - fallas: desgaste: Se marca si el resorte se mueve.
  - sintomas: Tirones al soltar la palanca.
  - arrastra: — falta
  - conecta: 9, 12 · efectos: 0
- **9 · Resorte antibrinco** · cambia · taller · RESORTE ANTIBRINCO · 1 pieza · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un aro de acero curvo (como un platillo) que va con su asiento (8) en la manzana (12), antes del primer disco.
  - sirve: Hace que el clutch agarre suave, sin tirones ni temblor, cuando sueltas la palanca.
  - porque: Si quedó plano, va nuevo; si estaba al revés, voltéalo. Al sacarlo, fíjate de qué lado mira la curva.
  - cuando: Revísalo cada vez que cambies los discos.
  - fallas: montaje: Al revés no hace su trabajo: la moto sale a tirones.; calor: Se aplana con el calor de patinar.
  - sintomas: La moto sale a brincos aunque sueltes despacio.
  - arrastra: Resorte plano → la moto sale a tirones y los discos de fricción (5) se gastan disparejo.
  - conecta: 8, 5, 12 · efectos: 0
- **10 · Resortes del clutch** · cambia · taller · RESORTE PRESION CLUTCH · 3 piezas · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los tres resortes que van entre la placa de los resortes (13) y la manzana (12); por dentro de cada uno pasa una torre de la placa de presión (4).
  - sirve: (heredado)
  - porque: Si están más cortos que el límite del manual de servicio, van nuevos los tres.
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: Patina con discos buenos.; Palanca muy blanda.
  - arrastra: (heredado)
  - conecta: 4, 13, 14 · efectos: 0
- **11 · Arandela espaciadora** · reutiliza · taller · ARANDELA ESPACIADORA CLUTCH · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela que va en el eje de la caja, entre la campana (2) y la manzana (12) (posición aprox.).
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: desgaste: Se gasta y deja juego.
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 2, 3 · efectos: 0
- **12 · Manzana del clutch** · reutiliza · taller · CORONA INTERNA CLUTCH · 1 pieza · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El cubo con estrías por fuera y por dentro: por fuera engranan los separadores (7) y por dentro el eje de la caja; hacia la placa de presión (4) tiene las rampas del slipper.
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 7, 4, 16, 15 · efectos: 0
- **13 · Placa de los resortes** · reutiliza · taller · PORTA DISCOS CLUTCH · 1 pieza · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La placa de afuera con tres orejas: lleva la balinera (17) en el centro y los tres tornillos (14).
  - sirve: Recibe el empuje del pin adaptador (18) y aleja la placa de presión (4) para soltar los discos.
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 17, 14, 10, 20 · efectos: 0
- **14 · Tornillos de los resortes** · reutiliza · basico · TORNILLO M6X25 · 3 piezas · también en el kit ref. 22 (kit clutch completo, NF070010) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los tres tornillos con brida que sujetan la placa de los resortes (13) y comprimen los resortes (10).
  - sirve: Aprietan la placa de los resortes contra las torres de la placa de presión (4).
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: Tornillo flojo → la placa de los resortes (13) se tuerce.
  - conecta: 13, 10, 4 · efectos: 0
- **15 · Arandela de la tuerca** · reutiliza · taller · ARANDELA · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela que va debajo de la tuerca (16).
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: Tuerca que se afloja.
  - arrastra: (heredado)
  - conecta: 16, 12 · efectos: 0
- **16 · Tuerca de la manzana** · reutiliza · taller · TUERCA · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tuerca con brida que sujeta la manzana (12) en el eje de la caja.
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: (heredado)
  - conecta: 12, 15 · efectos: 0
- **17 · Balinera de la placa de los resortes** · cambia · taller · RODAMIENTO BOLAS 15X32X9 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La balinera de 15 × 32 × 9 mm que va en el centro de la placa de los resortes (13).
  - sirve: Deja que la placa gire con el clutch mientras el pin adaptador (18) la empuja sin girar.
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado); Palanca áspera.
  - arrastra: Balinera trabada → el pin adaptador (18) se gasta en la punta.
  - conecta: 13, 18 · efectos: 0
- **18 · Pin adaptador** · reutiliza · taller · PIN ADAPTADOR CLUTCH · 1 pieza · aprox.: que, sirve, sintomas, fallas, porque, cuando
  - que: El pin corto que va entre el balín (19) y la balinera (17) de la placa de los resortes (13) (posición aprox.).
  - sirve: Pasa el empuje del brazo del clutch a la placa de los resortes.
  - porque: Si la punta no está gastada ni torcida, se vuelve a poner.
  - cuando: Revísalo cada vez que abras el clutch.
  - fallas: desgaste: Se gasta en la punta y el juego libre cambia.
  - sintomas: (heredado)
  - arrastra: — falta
  - conecta: 19, 17, 20 · efectos: 0
- **19 · Balín** · cambia · taller · BALIN 3/16 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Una bola de acero de 3/16 de pulgada entre el pin empujador (20) y el pin adaptador (18).
  - sirve: Deja que los pines se empujen sin rozar de lado: el empuje pasa por un punto.
  - porque: Es barato: si está marcado o se perdió, va nuevo.
  - cuando: Cuídalo cada vez que abras el clutch: se cae fácil.
  - fallas: perdida: Se pierde al desarmar: sin él, el clutch no suelta.
  - sintomas: Palanca áspera o con saltos.
  - arrastra: — falta
  - conecta: 18, 20 · efectos: 0
- **20 · Pin empujador** · reutiliza · taller · PIN EMPUJADOR CLUTCH · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El pin largo que recibe el empuje del brazo del clutch en la tapa y lo pasa al balín (19).
  - sirve: Lleva el movimiento de la palanca hasta los pines de adentro.
  - porque: Si está recto y con la punta sana, se vuelve a poner.
  - cuando: Revísalo cada vez que quites la tapa del clutch.
  - fallas: (heredado)
  - sintomas: (heredado)
  - arrastra: Pin gastado → falta recorrido y el clutch arrastra.
  - conecta: 19, 18 · efectos: 0
- **21 · Arandela de atrás de la campana** · reutiliza · taller · ARANDELA · 1 pieza · aprox.: que, sirve, sintomas, fallas, porque, cuando
  - que: La arandela que va en el eje de la caja, detrás de la campana (2) (posición aprox.).
  - sirve: Hace de tope para que la campana no roce contra la carcasa.
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: desgaste: Se marca o se adelgaza con los años.
  - sintomas: (heredado)
  - arrastra: — falta
  - conecta: 2, 11 · efectos: 0

## Cómo funciona
1. (heredado)
2. 2 · Aprietas la palanca. El cable gira el brazo del clutch en la tapa, los pines empujan la placa de los resortes y la placa de presión se aleja: los discos se separan y el eje de la caja se queda quieto.
3. (heredado)
4. (heredado)
5. 5 · Palanca suelta y aceleras. Los resortes aprietan los discos y las rampas entre la manzana y la placa de presión aprietan más; así bastan resortes blandos y la palanca es suave. El eje gira con la campana.
6. 6 · Reduces de golpe. La rueda empuja al motor y las rampas corren al revés: alejan un poco la placa de presión y los discos patinan. La rueda de atrás brinca mucho menos.

## Si falla
- **Cable sin juego libre**: Pin empujador: El cable queda tenso y los pines siguen empujando la placa de los resortes. → Placa de presión: La placa de presión no aprieta del todo los discos. → Discos de fricción: Los discos patinan en subida y se queman. → Discos separadores: Los separadores se recalientan, se azulan y se tuercen.
- **Aceite equivocado o viejo**: Discos de fricción: Con aceite para carro (con aditivos antifricción) o muy viejo, los discos resbalan y se vitrifican. → Resortes del clutch: El calor de patinar cansa los resortes. → Placa de presión: La placa de presión se azula y aprieta disparejo: patina aunque cambies los discos.

## Cuándo
- Cambiar el aceite del motor (baña el clutch): A los 500-750 km, a los 5.000-6.000 km, a los 11.500-12.000 km y después cada 6.000 km o 6 meses. 10W-30 sintético API SL, JASO MA2: 1,2 L (1,4 L si se desarma el motor). · manual del propietario TVS Apache RTR 160 4V (inglés), cuadro de mantenimiento (p. 84 impresa, 91 del PDF) y lubricantes (p. 88 impresa, 95 del PDF). Seguro
- Revisar el juego libre de la palanca: 8 - 13 mm en la punta de la palanca, con el motor frío; ajústalo con el ajustador del cable en el brazo del clutch y aprieta la contratuerca. · manual del propietario TVS Apache RTR 160 4V (inglés), «Clutch adjustment» (pp. 95-96 impresas, 102-103 del PDF). Seguro
- Revisar los discos del clutch: Revisarlos y cambiarlos si hace falta cada 24.000 km, o antes si patina con el juego libre bien ajustado. · manual del propietario TVS Apache RTR 160 4V (inglés), cuadro de mantenimiento (p. 84 impresa), fila «Clutch plates». Seguro

## Fuentes y certezas
- Seguro: Números, nombres, códigos y cantidades de las 21 piezas y del kit ref. 22: catálogo de partes TVS Apache RTR 160 4V 2026 (Colombia), fig. 8 «Clutch (con slipper clutch)» (p. 11).
- Seguro: Medidas del balín (3/16) y de la balinera (15 × 32 × 9 mm): descripción del catálogo, fig. 8.
- Seguro: Aceite 10W-30 API SL JASO MA2, 1,2 L, intervalos de cambio, discos cada 24.000 km y juego libre de 8 - 13 mm: manual del propietario TVS Apache RTR 160 4V (inglés), pp. 84, 88 y 95-96 impresas.
- Aprox.: Proporciones, vista y orden del dibujo: deducidos del plano del catálogo, en vista caballera con el eje de la caja hacia ti, como los otros clutch.
- Aprox.: Papel de cada placa (placa de presión adentro con las torres y las rampas, placa de los resortes afuera con la balinera), orden de los pines y lugar del retén y de las arandelas: deducidos del plano y de la práctica de taller.
- Aprox.: Torques, largo libre de los resortes y espesor de los discos: no están en el manual del propietario; van como «manual de servicio».

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `owners-manual-apache-rtr160-4v.pdf` (manual de propietario, sin torques de chasis ni motor; 138 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 12 (impresa -, 2 piezas), 39 (impresa -, 2 piezas), 82 (impresa -, 2 piezas), 84 (impresa -, 2 piezas), 89 (impresa -, 2 piezas), 131 (impresa -, 2 piezas)
  claves buscadas: adaptador, apache, arandela, asiento, balinera, balín, campana, clutch, discos, empujador, manzana, placa, resorte, resortes, retén, tornillos, tuerca · para más: `buscar_manual.py tvs-apache160-4v "palabra,otra" --paginas N-M`

## Pendientes de la creadora
- Confirmar con el manual de servicio el papel de cada placa (refs. 4 y 13), el orden de los pines (18, 19 y 20) y el lugar del retén (1) y de las arandelas (11 y 21).
- Torques de los tornillos de los resortes y de la tuerca de la manzana, largo libre de los resortes y espesor mínimo de los discos: manual de servicio.
- En qué puesto van los discos de fricción de los dos tipos (refs. 5 y 6) y de qué lado mira el resorte antibrinco (9): manual de servicio.
- garaje/intervalos/tvs_apache_rtr_160.json no tiene tareas de aceite ni de clutch: las filas de «Cuándo» van sin tarea, con la fuente del manual del propietario.
- La tapa del clutch (fig. 6) con el brazo y la guía del cable, y la versión sin slipper (fig. 7), quedan para otras láminas.
