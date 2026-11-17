# Revisión rápida · cb125f-freno

Freno delantero · Honda CB 125F · catálogo honda-cb125f fig. F10 · página `motor/cb125f-freno.html` · hermana `nmax-fig22` (lo heredado sin cambio ya se revisó allá y va resumido)

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 8 avisos.
  - aviso: armado transparente: 6·6 y 9·9 muy juntos (3.9 px de radio); solo se ven al tocar la pieza
  - aviso: funciona[1]: «un pistón», pero el catálogo trae 2 o más (¿«uno de los…» o plural?)
  - aviso: ficha 12.fallas: «los guardapolvos», pero el catálogo trae 1
  - aviso: pasos[4]: «(manual)» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes
  - aviso: ficha 1.cuando: «(manual)» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes
  - aviso: ficha 2.cuando: «(manual)» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes
  - aviso: ficha 11.cuando: «(manual)» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes
  - aviso: fuentes.seguro[1]: «(catálogo)» suena a nota interna: di cuál («manual del propietario, pág. N») o déjalo en Fuentes
- Medición: Bloqueantes: ninguno · Medible APRUEBA · Notas estimadas (criterios medibles): 6: 5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.88

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Sellos del pistón (juego) ×2 · 2 Pastillas de freno (juego) ×1 · 3 Purgador ×1 · 4 Tapa del purgador ×1 · 5 Pistón del cáliper ×2 · 6 Resorte de las pastillas ×1 · 7 Buje del pasador ×1 · 8 Guardapolvo del pasador ×1 · 9 Tapón del pasador ×2 · 10 Pasador de las pastillas ×2 · 11 Cáliper (cuerpo) ×1 · 12 Soporte del cáliper ×1 · 13 Tornillos del soporte ×2

## Grupos
- **Cáliper**: Cáliper (cuerpo), Soporte del cáliper, Guardapolvo del pasador, Buje del pasador, Purgador, Tapa del purgador, Pistón del cáliper, Pistón del cáliper, Sellos del pistón (juego), Sellos del pistón (juego)
- **Pastillas**: Pastillas de freno (juego), Pastillas de freno (juego), Resorte de las pastillas, Pasador de las pastillas, Tapón del pasador

## Desarme
1. Tornillos del soporte. Moto en el gato central, rueda delantera al aire y freno frío. Cubre pintura y plásticos: el líquido de frenos los daña. Afloja los dos tornillos que sujetan el soporte a la barra.
2. Sacar el cáliper. Sale con su soporte, deslizándolo fuera del disco. Para cambiar pastillas no sueltes la manguera: déjala colgando sin estirarla. No aprietes la manigueta con el cáliper afuera: los pistones se salen.
3. Tapón del pasador. Desenróscalo con la herramienta que calce en su cabeza. Guárdalo donde no se pierda.
4. Pasador de las pastillas. Sácalo. Es lo que sostiene las pastillas: al salir, caen. Si está oxidado o doblado, va uno nuevo.
5. Pastillas. Salen las dos. Mira el indicador de desgaste: si una llegó a él, cambia las dos (manual). Al armar: limpia los pistones antes de empujarlos, despacio y vigilando el depósito: el líquido daña la pintura.
6. Resorte de las pastillas. Las mantiene firmes para que no traqueteen. Al armar, va en la misma posición.
7. Separar el cuerpo del soporte. El cuerpo del cáliper se desliza fuera de los pasadores del soporte. Para desarmar los pistones, antes drena el líquido en un recipiente (no se reutiliza) y suelta el racor.
8. Guardapolvo y buje. Protegen el pasador del soporte para que el cáliper flote. Si el caucho está roto o duro, va nuevo. Al armar: grasa de silicona en el pasador.
9. Purgador. Quita la tapa y desenróscalo con cuidado: es de acero y el cáliper de aluminio. Si está pegado, no lo fuerces.
10. Pistones. Sácalos con aire comprimido a poca presión por la entrada del líquido, cáliper sujeto, trapo grueso delante y gafas. Nunca los dedos: salen con fuerza. Si están picados o rayados, van nuevos.
11. Sellos. Sácalos con un palillo de plástico, sin rayar la ranura. Van siempre nuevos. Al armar: líquido DOT3 o DOT4 de envase sellado, purgar y probar la manigueta antes de rodar.

## Fichas (solo lo propio; aprox. = sin fuente)
- **1 · Sellos del pistón (juego)** · cambia · SEAL SET, PISTON · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Dos juegos de cauchos, uno por pistón (5): el sello va en la ranura del cáliper y el guardapolvo afuera.
  - cuando: Van nuevos cada vez que abras el cáliper. Revísalos al cambiar el líquido, cada 2 años (manual), o antes si hay fuga o el freno no suelta.
- **2 · Pastillas de freno (juego)** · cambia · PAD SET, FR. · 1 pieza · aprox.: sirve, fallas, porque
  - cuando: Revísalas antes de rodar y en cada servicio (manual). Cámbialas cuando una llegue al indicador de desgaste, siempre el juego completo.
- **3 · Purgador** · cambia · SCREW, BLEEDER · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - cuando: Se usa en cada cambio de líquido: cada 2 años, con DOT3 o DOT4 (manual del propietario Honda).
- **4 · Tapa del purgador** · cambia · CAP, BLEEDER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El capuchón de caucho que tapa la punta del purgador (3).
  - sirve: Evita que entren agua y mugre por el agujero del purgador; si se tapa, no podrás purgar.
  - porque: Cuesta poco: si está partido o falta, va uno nuevo.
  - cuando: Míralo cada vez que purgues el freno.
  - fallas: sol: El sol y el calor lo resecan y se parte.; perdida: Se pierde al purgar y nadie lo vuelve a poner.
  - sintomas: Purgador oxidado o tapado.; Cuesta purgar el freno.
  - arrastra: Sin tapa → el purgador (3) se oxida y se pega.
- **5 · Pistón del cáliper** · cambia · PISTON · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un cilindro metálico, hueco por delante, que vive dentro del cáliper (11). Este cáliper lleva dos, uno al lado del otro.
  - sirve: El líquido los empuja por detrás y ellos empujan la pastilla (2). Juntos tienen mucha más área que el pistón de la bomba: así multiplican la fuerza de tu mano.
  - cuando: Revísalos cada vez que abras el cáliper o cambies el líquido (cada 2 años, manual). Antes de meterlos para poner pastillas nuevas, límpiales la parte que queda afuera.
- **6 · Resorte de las pastillas** · cambia · SPRING, PAD · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - fallas: edad: Pierde tensión.; humedad: Se oxida.; maluso: Se monta al revés al cambiar pastillas.
  - sintomas: Traqueteo en los huecos o en el empedrado.; Chillido.; Pastillas gastadas en cuña.
- **7 · Buje del pasador** · reutiliza · BUSH B · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un buje que va dentro del guardapolvo (8), sobre el pasador del soporte (12).
  - sirve: Deja que el cáliper (11) se deslice suave y sin juego sobre el pasador.
  - porque: Si está liso y sin juego se reutiliza con grasa de silicona; si está gastado o trabado, va nuevo.
  - cuando: Revísalo cada vez que separes el cáliper del soporte.
  - fallas: oxido: Sin grasa y con agua, se oxida y se traba.
  - sintomas: El cáliper traquetea.; Una pastilla se gasta más que la otra.
  - arrastra: Buje trabado → el cáliper no flota y frena una sola pastilla (2).
- **8 · Guardapolvo del pasador** · cambia · BOOT B, BUSH · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - sintomas: El caucho está rajado o fuera de su sitio.; Con el cáliper desmontado, el pasador del soporte no se mueve con la mano.; Las pastillas se gastan disparejo.
- **9 · Tapón del pasador** · reutiliza · PLUG, PIN · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un tapón roscado que cierra la punta del pasador (10) de las pastillas.
  - sirve: Evita que el pasador se salga y le entre mugre.
  - porque: Se reutiliza si la ranura está sana; si falta o está barrido, va uno nuevo.
  - cuando: Cada vez que cambies pastillas.
  - fallas: perdida: Se pierde al cambiar pastillas.; rosca: Se barre la ranura si se usa el destornillador equivocado.
  - sintomas: Falta el tapón.; El pasador está sucio u oxidado.
  - arrastra: Sin tapón → el pasador (10) se oxida y las pastillas (2) no se deslizan.
- **10 · Pasador de las pastillas** · cambia · PIN, HANGER · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - sintomas: Una pastilla no se despega del disco.; Ruido metálico.; Se le ven surcos.
- **11 · Cáliper (cuerpo)** · repara · CALIPER SUB ASSY., R. FR. · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: La «pinza» del freno: un cuerpo de aluminio con dos cilindros adentro. En la CB 125F es flotante y de dos pistones, uno al lado del otro.
  - sirve: Convierte la presión del líquido en fuerza sobre las pastillas (2). Los pistones (5) empujan una pastilla y el cuerpo se corre en sus pasadores para jalar la otra.
  - porque: El cuerpo se limpia y se le cambian los sellos (1) y el líquido. Solo se cambia entero si el cilindro está picado.
  - cuando: Límpialo y revísalo en cada cambio de pastillas. Los sellos de adentro se renuevan cada 2 años con el líquido (manual), o antes si hay fuga o el freno queda pegado.
  - fallas: humedad: El líquido viejo trae agua: oxida el cilindro y el pistón por dentro y el pistón se pega.; edad: Los sellos se endurecen con los años y el calor: aparecen fugas o el pistón no regresa.; humedad: Si los pasadores se oxidan, el cuerpo deja de flotar y solo trabaja una pastilla.; maluso: La rosca del purgador se daña si lo aprietas de más. La hidrolavadora a presión directa también lo daña.
- **12 · Soporte del cáliper** · repara · BRACKET SUB ASSY., R. FR. · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - sintomas: El cáliper no se desliza.; Pastillas gastadas en cuña.; El freno roza aunque los sellos sean nuevos.
- **13 · Tornillos del soporte** · cambia · BOLT, FLANGE, 8X25 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - porque: Si están barridos o dudosos, van nuevos, con el torque y el fijador que indique el manual de servicio.
  - sintomas: Golpe o clic al frenar.; El cáliper se mueve con la mano.; Marcas del cáliper en el rin o en el disco.

## Cómo funciona
1. (heredado)
2. (heredado)
3. 3 · La presión viaja por el líquido. El líquido no se comprime: la presión llega al cáliper al instante, y sus dos pistones, con mucha más área que el de la bomba, multiplican tu fuerza (aprox.).
4. 4 · Los pistones empujan una pastilla. La presión saca los dos pistones (en el corte ves uno) y pegan la pastilla de su lado contra el disco. Cada sello se tuerce un poquito: eso servirá al soltar.
5. (heredado)
6. 6 · Fricción: el movimiento se vuelve calor. Las pastillas frenan el disco y la rueda. En una bajada larga el disco se calienta tanto que no se puede tocar. El líquido viejo, con agua, hierve antes y la manigueta se vuelve esponjosa.
7. (heredado)

## Si falla
- **Pastillas que llegan al metal**: Pastillas de freno (juego): Se gastan y nadie mira el indicador de desgaste. → Pastillas de freno (juego): La placa de acero raya el disco: ahora toca cambiar disco y pastillas. → Pistón del cáliper: Los pistones salieron de más para alcanzar el disco y se les pegó mugre. → Sellos del pistón (juego): Al meterlos para poner pastillas nuevas, la parte sucia raya el sello y aparece una fuga. Por eso se limpian antes de empujarlos.
- **Líquido de más de 2 años**: Pistón del cáliper: El líquido viejo tiene agua y pica los pistones. → Sellos del pistón (juego): El pistón picado rompe el sello: fuga y freno que no suelta. → Pastillas de freno (juego): La pastilla queda rozando, se recalienta y se cristaliza: frena menos.
- **Pasador del soporte seco**: Guardapolvo del pasador: El guardapolvo roto deja entrar agua y polvo. → Buje del pasador: El buje se oxida y el cáliper deja de flotar. → Pastillas de freno (juego): Frena una sola pastilla: se gasta dispareja y la moto frena menos.

## Cuándo
- Líquido de frenos: cambiar: Cada 2 años, aunque la moto ruede poco: el líquido absorbe agua. Usa DOT3 o DOT4 de envase sellado. Si no tienes experiencia purgando, hazlo en el taller (el manual lo pide así). · Manual del propietario Honda CB125F (español), cuadro de mantenimiento (págs. impresas 35-36), fila «Líquido de frenos»: 2 años; pág. 55: DOT3 o DOT4. Seguro
- Pastillas y nivel del líquido: revisar: Antes de rodar y en cada servicio. Cambia las dos pastillas del cáliper cuando una llegue al indicador de desgaste; si el nivel baja de la marca LOWER, revísalas. · Manual del propietario Honda CB125F (español), págs. impresas 40, 64 y 65: inspección previa, nivel del líquido y pastillas delanteras. Seguro

## Fuentes y certezas
- Seguro: Números, nombres y cantidad de piezas: catálogo de partes Honda CB 125F, figura F-10 «Front brake caliper», columna GLH125SH (versión con disco; sin las piezas Nissin).
- Seguro: Cáliper flotante de dos pistones, con soporte, un guardapolvo y un buje de pasador (catálogo).
- Seguro: Líquido DOT3 o DOT4, cambio cada 2 años, nivel sobre la marca LOWER y pastillas hasta el indicador de desgaste: manual del propietario, págs. impresas 40, 55, 64 y 65.
- Aprox.: Dibujo propio de TallerYa, adaptado del cáliper de otra lámina del esquema: vista de lado, proporciones aproximadas.
- Aprox.: Se dibujan uno de los dos pasadores y uno de los dos tapones; el catálogo trae 2 de cada uno.
- Aprox.: El disco y la barra son contexto (el disco está en la fig. F-11-3 de la rueda).
- Aprox.: Torques: el manual que tenemos es el del propietario y no los trae («manual de servicio»).

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-cb125f.pdf` (122 págs.): págs. del PDF 3 (impresa ?, 3 piezas), 24 (impresa ?, 3 piezas), 99 (impresa ?, 2 piezas), 100 (impresa ?, 2 piezas), 107 (impresa ?, 2 piezas), 117 (impresa 109, 2 piezas)
- `manual-usuario-cb125f.pdf` (123 págs.): págs. del PDF 94 (impresa ?, 2 piezas), 96 (impresa 87, 2 piezas), 98 (impresa ?, 2 piezas), 99 (impresa ?, 2 piezas), 106 (impresa ?, 2 piezas), 116 (impresa 107, 2 piezas)
  claves buscadas: cáliper, freno, guardapolvo, pasador, pastillas, pistón, purgador, resorte, sellos, soporte, tapón, tornillos

## Pendientes de la creadora
- Torques de los tornillos del soporte, del purgador y del tapón: falta el manual de servicio Honda (el PDF «manual-cb125f» es el del propietario).
- Fila «Pastillas y nivel» sin tarea en garaje/intervalos/honda_cb_125f.json.
- Sin 3D propio (con3d vacío): el cáliper de dos pistones no se modeló.
- Catálogo Honda extraído a mano con un script: extraer_catalogo.py no lee el formato Honda.
- Revisión UX: en transparente, 6 y 9 quedan a 3,9 px (solo al tocar la pieza).
- Revisión UX: el «cat» muestra el nombre del catálogo en inglés (así en todas las láminas).
