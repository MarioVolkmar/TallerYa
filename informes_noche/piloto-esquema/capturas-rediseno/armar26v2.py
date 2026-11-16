# RETIRADO (adopción v2): la v2 ya es datos/nmax-fig26.json y se edita directo (ladoTxt y certezaDe se agregaron a mano). No volver a correr: pisaría esos cambios.
# Arma datos/nmax-fig26.json desde nmax-fig26.json: grupos, tornillería agrupada, lados y fichas con la guía de estilo nueva.
# Enlaces en la prosa: [[clave|texto]]; clave simbólica (b, kit, man…) se resuelve por lado.
import json, re, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/dev/TallerYa/informes_noche/piloto-esquema/motor/"
D = json.load(open(M + "datos/nmax-fig26-v1.json", encoding="utf8"))
CAT = {p["ref"]: p for p in json.load(open(M + "catalogo/nmax-bbe4.json", encoding="utf8"))["figuras"]["26"]["partes"]}
V1 = copy.deepcopy(D["fichas"])

LADOS = {
 "del": dict(L="delantera", Lm="delantero", mano="derecha", off=0, mabs="15", mcal="18", uabs="16", aabs="17", ucal="19", acal="20", otro="tra"),
 "tra": dict(L="trasera", Lm="trasero", mano="izquierda", off=20, mabs="34", mcal="38", uabs="35", aabs="36", ucal="39", acal="40", otro="del"),
}
BASE = dict(b=1, kit=2, tapa=3, placa=4, diaf=5, ttapa=6, man=7, pman=8, tuer=9, abr=10, pabr=11, int=12, tint=13)

def clave(k, S):
    if k in BASE: return str(BASE[k] + S["off"])
    if k in S: return S[k]
    return k  # número literal, «liquido», «14»…

def txt(s, S):
    s = re.sub(r"\[\[(\w+)\|", lambda m: "[[" + clave(m.group(1), S) + "|", s)
    return s.format(**S) if "{" in s else s

def F(S, **kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, str): out[k] = txt(v, S)
        elif isinstance(v, list): out[k] = [txt(x, S) if isinstance(x, str) else [x[0], txt(x[1], S)] for x in v]
        else: out[k] = v
    return out

# ---------- fichas por concepto (mismo texto para los dos lados) ----------
def bomba(S): return F(S,
 que="El cilindro de aluminio con depósito que va en el manubrio, al lado {mano}.",
 sirve="Convierte el apretón de tu mano en presión de líquido. Esa presión baja por la [[mabs|manguera]] y hace que el cáliper apriete el disco.",
 sintomas=["La [[man|manigueta]] se hunde hasta el puño o baja despacio con la moto quieta.", "Ves gotas o manchas de líquido debajo de la bomba o en el puño.", "El freno queda pegado y la rueda se calienta.", "El líquido del visor está oscuro."],
 fallas=[["desgaste", "Si el líquido trae mugre o lleva años sin cambiarse, el cilindro se raya por dentro. Ahí ni las copas nuevas sellan."], ["humedad", "El líquido chupa humedad del aire. Con los años esa agua oxida el cilindro y tapa el orificio que deja volver el líquido."], ["golpe", "En una caída la bomba se puede rajar o doblar donde gira la manigueta."]],
 porque="Si el cilindro está liso, basta con cambiar el [[kit|kit de adentro]]. Si está rayado, oxidado o rajado, va la bomba completa.",
 cuando="Revísala cada vez que cambies el [[liquido|líquido]], cada 2 años: que no gotee, que el visor esté limpio y que la manigueta quede firme.",
 arrastra=["Cilindro rayado → corta las copas del [[kit|kit nuevo]] en pocos días.", "Bomba sin presión → la [[mabs|manguera]] y el cáliper no frenan."])

def kit(S): return F(S,
 que="Las piezas de adentro de la [[b|bomba]]: pistón, dos copas de caucho, resorte, seguro y guardapolvo.",
 sirve="El pistón empuja el líquido cuando aprietas. Las copas sellan para que la presión no se devuelva, y el resorte regresa todo cuando sueltas.",
 sintomas=["La manigueta se siente esponjosa o se va hasta el puño.", "Hay líquido en el guardapolvo o en el puño.", "Frenas menos aunque las pastillas estén bien."],
 fallas=[["edad", "El caucho de las copas se endurece con los años y deja de sellar."], ["humedad", "El líquido viejo con agua hincha las copas."], ["desgaste", "Si el cilindro está rayado, las copas se cortan con el roce."]],
 porque="El caucho no se repara. Se cambia todo el kit, nunca una copa suelta.",
 cuando="Cámbialo cada 2 años, junto con el [[liquido|líquido]], o antes si la manigueta se hunde.",
 arrastra=["Copas sin sellar → la [[man|manigueta]] se hunde y frenas menos."])

def tapa(S): return F(S,
 que="La tapa de arriba del depósito de la bomba {L}. Trae marcado el tipo de líquido.",
 sirve="Cierra el depósito para que no entre polvo ni agua. Mira lo que dice antes de completar: así no echas un líquido equivocado.",
 sintomas=["Hay líquido seco o pegajoso alrededor de la tapa.", "La tapa está rajada o los tornillos tienen la cabeza dañada."],
 fallas=[["golpe", "Se raja en una caída."], ["maluso", "Si aprietas de más los tornillos, la tapa se tuerce y deja de sellar."]],
 porque="Si se raja, se cambia; no se pega.",
 cuando="Ábrela solo para completar o cambiar el líquido, con el manubrio recto. Límpiala antes y tapa la pintura con un trapo: el líquido de frenos la mancha.",
 arrastra=["Tapa rajada → entra agua y el [[liquido|líquido]] se daña antes de tiempo."])

def placa(S): return F(S,
 que="Una lámina delgada entre la [[tapa|tapa]] y el [[diaf|diafragma]].",
 sirve="Reparte el apriete de la tapa sobre el diafragma para que selle parejo.",
 sintomas=["Está doblada o tiene óxido."],
 fallas=[["maluso", "Se dobla si la tapa se aprieta torcida."], ["humedad", "Se oxida si el líquido viejo tiene agua."]],
 porque="Es barata y no se endereza bien: si está doblada, cámbiala.",
 cuando="Mírala cada vez que abras el depósito.",
 arrastra=["Placa doblada → el [[diaf|diafragma]] no sella y entra humedad."])

def diaf(S): return F(S,
 que="Un fuelle de caucho dentro del depósito, debajo de la tapa.",
 sirve="Tapa el líquido sin dejar que toque el aire. Se estira hacia abajo a medida que las pastillas se gastan y el nivel baja.",
 sintomas=["Está rajado, duro o hinchado.", "El líquido se oscurece rápido."],
 fallas=[["edad", "El caucho se endurece y se raja con los años."], ["humedad", "El líquido viejo lo hincha."]],
 porque="Si está rajado, cámbialo. Si está bien, lávalo y vuelve a ponerlo con el fuelle recogido.",
 cuando="Revísalo cada vez que cambies el [[liquido|líquido]].",
 arrastra=["Diafragma rajado → el [[liquido|líquido]] chupa humedad y pierde fuerza."])

def ttapa(S): return F(S,
 que="Dos tornillos chiquitos de cabeza plana que sujetan la [[tapa|tapa]].",
 sirve="Mantienen la tapa cerrada y apretada sobre el diafragma.",
 sintomas=["La cabeza está barrida y el destornillador no agarra."],
 fallas=[["maluso", "Se barren con un destornillador que no es el de la medida."], ["humedad", "Se pegan por el óxido."]],
 porque="Son baratos: si la cabeza está dañada, cámbialos.",
 cuando="Revísalos cada vez que abras el depósito. Apriétalos suave.",
 arrastra=["Tornillo barrido → no puedes abrir el depósito para cambiar el líquido."])

def man(S): return F(S,
 que="La palanca de aluminio delante del puño {mano}.",
 sirve="Es lo que aprietas para frenar. Multiplica la fuerza de tu mano y empuja el pistón de la [[b|bomba]].",
 sintomas=["Tiene juego de lado a lado.", "Está doblada o con la punta partida.", "Queda dura o regresa despacio."],
 fallas=[["golpe", "Se dobla o se parte en una caída."], ["desgaste", "Sin grasa, el agujero del eje se agranda y queda con juego."]],
 porque="Una manigueta doblada no se endereza: el aluminio se debilita y se puede partir frenando.",
 cuando="Revisa el juego en cada servicio, y después de cualquier caída.",
 arrastra=["Manigueta doblada → la luz de freno queda prendida o el freno queda pegado."])

def pman(S): return F(S,
 que="El eje sobre el que gira la [[man|manigueta]].",
 sirve="Deja girar la manigueta suave y sin juego.",
 sintomas=["La manigueta queda dura o regresa despacio.", "Chirría al frenar."],
 fallas=[["desgaste", "Sin grasa se gasta y la manigueta queda con juego."], ["humedad", "Se oxida y la manigueta no regresa sola."]],
 porque="Si está gastado u oxidado, cámbialo; es barato.",
 cuando="Límpialo y engrásalo con grasa de silicona en cada servicio.",
 arrastra=["Eje gastado → la [[man|manigueta]] queda con juego."])

def tuer(S): return F(S,
 que="Una tuerca con anillo de nailon, debajo del eje de la [[man|manigueta]].",
 sirve="Asegura el eje para que no se salga con la vibración.",
 sintomas=["Se suelta con la mano o gira sin frenar."],
 fallas=[["desgaste", "El anillo de nailon pierde agarre cada vez que se quita."]],
 porque="Al quitarla pierde el agarre: pon una nueva cada vez.",
 cuando="Cámbiala cada vez que desarmes la manigueta.",
 arrastra=["Tuerca floja → el eje se sale y la [[man|manigueta]] queda suelta."])

def abr(S): return F(S,
 que="La media luna que abraza el manubrio por detrás de la [[b|bomba]].",
 sirve="Fija la bomba al manubrio. Al montarla, la marca de la abrazadera va como estaba; el orden de apriete y el torque están en el manual de servicio.",
 sintomas=["La bomba gira en el manubrio al frenar duro."],
 fallas=[["maluso", "Se raja si se aprieta de más o en desorden."], ["golpe", "Se dobla en una caída."]],
 porque="Si está rajada, cámbiala; no aguanta el apriete.",
 cuando="Revisa el apriete en cada servicio.",
 arrastra=["Abrazadera floja → la bomba gira y la [[man|manigueta]] queda en mal ángulo."])

def pabr(S): return F(S,
 que="Los dos pernos que cierran la [[abr|abrazadera]] de la bomba.",
 sirve="Aprietan la abrazadera contra el manubrio.",
 sintomas=["La bomba se mueve en el manubrio."],
 fallas=[["maluso", "Se barren si se aprietan de más."]],
 porque="Si la rosca está dañada, cámbialos.",
 cuando="Revisa el apriete en cada servicio. El torque está en el manual de servicio.",
 arrastra=["Perno flojo → la bomba se mueve al frenar."])

def int_(S): return F(S,
 que="El interruptor de la luz de freno, atornillado debajo de la [[b|bomba]].",
 sirve="Prende la luz de freno cuando aprietas la [[man|manigueta]], para que el de atrás te vea frenar.",
 sintomas=["La luz de freno no prende al frenar.", "La luz queda prendida todo el tiempo."],
 fallas=[["humedad", "El agua de las lavadas oxida el contacto."], ["golpe", "Un golpe en la manigueta lo deja hundido."]],
 porque="No se abre: si falla, se cambia completo.",
 cuando="Pruébalo antes de salir: aprieta la manigueta y mira que prenda la luz. Si lo cambias, vuelve a probarlo antes de rodar.",
 arrastra=["Interruptor dañado → la luz de freno no avisa y te pueden chocar por detrás."])

def tint(S): return F(S,
 que="Un tornillo chiquito con arandela que sujeta el [[int|interruptor]].",
 sirve="Mantiene el interruptor en su sitio, tocando la manigueta.",
 sintomas=["El interruptor se mueve y la luz falla a ratos."],
 fallas=[["maluso", "Se barre si se aprieta de más."]],
 porque="Si está barrido, cámbialo.",
 cuando="Revísalo al cambiar el interruptor.",
 arrastra=["Tornillo flojo → la luz de freno prende a ratos."])

def manguera(S, tramo):
    a, b = ("la bomba {L}", "la unidad ABS") if tramo == "abs" else ("la unidad ABS", "el cáliper {L}")
    u, ar = ("uabs", "aabs") if tramo == "abs" else ("ucal", "acal")
    return F(S,
     que=f"La manguera de caucho reforzado que va de {a} a {b}.",
     sirve="Lleva la presión del líquido sin inflarse. Así la manigueta se siente firme.",
     sintomas=["Tiene grietas, bombas o partes mojadas.", "La manigueta se siente esponjosa.", "Gotea en las puntas."],
     fallas=[["edad", "El caucho se agrieta con el sol y los años."], ["golpe", "Se pellizca en una caída o roza con el giro del manubrio."]],
     porque="Una manguera no se parcha: si tiene grietas o bombas, se cambia. Después hay que purgar el freno; con ABS, en el taller.",
     cuando="Cámbiala cada 4 años. Revísala en cada servicio, girando el manubrio de lado a lado.",
     arrastra=[f"Manguera inflada → la [[man|manigueta]] se siente esponjosa y frenas menos.", f"Fuga en la punta → si cambias el [[{u}|perno]], pon [[{ar}|arandelas]] nuevas."])

def union(S, tramo):
    a, b = ("la bomba {L}", "la unidad ABS") if tramo == "abs" else ("la unidad ABS", "el cáliper {L}")
    ar, mg = ("aabs", "mabs") if tramo == "abs" else ("acal", "mcal")
    return F(S,
     que=f"Un perno hueco que fija la punta de la [[{mg}|manguera]] en {a} y en {b}.",
     sirve="Deja pasar el líquido por adentro mientras aprieta la punta de la manguera.",
     sintomas=["Gotea o hay líquido seco en la unión."],
     fallas=[["maluso", "Si se aprieta de más se parte o se barre la rosca."], ["humedad", "Por el hueco pasa líquido viejo y se tapa con óxido."]],
     porque="Si está sano y sin daño en la rosca, se vuelve a usar. Las [[" + ar + "|arandelas]] van nuevas siempre.",
     cuando="Revísalo cada vez que sueltes la manguera. El torque está en el manual de servicio.",
     arrastra=[f"Perno flojo → entra aire y la [[man|manigueta]] se hunde."])

def arand(S, tramo):
    u = "uabs" if tramo == "abs" else "ucal"
    return F(S,
     que=f"Arandelas de metal blando, una arriba y otra abajo de la punta de la manguera, en cada [[{u}|perno hueco]].",
     sirve="Se aplastan al apretar y sellan para que no salga el líquido.",
     sintomas=["Gotea la unión de la manguera."],
     fallas=[["maluso", "Ya aplastadas no vuelven a sellar si las reutilizas."]],
     porque="Siempre nuevas: una arandela usada ya no sella.",
     cuando="Cámbialas cada vez que sueltes el perno hueco.",
     arrastra=["Arandela reutilizada → gotea la unión y entra aire."])

def soporte_simple(que, sirve, extra_sint=None, ojo=True):
    return lambda S: F(S, que=que, sirve=sirve,
     sintomas=["Está doblado, roto o suelto.", "La manguera roza el chasis o una rueda."] + (extra_sint or []),
     fallas=[["golpe", "Se dobla en una caída."], ["edad", "El caucho del ojo se reseca y se parte."] if ojo else ["humedad", "Se oxida con el agua de las lavadas."]],
     porque="Si está doblado o roto, cámbialo; no se endereza bien.",
     cuando="Revísalo en cada servicio y después de una caída.",
     arrastra=["Soporte roto → la [[38|manguera]] roza y se gasta hasta romperse."])

def perno_simple(que):
    return lambda S: F(S, que=que, sirve="Fija el soporte al chasis.",
     sintomas=["El soporte está flojo."], fallas=[["humedad", "Se oxida con las lavadas."], ["maluso", "Se barre si se aprieta de más."]],
     porque="Si la rosca está dañada, cámbialo.", cuando="Revisa el apriete en cada servicio.",
     arrastra=["Perno flojo → el soporte vibra y la [[38|manguera]] roza."])

TRA = LADOS["tra"]
UNICAS = {
 "14": lambda S: F(S, que="Una pieza junto a la unidad ABS que sujeta las dos mangueras que bajan de las bombas.",
   sirve="Mantiene la [[15|manguera delantera]] y la [[34|trasera]] quietas, lejos de lo que se mueve.",
   sintomas=["Está rota o las mangueras se mueven sueltas."], fallas=[["golpe", "Se rompe en una caída."], ["edad", "El plástico se reseca y se parte."]],
   porque="Si está rota, cámbiala.", cuando="Revísala en cada servicio, sobre todo después de una caída.",
   arrastra=["Tope roto → las mangueras rozan y se gastan."]),
 "37": lambda S: F(S, que="Una abrazadera pequeña sobre la [[34|manguera que baja de la bomba trasera]].",
   sirve="Sujeta la manguera para que no roce con el giro del manubrio.",
   sintomas=["Está abierta o la manguera roza."], fallas=[["golpe", "Se abre en una caída."]],
   porque="Si está abierta o rota, cámbiala.", cuando="Revísala en cada servicio.",
   arrastra=["Abrazadera abierta → la [[34|manguera]] roza y se gasta."]),
 "41": lambda S: F(S, que="Una abrazadera sobre la [[38|manguera que va al cáliper trasero]], cerca de la unidad ABS.",
   sirve="Sujeta el primer tramo de la manguera.", sintomas=["Está abierta o la manguera se mueve."], fallas=[["golpe", "Se abre en una caída."]],
   porque="Si está abierta o rota, cámbiala.", cuando="Revísala en cada servicio.",
   arrastra=["Abrazadera abierta → la [[38|manguera]] roza."]),
 "42": soporte_simple("Un soporte de metal con ojo de caucho por donde pasa la [[38|manguera trasera]], en el tramo del medio.", "Guía la manguera por el chasis para que no toque nada que se mueva."),
 "43": perno_simple("El perno con arandela pegada que fija el [[42|soporte del tramo medio]]."),
 "44": soporte_simple("Un soporte de metal en el recorrido de la [[38|manguera trasera]] que lleva una [[45|abrazadera]].", "Sostiene la abrazadera que aguanta la manguera.", ojo=False),
 "45": lambda S: F(S, que="La abrazadera montada en el [[44|soporte]].", sirve="Sujeta la [[38|manguera trasera]] contra el soporte.",
   sintomas=["Está abierta o la manguera se mueve."], fallas=[["golpe", "Se abre en una caída."]], porque="Si está abierta o rota, cámbiala.",
   cuando="Revísala en cada servicio.", arrastra=["Abrazadera abierta → la [[38|manguera]] roza."]),
 "46": soporte_simple("El soporte de la bobina de encendido. También guía la [[38|manguera trasera]].", "Sostiene la bobina y mantiene la manguera en su ruta.", ["La moto falla si la bobina quedó suelta."], ojo=False),
 "47": perno_simple("Los dos pernos con arandela pegada que fijan el [[46|soporte de la bobina]]."),
 "48": soporte_simple("Un soporte de metal con ojo de caucho para la [[38|manguera trasera]], en el último tramo antes del cáliper.", "Mantiene la manguera lejos de la rueda y del basculante."),
 "49": perno_simple("El perno con arandela pegada que fija el [[48|soporte del último tramo]]."),
}

PARES = dict(b=bomba, kit=kit, tapa=tapa, placa=placa, diaf=diaf, ttapa=ttapa, man=man, pman=pman, tuer=tuer, abr=abr, pabr=pabr, int=int_, tint=tint)
NUEVAS = {}
for l, S in LADOS.items():
    for k, fn in PARES.items(): NUEVAS[clave(k, S)] = fn(S)
    NUEVAS[S["mabs"]] = manguera(S, "abs"); NUEVAS[S["mcal"]] = manguera(S, "cal")
    NUEVAS[S["uabs"]] = union(S, "abs"); NUEVAS[S["ucal"]] = union(S, "cal")
    NUEVAS[S["aabs"]] = arand(S, "abs"); NUEVAS[S["acal"]] = arand(S, "cal")
for k, fn in UNICAS.items(): NUEVAS[k] = fn(TRA)

NOMBRES_NUEVOS = {"15": "Manguera de la bomba a la ABS (delantera)", "18": "Manguera de la ABS al cáliper (delantera)",
 "34": "Manguera de la bomba a la ABS (trasera)", "38": "Manguera de la ABS al cáliper (trasera)",
 "16": "Perno hueco de la manguera bomba–ABS (delantera)", "17": "Arandelas de la unión de la manguera bomba–ABS (delantera)",
 "19": "Perno hueco de la manguera ABS–cáliper (delantera)", "20": "Arandelas de la unión de la manguera ABS–cáliper (delantera)",
 "35": "Perno hueco de la manguera bomba–ABS (trasera)", "36": "Arandelas de la unión de la manguera bomba–ABS (trasera)",
 "39": "Perno hueco de la manguera ABS–cáliper (trasera)", "40": "Arandelas de la unión de la manguera ABS–cáliper (trasera)",
 "14": "Tope de las mangueras", "37": "Abrazadera de la manguera trasera", "41": "Abrazadera del tramo inicial",
 "42": "Soporte del tramo medio", "43": "Perno del soporte del tramo medio", "44": "Soporte de la abrazadera", "45": "Abrazadera del soporte",
 "48": "Soporte del último tramo", "49": "Perno del soporte del último tramo"}

DIF = {"facil": "facil", "media": "taller", "taller": "taller"}
for k, N in NUEVAS.items():
    v = V1[k]; c = CAT.get(k, {})
    N["nombre"] = NOMBRES_NUEVOS.get(k, v["nombre"]); N["cat"] = v["cat"]; N["codigo"] = c.get("codigo", "")
    N["decision"] = v["decision"]; N["dif"] = DIF[v["dif"]]
    N["conecta"] = [x for x in v["conecta"]]; N["certeza"] = v["certeza"]
    if "forma3d" in v: N["forma3d"] = v["forma3d"]
    if k in ("17", "20", "36", "40", "16", "19", "35", "39"): N["dif"] = "taller"
    if k in ("16", "19", "35", "39"): N["decision"] = "reutiliza"
    D["fichas"][k] = N
    D["nombres"][k] = N["nombre"]
# los kits se cambian con el líquido: decisión «cambia», arandelas nuevas siempre
D["fichas"]["liquido"]["conecta"] = D["fichas"]["liquido"].get("conecta", [])

# ---------- grupos (subconjuntos) ----------
def ids(*xs): return [str(x) for x in xs]
G = []
for l, S in LADOS.items():
    o = S["off"]; n = lambda x: str(x + o)
    G.append(dict(id=f"bomba-{l}", lado=l, nombre="Bomba", piezas=ids(n(1), n(2), n(3), n(4), n(5), n(10)),
      torn=[dict(nombre="Tornillos de la tapa", ids=[n(6)], ancla=None), dict(nombre="Pernos de la abrazadera", ids=[n(11)], ancla=None)],
      pasos=[0 + (6 if o else 0), 4 + (6 if o else 0), 5 + (6 if o else 0)]))
    G.append(dict(id=f"manigueta-{l}", lado=l, nombre="Manigueta e interruptor", corto="Manigueta", piezas=ids(n(7), n(12)),
      torn=[dict(nombre="Eje y tuerca de la manigueta", ids=[n(8), n(9)]), dict(nombre="Tornillo del interruptor", ids=[n(13)])],
      pasos=[2 + (6 if o else 0), 3 + (6 if o else 0)]))
    G.append(dict(id=f"mabs-{l}", lado=l, nombre="Manguera a la ABS", corto="Manguera ABS", piezas=[S["mabs"]] + (["14"] if l == "del" else ["37"]),
      torn=[dict(nombre="Unión en la bomba", ids=[S["uabs"] + "a", S["aabs"] + "a"]), dict(nombre="Unión en la ABS", ids=[S["uabs"] + "b", S["aabs"] + "b"])],
      pasos=[1, 12] if l == "del" else [7, 13]))
    G.append(dict(id=f"mcal-{l}", lado=l, nombre="Manguera al cáliper", corto="Manguera cáliper", piezas=[S["mcal"]],
      torn=[dict(nombre="Unión en la ABS", ids=[S["ucal"] + "a", S["acal"] + "a"]), dict(nombre="Unión en el cáliper", ids=[S["ucal"] + "b", S["acal"] + "b"])],
      pasos=[14] if l == "del" else [16]))
G.append(dict(id="soportes-tra", lado="tra", nombre="Soportes de la manguera", corto="Soportes", piezas=ids(41, 42, 44, 45, 46, 48),
  torn=[dict(nombre="Perno del soporte del tramo medio", ids=["43"]), dict(nombre="Pernos del soporte de la bobina", ids=["47"]), dict(nombre="Perno del soporte del último tramo", ids=["49"])],
  pasos=[15]))
PZ = {p["id"]: p for p in D["piezas"]}
MARCAS = {"bomba-del":[745,16],"manigueta-del":[975,78],"mabs-del":[640,250],"mcal-del":[820,610],
 "bomba-tra":[355,16],"manigueta-tra":[125,78],"mabs-tra":[460,250],"mcal-tra":[250,560],"soportes-tra":[330,820]}
for g in G:
    g["marca"] = MARCAS[g["id"]]
    for t in g["torn"]:
        t["cant"] = sum(CAT[PZ[i]["n"]]["cantidad"] // (2 if i[-1] in "ab" else 1) for i in t["ids"])
        t["ancla"] = PZ[t["ids"][0]]["anc"]
        t["corto"] = {"Tornillos de la tapa":"Tornillos","Pernos de la abrazadera":"Pernos","Eje y tuerca de la manigueta":"Eje y tuerca","Tornillo del interruptor":"Tornillo","Pernos del soporte de la bobina":"Pernos"}.get(t["nombre"], "Unión" if t["nombre"].startswith("Unión") else "Perno")

# ---------- textos de los pasos, sin números ----------
PASOS_T = {}
PINTURA = "Tapa la pintura con un trapo: el líquido de frenos la mancha."
for l, S in LADOS.items():
    o = 6 if S["off"] else 0
    B = f"Bomba {S['L']} ({S['mano']})"
    PASOS_T[0 + o] = f"<b>{B} · Tapa del depósito.</b> Manubrio recto, para que el depósito quede plano. {PINTURA} Sacas los dos tornillos, la tapa, la placa y el diafragma, y sacas el líquido con una jeringa limpia o purgándolo por el cáliper."
    PASOS_T[1 + o] = f"<b>{B} · Unión de la manguera.</b> Saca el líquido con una jeringa antes de soltar el perno hueco: si no, todo sale por la unión. {PINTURA} Con un trapo debajo, sueltas el perno: salen el perno y sus dos arandelas. Tapa la punta de la manguera con una bolsa."
    PASOS_T[2 + o] = f"<b>{B} · Interruptor de la luz de freno.</b> Desconecta el cable, sueltas un tornillo y sale."
    PASOS_T[3 + o] = f"<b>{B} · Manigueta.</b> Primero la tuerca de abajo, después el eje, y la manigueta sale hacia adelante. Al armar, la tuerca va nueva."
    PASOS_T[4 + o] = f"<b>{B} · Abrazadera y bomba.</b> Sueltas los dos pernos de la abrazadera y la bomba sale del manubrio. Al montarla, la marca de la abrazadera va como estaba; el orden de apriete y el torque están en el manual de servicio."
    PASOS_T[5 + o] = f"<b>{B} · Kit de adentro.</b> En el banco: quitas el guardapolvo y el seguro, y salen pistón, copas y resorte. El kit va completo y nuevo."
PASOS_T[12] = "<b>Manguera de la bomba a la ABS (delantera).</b> Sueltas la unión en la ABS y el tope, y la manguera sale. Tapa las puntas para que no entre mugre."
PASOS_T[13] = "<b>Manguera de la bomba a la ABS (trasera).</b> Igual atrás: unión en la ABS, abrazadera y manguera."
PASOS_T[14] = "<b>Manguera de la ABS al cáliper (delantera).</b> Sueltas las uniones en la ABS y en el cáliper."
PASOS_T[15] = "<b>Soportes de la manguera trasera.</b> Abres las abrazaderas y sueltas los pernos de cada soporte, de la ABS hacia la rueda."
PASOS_T[16] = "<b>Manguera de la ABS al cáliper (trasera).</b> Sueltas las dos uniones y la manguera sale por los soportes. <b>Al armar todo:</b> arandelas nuevas en cada unión, líquido DOT 4 nuevo y purgar hasta que la manigueta quede firme; con ABS, la purga se hace en el taller. <b>Antes de rodar, prueba los dos frenos con la moto quieta.</b>"
for i, t in PASOS_T.items(): D["pasos"][i]["t"] = t

# ---------- «Cuándo» y «Si falla» sin números ----------
for r in D["cuando"]: r["que"] = re.sub(r"\s*\([\d ,ya]+\)", "", r["que"])

# ---------- 3D: solo formas difíciles de imaginar ----------
D["v2"] = dict(deriva="nmax-fig26-v1.json", toqueExtra=["37", "41", "44", "45"], grupos=G, lados={"del": "Delantera", "tra": "Trasera"}, lado="del",
  con3d=["1", "2", "21", "22"],
  conjunto3d={"bomba": {"titulo": "La bomba armada", "partes": V1["1"]["forma3d"]["partes"] + [
     {"tipo": "caja", "color": "alum", "tam": [12, 8, 92], "pos": [30, -22, 30], "rot": [0, 18, 0]},
     {"tipo": "cilindro", "color": "aceroOsc", "r": 4, "z": [-12, 12], "pos": [22, -20]},
     {"tipo": "caja", "color": "plast", "tam": [14, 10, 18], "pos": [-6, -30, 30]}]}})
D["cabeza"]["titulo"] = D["cabeza"]["titulo"]
json.dump(D, open(M + "datos/nmax-fig26.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("ok", len(NUEVAS), "fichas nuevas;", len(G), "grupos")
