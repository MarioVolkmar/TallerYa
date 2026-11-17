# Orden y seguridad del desarme por sistema

Reglas cortas para escribir los pasos sin hermana (paso 3, «Pasos del desarme»). Lo que tenga cifra (torque, altura, volumen) sale del manual o va «manual de servicio». `mas_controles.py` (`revisar_orden_sistema`) avisa cuando un paso hace algo antes de lo que debe ir primero (lista `ORDEN_SISTEMA`).

## Por tipo de moto (antes de las reglas del sistema)
- **Scooter** (NMAX, motor y basculante en una pieza): el gato central levanta la **trasera**; para la delantera, calza firme bajo el chasis o usa elevador. Carenajes: tornillos y clips en orden, sin forzar las pestañas. Batería bajo el asiento o el piso.
- **Cub o semiautomática** (Crypton): igual con el gato central (solo levanta la trasera). Cadena con cubrecadena cerrado: se abre antes de tocar el arrastre.
- **Calle sin gato central** (CB 125F, Boxer, NKD según versión): ninguna rueda queda en el aire sola; soporte o elevador bajo el chasis antes de soltar ejes.
- **Con CBS:** la palanca o el pedal frena las dos ruedas; ajusta y purga en el orden del manual. **Con ABS:** no abras la unidad ni sus tubos; purga según el manual (a veces con equipo).
- `mas_controles.py` (`revisar_gato`) avisa si un paso pone la rueda delantera en el aire con el gato central.

## Suspensión delantera (horquilla)
1. Moto firme con la rueda delantera en el aire; primero el cáliper (sin tocar la palanca), el eje y la rueda.
2. El tapón de la barra se **afloja con la barra aún apretada en la tijera de abajo**; después se sueltan los pernos de las tijeras.
3. Antes de sacar la barra, anota la **altura** de la barra sobre la tijera de arriba; al armar, la misma en las dos.
4. El tapón sale empujado por el resorte: sujétalo al soltar el último hilo.
5. El mismo aceite (tipo y nivel) en las dos barras; retén y guardapolvo nuevos si se abrió.
6. Pernos de las tijeras con su torque, alternando.

## Suspensión trasera (amortiguadores)
1. Moto apoyada bajo el chasis para que el basculante no caiga.
2. Con dos amortiguadores, uno a la vez: el otro sostiene el basculante.
3. El amortiguador no se abre ni se calienta (gas a presión); el resorte, solo con compresor.
4. Pernos de arriba y de abajo con su torque; revisa bujes y casquillos.
5. La misma precarga en los dos lados.

## Freno de disco
1. Con el cáliper o las pastillas fuera, **no se toca la palanca ni el pedal** (saca los pistones).
2. El líquido daña la pintura: trapo encima; no se mezcla DOT 5 con DOT 3/4.
3. Pastillas por pares; limpia los pistones antes de empujarlos.
4. Si se abrió el circuito, purgar; palanca firme antes de rodar.
5. Pernos del cáliper con su torque; disco sin grasa ni líquido.

## Freno de tambor
1. Afloja el ajuste (tuerca de la varilla o del cable) antes de sacar la rueda.
2. Marca la leva y su brazo (estrías) antes de separarlos; zapatas por pares.
3. El polvo de las zapatas no se sopla: trapo húmedo.
4. Al armar, poca grasa en la leva y nada en las bandas; ajusta el juego libre y prueba.

## Clutch
1. Afloja el cable (juego libre) y drena el aceite antes de abrir la tapa.
2. Tornillos de los resortes en cruz, poco a poco.
3. La tuerca de la manzana se suelta con la manzana trabada (herramienta de sujeción); arandela de seguridad nueva.
4. Discos de fricción remojados en aceite, en su orden y orientación.
5. Empaque de la tapa nuevo; aceite y juego libre del cable al final.

## Culata
1. Motor frío; PMS de compresión con las marcas alineadas **antes** de soltar la cadena.
2. Tensor aflojado o fuera antes del piñón del árbol de levas; amarra la cadena para que no caiga.
3. Tuercas de la culata en cruz, poco a poco (el orden inverso al apriete).
4. Empaques nuevos; torque en cruz y en pasos.
5. Al armar, marcas otra vez, dos vueltas a mano y holgura de válvulas.

## Transmisión final (cadena y piñones)
1. Motor apagado y en neutro: nunca la mano cerca del piñón con el motor prendido.
2. Afloja el eje trasero y los tensores antes de sacar la cadena; el clip del eslabón, con la abertura contra el sentido de giro.
3. Cadena, piñón y corona se cambian juntos.
4. Juego de la cadena del manual y las marcas de alineación iguales en los dos lados; eje con torque y chaveta nueva.

## Rueda
1. Moto firme con la rueda en el aire.
2. Primero el freno (cáliper, o cable/varilla del tambor) y la guaya del velocímetro; atrás, la cadena.
3. Anota de qué lado va cada separador antes de sacar el eje.
4. Eje con torque y chaveta nueva; prueba el freno antes de rodar.

## Carburación e inyección
1. Motor frío, sin chispas, ventilado y con trapo para la gasolina.
2. Inyección: alivia la presión (sin el fusible o el relé de la bomba, da arranque) antes de soltar mangueras.
3. Carburador: llave de gasolina cerrada y cuba drenada.
4. Anota las vueltas de los tornillos de mezcla antes de moverlos.
5. O-rings nuevos; revisa que no gotee antes de prender.

## Eléctrico
1. Primero el borne negativo de la batería; al armar, de último.
2. Se tira del conector, nunca del cable; marca los conectores parecidos.
3. Fusible del mismo amperaje.
4. Batería: ácido y gases, sin chispas cerca.
