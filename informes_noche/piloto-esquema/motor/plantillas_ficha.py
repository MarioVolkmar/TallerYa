"""Plantillas de ficha v2 por tipo de pieza (estilo v2 y regla de seguridad ya puestos). Llenan SOLO los campos vacíos.

Uso:
  python plantillas_ficha.py datos/<lamina>.json                 muestra qué tipo le toca a cada ficha vacía (por la descripción del catálogo)
  python plantillas_ficha.py datos/<lamina>.json --escribir      llena los campos vacíos con la plantilla de su tipo
  python plantillas_ficha.py datos/<lamina>.json --tipo 23=filtro,33=abrazadera --escribir   fuerza el tipo de algunas fichas

Las plantillas son un borrador correcto y prudente, no la ficha final: la creadora cambia «dónde va», el síntoma propio de
este sistema y los enlaces [[n|texto]] a las piezas vecinas. {pieza} = nombre de la ficha en minúscula; {donde} = «dónde va»
si la ficha ya trae «que» (si no, queda la frase genérica). Tipos: tornillos, tuerca, arandela, oring, empaque, sello, reten,
rodamiento, buje, resorte, seguro, grapa, abrazadera, caucho, manguera, tubo, filtro, tapa, caja, conjunto, pieza.
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
TIPOS = [(r"ELEMENT|FILTER", "filtro"), (r"HOSE CLAMP", "abrazadera"), (r"CIRCLIP", "seguro"), (r"OIL SEAL", "reten"), (r"O-RING", "oring"),
         (r"GASKET", "empaque"), (r"SEAL", "sello"), (r"BEARING", "rodamiento"), (r"BOLT|SCREW", "tornillos"), (r"NUT", "tuerca"),
         (r"WASHER", "arandela"), (r"COLLAR|BUSH", "buje"), (r"SPRING", "resorte"), (r"CLIP", "grapa"), (r"GROMMET|DAMPER", "caucho"),
         (r"HOSE|PIPE", "manguera"), (r"CAP|COVER", "tapa"), (r"CASE", "caja"), (r"ASSY|COMP", "conjunto")]


def tipo_de(cat, desc_en=None):
    """Tipo por la descripción del catálogo; en español (o con descripcion_en) se pasa antes por catalogo/claves_es.py."""
    d = clave_en(cat.split(" · ")[0], desc_en)
    return next((t for ex, t in TIPOS if re.search(ex, d)), "pieza")


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


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    ruta = pathlib.Path(a[0]); D = json.loads(ruta.read_text(encoding="utf-8"))
    forz = dict(x.split("=") for x in (a[a.index("--tipo") + 1].split(",") if "--tipo" in a else []))
    escribir = "--escribir" in a
    EN = descripciones_en(D)
    for k, F in D["fichas"].items():
        if F.get("ctx"): continue
        t = forz.get(k) or tipo_de(F.get("cat", ""), EN.get(k))
        vac = [c for c in P[t] if not F.get(c)]
        if not vac: continue
        if escribir: llenar(F, t, lugar_de(D, k))
        print(f"  {k:5} {F.get('nombre', '')[:30]:30} → {t:11} {'llenó' if escribir else 'llenaría'}: {', '.join(vac)}")
    if escribir:
        ruta.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8"); print("escrito", ruta.name)


if __name__ == "__main__":
    main()
