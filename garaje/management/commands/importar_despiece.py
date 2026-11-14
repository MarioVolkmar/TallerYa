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

RE_TITULO_PAGINA = re.compile(r"FIGURA\s*N\S{0,2}\s*(\d+[A-Z]?)", re.I)   # números de figura que aparecen en una página
RE_FIGURA = re.compile(r"FIGURA\s*N\S{0,2}\s*(\d+[A-Z]?)\s*:\s*(.+?)(?:\s*\(\d\s*/\s*\d\s*\))?\s*$", re.I)


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
        descripcion, cantidad = [], 1
        for w in resto[1:]:
            if w[0] >= x_cant and w[4].isdigit():
                cantidad = int(w[4])
                break
            descripcion.append(w[4])
        descripcion = " ".join(descripcion).strip()
        if not descripcion or not re.search(r"\d", codigo):
            continue
        ref_anterior = ref
        filas.append({"ref": ref, "codigo": codigo[:30], "descripcion": descripcion[:120], "nivel": 0,
                      "cantidad": cantidad, "espanol": descripcion})
    return filas


FORMATOS = {"yamaha": leer_figuras, "auteco": leer_figuras_auteco}


def _imagen(documento, fig, formato):
    """Dibujo de la figura: en Yamaha la primera imagen de su página; en Auteco la más grande de sus
    páginas (o de la anterior, cuando el dibujo va en una página aparte antes de la tabla)."""
    if formato == "yamaha":
        imagenes = documento[fig["pagina"]].get_images()
        return documento.extract_image(imagenes[0][0]) if imagenes else None
    paginas = fig.get("paginas") or [fig["pagina"]]
    grandes = [i for n in paginas for i in documento[n].get_images() if i[2] * i[3] > 100_000]
    if grandes:
        return documento.extract_image(max(grandes, key=lambda i: i[2] * i[3])[0])
    # Dibujo armado con muchas imágenes pequeñas o en vector en su propia página: se renderiza esa página (abajo).
    propia = documento[paginas[0]]
    if not (propia.get_images() or propia.get_drawings()):
        # Sin nada en su página: el dibujo puede ir en la anterior, pero solo si esa página no es de otra figura
        # (antes se tomaba sin mirar y la fig. 22 de la NS 200 quedaba con el dibujo de la 21).
        anterior = paginas[0] - 1
        titulos = lambda n: {m.group(1) for m in RE_TITULO_PAGINA.finditer(documento[n].get_text())}
        if anterior >= 0 and titulos(anterior) <= titulos(paginas[0]):
            imagenes = [i for i in documento[anterior].get_images() if i[2] * i[3] > 100_000]
            if imagenes:
                return documento.extract_image(max(imagenes, key=lambda i: i[2] * i[3])[0])
    # Dibujo vectorial (sin imagen): se renderiza la parte izquierda de la página, a la izquierda de la tabla.
    import pymupdf
    pagina = documento[paginas[0]]
    recorte = pymupdf.Rect(0, 0, fig["x_tabla"] - 6, pagina.rect.height)
    pix = pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=recorte)
    return {"image": pix.tobytes("png"), "width": pix.width, "height": pix.height, "ext": "png"}


def _nombre_es(fila):
    nombre = traducir(fila["descripcion"])
    if nombre:
        return nombre
    espanol = fila.get("espanol", "")
    return espanol[:1].upper() + espanol[1:].lower() if espanol else ""


class Command(BaseCommand):
    help = "Importa láminas de un catálogo de despiece en PDF según un mapa JSON"

    def add_arguments(self, parser):
        parser.add_argument("pdf")
        parser.add_argument("mapa")
        parser.add_argument("--reemplazar", action="store_true",
                            help="Borra y vuelve a crear las láminas (se pierden las marcas hechas)")

    def handle(self, pdf, mapa, reemplazar, **opts):
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

        documento = pymupdf.open(pdf)
        figuras = FORMATOS[formato](documento)

        with transaction.atomic():
            despiece, _ = Despiece.objects.update_or_create(
                linea=linea, version=conf["version"], defaults={"anio": conf["anio"], "fuente": conf.get("fuente", "")},
            )
            for orden, item in enumerate(conf["laminas"]):
                clave_fig = str(item["figura"]).upper()
                numero = int(re.match(r"\d+", clave_fig).group())
                fig = figuras.get(clave_fig)
                if not fig:
                    self.stderr.write(f"FIG. {clave_fig} no está en el PDF; se omite.")
                    continue
                existente = despiece.laminas.filter(figura=numero).first()
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
                    texto = f"{fila['descripcion']} {fila.get('espanol', '')}".upper()
                    clave = next((c for patron, c in item.get("reglas", {}).items() if patron.upper() in texto), None)
                    tarea = tareas.get(clave) if clave else None
                    enlazadas += bool(tarea)
                    datos = {k: v for k, v in fila.items() if k != "espanol"}
                    ParteDespiece.objects.create(lamina=lamina, nombre_es=_nombre_es(fila),
                                                 ayuda=ayuda_para(fila["descripcion"]), tarea=tarea, **datos)
                self.stdout.write(self.style.SUCCESS(
                    f"FIG. {clave_fig:>3} {lamina.nombre}: {len(fig['filas'])} partes, {enlazadas} enlazadas al plan"))
        self.stdout.write(f"Listo: {despiece}. Marca las piezas en el admin > Láminas de despiece.")
