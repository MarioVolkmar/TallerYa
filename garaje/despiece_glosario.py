"""Nombres en español para las descripciones de los catálogos de partes (inglés técnico).

Buscamos nombres que un motociclista reconozca en el taller: precisos, pero sin jerga de ingeniería.
- traducir(descripcion) → nombre en español (con lado, medida o referencia cuando aporta).
- ayuda_para(descripcion) → explicación corta para las piezas de mantenimiento ("" si no hay).
"""
import re

# Clave: descripción del catálogo normalizada (ver _normalizar). Valor: nombre en español.
_NOMBRES = {
    # Frenos
    "BRAKE PAD KIT": "Pastillas de freno (juego)",
    "DISK, BRAKE": "Disco de freno",
    "DISK, REAR BRAKE": "Disco de freno trasero",
    "CALIPER ASSY": "Caliper de freno completo",
    "CALIPER ASSY, REAR": "Caliper de freno trasero completo",
    "PISTON ASSY, CALIPER": "Pistón del caliper",
    "CALIPER SEAL KIT": "Kit de empaques del caliper",
    "BLEED SCREW KIT": "Purgador del freno",
    "BOOT, CALIPER": "Guardapolvo del caliper",
    "BOOT": "Guardapolvo",
    "PIN, PAD": "Pasador de las pastillas",
    "SUPPORT, PAD": "Lámina soporte de las pastillas",
    "SHIM, CALIPER": "Lámina antirruido del caliper",
    "SUPT. BRKT. ASSY": "Soporte del caliper",
    "MASTER CYLINDER ASSY": "Bomba de freno delantera",
    "RR. MASTER CYLINDER ASSY": "Bomba de freno trasera",
    "CYLINDER KIT, MASTER": "Kit de reparación de la bomba de freno",
    "CAP, RESERVOIR": "Tapa del depósito de líquido de frenos",
    "DIAPHRAGM, RESERVOIR": "Diafragma del depósito de frenos",
    "PLATE, DIAPHRAGM": "Placa del diafragma",
    "BRACKET, MASTER CYLINDER": "Abrazadera de la bomba de freno",
    "HOSE, BRAKE": "Manguera de freno",
    "HOLDER, BRAKE HOSE": "Soporte de la manguera de freno",
    "BOLT, UNION": "Tornillo banjo de la manguera",
    "LEVER": "Manigueta",
    "BOLT, LEVER": "Tornillo de la manigueta",
    "FRONT STOP SWITCH ASSY": "Interruptor de la luz de freno delantero",
    "STOP SWITCH ASSY": "Interruptor de la luz de freno",
    "ROTOR, SENSOR": "Anillo sensor del ABS",

    # Transmisión CVT y clutch
    "V-BELT": "Correa del variador (CVT)",
    "WEIGHT SET": "Rodillos del variador (juego)",
    "PRIMARY SLIDING SHEAVE COMP": "Polea móvil del variador",
    "SHEAVE, PRIMARY FIXED": "Polea fija del variador (con ventilador)",
    "SLIDER": "Deslizador del variador",
    "CAM": "Rampa del variador",
    "CLUTCH CARRIER ASSY": "Clutch centrífugo completo",
    "CLUTCH WEIGHT SHOE SET": "Zapatas del clutch (juego)",
    "DAMPER, CLUTCH WEIGHT": "Caucho de las zapatas",
    "SPRING, CLUTCH WEIGHT": "Resorte de las zapatas",
    "CLUTCH HOUSING COMP": "Campana del clutch",
    "SECONDARY FIXED SHEAVE COMP": "Polea fija trasera (del clutch)",
    "SECONDARY SLIDING SHEAVE": "Polea móvil trasera (del clutch)",
    "SPRING, SECONDARY": "Resorte de torque del clutch",
    "SEAT, SECONDARY SPRING": "Base del resorte de torque",
    "CIRCLIP, CLUTCH": "Pin seguro del clutch",
    "DAMPER, PLATE": "Caucho de la placa",

    # Motor, culata y válvulas
    "CYLINDER HEAD ASSY": "Culata completa",
    "CYLINDER": "Cilindro",
    "COVER, CYLINDER HEAD": "Tapa de válvulas",
    "GASKET, CYLINDER": "Empaque del cilindro",
    "GASKET, CYLINDER HEAD": "Empaque de la culata",
    "GASKET, HEAD COVER": "Empaque de la tapa de válvulas",
    "PLUG, SPARK": "Bujía",
    "VALVE, INTAKE": "Válvula de admisión",
    "VALVE, EXHAUST": "Válvula de escape",
    "VALVE ROCKER ARM ASSY": "Balancín de válvula",
    "SHAFT, ROCKER": "Eje del balancín",
    "SCREW, VALVE ADJUSTING": "Tornillo de calibración de válvula",
    "SPRING, VALVE INNER": "Resorte de válvula",
    "SEAT, VALVE SPRING": "Base del resorte de válvula",
    "RETAINER, VALVE SPRING": "Platillo del resorte de válvula",
    "LOCK, VALVE SPRING RETAINER": "Cuñas de la válvula",
    "SEAL, VALVE STEM": "Sello de válvula (cauchito)",
    "GUIDE, VALVE": "Guía de válvula",
    "RING, PISTON": "Anillos del pistón",
    "BOLT, STUD": "Espárrago",
    "PIN, DOWEL": "Guía de centrado",

    # Lubricación
    "OIL PUMP ASSY": "Bomba de aceite",
    "STRAINER, OIL": "Malla del aceite",
    "PLUG,DRAIN": "Tapón de drenaje del aceite",
    "SPRING, COMPRESSION": "Resorte de la malla de aceite",

    # Admisión e inyección
    "ELEMENT, AIR CLEANER": "Filtro de aire",
    "CASE, AIR CLEANER": "Caja del filtro de aire",
    "CAP, CLEANER CASE": "Tapa de la caja del filtro de aire",
    "JOINT, AIR CLEANER": "Ducto del filtro al cuerpo de aceleración",
    "DUCT": "Ducto de aire",
    "THROTTLE BODY ASSY": "Cuerpo de aceleración",
    "MANIFOLD": "Múltiple de admisión",
    "GASKET, MANIFOLD": "Empaque del múltiple de admisión",
    "INJECTOR": "Inyector",
    "INJECTOR ASSY": "Inyector completo",
    "STEPPING MOTOR": "Motor de ralentí",
    "SPRING, PLUNGER": "Resorte del émbolo",
    "PIPE, BREATHER": "Manguera del respiradero",
    "PLATE, BREATHER": "Placa del respiradero",
    "GASKET, BREATHER COVER": "Empaque de la tapa del respiradero",
    "PIPE, DRAIN": "Manguera de drenaje",

    # Refrigeración
    "RADIATOR ASSY": "Radiador",
    "CAP, RADIATOR": "Tapa del radiador",
    "COVER, RADIATOR": "Rejilla del radiador",
    "THERMOSTAT ASSY": "Termostato",
    "COCK, DRAIN": "Tornillo de drenaje del refrigerante",
    "FAN": "Ventilador",
    "CASE, FAN": "Carcasa del ventilador",
    "HOSE CLAMP ASSY": "Abrazadera de manguera",

    # Ruedas
    "TIRE": "Llanta",
    "CAST WHEEL, FRONT": "Rin delantero",
    "CAST WHEEL, REAR": "Rin trasero",
    "AXLE, WHEEL": "Eje de la rueda",
    "VALVE, RIM": "Válvula de la llanta",
    "BEARING": "Rodamiento (balinera)",

    # Suspensión y dirección
    "FRONT FORK ASSY": "Barra de suspensión completa",
    "INNER TUBE COMP": "Barra cromada de la suspensión",
    "TUBE, OUTER": "Botella de la suspensión",
    "CYLINDER COMP., FRONT FORK": "Cilindro amortiguador de la barra",
    "SPRING, FRONT FORK": "Resorte de la barra",
    "SPRING, SUB": "Resorte auxiliar de la barra",
    "BOLT, CAP": "Tapón superior de la barra",
    "SEAL, DUST": "Guardapolvo de la barra",
    "OIL SEAL": "Retenedor",
    "SHOCK ABSORBER ASSY, REAR": "Amortiguador trasero",
    "ARM, REAR": "Basculante (brazo trasero)",
    "UNDER BRACKET COMP": "Tijera inferior de la dirección",
    "SPINDLE, TAPER": "Eje de la dirección",
    "BEARING, STEERING LOWER": "Rodamiento inferior de la dirección",
    "RACE, BALL": "Taza de la dirección",
    "COVER, BALL RACE": "Guardapolvo de la dirección",
    "RETAINER, BALL BEARING": "Seguro del rodamiento",
    "ROD": "Varilla amortiguadora",

    # Eléctrico
    "BATTERY ASSY": "Batería",
    "FUSE": "Fusible",
    "RELAY ASSY": "Relé",
    "DIODE ASSY": "Diodo",
    "WIRE HARNESS ASSY": "Arnés eléctrico (cableado)",
    "MAIN SWITCH STEERING LOCK": "Switch de encendido con bloqueo de dirección",
    "COVER, MAIN SWITCH": "Tapa del switch de encendido",
    "REMOTE CONTROL UNIT ASSY": "Módulo de la llave inteligente",
    "XMTR. COMP": "Llave inteligente (transmisor)",
    "KNOB COMP": "Perilla del switch",
    "SWITCH, SIDE STAND": "Sensor de la pata lateral",
    "STAY, IGNITION COIL": "Soporte de la bobina",
    "BUZZER": "Pito de alerta",
    "TERMINAL COMP": "Terminal",

    # Tornillería y piezas pequeñas
    "BOLT": "Tornillo",
    "BOLT, FLANGE": "Tornillo con arandela",
    "BOLT, FLANGE DEEP RECESS": "Tornillo con arandela",
    "BOLT, HEXAGON SOCKET HEAD": "Tornillo Allen",
    "SCREW": "Tornillo",
    "SCREW, FLAT HEAD": "Tornillo de cabeza plana",
    "SCREW, PAN HEAD": "Tornillo de cabeza redonda",
    "SCREW, PAN HEAD WITH WASHER": "Tornillo con arandela",
    "SCREW, TAPPING": "Tornillo autorroscante",
    "SCREW,TAPPING": "Tornillo autorroscante",
    "NUT": "Tuerca",
    "NUT, HEXAGON": "Tuerca",
    "NUT, SELF-LOCKING": "Tuerca de seguridad",
    "WASHER, PLATE": "Arandela",
    "WASHER, SPECIAL": "Arandela especial",
    "GASKET": "Empaque",
    "O-RING": "O-ring (empaque redondo)",
    "SEAL": "Sello",
    "CLIP": "Grapa",
    "CLAMP": "Abrazadera",
    "BAND": "Abrazadera plástica",
    "CIRCLIP": "Pin seguro",
    "RING, SNAP": "Pin seguro",
    "COLLAR": "Buje",
    "COLLAR, GUIDE": "Buje guía",
    "BUSH, SOLID": "Buje",
    "PIN, GUIDE": "Pasador guía",
    "SPRING, COIL": "Resorte",
    "DAMPER": "Caucho amortiguador",
    "DAMPER ASSY": "Caucho amortiguador",
    "GROMMET": "Caucho pasacables",
    "HOLDER": "Soporte",
    "STOPPER": "Tope",
    "PLATE": "Placa",
    "PIPE": "Manguera",
    "CAP": "Tapón",
    "PLUG, HOLE": "Tapón",
    "PLUG, STRAIGHT SCREW": "Tapón roscado",
    "COVER, UNDER": "Tapa inferior",
    # Piezas críticas de otros catálogos (Yamaha Crypton, FZ25, MT-03, XTZ125 y Honda Wave)
    "PLUG SPARK": "Bujía",
    "ELEMENT ASSY, OIL CLEANER": "Filtro de aceite",
    "AIR CLEANER ELEMENT ASSY": "Filtro de aire",
    "ELEMENT ASSY, AIR CLEANER": "Filtro de aire",
    "ELEMENT COMP., AIR CLEANER": "Filtro de aire",
    "BRAKE SHOE SET": "Bandas de freno (juego)",
    "SHOE SET, BRAKE": "Bandas de freno (juego)",
    "PAD SET, FR": "Pastillas de freno delanteras (juego)",
    "SPROCKET, DRIVE": "Piñón de salida",
    "SPROCKET, DRIVEN": "Corona (sprocket trasero)",
    "SPROCKET, FINAL DRIVEN": "Corona (sprocket trasero)",
    "CHAIN": "Cadena de transmisión",
    "RADIATOR COMP": "Radiador completo",
    "TANK, RESERVOIR": "Depósito de líquido de frenos",
    "SCREEN, OIL FILTER": "Malla del filtro de aceite",
    "BOLT, DRAIN PLUG": "Tornillo de drenaje del aceite",
    "VALVE, IN": "Válvula de admisión",
    "VALVE, EX": "Válvula de escape",
}

# Explicaciones cortas para piezas de mantenimiento (se busca por el inicio de la clave normalizada).
_AYUDAS = {
    "BRAKE PAD KIT": "Aprietan el disco para frenar y se gastan con el uso. Si chillan o el freno se siente largo, revísalas.",
    "DISK, BRAKE": "Gira con la rueda y las pastillas lo aprietan para frenar. Se cambia si está muy delgado o torcido.",
    "DISK, REAR BRAKE": "Gira con la rueda y las pastillas lo aprietan para frenar. Se cambia si está muy delgado o torcido.",
    "CALIPER ASSY": "Sostiene las pastillas y las empuja contra el disco cuando frenas.",
    "MASTER CYLINDER ASSY": "Empuja el líquido de frenos cuando aprietas la manigueta.",
    "RR. MASTER CYLINDER ASSY": "Empuja el líquido de frenos cuando aprietas la manigueta izquierda.",
    "CAP, RESERVOIR": "Cierra el depósito del líquido de frenos. Revisa el nivel por la mirilla y cámbialo cada 2 años.",
    "DIAPHRAGM, RESERVOIR": "Evita que entre humedad al líquido de frenos. Se revisa al cambiar el líquido.",
    "V-BELT": "Lleva la fuerza del motor a la rueda trasera. Si patina, chilla o la moto pierde fuerza al arrancar, revísala.",
    "WEIGHT SET": "Hacen que el variador cambie de relación. Gastados causan tirones o que la moto no alcance velocidad.",
    "CLUTCH WEIGHT SHOE SET": "Hacen que la moto arranque suave. Gastadas, la moto vibra o patina al salir.",
    "ELEMENT, AIR CLEANER": "Evita que entre polvo al motor. Sucio, la moto gasta más gasolina y pierde fuerza.",
    "PLUG, SPARK": "Da la chispa que enciende la gasolina. Gastada, la moto prende mal y consume más.",
    "PLUG,DRAIN": "Se quita para sacar el aceite viejo en cada cambio. Cambia su arandela si está aplastada.",
    "STRAINER, OIL": "Atrapa partículas del aceite. Se limpia en cada cambio de aceite.",
    "VALVE, INTAKE": "Deja entrar la mezcla de aire y gasolina. Mal calibrada hace ruido y quita fuerza.",
    "VALVE, EXHAUST": "Deja salir los gases quemados. Mal calibrada hace ruido y quita fuerza.",
    "RADIATOR ASSY": "Enfría el motor con el refrigerante. Revisa que no tenga fugas ni el panal tapado.",
    "CAP, RADIATOR": "Mantiene la presión del refrigerante. Nunca la abras con el motor caliente.",
    "TIRE": "Revisa la presión cada semana y cámbiala cuando el labrado llegue al indicador de desgaste.",
    "SHOCK ABSORBER ASSY, REAR": "Absorbe los golpes atrás. Si rebota mucho o bota aceite, hay que revisarlo.",
    "OIL SEAL": "Evita que se salga el aceite. Si ves aceite en la barra o alrededor, toca cambiarlo.",
    "SPRING, FRONT FORK": "Sostiene el peso adelante. Con los años pierde firmeza y la moto se hunde al frenar.",
    "FRONT FORK ASSY": "La suspensión delantera completa. Su aceite y retenedores se cambian cada 20.000 km aprox.",
    "BATTERY ASSY": "Da energía para el arranque y la inyección. Suele durar entre 2 y 3 años.",
}

_LADO_DER, _LADO_IZQ = "lado derecho", "lado izquierdo"
_LADOS = {"RIGHT": _LADO_DER, "R": _LADO_DER, "R.H": _LADO_DER, "LEFT": _LADO_IZQ, "L": _LADO_IZQ, "L.H": _LADO_IZQ}


def _normalizar(texto):
    t = re.sub(r"\s*\(.*?\)", "", texto.upper()).strip()
    t = re.sub(r"[\s.]*\d+$", "", t)     # "BOLT 1", "INNER TUBE COMP.1"
    return t.rstrip(". ").strip()


_INDICE = {_normalizar(k): v for k, v in _NOMBRES.items()}
_INDICE_AYUDAS = {_normalizar(k): v for k, v in _AYUDAS.items()}


def _detalle(descripcion):
    """Información útil entre paréntesis: lado, medida de llanta, amperaje o referencia."""
    extra = []
    for dentro in re.findall(r"\((.*?)\)", descripcion.upper()):
        dentro = dentro.strip()
        if dentro in _LADOS:
            extra.append(f"({_LADOS[dentro]})")
        elif m := re.match(r"(\d{2,3}/\d{2,3}-\d{2})", dentro):
            extra.append(m.group(1))                       # medida de llanta
        elif m := re.match(r"(\d+(?:\.\d+)?)A\b", dentro):
            extra.append(f"{m.group(1).replace('.', ',')} A")  # amperaje de fusible
        elif m := re.match(r"NGK\s+(\S+)", dentro):
            extra.append(f"NGK {m.group(1)}")
        elif m := re.match(r"YUASA\s+(\S+)", dentro):
            extra.append(m.group(1))
    return " ".join(extra)


def traducir(descripcion):
    clave = _normalizar(descripcion)
    nombre = _INDICE.get(clave)
    if not nombre:
        # Coincidencia más larga por el inicio (ej: "SCREW, PAN HEAD WITH WASHER" → la más específica)
        candidatos = [k for k in _INDICE if clave.startswith(k + ",") or clave.startswith(k + " ")]
        if candidatos:
            nombre = _INDICE[max(candidatos, key=len)]
    if not nombre:
        return ""
    detalle = _detalle(descripcion)
    return f"{nombre} {detalle}".strip() if detalle else nombre


def ayuda_para(descripcion):
    clave = _normalizar(descripcion)
    if clave in _INDICE_AYUDAS:
        return _INDICE_AYUDAS[clave]
    candidatos = [k for k in _INDICE_AYUDAS if clave.startswith(k)]
    return _INDICE_AYUDAS[max(candidatos, key=len)] if candidatos else ""
