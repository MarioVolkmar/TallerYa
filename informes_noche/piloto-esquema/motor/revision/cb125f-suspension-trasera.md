<!-- json 1991d59e46e2 -->
# Revisión rápida · cb125f-suspension-trasera

Suspensión trasera: tijera y cadena · catálogo honda-cb125f fig. F22-1 · página `motor/cb125f-suspension-trasera.html`

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 1 avisos.
  - aviso: armado transparente: 11·11 y 12·12 muy juntos (0.0 px de radio); solo se ven al tocar la pieza
- Medición: Bloqueantes: ninguno · Medible APRUEBA · Notas estimadas (criterios medibles): 6: 5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.88

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Guardacadena ×1 · 2 Cadena ×1 · 3 Eslabón de unión ×1 · 4 Brazo del freno ×1 · 5 Eje de la tijera ×1 · 6 Deslizador de la cadena ×1 · 7 Tijera ×1 · 8 Tornillos del guardacadena ×2 · 9 Tuerca del eje de la tijera ×1 · 10 Tornillo del brazo del freno ×1 · 11 Tuerca del brazo del freno ×1 · 12 Arandela del brazo del freno ×1 · 13 Arandela de presión del brazo ×1 · 14 Pasador del brazo del freno ×1

## Grupos (nombre (id); tornillería aparte)
- **Guardacadena** [guardacadena]: Guardacadena (1) · Tornillos del guardacadena (8)
- **Cadena y eslabón de unión** [cadena]: Cadena (2), Eslabón de unión (3)
- **Brazo del freno** [freno]: Brazo del freno (4) · Tornillo y tuerca del brazo (10, 11) · Arandelas y pasador del brazo (12, 13, 14)
- **Tijera y su eje** [tijera]: Tijera (7), Deslizador de la cadena (6) · Eje y tuerca de la tijera (5, 9)

## Desarme
1. Guardacadena. Con la moto firme en el gato central, quita los dos tornillos (8) y saca el guardacadena (1) hacia arriba. Al armar: que no roce la cadena (2) en ningún punto.
2. Cadena. Saca antes la rueda (fig. F-13-1). Abre el eslabón de unión (3) con pinza y saca la cadena (2). Al armar: grapa con la punta cerrada hacia donde gira la cadena y holgura de 25-35 mm.
3. Brazo del freno. En la tijera, quita el pasador (14), la tuerca (11) y las arandelas, y saca el tornillo (10) y el brazo (4). Al armar: pasador nuevo, con las puntas dobladas. Sin él, el brazo se suelta y el freno se traba.
4. Tijera. Soporta la tijera y quita los pernos de abajo de los amortiguadores (fig. F-23). Quita la tuerca (9), saca el eje de la tijera (5) y baja la tijera (7). Al armar: eje con grasa y torque del manual de servicio.
5. Deslizador. Suelta el deslizador (6) de la tijera. Cámbialo si la cadena ya le hizo canal; si llega al metal, la cadena se come la tijera.

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **1 · Guardacadena** · cambia · facil · CASE, DRIVE CHAIN · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tapa de plástico que cubre el tramo de arriba de la cadena (2), atornillada a la tijera (7).
  - sirve: Evita que la cadena te agarre la ropa o el pie y que tire grasa a la moto.
  - porque: Rajado no se pega bien: vibra y se vuelve a partir. Los tornillos sí se reutilizan.
  - cuando: Míralo cada vez que lubriques la cadena.
  - fallas: golpe: La cadena floja da latigazos y lo raja por dentro.; maluso: Tornillos flojos: vibra y se parte en la base.
  - sintomas: Ruido de plástico que vibra o golpea al acelerar.; Rajado o con la marca de la cadena por dentro.
  - arrastra: Cadena floja → latigazos que lo rajan; ajusta la cadena (2).
  - conecta: 8, 2, 7 · efectos: 0
- **2 · Cadena** · cambia · facil · CHAIN, DRIVE(428H-120L) · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: La cadena 428H de 120 eslabones que lleva la fuerza del piñón del motor a la corona de la rueda.
  - sirve: Mueve la rueda trasera. Corre por encima del deslizador (6) de la tijera.
  - porque: Estirada no se recupera: se cambia junto con el piñón y la corona, porque una cadena nueva en dientes gastados se estira rápido.
  - cuando: Lubrícala cada 600 km y mide la holgura: 25-35 mm en el tramo de abajo, entre piñón y corona. No ruedes si pasa de 50 mm.
  - fallas: desgaste: Sin grasa se estira y se gasta con la corona y el piñón.; humedad: El agua y el barro la oxidan y le traban eslabones.
  - sintomas: Tirones o golpes al acelerar y soltar.; Ruido metálico, peor si está seca.; Los tensores llegan al tope y la holgura sigue pasando de 35 mm.
  - arrastra: Cadena floja → canal en el deslizador (6) y latigazos al guardacadena (1).
  - conecta: 3, 6, 1 · efectos: 0
- **3 · Eslabón de unión** · cambia · facil · JOINT, DRIVE CHAIN · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El eslabón que cierra la cadena (2): dos pasadores, una placa y una grapa.
  - sirve: Te deja abrir la cadena para sacarla sin cortar ningún eslabón.
  - porque: La grapa se deforma al quitarla; si cambias la cadena, el eslabón nuevo viene con ella.
  - cuando: Revisa la grapa cada vez que lubriques la cadena.
  - fallas: maluso: Grapa puesta al revés: se engancha y se cae.; desgaste: Se gasta igual que el resto de la cadena.
  - sintomas: Grapa torcida, suelta o que falta.; Un eslabón que se traba justo en la unión.
  - arrastra: Grapa suelta → la cadena (2) se abre andando y se enreda en la rueda.
  - conecta: 2 · efectos: 0
- **4 · Brazo del freno** · reutiliza · facil · ARM, RR. BRAKE STOPPER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La barra de acero que une el plato del freno trasero con la tijera (7).
  - sirve: Sujeta el plato del freno para que no gire con la rueda cuando frenas.
  - porque: Si está derecho y los huecos no están ovalados, sirve; doblado o con huecos gastados va nuevo.
  - cuando: Mira el pasador y la tuerca cada vez que saques la rueda trasera.
  - fallas: maluso: Sin el pasador (14) la tuerca se afloja y el brazo se suelta.; golpe: Se dobla si la rueda se arma mal.
  - sintomas: Golpe atrás al frenar o al soltar el freno.; Freno que se traba de golpe.
  - arrastra: Brazo suelto → el plato gira con la rueda y el freno se traba.
  - conecta: 10, 11, 14, 7 · efectos: 0
- **5 · Eje de la tijera** · reutiliza · taller · BOLT, SWINGARM PIVOT · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El perno largo que atraviesa la tijera y el chasis: la tijera gira sobre él, en unos bujes (casquillos) metidos en ella.
  - sirve: Une la tijera (7) al chasis y es el centro donde gira cuando la rueda sube y baja.
  - porque: Derecho y sin óxido se limpia, se engrasa y vuelve. Doblado o pegado va nuevo, con los bujes.
  - cuando: Engrásalo cada vez que bajes la tijera; revisa el juego en cada servicio.
  - fallas: humedad: Sin grasa se oxida dentro de los bujes y se pega.; desgaste: Gasta los bujes y la tijera toma juego.
  - sintomas: La rueda se mueve de lado a lado con la moto en el gato.; Crujido atrás en los baches.
  - arrastra: Eje seco → bujes gastados y tijera (7) con juego.
  - conecta: 9, 7 · efectos: 0
- **6 · Deslizador de la cadena** · cambia · taller · SLIDER, CHAIN · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La pieza de plástico duro sobre la parte de adelante de la tijera (7), donde roza la cadena (2).
  - sirve: Protege la tijera del roce de la cadena y la guía cuando la tijera sube.
  - porque: No se repara: es barato y protege una tijera que sí es cara.
  - cuando: Míralo cuando ajustes la cadena; cámbialo si el canal ya le pasó la mitad.
  - fallas: desgaste: La cadena floja lo gasta hasta romperlo.; edad: El plástico se reseca y se parte.
  - sintomas: Canal profundo o roto donde pasa la cadena.; Ruido de roce de la cadena con metal.
  - arrastra: Deslizador roto → la cadena (2) se come el metal de la tijera (7).
  - conecta: 2, 7 · efectos: 0
- **7 · Tijera** · repara · taller · SWINGARM SUB ASSY., RR. · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El brazo de acero que va del chasis a la rueda trasera; en la punta lleva la ranura del eje y la oreja del amortiguador.
  - sirve: Sostiene la rueda trasera y la deja subir y bajar. Los amortiguadores (fig. F-23) frenan ese movimiento.
  - porque: Se cambian los bujes y se engrasa el eje. Torcida o rajada va nueva: no se endereza.
  - cuando: Revisa el juego en cada servicio y siempre después de una caída.
  - fallas: desgaste: Los bujes gastados le dan juego lateral.; golpe: Un golpe la tuerce y la rueda queda desalineada.
  - sintomas: La moto se va de lado en las curvas.; La rueda se mueve de lado con la moto en el gato.; Desgaste disparejo de la llanta trasera.
  - arrastra: Tijera con juego → la cadena (2) se gasta de un lado.
  - conecta: 5, 6, 4, 2 · efectos: 0
- **8 · Tornillos del guardacadena** · reutiliza · facil · BOLT, FLANGE, 6MM · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los dos tornillos de 6 mm con arandela pegada que sujetan el guardacadena (1) a la tijera (7).
  - sirve: Mantienen el guardacadena firme para que no vibre ni toque la cadena (2).
  - porque: Con la rosca sana vuelven; aprieta suave a mano porque son de 6 mm.
  - cuando: Revísalos cuando lubriques la cadena.
  - fallas: maluso: Apretados de más, se barre la rosca de la tijera.
  - sintomas: Guardacadena que suena o se mueve.
  - arrastra: — falta
  - conecta: 1 · efectos: 0
- **9 · Tuerca del eje de la tijera** · reutiliza · taller · NUT, FLANGE, 12MM(PT) · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tuerca de 12 mm con brida que cierra el eje de la tijera (5).
  - sirve: Aprieta el eje para que la tijera quede firme al chasis.
  - porque: Con la rosca sana vuelve; si está barrida o con las esquinas redondeadas, va nueva.
  - cuando: Cada vez que saques el eje de la tijera.
  - fallas: maluso: Apretada con la llave equivocada, se le redondean las esquinas.
  - sintomas: Tuerca floja o con la rosca barrida.
  - arrastra: — falta
  - conecta: 5 · efectos: 0
- **10 · Tornillo del brazo del freno** · reutiliza · facil · BOLT A, BRAKE STOPPER ARM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tornillo especial que une el brazo del freno (4) a la tijera (7).
  - sirve: Es el punto de giro del brazo; tiene un hueco para el pasador (14).
  - porque: Si no está gastado ni doblado, sirve; la tuerca y el pasador sí van nuevos si se dañaron.
  - cuando: Cada vez que sueltes el brazo del freno.
  - fallas: desgaste: Se gasta el cuerpo y el brazo baila.
  - sintomas: Brazo con juego en su unión.
  - arrastra: — falta
  - conecta: 4, 11, 14 · efectos: 0
- **11 · Tuerca del brazo del freno** · reutiliza · facil · NUT, HEX., 8MM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tuerca de 8 mm que cierra el tornillo (10) del brazo, trabada con el pasador (14).
  - sirve: Aprieta la unión del brazo del freno (4).
  - porque: Con la rosca sana vuelve; alinea su ranura con el hueco del pasador.
  - cuando: Cada vez que sueltes el brazo del freno.
  - fallas: maluso: Sin pasador se afloja con la vibración.
  - sintomas: Tuerca floja o sin pasador.
  - arrastra: — falta
  - conecta: 10, 14 · efectos: 0
- **12 · Arandela del brazo del freno** · reutiliza · facil · WASHER, PLAIN, 8MM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela plana de 8 mm bajo la tuerca (11) del brazo.
  - sirve: Reparte el apriete para que la tuerca no marque el brazo.
  - porque: Plana y sin óxido vuelve.
  - cuando: Cada vez que sueltes el brazo del freno.
  - fallas: maluso: Se pierde al desarmar.
  - sintomas: Arandela doblada o que falta.
  - arrastra: — falta
  - conecta: 11 · efectos: 0
- **13 · Arandela de presión del brazo** · cambia · facil · WASHER, SPRING, 10MM · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La arandela partida de presión de 10 mm del tornillo (10) del brazo del freno.
  - sirve: Hace de resorte para que la tuerca no se afloje.
  - porque: Si quedó plana ya no frena la tuerca: es barata, ponla nueva.
  - cuando: Cada vez que sueltes el brazo del freno.
  - fallas: edad: Pierde la presión después de varias puestas.
  - sintomas: Arandela aplastada, sin la abertura en espiral.
  - arrastra: — falta
  - conecta: 11 · efectos: 0
- **14 · Pasador del brazo del freno** · cambia · facil · PIN, SPLIT, 2.0X15 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El pasador partido de 2 × 15 mm que atraviesa el tornillo (10) y traba la tuerca (11).
  - sirve: Es el seguro final: aunque la tuerca se afloje, no se sale.
  - porque: Va nuevo siempre: al doblarlo de nuevo se parte. Sin él, el freno se puede trabar.
  - cuando: Cada vez que sueltes el brazo del freno.
  - fallas: maluso: Reutilizado, se parte al doblarlo otra vez.
  - sintomas: Falta, o tiene las puntas sin doblar.
  - arrastra: Sin pasador → la tuerca (11) se cae y el brazo (4) se suelta.
  - conecta: 11, 10, 4 · efectos: 0

## Cómo funciona
1. 1 · Reposo. El resorte de cada amortiguador sostiene el peso de la moto y del piloto. La precarga (cuánto viene apretado el resorte) viene en la posición 2 de 5; súbela si llevas parrillero o carga, igual en los dos y sin saltar de 1 a 5.
2. 2 · Bache. La rueda sube y la tijera gira en su eje, el perno que la une al chasis. El amortiguador se acorta y su resorte se comprime.
3. 3 · Amortigua. Dentro del amortiguador el pistón empuja el aceite por sus orificios: eso frena el golpe para que la rueda no rebote.
4. 4 · Rebote. El resorte vuelve a estirar el amortiguador y baja la tijera; el aceite frena el regreso para que la moto no salte.
5. 5 · La cadena cambia con la tijera. Al subir la tijera, la cadena se tensa. Por eso se le deja holgura: 25-35 mm, medida en el gato central. Si pasa de 50 mm, no ruedes.
6. 6 · Bujes gastados o amortiguador vencido. La tijera baila en su eje: la rueda se tuerce en las curvas. Si el amortiguador bota aceite, la moto rebota en cada bache.

## Si falla
- **Cadena sin lubricar ni ajustar**: Cadena: Seca y floja, la cadena da latigazos al acelerar y soltar. → Deslizador de la cadena: Golpea el deslizador y le hace canal. → Tijera: Sin deslizador, roza la tijera y le come el metal. → Guardacadena: Los latigazos rajan el guardacadena y sueltan sus tornillos.
- **Eje de la tijera sin grasa**: Eje de la tijera: Sin grasa, el eje se oxida y gasta los bujes de la tijera. → Tijera: La tijera toma juego lateral y la rueda se tuerce. → Cadena: La cadena entra torcida a la corona y se gasta de un lado.
- **Brazo del freno sin pasador**: Pasador del brazo del freno: Falta el pasador o no se dobló. → Tuerca del brazo del freno: La tuerca se afloja con la vibración. → Brazo del freno: El brazo se suelta y el plato del freno gira con la rueda. → Tijera: El freno se traba de golpe y el brazo golpea la tijera.

## Cuándo
- Lubricar la cadena: Cada 600 km. · Manual del propietario Honda CB125F Twister (español), copia entregada por el usuario, cuadro de mantenimiento (pág. 35-36 del manual; columnas 1.000 / 4.000 … 24.000 km, anual y sustitución normal; círculo gris = revisar, figura oscura = cambiar), fila 'Cadena de transmisión: cada 500 km'; consultado el 14-nov-2026; TallerYa unifica la lubricación de la cadena a 600 km para todas las líneas (decisión del 15-nov-2026) Seguro
- Holgura de la cadena: En cada lubricación: 25-35 mm a mitad de camino; no ruedes si pasa de 50 mm. · Manual del propietario CB 125F (español), p. 72 (inspección de la cadena) Seguro
- Tijera, bujes y amortiguadores: En cada servicio: mueve la rueda de lado a lado y busca juego o fugas. · Manual del propietario CB 125F (español), cuadro de mantenimiento (fila «Suspensión», p. 81); el intervalo exacto no se leyó Aprox.

## Fuentes y certezas
- Seguro: Números, nombres, códigos y cantidades: catálogo de partes Honda CB 125F GLH125SH, fig. F-22-1 «Swingarm/Chain case» (p. 161), columna SH.
- Seguro: Cadena 428H × 120 eslabones; tornillos de 6 mm, tuercas de 8 y 12 mm, arandelas de 8 y 10 mm y pasador de 2 × 15 mm: mismo catálogo.
- Seguro: Holgura de la cadena 25-35 mm (no rodar sobre 50 mm), tuerca del eje trasero 88 N·m y precarga de 5 posiciones (estándar 2, sin saltar de 1 a 5): Manual del propietario CB 125F (español), pp. 72-74 y 81.
- Aprox.: Vista desde el lado izquierdo, en caballera; proporciones a ojo. El brazo del freno va del lado del freno y aquí se dibuja bajo la tijera para que se vea.
- Aprox.: Orden del desarme, fallas, síntomas y «Cómo funciona»: práctica de taller.
- Aprox.: Torque del eje de la tijera y del brazo del freno: no están en el manual del propietario (manual de servicio).

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-cb125f.pdf` (manual de propietario, sin torques de chasis ni motor; 122 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 82 (impresa -, 3 piezas), 89 (impresa -, 3 piezas), 95 (impresa -, 6 piezas), 96 (impresa -, 4 piezas), 97 (impresa -, 3 piezas), 117 (impresa -, 3 piezas)
- `manual-usuario-cb125f.pdf` (manual de propietario, sin torques de chasis ni motor; 123 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 81 (impresa -, 3 piezas), 94 (impresa -, 6 piezas), 95 (impresa -, 4 piezas), 96 (impresa -, 4 piezas), 99 (impresa -, 3 piezas), 116 (impresa -, 3 piezas)
  claves buscadas: arandela, brazo, cadena, deslizador, eslabón, guardacadena, pasador, suspensión, tijera, tornillo, tornillos, trasera, tuerca · para más: `buscar_manual.py honda-cb125f "palabra,otra" --paginas N-M`

## Pendientes de la creadora
- Torques del eje de la tijera y del tornillo del brazo del freno: falta el manual de servicio.
- Intervalo exacto de revisión de la suspensión en el cuadro de mantenimiento (la tabla no se lee como texto).
