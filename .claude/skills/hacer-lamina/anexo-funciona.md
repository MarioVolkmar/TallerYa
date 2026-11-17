# «Cómo funciona» por sistema (esqueleto de pasos y estados)

Para no inventar la animación desde cero: lee **solo** la sección de tu sistema. Cada paso dice qué cambia a la vista (estados en `funciona.pasos[].s`) y el indicador. Los nombres de estado son sugerencias; usa los de tu arte. Cifras: del manual o «aprox.». Cada paso, ≤ 250 caracteres. Corte o transparencia: el que se indica.

## Carburador (cortina y aguja)
Corte: cuerpo abierto de lado (venturi, cortina, aguja, surtidor, cuba con flota). Indicador: % de acelerador y nivel de la cuba.
1. **Cuba llena:** la flota sube y la aguja de corte cierra la entrada. `nivel:1, corte:cerrado, acel:0`
2. **Ralentí:** cortina casi cerrada; el chiclé de baja da el rocío por el boquerel. `acel:5, rocioBaja:1`
3. **Abres un poco:** sube la cortina y con ella la aguja; pasa más aire y más gasolina. `acel:30, aguja:sube`
4. **A fondo:** cortina arriba; manda el chiclé de alta. `acel:100, rocioAlta:1`
5. **La cuba baja y se llena:** baja la flota, abre la aguja de corte y entra gasolina. `nivel:.7→1, corte:abierto→cerrado`
6. (opcional) **Rebose:** si la aguja de corte no cierra, la gasolina sale por el rebose (la falla de «Si falla»).

## Inyección
Corte: cuerpo de aceleración con mariposa e inyector; bomba en el tanque. Indicadores: % de acelerador, presión aprox. y ms de inyección.
1. **Contacto:** la bomba da presión unos segundos. `bomba:1, presion:sube`
2. **Ralentí:** mariposa casi cerrada; el motor de ralentí deja pasar aire; pulsos cortos del inyector. `acel:0, pulso:corto`
3. **Aceleras:** se abre la mariposa; el sensor (TPS) lo lee; pulsos más largos. `acel:50, pulso:medio`
4. **A fondo:** mariposa abierta y pulsos largos. `acel:100, pulso:largo`
5. **Sueltas:** se cierra la mariposa y la ECU corta la inyección (freno motor). `acel:0, pulso:0`

## Freno de disco
Corte: bomba y cáliper con su pistón; manguera. Indicadores: % de manigueta y presión.
1. **Reposo:** pastillas casi tocando el disco (espacio exagerado). `lever:0, piston:0`
2. **Aprietas:** el pistón de la bomba empuja el líquido. `lever:.5, presion:sube`
3. **Frena:** el pistón del cáliper aprieta las pastillas contra el disco; el disco se calienta. `piston:1, calor:1`
4. **Sueltas:** el sello retrae el pistón; las pastillas se separan. `lever:0, piston:0`
5. **Desgaste:** las pastillas se gastan y el pistón sale más (sube el líquido de reserva).

## Freno de tambor
Corte: campana abierta con bandas, leva y resortes. Indicadores: % de pedal o manigueta y ángulo de la leva.
1. **Reposo:** los resortes mantienen las bandas cerradas. `leva:0`
2. **Pisas:** la varilla o el cable gira la leva. `pedal:.5, leva:15`
3. **Frena:** la leva abre las bandas contra la campana. `bandas:abiertas, calor:1`
4. **Sueltas:** los resortes cierran las bandas. `leva:0`
5. **Desgaste:** el indicador de desgaste se mueve hacia el límite.

## Clutch (multidisco en baño de aceite)
Corte: canasta, discos y resortes. Indicadores: % de manigueta y giro de canasta y manzana.
1. **Suelto (embragado):** los resortes aprietan los discos; canasta y manzana giran juntas. `palanca:0, giroManzana:1`
2. **Aprietas:** el cable y la varilla empujan el plato de presión. `palanca:.5`
3. **Desembragado:** los discos se separan; la canasta gira y la manzana no. `giroManzana:0`
4. **Sueltas de a poco:** los discos rozan y transmiten (punto de fricción). `giroManzana:.5`
5. **Embragado:** discos apretados; todo gira junto.

## Suspensión delantera (horquilla)
Corte: barra con resorte, pistón y aceite. Indicadores: mm de recorrido y velocidad del aceite.
1. **Reposo:** el resorte sostiene el peso (precarga). `recorrido:0`
2. **Bache:** la barra se comprime; el resorte se acorta. `recorrido:60`
3. **Amortigua:** el aceite pasa por los orificios del pistón y frena el movimiento. `aceite:fluye`
4. **Rebote:** el resorte extiende la barra y el aceite frena el regreso. `recorrido:0`
5. **Retén gastado:** sale aceite por la barra (la falla de «Si falla»).

## Suspensión trasera (tijera y amortiguadores)
Sin corte: vista de lado; la tijera gira sobre su eje (pivote) y el amortiguador une la tijera al chasis. Indicadores: mm de recorrido de la rueda y holgura de la cadena.
1. **Reposo:** el amortiguador sostiene la moto; la tijera, casi horizontal. `giro:0, amort:largo`
2. **Bache:** la rueda sube; la tijera gira sobre el pivote y el amortiguador se acorta. `giro:8, amort:corto`
3. **La cadena:** al subir la rueda, la cadena se tensa un poco (por eso lleva holgura). `holgura:baja`
4. **Rebote:** el resorte baja la rueda y el aceite del amortiguador frena el regreso. `giro:0`
5. **Bujes gastados:** la tijera tiene juego de lado y la rueda se desalinea (la falla de «Si falla»).

## Transmisión final (cadena, piñón y corona)
Sin corte: vista de lado con la rueda. Indicadores: rpm del piñón, de la rueda y juego de la cadena.
1. **En neutro:** el piñón no gira. `rpmPinon:0`
2. **Sales:** el piñón tira de la cadena por arriba; la corona y la rueda giran. `rpmPinon:1, tramo:tenso`
3. **Relación:** dientes de la corona entre los del piñón: la rueda gira más lento y con más fuerza.
4. **Cauchos de la campana:** suavizan el tirón al acelerar. `cauchos:comprimen`
5. **Cadena estirada:** juego de más; la cadena salta (la falla de «Si falla»).

## Culata y distribución
Corte: culata con levas, balancines y válvulas; cilindro con pistón. Indicadores: ángulo del cigüeñal y tiempo (admisión, compresión, explosión, escape).
1. **Admisión:** el pistón baja y la válvula de admisión abre. `cig:0-180, adm:abierta`
2. **Compresión:** las dos válvulas cerradas; el pistón sube (PMS de compresión: marcas alineadas). `cig:180-360`
3. **Explosión:** salta la chispa y empuja el pistón. `cig:360-540, chispa:1`
4. **Escape:** abre la válvula de escape; salen los gases. `cig:540-720, esc:abierta`
5. **La cadena de distribución:** el árbol de levas gira a la mitad que el cigüeñal; el tensor la mantiene tensa.

## Dirección (tija, pistas y rodamientos)
Corte: tubo de la dirección con pistas, balineras y tuerca de ajuste. Indicadores: ángulo del manubrio y juego.
1. **Recto:** la tija gira sobre las balineras dentro del tubo del chasis. `angulo:0`
2. **Giras:** las barras y la rueda giran con el manubrio. `angulo:30`
3. **Ajuste:** la tuerca de arriba precarga las pistas: sin juego y sin dureza.
4. **Juego:** con la pista marcada, el manubrio se «pega» en el centro o golpea al frenar (la falla de «Si falla»).

## Arranque eléctrico
Corte: motor de arranque, relé y piñón. Indicadores: voltios de la batería y rpm.
1. **Botón:** el relé conecta la batería al motor de arranque. `rele:1, volt:12→10`
2. **Gira:** el motor de arranque mueve el cigüeñal por su piñón y el embrague de arranque. `rpm:300`
3. **Arranca:** el motor prende; el embrague de arranque se suelta. `rpm:1300`
4. **Sueltas:** el relé corta. Batería baja: el relé «clica» y no gira (la falla de «Si falla»).

## Encendido (CDI o ECU, bobina y bujía)
Sin corte: esquema del circuito. Indicadores: rpm y momento de la chispa (grados antes del PMS).
1. **El volante gira:** el sensor (pulsador) avisa la posición del cigüeñal. `pulso:1`
2. **El CDI o la ECU** decide el momento y carga la bobina. `carga:1`
3. **Chispa:** la bobina sube el voltaje y salta la chispa en la bujía. `chispa:1`
4. **Más rpm:** la chispa se adelanta. `avance:sube`
5. **Bujía gastada o capuchón roto:** falla la chispa y el motor tironea.

## Escape
Sin corte o con corte del silenciador. Indicadores: °C del tubo y ruido.
1. **Sale el gas** por la válvula de escape al tubo (empaque en la culata). `gas:1`
2. **El tubo se calienta**: el protector evita quemaduras. `calor:1`
3. **El silenciador** frena el gas en cámaras y baja el ruido (catalizador si lo trae). `ruido:baja`
4. **Empaque roto o tubo picado:** petardeo y ruido (la falla de «Si falla»).

## Tanque y bomba de combustible
Corte: tanque con llave o bomba, filtro y manguera. Indicadores: nivel y presión (inyección).
1. **Carburador:** la gasolina baja por gravedad por la llave (con reserva). `llave:on`
2. **Inyección:** la bomba dentro del tanque da presión por el filtro. `bomba:1, presion:sube`
3. **Respiradero:** deja entrar aire al tanque a medida que baja el nivel. `nivel:baja`
4. **Filtro tapado o respiradero tapado:** la moto se apaga en subida o a fondo (la falla de «Si falla»).
