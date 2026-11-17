# Revisión rápida · cb125f-culata

Culata · Honda CB 125F · catálogo honda-cb125f fig. E1-2 · página `motor/cb125f-culata.html` · hermana `nmax-fig1` (lo heredado sin cambio ya se revisó allá y va resumido)

Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md`. Hallazgos: máximo 12, graves primero, en el formato de `aplicar_hallazgos.py`.

## Lo que ya midió la máquina (no lo repitas)
- Validador: 0 errores, 4 avisos.
  - aviso: armado transparente: 7·7 y 18·18 muy juntos (6.1 px de radio); solo se ven al tocar la pieza
  - aviso: regresión: «torque» aparecía 15 vez(es) antes de la corrección y ahora 9; revisa que no se perdiera un aviso o un paso
  - aviso: regresión: «en cruz» aparecía 13 vez(es) antes de la corrección y ahora 4; revisa que no se perdiera un aviso o un paso
  - aviso: regresión: «manual de servicio» aparecía 15 vez(es) antes de la corrección y ahora 9; revisa que no se perdiera un aviso o un paso
- Medición: Bloqueantes: Cómo funciona: un paso tiene 266 caracteres (pedir ≤ 250) · Medible NO APRUEBA · Notas estimadas (criterios medibles): 6: 3.5 · 8: 4.7 · 9: 5.0 · 10: 5.0 · 11: 4.8 · 12: 4.8  → promedio 4.63

## Catálogo (ref · nombre en la lámina · cantidad · código)
- 1 Caucho de las aletas ×2 · 2 Culata ×1 · 3 Guía de la válvula de escape ×1 · 4 Guía de la válvula de admisión ×1 · 5 Portalevas ×1 · 6 Placa de tope del árbol de levas ×1 · 7 Seguro de la guía ×2 · 8 Empaque de la culata ×1 · 9 Tubo de admisión ×1 · 10 Abrazadera del tubo de admisión ×1 · 11 Bujía ×1 · 12 Tornillo del portalevas ×2 · 13 Espárrago del escape ×2 · 14 Tornillo del tubo de admisión ×2 · 15 Tuerca de la culata ×4 · 16 Arandela de la tuerca de la culata ×4 · 17 Pasador guía de la culata ×2 · 18 Pasador guía del portalevas ×2 · 19 O-ring del tubo de admisión ×1 · 20 Tornillo de la placa de tope ×1 · 21 Tornillo largo de la culata ×2

## Grupos
- **Bujía**: Bujía
- **Tubo de admisión**: Tubo de admisión, O-ring del tubo de admisión, Abrazadera del tubo de admisión
- **Portalevas**: Portalevas, Placa de tope del árbol de levas, Pasador guía del portalevas
- **Culata**: Culata, Empaque de la culata, Pasador guía de la culata, Caucho de las aletas, Guía de la válvula de escape, Guía de la válvula de admisión, Seguro de la guía

## Desarme
1. Bujía. Con el motor frío, quita el capuchón y saca la bujía (11) con la llave de bujías. Al armar: NGK CPR6EA-9 · 0,8–0,9 mm · nueva: ½ vuelta, afloja y ⅛ de vuelta.
2. Escape y admisión. Quita el tubo de escape (otra figura). Afloja la abrazadera (10) del carburador, quita los dos tornillos y saca el tubo (9). El o-ring (19) va nuevo al armar.
3. Tuercas de la culata. Sin la tapa y con el pistón arriba en compresión (PMS) y las marcas alineadas, afloja en cruz y en frío las cuatro tuercas; quita los dos tornillos y la placa de tope. Al armar: torque del manual de servicio.
4. Portalevas. Afloja el tensor de la cadena y suelta el piñón del árbol de levas (otra figura); amarra la cadena con un alambre. Levanta el portalevas (5) derecho con el árbol y los balancines.
5. Culata. Quita los dos tornillos largos (21) y sube la culata (2) derecha, sin hacer palanca en las aletas; saca los cauchos (1). Tapa la boca del cilindro. El empaque (8) va nuevo siempre; guarda los pasadores.
6. Guías de válvula. Solo en el taller: antes salen las válvulas con el compresor (otra figura); las guías se sacan a presión con la culata caliente, van unas de medida mayor y se rectifican los asientos. Luego, holgura en frío.

## Fichas (solo lo propio; aprox. = sin fuente)
- **1 · Caucho de las aletas** · cambia · RUBBER, INSERT · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Bloquecitos de caucho que van metidos entre las aletas de la culata (2).
  - sirve: Frenan la vibración de las aletas para que no zumben ni se rajen.
  - porque: Son baratos: si faltan o están duros, van nuevos.
  - cuando: Míralos cuando laves el motor.
  - fallas: edad: Se endurecen, se encogen y se caen.
  - sintomas: Zumbido metálico del motor a ciertas rpm.
  - arrastra: Caucho caído → la aleta vibra → zumbido.
- **2 · Culata** · repara · HEAD COMP., CYLINDER · 1 pieza · aprox.: sirve, sintomas, fallas, porque
  - que: El bloque de aluminio con aletas que cierra el cilindro: abajo forma la cámara donde se quema la mezcla y arriba guarda las válvulas y el portalevas (5).
  - sirve: Deja entrar la mezcla, saca los gases, sostiene la bujía (11) y pasa el calor al aire por sus aletas.
  - porque: Una cara torcida se rectifica y una rosca de bujía dañada lleva inserto; si está rajada o le falta una aleta grande, va nueva. Abrirla es trabajo de taller: con el pistón en el PMS de compresión y las marcas alineadas.
  - cuando: Holgura de válvulas a los 1.000 km y después cada 4.000 km, en frío y en el taller.
  - fallas: calor: Si el motor se recalienta, se tuerce y deja de sellar contra el empaque (8).; maluso: Una bujía apretada de más o torcida le daña la rosca.; desgaste: Las guías (3) y los asientos de válvula se gastan con los km.
  - sintomas: Pierde fuerza y le cuesta prender en caliente.; Aceite por la unión con el cilindro.; Golpeteo de válvulas o humo azul al acelerar.
  - arrastra: Recalentamiento → culata torcida → el empaque (8) deja de sellar → pierde compresión.
- **3 · Guía de la válvula de escape** · cambia · GUIDE, VALVE(OS) · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tubito metido a presión en la culata (2) por donde corre el vástago de la válvula de escape. De repuesto viene una de medida mayor, para reparar.
  - sirve: Mantiene la válvula centrada sobre su asiento para que cierre parejo.
  - porque: Se cambia en el taller con prensa y la culata caliente, por una de medida mayor, y después se escarían y se rectifican los asientos. Con ella va el seguro (7).
  - cuando: Revísala cuando la culata se abra por gasto de aceite o compresión baja.
  - fallas: desgaste: Con los km la guía se ovala y la válvula baila.; calor: Un recalentamiento la afloja en la culata.
  - sintomas: Humo azul al soltar el acelerador (admisión) o al arrancar (escape).; Gasta aceite sin fugas por fuera.
  - arrastra: Guía gastada → la válvula baila → gasta aceite y no sella.
- **4 · Guía de la válvula de admisión** · cambia · GUIDE, IN. VALVE(OS) · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando
  - que: El tubito metido a presión en la culata (2) por donde corre el vástago de la válvula de admisión. De repuesto viene una de medida mayor, para reparar.
  - sirve: Mantiene la válvula centrada sobre su asiento para que cierre parejo.
  - porque: Se cambia en el taller con prensa y la culata caliente, por una de medida mayor, y después se escarían y se rectifican los asientos. Con ella va el seguro (7).
  - cuando: Revísala cuando la culata se abra por gasto de aceite o compresión baja.
  - fallas: desgaste: Con los km la guía se ovala y la válvula baila.; calor: Un recalentamiento la afloja en la culata.
  - sintomas: Humo azul al soltar el acelerador (admisión) o al arrancar (escape).; Gasta aceite sin fugas por fuera.
  - arrastra: Guía gastada → la válvula baila → gasta aceite y no sella.
- **5 · Portalevas** · cambia · HOLDER COMP., CAMSHAFT · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: El soporte de aluminio que va encima de la culata: sostiene el árbol de levas y los ejes de los balancines.
  - sirve: Mantiene las levas alineadas con las válvulas; sus tuercas aprietan también la culata contra el cilindro.
  - porque: Si los apoyos del árbol de levas están rayados, va completo con sus balancines. Al armar, las tuercas (15) van en cruz, en frío y con el torque del manual de servicio.
  - cuando: Míralo cuando ajusten la holgura de válvulas (cada 4.000 km) o cambien la cadena de distribución.
  - fallas: desgaste: Sin aceite limpio se rayan los apoyos del árbol de levas.; maluso: Apretar las tuercas sin orden lo tuerce.
  - sintomas: Tic-tac fuerte arriba del motor.; Aceite por la tapa de la culata.
  - arrastra: Aceite viejo → apoyos rayados → ruido y desgaste del árbol de levas.
- **6 · Placa de tope del árbol de levas** · reutiliza · PLATE, STOPPER · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: La placa pequeña atornillada al portalevas (5) que tranca el árbol de levas.
  - sirve: No deja que el árbol de levas se corra de lado.
  - porque: Se reutiliza si está plana y sin desgaste; su tornillo (20) va con el torque del manual de servicio.
  - cuando: Revísala cuando se saque el portalevas.
  - fallas: maluso: Si se olvida al armar, el árbol se corre y roza.
  - sintomas: Ruido de golpe arriba del motor.
  - arrastra: Placa olvidada → árbol de levas suelto → roce y ruido.
- **7 · Seguro de la guía** · cambia · CLIP, VALVE GUIDE · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: El aro elástico que va en la ranura de cada guía de válvula, por encima de la culata.
  - sirve: Hace de tope: no deja que la guía se hunda en la culata.
  - porque: Va nuevo cada vez que se cambia una guía (3).
  - cuando: Solo cuando se cambian las guías.
  - fallas: calor: Pierde tensión con los recalentamientos.; maluso: Se pierde o se pone mal al cambiar la guía.
  - sintomas: Golpeteo de válvulas que no se quita al ajustar la holgura.
  - arrastra: Seguro flojo → la guía se corre → la válvula no cierra bien.
- **8 · Empaque de la culata** · cambia · GASKET, CYLINDER HEAD · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: La lámina metálica que sella entre la culata (2) y el cilindro.
  - sirve: Mantiene la compresión adentro y el aceite en su paso.
  - porque: Va nueva cada vez que se abre la culata, sin silicona. Con las guías (17) en su lugar y las tuercas (15) en cruz, en frío.
  - cuando: Cámbiala siempre que se levante la culata.
  - fallas: calor: Un recalentamiento la quema.; edad: Una vez apretada ya no sella igual.
  - sintomas: Pierde fuerza.; Aceite por la unión de la culata y el cilindro.
  - arrastra: Empaque quemado → pierde compresión → no tiene fuerza.
- **9 · Tubo de admisión** · cambia · PIPE COMP., INLET · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: El codo de caucho con brida que une el carburador con la culata (2).
  - sirve: Lleva la mezcla al puerto de admisión sin dejar entrar aire de afuera.
  - porque: Si tiene grietas o está duro, va nuevo con su o-ring (19). Pruébalo en mínimo: rocía limpiador de carburador en la unión, lejos de chispas; si el mínimo cambia, entra aire.
  - cuando: Míralo cada vez que limpies el filtro de aire o revises el carburador.
  - fallas: edad: El caucho se endurece y se raja con el calor.; maluso: Apretar de más la abrazadera (10) lo corta.
  - sintomas: Mínimo acelerado o que sube y baja.; Petardea y se calienta más.
  - arrastra: Tubo rajado → entra aire → motor pobre y caliente.
- **10 · Abrazadera del tubo de admisión** · reutiliza · BAND, INSULATOR · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: La abrazadera de banda con tornillo que aprieta la boca del tubo de admisión (9) sobre el carburador.
  - sirve: Sella esa unión para que no entre aire por ahí.
  - porque: Se reutiliza si el tornillo gira bien; apriétala hasta que el caucho quede firme, sin cortarlo.
  - cuando: Revísala cuando limpies el filtro de aire.
  - fallas: maluso: Apretada de más corta el caucho; floja, deja entrar aire.; edad: El tornillo se oxida y se barre.
  - sintomas: Mínimo inestable.; El carburador se mueve con la mano.
  - arrastra: Abrazadera floja → entra aire → mínimo inestable.
- **11 · Bujía** · cambia · PLUG, SPARK(CPR7EA-9)(NGK) · 1 pieza · aprox.: sirve, sintomas, fallas
  - que: La pieza que salta la chispa dentro de la cámara de la culata (2).
  - sirve: Enciende la mezcla en el momento justo.
  - porque: Se limpia y se calibra a los 4.000 km y va nueva a los 8.000 km. Estándar NGK CPR6EA-9; para andar mucho rato rápido, CPR7EA-9. Apriétala con el motor frío.
  - cuando: Revisar a los 4.000 km y cambiar cada 8.000 km.
  - fallas: desgaste: Los electrodos se gastan y la separación pasa de 0,9 mm.; calor: Una mezcla pobre la deja blanca; una rica, negra de hollín.
  - sintomas: Prende mal en frío.; Tironea al acelerar.; Gasta más gasolina.
  - arrastra: Bujía gastada → chispa débil → tironea y gasta más.
- **12 · Tornillo del portalevas** · reutiliza · BOLT, FLANGE, 5X14 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Uno de los dos tornillos pequeños con brida que van encima del portalevas (5).
  - sirve: Ayuda a fijar el portalevas sobre la culata.
  - porque: Se reutiliza si la rosca está sana; si está barrido, va uno nuevo. Al armar, los dos parejo, con el torque del manual de servicio y a mano, sin pistola.
  - cuando: Se suelta con el portalevas.
  - fallas: maluso: Es delgado: apretado de más se parte o barre la rosca de la culata.
  - sintomas: Aceite alrededor de la cabeza del tornillo.
  - arrastra: Tornillo barrido → rosca dañada en la culata → inserto.
- **13 · Espárrago del escape** · reutiliza · BOLT, STUD, 8X22 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: La varilla roscada fija en la culata (2) donde se atornilla el tubo de escape.
  - sirve: Sostiene el escape contra el puerto de salida, con su empaque.
  - porque: Se queda en la culata; si se parte, se saca con extractor y va uno nuevo. Ponle antiadherente a la rosca y aprieta las tuercas del escape con el torque del manual de servicio.
  - cuando: Revísalo cuando cambies el empaque del escape.
  - fallas: calor: El calor y el agua lo oxidan y la tuerca se pega.; maluso: Forzar la tuerca pegada lo parte.
  - sintomas: Ruido de escape (tos) junto al motor.; Hollín alrededor del puerto.
  - arrastra: Espárrago partido → el escape queda flojo → fuga de gases.
- **14 · Tornillo del tubo de admisión** · reutiliza · BOLT, FLANGE SOCKET, 6X22 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Uno de los dos tornillos allen que sujetan la brida del tubo de admisión (9) a la culata.
  - sirve: Aprietan el tubo contra la culata sobre su o-ring (19).
  - porque: Se reutiliza si la cabeza y la rosca están sanas; si está barrido, va uno nuevo. Los dos se aprietan parejo. Torque: manual de servicio.
  - cuando: Se sueltan con el tubo de admisión.
  - fallas: maluso: Apretado de más se barre la rosca en el aluminio.
  - sintomas: Mínimo inestable o acelerado.
  - arrastra: Tornillo flojo → el o-ring no sella → entra aire.
- **15 · Tuerca de la culata** · reutiliza · NUT, CYLINDER HEAD · 4 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Una de las cuatro tuercas altas que van encima del portalevas (5), en los espárragos que salen del cilindro.
  - sirve: Aprietan a la vez el portalevas y la culata (2) contra el cilindro.
  - porque: Se reutilizan si la rosca está sana; si están barridas, van nuevas. Al armar: en cruz, en dos o tres vueltas, en frío y con el torque del manual de servicio.
  - cuando: Se sueltan cuando se abre la culata.
  - fallas: maluso: Apretarlas sin orden o en caliente tuerce la culata.
  - sintomas: Aceite o compresión que se escapa por la unión de la culata.
  - arrastra: Tuercas sin orden → culata torcida → el empaque no sella.
- **16 · Arandela de la tuerca de la culata** · reutiliza · WASHER, PLAIN, 12MM · 4 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: La arandela plana que va debajo de cada tuerca de la culata (15).
  - sirve: Reparte el apriete para que la tuerca no marque el aluminio del portalevas.
  - porque: Se reutiliza si está plana; si está marcada o hundida, va nueva. Cada una vuelve debajo de su tuerca.
  - cuando: Se sueltan con las tuercas de la culata.
  - fallas: maluso: Si se olvida, la tuerca se hunde y el apriete queda corto.
  - sintomas: Arandela marcada o hundida.
  - arrastra: Arandela olvidada → apriete corto → el empaque no sella.
- **17 · Pasador guía de la culata** · reutiliza · DOWEL PIN, 10X12 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Uno de los dos bujes huecos que van entre el cilindro y la culata (2).
  - sirve: Centran la culata sobre el cilindro para que el empaque (8) asiente parejo.
  - porque: Se reutilizan si están rectos y sin óxido; no se arma sin ellos.
  - cuando: Se sacan con la culata.
  - fallas: maluso: Se pierden o se quedan pegados en la culata al desarmar.
  - sintomas: La culata no baja derecha al armar.
  - arrastra: Pasador perdido → culata corrida → el empaque se quema.
- **18 · Pasador guía del portalevas** · reutiliza · DOWEL PIN, 6X10 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Uno de los dos bujes huecos que van entre la culata y el portalevas (5).
  - sirve: Alinean el portalevas para que el árbol de levas gire derecho.
  - porque: Se reutilizan si están rectos; no se arma sin ellos.
  - cuando: Se sacan con el portalevas.
  - fallas: maluso: Se pierden al levantar el portalevas.
  - sintomas: Árbol de levas duro o con ruido después de armar.
  - arrastra: Pasador perdido → portalevas corrido → el árbol de levas roza.
- **19 · O-ring del tubo de admisión** · cambia · O-RING, 33.5X3 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: El anillo de caucho que sella entre la brida del tubo de admisión (9) y la culata.
  - sirve: No deja entrar aire de afuera a la mezcla.
  - porque: Va nuevo cada vez que se saca el tubo de admisión: es barato y no vuelve a sellar igual.
  - cuando: Cámbialo siempre que se suelte el tubo de admisión.
  - fallas: edad: Se endurece y se aplana con el calor.
  - sintomas: Mínimo acelerado o que sube y baja.
  - arrastra: O-ring duro → entra aire → motor pobre y caliente.
- **20 · Tornillo de la placa de tope** · reutiliza · BOLT, FLANGE, 6X14 · 1 pieza · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: El tornillo pequeño con brida que fija la placa de tope (6) al portalevas.
  - sirve: Mantiene la placa en su sitio.
  - porque: Se reutiliza si la rosca está sana; si está barrido, va uno nuevo. Al armar, con traba de rosca suave y el torque del manual de servicio.
  - cuando: Se suelta con el portalevas.
  - fallas: maluso: Si se afloja, la placa se suelta adentro del motor.
  - sintomas: La placa se mueve.
  - arrastra: Tornillo suelto → placa suelta → el árbol de levas se corre.
- **21 · Tornillo largo de la culata** · reutiliza · BOLT, FLANGE, 6X105 · 2 piezas · aprox.: sirve, sintomas, fallas, porque, cuando, que
  - que: Uno de los dos tornillos largos de 105 mm que unen la culata con el cilindro por el lado de la cadena.
  - sirve: Aprietan ese lado de la culata (2), donde no llegan las tuercas.
  - porque: Se reutilizan si están rectos; doblados o barridos, van nuevos. Se aflojan antes de subir la culata y se aprietan después de las tuercas, con el torque del manual de servicio.
  - cuando: Se sueltan cuando se abre la culata.
  - fallas: maluso: Si se olvida aflojarlos, al subir la culata se rompen las aletas.
  - sintomas: Aceite por el costado de la cadena.
  - arrastra: Tornillo olvidado → aleta rota al levantar la culata.

## Cómo funciona
1. 1 · Admisión (0–180°, ideal). El pistón baja. La leva empuja el balancín del portalevas (5) y este abre la válvula de admisión: el pistón chupa aire con gasolina al cilindro.
2. (heredado)
3. 3 · Chispa. Un poco antes de que el pistón llegue arriba, la bujía (11) salta la chispa entre sus electrodos y la mezcla se enciende. Al armar: NGK CPR6EA-9 · 0,8–0,9 mm.
4. (heredado)
5. 5 · Escape (540–720°, ideal). La leva, con su balancín, abre la válvula de escape y el pistón, al subir, saca los gases quemados. Un instante quedan las dos abiertas (el cruce). En 720° el cigüeñal dio dos vueltas y la leva una.
6. 6 · Enfriamiento por aire. Las aletas de la culata (2) y del cilindro pasan el calor al aire que llega al andar; los cauchos (1) evitan que zumben. Con la moto quieta y prendida mucho rato, se recalienta.

## Si falla
- **Bujía vieja**: Bujía: Los electrodos se gastan y la separación pasa de 0,9 mm. → Culata: La mezcla mal quemada deja hollín en la cámara: tironea y cascabelea. → Empaque de la culata: Con el cascabeleo sube la presión y el calor, y el empaque se puede quemar.
- **Recalentamiento**: Caucho de las aletas: Faltan los cauchos o las aletas están tapadas de barro: se enfría peor. → Culata: La culata se recalienta y se tuerce. → Empaque de la culata: El empaque deja de sellar: pierde compresión y sale aceite.
- **Tubo de admisión rajado**: Tubo de admisión: El caucho del tubo se raja con el calor y los años. → Bujía: Entra aire sin gasolina: la mezcla pobre quema más caliente y la bujía queda blanca. → Culata: La culata trabaja más caliente y las válvulas sufren.

## Cuándo
- Holgura de las válvulas: A los 1.000 km y después cada 4.000 km, en frío y en el taller. · Manual del propietario Honda CB125F Twister (español), copia entregada por el usuario, cuadro de mantenimiento (pág. 35-36 del manual; columnas 1.000 / 4.000 … 24.000 km, anual y sustitución normal; círculo gris = revisar, figura oscura = cambiar), fila 'Holgura de las válvulas' (revisar a los 1.000 km y en cada columna desde los 4.000); consultado el 14-nov-2026 Seguro
- Bujía: Revisar a los 4.000 km y cambiar cada 8.000 km (NGK CPR6EA-9 · 0,8–0,9 mm). · Manual del propietario Honda CB125F Twister (español), copia entregada por el usuario, cuadro de mantenimiento (pág. 35-36 del manual; columnas 1.000 / 4.000 … 24.000 km, anual y sustitución normal; círculo gris = revisar, figura oscura = cambiar), fila 'Bujía' (revisar a los 4.000, 12.000 y 20.000 km; cambiar a los 8.000, 16.000 y 24.000); consultado el 14-nov-2026 Seguro

## Fuentes y certezas
- Seguro: Números, nombres, cantidades y códigos: catálogo de partes Honda CB 125F (GLH125SH), fig. E-1-2 «Cylinder head», columna GLH125SH.
- Seguro: Bujía NGK CPR6EA-9 (CPR7EA-9 para alta velocidad), 0,8–0,9 mm y apriete en vueltas; holgura de válvulas a los 1.000 km y cada 4.000 km; bujía revisar 4.000 y cambiar 8.000 km (manual del propietario CB125F, especificaciones, apriete de la bujía y cuadro de mantenimiento).
- Aprox.: Dibujo simplificado de tres cuartos, como el plano; las piezas comunes se ven de frente.
- Aprox.: Función de la placa de tope, de los tornillos pequeños y de los cauchos; fallas, síntomas y decisiones: práctica de taller.
- Aprox.: Torques de la culata y el portalevas: sin dato (manual de servicio, que no está en la carpeta).

## Páginas del manual que aplican (para la mecánica: lee solo estas)
- `manual-cb125f.pdf` (122 págs.): págs. del PDF 95 (impresa ?, 4 piezas), 96 (impresa ?, 2 piezas), 101 (impresa ?, 2 piezas), 106 (impresa ?, 2 piezas), 117 (impresa 109, 3 piezas), 118 (impresa ?, 3 piezas)
- `manual-usuario-cb125f.pdf` (123 págs.): págs. del PDF 94 (impresa ?, 3 piezas), 96 (impresa 87, 2 piezas), 100 (impresa ?, 2 piezas), 105 (impresa 96, 2 piezas), 116 (impresa 107, 3 piezas), 117 (impresa 108, 3 piezas)
  claves buscadas: abrazadera, admisión, arandela, bujía, caucho, culata, empaque, espárrago, pasador, placa, portalevas, seguro, tornillo, tuerca, válvula

## Pendientes de la creadora
- Torques de tuercas de culata, portalevas y tubo de admisión: no están en el manual del propietario; falta el manual de servicio.
- Extractor Honda: no lee figuras de tres niveles (E-1-2) ni tablas sin guiones; se extrajo con un parser propio (ver informe).
- La tapa de la culata (E-1-1) y el árbol de levas con las válvulas (E-2-1) van en otras figuras: láminas aparte.
- Revisión cortada (10 min, meta 3): las fichas de plantilla de tornillería y pasadores salieron con relleno y hubo que escribirlas a mano; quedan sin pulir los menores de UX.
- Criterio 6 en 3,5: el toque del o-ring (19) mide 21 px a 360 aunque está en toqueExtra; el botón «Bujía» (32×22) es del motor.
- Catálogo: la bujía principal es CPR7EA-9 y la CPR8EA-9 va entre paréntesis; el manual del propietario dice CPR6EA-9 estándar. Se usa la del manual.
