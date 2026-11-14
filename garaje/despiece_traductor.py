"""Traducción por palabras de las descripciones en inglés de los catálogos, para las que el glosario no conoce.

Los catálogos escriben "SUSTANTIVO, MODIFICADORES" ("PROTECTOR, MUFFLER") o una frase en orden inglés ("OIL PUMP
GEAR"). Se traduce el sustantivo principal y se le agregan los adjetivos ("delantero", "interior") y lo que lo
complementa ("del silenciador"): "Protector del silenciador". Las marcas y referencias se dejan como están.
"""
import re

# Frases de varias palabras que son una sola pieza (se buscan antes que las palabras sueltas)
FRASES = {
    "OIL SEAL": ("Retén", "m"), "DUST SEAL": ("Guardapolvo", "m"), "SPARK PLUG": ("Bujía", "f"),
    "AIR CLEANER": ("Filtro de aire", "m"), "AIR FILTER": ("Filtro de aire", "m"), "OIL FILTER": ("Filtro de aceite", "m"),
    "OIL STRAINER": ("Malla del aceite", "f"), "OIL PUMP": ("Bomba de aceite", "f"), "FUEL PUMP": ("Bomba de gasolina", "f"),
    "FUEL TANK": ("Tanque de gasolina", "m"), "DRIVE CHAIN": ("Cadena de arrastre", "f"), "CAM CHAIN": ("Cadenilla", "f"),
    "CAM SPROCKET": ("Piñón de levas", "m"), "BALL RACE": ("Cuna de dirección", "f"), "STEERING STEM": ("Eje de dirección", "m"),
    "SHOCK ABSORBER": ("Amortiguador", "m"), "SWING ARM": ("Basculante", "m"), "SWINGING ARM": ("Basculante", "m"),
    "SWINGINGARM": ("Basculante", "m"), "SWGARM": ("Basculante", "m"), "CONNECTING ROD": ("Biela", "f"),
    "CONN ROD": ("Biela", "f"), "SNAP RING": ("Pin seguro", "m"), "E-RING": ("Seguro tipo E", "m"), "E RING": ("Seguro tipo E", "m"),
    "O-RING": ("O-ring", "m"), "O RING": ("O-ring", "m"), "COTTER PIN": ("Pasador de seguridad", "m"),
    "KICK STARTER": ("Pedal de arranque", "m"), "KICK STARTER ARM": ("Pedal de arranque", "m"), "STARTER MOTOR": ("Motor de arranque", "m"),
    "STARTING MOTOR": ("Motor de arranque", "m"), "MASTER CYLINDER": ("Bomba de freno", "f"), "BRAKE SHOE": ("Banda de freno", "f"),
    "BRAKE PAD": ("Pastilla de freno", "f"), "BRAKE DISC": ("Disco de freno", "m"), "BRAKE DISK": ("Disco de freno", "m"),
    "BRAKE PANEL": ("Plato portabandas", "m"), "BRAKE DRUM": ("Campana de freno", "f"), "BRAKE ARM": ("Palanca de freno", "f"),
    "BRAKE CAM": ("Leva del freno", "f"), "BRAKE LEVER": ("Manigueta de freno", "f"), "BRAKE PEDAL": ("Pedal de freno", "m"),
    "BRAKE HOSE": ("Manguera de freno", "f"), "BRAKE CABLE": ("Guaya de freno", "f"), "CLUTCH CABLE": ("Guaya del clutch", "f"),
    "THROTTLE CABLE": ("Guaya del acelerador", "f"), "SPEEDOMETER CABLE": ("Guaya del velocímetro", "f"),
    "SPEEDOMETER GEAR": ("Piñón del velocímetro", "m"), "WHEEL HUB": ("Manzana de la rueda", "f"), "WHEEL RIM": ("Rin", "m"),
    "TIRE TUBE": ("Neumático", "m"), "INNER TUBE": ("Neumático", "m"), "TUBE TIRE": ("Llanta", "f"),
    "FRONT FORK": ("Suspensión delantera", "f"), "FORK PIPE": ("Barra de la suspensión", "f"), "INNER PIPE": ("Barra cromada", "f"),
    "OUTER TUBE": ("Botella de la suspensión", "f"), "BOTTOM CASE": ("Botella de la suspensión", "f"),
    "FORK SPRING": ("Resorte de la suspensión", "m"), "CYLINDER HEAD": ("Culata", "f"), "HEAD COVER": ("Tapa de válvulas", "f"),
    "CYLINDER HEAD COVER": ("Tapa de válvulas", "f"), "CRANKCASE COVER": ("Tapa del cárter", "f"), "CLUTCH COVER": ("Tapa del clutch", "f"),
    "MAGNETO COVER": ("Tapa del magneto", "f"), "VALVE GUIDE": ("Guía de válvula", "f"), "VALVE SPRING": ("Resorte de válvula", "m"),
    "VALVE COTTER": ("Cuña de válvula", "f"), "VALVE RETAINER": ("Platillo de válvula", "m"), "VALVE STEM SEAL": ("Sello de válvula", "m"),
    "STEM SEAL": ("Sello de válvula", "m"), "ROCKER ARM": ("Balancín", "m"), "ROCKER SHAFT": ("Eje del balancín", "m"),
    "TAPPET ADJUSTING SCREW": ("Tornillo de calibración", "m"), "PISTON RING": ("Anillos del pistón", "m"),
    "PISTON PIN": ("Pasador del pistón", "m"), "PISTON PIN CLIP": ("Seguro del pasador", "m"), "CAM CHAIN TENSIONER": ("Tensor de la cadenilla", "m"),
    "CHAIN TENSIONER": ("Tensor de la cadenilla", "m"), "CHAIN GUIDE": ("Guía de la cadenilla", "f"), "CHAIN ADJUSTER": ("Templador de la cadena", "m"),
    "CHAIN CASE": ("Guardacadena", "m"), "CHAIN COVER": ("Guardacadena", "m"), "DRIVE SPROCKET": ("Piñón de salida", "m"),
    "DRIVEN SPROCKET": ("Corona", "f"), "FINAL DRIVEN SPROCKET": ("Corona", "f"), "FINAL DRIVE SPROCKET": ("Piñón de salida", "m"),
    "WHEEL DAMPER": ("Caucho de la corona", "m"), "SPROCKET DAMPER": ("Caucho de la corona", "m"), "CUSHION RUBBER": ("Caucho amortiguador", "m"),
    "DAMPER RUBBER": ("Caucho amortiguador", "m"), "BALL BEARING": ("Rodamiento", "m"), "RADIAL BALL BEARING": ("Rodamiento", "m"),
    "NEEDLE BEARING": ("Rodamiento de agujas", "m"), "STEERING HEAD": ("Dirección", "f"), "HANDLE BAR": ("Manubrio", "m"),
    "HANDLEBAR": ("Manubrio", "m"), "MAIN STAND": ("Gato central", "m"), "SIDE STAND": ("Gato lateral", "m"), "FOOT REST": ("Posapié", "m"),
    "FOOTREST": ("Posapié", "m"), "CHANGE PEDAL": ("Palanca de cambios", "f"), "GEAR SHIFT": ("Palanca de cambios", "f"),
    "SHIFT DRUM": ("Tambor selector", "m"), "SHIFT FORK": ("Horquilla de cambios", "f"), "GEARSHIFT FORK": ("Horquilla de cambios", "f"),
    "MAIN AXLE": ("Eje principal", "m"), "MAINSHAFT": ("Eje principal", "m"), "COUNTERSHAFT": ("Eje secundario", "m"),
    "DRIVE AXLE": ("Eje de salida", "m"), "DRIVESHAFT": ("Eje de salida", "m"), "CRANKSHAFT": ("Cigüeñal", "m"),
    "CAMSHAFT": ("Árbol de levas", "m"), "BALANCER SHAFT": ("Eje balanceador", "m"), "STARTER CLUTCH": ("Clutch de arranque", "m"),
    "ONE WAY CLUTCH": ("Clutch de arranque", "m"), "FRICTION PLATE": ("Disco de clutch", "m"), "CLUTCH PLATE": ("Separador de clutch", "m"),
    "PRESSURE PLATE": ("Plato de presión", "m"), "CLUTCH OUTER": ("Campana del clutch", "f"), "CLUTCH CENTER": ("Manzana del clutch", "f"),
    "CLUTCH HOUSING": ("Campana del clutch", "f"), "CLUTCH BOSS": ("Manzana del clutch", "f"), "CLUTCH SPRING": ("Resorte del clutch", "m"),
    "V-BELT": ("Correa", "f"), "DRIVE BELT": ("Correa", "f"), "WEIGHT ROLLER": ("Rodillos del variador", "m"), "WEIGHT SET": ("Rodillos del variador", "m"),
    "MOVABLE DRIVE FACE": ("Polea móvil", "f"), "DRIVE FACE": ("Polea fija", "f"), "MOVABLE DRIVEN FACE": ("Polea conducida móvil", "f"),
    "DRIVEN FACE": ("Polea conducida", "f"), "CLUTCH SHOE": ("Zapata del clutch", "f"), "THROTTLE BODY": ("Cuerpo de aceleración", "m"),
    "AIR CLEANER CASE": ("Caja del filtro de aire", "f"), "AIR CLEANER ELEMENT": ("Filtro de aire", "m"), "AIR CLEANER COVER": ("Tapa del filtro de aire", "f"),
    "EXHAUST PIPE": ("Tubo de escape", "m"), "EX PIPE": ("Tubo de escape", "m"), "EXH PIPE": ("Tubo de escape", "m"),
    "MUFFLER COMP": ("Silenciador", "m"), "HEAT SHIELD": ("Protector de calor", "m"), "BATTERY CASE": ("Caja de la batería", "f"),
    "BATTERY BOX": ("Caja de la batería", "f"), "WIRE HARNESS": ("Arnés eléctrico", "m"), "WIRING HARNESS": ("Arnés eléctrico", "m"),
    "IGNITION COIL": ("Bobina de encendido", "f"), "IGN COIL": ("Bobina de encendido", "f"), "REG REC": ("Regulador rectificador", "m"),
    "REGULATOR RECTIFIER": ("Regulador rectificador", "m"), "RECTIFIER": ("Regulador rectificador", "m"), "STARTER RELAY": ("Relé de arranque", "m"),
    "FUSE BOX": ("Caja de fusibles", "f"), "NEUTRAL SWITCH": ("Sensor de neutro", "m"), "WINKER": ("Direccional", "f"),
    "TAIL LIGHT": ("Stop", "m"), "TAILLIGHT": ("Stop", "m"), "HEAD LIGHT": ("Farola", "f"), "HEADLIGHT": ("Farola", "f"), "HEADLAMP": ("Farola", "f"),
    "SPEEDOMETER": ("Velocímetro", "m"), "TACHOMETER": ("Tacómetro", "m"), "WOODRUFF KEY": ("Cuña media luna", "f"),
    "THRUST WASHER": ("Arandela de empuje", "f"), "PLAIN WASHER": ("Arandela plana", "f"), "SPRING WASHER": ("Arandela de presión", "f"),
    "LOCK WASHER": ("Arandela de seguridad", "f"), "SEALING WASHER": ("Arandela de sello", "f"), "LOCK NUT": ("Contratuerca", "f"),
    "U-NUT": ("Tuerca de seguridad", "f"), "DOWEL PIN": ("Pin guía", "m"), "GREASE": ("Grasa", "f"), "DRAIN PLUG": ("Tapón de drenaje", "m"),
    "DRAIN BOLT": ("Tapón de drenaje", "m"), "FILLER CAP": ("Tapa de llenado", "f"), "OIL LEVEL GAUGE": ("Varilla del aceite", "f"),
    "OIL GAUGE": ("Varilla del aceite", "f"), "LEVEL GAUGE": ("Varilla del aceite", "f"), "BREATHER TUBE": ("Manguera del respiradero", "f"),
    "BREATHER HOSE": ("Manguera del respiradero", "f"), "OVER FLOW PIPE": ("Manguera de rebose", "f"), "SPOKE": ("Radio", "m"),
    "SPOKE SET": ("Juego de radios", "m"), "RIM BAND": ("Protector del neumático", "m"), "RIM STRIP": ("Protector del neumático", "m"),
    "TIRE": ("Llanta", "f"), "TYRE": ("Llanta", "f"), "AIR VALVE": ("Válvula de aire", "f"), "DECOMPRESSION": ("Descompresor", "m"),
    "DECOMP": ("Descompresor", "m"), "MAGNETO ROTOR": ("Volante del magneto", "m"), "FLYWHEEL": ("Volante del magneto", "m"),
    "STATOR": ("Estator", "m"), "PULSER": ("Captador", "m"), "PICK UP COIL": ("Captador", "m"),
    "CHAIN DAMPER": ("Caucho de la cadena", "m"), "YOKE": ("Horquilla de la varilla", "f"),
    "WHEEL TAPE": ("Calcomanía del rin", "f"), "TAPE": ("Calcomanía", "f"), "CAMSHAFT C-RING": ("Anillo de retención del árbol de levas", "m"),
    "C-RING": ("Anillo de retención", "m"), "MUFFLER BODY": ("Cuerpo del silenciador", "m"), "CLUTCH WEIGHT SET": ("Zapatas del clutch", "f"), "CLUTCH WEIGHT": ("Zapatas del clutch", "f"),
    "WINKER RELAY SUSPENSION": ("Caucho soporte del flasher", "m"), "NOISE SUPPRESSOR CAP": ("Capuchón de la bujía", "m"),
    "FLANGE CAP NUT": ("Tuerca ciega", "f"), "CAP NUT": ("Tuerca ciega", "f"), "BLEEDER": ("Purgador", "m"), "THROUGH": ("Paso de aceite", "m"), "METAL": ("Buje metálico", "m"), "SLIDE METAL": ("Buje de deslizamiento", "m"),
    "WINKER RELAY": ("Flasher de direccionales", "m"), "RELAY, WINKER": ("Flasher de direccionales", "m"), "BOSS": ("Manzana", "f"),
    "MAIN SHAFT": ("Eje principal", "m"), "COUNTER SHAFT": ("Eje secundario", "m"), "COUNTERSHAFT": ("Eje secundario", "m"),
    "CRANK CASE": ("Cárter", "m"), "AIR C": ("Filtro de aire", "m"), "CABLE TIE": ("Amarre plástico", "m"),
    "TUBE BREATHER": ("Manguera del respiradero", "f"), "TIRE FLAP": ("Protector del neumático", "m"),
    "CDI UNIT": ("CDI", "m"), "UNIT CDI": ("CDI", "m"), "STOP SWITCH": ("Interruptor del stop", "m"),
    "CHANGE SWITCH": ("Interruptor de luces", "m"), "STARTER MAGNETIC SWITCH": ("Relé de arranque", "m"),
    "MAGNETIC SWITCH": ("Relé de arranque", "m"), "BACKUP RING": ("Anillo de respaldo", "m"),
}

# Sustantivos principales: (traducción, género)
SUSTANTIVOS = {
    "BOLT": ("Tornillo", "m"), "SCREW": ("Tornillo", "m"), "SCREW-WASHER": ("Tornillo con arandela", "m"), "NUT": ("Tuerca", "f"),
    "WASHER": ("Arandela", "f"), "SPRING": ("Resorte", "m"), "PIN": ("Pin", "m"), "CLIP": ("Gancho", "m"), "CIRCLIP": ("Pin seguro", "m"),
    "RING": ("Anillo", "m"), "COLLAR": ("Buje", "m"), "BUSH": ("Buje", "m"), "BUSHING": ("Buje", "m"), "SPACER": ("Separador", "m"),
    "SLEEVE": ("Camisa", "f"), "SHIM": ("Laina", "f"), "PLATE": ("Platina", "f"), "BRACKET": ("Soporte", "m"), "STAY": ("Soporte", "m"),
    "HOLDER": ("Soporte", "m"), "SUPPORT": ("Soporte", "m"), "MOUNT": ("Soporte", "m"), "HANGER": ("Soporte", "m"), "BASE": ("Base", "f"),
    "COVER": ("Tapa", "f"), "CAP": ("Tapa", "f"), "LID": ("Tapa", "f"), "PLUG": ("Tapón", "m"), "GUARD": ("Protector", "m"),
    "PROTECTOR": ("Protector", "m"), "SHIELD": ("Protector", "m"), "GASKET": ("Empaque", "m"), "PACKING": ("Empaque", "m"),
    "SEAL": ("Sello", "m"), "GROMMET": ("Caucho pasacable", "m"), "RUBBER": ("Caucho", "m"), "CUSHION": ("Caucho amortiguador", "m"),
    "DAMPER": ("Amortiguador", "m"), "BUFFER": ("Tope de caucho", "m"), "STOPPER": ("Tope", "m"), "STOP": ("Tope", "m"),
    "BEARING": ("Rodamiento", "m"), "RACE": ("Cuna", "f"), "BALL": ("Balín", "m"), "SHAFT": ("Eje", "m"), "AXLE": ("Eje", "m"),
    "SPINDLE": ("Eje", "m"), "ROD": ("Varilla", "f"), "ARM": ("Brazo", "m"), "LEVER": ("Palanca", "f"), "PEDAL": ("Pedal", "m"),
    "GEAR": ("Piñón", "m"), "SPROCKET": ("Piñón", "m"), "PINION": ("Piñón", "m"), "CHAIN": ("Cadena", "f"), "BELT": ("Correa", "f"),
    "CABLE": ("Guaya", "f"), "WIRE": ("Cable", "m"), "HOSE": ("Manguera", "f"), "TUBE": ("Tubo", "m"), "PIPE": ("Tubo", "m"),
    "DUCT": ("Ducto", "m"), "JOINT": ("Unión", "f"), "CLAMP": ("Abrazadera", "f"), "CLAMPER": ("Abrazadera", "f"), "BAND": ("Abrazadera", "f"),
    "TIE": ("Amarre", "m"), "CASE": ("Carcasa", "f"), "CRANKCASE": ("Cárter", "m"), "HOUSING": ("Carcasa", "f"), "BOX": ("Caja", "f"),
    "TANK": ("Tanque", "m"), "RESERVOIR": ("Depósito", "m"), "CUP": ("Copa", "f"), "PUMP": ("Bomba", "f"), "VALVE": ("Válvula", "f"),
    "PISTON": ("Pistón", "m"), "CYLINDER": ("Cilindro", "m"), "HEAD": ("Culata", "f"), "CAM": ("Leva", "f"), "ROCKER": ("Balancín", "m"),
    "TAPPET": ("Taqué", "m"), "GUIDE": ("Guía", "f"), "TENSIONER": ("Tensor", "m"), "ADJUSTER": ("Templador", "m"), "ROLLER": ("Rodillo", "m"),
    "WHEEL": ("Rueda", "f"), "RIM": ("Rin", "m"), "HUB": ("Manzana", "f"), "DRUM": ("Campana", "f"), "DISC": ("Disco", "m"), "DISK": ("Disco", "m"),
    "SHOE": ("Banda", "f"), "PAD": ("Pastilla", "f"), "PANEL": ("Plato", "m"), "CALIPER": ("Caliper", "m"), "FORK": ("Barra", "f"),
    "SWITCH": ("Interruptor", "m"), "RELAY": ("Relé", "m"), "FUSE": ("Fusible", "m"), "TERMINAL": ("Terminal", "m"), "COIL": ("Bobina", "f"),
    "HARNESS": ("Arnés", "m"), "CONNECTOR": ("Conector", "m"), "BATTERY": ("Batería", "f"), "MOTOR": ("Motor", "m"), "UNIT": ("Unidad", "f"),
    "SENSOR": ("Sensor", "m"), "LAMP": ("Bombillo", "m"), "BULB": ("Bombillo", "m"), "LENS": ("Mica", "f"), "MIRROR": ("Espejo", "m"),
    "REFLECTOR": ("Reflector", "m"), "EMBLEM": ("Emblema", "m"), "LABEL": ("Etiqueta", "f"), "MARK": ("Calcomanía", "f"),
    "STRIPE": ("Calcomanía", "f"), "SEAT": ("Asiento", "m"), "MAT": ("Tapete", "m"), "SHEET": ("Lámina", "f"), "FLAP": ("Guardabarro", "m"),
    "FENDER": ("Guardabarro", "m"), "MUDGUARD": ("Guardabarro", "m"), "MUFFLER": ("Silenciador", "m"), "SILENCER": ("Silenciador", "m"),
    "RESONATOR": ("Resonador", "m"), "ELEMENT": ("Elemento filtrante", "m"), "FILTER": ("Filtro", "m"), "SCREEN": ("Malla", "f"),
    "STRAINER": ("Malla", "f"), "NET": ("Malla", "f"), "CLEANER": ("Filtro", "m"), "CARBURETOR": ("Carburador", "m"), "JET": ("Chicler", "m"),
    "NEEDLE": ("Aguja", "f"), "FLOAT": ("Flotador", "m"), "DIAPHRAGM": ("Diafragma", "m"), "NOZZLE": ("Surtidor", "m"), "INJECTOR": ("Inyector", "m"),
    "ROTOR": ("Rotor", "m"), "STATOR": ("Estator", "m"), "FACE": ("Polea", "f"), "WEIGHT": ("Contrapeso", "m"), "SLIDER": ("Deslizador", "m"),
    "SHOCK": ("Amortiguador", "m"), "ABSORBER": ("Amortiguador", "m"), "LINK": ("Varilla", "f"), "KEY": ("Cuña", "f"), "COTTER": ("Pasador", "m"),
    "GAUGE": ("Indicador", "m"), "INDICATOR": ("Indicador", "m"), "METER": ("Tablero", "m"), "STEM": ("Eje", "m"), "SPOKE": ("Radio", "m"),
    "INSULATOR": ("Aislante", "m"), "SEPARATOR": ("Separador", "m"), "RETAINER": ("Retenedor", "m"), "ANCHOR": ("Anclaje", "m"),
    "BOSS": ("Manzana", "f"), "RATCHET": ("Trinquete", "m"), "PIECE": ("Pieza", "f"), "INSERT": ("Inserto", "m"), "TRAY": ("Bandeja", "f"),
    "BREATHER": ("Respiradero", "m"), "COCK": ("Llave", "f"), "SLIDE": ("Deslizador", "m"), "STAND": ("Gato", "m"), "GRIP": ("Puño", "m"),
    "HANDLE": ("Manubrio", "m"), "STEP": ("Posapié", "m"), "LOCK": ("Chapa", "f"), "MOLDING": ("Moldura", "f"), "GARNISH": ("Moldura", "f"),
    "FIN": ("Aleta", "f"), "DOG": ("Trinquete", "m"), "FLANGE": ("Brida", "f"), "PULLEY": ("Polea", "f"), "DRIVER": ("Impulsor", "m"),
    "SET": ("Juego", "m"), "KIT": ("Kit", "m"), "BOOT": ("Guardapolvo", "m"), "PIVOT": ("Pivote", "m"), "TOUCH": ("Toque", "m"), "LEAD": ("Cable", "m"), "COUNTER": ("Contador", "m"),
    "SPEEDOMETER": ("Velocímetro", "m"), "TACHOMETER": ("Tacómetro", "m"), "CIRCUIT": ("Circuito", "m"), "WINDOW": ("Visor", "m"),
}

# Adjetivos: (masculino, femenino)
ADJETIVOS = {
    "FRONT": ("delantero", "delantera"), "FR": ("delantero", "delantera"), "FORNT": ("delantero", "delantera"),
    "REAR": ("trasero", "trasera"), "RR": ("trasero", "trasera"), "LEFT": ("izquierdo", "izquierda"), "LH": ("izquierdo", "izquierda"),
    "L": ("izquierdo", "izquierda"), "RIGHT": ("derecho", "derecha"), "RH": ("derecho", "derecha"), "R": ("derecho", "derecha"),
    "UPPER": ("superior", "superior"), "LOWER": ("inferior", "inferior"), "UNDER": ("inferior", "inferior"), "TOP": ("superior", "superior"),
    "BOTTOM": ("inferior", "inferior"), "INNER": ("interior", "interior"), "OUTER": ("exterior", "exterior"), "MAIN": ("principal", "principal"),
    "DRIVE": ("motriz", "motriz"), "DRIVEN": ("conducido", "conducida"), "PRIMARY": ("primario", "primaria"), "SECONDARY": ("secundario", "secundaria"),
    "FINAL": ("final", "final"), "IDLE": ("intermedio", "intermedia"), "MOVABLE": ("móvil", "móvil"), "FIXED": ("fijo", "fija"),
    "PLAIN": ("plano", "plana"), "FLAT": ("plano", "plana"), "LONG": ("largo", "larga"), "SHORT": ("corto", "corta"), "SPECIAL": ("especial", "especial"),
    "DOUBLE": ("doble", "doble"), "METALLIC": ("metálico", "metálica"), "MAGNETIC": ("magnético", "magnética"), "STD": ("estándar", "estándar"),
    "COMP": ("completo", "completa"), "ASSY": ("completo", "completa"), "SUB": ("", ""), "CENTER": ("central", "central"),
    "SIDE": ("lateral", "lateral"), "ROTARY": ("rotativo", "rotativa"), "LOW": ("bajo", "baja"), "HIGH": ("alto", "alta"),
    "1ST": ("de primera", "de primera"), "2ND": ("de segunda", "de segunda"), "3RD": ("de tercera", "de tercera"), "4TH": ("de cuarta", "de cuarta"),
    "5TH": ("de quinta", "de quinta"), "6TH": ("de sexta", "de sexta"), "SECOND": ("de segunda", "de segunda"), "THIRD": ("de tercera", "de tercera"),
    "FOURTH": ("de cuarta", "de cuarta"), "FIFTH": ("de quinta", "de quinta"), "BLACK": ("negro", "negra"), "SILVER": ("plateado", "plateada"),
    "GOLD": ("dorado", "dorada"), "GRAY": ("gris", "gris"), "GREEN": ("verde", "verde"), "RED": ("rojo", "roja"), "WHITE": ("blanco", "blanca"),
    "BLUE": ("azul", "azul"), "SLIDE": ("de deslizamiento", "de deslizamiento"), "SPLINE": ("estriado", "estriada"), "WOODRUFF": ("media luna", "media luna"),
    "INLET": ("de admisión", "de admisión"), "INTAKE": ("de admisión", "de admisión"),
    "BACKUP": ("de respaldo", "de respaldo"), "PUSH": ("de empuje", "de empuje"), "SLIDING": ("deslizante", "deslizante"),
}

# Complementos: lo que acompaña al sustantivo ("del silenciador")
COMPLEMENTOS = {
    "MUFFLER": "del silenciador", "SILENCER": "del silenciador", "EXHAUST": "del escape", "EX": "del escape", "EXH": "del escape",
    "ENGINE": "del motor", "OIL": "del aceite", "FUEL": "de la gasolina", "AIR": "del aire", "WATER": "del agua", "BRAKE": "del freno",
    "CLUTCH": "del clutch", "CHAIN": "de la cadena", "WHEEL": "de la rueda", "AXLE": "del eje", "SHAFT": "del eje", "CAM": "de levas",
    "CAMSHAFT": "del árbol de levas", "CRANKSHAFT": "del cigüeñal", "CRANK": "del cigüeñal", "PISTON": "del pistón",
    "CYLINDER": "del cilindro", "HEAD": "de la culata", "VALVE": "de la válvula", "ROCKER": "del balancín", "TAPPET": "del taqué",
    "STARTER": "de arranque", "STARTING": "de arranque", "KICK": "del pedal de arranque", "PUMP": "de la bomba", "TANK": "del tanque",
    "BATTERY": "de la batería", "SWITCH": "del interruptor", "CABLE": "de la guaya", "HOSE": "de la manguera", "PIPE": "del tubo",
    "TUBE": "del tubo", "SPEEDOMETER": "del velocímetro", "TACHOMETER": "del tacómetro", "METER": "del tablero", "HANDLE": "del manubrio",
    "HANDLEBAR": "del manubrio", "STEERING": "de la dirección", "FORK": "de la suspensión", "CUSHION": "del amortiguador",
    "SHOCK": "del amortiguador", "SWINGARM": "del basculante", "ARM": "del brazo", "PEDAL": "del pedal", "LEVER": "de la palanca",
    "SEAT": "del asiento", "FENDER": "del guardabarro", "CHANGE": "de cambios", "SHIFT": "de cambios", "GEAR": "del piñón",
    "SPROCKET": "del piñón", "CRANKCASE": "del cárter", "CASE": "de la carcasa", "COVER": "de la tapa", "CARBURETOR": "del carburador",
    "THROTTLE": "del acelerador", "CHOKE": "del choque", "INTAKE": "de admisión", "INLET": "de admisión", "OUTLET": "de salida",
    "FILTER": "del filtro", "CLEANER": "del filtro", "ELEMENT": "del filtro", "STRAINER": "de la malla", "RADIATOR": "del radiador",
    "COOLANT": "del refrigerante", "THERMOSTAT": "del termostato", "FAN": "del ventilador", "IGNITION": "de encendido", "IGN": "de encendido",
    "SPARK": "de la bujía", "PLUG": "del tapón", "DRAIN": "de drenaje", "FILLER": "de llenado", "LEVEL": "de nivel", "BREATHER": "del respiradero",
    "BALANCER": "del balanceador", "MAGNETO": "del magneto", "GENERATOR": "del generador", "STATOR": "del estator", "ROTOR": "del rotor",
    "LIGHT": "de la luz", "LAMP": "de la luz", "HEADLIGHT": "de la farola", "HEADLAMP": "de la farola", "WINKER": "de la direccional",
    "TAIL": "del stop", "HORN": "del pito", "MIRROR": "del espejo", "STAND": "del gato", "FOOTREST": "del posapié", "STEP": "del posapié",
    "PAD": "de las pastillas", "SHOE": "de las bandas", "DISC": "del disco", "DISK": "del disco", "DRUM": "de la campana", "HUB": "de la manzana",
    "RIM": "del rin", "TIRE": "de la llanta", "SPOKE": "del radio", "CALIPER": "del caliper", "MASTER": "de la bomba", "RESERVOIR": "del depósito",
    "BEARING": "del rodamiento", "SEAL": "del sello", "BELT": "de la correa", "FACE": "de la polea", "PULLEY": "de la polea", "WEIGHT": "del contrapeso",
    "MISSION": "de la caja", "TRANSMISSION": "de la caja", "TORQUE": "de torque", "NEUTRAL": "de neutro", "DECOMPRESSION": "del descompresor",
    "DECOMP": "del descompresor", "TENSIONER": "del tensor", "GUIDE": "de la guía", "BODY": "del cuerpo", "SENSOR": "del sensor",
    "FRAME": "del chasis", "CHASSIS": "del chasis", "SIDE": "lateral", "LOCK": "de seguridad", "SETTING": "de ajuste", "ADJUSTING": "de ajuste",
    "RETURN": "de retorno", "REBOUND": "de rebote", "THRUST": "de empuje", "SEALING": "de sello", "STOPPER": "del tope", "CONNECTING": "",
    "SPRING": "del resorte", "HARNESS": "del arnés", "CONNECTOR": "del conector", "RELAY": "del relé", "FUSE": "del fusible",
    "BOX": "de la caja", "TOOL": "de herramientas", "GRIP": "del puño", "BALL": "de balines", "NEEDLE": "de agujas", "ROLLER": "de rodillos",
    "MOUNTING": "de montaje", "MOUNT": "de montaje", "INSPECTION": "de inspección", "HARN": "del arnés", "CORD": "del cable",
    "PULSER": "del captador", "CAP": "de la tapa", "PINION": "del piñón", "MAINSHAFT": "del eje principal", "COUNTERSHAFT": "del eje secundario",
    "BRACKET": "del soporte", "DIAPHRAGM": "del diafragma", "TIE": "de amarre", "CDI": "del CDI", "SILICON": "",
    "START": "de arranque", "STOP": "del stop", "THROUGH": "de paso", "SUSPENSION": "de la suspensión", "BUFFER": "del tope", "BOLT": "del tornillo", "NUT": "de la tuerca", "JOINT": "de la unión", "DUCT": "del ducto", "PANEL": "del plato", "INSULATOR": "del aislante",
}

_IGNORAR = {"AND", "WITH", "FOR", "OF", "THE", "NO", "TYPE", "A", "B", "C", "D", "E", "MM", "ID", "OD", "SUB", "SET", "COMP", "ASSY", "ASSEMBLY"}
_ABREV = {"ASSY": "ASSY", "COMP": "COMP", "CONN": "CONNECTING", "RR": "RR", "FR": "FR", "EX": "EX", "EXH": "EXH", "IGN": "IGN",
          "SUSP": "FORK", "TRANS": "TRANSMISSION", "STRG": "STEERING", "SPDMTR": "SPEEDOMETER"}


def _palabras(texto):
    texto = re.sub(r"\(.*?\)", " ", texto.upper())
    texto = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:X\s*\d+(?:[.,]\d+)?)*\s*(?:MM|L|T)?\b", " ", texto)   # medidas y números
    texto = texto.replace(".", " ").replace("'", " ").replace("/", " ")
    return [_ABREV.get(w, w) for w in re.findall(r"[A-Z0-9][A-Z0-9-]*", texto)]


def _frase(palabras, i):
    """La frase más larga (hasta 4 palabras) que empieza en i y está en FRASES: (traducción, género, palabras usadas)."""
    for n in (4, 3, 2, 1):
        clave = " ".join(palabras[i:i + n])
        if len(palabras[i:i + n]) == n and clave in FRASES:
            return FRASES[clave] + (n,)
    return None


def traducir_palabras(descripcion):
    """'PROTECTOR, MUFFLER' → 'Protector del silenciador'; 'GEAR, PUMP DRIVEN' → 'Piñón conducido de la bomba'.
    Devuelve "" si no reconoce el sustantivo principal."""
    if re.search(r"[áéíóúñ]", descripcion.lower()):
        return ""
    alto = descripcion.upper()
    if re.match(r"^\.*CUSHION (ASSY|COMP|SUB)", alto):
        marca = re.search(r"\((SHOWA|GABRIEL|ENDURANCE|KYB|ENDURANCE TECH|YSS)\)", alto)
        lado = " izquierda" if re.search(r"\b(L|LH|LEFT)\b", alto) else " derecha" if re.search(r"\b(R|RH|RIGHT)\b", alto) else ""
        if re.search(r"\b(FR|FRONT)\b", alto):
            nombre = f"Barra de suspensión completa{lado}"
        else:
            nombre = "Amortiguador trasero completo"
        return nombre + (f" ({marca.group(1).capitalize()})" if marca else "")
    cabeza_txt, _, resto_txt = descripcion.partition(",")
    cabeza, resto = _palabras(cabeza_txt), _palabras(resto_txt)
    while cabeza and cabeza[-1] in _IGNORAR:
        cabeza.pop()
    if not cabeza:
        return ""
    for n in (3, 2, 1):                          # "TUBE, TIRE" = "TIRE TUBE" (neumático)
        clave = " ".join([w for w in resto if w not in _IGNORAR][-n:] + cabeza) if resto else ""
        if clave in FRASES and len(cabeza) <= 2:
            return FRASES[clave][0]
    # Sustantivo principal: frase conocida al final de la cabeza, o su última palabra (orden inglés)
    nucleo = None
    for i in range(len(cabeza)):
        f = _frase(cabeza, i)
        if f and i + f[2] == len(cabeza):
            nucleo, previas = f, cabeza[:i]
            break
    if not nucleo:                                   # "SPARK PLUG DR8EA", "CRANK CASE COMP LEFT": la frase y lo demás modifica
        for i in range(len(cabeza)):
            f = _frase(cabeza, i)
            if f and f[2] > 1:
                nucleo, previas = f, cabeza[:i] + cabeza[i + f[2]:]
                break
    if not nucleo:
        ultima = cabeza[-1]
        if ultima in SUSTANTIVOS:
            nucleo, previas = SUSTANTIVOS[ultima] + (1,), cabeza[:-1]
        elif cabeza[0] in SUSTANTIVOS:           # sin coma pero con el sustantivo primero: "VALVE INLET", "ARM RR. BRAKE"
            nucleo, previas = SUSTANTIVOS[cabeza[0]] + (1,), cabeza[1:]
        else:
            return ""
    nombre, genero = nucleo[0], nucleo[1]
    adjetivos, complementos, otros = [], [], []
    modificadores = previas + resto
    i = 0
    while i < len(modificadores):
        w = modificadores[i]
        f = _frase(modificadores, i)
        if f and f[2] > 1:
            articulo = "del" if f[1] == "m" else "de la"
            complementos.append(f"{articulo} {f[0][:1].lower() + f[0][1:]}")
            i += f[2]
            continue
        if w in _IGNORAR:
            pass
        elif w in ADJETIVOS:
            adj = ADJETIVOS[w][0 if genero == "m" else 1]
            if adj and adj not in adjetivos:
                adjetivos.append(adj)
        elif w in COMPLEMENTOS:
            if COMPLEMENTOS[w] and COMPLEMENTOS[w] not in complementos and COMPLEMENTOS[w].split()[-1] not in nombre.lower():
                complementos.append(COMPLEMENTOS[w])
        elif re.fullmatch(r"[A-Z]{3,}", w):
            otros.append(w.capitalize())      # marca o palabra desconocida: se deja como está
        i += 1
    otros = [o for o in otros if o.upper() in ("SHOWA", "GABRIEL", "ENDURANCE", "NISSIN", "KYB", "NGK", "DENSO")]  # marcas sí; lo demás no se inventa
    complementos.reverse()
    # "Varilla del freno trasero", no "Varilla trasera del freno": delantero/trasero califican al freno
    if "del freno" in complementos:
        for adj in [a for a in adjetivos if a.startswith(("delanter", "traser"))]:
            adjetivos.remove(adj)
            complementos[complementos.index("del freno")] = "del freno " + ("delantero" if adj.startswith("delanter") else "trasero")
    partes = [nombre] + [a for a in adjetivos if a.startswith("de ")] + [a for a in adjetivos if not a.startswith("de ")] \
        + complementos + otros
    texto = " ".join(p for p in partes if p)
    # Caja de cambios: el piñón "motriz" de una marcha va en el eje principal y el "conducido" en el secundario
    marcha = re.search(r"de (primera|segunda|tercera|cuarta|quinta|sexta)", texto)
    if nombre in ("Arandela", "Buje", "Pin seguro", "Separador") and marcha:
        papel = "motriz" if "motriz" in texto else "conducido" if re.search(r"conducid", texto) else ""
        return f"{nombre} del piñón {papel + ' ' if papel else ''}{marcha.group(0)}"
    if nombre == "Piñón" and marcha and " del eje " not in texto:
        texto = texto.replace(" motriz", " del eje principal").replace(" conducido", " del eje secundario")
        texto = texto.replace(" de la rueda", " del eje secundario")   # Yamaha: "WHEEL" = piñón conducido
    return re.sub(r"\s{2,}", " ", texto).strip()
