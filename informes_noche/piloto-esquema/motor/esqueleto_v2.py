"""Esqueleto v2 de una lámina desde el catálogo, en segundos (antes lo hacía un subagente en 3-5 min).

Uso:
  python esqueleto_v2.py <moto-catalogo> <figura> <lamina> [--intervalos yamaha_nmax_155] [--tareas filtro-aire,bujia] [--escribir]

Sin --escribir solo imprime el resumen (grupos y tornillería propuestos) para revisarlo; con --escribir crea datos/<lamina>.json
(si ya existe, no lo pisa: sale datos/<lamina>.esqueleto.json).

Qué arma (todo es propuesta; el criterio mecánico es de la creadora):
- fichas{ref}: nombre sugerido (glosario inglés→español del catálogo), cat «DESCRIPCIÓN · n pieza(s)», codigo, certeza de catálogo
  y certezaDe {que: ok}; los textos pedagógicos van vacíos (se llenan con plantillas_ficha.py o a mano).
- v2.grupos: un grupo por conjunto del catálogo (una pieza «ASSY» con sus hijas «.X», «..Y») y el resto en tramos seguidos;
  la tornillería (BOLT, SCREW, NUT, WASHER, CLIP, COLLAR, GROMMET…) se agrupa como «torn» con la pieza de antes.
- piezas[]: una por ref, con «comun» sugerido para la biblioteca cuando el tipo se reconoce (tornillo, tuerca, arandela, oring…,
  y formas de lámina: abrazadera, manguera, ducto, caja con tapa, placa/empaque);
  anc/et en una rejilla para que el validador corra desde el primer minuto (se reemplazan al dibujar).
- cuando[]: una fila por tarea de intervalos (--tareas), con km, años, fuente y «Seguro» o «Aproximado».
- pasos[]: uno por grupo (orden del catálogo), sin movimientos: se reordenan y se parten al dibujar.
Catálogos en español (Auteco/Bajaj…): se clasifican con catalogo/claves_es.py (descripcion_en si la hay; si no, la primera
palabra: tornillo, tuerca, arandela, resorte, balinera, buje, retén, empaque, placa/disco…) y el nombre sale de la descripción.
"""
import argparse, json, pathlib, re, sys, unicodedata
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI / "catalogo"))
from claves_es import aviso_es, clave_en, es_espanol, nombre_es

GLOSARIO = [  # (expresión del catálogo, nombre en español); gana la primera que calce
    (r"PLUG, SPARK", "Bujía"), (r"COVER, CYLINDER HEAD|HEAD COVER", "Tapa de la culata"), (r"CYLINDER HEAD", "Culata"),
    (r"GUIDE, VALVE", "Guía de válvula"), (r"PLUG, STRAIGHT SCREW", "Tapón roscado"), (r"BOLT, STUD", "Espárrago"),
    (r"PIN, DOWEL", "Pasador guía"), (r"PISTON RING", "Anillos del pistón"), (r"PISTON", "Pistón"), (r"CRANKSHAFT", "Cigüeñal"),
    (r"CRANKCASE", "Cárter"), (r"CAMSHAFT", "Árbol de levas"), (r"ROCKER ARM", "Balancín"), (r"VALVE, INTAKE", "Válvula de admisión"),
    (r"VALVE, EXHAUST", "Válvula de escape"), (r"CAM CHAIN|CHAIN, CAM", "Cadena de distribución"), (r"TENSIONER", "Tensor de la cadena"),
    (r"RADIATOR", "Radiador"), (r"THERMOSTAT", "Termostato"), (r"IMPELLER|WATER PUMP", "Bomba de agua"), (r"^CYLINDER\b", "Cilindro"),
    (r"^ROD\b", "Varilla"), (r"^PLUG\b", "Tapón"),
    (r"ELEMENT, AIR CLEANER", "Filtro de aire"), (r"CASE, AIR CLEANER", "Caja del filtro"), (r"CAP, CLEANER CASE", "Tapa de la caja del filtro"),
    (r"JOINT, AIR CLEANER", "Unión de la caja del filtro"), (r"THROTTLE BODY", "Cuerpo de aceleración"), (r"STEPPING MOTOR", "Motor de ralentí"),
    (r"INJECTOR", "Inyector"), (r"GASKET, MANIFOLD", "Empaque del múltiple"), (r"MANIFOLD", "Múltiple de admisión"),
    (r"PIPE, BREATHER", "Manguera del respiradero"), (r"PIPE, DRAIN", "Manguera de drenaje"), (r"HOSE CLAMP", "Abrazadera"),
    (r"MASTER CYLINDER", "Bomba de freno"), (r"CALIPER", "Cáliper"), (r"DISK, BRAKE", "Disco de freno"), (r"BRAKE PAD", "Pastillas"),
    (r"V-BELT", "Correa"), (r"SHEAVE", "Polea"), (r"CLUTCH", "Clutch"), (r"BEARING", "Rodamiento"), (r"OIL SEAL", "Retén"),
    (r"O-RING", "O-ring"), (r"SEAL", "Sello"), (r"GASKET", "Empaque"), (r"CIRCLIP", "Seguro"), (r"WASHER", "Arandela"), (r"NUT", "Tuerca"),
    (r"BOLT|SCREW", "Tornillo"), (r"CLIP", "Grapa"), (r"COLLAR", "Buje"), (r"GROMMET", "Caucho de montaje"), (r"DAMPER", "Amortiguador"),
    (r"SPRING", "Resorte"), (r"PLATE", "Placa"), (r"DUCT", "Ducto"), (r"HOSE", "Manguera"), (r"PIPE", "Tubo"), (r"\bPIN\b", "Pasador"),
    (r"CAP", "Tapa"), (r"COVER", "Tapa"), (r"BRACKET|BRKT|STAY", "Soporte"), (r"SENSOR", "Sensor"), (r"FILTER", "Filtro"),
]
LUGAR = [  # complemento del catálogo (lo que va tras la coma) → «de …»; gana el primero que calce
    (r"CYLINDER HEAD|HEAD COVER", None), (r"BREATHER", "del respiradero"), (r"MANIFOLD", "del múltiple"), (r"CRANKCASE", "del cárter"),
    (r"AIR CLEANER|CLEANER CASE", "de la caja del filtro"), (r"CALIPER", "del cáliper"), (r"MASTER CYLINDER", "de la bomba"),
    (r"CYLINDER", "del cilindro"), (r"DRAIN", "de drenaje"), (r"RADIATOR", "del radiador"), (r"THERMOSTAT", "del termostato")]
COMPUESTO = {"Empaque": [(r"HEAD COVER", "Empaque de la tapa de la culata"), (r"CYLINDER HEAD", "Empaque de culata"), (r"^GASKET, CYLINDER\b", "Empaque de la base del cilindro")]}
FAMILIAS = [  # grupos por función: el lugar que nombra la descripción manda sobre el orden del catálogo
    (r"PLUG, SPARK", "bujia", "Bujía"), (r"HEAD COVER|COVER, CYLINDER HEAD", "tapa-culata", "Tapa de la culata"),
    (r"CYLINDER HEAD|GUIDE, VALVE", "culata", "Culata"), (r"^CYLINDER\b|GASKET, CYLINDER\b", "cilindro", "Cilindro"),
    (r"PISTON", "piston", "Pistón"), (r"CRANKSHAFT|CRANK\b", "ciguenal", "Cigüeñal"), (r"CAMSHAFT|ROCKER|VALVE, (INTAKE|EXHAUST)", "levas", "Levas y válvulas"),
    (r"CAM CHAIN|CHAIN, CAM|TENSIONER", "cadena", "Cadena de distribución"), (r"RADIATOR|THERMOSTAT|IMPELLER|WATER PUMP|RESERVOIR", "refrigeracion", "Refrigeración")]
# Figuras de rueda (título con RUEDA/WHEEL): grupos por eje, freno, arrastre y rueda; se miran la descripción en español y la clave.
# Las piezas sin lugar propio (buje, balinera, retén…) van con la de antes, salvo que digan «rueda».
FAMILIAS_RUEDA = [
    (r"EJE RUEDA|\bAXLE\b|TENSOR(ES)? (DE )?CADENA|CHAIN (ADJUSTER|PULLER)|PULLER, CHAIN", "eje", "Eje y tensores"),
    (r"PORTA ?BANDAS|\bBANDAS\b|ABREBANDAS|INDICADOR (DE )?DESGASTE|BRAKE SHOE|SHOE, BRAKE|CAMSHAFT, BRAKE|BRAKE PANEL|DISCO DE FRENO|DISK, BRAKE", "freno", "Freno"),
    (r"SPROCKET|ARRAST|CADENA DE TRANSMISI|DRIVE CHAIN|CHAIN, DRIVE|\bCORONA\b|PI[ÑN]ON|DAMPER, HUB|CLUTCH, HUB", "arrastre", "Arrastre (cadena, piñón y corona)"),
    (r"CAMPANA|\bHUB\b|\bRIN\b|\bRIM\b|RADIOS?\b|SPOKE|NEUM[AÁ]TICO|\bTIRE\b|\bTYRE\b|LLANTA|\bTUBE\b|\bRUEDA\b|\bWHEEL\b", "rueda", "Rueda")]
SIN_LUGAR = re.compile(r"^(BUJE|BUSH|COLLAR|BALINERA|BEARING|RODAMIENTO|RETEN|RETENEDOR|OIL SEAL|ARANDELA|WASHER|SEPARADOR|SPACER)", re.I)
KIT = re.compile(r"^\.*\s*(KIT|JGO|JUEGO)\b", re.I)
TORN = re.compile(r"\b(BOLT|SCREW|NUT|WASHER|CLIP|CIRCLIP|COLLAR|GROMMET|PIN, DOWEL)\b")
COMUN = [(r"^(SPROCKET|CORONA|PI[ÑN]ON)\b|SPROCKET, (DRIVE|DRIVEN)", "pinon"), (r"^(CADENA DE TRANSMISION|CHAIN, DRIVE|DRIVE CHAIN)|^ARRAST|KIT ARRASTRE|CHAIN KIT", "cadena"),
         (r"^(RIN|RIM)\b|^WHEEL, (FRONT|REAR)|CAST WHEEL", "rin"), (r"^(LLANTA|TIRE|TYRE)\b", "llanta"), (r"^(EJE RUEDA|AXLE|SHAFT, WHEEL)", "eje"),
         (r"^TENSOR (DE )?CADENA|ADJUSTER, CHAIN|PULLER, CHAIN|CHAIN PULLER", "tensor"), (r"GROMMET", "arandela"), (r"BOLT|SCREW", "tornillo"), (r"NUT", "tuerca"), (r"WASHER", "arandela"), (r"CIRCLIP", "seguro"), (r"O-RING", "oring"),
         (r"OIL SEAL", "reten"), (r"BEARING", "rodamiento"), (r"COLLAR|BUSH", "buje"), (r"SPRING", "resorte"), (r"\bPIN\b", "pasador"),
         (r"HOSE CLAMP|\bCLIP\b|\bCLAMP\b", "abrazadera"), (r"\bPIPE\b|\bHOSE\b", "manguera"), (r"\bDUCT\b|FUNNEL", "ducto"),
         (r"\bCASE\b|\bBOX\b", "caja"), (r"GASKET|\bPLATE\b", "placa")]


MEDIDAS = {"tornillo": {"cabeza": 10, "largo": 40, "d": 10}, "tuerca": {"r": 12}, "arandela": {"r": 12, "ri": 6}, "seguro": {"r": 12},
           "oring": {"r": 12, "g": 3}, "reten": {"r": 18, "ri": 10}, "rodamiento": {"r": 18, "ri": 9}, "buje": {"r": 9, "ri": 5, "largo": 18},
           "resorte": {"r": 9, "largo": 36}, "pasador": {"r": 4, "largo": 28},
           "abrazadera": {"r": 9}, "manguera": {"g": 9, "puntos": [[0, 0], [40, 20], [80, 20]]}, "ducto": {"r0": 18, "r1": 24, "puntos": [[0, 0], [50, -10]]},
           "caja": {"w": 120, "h": 90, "prof": 18, "tapa": True},
           "rin": {"r": 110, "ri": 26}, "llanta": {"r": 140, "ri": 112}, "pinon": {"r": 40, "dientes": 15}, "cadena": {"c1": [-120, 0], "r1": 22, "c2": [120, 0], "r2": 55},
           "eje": {"cabeza": 12, "d": 14, "largo": 160}, "tensor": {"w": 34, "h": 24}, "placa": {"contorno": [[-24, -16], [24, -16], [24, 16], [-24, 16]], "huecos": [[0, 0, 9]]}}
GRANDE = {"caja", "ducto", "manguera", "rin", "llanta", "pinon", "cadena", "tensor"}   # formas grandes: se ven armadas («vis»: «arm»)


def grilla(moto, figura, C):
    """Ronda 7: la imagen del plano para comprobar el orden de las piezas. Usa despiece_local/grillas/*-figNN.png si existe;
    si no, la genera con pymupdf (el PDF solo se lee) en la carpeta temporal del sistema (tallerya-grillas): la página del plano
    de la figura a 900 px de ancho. Devuelve (ruta, recién generada)."""
    gr = RAIZ / "despiece_local" / "grillas"
    cod = moto.split("-")[-1].upper()
    n = f"{int(figura):02d}" if str(figura).isdigit() else str(figura)
    hay = [x for x in gr.glob(f"*-fig{n}.png") if cod in x.name.upper()] if gr.exists() else []
    if hay: return hay[0], False
    fig = C["figuras"][str(figura)]; fuente = pathlib.Path(str(C.get("fuente", "")).split(" (")[0]).name
    pdf = next((x for base in ("despiece_local", "manual_despiece") for x in (RAIZ / base).rglob(fuente)), None) if fuente else None
    if not pdf or not fig.get("paginas"): return None, False
    try:
        import pymupdf
    except ImportError:
        return None, False
    d = pymupdf.open(str(pdf)); p0 = fig["paginas"][0] - 1
    # ronda 8: el plano va en la misma página que la tabla (comprobado en Yamaha NMAX y Colombia, Auteco/Bajaj, AKT y Honda)
    pg = d[p0]; z = min(900 / pg.rect.width, 2.4)
    import tempfile   # fuera del repo y de las carpetas de fuentes: carpeta temporal local
    sal = pathlib.Path(tempfile.gettempdir()) / "tallerya-grillas"; sal.mkdir(exist_ok=True); dest = sal / f"{moto}-fig{n}.png"
    if dest.exists(): return dest, False
    pg.get_pixmap(matrix=pymupdf.Matrix(z, z)).save(str(dest))
    return dest, True


def nombre_de(desc):
    desc = re.sub(r"\s+\d+$", "", desc)   # «ROD 1» → «ROD»
    coma = desc.find(",")
    for ex, es in GLOSARIO:
        m = re.search(ex, desc)
        if m and (coma < 0 or m.start() < coma):   # manda el sustantivo («GASKET, HEAD COVER» es un empaque, no una tapa)
            for ex2, comp in COMPUESTO.get(es, []):
                if re.search(ex2, desc): return comp
            if "," in desc and es in ("Empaque", "Tornillo", "Tapa", "Placa", "Tubo", "Manguera", "Retén", "Soporte", "Tapón"):
                resto = desc.split(",", 1)[1]
                de = next((d for ex2, d in LUGAR if re.search(ex2, resto)), None)
                if de: return f"{es} {de}"
            return es
    return desc.title()


def familia_de(desc, desc_cat="", rueda=False):
    if rueda:
        u = re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", desc_cat.upper())) + " | " + desc
        fams = FAMILIAS_RUEDA[3:] if SIN_LUGAR.match(desc_cat.lstrip(". ")) or SIN_LUGAR.match(desc) else FAMILIAS_RUEDA
        if SIN_LUGAR.match(desc_cat.lstrip(". ")) or SIN_LUGAR.match(desc):   # sin lugar propio: solo «rueda» si lo dice
            return ("rueda", "Rueda") if re.search(r"\bRUEDA\b|\bWHEEL\b", u) else None
        f = next(((i, n) for ex, i, n in fams if re.search(ex, u)), None)
        if f: return f
    return next(((i, n) for ex, i, n in FAMILIAS if re.search(ex, desc)), None)


def kits_alternos(partes):
    """{ref alterna: ref base}: «20A» cuando ya está «20» y los dos son kit/juego (el mismo repuesto con otra marca o largo).
    El alterno no lleva dibujo, ficha ni grupo: va en «kits» y en el cat de la base."""
    refs = {p["ref"]: p for p in partes}; alt = {}
    for p in partes:
        m = re.fullmatch(r"(\d+)[A-Za-z]", p["ref"])
        if m and m.group(1) in refs and KIT.match(p["descripcion"]) and KIT.match(refs[m.group(1)]["descripcion"]):
            alt[p["ref"]] = m.group(1)
    return alt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("moto"); ap.add_argument("figura"); ap.add_argument("lamina")
    ap.add_argument("--intervalos"); ap.add_argument("--tareas", default=""); ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()
    m = re.fullmatch(r"\s*([A-Za-z])\s*-?\s*(\d+)\s*", a.figura)   # AKT: «E4» o «E-4» (motor) no choca con «F4» (chasis)
    a.figura = m.group(1).upper() + m.group(2) if m else a.figura
    CAT = json.loads((AQUI / f"catalogo/{a.moto}.json").read_text(encoding="utf-8"))
    fig = CAT["figuras"][str(a.figura)]
    g, nueva = grilla(a.moto, a.figura, CAT)
    print(f"  plano: {g}" + (" (generado ahora desde el PDF; míralo una vez, ≤ 900 px)" if nueva else "") if g else "  plano: sin grilla ni PDF a mano; recórtalo con pymupdf (anexo «Para ver la lámina»)")
    partes = fig["partes"]
    rueda = bool(re.search(r"RUEDA|WHEEL", fig.get("titulo", "").upper()))
    alternos = kits_alternos(partes)
    for r, b in alternos.items(): print(f"  kit {r} = otro repuesto del kit {b}: sin ficha ni dibujo, va en «kits» y en el cat de {b}")
    kits = {r: [b] for r, b in alternos.items()}
    pal = re.findall(r"\b(CBS|ABS)\b", (json.loads((AQUI / f"catalogo/{a.moto}.json").read_text(encoding="utf-8")).get("moto") or "").upper())
    if pal: print(f"  aviso: el modelo del catálogo dice {'/'.join(pal)}: es parte del nombre de la moto. Pon «moto» igual al catálogo y no lo nombres como sistema de la figura si esta no lo trae (el control «la lámina dice {pal[0]}» lo mira)")
    partes = [p for p in partes if p["ref"] not in alternos]
    fichas, piezas, nombres, grupos = {}, [], {}, []
    actual = None   # grupo en curso
    usados = {}
    for i, p in enumerate(partes):
        ref, cant, desc_cat = p["ref"], p.get("cantidad", 1), p["descripcion"]
        desc0 = clave_en(desc_cat, p.get("descripcion_en"))   # para las reglas (igual al catálogo si es Yamaha)
        nivel = len(desc0) - len(desc0.lstrip("."))
        desc = desc0.lstrip(".")
        nom = nombre_es(desc_cat) if es_espanol(desc_cat) else nombre_de(desc)
        if es_espanol(desc_cat) and aviso_es(desc_cat): print(f"  aviso {ref}: {aviso_es(desc_cat)}")
        usados.setdefault(nom, []).append(ref)
        nombres[ref] = nom
        F = {"nombre": nom, "cat": f"{desc_cat.lstrip('.')} · {cant} pieza{'s' if cant != 1 else ''}", "que": "", "sirve": "", "sintomas": [], "fallas": [],
             "decision": "", "porque": "", "dif": "", "cuando": "", "arrastra": [], "conecta": [],
             "certeza": [["ok", f"Nombre y cantidad: catálogo {a.moto}, fig. {a.figura}."]], "certezaDe": {"que": "ok"}}
        if p.get("codigo"): F["codigo"] = p["codigo"]
        for r, b in alternos.items():
            if b == ref:
                q = next(x for x in fig["partes"] if x["ref"] == r)
                F["cat"] += f" · también en el kit ref. {r} ({q['descripcion']}, {q.get('codigo') or 'sin código'})"
        fichas[ref] = F
        comun = next((c for ex, c in COMUN if re.search(ex, desc)), None)
        pz = {"id": ref, "n": ref, "anc": [100 + (i % 8) * 95, 100 + (i // 8) * 95], "et": [0, -30], "vis": "arm"}
        if comun: pz["comun"] = comun; pz["p"] = json.loads(json.dumps(MEDIDAS[comun])); pz["vis"] = "arm" if comun in GRANDE else "exp"
        if comun and "GROMMET" in desc: pz["p"].update(r=10, ri=4, e=6, material="plast")   # caucho de montaje: arandela gruesa de plástico   # biblioteca: ya se dibuja; se ajustan medidas y lugar
        piezas.append(pz)
        es_torn = bool(TORN.search(desc)) and nivel == 0 or (bool(TORN.search(desc)) and nivel > 0 and actual is None)
        fam = None if (es_torn or (nivel > 0 and actual is not None and actual.get("_conjunto"))) else familia_de(desc, desc_cat, rueda)
        if fam:   # grupo por función: reúne piezas del mismo lugar aunque el catálogo las separe
            g = next((x for x in grupos if x["id"] == fam[0]), None)
            if g is None:
                g = {"id": fam[0], "nombre": fam[1], "piezas": [], "torn": [], "pasos": [], "_conjunto": True}; grupos.append(g)
            g["piezas"].append(ref); actual = g; continue
        if not es_torn and nivel == 0 and actual is not None and actual["id"] in {f[1] for f in FAMILIAS + FAMILIAS_RUEDA} and (rueda or "ASSY" not in desc):
            actual["piezas"].append(ref); continue   # sin lugar propio (empaque, varilla, retén): va con la pieza de antes
        if es_torn and actual is not None:
            actual["torn"].append({"nombre": f"{nom}s" if cant > 1 else nom, "corto": nom.split()[0] + ("s" if cant > 1 else ""), "ids": [ref], "cant": cant})
            continue
        if nivel > 0 and actual is not None and actual.get("_conjunto"):
            actual["piezas"].append(ref); continue
        conjunto = "ASSY" in desc or (i + 1 < len(partes) and partes[i + 1]["descripcion"].startswith("."))
        actual = {"id": re.sub(r"[^a-z]+", "-", unicodedata.normalize("NFD", nom.lower()).encode("ascii", "ignore").decode()).strip("-")[:14].strip("-") or f"g{ref}", "nombre": nom, "piezas": [ref], "torn": [], "pasos": [],
                  "_conjunto": conjunto}
        grupos.append(actual)
    # tramos sueltos de una sola pieza seguida: se juntan con el grupo anterior si no son conjunto (propuesta, se revisa)
    juntos = []
    for g in grupos:
        if juntos and not g["_conjunto"] and not juntos[-1]["_conjunto"] and len(juntos[-1]["piezas"]) < 4:
            juntos[-1]["piezas"] += g["piezas"]; juntos[-1]["torn"] += g["torn"]
        else: juntos.append(g)
    cuenta = {}
    for g in juntos:   # ids y nombres de grupo únicos («Polea», «Polea 2»): la creadora les pone el nombre de verdad
        cuenta[g["nombre"]] = cuenta.get(g["nombre"], 0) + 1
        if cuenta[g["nombre"]] > 1: g["nombre"] += f" {cuenta[g['nombre']]}"; g["id"] += f"-{cuenta[g['nombre'].rsplit(' ', 1)[0]]}"
    vistos_id = {}
    for g in juntos:   # ids únicos aunque los nombres difieran («juego-de-disco» de «Juego de discos» y «Juego de disco separadores»)
        vistos_id[g["id"]] = vistos_id.get(g["id"], 0) + 1
        if vistos_id[g["id"]] > 1: g["id"] = f"{g['id']}-{vistos_id[g['id']]}"
    gde = {i: g for g in juntos for i in g["piezas"] + [x for t in g["torn"] for x in t["ids"]]}
    for nom, refs in usados.items():   # nombres repetidos: se distinguen por su grupo (el validador acepta el paréntesis)
        if len(refs) < 2: continue
        vistos = {}
        for r in refs:
            g = gde.get(r); et = g["nombre"].lower() if g and g["nombre"].rsplit(" ", 1)[0] != nom else ""
            if not et and g and g["nombre"] != nom: nombres[r] = fichas[r]["nombre"] = g["nombre"]; continue
            vistos[et] = vistos.get(et, 0) + 1
            if et and vistos[et] == 1: nombres[r] = f"{nom} ({et})"
            elif et: nombres[r] = f"{nom} ({et}, otro)"
            fichas[r]["nombre"] = nombres[r]
    for g in juntos:
        for t in g["torn"]:
            t["nombre"] = nombres[t["ids"][0]].split(" (")[0] + ("s" if t["cant"] > 1 and not nombres[t["ids"][0]].split(" (")[0].endswith("s") else "")
            t["corto"] = t["nombre"].split()[0]
    PZ = {p["id"]: p for p in piezas}
    for j, g in enumerate(juntos):   # anclas iniciales: una franja por grupo (columna por grupo, filas por pieza)
        for k, i in enumerate(g["piezas"] + [x for t in g["torn"] for x in t["ids"]]):
            PZ[i]["anc"] = [70 + (j % 6) * 140 + (k % 2) * 60, 90 + (j // 6) * 330 + (k // 2) * 55]; PZ[i]["p"] = {**PZ[i].get("p", {}), "x": PZ[i]["anc"][0], "y": PZ[i]["anc"][1]} if "comun" in PZ[i] else PZ[i].get("p")
            if PZ[i].get("p") is None: PZ[i].pop("p", None)
    pasos = []
    for j, g in enumerate(juntos):
        g.pop("_conjunto"); g["pasos"] = [j]
        m = {i: [0, 0] for i in g["piezas"] + [x for t in g["torn"] for x in t["ids"]]}
        pasos.append({"t": f"<b>{g['nombre']}.</b> (texto del paso)", "m": m})
    cuando = []
    if a.intervalos and a.tareas:
        T = json.loads((RAIZ / f"garaje/intervalos/{a.intervalos}.json").read_text(encoding="utf-8"))["tareas"]
        for k in [x for x in a.tareas.split(",") if x]:
            if k not in T:
                print(f"  aviso: la tarea «{k}» no está en {a.intervalos}.json (hay: {', '.join(T)}); esa fila de «Cuándo» va a mano, sin «tarea»"); continue
            t = T[k]; km, dias = t.get("km"), t.get("dias")
            if not km and not dias:
                print(f"  aviso: la tarea «{k}» no tiene km ni días en {a.intervalos}.json; esa fila de «Cuándo» va a mano (fuente del manual, «aprox.» y a «pendientes»)"); continue
            cada = " o ".join(x for x in (f"<b>{km:,} km</b>".replace(",", ".") if km else "", f"{round(dias / 365)} años" if dias else "") if x)
            s = "esq-s-ap\">Aproximado" if t.get("aproximado") else "esq-s-ok\">Seguro"
            cuando.append({"que": k.replace("-", " ").capitalize(), "cuando": f"Cada {cada}.", "fuente": f"{t.get('fuente', '')} <span class=\"{s}</span>", "tarea": k})
    tit = fig.get("titulo", "").capitalize()
    D = {"cabeza": {"cinta": f"TallerYa · esquema piloto · lámina {a.figura}", "titulo": f"{tit} · {a.moto}", "aviso": "Prototipo local. Dibujos propios."},
         "visor": {"titulo": tit, "sub": f"Lámina {a.figura} · {len(partes)} piezas"},
         "textos": {"pestanasAria": "Vistas de la lámina", "laminaAria": f"Dibujo de la lámina {a.figura}", "introFunciona": "", "introCadenas": "", "introCuando": ""},
         "pie": "", "encuadreArmado": [0, 0, 900, 700], "radioToqueMin": 9,
         "funciona": {"vbCelular": "0 0 470 560", "vbEscritorio": "0 0 900 320", "pasos": []},
         "fuentes": {"seguro": [], "aproximado": [], "lista": []}, "comun": {"atras": [0.5, -0.32], "colores": {}},
         "lamina": a.lamina, "moto": a.moto, "figura": int(a.figura) if str(a.figura).isdigit() else a.figura, "catalogo": a.moto, "intervalos": a.intervalos or "", "arte": a.lamina,
         "refsFigura": [p["ref"] for p in fig["partes"]], **({"kits": kits} if kits else {}), "nombres": nombres, "ordenChips": [p["ref"] for p in partes], "ocultas": [],
         "piezas": piezas, "pasos": pasos, "textoArmado": "", "fichas": fichas, "cadenas": [], "cuando": cuando, "sujeta": {},
         "v2": {"grupos": juntos, "con3d": [], "toqueExtra": [], "inicio": f"Piezas: {fig.get('titulo', '').lower()}"}}
    print(f"fig. {a.figura} «{fig.get('titulo', '')}»: {len(partes)} refs → {len(juntos)} grupos propuestos")
    for g in juntos:
        print(f"  {g['id']:14} {g['nombre']:28} piezas {','.join(g['piezas']):24} torn {', '.join(t['corto'] + '(' + ','.join(t['ids']) + ')' for t in g['torn'])}")
    print("  biblioteca (ya dibujadas):", ", ".join(f"{p['id']}={p['comun']}" for p in piezas if "comun" in p))
    print("  arte propio por hacer:", ", ".join(p["id"] for p in piezas if "comun" not in p))
    for p in piezas:
        if p.get("comun") == "cadena" and re.search(r"ARRAST|KIT", fichas[p["id"]]["cat"].upper()):
            print(f"  kit de arrastre {p['id']}: dibújalo como cadena ({p['id']}a) + piñón y corona con «pinon» ({p['id']}b, {p['id']}c), en un solo grupo")
    if cuando: print("  cuando:", "; ".join(c["que"] + ": " + re.sub("<[^>]+>", "", c["cuando"]) for c in cuando))
    if a.escribir:
        dest = AQUI / f"datos/{a.lamina}.json"
        # ronda 3: siempre queda la copia limpia <lamina>.esqueleto.json; el script de armado parte de ella (nunca de su propia salida)
        copia = AQUI / f"datos/{a.lamina}.esqueleto.json"
        texto = json.dumps(D, ensure_ascii=False, indent=1)
        copia.write_text(texto, encoding="utf-8")
        if not dest.exists(): dest.write_text(texto, encoding="utf-8"); print("escrito", dest.name, "y", copia.name)
        else: print("escrito", copia.name, f"({dest.name} ya existía: no se tocó)")


if __name__ == "__main__":
    main()
