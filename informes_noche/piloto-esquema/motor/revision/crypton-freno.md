<!-- json 431832ffae72 -->
# Revisión rápida · crypton-freno

Freno delantero · Crypton FI 115 · catálogo crypton-bf24 fig. 25 · página `motor/crypton-freno.html`

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 1 avisos.
  - aviso: armado transparente: 14·14 y 11·11a muy juntos (2.0 px de radio); solo se ven al tocar la pieza
- Medición: Bloqueantes: ninguno · Medible APRUEBA · Notas estimadas (criterios medibles): 6: 4.5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.8

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Placa del disco ×1 · 2 Disco de freno ×1 · 3 Tornillos del disco ×4 · 4 Cáliper (cuerpo) ×1 · 5 Pistón del cáliper ×1 · 6 Empaques del cáliper ×1 · 7 Guardapolvo de un pasador del cáliper ×1 · 8 Guardapolvo del segundo pasador ×1 · 9 Purgador ×1 · 10 Pastillas de freno (juego) ×1 · 11 Grapas del pasador ×2 · 12 Soporte del cáliper ×1 · 13 Guía de las pastillas ×1 · 14 Resorte de las pastillas ×1 · 15 Pasador de las pastillas ×1 · 16 Tornillos del soporte del cáliper ×2

## Grupos
- **Disco**: Disco de freno, Placa del disco
- **Cáliper**: Cáliper (cuerpo), Pistón del cáliper, Empaques del cáliper, Empaques del cáliper, Guardapolvo de un pasador del cáliper, Guardapolvo del segundo pasador, Purgador, Soporte del cáliper, Guía de las pastillas
- **Pastillas**: Pastillas de freno (juego), Pastillas de freno (juego), Resorte de las pastillas, Pasador de las pastillas, Grapas del pasador, Grapas del pasador

## Desarme
1. Tornillos del soporte. Con la moto en el gato central y la rueda delantera en el aire, afloja los dos tornillos que sujetan el soporte a la barra.
2. Sacar el cáliper. Sale con su soporte, deslizándolo fuera del disco. Para cambiar pastillas no hace falta soltar la manguera: déjala colgando sin estirarla. Para el desarme completo, antes drena el líquido y suelta el perno de unión de la manguera.
3. Grapas. Saca las dos grapas que impiden que el pasador se salga.
4. Pasador de las pastillas. Sácalo. Es lo único que sostiene las pastillas: por eso las grapas importan.
5. Pastillas. Salen las dos, con su lámina antirruido. Si les queda 0,8 mm o menos de material, cambia el juego completo con su resorte y su guía.
6. Resorte de las pastillas. Las mantiene firmes para que no traqueteen. Hasta aquí llega un cambio de pastillas normal. Al armar: tornillos del soporte a 35 N·m, y bombea la manigueta hasta que quede firme antes de rodar.
7. Separar el cuerpo del soporte. El cuerpo del cáliper se desliza fuera de los pasadores del soporte. Así flota el cáliper: por eso esos pasadores deben quedar limpios y engrasados.
8. Guardapolvos de los pasadores. Son cauchos que protegen los pasadores del agua y del polvo. Si están rotos, el pasador se oxida.
9. Purgador. Desenróscalo con cuidado: es de acero y el cáliper es de aluminio, así que la rosca se daña fácil si aprietas de más.
10. Pistón. Sácalo con aire comprimido a poca presión por la entrada del líquido, con un trapo delante. Nunca con los dedos delante del pistón.
11. Empaques. Saca el sello y el guardapolvo del pistón con un palillo de plástico, sin rayar las ranuras. Se cambian siempre los dos, nunca se reutilizan.
12. Tornillos del disco. Con la rueda desmontada (otra lámina), afloja en cruz los tornillos del disco. Llevan fijador de rosca.
13. Disco. Sale con su placa (1). Al armar: tornillos con fijador, en cruz, 23 N·m; cáliper 35 N·m; purgador 6 N·m; líquido DOT 3 o DOT 4 nuevo y purgar hasta que la manigueta quede firme. Antes de rodar, prueba el freno con la moto quieta.

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **1 · Placa del disco** · reutiliza · taller · PLATE, FITTING · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Una placa delgada de acero con cuatro agujeros que va entre el disco (2) y el cubo de la rueda.
  - sirve: Reparte el apriete de los tornillos (3) y deja el disco bien asentado y derecho sobre el cubo.
  - porque: Si está plana y sin óxido, se vuelve a poner. Si se dobló, se pide sola.
  - cuando: Revísala cada vez que desmontes el disco.
  - fallas: maluso: Se dobla si se aprietan los tornillos sin orden o se olvida al armar.; humedad: El óxido la levanta y el disco queda chueco.
  - sintomas: El disco se ve torcido o vibra la manigueta al frenar después de cambiarlo.; La placa quedó doblada o falta al armar.
  - arrastra: Placa doblada → disco torcido → la manigueta pulsa al frenar.
  - conecta: 2, 3, rueda · efectos: 0
- **2 · Disco de freno** · cambia · taller · DISK, BRAKE (RIGHT) · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: Una placa redonda de acero, atornillada al cubo de la rueda con su placa (1). Gira siempre con la rueda.
  - sirve: Es lo que aprietan las pastillas (10). Convierte el movimiento de la moto en calor y lo bota al aire; los huecos lo enfrían y sacan el agua y el polvo.
  - porque: Cuando llega al mínimo grabado, está torcido o rajado, se cambia. En moto no se rectifica: casi no le sobra espesor. Si solo está untado de grasa, lávalo con limpiador de frenos y cambia las pastillas.
  - cuando: Mide el grosor y mira si está torcido en cada cambio de pastillas (10). Cámbialo si baja de 3,0 mm o se tuerce más de 0,15 mm (manual de taller Crypton FI 115, p. 6-6).
  - fallas: desgaste: Cada frenada le quita material. Con los años se adelgaza hasta el mínimo grabado («MIN TH»).; calor: Las bajadas largas frenando todo el tiempo (Las Palmas, la vía a Santa Elena) lo recalientan y lo pueden torcer.; maluso: Pastillas gastadas hasta el metal le hacen surcos. Grasa, lubricante de cadena o líquido de frenos lo dejan resbaloso.; golpe: Una caída o tornillos apretados disparejos lo pueden torcer.
  - sintomas: La manigueta palpita o vibra al frenar (disco torcido).; Surcos o rayas que sientes con la uña.; Frena menos aunque las pastillas sean nuevas.; Un «chas-chas» rítmico a poca velocidad, o manchas azuladas por recalentamiento.
  - arrastra: Disco torcido → la manigueta palpita y las pastillas (10) se gastan disparejo.; Disco untado de aceite → las pastillas se untan y hay que cambiarlas.
  - conecta: 3, 10, 4, rueda · efectos: 0
- **3 · Tornillos del disco** · cambia · taller · BOLT,HEX. SOCKET BUTTON · 4 piezas · aprox.: sirve, sintomas, fallas, cuando
  - que: Los cuatro tornillos que unen el disco (2) y su placa (1) al cubo de la rueda.
  - sirve: Pasan toda la fuerza del frenado del disco a la rueda. Son pocos y trabajan mucho.
  - porque: Si están barridos van nuevos. Al armar: fijador de rosca (LOCTITE), en cruz y a 23 N·m (manual de taller Crypton FI 115, p. 6-7).
  - cuando: Revísalos cada vez que desmontes la rueda o el disco.
  - fallas: maluso: Se aflojan si los montas sin fijador de rosca o sin el torque del manual de servicio.; maluso: La cabeza se barre con una llave que no es del tamaño exacto.; humedad: Se oxidan y luego no salen, sobre todo si nunca se han tocado.
  - sintomas: Un clic o golpe al empezar a frenar.; El disco tiene juego al moverlo con la mano.; La cabeza está redondeada (barrida).
  - arrastra: Tornillo flojo → el disco (2) se mueve y suena al frenar.
  - conecta: 2, rueda · efectos: 0
- **4 · Cáliper (cuerpo)** · repara · taller · CALIPER ASSY (RIGHT) · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: La «pinza» del freno: un cuerpo de aluminio con un cilindro adentro. En la Crypton es flotante y de un solo pistón.
  - sirve: Convierte la presión del líquido (liquido) en fuerza sobre las pastillas (10). El pistón (5) empuja una pastilla y el cuerpo se corre en sus pasadores para jalar la otra.
  - porque: El cuerpo se limpia y se le cambian los empaques (6) y el líquido. Solo se cambia entero si el cilindro está picado.
  - cuando: Límpialo y revísalo en cada cambio de pastillas. Los empaques de adentro se renuevan cada 2 años con el líquido (manual del propietario, p. 7-21), o antes si hay fuga o el freno queda pegado.
  - fallas: humedad: El líquido viejo trae agua: oxida el cilindro y el pistón por dentro y el pistón se pega.; edad: Los empaques se endurecen con los años y el calor: aparecen fugas o el pistón no regresa.; humedad: Si los pasadores se oxidan, el cuerpo deja de flotar y solo trabaja una pastilla.; maluso: La rosca del purgador se daña si lo aprietas de más. La hidrolavadora a presión directa también lo daña.
  - sintomas: La rueda queda frenada o caliente después de rodar.; Olor a quemado después de frenar.; Una pastilla se gasta mucho más que la otra.; Manchas de líquido alrededor, o el nivel del depósito baja sin que las pastillas estén gastadas.
  - arrastra: Cáliper que no flota → una sola pastilla se gasta y el disco (2) se recalienta de un lado.; Cilindro oxidado → el pistón (5) se pega y el freno queda arrastrando.
  - conecta: 5, 6, 9, 10, 12, 13, 14, 15, 7, 8, manguera · efectos: 0
- **5 · Pistón del cáliper** · cambia · taller · PISTON ASSY, CALIPER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un cilindro metálico, hueco por delante, que vive dentro del cáliper (4).
  - sirve: El líquido lo empuja por detrás y él empuja la pastilla (10). Como es mucho más grande que el pistón de la bomba, multiplica la fuerza de tu mano.
  - porque: Si está picado o rayado no sella y va uno nuevo.
  - cuando: Revísalo cada vez que abras el cáliper: cada 2 años, al cambiar los empaques junto con el líquido (manual del propietario, p. 7-21), o antes si hay problemas. Antes de meterlo para poner pastillas nuevas, límpiale la parte que queda afuera y mételo con el purgador abierto y una manguera a un frasco (manual de taller, p. 6-26).
  - fallas: humedad: El agua del líquido viejo lo pica por dentro (corrosión).; desgaste: Con pastillas muy gastadas sale de más y se le pega mugre. Al meterlo para poner pastillas nuevas, esa parte sucia raya el sello (6).; calor: El calor de un freno pegado lo dilata y empeora el problema.
  - sintomas: El freno no suelta del todo.; Fuga de líquido detrás de la pastilla.; La pastilla del lado del pistón se gasta más.
  - arrastra: Pistón sucio o picado → rompe el sello (6) y el cáliper bota líquido.
  - conecta: 4, 6, 10 · efectos: 0
- **6 · Empaques del cáliper** · cambia · taller · CALIPER SEAL KIT · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: Dos anillos de caucho: el sello del pistón (adentro) y el guardapolvo (afuera).
  - sirve: El sello no deja salir el líquido y, al soltar el freno, jala el pistón (5) de vuelta: se tuerce un poquito al frenar y regresa. El guardapolvo no deja entrar agua ni mugre.
  - porque: El caucho no se repara. Se cambian siempre los dos, nunca se reutilizan.
  - cuando: Cámbialos cada 2 años, junto con el líquido (liquido), y siempre que abras el cáliper (manual de taller, p. 6-29), o antes si hay fuga o el freno queda pegado.
  - fallas: edad: Se endurecen con los años y el calor: pierden elasticidad y ya no regresan el pistón.; maluso: Se hinchan y se dañan con un líquido equivocado (DOT 5, aceite, gasolina usada para «lavar»).; humedad: Si el guardapolvo se rompe, entra agua y el pistón se oxida.
  - sintomas: El freno queda pegado o la rueda se calienta.; Fuga de líquido en el cáliper.; La manigueta se va al fondo (entró aire).
  - arrastra: Sello endurecido → el pistón (5) no regresa y las pastillas rozan el disco.
  - conecta: 5, 4 · efectos: 0
- **7 · Guardapolvo de un pasador del cáliper** · cambia · taller · BOOT, CALIPER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Un fuelle de caucho entre el cuerpo del cáliper (4) y uno de los pasadores del soporte (12).
  - sirve: Protege el pasador para que el cáliper siga deslizándose (flotando) sin oxidarse.
  - porque: Si está rajado o suelto, cámbialo; con el caucho roto el pasador se oxida.
  - cuando: Míralo en cada cambio de pastillas.
  - fallas: edad: El caucho se reseca y se raja.; calor: El calor del freno lo endurece.; maluso: Se hincha con grasa común (no de frenos) o se sale de su sitio si lo montas mal.
  - sintomas: El caucho está rajado o fuera de su sitio.; Con el cáliper desmontado, no se deja mover con la mano.; Las pastillas se gastan disparejo.
  - arrastra: Guardapolvo roto → entra agua, el pasador del soporte (12) se oxida y el cáliper deja de flotar.
  - conecta: 12, 4 · efectos: 0
- **8 · Guardapolvo del segundo pasador** · cambia · taller · BOOT 2 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El fuelle de caucho del segundo pasador deslizante.
  - sirve: Igual que el otro guardapolvo (7): mantiene limpio y seco el pasador para que el cáliper flote.
  - porque: Si está roto, cámbialo antes de que el pasador se oxide.
  - cuando: Míralo en cada cambio de pastillas.
  - fallas: edad: Se reseca y se raja con los años.; humedad: Si está roto, entra agua y el pasador se oxida.
  - sintomas: El caucho está roto.; El freno queda rozando.; Una pastilla se gasta en cuña.
  - arrastra: Guardapolvo roto → el pasador se oxida y el cáliper (4) se traba.
  - conecta: 12, 4 · efectos: 0
- **9 · Purgador** · cambia · taller · BLEED SCREW KIT · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: Un tornillo hueco en la parte alta del cáliper (4), con una tapita de caucho.
  - sirve: Por ahí sale el aire y el líquido viejo cuando cambias el líquido (liquido) o purgas.
  - porque: Si está pegado, barrido o tapado, va uno nuevo.
  - cuando: Se usa en cada cambio de líquido: cada 2 años (manual del propietario). Al cerrarlo, 6 N·m (manual de taller Crypton FI 115, p. 6-27): es fácil barrer la rosca.
  - fallas: maluso: Se parte o barre la rosca del cáliper si lo aprietas de más.; humedad: Sin tapita entran agua y mugre, el agujero se tapa y el purgador se pega por óxido.
  - sintomas: Gotas de líquido en el purgador.; No deja purgar (está tapado).; La manigueta sigue esponjosa después de purgar.
  - arrastra: Purgador tapado → no sale el aire y la manigueta queda esponjosa.
  - conecta: 4, manguera · efectos: 0
- **10 · Pastillas de freno (juego)** · cambia · taller · BRAKE PAD KIT · 1 pieza · aprox.: sirve, fallas
  - que: El juego trae dos pastillas: placas de acero con un bloque de fricción pegado y ranuras que avisan el desgaste. Trae también la lámina antirruido (cuña) que va detrás.
  - sirve: Son las que rozan el disco (2). Se gastan a propósito para que el disco dure.
  - porque: Se cambia el juego completo, y con él el resorte (14) y la guía (13) nuevos, como pide el manual de taller (p. 6-26).
  - cuando: Míralas en cada servicio del cuadro de mantenimiento (manual del propietario, p. 7-4). Cámbialas cuando les quede 0,8 mm de material (manual de taller Crypton FI 115, p. 6-26).
  - fallas: desgaste: Cada frenada las gasta. En Medellín se gastan más rápido por las lomas, el trancón y frenar solo con el delantero.; calor: Con calor sostenido se cristalizan: la cara queda brillante, chillan y frenan menos.; maluso: Aceite, grasa o líquido de frenos las contaminan. Una pastilla untada no se recupera.; desgaste: Si llegan al metal, el acero raya el disco.
  - sintomas: La ranura del centro ya casi no se ve.; Chillido metálico o raspado al frenar.; Frena menos y tienes que apretar más.; El nivel del depósito baja poco a poco.
  - arrastra: Pastillas al metal → rayan el disco (2).; Pastillas untadas → frenas menos y toca cambiarlas.
  - conecta: 2, 5, 15, 14 · efectos: 0
- **11 · Grapas del pasador** · cambia · taller · CLIP · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Dos grapas de alambre de acero, en forma de R, que se meten en el pasador (15).
  - sirve: Impiden que el pasador de las pastillas se salga con la vibración.
  - porque: Son baratas: si falta una, está floja o deformada, pon una nueva.
  - cuando: En cada cambio de pastillas.
  - fallas: maluso: Se pierden al cambiar pastillas o se deforman si las sacas con alicate.; edad: Pierden tensión con el tiempo.
  - sintomas: La grapa falta o está floja.; El pasador se mueve o se sale.
  - arrastra: Grapa floja → el pasador (15) se sale y las pastillas quedan sueltas.
  - conecta: 15 · efectos: 0
- **12 · Soporte del cáliper** · repara · taller · SUPPORT BRACKET ASSY · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Una pieza fundida que se atornilla a la barra. En sus dos pasadores se desliza el cuerpo del cáliper (4).
  - sirve: Aguanta la fuerza del frenado y deja flotar el cáliper para que las dos pastillas aprieten parejo.
  - porque: Si los pasadores solo están sucios, se limpian y engrasan. Si está doblado o los pasadores están picados, se cambia.
  - cuando: Revisa los pasadores en cada cambio de pastillas: límpialos y engrásalos con grasa de silicona para frenos.
  - fallas: humedad: Los pasadores se oxidan si los guardapolvos están rotos.; golpe: Se dobla en una caída o con un golpe en la rueda.; maluso: Las roscas se dañan si aprietas de más los tornillos (16).
  - sintomas: El cáliper no se desliza.; Pastillas gastadas en cuña.; El freno roza aunque los empaques sean nuevos.
  - arrastra: Pasadores oxidados → el cáliper (4) deja de flotar y una sola pastilla trabaja.
  - conecta: 4, 16, 7, 8, barra · efectos: 0
- **13 · Guía de las pastillas** · cambia · taller · PAD, SUPPORT 2 · 1 pieza · aprox.: sirve, sintomas, fallas, cuando
  - que: Una lámina pequeña de acero que se encaja en el soporte (12) del cáliper, donde se apoyan las pastillas (10).
  - sirve: Deja que las pastillas se deslicen sin traquetear contra el aluminio del soporte.
  - porque: Va nueva con las pastillas: el manual pide cambiar el resorte y esta guía en conjunto.
  - cuando: En cada cambio de pastillas.
  - fallas: edad: Se oxida y pierde tensión.; maluso: Se olvida o se pone al revés al cambiar pastillas.
  - sintomas: Ruido metálico o traqueteo al pasar huecos.; Las pastillas se pegan y una se gasta más.
  - arrastra: Guía oxidada → pastilla trabada → roce y calor.
  - conecta: 10, 12 · efectos: 0
- **14 · Resorte de las pastillas** · cambia · taller · SUPPORT, PAD · 1 pieza · aprox.: sirve, sintomas, fallas, cuando
  - que: Una lámina de acero doblada que hace de resorte sobre las pastillas (10).
  - sirve: Las mantiene firmes contra el pasador para que no traqueteen ni vibren.
  - porque: Va nuevo con cada juego de pastillas (manual de taller Crypton FI 115, p. 6-26). Fíjate que quede puesto como estaba.
  - cuando: En cada cambio de pastillas.
  - fallas: edad: Pierde tensión.; humedad: Se oxida.; maluso: Se monta al revés al cambiar pastillas.
  - sintomas: Traqueteo en los huecos o en el empedrado.; Chillido.; Pastillas gastadas en cuña.
  - arrastra: Resorte flojo → las pastillas (10) traquetean y se gastan en cuña.
  - conecta: 10, 4 · efectos: 0
- **15 · Pasador de las pastillas** · cambia · taller · PIN, PAD · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: Una varilla de acero que atraviesa el cáliper (4) y las orejas de las pastillas (10).
  - sirve: Sostiene las pastillas y las deja deslizarse hacia el disco y de regreso.
  - porque: Si está oxidado, doblado o con surcos, cámbialo.
  - cuando: Límpialo en cada cambio de pastillas y úntale muy poca grasa de silicona (manual de taller, p. 6-27), sin que toque las pastillas.
  - fallas: humedad: Se oxida y las pastillas no deslizan.; desgaste: Las orejas de las pastillas le hacen surcos con la vibración.; golpe: Se dobla si lo sacas a golpes.
  - sintomas: Una pastilla no se despega del disco.; Ruido metálico.; Se le ven surcos.
  - arrastra: Pasador oxidado → una pastilla queda pegada al disco (2) y se calienta.
  - conecta: 10, 11, 4 · efectos: 0
- **16 · Tornillos del soporte del cáliper** · cambia · taller · SCREW · 2 piezas · aprox.: sirve, sintomas, fallas, cuando
  - que: Los dos tornillos que fijan el soporte (12) a las orejas de la barra.
  - sirve: Aguantan toda la fuerza del frenado de la rueda delantera. Son de seguridad.
  - porque: Si están barridos o dudosos, van nuevos. Al armar: 35 N·m (manual de taller Crypton FI 115, p. 6-27).
  - cuando: Revisa el apriete después de cualquier trabajo en la rueda o en los frenos.
  - fallas: maluso: Quedan flojos si después de montar la rueda no los aprietas con torquímetro.; maluso: Se barren si aprietas de más; sin fijador se aflojan con la vibración.
  - sintomas: Golpe o clic al frenar.; El cáliper se mueve con la mano.; Marcas del cáliper en el rin o en el disco.
  - arrastra: Tornillo flojo → el soporte (12) golpea al frenar y el cáliper puede morder el disco.
  - conecta: 12, barra · efectos: 0
- **barra · Barra derecha de la suspensión** · repara · taller · Lámina 18 (dirección y suspensión) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La barra donde va atornillado el soporte (12) del cáliper.
  - sirve: Sostiene la rueda y el freno.
  - porque: Si hay aceite, se arregla el retenedor y se limpia el disco; si el aceite tocó las pastillas, van pastillas nuevas.
  - cuando: Mira si hay aceite en la barra en cada lavada.
  - fallas: edad: Si su retenedor bota aceite, el aceite baja por la barra y puede caer en el disco (2) y las pastillas (10).
  - sintomas: Aceite en la barra o en el disco.; El freno pierde agarre de repente.
  - arrastra: Retenedor que bota aceite → disco (2) y pastillas untados.
  - conecta: 12, 16 · efectos: 0
- **rueda · Rueda delantera** ·  ·  · Lámina 21
  - que: El rin donde va atornillado el disco (2).
  - sirve: — falta
  - porque: — falta
  - cuando: — falta
  - fallas: — falta
  - sintomas: — falta
  - arrastra: — falta
  - conecta: 2, 3 · efectos: 0
- **liquido · Líquido de frenos DOT 3 o DOT 4** · cambia · taller · Lámina 26 · plan de TallerYa · aprox.: sirve, sintomas, porque
  - que: El líquido que llena la bomba, la manguera y el cáliper (4).
  - sirve: No se deja comprimir: por eso pasa la fuerza de tu mano al cáliper al instante.
  - porque: Es DOT 3 o DOT 4 y se cambia por tiempo, no por kilómetros.
  - cuando: Cámbialo cada 2 años, ruede lo que ruede (manual del propietario). No mezcles tipos: rellena con el mismo que tiene.
  - fallas: humedad: Absorbe la humedad del aire con los años. Con agua hierve antes: nuevo hierve sobre 230 °C y con humedad puede bajar a unos 155 °C (mínimos de la norma).; calor: Si hierve en una bajada larga se forman burbujas, y las burbujas sí se comprimen.
  - sintomas: La manigueta se siente esponjosa o se va al fondo después de frenar mucho.; El líquido se ve oscuro en el visor.
  - arrastra: Líquido con agua → hierve antes y el pistón (5) se oxida por dentro.
  - conecta: 4, 9, manguera · efectos: 0
- **manguera · Manguera del freno** · cambia · taller · Fig. 28 · HOSE, BRAKE 1 (bomba → cáliper), con dos pernos de unión y cuatro arandelas · aprox.: sirve, sintomas, fallas
  - que: Una sola manguera va de la bomba del manubrio al cáliper (4). Cada punta lleva un perno hueco (de unión) con dos arandelas.
  - sirve: Pasa la presión de tu mano al cáliper sin inflarse.
  - porque: El caucho no se repara: si está agrietada o inflada, se cambia, con arandelas nuevas en los dos pernos de unión (26 N·m, manual de taller Crypton FI 115, p. 6-31). Después hay que purgar.
  - cuando: Revísala en cada servicio y cámbiala cada 4 años (manual del propietario, p. 7-4).
  - fallas: edad: El caucho se agrieta y se infla con los años.; golpe: Se pellizca si queda mal guiada al girar el manubrio.
  - sintomas: La manigueta se siente esponjosa.; Ves grietas o humedad en la manguera.
  - arrastra: Manguera inflada → la manigueta se siente esponjosa y el cáliper (4) recibe menos presión.
  - conecta: 4, 9 · efectos: 0

## Cómo funciona
1. 1 · En reposo. La rueda gira y el disco gira con ella. Las pastillas quedan casi tocando el disco, a una fracción de milímetro (aquí el espacio está exagerado para que se vea).
2. 2 · Aprietas la manigueta derecha. La manigueta es una palanca: con poco esfuerzo empuja un pistón pequeño dentro de la bomba, en el manubrio.
3. 3 · La presión viaja por el líquido. El líquido no se comprime: la presión llega al cáliper al instante y su pistón, más grande que el de la bomba, multiplica tu fuerza (aprox.).
4. 4 · El pistón empuja una pastilla. La presión saca el pistón del cáliper y este pega la pastilla de su lado contra el disco. El sello del pistón se tuerce un poquito: eso servirá al soltar.
5. 5 · El cáliper flota y jala la otra. El cuerpo del cáliper se desliza sobre pasadores: al empujar, se corre al otro lado y trae la otra pastilla, y el disco queda prensado por los dos lados. Si los pasadores están oxidados, frena una sola pastilla.
6. 6 · Fricción: el movimiento se vuelve calor. Las pastillas frenan el disco y la rueda, y el movimiento se vuelve calor: en una bajada larga el disco pasa de 200 °C (aprox.). El líquido viejo, con agua, hierve antes y la manigueta se vuelve esponjosa.
7. 7 · Sueltas. La presión cae. El sello, que estaba torcido, regresa el pistón y las pastillas se despegan apenas del disco. Si el sello está viejo o el pistón sucio, el pistón no regresa: el freno queda pegado y se calienta solo.

## Si falla
- **Pastillas que llegan al metal**: Pastillas de freno (juego): Se gastan y nadie revisa la ranura. → Disco de freno: La placa de acero raya el disco: ahora toca cambiar disco y pastillas. → Pistón del cáliper: El pistón salió de más para alcanzar el disco y se le pegó mugre. → Empaques del cáliper: Al meter el pistón para poner pastillas nuevas, la parte sucia raya el sello y aparece una fuga. Por eso se limpia antes de empujarlo.
- **Líquido y empaques de más de 2 años**: Líquido de frenos DOT 3 o DOT 4: Absorbió agua y hierve antes. → Pistón del cáliper: El agua oxida el pistón por dentro. → Empaques del cáliper: Los empaques, que el manual manda cambiar junto con el líquido cada 2 años, se endurecen y ya no regresan el pistón. → Pastillas de freno (juego): La pastilla queda rozando, se calienta y se cristaliza.
- **Guardapolvo roto**: Guardapolvo de un pasador del cáliper: El caucho se raja y entra agua. → Soporte del cáliper: El pasador del soporte se oxida y se traba. → Cáliper (cuerpo): El cáliper deja de flotar. → Pastillas de freno (juego): Solo trabaja la pastilla del pistón y se gasta sola. → Disco de freno: El disco se recalienta de un lado y se puede torcer.
- **Retenedor de la barra que bota aceite**: Barra derecha de la suspensión: El aceite baja por la barra. → Disco de freno: Cae al disco: el freno pierde agarre de golpe. → Pastillas de freno (juego): Las pastillas se untan y no se recuperan: se cambian.
- **Tornillos sin apretar después de montar la rueda**: Tornillos del soporte del cáliper: Quedan flojos. → Soporte del cáliper: El soporte se mueve y golpea al frenar. → Disco de freno: El cáliper muerde el disco: es lo más peligroso de la lámina.

## Cuándo
- Pastillas: revisar el desgaste: En cada servicio. Cámbialas con 0,8 mm de material o cuando la ranura casi desaparezca. · Manual del propietario, cuadro de mantenimiento (p. 7-4) y p. 7-19; límite: manual de taller Crypton FI 115, p. 6-26. Seguro
- Líquido de frenos DOT 3 o DOT 4: cambiar: Cada 2 años, ruede lo que ruede. · Manual del propietario Yamaha Crypton FI (T115FL-5, códigos BF2), copia entregada por el usuario, cuadro de mantenimiento y sección 'Líquido de frenos'; consultado el 14-nov-2026 Seguro
- Manguera del freno: cambiar: Cada 4 años, y revisa grietas en cada servicio. · Manual del propietario, p. 7-4. Seguro
- Disco: medir grosor y mirar si está torcido: En cada cambio de pastillas: mínimo 3,0 mm y torcido máximo 0,15 mm. · manual de taller Crypton FI 115, p. 6-6. Seguro
- Cáliper, pasadores y guardapolvos: limpiar y revisar: En cada cambio de pastillas. · Práctica de taller (el manual no da intervalo para estas piezas). Práctica de taller

## Fuentes y certezas
- Seguro: Números, nombres y cantidad de piezas: catálogo de partes Crypton FI 115 BF24 (2019, Colombia), fig. 25 «Front brake caliper».
- Seguro: Cáliper flotante de un pistón, con soporte y dos guardapolvos de pasador; cuatro tornillos del disco con su placa (catálogo, fig. 25).
- Seguro: Una sola manguera de la bomba al cáliper (catálogo, fig. 28).
- Seguro: Pastillas: límite 0,8 mm; resorte y soporte nuevos con cada juego. Disco: mínimo 3,0 mm, torcido máx. 0,15 mm. Torques: disco 23 N·m con fijador, cáliper 35 N·m, purgador 6 N·m, pernos de unión 26 N·m (manual de taller Crypton FI 115, pp. 6-6, 6-7, 6-26, 6-27 y 6-31).
- Seguro: Líquido DOT 3 o DOT 4 cada 2 años, manguera cada 4 años, pastillas con ranura indicadora (manual del propietario, pp. 7-4 y 7-19).
- Aprox.: Proporciones del dibujo: adaptadas de otra lámina de freno de TallerYa y del plano de la Crypton; no se midió una pieza real.
- Aprox.: Orden de desarme: el del manual de taller (p. 6-24) y el procedimiento general de un cáliper flotante.
- Aprox.: Cifras de la animación (temperaturas, multiplicación de fuerza): aproximadas.

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-propietario-crypton-fi.pdf` (97 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 9 (impresa 1-1, 5 piezas), 41 (impresa 7-4, 4 piezas), 69 (impresa 7-32, 6 piezas), 70 (impresa 7-33, 5 piezas), 71 (impresa 7-34, 4 piezas), 82 (impresa 8-3, 4 piezas)
- `manual-taller-crypton-fi-115.pdf` (199 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 101 (impresa 6-22, 6 piezas), 103 (impresa 6-24, 7 piezas), 105 (impresa 6-26, 6 piezas), 107 (impresa 6-28, 6 piezas), 110 (impresa 6-31, 6 piezas), 194 (impresa 8-4, 6 piezas)
- `manual-usuario-crypton-fi.pdf` (101 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 11 (impresa 3-6, 5 piezas), 31 (impresa 4-3, 5 piezas), 68 (impresa 6-30, 5 piezas), 69 (impresa 6-31, 4 piezas), 70 (impresa 6-32, 4 piezas), 78 (impresa 8-2, 4 piezas)
  claves buscadas: barra, crypton, cáliper, disco, empaques, freno, grapas, guardapolvo, líquido, manguera, pasador, pastillas, pistón, placa, purgador, resorte, rueda, soporte, tornillos · para más: `buscar_manual.py crypton-bf24 "palabra,otra" --paginas N-M`

## Pendientes de la creadora
- Diámetro del disco sin dato en las fuentes; el dibujo usa una proporción aproximada.
