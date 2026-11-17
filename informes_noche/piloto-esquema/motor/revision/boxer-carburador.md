<!-- json 05cee0e680bc -->
# Revisión rápida · boxer-carburador

Carburador · Bajaj Boxer CT100 · catálogo boxer-ct100 fig. 16 · página `motor/boxer-carburador.html`

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 4 avisos.
  - aviso: armado transparente: 10·10 y 19·19 muy juntos (6.2 px de radio); solo se ven al tocar la pieza
  - aviso: v2.grupos[cuerpo]: «Desarmar» no mueve 1
  - aviso: v2.grupos[flota]: la píldora del grupo apunta a piezas que no se ven armadas (¿kit sin cuerpo? va en «kits», sin grupo)
  - aviso: v2.grupos[chicles]: la píldora del grupo apunta a piezas que no se ven armadas (¿kit sin cuerpo? va en «kits», sin grupo)
- Medición: Bloqueantes: ninguno · Medible APRUEBA · Notas estimadas (criterios medibles): 6: 5 · 8: 4.3 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.82

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Cuerpo del carburador ×1 · 2 Aislador del carburador ×1 · 3 O-ring del aislador ×1 · 4 Kit Carburador ×1 · 5 Empaques de la taza y la tapa ×1 · 6 Kit Flota y Aguja Paso Gasolina ×1 · 7 Tornillo de la mezcla ×1 · 8 Tornillo del ralentí ×1 · 9 Tornillos del carburador ×2 · 10 Chiclé de alta ×1 · 11 Tornillos de la taza ×2 · 12 Cortina ×1 · 13 Imán del sensor ×1 · 14 Cable del sensor ×1 · 15 Tornillo del imán ×1 · 16 Tapa del carburador ×1 · 17 Resorte de la cortina ×1 · 18 Aguja de la cortina ×1 · 19 Boquerel de baja ×1 · 20 Aguja de corte de la flota ×1 · 21 Flota ×1

## Grupos (nombre (id); tornillería aparte)
- **Tapa, cortina y aguja** [tapa]: Tapa del carburador (16), Resorte de la cortina (17), Cortina (12), Aguja de la cortina (18)
- **Montaje al motor** [montaje]: Aislador del carburador (2), O-ring del aislador (3) · Tornillos del carburador (9)
- **Sensor del acelerador** [sensor]: Imán del sensor (13), Cable del sensor (14) · Tornillo del imán (15)
- **Cuerpo y taza** [cuerpo]: Cuerpo del carburador (1), Cuerpo del carburador (1t), Empaques de la taza y la tapa (5) · Tornillos de la taza (11)
- **Flota y aguja de corte** [flota]: Flota (21), Aguja de corte de la flota (20)
- **Chiclés** [chicles]: Chiclé de alta (10), Boquerel de baja (19)
- **Tornillos de ajuste** [ajuste]: Tornillo de la mezcla (7), Tornillo del ralentí (8)

## Desarme
1. Antes. Motor frío, llave de gasolina en OFF y sin chispas cerca. Afloja la tapa (16) y saca con el cable la cortina (12), el resorte (17) y la aguja (18), sin doblarla. Al armar, la cortina entra en su guía, el acelerador vuelve solo y nada gotea.
2. Carburador fuera. Suelta la manguera de gasolina sobre un trapo (sin chispas), el ducto del filtro y el conector del sensor (14). Quita los tornillos (9): el aislador (2) y su o-ring (3) quedan en el motor. Al armar, que no gotee.
3. Taza. Lejos de chispas, vacía la gasolina en un recipiente. Quita los tornillos (11) y baja la taza con su empaque (5). Agua o mugre en el fondo explican que se apague. Al armar: empaque nuevo y que no gotee.
4. Flota y aguja de corte. Saca el pasador y levanta la flota (21) con la aguja (20) colgada. Mira la punta de la aguja: con un escalón o rayas no sella y la taza rebosa.
5. Chiclés. Desenrosca el chiclé de alta (10) y el boquerel de baja (19) con un destornillador justo. Límpialos con limpiador y aire, nunca con alambre: agranda el orificio.
6. Ajuste. Cierra el tornillo de la mezcla (7) suave, sin forzar, contando las vueltas y anótalas antes de sacarlo. Al armar: mismas vueltas, empaques nuevos, sin fugas y ralentí a 1.300 rpm en caliente con el tornillo del ralentí (8).

## Fichas (todos los campos; «(heredado)» = igual que en la hermana, ya revisado; «— falta» = vacío; aprox. = sin fuente)
- **1 · Cuerpo del carburador** · repara · taller · Carburador (PB-16) · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El bloque de aluminio del carburador: el paso del aire, la torre de la cortina y los conductos de gasolina. Abajo lleva la taza.
  - sirve: Junta el aire que entra del filtro con la gasolina de la taza y le manda la mezcla al motor.
  - porque: Casi siempre basta limpiarlo y cambiar empaques; si la torre está rayada o torcida, se cambia completo.
  - cuando: Límpialo cuando la moto prenda mal o cada vez que limpies la taza.
  - fallas: mugre: La gasolina vieja deja barniz y tapa los conductos finos.; golpe: Una caída tuerce la torre y la cortina se pega.
  - sintomas: La moto no prende o se apaga en ralentí.; Huele a gasolina cerca del carburador.; Gotea gasolina por la taza.
  - arrastra: conductos tapados → el boquerel de baja (19) no chupa y el ralentí se cae
  - conecta: 12, 10, 21 · efectos: 0
- **2 · Aislador del carburador** · cambia · facil · Insulador Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El acople de caucho y plástico entre el carburador y la culata.
  - sirve: Sella el paso de la mezcla y aísla el carburador del calor del motor para que la gasolina no hierva.
  - porque: Rajado deja entrar aire falso: no se repara.
  - cuando: Revísalo cada vez que saques el carburador.
  - fallas: calor: El calor del motor endurece y raja el caucho.; apriete: Los tornillos muy apretados lo deforman.
  - sintomas: El ralentí sube y baja solo.; Se oye un silbido de aire con el motor prendido.; Ves grietas en el caucho.
  - arrastra: rajado → entra aire falso y la mezcla queda pobre
  - conecta: 3, 9, 1 · efectos: 0
- **3 · O-ring del aislador** · cambia · facil · Anillo Retén Múltiple Admisión · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El anillo de caucho entre el aislador y el carburador.
  - sirve: Sella la unión para que no entre aire sin pasar por el carburador.
  - porque: Es barato y viene en el kit de empaques: va nuevo siempre que lo desarmes.
  - cuando: Cámbialo cada vez que saques el carburador.
  - fallas: edad: Se aplana y endurece con el calor.
  - sintomas: Ralentí inestable.; Silbido en la unión del carburador.
  - arrastra: aplanado → aire falso y mezcla pobre
  - conecta: 2, 1 · efectos: 0
- **5 · Empaques de la taza y la tapa** · cambia · taller · Kit Empaques Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los empaques de caucho: el de la taza (el grande) y el o-ring de la tapa de la cortina. Vienen en el kit de empaques.
  - sirve: Sellan la taza para que no gotee gasolina y la tapa para que no entre agua ni mugre a la cortina.
  - porque: Un empaque que gotea gasolina es riesgo de incendio: va nuevo siempre que abras la taza.
  - cuando: Cámbialos cada vez que abras la taza.
  - fallas: edad: La gasolina los hincha o los endurece.; mal armado: Si queda mordido al cerrar la taza, gotea desde el primer día.
  - sintomas: Gotea gasolina por la unión de la taza.; Huele a gasolina con la moto parada.
  - arrastra: empaque duro → gotea gasolina sobre el motor caliente
  - conecta: 11, 1 · efectos: 0
- **7 · Tornillo de la mezcla** · reutiliza · taller · Tornillo Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tornillo pequeño con resorte en el costado del cuerpo: regula el aire del circuito de baja (el manual lo llama tornillo de aire).
  - sirve: Regula cuánta mezcla pasa en ralentí: al cerrarlo o abrirlo cambias qué tan rica queda la mezcla con la cortina casi cerrada.
  - porque: Sano se vuelve a usar; si la punta está marcada, se cambia.
  - cuando: Ajústalo solo si el ralentí queda mal después de limpiar el carburador.
  - fallas: mal ajuste: Alguien lo movió sin contar vueltas.; golpe: Apretarlo a fondo daña la punta y su asiento.
  - sintomas: El ralentí queda inestable después de una limpieza.; La moto se apaga al soltar el acelerador.
  - arrastra: mal ajustado → el ralentí se cae o el motor queda rico
  - conecta: 8, 19 · efectos: 0
- **8 · Tornillo del ralentí** · reutiliza · facil · Tornillo Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tornillo con resorte de la torre, con la cabeza moleteada para girarlo con los dedos.
  - sirve: Topa la cortina para que no cierre del todo: fija las vueltas del motor en ralentí.
  - porque: Sano se vuelve a usar; el resorte lo mantiene en su sitio.
  - cuando: Ajusta el ralentí a 1.300 rpm aprox. con el motor caliente.
  - fallas: vibración: Se va aflojando y el ralentí baja.
  - sintomas: El motor se apaga en los semáforos.; El ralentí queda muy acelerado.
  - arrastra: muy bajo → la moto se apaga al frenar
  - conecta: 12, 7 · efectos: 0
- **9 · Tornillos del carburador** · reutiliza · facil · Tornillo Carburador · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los dos tornillos que pasan por la brida del carburador y lo sujetan al motor.
  - sirve: Aprietan el carburador contra el aislador para que no entre aire.
  - porque: Sanos se vuelven a usar, apretados parejo y sin exceso.
  - cuando: Revísalos cuando saques el carburador.
  - fallas: vibración: Se aflojan.; apriete: Pasarse de fuerza raja la brida de aluminio.
  - sintomas: Silbido de aire en la unión.; El carburador se mueve con la mano.
  - arrastra: flojos → aire falso y ralentí inestable
  - conecta: 2, 3, 1 · efectos: 0
- **10 · Chiclé de alta** · repara · taller · Difusor · 1 pieza · también en el kit ref. 4 (kit del carburador, 36DU1206) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El chiclé de bronce con su difusor, debajo de la torre: el difusor es el tubo con huecos por donde entra la aguja.
  - sirve: Mide la gasolina que pasa con media y mucha aceleración: el orificio calibrado pone el tope.
  - porque: Tapado se limpia con limpiador y aire; agrandado o rayado se cambia por uno del mismo número.
  - cuando: Límpialo cada vez que limpies la taza.
  - fallas: mugre: La gasolina vieja o con agua lo tapa.; mal limpiado: Un alambre agranda el orificio y la mezcla queda rica.
  - sintomas: No tiene fuerza arriba y no pasa de cierta velocidad.; Se apaga al abrir el acelerador de golpe.
  - arrastra: tapado → sin fuerza al acelerar
  - conecta: 18, 19, 1 · efectos: 0
- **11 · Tornillos de la taza** · reutiliza · taller · Tornillos Taza Carburador · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los dos tornillos que sujetan la taza al cuerpo del carburador.
  - sirve: Aprietan la taza contra su empaque.
  - porque: Sanos se vuelven a usar con un destornillador justo y apriete parejo.
  - cuando: Revísalos cada vez que abras la taza.
  - fallas: apriete: Pasarse de fuerza barre la rosca del aluminio.; edad: La cabeza se daña con el destornillador equivocado.
  - sintomas: Gotea gasolina por la taza.
  - arrastra: flojos → la taza gotea gasolina
  - conecta: 5, 1 · efectos: 0
- **12 · Cortina** · repara · facil · Cortina Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El cilindro metálico que sube y baja dentro de la torre, colgado del cable del acelerador.
  - sirve: Abre y cierra el paso del aire: con ella dosificas la potencia. Lleva la aguja en el centro.
  - porque: Pegada se limpia; rayada o con juego se cambia.
  - cuando: Revísala si el acelerador no vuelve solo.
  - fallas: mugre: Barniz de gasolina vieja en la torre.; desgaste: Rayas por polvo que entra sin filtro.
  - sintomas: El acelerador se queda pegado o vuelve lento.; Ralentí alto que no baja.
  - arrastra: pegada → el acelerador no cierra: peligro al frenar
  - conecta: 16, 17, 18 · efectos: 0
- **13 · Imán del sensor** · cambia · taller · Imán Swiche Gato Lateral · 1 pieza · también en el kit ref. 22 (sensor completo, DD111046) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El imán pequeño que va con el sensor de posición del acelerador. El catálogo lo llama «imán swiche gato lateral».
  - sirve: Junto con el sensor y su cable, le dice al encendido qué tanto acelera la moto.
  - porque: Roto no se repara: se pide solo o con el sensor completo.
  - cuando: Revísalo si el testigo del motor prende (si tu versión lo trae) o la moto falla a media aceleración.
  - fallas: golpe: Se suelta o se rompe al desarmar.
  - sintomas: Testigo del motor prendido.; La moto falla a media aceleración.
  - arrastra: suelto → el encendido no sabe cuánto aceleras
  - conecta: 14, 15 · efectos: 0
- **14 · Cable del sensor** · repara · taller · Instalación Eléctrica Carburador · 1 pieza · también en el kit ref. 22 (sensor completo, DD111046) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El cable con sus conectores que sale del sensor del carburador.
  - sirve: Lleva la señal del sensor al encendido.
  - porque: Un conector sucio se limpia; un cable pelado se cambia.
  - cuando: Revísalo si el testigo del motor prende (si tu versión lo trae) o la moto falla al pasar baches.
  - fallas: vibración: El conector se suelta o se sulfata.; roce: El cable se pela contra el chasis.
  - sintomas: Testigo del motor prendido.; Falla al acelerar al pasar baches.
  - arrastra: conector sulfatado → la moto falla al acelerar
  - conecta: 13, 15 · efectos: 0
- **15 · Tornillo del imán** · reutiliza · taller · Tornillo · 1 pieza · también en el kit ref. 22 (sensor completo, DD111046) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tornillo pequeño que fija el imán del sensor.
  - sirve: Mantiene el imán en su sitio.
  - porque: Sano se vuelve a usar.
  - cuando: Revísalo cuando cambies el sensor.
  - fallas: vibración: Se afloja.
  - sintomas: El imán se mueve.
  - arrastra: flojo → se mueve el imán (13)
  - conecta: 13 · efectos: 0
- **16 · Tapa del carburador** · reutiliza · facil · Tapa Carburador · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La tapa roscada de la torre, con el codo por donde entra el cable del acelerador.
  - sirve: Cierra la torre y guía el cable hasta la cortina.
  - porque: Sana se vuelve a usar con su o-ring en buen estado.
  - cuando: Revísala cuando saques la cortina.
  - fallas: golpe: El codo se parte.; roscas: Se barre si la enroscas torcida.
  - sintomas: El acelerador se siente duro.; Entra agua a la torre al lavar la moto.
  - arrastra: rosca torcida → entra agua y mugre
  - conecta: 12, 17, 5 · efectos: 0
- **17 · Resorte de la cortina** · cambia · facil · Resorte Carburador · 1 pieza · también en el kit ref. 4 (kit del carburador, 36DU1206) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El resorte largo entre la tapa y la cortina.
  - sirve: Empuja la cortina abajo para que el acelerador cierre solo al soltarlo.
  - porque: Si el acelerador no vuelve solo, es un riesgo al frenar: se cambia.
  - cuando: Revísalo cuando saques la cortina.
  - fallas: edad: Se cansa y pierde fuerza.
  - sintomas: El acelerador no vuelve solo.; El ralentí queda alto.
  - arrastra: cansado → la cortina no cierra
  - conecta: 12, 16 · efectos: 0
- **18 · Aguja de la cortina** · cambia · facil · Aguja Cortina Carburador · 1 pieza · también en el kit ref. 4 (kit del carburador, 36DU1206) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La aguja cónica que cuelga de la cortina y entra en el difusor. Arriba tiene ranuras para su seguro.
  - sirve: Al subir con la cortina destapa más el difusor, encima del chiclé: así la gasolina crece con el aire a media aceleración.
  - porque: Doblada o gastada no se repara: va nueva, con el seguro en la misma ranura.
  - cuando: Revísala cuando saques la cortina.
  - fallas: desgaste: Se gasta por el roce con el difusor.; golpe: Se dobla al sacarla.
  - sintomas: La moto tironea a media aceleración.; Humo negro o consumo alto.
  - arrastra: gastada → mezcla rica a media aceleración
  - conecta: 12, 10 · efectos: 0
- **19 · Boquerel de baja** · repara · taller · Boquerel de Baja · 1 pieza · también en el kit ref. 4 (kit del carburador, 36DU1206) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El chiclé delgado de bronce, al lado del de alta.
  - sirve: Mide la gasolina del ralentí y del primer toque del acelerador.
  - porque: Se limpia con limpiador y aire; si no queda limpio, se cambia.
  - cuando: Límpialo cada vez que limpies la taza.
  - fallas: mugre: Es el orificio más fino: se tapa primero con gasolina vieja.
  - sintomas: La moto no queda prendida en ralentí.; Prende solo con el cebador.
  - arrastra: tapado → la moto se apaga en ralentí
  - conecta: 7, 10 · efectos: 0
- **20 · Aguja de corte de la flota** · cambia · taller · Aguja Flota Carburador · 1 pieza · también en el kit ref. 6 (flota y aguja, 36DU1205) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: La aguja pequeña con punta de caucho que cuelga de la flota: es la válvula que corta la entrada de gasolina.
  - sirve: Cuando la taza se llena, la flota la empuja contra su asiento y cierra el paso de gasolina.
  - porque: Marcada no sella: va nueva, mejor junto con la flota (vienen en el mismo kit).
  - cuando: Revísala cada vez que abras la taza.
  - fallas: desgaste: La punta se marca y deja de sellar.; mugre: Un grano de mugre la deja abierta.
  - sintomas: Gotea gasolina por el rebose.; La moto se ahoga y huele a gasolina.; Bujía negra.
  - arrastra: no sella → la taza rebosa y moja el motor
  - conecta: 21, 1 · efectos: 0
- **21 · Flota** · cambia · taller · Flota Carburador · 1 pieza · también en el kit ref. 6 (flota y aguja, 36DU1205) · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: Los dos flotadores de plástico unidos, dentro de la taza.
  - sirve: Suben con la gasolina y cierran la aguja de corte: guardan el nivel siempre igual.
  - porque: Una flota con gasolina adentro no se repara: va nueva con su aguja.
  - cuando: Revísala cada vez que abras la taza: sacúdela, no debe sonar líquido adentro.
  - fallas: golpe: El plástico se raja y le entra gasolina: pesa más y no sube.; desgaste: El pasador gasta su bisagra.
  - sintomas: La taza rebosa.; La moto se ahoga, la bujía sale negra y el consumo sube.
  - arrastra: rajada → no sube, la aguja no cierra y la taza rebosa
  - conecta: 20, 1 · efectos: 0

## Cómo funciona
1. 1 · Abres la llave. La gasolina baja del tanque y entra por la aguja de corte (20), abierta porque la flota (21) está abajo. La taza se va llenando.
2. 2 · Taza llena. La flota sube con la gasolina y empuja la aguja contra su asiento: cierra la entrada. Así el nivel queda siempre igual, como el flotador de un tanque de agua.
3. 3 · Ralentí. La cortina (12) está casi cerrada. El aire que pasa por debajo chupa gasolina por el boquerel de baja (19): poca, la justa para unas 1.300 rpm.
4. 4 · Aceleras. El cable sube la cortina y con ella la aguja (18). Entra más aire y la aguja, que es cónica, destapa más el chiclé (10): sale más gasolina en la misma proporción.
5. 5 · A fondo. La cortina queda arriba y la aguja casi afuera: ahora manda el tamaño del chiclé. El nivel baja un poco, la flota cae y la aguja de corte abre para reponer.
6. 6 · Aguja de corte gastada. Ya no sella: la gasolina sigue entrando con la taza llena, rebosa y moja el motor. Huele a gasolina, la bujía se ahoga y el consumo sube.

## Si falla
- **Agua en la gasolina**: Cuerpo del carburador: El agua pesa más que la gasolina y se va al fondo de la taza. → Boquerel de baja: Tapa primero el boquerel de baja, el más fino: el ralentí se cae. → Chiclé de alta: Si sigue, llega al chiclé de alta: la moto se apaga al acelerar.
- **Aguja de corte rayada**: Aguja de corte de la flota: La punta se marca con los años y deja de sellar. → Flota: Aunque la flota suba y empuje, la aguja rayada no sella: la taza rebosa. → Empaques de la taza y la tapa: Si además el empaque de la taza está duro, la gasolina gotea sobre el motor caliente: riesgo de incendio.
- **Aislador rajado**: Aislador del carburador: El caucho del aislador se raja con el calor del motor. → O-ring del aislador: Aunque el o-ring esté nuevo, el aire entra por la grieta del aislador sin pasar por el carburador. → Tornillo de la mezcla: La mezcla queda pobre: el ralentí sube y baja y ningún ajuste del tornillo lo arregla.

## Cuándo
- Filtro aire: Cada 15.000 km. · Owner's Manual Bajaj CT 100 / CT 110 BS VI, Bajaj Auto India, cuadro de mantenimiento; consultado el 14-nov-2026 Aproximado
- Bujía: Cada 30.000 km. · Owner's Manual Bajaj CT 100 / CT 110 BS VI, Bajaj Auto India, cuadro de mantenimiento, fila 8 'Spark plug clean & check gap' (CL,A a los 10.000 y 20.000 km; R a los 30.000); consultado el 14-nov-2026 Aproximado
- Limpiar la taza del carburador: En los mantenimientos de la tabla del manual («Carburettor float chamber cleaning»). En taller, también cuando la moto prenda mal o se apague. · Manual del propietario Bajaj CT 100 BS VI (India, otra versión), tabla de mantenimiento, p. 30. Los km de esa fila no se leen del texto. Aprox.
- Revisar el ralentí: Con el motor caliente: 1.300 ± 100 rpm. · Manual del propietario Bajaj CT 100 BS VI (India, otra versión), p. 5. Aprox.

## Fuentes y certezas
- Seguro: Números, nombres, cantidades y códigos de las 22 referencias: catálogo de partes Auteco Bajaj Boxer CT100, fig. 16 «Carburador (TEC-S1D)», columna TEC.
- Seguro: Kits del catálogo: ref. 4 (kit del carburador), ref. 5 (empaques), ref. 6 (flota y aguja) y ref. 22 (sensor completo).
- Aprox.: Vista de lado, con el paso del aire horizontal y la torre vertical: proporciones a ojo, sin lámina hermana. Qué piezas trae cada kit sale de las líneas del plano.
- Aprox.: Ralentí 1.300 rpm y la tabla de limpieza: manual del propietario de la CT 100 BS VI de India (otra versión, con cebador automático).
- Aprox.: Función del imán y el cable del sensor (13, 14): práctica de taller; el catálogo no la describe.

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `bajaj-ct100-bs6-manual-propietario.pdf` (48 págs.): págs. del PDF contando desde 1 (Read pages=N; en pymupdf, d[N-1]) 24 (impresa -, 2 piezas), 36 (impresa -, 1 piezas), 38 (impresa -, 2 piezas), 39 (impresa -, 2 piezas), 40 (impresa -, 1 piezas), 42 (impresa -, 1 piezas)
  claves buscadas: aguja, aislador, bajaj, boquerel, cable, carburador, chiclé, cortina, cuerpo, empaques, flota, resorte, sensor, tornillo, tornillos · para más: `buscar_manual.py boxer-ct100 "palabra,otra" --paginas N-M`

## Pendientes de la creadora
- Número del chiclé de alta y del boquerel de baja, vueltas del tornillo de la mezcla y nivel de la flota: sin manual de servicio de la Boxer CT100.
- Función exacta del imán 13 («imán swiche gato lateral» en el catálogo) y del cable 14: sin dato en el manual.
- El o-ring de la tapa (parte del kit 5) no se dibuja aparte: lo nombra la ficha 5. La taza va dibujada aparte (número 1, parte del carburador completo); el plano no le da número propio, y por eso el grupo «Cuerpo y taza» lista el 1 dos veces.
- El extractor de catálogo no reconoce la fig. 16 por el «(TEC-S1D)» del título; se agregó con un parser del scratchpad.
