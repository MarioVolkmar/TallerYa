"""Traducción aproximada de descripciones de catálogos de partes (inglés técnico → español de Colombia).

Primero busca la descripción completa; si no, traduce la primera palabra clave (antes de la coma).
Lo que no conoce lo deja vacío para que se muestre el texto original.
"""
import re

FRASES = {
    "BRAKE PAD KIT": "Kit de pastillas de freno",
    "DISK, BRAKE": "Disco de freno",
    "DISK, REAR BRAKE": "Disco de freno trasero",
    "CALIPER ASSY": "Caliper completo",
    "PISTON ASSY, CALIPER": "Pistón del caliper",
    "CALIPER SEAL KIT": "Kit de sellos del caliper",
    "BLEED SCREW KIT": "Purgador",
    "MASTER CYLINDER ASSY": "Bomba de freno",
    "CAP, RESERVOIR": "Tapa del depósito de líquido",
    "DIAPHRAGM, RESERVOIR": "Diafragma del depósito",
    "V-BELT": "Correa CVT",
    "WEIGHT SET": "Juego de rodillos del variador",
    "CLUTCH WEIGHT SHOE SET": "Zapatas del clutch",
    "PRIMARY SLIDING SHEAVE COMP.": "Polea móvil del variador",
    "STRAINER, OIL": "Malla del aceite",
    "PLUG,DRAIN": "Tapón de drenaje del aceite",
    "OIL PUMP ASSY": "Bomba de aceite",
    "ELEMENT, AIR CLEANER": "Filtro de aire",
    "CASE, AIR CLEANER": "Caja del filtro de aire",
    "PLUG, SPARK": "Bujía",
    "CYLINDER HEAD ASSY": "Culata completa",
    "VALVE, INTAKE": "Válvula de admisión",
    "VALVE, EXHAUST": "Válvula de escape",
    "CAP, RADIATOR": "Tapa del radiador",
    "RADIATOR ASSY": "Radiador",
    "THERMOSTAT ASSY": "Termostato",
    "TIRE": "Llanta",
    "CAST WHEEL, FRONT": "Rin delantero",
    "CAST WHEEL, REAR": "Rin trasero",
    "SHOCK ABSORBER ASSY, REAR": "Amortiguador trasero",
    "FRONT FORK ASSY": "Suspensión delantera completa",
    "SPRING, FRONT FORK": "Resorte de la suspensión",
    "OIL SEAL": "Retenedor",
    "BATTERY ASSY": "Batería",
    "ARM, REAR": "Brazo trasero",
}

PALABRAS = {
    "BOLT": "Tornillo", "SCREW": "Tornillo", "NUT": "Tuerca", "WASHER": "Arandela", "GASKET": "Empaque",
    "O-RING": "O-ring", "SPRING": "Resorte", "COLLAR": "Buje", "BEARING": "Rodamiento", "CLIP": "Clip",
    "HOSE": "Manguera", "PIPE": "Tubo", "CLAMP": "Abrazadera", "BRACKET": "Soporte", "COVER": "Tapa",
    "CAP": "Tapa", "PIN": "Pasador", "SEAL": "Sello", "BOOT": "Guardapolvo", "SHIM": "Lámina", "PLATE": "Placa",
    "GUIDE": "Guía", "HOLDER": "Sujetador", "DAMPER": "Amortiguador", "GROMMET": "Caucho", "SPACER": "Separador",
    "STAY": "Soporte", "CIRCLIP": "Pin seguro", "DOWEL": "Guía", "AXLE": "Eje", "CABLE": "Cable", "LEVER": "Palanca",
    "SUPPORT": "Soporte", "JOINT": "Unión", "VALVE": "Válvula", "SWITCH": "Interruptor", "LEAD": "Cable",
    "FUSE": "Fusible", "RELAY": "Relé", "BAND": "Banda", "SENSOR": "Sensor", "TANK": "Tanque", "PUMP": "Bomba",
}


def traducir(descripcion):
    limpia = re.sub(r"\s*\(.*?\)", "", descripcion.upper()).strip().rstrip(" 0123456789")
    if limpia in FRASES:
        return FRASES[limpia]
    for frase, texto in FRASES.items():
        if limpia.startswith(frase):
            return texto
    clave = re.split(r"[ ,]", limpia, maxsplit=1)[0]
    return PALABRAS.get(clave, "")
