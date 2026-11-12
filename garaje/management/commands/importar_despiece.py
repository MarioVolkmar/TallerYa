"""Importa láminas de un catálogo de partes en PDF (formato de catálogos Yamaha).

Uso (solo en local; requiere `pip install -r requirements-dev.txt`):
    python manage.py importar_despiece despiece_local/N-MAX-BBE4-2024.pdf garaje/despiece_mapas/yamaha_nmax_bbe4.json

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

# Columnas de la tabla (en puntos de la página A4 horizontal del catálogo).
COL_REF = (405, 429)
COL_CODIGO = (429, 500)
COL_DESC = (500, 655)
COL_CANT = (655, 690)


def leer_figuras(pdf):
    """Devuelve {figura: {"titulo", "pagina_imagen", "filas": [...]}} recorriendo todo el PDF."""
    figuras = {}
    for pagina in pdf:
        palabras = pagina.get_text("words")
        texto = " ".join(w[4] for w in palabras[:12])
        m = re.match(r"FIG\.\s+(\d+)\s+(.+?)\s+REF\.", texto)
        if not m:
            continue
        numero = int(m.group(1))
        fig = figuras.setdefault(numero, {"titulo": m.group(2).strip(), "pagina": pagina.number, "filas": []})
        fig["filas"].extend(_filas(palabras))
    return figuras


def _filas(palabras):
    refs = [w for w in palabras if COL_REF[0] <= w[0] < COL_REF[1] and w[4].isdigit() and w[1] > 62]
    filas = []
    for ref in refs:
        yc = (ref[1] + ref[3]) / 2
        en_fila = [w for w in palabras if abs((w[1] + w[3]) / 2 - yc) < 4]
        tomar = lambda col: " ".join(w[4] for w in sorted(en_fila, key=lambda w: w[0]) if col[0] <= w[0] < col[1])
        codigo = tomar(COL_CODIGO).replace("�", "-").replace("–", "-")
        descripcion = tomar(COL_DESC)
        cantidad = tomar(COL_CANT)
        if not codigo:
            continue
        nivel = len(descripcion) - len(descripcion.lstrip("."))
        filas.append({
            "ref": int(ref[4]), "codigo": codigo, "descripcion": descripcion.lstrip(". ").strip(),
            "nivel": nivel, "cantidad": int(cantidad) if cantidad.isdigit() else 1,
        })
    return filas


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
        linea = LineaMoto.objects.filter(marca__nombre=conf["marca"], nombre=conf["linea"]).first()
        if not linea:
            raise CommandError(f"No existe la línea {conf['marca']} {conf['linea']} en el catálogo.")
        tareas = {t.clave: t for t in TareaMantenimiento.objects.all()}

        documento = pymupdf.open(pdf)
        figuras = leer_figuras(documento)

        with transaction.atomic():
            despiece, _ = Despiece.objects.update_or_create(
                linea=linea, version=conf["version"], defaults={"anio": conf["anio"], "fuente": conf.get("fuente", "")},
            )
            for orden, item in enumerate(conf["laminas"]):
                fig = figuras.get(item["figura"])
                if not fig:
                    self.stderr.write(f"FIG. {item['figura']} no está en el PDF; se omite.")
                    continue
                existente = despiece.laminas.filter(figura=item["figura"]).first()
                if existente and not reemplazar:
                    self.stdout.write(f"FIG. {item['figura']} ya existe (usa --reemplazar para rehacerla).")
                    continue
                if existente:
                    existente.imagen.delete(save=False)
                    existente.delete()

                pagina = documento[fig["pagina"]]
                xref = pagina.get_images()[0][0]
                img = documento.extract_image(xref)
                lamina = Lamina(despiece=despiece, figura=item["figura"], titulo=fig["titulo"],
                                titulo_es=item.get("titulo_es", ""), pieza=item["pieza"], orden=orden,
                                ancho=img["width"], alto=img["height"])
                nombre = f"{conf['marca']}-{conf['linea']}-{conf['version']}-fig{item['figura']:02d}.{img['ext']}"
                lamina.imagen.save(re.sub(r"[^A-Za-z0-9._-]", "_", nombre), ContentFile(img["image"]), save=False)
                lamina.save()

                enlazadas = 0
                for fila in fig["filas"]:
                    clave = next((c for patron, c in item.get("reglas", {}).items() if patron in fila["descripcion"].upper()), None)
                    tarea = tareas.get(clave) if clave else None
                    enlazadas += bool(tarea)
                    ParteDespiece.objects.create(lamina=lamina, nombre_es=traducir(fila["descripcion"]),
                                                 ayuda=ayuda_para(fila["descripcion"]), tarea=tarea, **fila)
                self.stdout.write(self.style.SUCCESS(
                    f"FIG. {item['figura']:>2} {lamina.nombre}: {len(fig['filas'])} partes, {enlazadas} enlazadas al plan"))
        self.stdout.write(f"Listo: {despiece}. Marca las piezas en el admin → Láminas de despiece.")
