"""Clave «estilo Yamaha» (inglés en mayúsculas) de una descripción de catálogo, para clasificarla con las mismas reglas.

La usan esqueleto_v2.py y plantillas_ficha.py:
- si la parte trae «descripcion_en», se usa esa;
- una descripción Yamaha (inglés en mayúsculas) pasa igual, así la salida de la NMAX no cambia;
- una descripción en español («Tornillo Resorte Clutch», «KIT DISCOS CLUTCH») se clasifica por su PRIMERA palabra, el
  sustantivo («Porta Resorte» no es un resorte), y se le agregan los lugares que nombre (cigüeñal, culata, cilindro…).
  «Kit», «Juego», «Conjunto», «Ensamble» o «Completo» la marcan como conjunto (ASSY).
"""
import re, unicodedata

PRIMERA = [  # primera palabra en español → sustantivo Yamaha (lo que leen TORN, COMUN, TIPOS y GLOSARIO)
    (r"TORNILLOS?|PERNOS?|ESPARRAGOS?", "BOLT"), (r"TUERCAS?", "NUT"), (r"ARANDELAS?", "WASHER"), (r"RESORTES?|MUELLES?", "SPRING"),
    (r"BALINERAS?|RODAMIENTOS?|COJINETES?|RULIMANES?", "BEARING"), (r"BUJES?|CASQUILLOS?", "BUSH"),
    (r"RETEN(ES)?|RETENEDOR(ES)?|SELLOS? DE ACEITE", "OIL SEAL"), (r"EMPAQUES?|JUNTAS?|EMPAQUETADURAS?", "GASKET"),
    (r"SELLOS?", "SEAL"), (r"O-?RINGS?|ORINGS?|ANILLOS?", "O-RING"), (r"SEGUROS?|CIRCLIPS?|PINES? SEGURO", "CIRCLIP"),
    (r"PASADORES?|PINES?", "PIN"), (r"PLACAS?|DISCOS?|PLATINAS?", "PLATE"), (r"ABRAZADERAS?|GRAPAS?", "CLAMP"),
    (r"MANGUERAS?", "HOSE"), (r"TUBOS?", "PIPE"), (r"CAUCHOS?|GOMAS?", "GROMMET"), (r"CAJAS?", "CASE"),
    (r"DUCTOS?|CONDUCTOS?", "DUCT"), (r"BUJIAS?", "PLUG, SPARK"), (r"TAPAS?|CUBIERTAS?|TAPONES?", "COVER"),
    (r"SOPORTES?|BASES?", "BRACKET"), (r"FILTROS?|ELEMENTOS?", "FILTER"), (r"SENSOR(ES)?", "SENSOR"), (r"AMORTIGUADOR(ES)?", "DAMPER"),
]
AMBIGUAS = r"CIRCLIPS?|O-?RINGS?|ORINGS?|SENSORS?|SENSORES|PINS?|BASE|KIT|DAMPER"
CONJ = r"KIT|JUEGO|JGO|CONJUNTO|ENSAMBLE|ENSAMBLAJE"
LUGARES = [(r"CIGUENAL", "CRANKSHAFT"), (r"CULATA", "CYLINDER HEAD"), (r"CILINDRO", "CYLINDER"), (r"PISTON", "PISTON"),
           (r"ARBOL DE LEVAS|EJE DE LEVAS", "CAMSHAFT"), (r"CADENILLA|CADENA DE DISTRIBUCION", "CAM CHAIN"), (r"TENSOR", "TENSIONER"),
           (r"CARTER", "CRANKCASE"), (r"RADIADOR", "RADIATOR"), (r"TERMOSTATO", "THERMOSTAT"), (r"CALIPER|MORDAZA", "CALIPER"),
           (r"BOMBA DE FRENO", "MASTER CYLINDER"), (r"FILTRO DE AIRE|CAJA DEL FILTRO", "AIR CLEANER"), (r"DRENAJE", "DRAIN")]


def sin_tildes(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def es_espanol(d):
    if re.search(r"[a-záéíóúñ]", d):   # Yamaha escribe todo en mayúsculas
        return True
    pal = sin_tildes(d.upper()).lstrip(".").split()
    if not pal or re.fullmatch(AMBIGUAS, pal[0].strip(",")):   # palabras que también usa Yamaha en inglés
        return False
    return re.fullmatch(CONJ, pal[0]) is not None or any(re.fullmatch(ex, pal[0]) for ex, _ in PRIMERA)


def clave_en(desc, desc_en=None):
    """Descripción para las reglas en inglés. Conserva los puntos de nivel («.X») si los hay."""
    if desc_en:
        return desc_en
    if not es_espanol(desc):
        return desc
    puntos = desc[:len(desc) - len(desc.lstrip("."))]
    u = sin_tildes(desc.lstrip(".").upper())
    pal = u.split()
    conj = bool(pal) and (re.fullmatch(CONJ, pal[0]) is not None or bool({"COMPLETO", "COMPLETA", "CTA"} & set(pal)))
    if pal and re.fullmatch(CONJ, pal[0]) and len(pal) > 1:
        pal = pal[1:]
    sust = ""
    for n in (2, 1):   # «sello de aceite», «pin seguro» antes que una sola palabra
        cab = " ".join(pal[:n])
        sust = next((e for ex, e in PRIMERA if re.fullmatch(ex, cab)), "")
        if sust: break
    resto = " ".join(pal)
    lug = [e for ex, e in LUGARES if re.search(ex, resto)]
    base = sust or resto
    return puntos + base + (", " + " ".join(lug) if lug and sust else "") + (" ASSY" if conj else "")


# Abreviaturas de catálogos colombianos (AKT, Auteco) → palabra entera.
ABREV = [(r"jgo", "juego de"), (r"cta", "completa"), (r"cto", "completo"), (r"separad", "separadores"), (r"sliper|slip", "slipper"),
         (r"manza", "manzana"), (r"arand", "arandela"), (r"inf", "inferior"), (r"sup", "superior"), (r"tras", "trasero"), (r"izq", "izquierdo"), (r"der", "derecho")]
# Sufijos de modelo y números de referencia: 125NKD, 125S, 125/R, CGR, NKD, AKT, Rp, 200Sm, «x 6», «16003/P6».
MODELO = re.compile(r"\b(?:\d{2,3}(?:[a-z]+\w*)?(?:/\w+)*|cgr|nkd\w*|akt|rp|x\s?\d+|\d{4,5}(?:/\w+)?)\b", re.I)


def nombre_es(desc):
    """«TORNILLO RESORTE CLUTCH» / «Jgo Discos Clutch 125 x 6» → «Tornillo resorte clutch» / «Juego de discos clutch» (borrador).
    Quita sufijos de modelo (125NKD, CGR, Rp…) y números de balinera, y expande abreviaturas (Jgo, Cta, Separad…).
    Deja las medidas («6x25», «M6x40», «18x3.5»)."""
    d = re.sub(r"\s+", " ", desc.lstrip(".")).strip()
    pal = []
    for w in d.split(" "):
        if re.fullmatch(r"M?\d+(?:[.,]\d+)?[x×]\d+(?:[.,]\d+)?(?:[x×]\d+(?:[.,]\d+)?)?", w, re.I):   # medida: se queda
            pal.append(w); continue
        w2 = MODELO.sub("", w).strip("/ ")
        if not w2: continue
        lw = w2.lower()
        pal.append(next((e for ex, e in ABREV if re.fullmatch(ex, lw)), w2))
    d = re.sub(r"\bx\s?\d+\b", "", " ".join(pal), flags=re.I).strip() or d
    return d[:1].upper() + d[1:].lower() if d else d


def aviso_es(desc):
    """Avisos de clasificación dudosa en español (los imprime esqueleto_v2.py)."""
    u = sin_tildes(desc.upper())
    if re.match(r"PIN(ES)?\b", u) and re.search(r"CLUTCH|PRENSA|SEGURO|EJE|RETEN", u):
        return "«Pin» puede ser un seguro (anillo elástico) y no un pasador: mira la foto y, si es seguro, plantillas_ficha.py --tipo N=seguro"
    return ""
