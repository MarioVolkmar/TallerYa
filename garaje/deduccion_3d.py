"""Deduce la pieza y el acabado de una parte 3D desde el texto libre del usuario («guardabarros delantero negro»).

Palabras clave + frases aprendidas del glosario (garaje/etiquetas_3d/glosario.json). No inventa: lo que no entiende
queda «por revisar» (pieza «otra» y/o acabado sin definir).
"""
import re
import unicodedata


def normalizar(texto):
    """Minúsculas, sin tildes ni signos: «Plástico NEGRO!» → «plastico negro»."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


DEL = re.compile(r"\b(del|delant\w*|frontal|frente)\b")
TRAS = re.compile(r"\b(tras\w*|atras|posterior)\b")

# (patrón, pieza) o (patrón, pieza delantera, pieza trasera); gana la primera que aparezca
REGLAS_PIEZA = [
    (r"\b(basura|quitar|suelto|resto)\b", "basura"),
    # (gato o soporte lateral antes que «lateral» = tapa lateral: va en metal negro, no del color de la moto)
    (r"\b(gato|gatos|soporte lateral|pata lateral|pata de cabra|caballete|descanso)\b", "pata"),
    (r"\b(llanta|llantas|neumatico)\b", "llanta_del", "llanta_tras"),
    (r"\b(rin|rines|aro|rayos)\b", "rin_del", "rin_tras"),
    (r"\b(disco|pastillas?|freno|frenos|tambor)\b", "disco_del", "freno_tras"),
    (r"\b(guardabarros?|guardafango|fender)\b", "guardabarros_del", "guardabarros_tras"),
    (r"\bprotector (del )?escape\b", "protector_escape"),
    (r"\b(escape|exosto|silenciador|mofle|muffler)\b", "escape"),
    (r"\b(cvt|variador)\b", "cvt"),
    (r"\bguardacadena\b", "guardacadena"),
    (r"\b(cadena|pinon\w*|arrastre)\b", "cadena"),
    (r"\b(tijera|tijeras)\b", "basculante"),
    (r"\b(direccional\w*|cocuyo\w*|intermitente\w*)\b", "direccional"),
    (r"\b(stop|stops|luz trasera)\b", "stop"),
    (r"\b(farola|farolas|frente)\b", "frente"),
    (r"\b(faro|faros|foco|bombillo|luz delantera|optico)\b", "faro"),
    (r"\b(tapa lateral|tapas laterales|tapa|tapas|lateral|laterales|costado)\b", "tapa_lateral"),
    (r"\b(tanque|deposito)\b", "tanque"), (r"\b(asiento|silla|sillin|sillon)\b", "asiento"),
    (r"\b(colin|cola)\b", "colin"), (r"\b(carenado|carenaje|cubierta)\b", "carenado"),
    (r"\b(visor|parabrisas|vidrio|cupula)\b", "visor"), (r"\b(escudo|cuello|pechera)\b", "escudo"),
    (r"\b(pisadera|piso)\b", "pisadera"), (r"\b(bajos|quilla)\b", "bajos"),
    (r"\b(tablero|reloj|velocimetro|tacometro|pantalla)\b", "tablero"), (r"\b(manubrio|manillar)\b", "manubrio"),
    (r"\b(puno|punos|empunadura\w*)\b", "puno"), (r"\b(manigueta\w*|palanca\w*)\b", "manigueta"),
    (r"\b(espejo|espejos|retrovisor\w*)\b", "espejo"),
    (r"\b(horquilla|barras|telescopic\w+|suspension delantera)\b", "horquilla"),
    (r"\b(amortiguador\w*|suspension trasera|shock)\b", "amortiguador"), (r"\b(basculante|brazo oscilante)\b", "basculante"),
    (r"\b(motor|bloque|cilindro|culata|carter)\b", "motor"), (r"\b(chasis|cuadro|marco)\b", "chasis"),
    (r"\b(posapies?|pedal\w*|estribo\w*|reposapies)\b", "posapies"), (r"\b(pata|caballete|descanso)\b", "pata"),
    (r"\b(portaplaca|placa)\b", "portaplaca"), (r"\b(parrilla|rack|portaequipaje)\b", "parrilla"), (r"\bradiador\b", "radiador"),
]
# (patrón, acabado); gana el primero que aparezca, de lo más específico a lo más general
REGLAS_ACABADO = [
    (r"\b(oculta|oculto|escondida)\b", "oculta"),
    (r"\b(mica ambar|ambar|naranja)\b", "mica_ambar"),
    (r"\b(mica roja|roja de stop)\b", "mica_roja"),
    (r"\b(mica|micas|cristal|transparente|translucid\w+)\b", "mica_faro"),
    (r"\b(cromo|cromad\w+|espejado)\b", "cromo"),
    (r"\b(caucho|goma|llanta|llantas|neumatico)\b", "caucho"),
    (r"\b(vinilo|cuero|tapizad\w+|cojin)\b", "vinilo"),
    (r"\b(brillant\w+|brillo|piano)\b", "plastico_brillo"),
    (r"\b(aluminio|plateado|plata|metal\w*)\b", "aluminio"),
    (r"\b(pintura secundaria|secundari\w+|blanc\w+|segundo color|franja)\b", "pintura_secundaria"),
    (r"\b(negro|negra|negros|negras|plastic\w+|mate|oscur\w+)\b", "plastico_mate"),
    (r"\b(pintura|principal|color|colores|azul|rojo|roja|verde|amarill\w+|gris|morado|vino|dorad\w+|pintad\w+|de la moto)\b", "pintura"),
]
# Acabado habitual cuando el texto no dice color
ACABADO_DE_PIEZA = {
    "llanta_del": "caucho", "llanta_tras": "caucho", "rin_del": "aluminio", "rin_tras": "aluminio", "disco_del": "aluminio",
    "freno_tras": "aluminio", "faro": "mica_faro", "stop": "mica_roja", "direccional": "mica_ambar", "asiento": "vinilo",
    "motor": "motor", "cvt": "motor", "chasis": "chasis", "basculante": "chasis", "visor": "mica_faro", "escape": "aluminio",
    "horquilla": "cromo", "amortiguador": "aluminio", "radiador": "aluminio", "cadena": "motor", "basura": "oculta",
    "protector_escape": "plastico_brillo", "espejo": "plastico_brillo", "tablero": "plastico_brillo", "tanque": "pintura",
    "colin": "pintura", "carenado": "pintura", "tapa_lateral": "pintura", "escudo": "pintura", "frente": "pintura",
    "guardabarros_del": "pintura", "guardabarros_tras": "plastico_mate", "pata": "chasis",
}


def _pieza(t):
    for regla in REGLAS_PIEZA:
        if re.search(regla[0], t):
            if len(regla) == 2:
                return regla[1]
            return regla[2] if TRAS.search(t) and not DEL.search(t) else regla[1]
    return None


def deducir(texto, frases=None):
    """{pieza, acabado, por_revisar}. `frases`: {texto normalizado: {pieza, acabado}} aprendidas del glosario."""
    t = normalizar(texto)
    if not t:
        return {"pieza": None, "acabado": None, "por_revisar": True}
    if frases and t in frases:
        return {"pieza": frases[t]["pieza"], "acabado": frases[t]["acabado"], "por_revisar": False}
    pieza = _pieza(t)
    acabado = next((ac for patron, ac in REGLAS_ACABADO if re.search(patron, t)), None)
    if pieza is None:
        # sin pieza conocida pero con color o material («plástico mate», «cromo», «pintura principal»): vale, la pieza queda
        # como «otra» (tapa o parte genérica). Lo que no dice ni pieza ni material sí queda «por revisar».
        if acabado:
            return {"pieza": "otra", "acabado": acabado, "por_revisar": False}
        return {"pieza": None, "acabado": None, "por_revisar": True}
    # las luces y las llantas no se pintan: su acabado es el de siempre
    if pieza in ("llanta_del", "llanta_tras"):
        acabado = "caucho"
    elif pieza in ("faro", "stop", "direccional") and acabado in (None, "pintura", "plastico_mate", "mica_faro"):
        acabado = ACABADO_DE_PIEZA[pieza]
    elif pieza == "pata" and acabado in (None, "pintura", "plastico_mate", "plastico_brillo"):
        acabado = "chasis"  # (gato y caballete: metal negro aunque el texto diga «negro» o «color»)
    elif acabado is None:
        acabado = ACABADO_DE_PIEZA.get(pieza, "plastico_mate")
    return {"pieza": pieza, "acabado": acabado, "por_revisar": False}
