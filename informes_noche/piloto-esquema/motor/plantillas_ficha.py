"""Plantillas de ficha v2 por tipo de pieza (estilo v2 y regla de seguridad ya puestos). Llenan SOLO los campos vacíos.

Uso:
  python plantillas_ficha.py datos/<lamina>.json                 muestra qué tipo le toca a cada ficha vacía (por la descripción del catálogo)
  python plantillas_ficha.py datos/<lamina>.json --escribir      llena los campos vacíos con la plantilla de su tipo
  python plantillas_ficha.py datos/<lamina>.json --tipo 23=filtro,33=abrazadera --escribir   fuerza el tipo de algunas fichas
  python plantillas_ficha.py datos/<lamina>.json --hermana <lamina> --escribir   hermana con otra numeración: a cada ficha vacía le copia
      la de la hermana del mismo tipo (resorte, disco, arandela…) con el nombre nuevo; lo que falte, de la plantilla. Edítalas.

Las plantillas son un borrador correcto y prudente, no la ficha final: la creadora cambia «dónde va», el síntoma propio de
este sistema y los enlaces [[n|texto]] a las piezas vecinas. {pieza} = nombre de la ficha en minúscula; {donde} = «dónde va»
si la ficha ya trae «que» (si no, queda la frase genérica). Tipos: tornillos, tuerca, arandela, oring, empaque, sello, reten,
rodamiento, buje, resorte, seguro, grapa, abrazadera, caucho, manguera, tubo, filtro, tapa, caja, conjunto, pieza; por sistema
también aro-reten («RETEN CORONA/CLUTCH…»: aro de retención, no sello), bomba-freno, manigueta, interruptor-freno y cable-cbs.
Por sistema (ronda 8, mandan sobre el tipo): carburador (chicle-alta, chicle-baja, aguja-cortina, cortina, flota, aguja-corte, cuba,
tornillo-mezcla, tornillo-ralenti, ahogador, aislador), freno de tambor (bandas, leva-freno), rueda y transmisión (cadena, pinon, rin, llanta).
Modelo de estilo: las funciones por concepto de capturas-rediseno/armar26v2.py.
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "catalogo"))
from claves_es import clave_en
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

TORQUE = "Al armar, apriétalos en cruz y con el torque del manual de servicio: no a ojo."
NUEVO = "Cada vez que lo sueltes, va uno nuevo."

P = {
 "tornillos": dict(que="Los tornillos que sujetan {donde}.", sirve="Mantienen la pieza firme y en su sitio, con la presión justa.",
   sintomas=["Ves la pieza floja o con juego.", "Un tornillo tiene la cabeza redondeada o le falta."],
   fallas=[["maluso", "Si se aprietan de más, la rosca se estira o se barre; si quedan flojos, la pieza vibra y se suelta."], ["humedad", "El óxido los pega y la cabeza se daña al soltarlos."]],
   decision="reutiliza", porque="Si la rosca y la cabeza están sanas, se vuelven a poner. Si están barridos u oxidados, van nuevos. " + TORQUE,
   dif="facil", cuando="Revísalos cuando desarmes esta parte. " + TORQUE, arrastra=["Tornillo flojo → la pieza vibra y se daña la rosca de su base."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "tuerca": dict(que="La tuerca que sujeta {donde}.", sirve="Aprieta y deja fija la pieza sobre su eje o tornillo.",
   sintomas=["La pieza tiene juego.", "La tuerca está redondeada o golpeada."],
   fallas=[["maluso", "Apretada de más se estira la rosca; floja, se suelta con la vibración."]],
   decision="reutiliza", porque="Se reutiliza si la rosca está sana; si es autoblocante o está golpeada, va nueva. Al armar, va con el torque del manual de servicio.",
   dif="taller", cuando="Revísala cuando desarmes esta parte. Al armar, va con el torque del manual de servicio.", arrastra=["Tuerca floja → la pieza se suelta y golpea a las vecinas."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "arandela": dict(que="La arandela que va {donde}.", sirve="Reparte el apriete y protege la superficie de la pieza.",
   sintomas=["Está doblada, marcada o con el borde roto."], fallas=[["maluso", "Se deforma si el tornillo se aprieta de más."]],
   decision="reutiliza", porque="Se reutiliza si está plana y sana; si es de sello (cobre o aluminio), va nueva cada vez.",
   dif="facil", cuando="Mírala cuando sueltes su tornillo.", arrastra=["Arandela deformada → el tornillo pierde apriete."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "oring": dict(que="El anillo de caucho (O-ring) que sella {donde}.", sirve="Sella la unión para que no se escape líquido ni entre aire o polvo.",
   sintomas=["Hay humedad, gotas o mugre pegada en la unión.", "El motor aspira aire falso: ralentí inestable."],
   fallas=[["edad", "El caucho se endurece y se aplana con los años; deja de sellar."], ["calor", "El calor del motor lo reseca y lo agrieta."], ["maluso", "Se corta si se monta seco o torcido."]],
   decision="cambia", porque="El caucho no se repara. " + NUEVO + " Móntalo untado con el lubricante que indique el manual.",
   dif="taller", cuando="Cámbialo cada vez que desarmes esa unión.", arrastra=["O-ring vencido → fuga o entrada de aire en la unión."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "empaque": dict(que="El empaque que sella {donde}.", sirve="Llena la unión entre dos piezas para que no se escape nada ni entre aire.",
   sintomas=["Hay fuga o mugre húmeda en la unión.", "Ralentí inestable o silbido (aire falso), si es de admisión."],
   fallas=[["calor", "Con el calor se aplasta y pierde elasticidad."], ["edad", "Se reseca y se parte."]],
   decision="cambia", porque="Un empaque aplastado ya no sella. " + NUEVO,
   dif="taller", cuando="Cámbialo cada vez que separes esas dos piezas.", arrastra=["Empaque roto → entra aire o sale líquido por la unión."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "sello": dict(que="El sello de caucho que va {donde}.", sirve="Cierra la unión contra el polvo, el agua y el aire.",
   sintomas=["Está rajado, duro o fuera de su canal.", "Entra polvo o agua donde no debe."],
   fallas=[["edad", "El caucho se endurece y se raja con los años."], ["maluso", "Se tuerce o se corta al montarlo mal."]],
   decision="cambia", porque="El caucho no se repara: si está duro, rajado o deformado, va nuevo.",
   dif="facil", cuando="Míralo cada vez que abras esta parte y cámbialo si no está blando y entero.", arrastra=["Sello roto → entra polvo y desgasta lo de adentro."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "reten": dict(que="El retén que sella el eje {donde}.", sirve="Deja girar el eje sin que se escape el aceite ni entre mugre.",
   sintomas=["Hay aceite alrededor del eje.", "El labio del retén está duro o cortado."],
   fallas=[["desgaste", "El labio se gasta con el roce del eje."], ["edad", "El caucho se endurece y deja de abrazar el eje."]],
   decision="cambia", porque="Un retén que gotea no se repara. " + NUEVO + " Se monta con la herramienta adecuada, derecho.",
   dif="taller", cuando="Cámbialo si gotea o cada vez que saques el eje.", arrastra=["Retén con fuga → baja el aceite y se dañan rodamientos y piezas cercanas."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "rodamiento": dict(que="El rodamiento que sostiene el eje {donde}.", sirve="Deja girar el eje suave y centrado, con poco roce.",
   sintomas=["Zumbido o ronquido que sube con la velocidad.", "Juego o aspereza al girarlo con la mano."],
   fallas=[["desgaste", "Las bolas y las pistas se gastan con los kilómetros."], ["humedad", "El agua lo oxida y lo vuelve áspero."]],
   decision="cambia", porque="Un rodamiento áspero o con juego no se repara: va nuevo, montado a presión y derecho.",
   dif="taller", cuando="Gíralo con la mano cada vez que desarmes esta parte.", arrastra=["Rodamiento con juego → el eje se descentra y gasta sellos y piezas vecinas."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "buje": dict(que="El buje que va {donde}.", sirve="Guía y separa las piezas, y deja el apriete en la medida justa.",
   sintomas=["Juego o golpeteo en la unión.", "Está gastado de un lado o marcado."], fallas=[["desgaste", "El roce y la vibración lo van gastando."]],
   decision="reutiliza", porque="Se reutiliza si está liso y sin juego; si está gastado, va nuevo.",
   dif="taller", cuando="Míralo cada vez que desarmes esta parte.", arrastra=["Buje gastado → la pieza queda con juego y vibra."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "resorte": dict(que="El resorte que va {donde}.", sirve="Empuja la pieza a su posición y la regresa cuando sueltas.",
   sintomas=["La pieza no vuelve sola o vuelve despacio.", "El resorte está más corto, oxidado o roto."],
   fallas=[["edad", "Con los años pierde fuerza (se vence)."], ["humedad", "El óxido lo debilita y lo puede partir."]],
   decision="cambia", porque="Un resorte vencido no recupera su fuerza: va nuevo.",
   dif="taller", cuando="Revísalo cada vez que desarmes esta parte.", arrastra=["Resorte vencido → la pieza no regresa a su sitio."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "seguro": dict(que="El seguro (anillo elástico) que traba {donde}.", sirve="Impide que la pieza se salga de su eje o de su alojamiento.",
   sintomas=["Está abierto, torcido o fuera de su canal."], fallas=[["maluso", "Se abre de más al sacarlo y ya no aprieta."]],
   decision="cambia", porque=NUEVO.replace("lo sueltes", "lo saques") + " Un seguro abierto puede soltarse andando.",
   dif="taller", cuando="Cámbialo cada vez que lo saques.", arrastra=["Seguro flojo → la pieza se sale de su sitio."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "grapa": dict(que="La grapa que sujeta {donde}.", sirve="Mantiene la manguera o la pieza en su sitio para que no se suelte ni roce.",
   sintomas=["La manguera está suelta o se corrió.", "La grapa está floja, oxidada o rota."], fallas=[["edad", "Pierde tensión con el calor y los años."]],
   decision="cambia", porque="Si perdió tensión o está oxidada, va nueva: es barata y evita fugas.",
   dif="facil", cuando="Mírala cuando revises las mangueras de esta parte.", arrastra=["Grapa floja → la manguera se suelta o entra aire."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "abrazadera": dict(que="La abrazadera que aprieta {donde}.", sirve="Cierra la unión para que no entre aire ni polvo.",
   sintomas=["La unión está floja o se gira con la mano.", "Hay polvo dentro del ducto, después de la unión."],
   fallas=[["maluso", "Apretada de más corta el caucho; floja, deja pasar aire."], ["humedad", "El óxido la traba o la parte."]],
   decision="reutiliza", porque="Se reutiliza si el tornillo gira bien y no está oxidada. Al armar, apriétala parejo, sin cortar el caucho.",
   dif="facil", cuando="Revísala cada vez que cambies o limpies el filtro.", arrastra=["Abrazadera floja → entra aire sin filtrar y se gasta el motor."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "caucho-campana": dict(que="Los cauchos que van entre la campana de la rueda y el porta sprocket.", sirve="Reciben el tirón de la cadena y lo suavizan antes de que llegue a la rueda.",
   sintomas=["Golpe o juego al acelerar y soltar.", "El porta sprocket se mueve a mano dentro de la campana."], fallas=[["edad", "El caucho se endurece y se aplasta: queda juego."], ["maluso", "Los arranques bruscos los rajan."]],
   decision="cambia", porque="El caucho no se repara: si hay juego o están rajados, el juego completo va nuevo.",
   dif="medio", cuando="Míralos cada vez que cambies el kit de arrastre o saques la rueda.", arrastra=["Cauchos vencidos → golpe en cada cambio de acelerador y desgaste de la cadena."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "caucho": dict(que="El caucho de montaje que va {donde}.", sirve="Sostiene la pieza y absorbe la vibración del motor.",
   sintomas=["La pieza vibra o suena.", "El caucho está rajado, duro o aplastado."], fallas=[["edad", "El caucho se endurece y se raja."], ["calor", "El calor lo reseca."]],
   decision="cambia", porque="El caucho no se repara: si está duro o rajado, va nuevo.",
   dif="facil", cuando="Míralo cada vez que desmontes la pieza.", arrastra=["Caucho vencido → la pieza vibra y se rajan sus soportes."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "manguera": dict(que="La manguera que va {donde}.", sirve="Lleva el aire, el líquido o los vapores de una pieza a otra sin fugas.",
   sintomas=["Está rajada, inflada, dura o doblada.", "Hay fuga o mugre húmeda en sus puntas."],
   fallas=[["edad", "El caucho se agrieta con los años."], ["calor", "El calor del motor la reseca."], ["maluso", "Se dobla o se pellizca si se monta mal."]],
   decision="cambia", porque="Una manguera rajada no se repara con cinta: va nueva, con sus grapas en buen estado.",
   dif="facil", cuando="Revísala en cada servicio: sin grietas y bien asentada en sus puntas.", arrastra=["Manguera rajada → fuga o aire falso en el sistema."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "filtro": dict(que="El filtro que va {donde}.", sirve="Atrapa el polvo y la mugre antes de que lleguen al motor.",
   sintomas=["La moto pierde fuerza y gasta más.", "El filtro se ve negro, aceitoso o roto."],
   fallas=[["desgaste", "Se tapa con el polvo: entra menos aire."], ["humedad", "Mojado se deforma y deja pasar mugre."]],
   decision="cambia", porque="El filtro de papel no se lava ni se sopla con aire a presión: se cambia por uno nuevo.",
   dif="facil", cuando="Cámbialo con el intervalo del manual, y antes si andas mucho en polvo o destapado.", arrastra=["Filtro tapado o roto → menos fuerza, más consumo y desgaste del motor."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ok")),
 "tapa": dict(que="La tapa que cierra {donde}.", sirve="Cierra la caja y protege lo de adentro del agua y el polvo.",
   sintomas=["Está rajada o no cierra parejo.", "Faltan tornillos o tienen la rosca dañada."], fallas=[["golpe", "Se raja en una caída."], ["maluso", "Los tornillos apretados de más rompen la rosca del plástico."]],
   decision="cambia", porque="Si está rajada, va nueva; no se pega. Sus tornillos se aprietan suave, sin barrer la rosca.",
   dif="facil", cuando="Ábrela solo para revisar o cambiar lo de adentro, y ciérrala pareja.", arrastra=["Tapa rajada → entra agua y polvo."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "caja": dict(que="La caja {donde}.", sirve="Aloja y protege las piezas de adentro, y las mantiene en su sitio.",
   sintomas=["Está rajada o tiene un soporte roto.", "Las piezas de adentro se mueven o les entra mugre."], fallas=[["golpe", "Se raja en una caída."], ["edad", "El plástico se vuelve frágil con el sol y el calor."]],
   decision="cambia", porque="Si está rajada o le falta un soporte, va nueva.",
   dif="taller", cuando="Mírala cuando abras esta parte.", arrastra=["Caja rajada → entra mugre a lo de adentro."],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
 "conjunto": dict(que="El conjunto {donde}.", sirve="(Escribe para qué sirve este conjunto en una o dos frases.)",
   sintomas=["(Señales propias de este conjunto.)"], fallas=[["desgaste", "(Por qué se daña.)"]],
   decision="repara", porque="(Qué se cambia por separado y cuándo va el conjunto completo.)", dif="taller", cuando="(Cuándo revisarlo.)", arrastra=[],
   certezaDe=dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")),
}
P["pieza"] = P["conjunto"]
# ---------- ronda 8: plantillas por SISTEMA (carburador, freno de tambor, rueda y transmisión final) ----------
# Mandan sobre las de tipo cuando la descripción nombra la pieza del sistema (en inglés o en español). Son borrador: el número de
# chiclé, las vueltas y el nivel salen del manual de servicio; si no hay, «manual de servicio» y a «pendientes».
AP = dict(sirve="ap", sintomas="ap", fallas="ap", porque="ap", cuando="ap")
GAS = " Trabaja con el motor frío, ventilado y sin chispas cerca; al armar, revisa que nada gotee."
P.update({
 "chicle-alta": dict(que="El chiclé de alta: un tornillito de bronce con un agujero calibrado, en el fondo del carburador.", sirve="Deja pasar la gasolina justa cuando aceleras a fondo.",
   sintomas=["La moto se ahoga o pierde fuerza a fondo.", "Petardea o se calienta en carretera."], fallas=[["mugre", "La mugre de la gasolina tapa el agujero y la mezcla queda pobre."], ["maluso", "Limpiarlo con alambre agranda el agujero y la mezcla queda rica."]],
   decision="reutiliza", porque="Se limpia con limpiador y aire, nunca con alambre. Si el agujero está agrandado o la rosca dañada, va uno nuevo del mismo número." + GAS,
   dif="medio", cuando="Míralo cuando limpies el carburador o si la moto falla a fondo.", arrastra=["Chiclé tapado → mezcla pobre → el motor se calienta y pierde fuerza."], certezaDe=AP),
 "chicle-baja": dict(que="El chiclé de baja: el chiclé pequeño que alimenta el ralentí y el primer tramo del acelerador.", sirve="Da la gasolina del ralentí y de la salida desde parado.",
   sintomas=["La moto no sostiene el ralentí o se apaga al soltar el acelerador.", "Le cuesta arrancar en frío."], fallas=[["mugre", "Su agujero es muy fino: la gasolina vieja lo tapa primero que a todos."]],
   decision="reutiliza", porque="Se limpia con limpiador y aire, sin alambre; si no queda limpio o la rosca está dañada, va uno nuevo del mismo número." + GAS,
   dif="medio", cuando="Míralo si el ralentí falla o la moto estuvo parada mucho tiempo con gasolina.", arrastra=["Chiclé de baja tapado → la moto se apaga en el semáforo."], certezaDe=AP),
 "aguja-cortina": dict(que="La aguja que cuelga de la cortina y entra en el surtidor.", sirve="Con la cortina sube y deja pasar más gasolina a medio acelerador.",
   sintomas=["La moto tironea o falla a medio acelerador.", "Gasta más gasolina de lo normal."], fallas=[["desgaste", "El roce la gasta y la mezcla se enriquece."], ["maluso", "Si se dobla, la cortina se traba."]],
   decision="cambia", porque="Si está rayada, gastada o doblada va nueva (mejor con su surtidor). Su posición (ranura del clip) es la del manual de servicio.",
   dif="medio", cuando="Revísala al limpiar el carburador.", arrastra=["Aguja gastada → mezcla rica a medio acelerador → bujía negra y más consumo."], certezaDe=AP),
 "cortina": dict(que="La cortina (pistón del acelerador) que sube y baja dentro del cuerpo del carburador.", sirve="Abre el paso del aire cuando aceleras; con ella sube la aguja.",
   sintomas=["El acelerador se queda pegado o no vuelve solo.", "Ralentí que sube y baja."], fallas=[["desgaste", "El roce la raya y entra aire por los lados."], ["mugre", "La mugre la frena en su guía."]],
   decision="reutiliza", porque="Se limpia y se reutiliza si sube y baja suave y sin rayas; si está rayada o tiene juego, va nueva. Al armar, el acelerador debe volver solo.",
   dif="medio", cuando="Revísala si el acelerador no vuelve solo o al limpiar el carburador.", arrastra=["Cortina que se pega → el acelerador no regresa: peligro al frenar."], certezaDe=AP),
 "flota": dict(que="La flota (flotador): la pieza hueca que flota sobre la gasolina en la cuba.", sirve="Al subir con la gasolina, empuja la aguja de corte y cierra la entrada cuando la cuba está llena.",
   sintomas=["El carburador rebosa o gotea gasolina.", "La moto se ahoga."], fallas=[["desgaste", "Si se pica o se llena de gasolina, ya no flota."], ["maluso", "Doblar su lengüeta cambia el nivel."]],
   decision="cambia", porque="Si tiene gasolina adentro o está deformada, va nueva. El nivel se ajusta con el valor del manual de servicio." + GAS,
   dif="medio", cuando="Revísala si el carburador rebosa o al limpiarlo.", arrastra=["Flota pesada → cuba rebosada → gasolina al motor o al piso."], certezaDe=AP),
 "aguja-corte": dict(que="La aguja de corte (punzón) que abre y cierra la entrada de gasolina a la cuba.", sirve="La flota la empuja contra su asiento cuando la cuba está llena.",
   sintomas=["Gotea gasolina por el rebose con la moto quieta.", "Se ahoga después de estar parada."], fallas=[["desgaste", "La punta de caucho se marca y ya no cierra."], ["mugre", "Una basura entre la punta y el asiento la deja abierta."]],
   decision="cambia", porque="Si la punta está marcada o dura, va nueva (mejor con su asiento)." + GAS,
   dif="medio", cuando="Revísala si el carburador rebosa.", arrastra=["Aguja de corte que no cierra → rebose → gasolina en el aceite del motor."], certezaDe=AP),
 "cuba": dict(que="La cuba (taza): el depósito de abajo del carburador donde espera la gasolina.", sirve="Guarda la gasolina al nivel justo para los chiclés.",
   sintomas=["Gotea por el empaque.", "Tiene mugre o agua en el fondo."], fallas=[["mugre", "El fondo junta mugre y agua de la gasolina."], ["maluso", "Apretarla de más deforma su empaque."]],
   decision="reutiliza", porque="Se limpia y se reutiliza; su empaque va nuevo si está duro o aplastado." + GAS,
   dif="facil", cuando="Drénala si la moto estuvo parada; límpiala con el carburador.", arrastra=["Agua en la cuba → la moto se apaga y no arranca."], certezaDe=AP),
 "tornillo-mezcla": dict(que="El tornillo de mezcla (de aire): regula la mezcla del ralentí.", sirve="Afina cuánta mezcla entra en ralentí.",
   sintomas=["Ralentí inestable.", "La moto petardea al soltar el acelerador."], fallas=[["maluso", "Cerrarlo con fuerza daña su punta y su asiento."]],
   decision="reutiliza", porque="Antes de sacarlo, ciérralo suave contando las vueltas y vuelve a dejarlo igual (o como dice el manual de servicio). Si la punta está marcada, va nuevo con su o-ring.",
   dif="medio", cuando="Solo si el ralentí falla, después de limpiar el carburador.", arrastra=["Mezcla mal ajustada → ralentí inestable y más consumo."], certezaDe=AP),
 "tornillo-ralenti": dict(que="El tornillo de ralentí: empuja la cortina para que el motor no se apague en mínima.", sirve="Fija las revoluciones del ralentí.",
   sintomas=["El motor se apaga en mínima.", "El ralentí queda muy alto."], fallas=[["maluso", "Subirlo para tapar otra falla (chiclé tapado) esconde el problema."]],
   decision="reutiliza", porque="Se ajusta con el motor caliente a las rpm del manual; si la rosca o el resorte fallan, va nuevo.",
   dif="facil", cuando="Ajústalo después de limpiar o si el ralentí cambió.", arrastra=["Ralentí muy bajo → se apaga al frenar."], certezaDe=AP),
 "ahogador": dict(que="El ahogador (cebador) para el arranque en frío.", sirve="Enriquece la mezcla mientras el motor está frío.",
   sintomas=["Le cuesta arrancar en frío.", "Gasta mucho o se ahoga si queda puesto."], fallas=[["desgaste", "El émbolo o el cable se traban y queda abierto o cerrado."]],
   decision="reutiliza", porque="Se limpia y se reutiliza si se mueve libre; si se traba o el cable está deshilachado, va nuevo.",
   dif="facil", cuando="Revísalo si la moto no arranca en frío.", arrastra=["Ahogador pegado → mezcla rica → bujía negra."], certezaDe=AP),
 "aislador": dict(que="El aislador (múltiple de caucho) entre el carburador y el motor.", sirve="Une el carburador al motor sin dejar entrar aire y le quita calor y vibración.",
   sintomas=["Ralentí alto o que sube solo.", "Silbido cerca del carburador."], fallas=[["calor", "El calor lo endurece y se raja: entra aire falso."]],
   decision="cambia", porque="El caucho no se repara: si está duro o rajado, va nuevo con su o-ring." + GAS,
   dif="medio", cuando="Revísalo cuando saques el carburador o si hay aire falso.", arrastra=["Aislador rajado → aire falso → mezcla pobre y motor caliente."], certezaDe=AP),
 "bandas": dict(que="Las bandas (zapatas) del freno de tambor.", sirve="Se abren contra la campana y frenan la rueda.",
   sintomas=["Hay que pisar más para frenar.", "Chillan o rozan."], fallas=[["desgaste", "El forro se gasta; el indicador llega al límite."], ["humedad", "El aceite o la grasa en el forro le quitan agarre."]],
   decision="cambia", porque="Van por par y nuevas si el indicador llegó al límite o tienen grasa. El polvo no se sopla: trapo húmedo. Al armar, ajusta el juego libre y prueba antes de rodar.",
   dif="medio", cuando="Mira el indicador de desgaste en cada mantenimiento.", arrastra=["Bandas gastadas → el metal raya la campana."], certezaDe=AP),
 "leva-freno": dict(que="La leva del freno de tambor y su eje.", sirve="Al girar con la varilla o el cable, abre las bandas.",
   sintomas=["El freno queda pegado o vuelve lento.", "El pedal tiene juego de más."], fallas=[["humedad", "Sin grasa se oxida y se pega."], ["desgaste", "Se gasta y abre menos las bandas."]],
   decision="reutiliza", porque="Se limpia y lleva poca grasa en el eje, nada en las bandas. Marca leva y brazo (estrías) antes de separarlos.",
   dif="medio", cuando="Engrásala cuando cambies las bandas.", arrastra=["Leva pegada → la rueda frena sola y se calienta."], certezaDe=AP),
 "cadena": dict(que="La cadena de transmisión entre el piñón y la corona.", sirve="Lleva la fuerza del motor a la rueda trasera.",
   sintomas=["Suena o salta.", "Tiene eslabones tiesos o mucho juego."], fallas=[["desgaste", "Se estira con los kilómetros."], ["humedad", "Sin lubricar se oxida y se gasta rápido."]],
   decision="cambia", porque="Va con piñón y corona (el kit completo). Motor apagado y en neutro: nunca la mano cerca del piñón. El juego libre es el del manual.",
   dif="medio", cuando="Limpia, lubrica y revisa el juego en cada mantenimiento.", arrastra=["Cadena estirada → dientes del piñón y la corona gastados."], certezaDe=AP),
 "pinon": dict(que="El piñón o la corona: rueda dentada de la transmisión final.", sirve="Engrana con la cadena para mover la rueda.",
   sintomas=["Dientes en punta o en gancho.", "La cadena salta."], fallas=[["desgaste", "Los dientes se gastan con la cadena."]],
   decision="cambia", porque="Va con la cadena y el otro piñón: uno gastado acaba con los nuevos. Tornillos o tuerca con el torque del manual.",
   dif="medio", cuando="Míralo cada vez que revises la cadena.", arrastra=["Dientes en gancho → la cadena salta y se gasta."], certezaDe=AP),
 "rin": dict(que="El rin de la rueda.", sirve="Sostiene la llanta y lleva la fuerza al piso.",
   sintomas=["La rueda bambolea al girar.", "Radios flojos o el rin golpeado."], fallas=[["golpe", "Un hueco lo dobla."], ["desgaste", "Los radios se aflojan."]],
   decision="repara", porque="Un rin de radios se centra y se tensan los radios en taller; si está rajado, va nuevo.",
   dif="taller", cuando="Míralo al revisar la llanta o después de un golpe.", arrastra=["Rin doblado → vibra y se gastan balineras y llanta."], certezaDe=AP),
 "llanta": dict(que="La llanta (neumático).", sirve="Da el agarre al piso y amortigua.",
   sintomas=["Labrado gastado.", "Pierde aire o tiene rajas."], fallas=[["desgaste", "El labrado se gasta."], ["edad", "El caucho se reseca con los años."]],
   decision="cambia", porque="Va nueva si llegó al testigo de desgaste o está rajada. La presión es la del manual.",
   dif="taller", cuando="Revisa presión y labrado cada semana.", arrastra=["Llanta lisa → frena largo y patina en mojado."], certezaDe=AP),

 # ronda 10: «retén» en catálogos en español también es un aro de retención (clutch, caja: adentro todo va en aceite)
 "aro-reten": dict(que="El aro de acero que mantiene la pieza en su sitio {donde} (posición aprox.).", sirve="Retiene y ubica la pieza sobre el eje para que no se corra.",
   sintomas=["La pieza tiene juego o se corre en el eje.", "Ruido de golpeteo al soltar la palanca."],
   fallas=[["desgaste", "Se gasta o se deforma y deja juego."], ["maluso", "Se dobla si se saca haciendo palanca."]],
   decision="cambia", porque="Es barato: si está gastado, marcado o deformado, va nuevo.",
   dif="taller", cuando="Revísalo cada vez que desarmes esta parte.", arrastra=["Aro gastado → la pieza cabecea y se gastan los dientes y el buje."], certezaDe=AP),
 # ronda 10 (NKD freno): mandos del freno hidráulico y del CBS
 "bomba-freno": dict(que="La bomba de freno {donde}: el cilindro con su depósito de líquido.", sirve="Convierte el apretón de la manigueta en presión de líquido hacia el cáliper.",
   sintomas=["Manigueta esponjosa o que llega al puño.", "Líquido oscuro o fuga por el guardapolvo."],
   fallas=[["humedad", "El líquido absorbe agua, se oscurece y oxida el cilindro."], ["desgaste", "Las copas del pistón se gastan y la presión se escapa."]],
   decision="repara", porque="Con fuga o manigueta esponjosa después de purgar, va el kit de la bomba; si el cilindro está rayado, bomba nueva. Seguridad: sin freno firme no se sale.",
   dif="taller", cuando="Revisa el nivel del líquido antes de rodar y cámbialo cuando lo pida el manual.", arrastra=["Bomba con fuga → entra aire y la moto frena largo."], certezaDe=AP),
 "manigueta": dict(que="La manigueta (palanca) {donde}.", sirve="Es lo que aprietas con la mano: mueve el pistón o el cable.",
   sintomas=["Juego de lado o que no vuelve sola.", "Doblada o partida después de una caída."],
   fallas=[["golpe", "Se dobla o se parte en una caída."], ["desgaste", "El pivote se gasta y queda con juego."]],
   decision="cambia", porque="Doblada o partida va nueva: enderezarla la debilita. Con juego, se cambia el tornillo del pivote y se engrasa.",
   dif="facil", cuando="Revísala si se cae la moto y engrasa el pivote en cada mantenimiento.", arrastra=["Manigueta doblada → el recorrido cambia y el freno no responde igual."], certezaDe=AP),
 "interruptor-freno": dict(que="El interruptor de la luz de freno {donde}.", sirve="Prende la luz de freno cuando aprietas el freno.",
   sintomas=["La luz de freno no prende o se queda prendida."], fallas=[["humedad", "El agua oxida los contactos."], ["desgaste", "El botón se pega o se rompe."]],
   decision="cambia", porque="No se repara: si no prende con la bombilla buena, va nuevo. Sin luz de freno, los de atrás no te ven frenar.",
   dif="facil", cuando="Prueba la luz de freno antes de rodar.", arrastra=["Interruptor dañado → la luz de freno no avisa al de atrás."], certezaDe=AP),
 "cable-cbs": dict(que="El cable del freno combinado (CBS) {donde}.", sirve="Al pisar el freno de atrás, tira también del delantero para repartir la frenada.",
   sintomas=["El freno delantero no reacciona al pisar el de atrás.", "El cable está duro, pelado o con óxido."],
   fallas=[["humedad", "Se oxida por dentro y se pone duro."], ["ajuste", "Se destiempla y deja de repartir la frenada."]],
   decision="cambia", porque="Un cable duro o pelado va nuevo; el ajuste es el del manual. Seguridad: prueba los dos frenos antes de rodar.",
   dif="taller", cuando="Revisa su juego y lubrícalo en cada mantenimiento.", arrastra=["Cable duro → el freno delantero queda pegado o no ayuda."], certezaDe=AP),
})
SISTEMA = [  # (expresión sobre «DESCRIPCIÓN EN MAYÚSCULAS SIN TILDES | clave en inglés», plantilla); gana la primera
    (r"^RETEN\s+(CORONA|CAMPANA|CLUTCH|EMBRAGUE|BUJE|PI[NÑ]ON PRIMARIO)", "aro-reten"),
    (r"MASTER CYLINDER|CYLINDER, MASTER|BOMBA (DE )?FRENO", "bomba-freno"), (r"(^|\| )\.*\s*(BRAKE LEVER|LEVER, (FRONT |REAR )?(BRAKE|CLUTCH)|MANIGUETA)", "manigueta"),
    (r"STOP SWITCH|SWITCH, (FRONT |REAR )?STOP|(INTERRUPTOR|SWICHE) (DE )?(STOP|FRENO)", "interruptor-freno"), (r"\bCBS\b|EQUALIZER|IGUALADOR", "cable-cbs"),
    (r"MAIN JET|JET, MAIN|CHICLE (DE )?ALTA|CHICLE PRINCIPAL", "chicle-alta"), (r"PILOT JET|SLOW JET|JET, (PILOT|SLOW)|CHICLE (DE )?BAJA|CHICLE (DE )?RALENTI|BOQUEREL", "chicle-baja"),
    (r"NEEDLE, JET|JET NEEDLE|AGUJA (DE (LA )?)?CORTINA|AGUJA (DEL )?ACELER", "aguja-cortina"), (r"NEEDLE VALVE|VALVE, NEEDLE|VALVE SET, NEEDLE|AGUJA (DE )?(CORTE|FLOTA|FLOTADOR)|PUNZON", "aguja-corte"),
    (r"(^|\| )\.*\s*(THROTTLE VALVE|VALVE, THROTTLE|PISTON VALVE|CORTINA)", "cortina"), (r"(^|\| )\.*\s*(FLOAT|FLOTA|FLOTADOR)\b(?!.*(CHAMBER|BOWL))", "flota"),
    (r"FLOAT CHAMBER|CHAMBER, FLOAT|FLOAT BOWL|(^|\| )\.*\s*(TAZA|CUBA)\b", "cuba"), (r"SCREW, (PILOT )?AIR|PILOT (AIR )?SCREW|TORNILLO (DE (LA )?)?(MEZCLA|AIRE)", "tornillo-mezcla"),
    (r"THROTTLE STOP|IDLE (ADJUST|SCREW)|TORNILLO (DE(L)? )?(RALENTI|MINIMA|MINIMO)", "tornillo-ralenti"), (r"STARTER|CHOKE|AHOGADOR|CEBADOR", "ahogador"),
    (r"INSULATOR|AISLADOR|INSULADOR", "aislador"), (r"BRAKE SHOE|SHOE, BRAKE|SHOE COMP|(^|\| )\.*\s*(JGO |JUEGO DE )?(BANDAS|ZAPATAS)\b", "bandas"),
    (r"CAMSHAFT, BRAKE|BRAKE CAM|LEVA (DE(L)? )?(FRENO|PORTABANDAS)|ABREBANDAS", "leva-freno"),
    (r"DRIVE CHAIN|CHAIN, DRIVE|CADENA DE TRANSMISION|KIT ARRAST", "cadena"), (r"(^|\| )\.*\s*(SPROCKET|CORONA|PI[NÑ]ON)\b|SPROCKET, (DRIVE|DRIVEN)", "pinon"),
    (r"(^|\| )\.*\s*(RIM|RIN|CAST WHEEL)\b", "rin"), (r"(^|\| )\.*\s*(TIRE|TYRE|LLANTA)\b", "llanta")]

TIPOS = [(r"ELEMENT|FILTER", "filtro"), (r"HOSE CLAMP", "abrazadera"), (r"CIRCLIP", "seguro"), (r"OIL SEAL", "reten"), (r"O-RING", "oring"),
         (r"GASKET", "empaque"), (r"SEAL", "sello"), (r"BEARING", "rodamiento"), (r"BOLT|SCREW", "tornillos"), (r"NUT", "tuerca"),
         (r"WASHER", "arandela"), (r"COLLAR|BUSH", "buje"), (r"SPRING", "resorte"), (r"CLIP", "grapa"), (r"DAMPER, HUB", "caucho-campana"), (r"GROMMET|DAMPER", "caucho"),
         (r"HOSE|PIPE", "manguera"), (r"CAP|COVER", "tapa"), (r"CASE", "caja"), (r"ASSY|COMP", "conjunto")]


def tipo_de(cat, desc_en=None):
    """Tipo por la descripción del catálogo; en español (o con descripcion_en) se pasa antes por catalogo/claves_es.py."""
    d = clave_en(cat.split(" · ")[0], desc_en)
    import unicodedata
    u = "".join(c for c in unicodedata.normalize("NFD", cat.split(" · ")[0].upper()) if unicodedata.category(c) != "Mn") + " | " + d
    sis = next((t for ex, t in SISTEMA if re.search(ex, u)), None)   # ronda 8: la pieza del sistema manda sobre el tipo
    return sis or next((t for ex, t in TIPOS if re.search(ex, d)), "pieza")


def descripciones_en(D):
    """{ref: descripcion_en} del catálogo de la lámina, si lo tiene."""
    ruta = pathlib.Path(__file__).resolve().parent / "catalogo" / f"{D.get('catalogo', '')}.json"
    if not D.get("catalogo") or not ruta.exists(): return {}
    fig = json.loads(ruta.read_text(encoding="utf-8")).get("figuras", {}).get(str(D.get("figura")), {})
    return {p["ref"]: p["descripcion_en"] for p in fig.get("partes", []) if p.get("descripcion_en")}


def lugar_de(D, k):
    """«la culata», «el cilindro»… según el grupo v2 de la pieza; «esta parte» si no hay grupo."""
    for g in D.get("v2", {}).get("grupos", []):
        ids = g.get("piezas", []) + [x for t in g.get("torn", []) for x in t.get("ids", [])]
        if k in ids or any(re.fullmatch(re.escape(k) + r"[a-z]", i) for i in ids):
            n = re.sub(r"\s+\d+$", "", g["nombre"]); w = n.split()[0].lower()
            if w.endswith("s"): art = "las" if w[-2:] in ("as",) else "los"
            else: art = "la" if (w.endswith("a") or w.endswith("ía") or w.endswith("ión") or w in ("culata", "bujía")) else "el"
            return f"{art} {n[0].lower() + n[1:]}"
    return "esta parte"


def con_lugar(txt, lugar):
    """{donde} → «la culata» tras un verbo que la toma de objeto (sujeta, sella, aprieta, cierra, traba); «de la culata» tras caja o
    conjunto; «en la culata» en el resto («va en la culata»)."""
    txt = re.sub(r"\b(sujetan?|sella|aprieta|cierra|traba) \{donde\}", lambda m: f"{m.group(1)} {lugar}", txt)
    txt = re.sub(r"\b(caja|conjunto) \{donde\}", lambda m: f"{m.group(1)} de {lugar}", txt).replace(" de el ", " del ")
    return txt.replace("{donde}", f"en {lugar}").replace("desarmes esta parte", f"desarmes {lugar}" if lugar != "esta parte" else "desarmes esta parte").replace("abras esta parte", f"abras {lugar}" if lugar != "esta parte" else "abras esta parte")


def llenar(F, tipo, lugar="esta parte"):
    """Llena los campos vacíos de F con la plantilla; devuelve los campos que llenó."""
    pl = P[tipo]; donde = F.get("que") and re.sub(r"\.$", "", F["que"][0].lower() + F["que"][1:])
    hechos = []
    for c, v in pl.items():
        if F.get(c): continue
        if c == "certezaDe":
            F[c] = {**v, **F.get(c, {})}
        elif isinstance(v, str): F[c] = (v.format(donde=donde, pieza=F.get("nombre", "").lower()) if donde else con_lugar(v, lugar).replace("{pieza}", F.get("nombre", "").lower()))
        else: F[c] = json.loads(json.dumps(v))
        hechos.append(c)
    if "certezaDe" in F: F["certezaDe"] = {**P[tipo]["certezaDe"], **F["certezaDe"]}
    return hechos


CAMPOS_HERMANA = ("que", "sirve", "porque", "cuando", "fallas", "sintomas", "arrastra", "decision", "dif", "certezaDe")
VACIAS = {"de", "del", "la", "el", "los", "las", "y", "en", "con", "para"}


def palabras_de(t):
    return {re.sub(r"(es|s)$", "", w) for w in re.findall(r"[a-záéíóúñ]+", (t or "").lower()) if w not in VACIAS and len(w) > 2}


def desde_hermana(D, H, k, F, t, EN, ENH):
    """Ronda 3: la ficha de la hermana con el mismo tipo (claves_es) y más palabras del nombre en común, copiada a los campos vacíos
    con el nombre nuevo; los enlaces [[n|…]] de la hermana quedan como texto (su numeración es otra). Devuelve la ref usada o None."""
    GEN = {"CLUTCH", "COMP", "ASSY", "SUB", "NO", "FR", "RR", "SET", "KIT", "TYPE"}
    en = lambda cat, d: {w for w in re.findall(r"[A-Z]{3,}", clave_en((cat or "").split(" · ")[0], d).upper()) if w not in GEN}
    mio = en(F.get("cat"), EN.get(k))
    mejor, puntos = None, 0
    for kh, FH in H.get("fichas", {}).items():
        if FH.get("ctx") or tipo_de(FH.get("cat", ""), ENH.get(kh)) != t: continue
        p = 2 * len(mio & en(FH.get("cat"), ENH.get(kh))) + len(palabras_de(F.get("nombre")) & palabras_de(FH.get("nombre")) - {"clutch"})
        if t not in ("pieza", "conjunto"): p += 1   # tipo concreto (resorte, arandela…): ya es parecida aunque el nombre cambie
        if p > puntos: mejor, puntos = kh, p
    if t in ("pieza", "conjunto") and puntos < 2: return None   # genérica sin palabras en común: mejor la plantilla
    if not mejor: return None
    FH = H["fichas"][mejor]; viejo, nuevo = (FH.get("nombre") or "").lower(), (F.get("nombre") or "").lower()
    def pasar(v):
        if isinstance(v, str):
            v = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", v)
            return re.sub(re.escape(viejo), nuevo, v, flags=re.I) if viejo and nuevo else v
        if isinstance(v, list): return [pasar(x) for x in v]
        if isinstance(v, dict): return {a: pasar(b) for a, b in v.items()}
        return v
    for c in CAMPOS_HERMANA:
        if not F.get(c) and FH.get(c): F[c] = pasar(json.loads(json.dumps(FH[c])))
    return mejor


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    ruta = pathlib.Path(a[0]); D = json.loads(ruta.read_text(encoding="utf-8"))
    forz = dict(x.split("=") for x in (a[a.index("--tipo") + 1].split(",") if "--tipo" in a else []))
    escribir = "--escribir" in a
    EN = descripciones_en(D)
    H = json.loads((ruta.parent / f"{a[a.index('--hermana') + 1]}.json").read_text(encoding="utf-8")) if "--hermana" in a else None
    ENH = descripciones_en(H) if H else {}
    for k, F in D["fichas"].items():
        if F.get("ctx"): continue
        t = forz.get(k) or tipo_de(F.get("cat", ""), EN.get(k))
        if H:
            G = json.loads(json.dumps(F)); de = desde_hermana(D, H, k, G, t, EN, ENH)
            if de:
                if escribir: D["fichas"][k] = F = G
                print(f"  {k:5} {F.get('nombre', '')[:30]:30} ← ficha {de} de la hermana ({H['fichas'][de].get('nombre', '')[:28]}): edítala")
        vac = [c for c in P[t] if not F.get(c)]
        if not vac: continue
        if escribir: llenar(F, t, lugar_de(D, k))
        print(f"  {k:5} {F.get('nombre', '')[:30]:30} → {t:11} {'llenó' if escribir else 'llenaría'}: {', '.join(vac)}")
    if escribir:
        ruta.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8"); print("escrito", ruta.name)


if __name__ == "__main__":
    main()
