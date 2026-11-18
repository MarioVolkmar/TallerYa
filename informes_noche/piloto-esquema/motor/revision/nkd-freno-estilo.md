<!-- json e0acdfa9c61b -->
# Revisión rápida · nkd-freno-estilo

Freno delantero · AKT NKD 125 · catálogo akt-nkd125 fig. F5 · página `motor/nkd-freno-estilo.html` · hermana `crypton-freno` (lo heredado sin cambio ya se revisó allá y va resumido)

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 0 avisos.
- Medición: Bloqueantes: ninguno · Medible APRUEBA (faltan las notas a ojo 1-5 y 7: --ojo) · Notas estimadas (criterios medibles): 6: 5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.88

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Sistema De Freno Delantero Cto 125NKD CBS ×1 · 2 Bomba del freno ×1 · 3 Manigueta del freno ×1 · 4 Interruptor del freno ×1 · 5 Manguera del freno ×1 · 6 Pastillas de freno (juego) ×1 · 7 Cáliper (completo) ×1 · 8 Tornillos de unión de la manguera ×2 · 9 Cable del freno combinado (CBS) ×1

## Grupos (nombre (id); tornillería aparte)
- **Bomba y manigueta** [mando]: Bomba del freno (2), Manigueta del freno (3), Interruptor del freno (4)
- **Cable del pedal (CBS)** [cable]: Cable del freno combinado (CBS) (9)
- **Manguera** [manguera]: Manguera del freno (5) · Tornillos de unión (8a, 8b)
- **Cáliper y pastillas** [caliper]: Cáliper (completo) (7), Pastillas de freno (juego) (6a), Pastillas de freno (juego) (6b)

## Desarme
1. Cable del pedal. Afloja la tuerca de ajuste en el pedal y suelta el cable de la palanca de abajo de la bomba (2). Anota por dónde pasa en el chasis. Al armar, déjalo con holgura: la rueda de adelante debe girar libre.
2. Unión en el cáliper. Trapo sobre la pintura y saca el líquido del depósito con una jeringa. Afloja la unión, sácala con sus dos arandelas de cobre (van nuevas) y que no gotee en pastillas ni disco.
3. Cáliper. Saca los dos tornillos que lo sujetan a la barra y sácalo del disco. Si solo cambias pastillas (sin soltar la manguera), no aprietes la manigueta con el cáliper fuera: sacarías el pistón.
4. Pastillas. Saca el pasador y las dos pastillas. Se cambian siempre por pares; limpia el pistón antes de empujarlo para que entren las nuevas.
5. Unión en la bomba. Con el depósito vacío y el trapo puesto, afloja la unión de arriba y saca sus dos arandelas.
6. Manguera. Sácala de sus guías sin doblarla. Si tiene grietas o se infla, va nueva.
7. Interruptor del freno. Desconecta sus cables y sácalo de debajo de la manigueta.
8. Manigueta. Saca el perno del pivote y la manigueta. Al armar: grasa en el pivote y que regrese sola.
9. Bomba. Afloja la abrazadera y saca la bomba. Al armar: depósito nivelado, líquido nuevo, purgar y probar los frenos con la moto quieta antes de rodar.

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **2 · Bomba del freno** · cambia · taller · Bomba Freno Delantero 125NKD CBS · 1 pieza · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: que, sirve, sintomas, fallas, cuando
  - que: El cilindro del freno en el manubrio: un cuerpo de aluminio con su depósito de líquido arriba y un pistón pequeño adentro. Esta trae abajo una palanca para el cable (9) del pedal.
  - sirve: Cuando aprietas la manigueta (3), su pistón empuja el líquido (liquido) por la manguera (5) hasta el cáliper (7).
  - porque: El catálogo la vende entera, sin juego de reparación aparte. Si pierde líquido o la manigueta se va al fondo, va completa y después se purga. Pide la de freno combinado: la normal no trae la palanca del cable.
  - cuando: Mira el nivel del depósito en cada servicio. Revisa sus copas cada 2 años, con el cambio del líquido (aprox.), o antes si hay fuga.
  - fallas: edad: Las copas del pistón se endurecen y dejan pasar líquido: la manigueta se va al fondo.; humedad: El líquido viejo trae agua: oxida el cilindro por dentro y daña las copas.; golpe: En una caída la bomba se raja o se dobla la abrazadera.
  - sintomas: La manigueta se siente esponjosa o llega hasta el puño.; Hay líquido en el manubrio o debajo de la tapa.; El nivel del depósito baja sin que las pastillas estén gastadas.
  - arrastra: Copas gastadas → la manigueta se va al fondo y el cáliper (7) no recibe presión.; Fuga en la tapa → el líquido (liquido) daña la pintura del tanque o el tablero.
  - conecta: 3, 4, 5, 8, 9, liquido · efectos: 0
- **3 · Manigueta del freno** · cambia · facil · Manigueta Freno 125NKD CBS · 1 pieza · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La palanca de aluminio delante del puño derecho. Gira en un perno y su nariz empuja el pistón de la bomba (2).
  - sirve: Multiplica la fuerza de tus dedos y la lleva a la bomba. Al soltarla, un resorte de la bomba la regresa.
  - porque: Una manigueta doblada o rajada no se endereza: puede partirse frenando. Si solo está dura, se limpia y se engrasa el pivote.
  - cuando: Mírala después de cualquier caída y engrasa el pivote cada 2 años, con el cambio del líquido (aprox.), o antes si la sientes dura.
  - fallas: golpe: En las caídas se dobla o se parte la punta.; desgaste: El pivote sin grasa se gasta y la manigueta baila.; humedad: El pivote se oxida y la manigueta se pega.
  - sintomas: Queda dura o no regresa sola.; Tiene juego de lado a lado en el pivote.; Está doblada o le falta la punta después de una caída.
  - arrastra: Manigueta doblada → no llega bien al pistón de la bomba (2) y frenas menos.; Manigueta que no regresa → el freno queda rozando y calienta las pastillas (6).
  - conecta: 2, 4 · efectos: 0
- **4 · Interruptor del freno** · cambia · facil · Switch Freno Del 110S/125R · 1 pieza · aprox.: sintomas, fallas, porque, cuando
  - que: Un pulsador pequeño debajo de la manigueta (3), con sus cables eléctricos.
  - sirve: Prende la luz de freno de atrás cuando aprietas la manigueta.
  - porque: Es una pieza sellada y barata: si falla, se cambia. Antes revisa el fusible, el bombillo y el cableado.
  - cuando: Pruébalo en cada servicio: aprieta la manigueta y mira que prenda la luz de atrás.
  - fallas: humedad: El agua de la lavada le sulfata los contactos.; golpe: Se parte el émbolo o se suelta un cable.
  - sintomas: La luz de freno no prende con la manigueta (con el pedal sí).; La luz de freno se queda prendida.
  - arrastra: Interruptor dañado → no se ve que frenas y te pueden chocar por detrás.
  - conecta: 3, 2 · efectos: 0
- **5 · Manguera del freno** · cambia · taller · Manguera Freno Delantera 125SL/NKD/NKD CBS · 1 pieza · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tubo de caucho reforzado que va de la bomba (2) al cáliper (7). Cada punta lleva un ojo con su tornillo de unión (8).
  - sirve: Lleva la presión del líquido (liquido) hasta el cáliper sin inflarse.
  - porque: El caucho no se repara: si está agrietada o inflada, va nueva, con arandelas nuevas en las dos uniones, y después se purga.
  - cuando: Revísala en cada servicio y cada 2 años, con el cambio del líquido; cámbiala cada 4 años (aprox.: práctica de taller).
  - fallas: edad: El caucho se agrieta y se infla con los años y el sol.; (heredado)
  - sintomas: (heredado); Grietas, humedad o una parte inflada.; Se pellizca o roza al girar el manubrio.
  - arrastra: (heredado)
  - conecta: 2, 7, 8 · efectos: 0
- **6 · Pastillas de freno (juego)** · cambia · taller · Jgo Pastillas Freno Delantero 110S/125 · 1 pieza · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Dos placas de acero con un bloque de material de fricción pegado. Van dentro del cáliper (7), una a cada lado del disco (disco).
  - sirve: (heredado)
  - porque: Se cambia el juego completo, nunca una sola. Antes de meterlas, limpia el pistón y empújalo despacio. Después bombea la manigueta hasta que quede firme antes de rodar: el primer apretón no frena.
  - cuando: Míralas en cada servicio. Cámbialas cuando les quede cerca de 1 mm de material (aprox.: confirma el límite en el manual de servicio AKT).
  - fallas: desgaste: Cada frenada las gasta. En Medellín se gastan más rápido por las lomas y el trancón.; calor: Con calor sostenido se cristalizan: chillan y frenan menos.; (heredado)
  - sintomas: Les queda poco material o la ranura casi no se ve.; (heredado); (heredado); (heredado)
  - arrastra: (heredado); (heredado)
  - conecta: 7, disco · efectos: 0
- **7 · Cáliper (completo)** · repara · taller · Caliper Delantero Completo NKD · 1 pieza · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: sirve, sintomas, fallas, cuando
  - que: La «pinza» del freno: un cuerpo de aluminio con un pistón adentro, su soporte y el purgador. El catálogo lo vende completo.
  - sirve: Convierte la presión del líquido (liquido) en fuerza sobre las pastillas (6), que aprietan el disco (disco).
  - porque: Se limpia, se engrasan los pasadores y se le cambia el líquido. Si el pistón está picado o hay fuga, el catálogo solo trae el cáliper completo.
  - cuando: Límpialo en cada cambio de pastillas y revisa sus sellos cada 2 años, con el cambio del líquido (aprox.).
  - fallas: humedad: El líquido viejo trae agua: oxida el pistón por dentro y se pega.; edad: Los sellos se endurecen con los años y el calor: fugas o pistón que no regresa.; humedad: Si los pasadores se oxidan, el cuerpo deja de deslizarse y trabaja una sola pastilla.
  - sintomas: (heredado); (heredado); (heredado); Manchas de líquido alrededor.
  - arrastra: Pistón pegado → una pastilla roza siempre y el disco (disco) se recalienta.; Fuga en el cáliper → líquido en las pastillas (6): toca cambiarlas.
  - conecta: 6, 5, 8, disco, barra · efectos: 0
- **8 · Tornillos de unión de la manguera** · reutiliza · taller · Tornillo Conexion Manguera Freno · 2 piezas · también en el kit ref. 1 (Sistema De Freno Delantero Cto 125NKD CBS, 291410316-0001) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Dos tornillos huecos, uno en cada punta de la manguera (5). El líquido pasa por un agujero en su centro.
  - sirve: Sujetan el ojo de la manguera a la bomba (2) y al cáliper (7), con una arandela de cobre a cada lado que sella.
  - porque: El tornillo sano se reutiliza; las arandelas de cobre van siempre nuevas. Apriétalos con torquímetro al apriete del manual de servicio AKT (aquí no hay dato).
  - cuando: Revísalos cada 2 años, con el cambio del líquido (aprox.), o cuando cambies la manguera.
  - fallas: maluso: Reutilizar las arandelas de cobre o apretar de menos deja una fuga.; maluso: Apretar de más daña la rosca de la bomba o del cáliper.
  - sintomas: Humedad o costra de líquido alrededor de la unión.; La manigueta pierde firmeza poco a poco.
  - arrastra: Unión floja → entra aire y la bomba (2) no logra presión.
  - conecta: 5, 2, 7 · efectos: 0
- **9 · Cable del freno combinado (CBS)** · cambia · taller · Cable Freno 125NKD CBS · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un cable de acero con funda, de 127 cm, que va del pedal del freno trasero a la palanca de abajo de la bomba (2).
  - sirve: Cuando pisas el pedal, jala la palanca de abajo de la bomba y frena también un poco adelante: así la moto frena con las dos ruedas.
  - porque: Un cable deshilachado u oxidado no se arregla: va nuevo. Si solo está flojo, se ajusta como dice el manual de servicio.
  - cuando: Revisa su ajuste cada vez que ajustes el freno de atrás (aprox.).
  - fallas: humedad: Entra agua en la funda, el cable se oxida y se pone duro.; desgaste: Se estira y pierde el ajuste.; maluso: Ajustarlo muy tenso deja el freno de adelante rozando.
  - sintomas: Al pisar el pedal, la rueda de adelante no frena nada.; La rueda de adelante queda rozando después de ajustar el freno de atrás.; El pedal se siente duro o no regresa.
  - arrastra: Cable muy tenso → las pastillas (6) rozan el disco (disco) sin que frenes.; Cable roto → el pedal frena solo atrás y la moto tarda más en parar.
  - conecta: 2 · efectos: 0
- **barra · Barra derecha de la suspensión** · repara · taller · Otra lámina (suspensión delantera) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La barra donde va atornillado el cáliper (7).
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: (heredado)
  - fallas: (heredado)
  - sintomas: (heredado); (heredado)
  - arrastra: (heredado)
  - conecta: 7 · efectos: 0
- **disco · Disco de freno** · cambia · taller · Fig. F-6 (rueda delantera) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El plato de acero atornillado a la rueda delantera. Las pastillas (6) lo aprietan por los dos lados.
  - sirve: Gira con la rueda; al apretarlo, el movimiento se vuelve calor y la moto frena.
  - porque: Si está por debajo del grosor mínimo marcado en el disco o torcido, va nuevo, con pastillas nuevas.
  - cuando: Mídelo en cada cambio de pastillas.
  - fallas: desgaste: Se adelgaza con los años de frenadas.; calor: Se tuerce si se recalienta con una pastilla pegada.
  - sintomas: Rayas profundas en la cara.; La manigueta vibra al frenar (disco torcido).
  - arrastra: Disco torcido → la manigueta vibra y las pastillas (6) se gastan disparejas.
  - conecta: 6, 7 · efectos: 0
- **liquido · Líquido de frenos DOT 3 o DOT 4** · cambia · taller · Otra lámina · líquido del sistema · aprox.: sirve, sintomas, porque, cuando
  - que: (heredado)
  - sirve: (heredado)
  - porque: (heredado)
  - cuando: Cámbialo cada 2 años (aprox.: práctica de taller; confírmalo en el manual del propietario). No mezcles tipos: rellena con el que dice la tapa.
  - fallas: (heredado); (heredado)
  - sintomas: (heredado); (heredado)
  - arrastra: Líquido con agua → hierve antes y el pistón del cáliper (7) se oxida por dentro.
  - conecta: 2, 5, 7 · efectos: 0

## Cómo funciona
1. (heredado)
2. 2 · Aprietas la manigueta derecha. Es una palanca: con poco esfuerzo empuja un pistón pequeño dentro de la bomba. Si pisas el pedal, el cable del freno combinado jala la misma bomba.
3. (heredado)
4. (heredado)
5. (heredado)
6. (heredado)
7. (heredado)

## Si falla
- **Pastillas que llegan al metal**: Pastillas de freno (juego): Se gastan y nadie mira cuánto material les queda. → Disco de freno: La placa de acero raya el disco: toca cambiar disco y pastillas. → Cáliper (completo): El pistón sale de más, se ensucia y se puede pegar.
- **Líquido de más de 2 años**: Líquido de frenos DOT 3 o DOT 4: Absorbió agua y hierve antes. → Cáliper (completo): El agua oxida el pistón y los sellos se endurecen: el freno queda pegado. → Pastillas de freno (juego): Una pastilla queda rozando y se gasta sola. → Disco de freno: El disco se recalienta y se puede torcer.
- **Cable del CBS muy tenso**: Cable del freno combinado (CBS): Queda tenso después de ajustar el freno de atrás. → Bomba del freno: Jala un poco la bomba todo el tiempo. → Pastillas de freno (juego): Las pastillas de adelante rozan sin que frenes. → Disco de freno: El disco se calienta y la moto se siente pesada.
- **Arandelas de cobre reutilizadas**: Tornillos de unión de la manguera: La unión queda sin sellar. → Manguera del freno: Sale líquido por la punta de la manguera y entra aire. → Bomba del freno: Con aire en el sistema, la bomba empuja burbujas: la manigueta se va al fondo y casi no frena.

## Cuándo
- Pastillas: revisar el desgaste: En cada servicio; cámbialas con cerca de 1 mm de material. · Práctica de taller; confirmar en el manual del propietario NKD. Práctica de taller
- Líquido de frenos: cambiar: Cada 2 años, ruede lo que ruede. · Práctica de taller (plazo usual de las marcas); confirmar en el manual del propietario NKD. Práctica de taller
- Manguera del freno: revisar y cambiar: Revísala en cada servicio; cámbiala cada 4 años. · Práctica de taller. Práctica de taller
- Cable del freno combinado: revisar el ajuste: Cada vez que ajustes el freno de atrás. · Práctica de taller; ajuste exacto en el manual de servicio AKT. Práctica de taller

## Fuentes y certezas
- Seguro: Números, nombres, códigos y cantidades: catálogo de partes AKT NKD 125 2025, fig. F-5 «Sistema freno delantero» (p. 18).
- Seguro: Cable del CBS de 127 cm: nota del mismo catálogo.
- Aprox.: Vista desde el lado derecho: bomba arriba en el manubrio y cáliper abajo en la barra; proporciones a ojo.
- Aprox.: Cáliper, pastillas y disco adaptados de otras láminas de freno de TallerYa (cáliper flotante y bomba de manubrio).
- Aprox.: Contenido del kit ref. 1: por el plano (la llave abarca bomba, manguera y cáliper).
- Aprox.: Orden del desarme, fallas, síntomas y plazos: práctica de taller.

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-usuario-nkd125.pdf`: sin texto con esas piezas (¿escaneado?)
  claves buscadas: barra, bomba, cable, cáliper, disco, freno, interruptor, líquido, manguera, manigueta, pastillas, tornillos · para más: `buscar_manual.py akt-nkd125 "palabra,otra" --paginas N-M`

## Pendientes de la creadora
- Torques de los tornillos de unión y del cáliper: sin dato; confirmar con el manual de servicio AKT.
- Tipo de líquido (DOT 3 o DOT 4) y plazos de cambio: el manual del propietario está escaneado; no hay tareas de freno en garaje/intervalos/akt_nkd_125.json.
- Contenido exacto del kit ref. 1 y si trae el interruptor: confirmar con AKT.
- Ajuste del cable del CBS: confirmar en el manual de servicio.
- Sin 3D propio para bomba y cáliper (solo el tornillo de unión, de la biblioteca).
