"""Nombres que distinguen piezas que el catálogo llama igual (mismo nombre, distinto código).

1. VARIANTES: nombres revisados a mano contra el plano de la lámina (línea, figura, código).
2. nombres_distintos(): regla general. Los catálogos listan las piezas en orden de montaje, así que una pieza suele ir
   con la pieza principal que la precede: "Abrazadera · del conducto filtro aire". Si aun así coinciden, se usa la
   pieza que la sigue y, como último recurso, el orden ("1.ª", "2.ª").
"""
import re

VARIANTES = {
    # Correcciones del Auditor mecánico: nombres que no corresponden a la tecnología de la moto
    ("XTZ 125", 6): {"2MC-E4453-00": "Ducto del filtro al carburador"},           # de carburador: no tiene cuerpo de aceleración
    ("MT-03", 8): {"2MS-E3586-00": "Tobera de admisión (al cuerpo de aceleración)"},  # de inyección: "JOINT, CARBURETOR" es la tobera
    # Tapa de la transmisión (fig. 11, igual en NMAX y Aerox): las tapas, su empaque y el filtro de aire de la caja de la correa
    ("Aerox 155", 11): {"B6H-E5411-01": "Tapa de la transmisión", "B6H-E5431-00": "Tapa exterior de la transmisión",
                        "B6H-E5451-00": "Empaque de la tapa de la transmisión", "2DP-E5407-00": "Filtro de aire de la caja de la correa",
                        "B6H-E5316-00": "Caucho de la tapa", "B6H-E5326-00": "Caucho de la tapa", "B6H-E533C-00": "Caucho de la tapa",
                        "B6H-E533E-00": "Caucho de la tapa"},
    ("NMAX 155", 11): {"B6H-E5411-01": "Tapa de la transmisión", "B6H-E5431-00": "Tapa exterior de la transmisión",
                       "2DP-E5407-00": "Filtro de aire de la caja de la correa"},
    # Aerox, fig. 10: el "amortiguador" del cárter es el caucho del soporte del motor
    ("Aerox 155", 10): {"90388-10808": "Caucho del soporte del motor", "4D1-F2216-00": "Buje del soporte del motor"},
    # Aerox 155, fig. 7: el "filtro de aceite" del catálogo es el colador de malla que sostiene el tapón de drenaje
    ("Aerox 155", 7): {"54P-E3411-00": "Colador del aceite"},
    # Pulsar NS 200 FI, fig. 22 (encendido de tres bujías): bobina doble (8) para las laterales, sencilla (9) para la central
    ("Pulsar NS 200", 22): {
        "DD111012": "Antivibrante salida de bobina",
        "AN111015": "Capuchón bujía lateral izquierda",
        "JD351207": "Capuchón bujía lateral derecha",
        "DK111011": "Capuchón bujía central",
        "DH111013": "Antivibrante sobre la bujía",
        "DH111016": "Antivibrante capuchón lateral izquierdo",
        "DD111011": "Antivibrante capuchón lateral derecho",
    },
}

# Palabras de tornillería: no sirven para decir "con qué va" una pieza
_MENUDA = re.compile(r"^(tornillo|tuerca|arandela|anillo|pin|seguro|buje|abrazadera|grapa|o-ring|empaque|reten|retén|"
                     r"rodamiento|balinera|esparrago|espárrago|antivibrante|caucho|platina|resorte|kit|-)", re.I)


# Piezas en las que "grande / pequeño" sí dice algo (su medida es la de la pieza misma)
_CON_TAMANO = re.compile(r"^(rodamiento|balinera|tornillo|perno|esp[aá]rrago|tuerca|arandela|o-ring|ret[eé]n|buje)", re.I)


def _corto(nombre):
    nombre = re.sub(r"\s*[-–]\s*[-–\s]*$", "", nombre).strip()
    return nombre[:1].lower() + nombre[1:] if nombre else nombre


# El catálogo lista el empaque de un tapón justo después de él; solo se llama "O-ring" o "Empaque", pero es lo que se
# cambia en el mantenimiento, así que se nombra por su tapón: "Empaque del tapón con varilla del aceite".
_SELLO_SUELTO = re.compile(r"(?i)^(o[\s-]?ring|empaque|arandela|arandela de (cobre|sellado)|junta)( grande| pequeñ[oa])?$")
_TAPON = re.compile(r"(?i)^(tap[oó]n|tornillo de drenaje)\b")


def nombres_de_sellos(partes):
    """{índice: nombre} para el empaque que sigue a su tapón (número siguiente en la lámina)."""
    salida = {}
    for i in range(1, len(partes)):
        p, previa = partes[i], partes[i - 1]
        if p["ref"] == previa["ref"] + 1 and _SELLO_SUELTO.match(p["nombre"]) and _TAPON.match(previa["nombre"]):
            salida[i] = f"Empaque del {_corto(previa['nombre'])}"
    return salida

# Empaques, retenedores y guardapolvos sin dueño ("O ring", "Retén"): nunca solos. Se nombran por la pieza que sellan:
# la de su lugar en el dibujo (empaque_culata), la pieza que el catálogo lista antes o, si no, el sistema de la lámina.
_SELLO_SIN_DUENO = re.compile(r"(?i)^(o[\s-]?ring|oring|empaque|empaques|junta|ret[eé]n|retenedor|sello|guardapolvo)$")
_INICIO_SELLO = re.compile(r"(?i)^(o[\s-]?ring|oring)\b\s*")
_DUENO_PUESTO = {"culata": "culata", "cilindro": "cilindro", "tapa": "tapa de válvulas", "silenciador": "silenciador",
                 "tensor": "tensor de la cadenilla", "carcasa": "cárter", "carter": "cárter", "tapa_clutch": "tapa del clutch"}
_FEMENINAS = {"base", "llave", "parte", "red", "polea", "flor", "cruceta", "torre"}
_HERRAJE_O_SELLO = re.compile(r"(?i)^(tornillo|tuerca|arandela|anillo|pin|seguro|buje|abrazadera|grapa|o[\s-]?ring|oring|empaque|"
                              r"junta|ret[eé]n|retenedor|sello|guardapolvo|esp[aá]rrago|resorte|platina|perno|contratuerca|gu[ií]a de centrado|kit|"
                              r"remache|clip|chaveta|balinera|rodamiento|espaciador|-)")


# Pieza que el catálogo nombra después de la coma ("BOOT, PIN BUSH"): es la dueña del sello, antes que la pieza vecina
_DUENO_EN_DESCRIPCION = [
    (r"PIN BUSH|SLIDE PIN|PASADOR", "pasador del caliper"), (r"(REAR )?SHOCK ABSORBER|CUSHION", "amortiguador trasero"),
    (r"FRONT HUB|HUB,? FR", "manzana delantera"), (r"REAR HUB|HUB,? RR", "manzana trasera"), (r"\bHUB\b", "manzana"),
    (r"\bWHEEL\b|\bRUEDA\b", "rueda"), (r"FRONT FORK|\bFORK\b|HORQUILLA", "barra de la suspensión"),
    (r"STEERING|DIRECCION", "dirección"), (r"BRAKE CAM|CAMSHAFT, BRAKE", "leva del freno"), (r"\bCALIPER\b|CALIBRE", "caliper"),
    (r"\bPISTON\b", "pistón"), (r"SWING ?ARM|REAR ARM", "basculante"), (r"\bVALVE\b|VALVULA", "válvula"),
]


def articulo_de(frase):
    """'del', 'de la', 'de los' o 'de las' según la primera palabra de la frase (cárter → del, culata → de la)."""
    palabra = (frase.split() or [""])[0].lower()
    plural = palabra.endswith("s") and len(palabra) > 3 and not palabra.endswith(("ás", "és", "ís", "ós", "ús", "is"))
    base = palabra[:-1] if plural and not palabra.endswith("es") else (palabra[:-2] if plural else palabra)
    femenina = (base.endswith("a") or base.endswith(("ión", "ion", "dad")) or base in _FEMENINAS) and base not in ("sistema", "día")
    if plural:
        return "de las" if femenina else "de los"
    return "de la" if femenina else "del"


def _con_dueno(palabra, dueno):
    dueno = dueno[:1].lower() + dueno[1:]
    return f"{palabra} {articulo_de(dueno)} {dueno}"


def nombres_de_empaques(partes, lamina):
    """{índice: nombre} para empaques, retenedores y guardapolvos sin dueño. partes: dicts con nombre, descripcion y
    _puesto (su lugar en el dibujo). La palabra se unifica: o-ring/empaque → Empaque; retén/sello → Retenedor."""
    salida = {}
    for i, p in enumerate(partes):
        nombre = p["nombre"].strip()
        texto = (p.get("descripcion") or "").upper()
        if re.search(r"DUST SEAL|SEAL,\s*DUST|GUARDAP|^FUNDA", texto) or re.match(r"(?i)^guardapolvo", nombre):
            palabra = "Guardapolvo"
        elif re.search(r"OIL SEAL|SEAL,\s*OIL|RET[EÉ]N|RETENEDOR", texto) or re.match(r"(?i)^(ret[eé]n|retenedor|sello)$", nombre):
            palabra = "Retenedor"
        else:
            palabra = "Empaque"
        propio = next((d for patron, d in _DUENO_EN_DESCRIPCION if re.search(patron, texto)), None)
        if _SELLO_SIN_DUENO.match(nombre) and propio:
            salida[i] = _con_dueno(palabra, propio)          # la descripción nombra la pieza: manda sobre la vecina
        elif _SELLO_SIN_DUENO.match(nombre):
            puesto = p.get("_puesto") or ""
            sufijo = puesto.split("_", 1)[1] if "_" in puesto and not puesto.startswith("h_") else ""
            dueno = _DUENO_PUESTO.get(sufijo) or (sufijo.replace("_", " ") if sufijo else "")
            if not dueno:
                previa = next((q["nombre"] for q in reversed(partes[:i]) if 0 < p["ref"] - q["ref"] <= 2
                               and not _HERRAJE_O_SELLO.match(q["nombre"])), "")
                dueno = previa or re.split(r",| y | con | · |\(", lamina or "")[0].strip()
            if dueno:
                salida[i] = _con_dueno(palabra, dueno)
        elif _INICIO_SELLO.match(nombre):
            # "O ring eje balan inferior" → "Empaque del eje balan inferior"; "O ring de admisión" → "Empaque de admisión"
            resto = _INICIO_SELLO.sub("", nombre)
            if re.match(r"(?i)^(de|del|para)\b", resto):
                salida[i] = f"{palabra} {resto}"
            elif resto:
                salida[i] = _con_dueno(palabra, resto)
        else:
            # Catálogo sin preposiciones: "Empaque culata" → "Empaque de la culata"; "Retén rin trasero" → "Retenedor del rin trasero"
            m = re.match(r"(?i)^(empaque|junta|ret[eé]n|retenedor|sello|guardapolvo),?\s+(?!de\b|del\b|para\b)(\S.*)$", nombre)
            if m:
                cabeza = m.group(1).lower()
                palabra = ("Empaque" if cabeza in ("empaque", "junta") else "Guardapolvo" if cabeza == "guardapolvo"
                           else "Retenedor" if cabeza in ("retén", "reten", "retenedor") or palabra == "Retenedor" else "Sello")
                resto = re.sub(r"\s*[+]\s*$", "", m.group(2)).strip()
                if re.match(r"(?i)^(delantero|trasero|izquierdo|derecho|superior|inferior|grande|pequeño|interno|externo)\b", resto):
                    continue                                   # "Retén delantero de la suspensión" ya se entiende
                salida[i] = _con_dueno(palabra, resto)
    return salida


def nombres_distintos(linea, figura, partes):
    """partes: lista de dicts con ref, codigo y nombre (en orden de número).

    Devuelve ({índice: nombre distinto}, {índice: con qué pieza va}). El nombre solo cambia cuando hay algo concreto
    que decir (revisado a mano o el tamaño: "Rodamiento grande"); la pieza con la que va se muestra en la guía, no en
    el nombre (un nombre como "Rodamiento · para eje principal" es confuso en la lista)."""
    manual = VARIANTES.get((linea, figura), {})
    salida, va_con = {}, {}
    por_nombre = {}
    for i, p in enumerate(partes):
        if p["codigo"] in manual:
            salida[i] = manual[p["codigo"]]
        por_nombre.setdefault(p["nombre"], []).append(i)
    principales = [(i, p) for i, p in enumerate(partes) if not _MENUDA.match(p["nombre"])]

    def vecina(i, hacia):
        """La pieza principal más cercana antes (hacia=-1) o después (hacia=1) en la lista, con otro nombre."""
        candidatas = [(j, q) for j, q in principales if (j < i if hacia < 0 else j > i) and q["nombre"] != partes[i]["nombre"]]
        if not candidatas:
            return None
        j, q = (candidatas[-1] if hacia < 0 else candidatas[0])
        return _corto(q["nombre"])

    for nombre, indices in por_nombre.items():
        pendientes = [i for i in indices if i not in salida]
        if len({partes[i]["codigo"] for i in indices}) < 2 or not pendientes:
            continue
        # Tornillería y rodamientos: por tamaño (no dice nada "para carcasa"); las demás piezas, por la pieza con la que van
        tamanos = None
        if _CON_TAMANO.match(nombre):
            con_medida = [i for i in pendientes if _medida(partes[i])]
            tamanos = _por_tamano([partes[i] for i in con_medida]) if len(con_medida) > 1 else None
            if tamanos:
                for k, i in enumerate(con_medida):
                    salida[i] = f"{nombre} {tamanos[k]}"
                pendientes = [i for i in pendientes if i not in salida]
                if not pendientes:
                    continue
        etiquetas = {i: vecina(i, -1) for i in pendientes}
        repetida = lambda e: e is None or list(etiquetas.values()).count(e) > 1
        if any(repetida(e) for e in etiquetas.values()):
            etiquetas = {i: (e if not repetida(e) else vecina(i, 1)) for i, e in etiquetas.items()}
        for i in pendientes:
            etiqueta = etiquetas.get(i)
            if etiqueta:
                va_con[i] = etiqueta[:1].upper() + etiqueta[1:]
    return salida, va_con


# Diámetro exterior de los rodamientos de bolas por serie (60xx, 62xx, 63xx) y código de interior
_EXTERIOR = {"60": {0: 26, 1: 28, 2: 32, 3: 35, 4: 42, 5: 47, 6: 55},
             "62": {0: 30, 1: 32, 2: 35, 3: 40, 4: 47, 5: 52, 6: 62},
             "63": {0: 35, 1: 37, 2: 42, 3: 47, 4: 52, 5: 62, 6: 72}}


def _medida(parte):
    """Clave de tamaño desde los detalles técnicos: '6x16' → (6, 16) (diámetro y largo); '6202' (rodamiento) → (15,)
    (diámetro interior según su referencia); '28x68x18' → (28, 68, 18)."""
    tecnico = (parte.get("tecnico") or "").split("·")[0].strip()
    yamaha = re.match(r"93306-(\d)(\d\d)", parte.get("codigo") or "")     # Yamaha: 93306-302YU = rodamiento 6302
    if yamaha and not tecnico and int(yamaha.group(2)) <= 20:
        tecnico = f"6{yamaha.group(1)}{yamaha.group(2)}"
    ref = re.search(r"\b(6[023])(\d\d)\b", tecnico)
    if ref:                                                      # rodamiento: tamaño = (diámetro exterior, interior)
        serie, codigo = ref.group(1), int(ref.group(2))
        interior = {0: 10, 1: 12, 2: 15, 3: 17}.get(codigo, codigo * 5)
        exterior = _EXTERIOR.get(serie, {}).get(codigo, interior * 2)
        return (exterior, interior)
    numeros = tuple(float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", tecnico))
    return numeros or None


def _por_tamano(piezas):
    """Si todas tienen una medida distinta: ['grande', 'mediano', 'pequeño'...] en el orden de `piezas`; si no, None."""
    medidas = [_medida(p) for p in piezas]
    if None in medidas or len(set(medidas)) < len(medidas):
        return None
    orden = sorted(range(len(piezas)), key=lambda k: medidas[k], reverse=True)
    n = len(piezas)
    if n == 2:
        palabras = ["grande", "pequeño"]
    elif n == 3:
        palabras = ["grande", "mediano", "pequeño"]
    else:
        palabras = ["más grande"] + [f"mediano {k}" for k in range(1, n - 1)] + ["más pequeño"]
    resultado = [None] * n
    for puesto, k in enumerate(orden):
        resultado[k] = palabras[puesto]
    return resultado


# ---------------------------------------------------------------------------
# Nombres limpios: sin códigos pegados, guiones sueltos ni abreviaturas del catálogo
# ---------------------------------------------------------------------------
_CODIGO = re.compile(r"^(?:[A-Za-z]{0,4}\d{5,}[A-Za-z0-9/]*|[A-Za-z]{2,3}\d{3,}[A-Za-z0-9]*)\s+")
_ABREVIATURAS = [(r"\bdel\.", "delantera"), (r"\btras\.", "trasera"), (r"\bder\.", "derecha"), (r"\bizq\.", "izquierda"),
                 (r"\bdistrib\b\.?", "distribución"), (r"\bcto\b\.?", "completo"), (r"\bcomplt\b\.?", "completo"),
                 (r"\barand\b\.?", "arandela"), (r"\btorn\b\.?", "tornillo"), (r"\bsal\b\.?", "salida"),
                 (r"\bkit piston\b", "kit de pistón"), (r"\bkit anillos\b", "juego de anillos"), (r"\bjgo\b\.?", "juego de"),
                 (r"\bpiston\b", "pistón"), (r"\bvalvula\b", "válvula"), (r"\bvalvulas\b", "válvulas"), (r"\breten\b", "retén"),
                 (r"\bciguenal\b", "cigüeñal"), (r"\bbalancin\b", "balancín"), (r"\bbujia\b", "bujía"),
                 (r"\brodamiento bolas\b", "rodamiento de bolas"), (r"\s*\b(std|standard)\b\.?", "")]


def limpiar_nombre(nombre):
    """'Dk181012 pin cilindro tubo -' → 'Pin cilindro tubo'; 'Piñón de 2a. (17t) -' → 'Piñón de 2a. (17T)'."""
    n = (nombre or "").strip()
    n = re.sub(r"(?:\s*[-–]\s*)+$", "", n)                     # guiones sueltos al final
    n = re.sub(r"^(?:[-–]\s*)+", "", n)
    while _CODIGO.match(n):                                    # códigos pegados al principio
        n = _CODIGO.sub("", n, count=1)
    n = re.sub(r"\s*\bx\s+hasta\s+modelo\b", " · modelos anteriores", n, flags=re.I)
    n = re.sub(r"\s*\bx\s+desde\s+modelo\b", " · modelos nuevos", n, flags=re.I)
    for patron, reemplazo in _ABREVIATURAS:
        n = re.sub(patron, reemplazo, n, flags=re.I)
    n = re.sub(r"\((\d+)\s*t\)", r"(\1T)", n, flags=re.I)        # dientes: (22T)
    n = re.sub(r"\b(\d+)l\b", r"\1L", n)                         # eslabones: 120L
    n = re.sub(r"\s+x\s+", " × ", n)
    n = re.sub(r"\.\(", ". (", n)
    n = re.sub(r"\s{2,}", " ", n).strip(" -–·")
    return n[:1].upper() + n[1:] if n else n


# Detalles técnicos (medidas, dientes, eslabones, referencias, amperaje, modelos): van a la guía, no al nombre
_DETALLE = re.compile(
    r"\(([^)]*)\)"                                                    # lo que va entre paréntesis
    r"|·\s*(modelos (?:anteriores|nuevos))"                           # variante por modelo
    r"|\b((?:[A-Za-z]{0,3}\d+[A-Za-z0-9./-]*)(?:\s*[×x]\s*[A-Za-z]{0,2}\d+[A-Za-z0-9./-]*)*(?:\s*(?:mm|cm|m)\b\.?)?)",
    re.I)
_ORDINAL = re.compile(r"^\d{1,2}(?:a|o|ra|da|ta|na)\.?$")          # "2a." (segunda) sí es parte del nombre; "15A" no


def _es_dato(texto):
    """Un detalle técnico de verdad: medida, dientes, referencia o modelo (tiene números o dice "modelos")."""
    if re.fullmatch(r"\d+\s*(?:ST|ND|RD|TH)", texto.strip(), flags=re.I):
        return False                                   # "5TH" es parte del nombre (quinta), no un dato
    return bool(re.search(r"\d", texto)) or texto.lower().startswith("modelos")


def _formato_dato(texto):
    """'12T/56T' → '12 y 56 dientes'; '35T' → '35 dientes'; 'NT:24' → '24 dientes'."""
    t = re.sub(r"\bNT\s*:\s*(\d+)", r"\1T", texto.strip(), flags=re.I)
    dientes = re.fullmatch(r"(\d+)\s*T(?:\s*/\s*(\d+)\s*T)?", t, flags=re.I)
    if dientes:
        a, b = dientes.groups()
        return f"{a} y {b} dientes" if b else f"{a} dientes"
    return t


_SOBREMEDIDAS = {"0.25", "0.50", "0.75", "1.00", "0,25", "0,50", "0,75", "1,00"}
_PIEZAS_CON_SOBREMEDIDA = re.compile(r"(PIST|ANILLO|RING|CILINDRO|CYLINDER|BIELA|CIGUE|CRANK|METAL|BEARING, ?CON)", re.I)


def datos_tecnicos(nombre, descripcion, codigo=""):
    """Datos para la guía, siempre con la misma etiqueta según su tipo: [("Medidas", "6 × 16 mm"), ("Dientes", "35")...].

    Solo lo que se reconoce: medidas (diámetro × largo), dientes, referencia del rodamiento, sobremedida (pistón,
    anillos), paso y eslabones de la cadena, medida de la llanta, amperaje, referencia de la bujía y modelos a los
    que aplica. Lo demás (códigos de modelo como "125CGR", sinónimos) no se muestra."""
    texto = f"{nombre or ''} {descripcion or ''}"
    alto = texto.upper()
    datos = []

    def poner(etiqueta, valor):
        if valor and all(e != etiqueta for e, _ in datos):
            datos.append((etiqueta, valor))
    # Cadena: "428 × 120L", "520x108L" → paso y eslabones
    cadena = re.search(r"\b(41[05]|42[08]|520|525|530)\s*[X×H]?\s*[X×]?\s*(\d{2,3})\s*L\b", alto)
    if cadena:
        poner("Paso de cadena", cadena.group(1))
        poner("Eslabones", cadena.group(2))
    # Dientes: "(35T)", "12T/56T", "NT:24", "14/42T"
    d2 = re.search(r"\b(\d{1,3})\s*T?\s*/\s*(\d{1,3})\s*T\b", alto)
    d1 = re.search(r"(?:\bNT\s*:\s*|\b)(\d{1,3})\s*(?:T|DIENTES)\b", alto)
    if d2:
        poner("Dientes", f"{d2.group(1)} y {d2.group(2)}")
    elif d1 and not cadena:
        poner("Dientes", d1.group(1))
    # Rodamiento: referencia ISO (6302, 6004C3) o el código Yamaha 93306-302YU
    ref = re.search(r"\b(6[0-3]\d\d)(?:[- ]?(?:2RS|ZZ|Z|C3|RS))*\b", alto)
    yamaha = re.match(r"93306-(\d)(\d\d)", codigo or "")
    if ref and re.search(r"(RODAMIENTO|BALINERA|BEARING)", alto):
        poner("Rodamiento", ref.group(1))
    elif yamaha and int(yamaha.group(2)) <= 20:
        poner("Rodamiento", f"6{yamaha.group(1)}{yamaha.group(2)}")
    # Llanta: "100/80-17", "3.00-18"
    llanta = re.search(r"\b(\d{2,3}/\d{2,3}[- ]?(?:R)?\d{2}|\d\.\d{2}-\d{2})\b", alto)
    if llanta:
        poner("Medida de llanta", llanta.group(1))
    # Fusible
    amp = re.search(r"\b(\d{1,2}(?:[.,]\d)?)\s*A\b", alto)
    if amp and re.search(r"(FUS|FUSE)", alto):
        poner("Amperaje", f"{amp.group(1).replace('.', ',')} A")
    # Bujía: referencia NGK/Denso/Champion
    bujia = re.search(r"\b([BCDX][A-Z]{0,3}\d{1,2}[A-Z]{1,4}(?:-\d{1,2}|-U)?)\b", alto)
    if bujia and re.search(r"(BUJ|SPARK PLUG|PLUG, SPARK)", alto):
        poner("Referencia de bujía", bujia.group(1))
    # Medidas: "6x16", "28x68x18", "M8 × 1.25 × 50" (tornillos, retenes, bujes, o-rings, separadores)
    if not cadena and not llanta and not _PIEZAS_CON_SOBREMEDIDA.search(alto):
        med = re.search(r"\bM?(\d{1,3}(?:[.,]\d{1,2})?)\s*[X×]\s*(\d{1,3}(?:[.,]\d{1,2})?)(?:\s*[X×]\s*(\d{1,3}(?:[.,]\d{1,2})?))?", alto)
        if med:
            poner("Medidas", " × ".join(n.replace(".", ",") for n in med.groups() if n) + " mm")
        else:
            mm = re.search(r"\b(\d{1,3}(?:[.,]\d)?)\s*MM\b", alto)
            if mm:
                poner("Medida", f"{mm.group(1).replace('.', ',')} mm")
    marca = marca_de(texto)
    if marca:
        poner("Marca/referencia", marca.title() if len(marca) > 3 else marca)
    # Variante por modelo
    modelo = re.search(r"modelos (anteriores|nuevos)", texto, re.I)
    if modelo:
        poner("Aplica a", f"modelos {modelo.group(1).lower()}")
    return datos


def texto_tecnico(datos):
    return " · ".join(v for _, v in datos)


# Nombres según el sistema: la misma palabra del catálogo significa otra cosa en otro conjunto. En la transmisión
# final de una automática (un reductor de dos etapas, sin marchas) "GEAR, 1ST WHEEL" es el engranaje conducido del
# eje de salida, no la "primera" de una caja de cambios.
NOMBRES_POR_SISTEMA = {
    # En la distribución, el "DAMPER, CHAIN" es la guía amortiguadora de la cadenilla (no el caucho de la cadena de arrastre)
    # Carburador: el "JET" es el chicler (no un inyector)
    "carburador": [("JET, MAIN", "Chicler de alta (principal)"), ("MAIN JET", "Chicler de alta (principal)"),
                   ("JET, PILOT", "Chicler de baja"), ("PILOT JET", "Chicler de baja")],
    # Variador en español de Yamaha Colombia: "contrapeso" son los rodillos y "leva", la rampa (solo en la CVT)
    "cvt": [("AMORT CONTRAPESO", "Caucho de las zapatas"), ("RESORTE CONTRAPESO", "Resorte de las zapatas"),
            ("CONTRAPESO", "Rodillos del variador"), ("LEVA", "Rampa del variador")],
    "distribucion": [("DAMPER, CHAIN", "Guía de la cadenilla"), ("CHAIN DAMPER", "Guía de la cadenilla"),
                     ("TENSOR CADENA", "Tensor de la cadenilla"), ("CADENA", "Cadenilla")],
    # Yamaha llama "BOLT, STRAIGHT SCREW" al tornillo de drenaje del aceite (con su empaque al lado)
    "carcasa": [("BOLT, STRAIGHT SCREW", "Tornillo de drenaje")],
    # Ruedas: la cámara (TUBE) es el neumático en Colombia; la llanta es la cubierta
    "rueda": [("TUBE, TIRE", "Neumático"), ("TUBE, TYRE", "Neumático"), ("TUBE (", "Neumático")],
    "rueda_trasera": [("TUBE, TIRE", "Neumático"), ("TUBE, TYRE", "Neumático"), ("TUBE (", "Neumático")],
    # Freno de tambor en español de Yamaha Colombia: el "árbol de levas" es la leva del freno
    "rueda_tambor": [("TUBE, TIRE", "Neumático"), ("TUBE, TYRE", "Neumático"), ("TUBE (", "Neumático"),
                     ("PALANCA DE ARBOL DE LEVAS", "Palanca del freno"), ("ARBOL DE LEVAS", "Leva del freno"),
                     ("PLACA INDICADOR", "Indicador de desgaste")],
    # En la parte eléctrica, las "correas" son amarras plásticas del cableado (no la correa del variador)
    "electrico": [("CORREA PL", "Amarra plástica del cableado"), ("KIT CORREAS", "Amarras plásticas del cableado")],
    # Clutch (Yamaha): "PLATE, CLUTCH" es el disco separador de acero; "PLATE, FRICTION", el de fricción
    "clutch": [("PLATE, FRICTION", "Disco de fricción"), ("FRICTION PLATE", "Disco de fricción"), ("PLATE, CLUTCH", "Disco separador"),
               ("PLATE, PRESSURE", "Plato de presión"), ("PRESSURE PLATE", "Plato de presión"), ("CUSHION", "Resorte amortiguador"),
               ("PLATE, SEAT", "Asiento del resorte amortiguador"), ("PLATE, THRUST", "Arandela de empuje"),
               ("PLATE, PUSH", "Placa de empuje"), ("SPRING, CLUTCH", "Resorte del clutch"), ("SCREW, SPRING", "Tornillo del resorte"),
               ("SPRING, RETURN", "Resorte de retorno")],
    "caja_secundaria": [("EJE PRINCIPAL", "Eje intermedio con piñón y engranaje"), ("EJE SECUNDARIO", "Eje de salida"),
                        ("ENGRANAJE RUEDA", "Engranaje conducido del eje de salida"), ("ENGRANAJE TRACC", "Piñón del eje primario"),
                        ("BOLT, STRAIGHT SCREW", "Tornillo de drenaje"), ("MAIN AXLE", "Eje intermedio con piñón y engranaje"), ("AXLE, DRIVE", "Eje de salida"),
                        ("DRIVE AXLE", "Eje de salida"), ("WHEEL", "Engranaje conducido del eje de salida"),
                        ("PRIMARY DRIVE", "Piñón del eje primario"), ("PRIMARY", "Piñón del eje primario"), ("PINION", "Piñón del eje intermedio"), ("OIL SEAL", "Retén"),
                        ("BEARING", "Rodamiento"), ("CIRCLIP", "Pin seguro")],
}


def nombre_por_sistema(diagrama, descripcion):
    texto = (descripcion or "").upper()
    return next((n for clave, n in NOMBRES_POR_SISTEMA.get(diagrama, []) if clave in texto), None)


# Lo que no es el nombre de la pieza: colores, normas y versiones (van en el catálogo, no en el nombre)
_RELLENO = re.compile(r"\b(negr[oa]|gris|roj[oa]|azul|blanc[oa]|plateado|plata|dorad[oa]|cromad[oa]|mate|brillante|euro\s*\d?|e\d|"
                      r"actual|nuevo modelo|original|gen[eé]rico|std|standard)\b\.?", re.I)
# Frases de catálogo sin preposiciones ("Eje rueda del") → español claro ("Eje de la rueda delantera")
_FRASES = [(r"\brueda del(?:\.|$|(?=\s+(?:completa?|cta|cto|izq|der|izquierd[oa]|derech[oa])\b))", "rueda delantera"), (r"\brueda tras\b\.?", "rueda trasera"), (r"\brin del(?:\.|$|(?=\s+(?:completa?|cta|cto|izq|der|izquierd[oa]|derech[oa])\b))", "rin delantero"),
           (r"\brin tras\b\.?", "rin trasero"), (r"\beje rueda\b", "eje de la rueda"), (r"\bbuje rueda\b", "buje de la rueda"),
           (r"\bdisco freno\b", "disco de freno"), (r"\bsensor velocimetro\b", "sensor del velocímetro"),
           (r"\bvelocimetro\b", "velocímetro"), (r"\bcampana del(?:\.|$|(?=\s+(?:completa?|cta|cto|izq|der|izquierd[oa]|derech[oa])\b))", "campana delantera"), (r"\bcampana tras\b\.?", "campana trasera"),
           (r"\bjuego de radios del(?:\.|$|(?=\s+(?:completa?|cta|cto|izq|der|izquierd[oa]|derech[oa])\b))", "juego de radios delantero"), (r"\bjuego de radios tras\b\.?", "juego de radios trasero"),
           (r"\beje clutch completo\b", "eje principal completo"), (r"\beje clutch\b", "eje principal"),
           (r"\beje pi[ñn][oó]n salida\b", "eje de salida"), (r"\bbuje pi[ñn][oó]n salida\b", "buje del piñón de salida"),
           (r"\barandela pi[ñn][oó]n salida\b", "arandela del piñón de salida"), (r"\bpi[ñn][oó]n salida\b", "piñón de salida"),
           (r"\bbuje caja\b", "buje de la caja"), (r"\barandela caja\b", "arandela de la caja"), (r"\bpiñon\b", "piñón"),
           (r"\bneumati?c?o?\b", "neumático"),
           # Catálogo Yamaha Colombia en español (traducción automática de la marca): a nombres de taller
           (r"\bcerrojo,?\s*reborde hueco( profund\w*)?\b", "tornillo con pestaña"), (r"^perno,\s*de brida\b", "tornillo con pestaña"),
           (r"^tornillo,\s*de drenaje\b", "tornillo de drenaje"), (r"^anillo (en )?o\b", "o-ring"), (r"\bpasador,\s*de espiga\b", "guía de centrado"),
           (r"\bpasador,\s*pist[oó]n\b", "pasador del pistón"), (r"\btuerca de brida\b", "tuerca con pestaña"),
           (r"\btuerca auto(blocante|frenante)\b|\btuerca de auto-cierre\b", "tuerca autofrenante"),
           (r"\bjunta,\s*de culata\b", "empaque de la culata"), (r"\bjunta,\s*de cilindro\b", "empaque del cilindro"),
           (r"\b(perno )?perno prisionero\b|\bperno de puntal\b", "espárrago"),
           (r"^calibre completo\b", "caliper"), (r"\bfunda de calibre\b", "guardapolvo del caliper"), (r"^funda$", "guardapolvo"),
           (r"\bjuego de retenes de pinza\b", "kit de sellos del caliper"), (r"\bcjto\.? tornillo de purga\b", "purgador"),
           (r"\bjuego de cojin de freno\b", "pastillas de freno"), (r"\bsoporte de pastillas\b", "resorte de las pastillas"),
           (r"\bcilindro maestro completo\b", "bomba de freno"), (r"\bjuego de cilindro maestro\b", "kit de reparación de la bomba"),
           (r"\btapa de tanque de reserva\b", "tapa del depósito"), (r"\bempaque,\s*diafragma\b", "diafragma del depósito"),
           (r"\bsoporte de cilindro maestro\b", "abrazadera de la bomba"), (r"\binterrup\.? de parada delantero\b", "interruptor del stop"),
           (r"\btornillo con rondona\b", "tornillo con arandela"), (r"\bperno de union\b", "tornillo banjo"), (r"\bunidad de hidraulica\b", "unidad ABS"),
           (r"\brueda fundida trasera\b", "rin trasero"), (r"\brueda fundida delantera\b", "rin delantero"),
           (r"\bpasador pivote\b", "pasador de las bandas"), (r"\bjuego de zapata de freno\b", "bandas de freno"), (r"\bresorte de tension\b", "resorte de las bandas"),
           (r"\brotor de sensor\b|\bsensor del rotor\b", "disco del sensor (rueda fónica)"), (r"\bsello del aceite\b|\bsello aceite\b", "retenedor"),
           (r"\bcojinete de rodillos\b", "rodamiento de agujas"), (r"\bcojinete\b", "rodamiento"),
           (r"\broldana primaria movil\b", "polea móvil del variador"),            (r"\bcorredera\b", "deslizadores del variador"), (r"\bpisco fixador de porea\b", "polea fija del variador"),
           (r"\bportador de embrague completo\b", "clutch completo"), (r"\bzapata,\s*peso de embreagem\b", "zapatas del clutch"),
           (r"\bamort contrapeso embrague\b", "caucho de las zapatas"), (r"\bresorte contrapeso embrague\b", "resorte de las zapatas"),
           (r"\broldana secundaria fija compl?\.?", "polea fija trasera"), (r"\broldana secundaria corrediza\b", "polea móvil trasera"),
           (r"\basiento de resorte secundario\b", "asiento del resorte de torque"), (r"\bresorte secundario\b", "resorte de torque"),
           (r"\bcaja de embrague completo\b", "campana del clutch"), (r"\bcorrea en v\b", "correa de la transmisión"),
           (r"\bcasquillo solido\b", "buje"), (r"\bpresilla redonda\b", "pin seguro"), (r"^presilla$|^grampa$", "grapa"),
           (r"\btapon de drenaje\b", "tapón de drenaje"), (r"\bresorte de compresion\b", "resorte"),
           (r"\btapon del nivel de aceite\b", "tapón con varilla del aceite"), (r"^tapon de aceite$", "tapón del aceite"),
           (r"\btapa de carter derecha\b", "tapa derecha del cárter"), (r"\bmanguela\b", "manguera"), (r"^carter completo\b", "cárter"),
           (r"^multiple$", "múltiple de admisión"), (r"\bcaja de acelerador compl\w*\.?", "cuerpo de aceleración"), (r"\bresorte de embolo\b", "resorte del émbolo"),
           (r"^motor$", "motor de ralentí"), (r"\bcaja filtro del aire\b", "caja del filtro de aire"), (r"\btapa caja del filtro\b", "tapa de la caja del filtro"),
           (r"\bunion del filtro del aire\b", "unión del filtro de aire"), (r"\belemento del filtro del aire\b", "filtro de aire"),
           (r"\btornillo (redondo )?rosca hembra\b", "tornillo"), (r"\btubo,\s*drenaje\b", "manguera de drenaje"), (r"\bequilibrio,\s*cubierta\b", "caucho de la cubierta"),
           (r"\bbrida,\s*manguera\b", "abrazadera de la manguera"), (r"^(brida|banda)$", "abrazadera"),
           (r"\bculata de cilindro completa\b", "culata"), (r"\btapa culata de cilindro\b", "tapa de válvulas"), (r"\bplaca respiradero\b", "placa del respiradero"),
           (r"\bemapq\.? cbta\.?\s*de\s*resp\w*\.?", "empaque de la tapa del respiradero"), (r"\btornillo de reglaje\b", "tornillo de ajuste"),
           (r"\bsello de aceite v[aá]lvula\b", "sello de la válvula"), (r"\bresorte v[aá]lvula interna\b", "resorte de la válvula"),
           (r"\bseguro de v[aá]lvula\b", "cuñas de la válvula"), (r"\bret[eé]n resorte de v[aá]lvula\b", "platillo del resorte"),
           (r"\basiento resorte de v[aá]lvula\b", "asiento del resorte"), (r"\bbrazo de balanc[ií]n de v[aá]lvula\b", "balancín"),
           (r"\btornillo de ajuste de v[aá]lvula\b", "tornillo de calibración"), (r"\bpasador manivela\b", "pasador del cigüeñal"),
           (r"\bcuna woodruff\b", "cuña del cigüeñal"), (r"^juego de anillos$", "anillos del pistón"), (r"\barbol de levas completo\b", "árbol de levas"),
           (r"\bequipo de descompresion\b", "descompresor"), (r"\bleva de descompresion\b", "leva del descompresor"),
           (r"\btope de guia\b", "guía de la cadenilla"), (r"\btensor cadena de leva\b", "tensor de la cadenilla"), (r"\bempaque de caja tensor\b", "empaque del tensor"),
           (r"\btermostato conjunto\b", "termostato"), (r"^radiador completo$", "radiador"), (r"\btapon,\s*del radiador\b", "tapa del radiador"),
           (r"\bgrifo de drenaje\b", "tornillo de drenaje del refrigerante"), (r"\bcaja ventilador\b", "carcasa del ventilador"),
           (r"\bbomba de agua completa\b", "bomba de agua"), (r"\bcubierta de caja\b", "tapa de la bomba de agua"), (r"\beje impulsor completo\b", "eje de la bomba de agua"),
           (r"\bllave de ignicion compl\w*\b", "switch de encendido"), (r"\bcubierta interruptor princ\.?", "tapa del switch"), (r"\bconjunto de cables\b", "arnés"),
           (r"\bconjunto diodo\b", "diodo"), (r"\brele completo\b", "relé"), (r"\bunidad de control remoto compl\.?", "unidad de la llave inteligente"),
           (r"\bunidad control comunicacion\b", "unidad de conectividad"), (r"\bunidad de control del generad\w*", "unidad de control del motor (ECU)"),
           (r"\badmision\b", "admisión"), (r"\bguia\b", "guía"), (r"^boton\b", "botón"), (r"^tapon$", "tapón"),
           (r"\bbobina de encendido completa\b", "bobina de encendido"), (r"\btapon de buj[ií]a completo\b", "capuchón de la bujía"),
           (r"\bunidad termostato\b", "sensor de temperatura"), (r"\brele de destellador compl\.?", "relé de direccionales"), (r"\banillo goma\b", "caucho"),
           (r"^empaquetadura$", "empaque"), (r"\bhorquilla delantera compl\w*\.?", "barra de la suspensión"), (r"\btubo exterior derecho\b", "botella derecha de la suspensión"),
           (r"\btubo exterior izquierdo\b", "botella izquierda de la suspensión"), (r"\btubo exterior\b", "botella de la suspensión"),
           (r"\banillo de enganche\b", "pin seguro"), (r"\btubo interior completo\b", "tubo interior de la barra"),
           (r"\bcilindro compl de horq delant\b", "cilindro amortiguador de la barra"), (r"\bresorte de subensamble\b", "resorte de rebote"),
           (r"\btornillo cabezahexagonal\b", "tornillo"), (r"\bresorte horquilla delant\.?", "resorte de la barra"), (r"\bperno de tapa\b", "tapón de la barra"),
           (r"\bplatina inferior completa\b", "tijera inferior con la espiga"), (r"\bpista de bolas\b", "taza de la dirección"),
           (r"\bret[eé]n de cojinete\b", "canastilla de la dirección"), (r"\bcubierta de base de bola\b", "tapa de la taza"), (r"\barandela de plana\b", "arandela"),
           (r"\bsoporte de manguera freno\b", "soporte de la manguera de freno"), (r"\bbrazo posterior\b", "basculante"),
           (r"\bamortiguador trasero completo\b", "amortiguador trasero"),
           # Abreviaturas y orden inglés en nombres de empaques
           (r"\bde admisi[oó]n del tubo\b", "del tubo de admisión"), (r"\bpulverizad\b", "pulverizador"), (r"\bcarb\b\.?", "carburador"),
           (r"^sensor carburador\s*-\s*map\b", "sensor MAP (presión de admisión)"), (r"^inyector (de )?aceite\b", "surtidor de aceite"),
           (r"^rodillo eje (clutch|principal)\b", "rodamiento de agujas del eje principal"), (r"^jet,?\s*main\b", "chicler de alta (principal)"),
           (r"\bguardap\b\.?\s*ti\b", "guardapolvo de la tijera"), (r"^bolt[- ]washer\b", "tornillo con arandela"),
           (r"^kit bujes amortiguador tras(era|ero)?\b\.?", "kit de bujes del amortiguador trasero"),(r"\bbalan\b", "balancín"),(r"\baguja aire\b", "tornillo de aire"), (r"\btapon tiempo\b", "tapón de tiempo"),
           (r"\bconector cilindro\b", "conector del cilindro"), (r"^empaque del aceite$", "empaque del conducto de aceite"),
           (r"^sello motriz del eje$", "retenedor del eje de salida"), (r"^sello del aceite$", "retenedor"),
           # Restos del amperaje ("Fusible A", "Fusible , A"): el amperaje va en la guía
           (r"^fusible[\s,.()\-]*(?:a\b[\s\-]*(?:bl)?)?\s*$", "fusible"), (r"\bcaja\s+(?:de\s+)?fusibles?\b", "caja de fusibles"),
           (r"\bsoporte\s+caja de fusibles\b", "soporte de la caja de fusibles"),
(r"^sello para polvo$", "guardapolvo de la dirección"), (r"\bouter comp\.?\s*clutch\b", "canasta del clutch"), (r"\b(ktl|india)\b", ""), (r"\banti\s*-\s*", "anti"),
           (r"\bprenscluslicgr\b", "plato de presión del clutch"), (r"\bouter ?clutch\b", "canasta del clutch"),
           (r"\s*\b(slipper|sliper|slip|carbx)\b", ""), (r"\bmeditor\b", "medidor"), (r"\bconj\.?(?=\s)", "conjunto de"),
           (r"\bmanzan?\b", "manzana"), (r"\bmanz\b", "manzana"),
           (r"\b(corona interna|corona|manzana|disco|discos|campana|empujador|impulsor|espaciador|portadiscos|presionador|prensa|"
            r"platina|portabalinera|separador|porta resortes?|leva interna|pin prensa|piñón corona|buje corona|arandela campana|"
            r"arandela corona|juego de discos|kit discos|disco separador|discos metálicos)\s+(del\s+)?clutch\b", r"\1 del clutch"), (r"\bjuego de disco separadores\b", "juego de separadores"),
           (r"\bdel neumático (interior )?de la suspensión\b", "de la barra de la suspensión"), (r"^tubo interior$", "tubo interior de la barra"),
           (r"^pieza (delantera )?de seguridad del aceite.*", "copa de bloqueo de aceite"),
           (r"^pieza de deslizamiento\b.*", "bujes deslizantes de la barra"), (r"\bembudo para aire\b", "embudo de aire"),
           (r"\bkit arbol\b", "kit del árbol de levas"), (r"\bkit balin\b", "kit de balines"), (r"\bbuje tijera\b", "buje de la tijera"),
           (r"\btuerca de auto ?cierre\b", "tuerca autofrenante"), (r"\bauto ?cierre\b", "autofrenante"), (r"\bmanivela semi ?armada\b", "cigüeñal"),
           (r"\bbobina pick ?up\b", "bobina captadora (pulsador)"), (r"\bconector termostato radiador\b", "manguera del termostato al radiador"),
           (r"\bsoporte manguera\b", "soporte de la manguera"), (r"\bseparad\b\.?", "separador"), (r"\bseparador clutch\b", "separador del clutch"),
           (r"\bplatina tensor cadena\b", "platina del tensor de cadena"), (r"\bcollar de (la )?rueda\b", "separador de la rueda"),
           (r"\bcubierta para polvo\b", "guardapolvo"), (r"\bset empaques medio\b", "juego de empaques del motor (medio)"),
           (r"\bset\b", "juego de"), (r"\bcir ?clip\b", "pin seguro"), (r"\bcabrecadena\b", "guardacadena"), (r"\bcubrecadena\b", "guardacadena"),
           (r"\bbalinera rueda\b", "balinera de la rueda"), (r"\bbateria\b", "batería"),
           (r"\bconector termostato\s*-\s*(radiador|motor|conducto)\b", r"manguera del termostato al \1"),
           (r"\basamblea de\s+", ""),
           (r"\bcollar distanciador\b", "separador"), (r"\bcollar,?\s*eje de rueda dentada\b", "separador del eje del piñón"),
           (r"\bcollar,?\s*varilla\b", "buje de la varilla"), (r"\bcollar\b", "buje"),
           (r"\bdel$", "delantero"), (r"\btras$", "trasero"), (r"\bizq$", "izquierdo"), (r"\bder$", "derecho")]


_MARCHA = {"1": "primera", "2": "segunda", "3": "tercera", "4": "cuarta", "5": "quinta", "6": "sexta"}
_INGLES = re.compile(r"\b(assy|comp|sub|bolt|screw|nut|washer|gear|shaft|cover|case|plate|spring|seal|holder|bracket|pipe|hose|"
                     r"muffler|wheel|front|rear|left|right|crank)\b", re.I)


def _marchas(n):
    """Piñones de la caja: '2da', '4a', '3ra' → 'de segunda'; 'salida' / 'rueda' = eje secundario; 'clutch' / 'piñón' = eje principal."""
    if re.search(r"(?i)fusible", n):
        return re.sub(r"(?i)\s*\b\d{1,2}(?:[.,]\d)?\s*a\b", "", n)           # el amperaje va en la guía
    doble = re.search(r"(?i)\b([1-6])\s*a\s*(?:&|y)\s*([1-6])\s*a\b", n)
    if doble:
        return f"Piñón doble de {_MARCHA[doble.group(1)]} y {_MARCHA[doble.group(2)]}"
    m = re.search(r"(?i)\b(?:de\s+)?([1-6])\s*(?:a|ra|da|ta|na|o)\b\.?", n)
    if not m or not re.search(r"(?i)(pi[ñn][oó]n|engranaje|buje|arandela)", n):
        return n
    marcha = "de " + _MARCHA[m.group(1)]
    resto = (n[:m.start()] + " " + n[m.end():]).strip()
    eje = ""
    if re.search(r"(?i)\b(salida|rueda|conducid)", resto):
        eje = " del eje secundario"
    elif re.search(r"(?i)\b(clutch|principal|motriz)\b", resto) or re.search(r"(?i)engranaje\s+(de\s+)?pi[ñn][oó]n", resto):
        eje = " del eje principal"
    base = re.sub(r"(?i)\b(engranaje\s+(de\s+)?(pi[ñn][oó]n|rueda)|pi[ñn][oó]n\s+caja|pi[ñn][oó]n)\b", "Piñón", resto)
    base = re.sub(r"(?i)\b(de\s+)?(salida|rueda|clutch|principal|caja)\b", " ", base)
    base = re.sub(r"\s{2,}", " ", base).strip(" de")
    if re.match(r"(?i)buje|arandela", base):
        base = re.sub(r"(?i)\s*pi[ñn][oó]n\b", "", base).strip()
        return f"{base} del piñón {marcha}{eje}"
    return f"Piñón {marcha}{eje}" + (f" ({base[6:].strip()})" if base.lower().startswith("piñón ") and base[6:].strip() else "")


# Modelos AKT que aparecen en los nombres aunque no sean de esta moto ("Conector carburador CGR"), con su cilindraje
_MODELOS = re.compile(r"(?i)\b(?:\d{3}\s*/?\s*)?(?:CGR|TTR|TTX|SLR|SL|NKD|R3|CR4|CR5|J4|GY6|ANA|AHO|EVO|SC|DS|XM)\d*(?:\s*/\s*\d{3})?\b")
# Abreviaturas de catálogo → palabra completa (los acabados como "cromo" o "zinc" no van en el nombre)
_ABREV = [(r"camp", "de pestaña"), (r"carcaza", "carcasa"), (r"empaq", "empaque"), (r"int", "interior"), (r"ext", "exterior"),
          (r"inf", "inferior"), (r"sup", "superior"), (r"izq", "izquierdo"), (r"der", "derecho"), (r"trans", "transmisión"),
          (r"tra", "trasero"), (r"tras", "trasero"), (r"buj", "buje"), (r"depos", "depósito"), (r"resp", "respiradero"),
          (r"manig", "manigueta"), (r"elem", "elemento"), (r"veloc", "velocímetro"), (r"guardab", "guardabarro"),
          (r"susp", "suspensión"), (r"cto", "completo"), (r"cta", "completa"), (r"arand", "arandela"),
          (r"conex", "conexión"), (r"mang", "manguera"), (r"guardap", "guardapolvo"), (r"calip", "caliper")]
_ACABADOS = re.compile(r"(?i)\b(cromo|cromad[oa]|zinc|zincad[oa]|antiox|pav|pavonad[oa]|inox)\b\.?")


# Marcas y líneas de fabricantes de repuestos: no van en el nombre (van en la guía, como "Marca/referencia")
_MARCAS = re.compile(r"(?i)\b(MRF|REVZ|IRC|QUEEN|ATT|ZAPPER(?:\s*FS)?|NGP(?:-?PLUS\w*)?|SPORT\s+DEMON|JET\s*4\s*XR|RX\s*01|NGK|CHAMPION|BOSCH|"
                     r"DENSO|KONTROL|YUASA|DID|STAR|TRACTO|LGB|CHOHO|AKT|NBC|NTN|SKF|MONONITROX|MRS[-\s]?STEEL|SHOWA|GABRIEL|ENDURANCE|"
                     r"KENDA|CHENG\s+SHIN|FENNER|ARAI|ARS|NOK|TVS|CEAT|MAXXIS|TIMSUN|PIRELLI|METZELER|MICHELIN|DUNLOP|VEE\s*RUBBER|"
                     r"KOYO|FAG|NACHI|NSK|TM\s*\d+|NR\s*-?\d+|MR\s*-?\d*|FS\s*-?\s*TT|TT|TL)\b")
_MARCAS_VALIDAS = re.compile(r"(?i)^emblema\b")         # "Emblema Yamaha": la marca es la pieza


def marca_de(texto):
    """Primera marca de repuesto en el texto (para la guía), o None."""
    m = _MARCAS.search(texto or "")
    return m.group(0).strip().upper() if m and not re.fullmatch(r"(?i)(TT|TL|MR\s*-?\d*|NR\s*-?\d+|TM\s*\d+|FS\s*-?\s*TT)", m.group(0).strip()) else None


def _lado_rueda(nombre, descripcion, pieza, lamina=""):
    """Delantera o trasera de una llanta, rin o neumático: por la descripción, la pieza de la lámina o la medida."""
    t = (descripcion or "").upper() + " " + (nombre or "").upper()
    if re.search(r"\b(DEL|DELANTER[OA]|FR|FRONT)\b", t):
        return "del"
    if re.search(r"\b(TRAS|TRASER[OA]|RR|REAR)\b", t):
        return "tras"
    delantera = re.search(r"\b(2[.,]?75|2[.,]?50|80/100|90/90-19|100/80)", t)
    trasera = re.search(r"\b(3[.,]?00|3[.,]?25|110/|120/|130/|140/)", t) or re.search(r"\d-(3[.,]?00|300)", t)
    combinada = re.search(r"(?i)\b(rines|ruedas|llantas)\b|\sy\s", lamina or "")   # lámina con las dos ruedas
    if combinada or not pieza:
        if delantera and trasera:
            return None                                  # "Neumático 275-300x18": sirve para las dos
        if delantera or trasera:
            return "del" if delantera else "tras"
    if pieza in ("llanta_del", "freno_del"):
        return "del"
    if pieza in ("llanta_tras", "freno_tras"):
        return "tras"
    if delantera and not trasera:
        return "del"
    if trasera and not delantera:
        return "tras"
    return None


def quitar_modelo(nombre, linea="", descripcion="", pieza=None, lamina=""):
    """Quita del nombre el modelo de la moto ("NKD", "125", "CR4"), colores, normas y versiones, y completa frases cortas."""
    n = nombre or ""
    # Guiones entre palabras de los catálogos AKT/Auteco ("Kit-arbol", "Buje-tijera") → espacios
    n = re.sub(r"(?i)(?<=[a-záéíóúñ])-(?=[a-záéíóúñ])", " ", n)
    # Nombres que quedaron en inglés o que son un código: la traducción por palabras de la descripción del catálogo
    if descripcion and (_INGLES.search(n) or re.fullmatch(r"[A-Za-z]{0,3}[\d-]{5,}[A-Za-z0-9]*", n.strip())):
        from .despiece_traductor import traducir_palabras
        n = traducir_palabras(descripcion) or n
    n = re.sub(r"(?i)\bcylindro maestro trasero\b", "Bomba de freno trasera", n)
    n = re.sub(r"(?i)^\s*12\s*v\s*\(?gel\)?", "Batería de gel", n)
    n = re.sub(r"(?i)\s+(sub\s+)?(assy|comp)\b\.?", "", n)
    n = re.sub(r"(?i)\s+(d=\s*)?x\s*$", "", n)                                 # restos de "x Hasta Modelo"
    n = re.sub(r"(?i)\b(cdi|ecu|abs|tps|led)\b", lambda m: m.group(1).upper(), n)
    n = _marchas(n)
    n = _MODELOS.sub(" ", n)
    if not _MARCAS_VALIDAS.match(n):
        n = _MARCAS.sub(" ", n)
    if _MARCAS_VALIDAS.match(n):
        n = re.sub(r"\s+", " ", n.replace(",", " ")).strip()
        n = re.sub(r"(?i)\b(yamaha|honda|suzuki|bajaj|hero|pulsar)\b", lambda m: m.group(1).capitalize(), n)
        n = re.sub(r"(?i)\b(ktm|tvs|akt)\b", lambda m: m.group(1).upper(), n)
    # Restos de catálogo: "#", "Rp", paréntesis sin cerrar, "derecha - izquierda" (si van los dos lados, no va lado)
    n = re.sub(r"\s*#\s*\d*", " ", n)
    n = re.sub(r"(?i)\s+rp\b", " ", n)
    n = re.sub(r"\s*\([^)]*$", "", n)
    n = re.sub(r"(?i)\b(derech[oa]|izquierd[oa])\s*-\s*(izquierd[oa]|derech[oa])\b", " ", n)
    n = re.sub(r"(?i)\s+(der|izq)\.?\s*-\s*(izq|der)\.?\b", " ", n)
    n = _ACABADOS.sub(" ", n)
    for abrev, completa in _ABREV:
        n = re.sub(rf"(?i)\b{abrev}\b\.?(?=\s|$)", completa, n)
    n = re.sub(r"(?i)\bdel\.(?=\s|$)|\bdel$", "delantero", n)
    n = re.sub(r"(?i)\bdelantero\b(?=.*\bdelantero\b)", "", n)            # "del" ya expandido no se repite
    # 4) Rodamientos nombrados solo por su referencia ("6002 2RS C3"): "Rodamiento" (la referencia va en la guía)
    if re.match(r"^\s*6[0-3]\d\d\b", n):
        n = "Rodamiento"
    for palabra in re.findall(r"[A-Za-z0-9-]+", linea or ""):
        if len(palabra) >= 2 and not palabra.lower() in ("de", "la", "el", "y"):
            n = re.sub(rf"(?i)\b{re.escape(palabra)}\b", " ", n)
    n = re.sub(r"(?i)\b\d{2,3}(?:cc|[a-z]{1,4})?\b(?=\s*$)", " ", n)       # cilindraje o código al final ("125CGR")
    n = _RELLENO.sub(" ", n)
    # Medidas o referencias pegadas al nombre ("Llanta trasera110x80", "Retén leva clutch12x18x4"): van en la guía
    n = re.sub(r"(?i)([a-záéíóúñ])(\d)", r"\1 \2", n)
    sin_numeros = re.sub(r"\s*\b[\w./+-]*\d[\w./+-]*", "", n).strip(" -–·,/()")
    if len(sin_numeros) >= 3:
        n = sin_numeros
    n = re.sub(r"\s{2,}", " ", n).strip(" -–·,/")
    for patron, cambio in _FRASES:
        n = re.sub(patron, cambio, n, flags=re.I)
    n = re.sub(r"\s{2,}", " ", n).strip(" -–·,/")
    # Llanta, rin y neumático: el nombre es la pieza y su posición, nada más (la marca y la medida van en la guía)
    base = re.match(r"(?i)^(llanta|rin|neum[aá]tico)\b", n)
    if base:
        palabra = {"llanta": "Llanta", "rin": "Rin"}.get(base.group(1).lower(), "Neumático")
        lado = _lado_rueda(n, descripcion, pieza, lamina)
        fem = palabra == "Llanta"
        n = palabra + ("" if not lado else (" delantera" if fem else " delantero") if lado == "del" else (" trasera" if fem else " trasero"))
    # Un nombre que es solo un código: el de la pieza según su lámina, nunca el código
    if not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3}", n.replace("Pieza", "")):
        if re.search(r"\d+\s*/\s*\d+", descripcion or "") and re.search(r"(?i)rueda|arrastre", lamina or ""):
            n = "Kit de arrastre"
        else:
            n = f"Pieza de {lamina.lower()}" if lamina else "Pieza"
    return n[:1].upper() + n[1:] if n else (nombre or "")


def separar_nombre(nombre):
    """('Cadena star 428 × 120L', '') → ('Cadena star', '428 × 120L'). Devuelve (nombre corto, detalles técnicos)."""
    limpio = limpiar_nombre(nombre)
    detalles = []

    def quitar(m):
        texto = next(g for g in m.groups() if g is not None).strip()
        if _ORDINAL.match(texto):
            return m.group(0)
        if texto:
            detalles.append(texto)
        return " "
    corto = _DETALLE.sub(quitar, limpio)
    detalles = [d for d in detalles if _es_dato(d)]
    corto = re.sub(r"\s{2,}", " ", corto).strip(" -–·,.") or limpio
    if corto.isupper() or sum(c.isupper() for c in corto) > len(corto) * 0.6:   # nombres en mayúsculas → normal
        corto = corto.lower()
    corto = corto[:1].upper() + corto[1:]
    return corto, " · ".join(dict.fromkeys(detalles))
