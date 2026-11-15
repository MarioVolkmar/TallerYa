"""Importa láminas de un catálogo de partes en PDF según un mapa JSON.

Uso (solo en local; requiere `pip install -r requirements-dev.txt`):
    python manage.py importar_despiece despiece_local/N-MAX-BBE4-2024.pdf garaje/despiece_mapas/yamaha_nmax_bbe4.json

Formatos de catálogo (clave "formato" del mapa; por defecto "yamaha"):
- yamaha: "FIG. N TÍTULO REF." arriba y tabla en columnas fijas. Si el catálogo es bilingüe
  (español arriba, inglés debajo), la descripción guardada es la inglesa (la del glosario) y el
  español del catálogo se usa como nombre cuando el glosario no la conoce.
- auteco: catálogos de Auteco (Bajaj, KTM, TVS): "FIGURA Nº N: TÍTULO" y tabla
  FIG. Nº / REFERENCIA / DESCRIPCIÓN / CANT. en español; las columnas se leen del encabezado.
  La figura del mapa puede llevar letra ("12A"); en la base se guarda solo el número.
- honda, hero, suzuki, fichas: ver garaje/despiece_lectores.py. En "fichas" el primer argumento es la
  carpeta con fichas.json (diagramas bajados de tiendas en línea cuando no hay catálogo en PDF).

Por cada figura del mapa guarda la imagen del dibujo y la tabla de partes (ref., código,
descripción, cantidad) y enlaza con el plan de mantenimiento las partes que cumplen las reglas.
Las posiciones de las piezas en el dibujo se marcan después en el admin.
"""
import json
import re

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from garaje.despiece_glosario import ayuda_para, traducir
from garaje.despiece_traductor import traducir_palabras
from garaje.despiece_variantes import nombre_por_sistema
from garaje.despiece_lectores import FORMATOS_EXTRA
from garaje.models import Despiece, Lamina, LineaMoto, ParteDespiece, TareaMantenimiento

# Columnas de la tabla Yamaha (en puntos de la página A4 horizontal del catálogo).
COL_REF = (405, 429)
COL_CODIGO = (429, 500)
COL_DESC = (500, 655)
COL_CANT = (655, 690)


def _centro(w):
    return (w[1] + w[3]) / 2


def _tomar(palabras, col):
    return " ".join(w[4] for w in sorted(palabras, key=lambda w: w[0]) if col[0] <= w[0] < col[1])


# ---------------- Formato Yamaha ----------------

def leer_figuras(pdf):
    """Devuelve {figura: {"titulo", "pagina", "filas": [...]}} recorriendo todo el PDF."""
    figuras = {}
    for pagina in pdf:
        palabras = pagina.get_text("words")
        texto = " ".join(w[4] for w in palabras[:12])
        m = re.match(r"FIG\.\s+(\d+)\s+(.+?)\s+REF\.", texto)
        if not m:
            continue
        numero = str(int(m.group(1)))
        fig = figuras.setdefault(numero, {"titulo": m.group(2).strip(), "pagina": pagina.number, "filas": []})
        fig["filas"].extend(_filas(palabras))
    return figuras


def _filas(palabras):
    refs = sorted((w for w in palabras if COL_REF[0] <= w[0] < COL_REF[1] and w[4].isdigit() and w[1] > 62),
                  key=lambda w: w[1])
    filas = []
    for i, ref in enumerate(refs):
        yc = _centro(ref)
        en_fila = [w for w in palabras if abs(_centro(w) - yc) < 4]
        codigo = _tomar(en_fila, COL_CODIGO).replace("�", "-").replace("–", "-")
        descripcion = _tomar(en_fila, COL_DESC)
        cantidad = _tomar(en_fila, COL_CANT)
        if not codigo:
            continue
        # Catálogo bilingüe: la línea siguiente (sin referencia) trae la descripción en inglés.
        siguiente = refs[i + 1][1] if i + 1 < len(refs) else 10_000
        debajo = [w for w in palabras if yc + 4 < _centro(w) < min(yc + 12, siguiente)
                  and COL_DESC[0] <= w[0] < COL_DESC[1]]
        espanol = ""
        if debajo:
            espanol, descripcion = descripcion, _tomar(debajo, COL_DESC)
        nivel = len(descripcion) - len(descripcion.lstrip("."))
        filas.append({
            "ref": int(ref[4]), "codigo": codigo, "descripcion": descripcion.lstrip(". ").strip(),
            "nivel": nivel, "cantidad": int(cantidad) if cantidad.isdigit() else 1,
            "espanol": espanol.lstrip(". ").strip(),
        })
    return filas


# ---------------- Formato Auteco (Bajaj, KTM, TVS) ----------------

RE_TITULO_PAGINA = re.compile(r"FIGURA\s*(?:N\S{0,2}\s*)?(\d+[A-Z]?)", re.I)   # números de figura que aparecen en una página
RE_FIGURA = re.compile(r"FIGURA\s*(?:N\S{0,2}\s*)?(\d+[A-Z]?)\b\s*:?\s*(.+?)(?:\s*\(\d\s*/\s*\d\s*\))?\s*$", re.I)


def leer_figuras_auteco(pdf):
    figuras = {}
    for pagina in pdf:
        palabras = pagina.get_text("words")
        encabezado = {}
        for w in palabras:
            if w[1] < 160:
                encabezado.setdefault(w[4].upper().rstrip(".").replace("DESCRIPCION", "DESCRIPCIÓN"), w)
        if "DESCRIPCIÓN" not in encabezado or "FIG" not in encabezado:
            continue
        if not ({"REFERENCIA", "PARTE"} & set(encabezado)):
            continue
        # Título de la figura: la línea "FIGURA Nº N: ..." más arriba de la página.
        lineas = []
        for bloque in pagina.get_text("dict")["blocks"]:
            for linea in bloque.get("lines", []):
                texto = " ".join(s["text"] for s in linea["spans"]).strip()
                m = RE_FIGURA.search(texto)
                if m:
                    lineas.append((linea["bbox"][1], m))
        if not lineas:
            continue
        m = min(lineas, key=lambda x: x[0])[1]
        numero = m.group(1).upper()
        fig = figuras.setdefault(numero, {"titulo": m.group(2).strip().upper(), "pagina": pagina.number,
                                          "paginas": [], "filas": [], "x_tabla": encabezado["FIG"][0]})
        fig["paginas"].append(pagina.number)
        fig["filas"].extend(_filas_auteco(palabras, encabezado))
    return figuras


def _filas_auteco(palabras, enc):
    """Lee la tabla fila por fila: [ref] código descripción… cantidad [observación].

    Las columnas no están alineadas con el encabezado en todas las páginas, así que se usa el orden
    de las palabras: la referencia es un número corto, el código la palabra siguiente y la cantidad
    el primer número suelto a la altura de la columna CANT. Si una fila no trae referencia es otra
    opción de la misma pieza (otro código) y hereda la anterior.
    """
    desc = enc["DESCRIPCIÓN"]
    x_min = enc["FIG"][0] - 4
    if "CANT" in enc:
        x_cant = enc["CANT"][0] - 12
    else:  # Boxer: una columna de cantidad por variante (TEC, S1D, UG...) a la derecha de la descripción
        variantes = [w[0] for w in enc.values() if w[0] > desc[0] + 60 and abs(w[1] - desc[1]) < 15
                     and not w[4].upper().startswith("OBSERVACI")]
        x_cant = (min(variantes) if variantes else desc[0] + 100) - 8
    y_tabla = desc[3] + 4
    filas_y = {}
    for w in sorted((w for w in palabras if w[0] >= x_min and w[1] > y_tabla), key=_centro):
        clave = next((y for y in filas_y if abs(y - _centro(w)) < 3), _centro(w))
        filas_y.setdefault(clave, []).append(w)
    filas, ref_anterior = [], None
    for clave in sorted(filas_y):
        fila = sorted(filas_y[clave], key=lambda w: w[0])
        textos = [w[4] for w in fila]
        if re.fullmatch(r"\d{1,3}", textos[0]) and len(textos) > 2:
            ref, resto = int(textos[0]), fila[1:]
        elif ref_anterior is not None and re.search(r"\d", textos[0]) and len(textos) > 1:
            ref, resto = ref_anterior, fila
        else:
            continue
        codigo = resto[0][4]
        descripcion, cantidad, anio = [], 1, None
        for w in resto[1:]:
            if re.fullmatch(r"(19|20)\d\d", w[4]):
                anio = w[4]                                  # "x Hasta Modelo 2014": el año no es la cantidad
                continue
            if w[0] >= x_cant:
                if re.fullmatch(r"\d{1,2}", w[4]):
                    cantidad = int(w[4])
                    break
                continue                                     # columnas de variantes (guiones): no son descripción
            descripcion.append(w[4])
        descripcion = " ".join(descripcion).strip()
        if not re.search(r"\d", codigo):
            continue
        modelo = re.search(r"(?i)\bx\s+(hasta|desde)\s+modelo\b", descripcion)
        if modelo:
            descripcion = (descripcion[:modelo.start()].strip() + f" ({modelo.group(1).lower()} modelo{' ' + anio if anio else ''})").strip()
        if not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{2}", re.sub(r"\((hasta|desde) modelo[^)]*\)", "", descripcion)):
            # Solo guiones o solo "(desde modelo 2015)": otra versión de la pieza anterior con la misma referencia
            previa = next((f for f in reversed(filas) if f["ref"] == ref), None)
            if not previa:
                continue
            base = re.sub(r"\s*\((hasta|desde) modelo[^)]*\)", "", previa["descripcion"]).strip()
            descripcion = f"{base} {descripcion}".strip() if "modelo" in descripcion else base
        descripcion = re.sub(r"(\s+-)+\s*$", "", descripcion).strip()
        if not descripcion:
            continue
        ref_anterior = ref
        filas.append({"ref": ref, "codigo": codigo[:30], "descripcion": descripcion[:120], "nivel": 0,
                      "cantidad": cantidad, "espanol": descripcion})
    return filas


FORMATOS = {"yamaha": leer_figuras, "auteco": leer_figuras_auteco, **FORMATOS_EXTRA}


def _imagen(documento, fig, formato):
    """Dibujo de la figura. Yamaha: la imagen de su página. Auteco: se RENDERIZA la zona del dibujo (a la izquierda de
    la tabla) tal como se ve impresa: extraer la imagen incrustada fallaba con algunas (salían dañadas, en mosaico) y
    con los dibujos armados de muchas imágenes pequeñas. Si la página de la figura no tiene dibujo, se usa la anterior,
    pero solo si esa página no es de otra figura."""
    if "imagen" in fig:  # formatos de garaje/despiece_lectores.py: el lector sabe dónde está el dibujo
        return fig["imagen"]()
    if formato == "yamaha":
        imagenes = documento[fig["pagina"]].get_images()
        return documento.extract_image(imagenes[0][0]) if imagenes else None
    import pymupdf
    paginas = fig.get("paginas") or [fig["pagina"]]
    propia = documento[paginas[0]]
    zoom = pymupdf.Matrix(2, 2)
    if not (propia.get_images() or propia.get_drawings()):
        anterior = paginas[0] - 1
        titulos = lambda n: {m.group(1) for m in RE_TITULO_PAGINA.finditer(documento[n].get_text())}
        if anterior >= 0 and titulos(anterior) <= titulos(paginas[0]) and documento[anterior].get_images():
            pix = documento[anterior].get_pixmap(matrix=zoom)
            return {"image": pix.tobytes("png"), "width": pix.width, "height": pix.height, "ext": "png"}
    recorte = pymupdf.Rect(0, 0, fig["x_tabla"] - 6, propia.rect.height)
    pix = propia.get_pixmap(matrix=zoom, clip=recorte)
    return {"image": pix.tobytes("png"), "width": pix.width, "height": pix.height, "ext": "png"}


# Primeras palabras que delatan un herraje o accesorio del sistema: "Capuchón Bujía" no es la bujía ni "BAND, BATTERY" la
# batería. Con ellas al principio, la regla solo enlaza si coincide desde el inicio de la descripción.
HERRAJES_INICIO = set("""TORNILLO TORNILLOS TUERCA ARANDELA ARAND BUJE EJE PLATINA ESPARRAGO RETEN RETENEDOR CAUCHO ANTIVIBRANTE EMPAQUE
CAPUCHON DUCTO SOPORTE PROTECTOR BASE ABRAZADERA CAJA LEVA PORTA PORTABANDAS PORTASPROCKET INDICADOR TORRE CORREA RESORTE
VENTILADOR CONECTOR MANGUERA BANDEJA PLACA PLATO PIN BOLT NUT SCREW WASHER BAND HOLDER PLATE TRAY RUBBER HOSE COVER CASE
BRACKET STAY SPACER COLLAR DAMPER SEAL GUIDE SPRING TUBE CLIP CLAMP RETAINER DRUM LEVER CAM INSULATOR TERMINAL""".split())


def _sin_tildes(texto):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


# Enlaces por defecto tarea → pieza, iguales para todas las motos: se usan después de las reglas del mapa (que mandan,
# también sus exclusiones null). Así cada tarea del plan tiene una pieza en su sistema y el visor abre en ella.
# Cuando la tarea no cambia una pieza (el líquido de frenos), la pieza representativa es donde se revisa y se rellena.
_RUEDA = ("rueda", "rueda_trasera", "rueda_tambor")
REGLAS_GLOBALES = [
    # (diagramas, piezas de la lámina o None, {patrón: tarea})
    (("bomba_freno", "freno_completo", "bombas_abs", "freno_trasero"), None,
     {"CAP, RESERVOIR": "liquido-frenos", "CAP, MASTER CYLINDER": "liquido-frenos", "RESERVOIR CAP": "liquido-frenos",
      "TAPA BOMBA": "liquido-frenos", "TAPA TANQUE": "liquido-frenos", "TAPA DEPOSITO": "liquido-frenos"}),
    (("electrico",), None, {"BATTERY": "bateria", "BATERIA": "bateria"}),
    (("culata", "encendido"), None, {"SPARK PLUG": "bujia", "PLUG, SPARK": "bujia", "PLUG,SPARK": "bujia", "BUJIA": "bujia"}),
    (_RUEDA, ("llanta_del",), {"TIRE": "llanta-del", "TYRE": "llanta-del", "LLANTA": "llanta-del", "NEUMATICO": "llanta-del"}),
    (_RUEDA, ("llanta_tras", "cadena"), {"TIRE": "llanta-tras", "TYRE": "llanta-tras", "LLANTA": "llanta-tras", "NEUMATICO": "llanta-tras"}),
    (("rueda_tambor", "freno_tambor"), ("llanta_tras", "freno_tras"), {"SHOE": "bandas-tras", "BANDA": "bandas-tras"}),
    (("suspension_delantera",), None, {"OIL SEAL": "suspension-del", "RETEN": "suspension-del", "RETENEDOR": "suspension-del"}),
    (("amortiguadores",), None, {"SHOCK ABSORBER": "suspension-tras", "CUSHION ASSY": "suspension-tras", "AMORTIGUADOR": "suspension-tras"}),
    (("admision",), None, {"ELEMENT": "filtro-aire", "FILTRO AIRE": "filtro-aire", "AIR FILTER": "filtro-aire",
                           "ELEMENTO FILTR": "filtro-aire", "ESPUMA FILTRO": "filtro-aire", "FILTRO DE AIRE": "filtro-aire"}),
    (("caja_secundaria",), None, {"DRAIN": "aceite-caja", "DRENAJE": "aceite-caja", "BOLT, STRAIGHT SCREW": "aceite-caja"}),
]


def completar_con_globales(despiece, tareas, conf):
    """Segunda pasada: las tareas que el mapa no logró enlazar en ninguna pieza de este despiece se enlazan con las
    reglas globales (respetando las exclusiones null del mapa). Devuelve cuántas piezas se enlazaron."""
    enlazadas = set(ParteDespiece.objects.filter(lamina__despiece=despiece, tarea__isnull=False)
                    .values_list("tarea__clave", flat=True))
    nuevas = 0
    for lamina in despiece.laminas.all():
        nulos = {k: None for laminas in conf["laminas"] for k, v in (laminas.get("reglas") or {}).items()
                 if v is None and laminas.get("diagrama") == lamina.diagrama}
        reglas = {}
        for diagramas, piezas, globales in REGLAS_GLOBALES:
            if lamina.diagrama in diagramas and (piezas is None or lamina.pieza in piezas):
                reglas.update({k: v for k, v in globales.items() if v not in enlazadas and v in tareas})
        if not reglas:
            continue
        partes = list(lamina.partes.all())
        cambio = []
        for parte in partes:
            if parte.tarea_id or any(_sin_tildes(k).upper() in _sin_tildes(parte.descripcion).upper() for k in nulos):
                continue
            clave = tarea_para(reglas, parte.descripcion)
            if clave:
                parte.tarea = tareas[clave]
                cambio.append(parte)
        if cambio:
            ParteDespiece.objects.bulk_update(cambio, ["tarea"])
            ParteDespiece.objects.bulk_update(tarea_al_sello(partes), ["tarea"])
            nuevas += len(cambio)
            enlazadas |= {p.tarea.clave for p in cambio}
    # Tercera opción: si el catálogo no vende la pieza que se cambia (la batería, el aceite de la caja), una pieza
    # representativa donde se hace el trabajo: el soporte de la batería, la bomba del freno, la carcasa de la caja.
    for clave, diagramas, patrones in REPRESENTATIVAS:
        if clave in enlazadas or clave not in tareas:
            continue
        candidatas = [p for p in ParteDespiece.objects.filter(lamina__despiece=despiece, tarea__isnull=True).select_related("lamina")
                      .order_by("lamina__orden", "ref") if diagramas is None or p.lamina.diagrama in diagramas]
        for patron in patrones:
            elegida = next((p for p in candidatas if re.search(patron, _sin_tildes(p.descripcion).upper())), None)
            if elegida:
                elegida.tarea = tareas[clave]
                elegida.save(update_fields=["tarea"])
                enlazadas.add(clave)
                nuevas += 1
                break
    return nuevas


_FRENOS = ("bomba_freno", "freno_completo", "bombas_abs", "freno_trasero", "freno_disco")
REPRESENTATIVAS = [
    ("liquido-frenos", _FRENOS, [r"BOMBA (DE )?FRENO|MASTER CYLINDER|CILINDRO MAESTRO"]),
    ("aceite-caja", ("caja_secundaria",), [r"^(CARCAZA|CARCASA|CASE COMP|CASE, TRANSMISSION|CASE COMP\., MISSION)"]),
]


def tarea_para(reglas, descripcion, espanol=""):
    """Clave de la tarea del plan para una fila del catálogo según las reglas del mapa ({patrón: clave}).

    Un patrón enlaza si coincide desde el inicio de la descripción (sin tildes ni puntos iniciales) o si la descripción no
    empieza por una palabra de herraje (ver HERRAJES_INICIO). Un valor null en las reglas es una exclusión explícita: la
    primera coincidencia con null deja la fila sin tarea."""
    textos = [re.sub(r"^[\s.]+", "", _sin_tildes(t).upper()) for t in (descripcion or "", espanol or "") if t]
    for patron, clave in (reglas or {}).items():
        p = _sin_tildes(patron).upper()
        for texto in textos:
            if p not in texto:
                continue
            primera = re.split(r"[\s,.(]+", texto, maxsplit=1)[0]
            if texto.startswith(p) or primera not in HERRAJES_INICIO:
                return clave
    return None


# Un tapón no se cambia en el mantenimiento: se cambia su empaque (o-ring o arandela). El catálogo suele listarlo justo
# antes o después del tapón; si no, el empaque dice de qué tapón es ("ARANDELA TAPÓN", "WASHER, DRAIN").
_TAPON = re.compile(r"^(PLUG(?!,?\s*SPARK)|TAP[OÓ]N(?! DE BUJ)|BOLT,?\s*(STRAIGHT SCREW|DRAIN)|DRAIN BOLT|TORNILLO,?\s+(DE\s+)?DRENAJE)", re.I)
# La tapa del filtro de aceite tampoco se cambia: se cambia su o-ring; si la lámina no lo trae, la tapa suelta la tarea
_TAPA_FILTRO = re.compile(r"^(TAPA|CUBIERTA|CAP|COVER)\b.*\b(FILTRO|FILTER)", re.I)
# La varilla (o tapón con varilla) del aceite tampoco: su o-ring si lo hay; si no, la suelta (el empaque de drenaje la tiene)
_VARILLA = re.compile(r"^(GAUGE,?\s*OIL LEVEL|OIL LEVEL GAUGE|PLUG,?\s*OIL LEVEL|VARILLA|TAP[OÓ]N DEL? NIVEL)", re.I)
_NOMBRA_VARILLA = re.compile(r"\b(GAUGE|LEVEL|VARILLA|MEDIDOR|TAP[OÓ]N)\b", re.I)
# El filtro sí se cambia, y con él el o-ring o empaque que lo acompaña
_FILTRO = re.compile(r"^(FILTER|FILTRO|ELEMENT|CEDAZO)", re.I)
_SELLO = re.compile(r"^(O-?\s?RING|ORING|GASKET|WASHER|EMPAQUE|EMPAQ|ARANDELA|ARAND|JUNTA|PACKING|ANILLO\s+RETEN|ANILLO\s+(EN\s+)?O\b)", re.I)
_SELLO_FILTRO = re.compile(r"^(O-?\s?RING|ORING|GASKET|EMPAQUE|EMPAQ|ANILLO\s+(EN\s+)?O\b)", re.I)
_NOMBRA_TAPON = re.compile(r"\b(TAP[OÓ]N|PLUG|DRAIN|DRENAJE)\b", re.I)
_CONJUNTO_TAPON = re.compile(r"^(STRAINER|SCREEN|SPRING|CEDAZO|MALLA|REJILLA|RESORTE|FILTER|FILTRO|COLADOR)", re.I)
_NOMBRA_TAPA = re.compile(r"\b(TAPA|CUBIERTA|CAP|COVER)\b", re.I)


def _sello_de(p, partes, por_ref, nombra):
    """El empaque de una pieza: primero el que la nombra ("WASHER, DRAIN PLUG", "ARAND TAPÓN DRENAJE"), el más cercano;
    si no, el número anterior o el siguiente; si no, el o-ring que sigue al conjunto tapón-colador-resorte."""
    nombran = sorted((q for q in partes if q is not p and not q.tarea_id and _SELLO.match(q.descripcion.strip(" ."))
                      and nombra.search(q.descripcion)), key=lambda q: abs(q.ref - p.ref))
    if nombran:
        return nombran[0]
    for ref in (p.ref + 1, p.ref - 1):
        q = por_ref.get(ref)
        if q and not q.tarea_id and _SELLO.match(q.descripcion.strip(" .")):
            return q
    # Tapón con colador (scooter): tapón, colador y resorte, y después su o-ring
    ref = p.ref + 1
    while por_ref.get(ref) and _CONJUNTO_TAPON.match(por_ref[ref].descripcion.strip(" .")):
        ref += 1
    q = por_ref.get(ref)
    if ref > p.ref + 1 and q and not q.tarea_id and _SELLO.match(q.descripcion.strip(" .")):
        return q
    return None


def tarea_al_sello(partes):
    """partes: las de una lámina. Devuelve las que cambiaron: el empaque de un tapón o de la tapa del filtro toma su
    tarea (y el tapón o la tapa la suelta); el o-ring de un filtro la comparte con el filtro."""
    por_ref = {p.ref: p for p in partes}
    cambios = []
    for p in sorted(partes, key=lambda q: q.ref):
        if not p.tarea_id:
            continue
        texto = p.descripcion.strip(" .")
        if _TAPA_FILTRO.match(texto) or _VARILLA.match(texto):
            sello = _sello_de(p, partes, por_ref, _NOMBRA_TAPA if _TAPA_FILTRO.match(texto) else _NOMBRA_VARILLA)
            if sello:
                sello.tarea_id = p.tarea_id
                cambios.append(sello)
            p.tarea_id = None
            cambios.append(p)
        elif _TAPON.match(texto):
            sello = _sello_de(p, partes, por_ref, _NOMBRA_TAPON)
            if sello:
                sello.tarea_id, p.tarea_id = p.tarea_id, None
                cambios += [sello, p]
        elif _FILTRO.match(texto):
            sello = por_ref.get(p.ref + 1)
            if sello and not sello.tarea_id and _SELLO_FILTRO.match(sello.descripcion.strip(" .")):
                sello.tarea_id = p.tarea_id
                cambios.append(sello)
    return list({id(q): q for q in cambios}.values())


def _nombre_es(fila):
    nombre = traducir(fila["descripcion"])
    if nombre:
        return nombre
    espanol = fila.get("espanol", "")
    if espanol:
        return espanol[:1].upper() + espanol[1:].lower()
    return traducir_palabras(fila["descripcion"])


class Command(BaseCommand):
    help = "Importa láminas de un catálogo de despiece en PDF según un mapa JSON"

    def add_arguments(self, parser):
        parser.add_argument("pdf")
        parser.add_argument("mapa")
        parser.add_argument("--reemplazar", action="store_true",
                            help="Borra y vuelve a crear las láminas (se pierden las marcas hechas)")
        parser.add_argument("--reenlazar", action="store_true",
                            help="En las láminas que ya existen: actualiza título, pieza y diagrama, y recalcula en cada parte la "
                                 "tarea, el nombre en español y la ayuda, sin tocar las marcas (x, y)")

    def handle(self, pdf, mapa, reemplazar, reenlazar=False, **opts):
        try:
            import pymupdf
        except ImportError:
            raise CommandError("Falta PyMuPDF. Instala las herramientas de desarrollo: pip install -r requirements-dev.txt")

        with open(mapa, encoding="utf-8") as f:
            conf = json.load(f)
        formato = conf.get("formato", "yamaha")
        if formato not in FORMATOS:
            raise CommandError(f"Formato de catálogo desconocido: {formato}")
        linea = LineaMoto.objects.filter(marca__nombre=conf["marca"], nombre=conf["linea"]).first()
        if not linea:
            raise CommandError(f"No existe la línea {conf['marca']} {conf['linea']} en el catálogo.")
        tareas = {t.clave: t for t in TareaMantenimiento.objects.all()}

        documento = pdf if formato == "fichas" else pymupdf.open(pdf)  # fichas: carpeta con fichas.json
        figuras = FORMATOS[formato](documento)

        with transaction.atomic():
            despiece, _ = Despiece.objects.update_or_create(
                linea=linea, version=conf["version"], defaults={"anio": conf["anio"], "fuente": conf.get("fuente", ""), "variante": conf.get("variante", ""),
                          "especificaciones": conf.get("especificaciones", {})},
            )
            for orden, item in enumerate(conf["laminas"]):
                clave_fig = str(item["figura"]).upper()
                fig = figuras.get(clave_fig)
                if not fig:
                    self.stderr.write(f"FIG. {clave_fig} no está en el PDF; se omite.")
                    continue
                numero = fig.get("numero") or int(re.match(r"\d+", clave_fig).group())
                existente = despiece.laminas.filter(figura=numero).first()
                if existente and reenlazar and not reemplazar:
                    self._reenlazar(existente, item, fig, tareas, clave_fig)
                    continue
                if existente and not reemplazar:
                    if existente.diagrama != item.get("diagrama", ""):
                        existente.diagrama = item.get("diagrama", "")
                        existente.save(update_fields=["diagrama"])
                    self.stdout.write(f"FIG. {clave_fig} ya existe (diagrama: {existente.diagrama or '—'}).")
                    continue
                if existente:
                    existente.imagen.delete(save=False)
                    existente.delete()

                img = _imagen(documento, fig, formato)
                if not img:
                    self.stderr.write(f"FIG. {clave_fig} no tiene dibujo en el PDF; se omite.")
                    continue
                lamina = Lamina(despiece=despiece, figura=numero, titulo=fig["titulo"][:120],
                                titulo_es=item.get("titulo_es", ""), pieza=item["pieza"], orden=orden,
                                diagrama=item.get("diagrama", ""),
                                ancho=img["width"], alto=img["height"])
                nombre = f"{conf['marca']}-{conf['linea']}-{conf['version']}-fig{clave_fig.zfill(2)}.{img['ext']}"
                lamina.imagen.save(re.sub(r"[^A-Za-z0-9._-]", "_", nombre), ContentFile(img["image"]), save=False)
                lamina.save()

                enlazadas = 0
                for fila in fig["filas"]:
                    if fila.get("codigo") in item.get("descripciones", {}):
                        fila["descripcion"] = item["descripciones"][fila["codigo"]]
                    texto = f"{fila['descripcion']} {fila.get('espanol', '')}".upper()
                    clave = tarea_para(item.get("reglas", {}), fila["descripcion"], fila.get("espanol", ""))
                    tarea = tareas.get(clave) if clave else None
                    enlazadas += bool(tarea)
                    datos = {k: v for k, v in fila.items() if k != "espanol"}
                    ParteDespiece.objects.create(lamina=lamina, nombre_es=_nombre_es(fila),
                                                 ayuda=ayuda_para(fila["descripcion"]), tarea=tarea, **datos)
                ParteDespiece.objects.bulk_update(tarea_al_sello(list(lamina.partes.all())), ["tarea"])
                self.stdout.write(self.style.SUCCESS(
                    f"FIG. {clave_fig:>3} {lamina.nombre}: {len(fig['filas'])} partes, {enlazadas} enlazadas al plan"))
            nuevas = completar_con_globales(despiece, tareas, conf)
            if nuevas:
                self.stdout.write(f"Enlaces por defecto (tareas sin pieza en el mapa): {nuevas}")
        self.stdout.write(f"Listo: {despiece}. Marca las piezas en el admin > Láminas de despiece.")

    def _reenlazar(self, lamina, item, fig, tareas, clave_fig):
        """Refresca una lámina existente sin perder sus marcas: título, pieza, diagrama y, en cada parte, tarea, nombre y ayuda."""
        lamina.titulo_es = item.get("titulo_es", lamina.titulo_es)
        lamina.pieza = item.get("pieza", lamina.pieza)
        lamina.diagrama = item.get("diagrama", lamina.diagrama)
        lamina.save(update_fields=["titulo_es", "pieza", "diagrama"])
        filas = {(str(f.get("ref")), f.get("codigo")): f for f in fig["filas"]}
        cambios, enlazadas = [], 0
        for parte in lamina.partes.all():
            fila = filas.get((str(parte.ref), parte.codigo)) or {"descripcion": parte.descripcion}
            if parte.codigo in item.get("descripciones", {}):
                parte.descripcion = item["descripciones"][parte.codigo]
            clave = tarea_para(item.get("reglas", {}), parte.descripcion, fila.get("espanol", ""))
            parte.tarea = tareas.get(clave) if clave else None
            parte.nombre_es = (nombre_por_sistema(lamina.diagrama, parte.descripcion)
                               or _nombre_es({**fila, "descripcion": parte.descripcion}))
            parte.ayuda = ayuda_para(parte.descripcion)
            enlazadas += bool(parte.tarea)
            cambios.append(parte)
        ParteDespiece.objects.bulk_update(cambios, ["tarea", "nombre_es", "ayuda", "descripcion"])
        ParteDespiece.objects.bulk_update(tarea_al_sello(cambios), ["tarea"])
        self.stdout.write(f"FIG. {clave_fig:>3} {lamina.nombre}: reenlazada ({len(cambios)} partes, {enlazadas} enlazadas al plan)")
