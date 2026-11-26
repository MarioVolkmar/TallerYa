"""Secciones de /sitemap.xml (django.contrib.sitemaps). Solo páginas públicas e indexables: nada de cuentas,
garajes, placas ni hojas de vida."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils.dateparse import parse_date

from consola.ajustes import ajuste


class Rutas(Sitemap):
    """Sección dada como lista de (ruta, fecha de última modificación o None)."""

    def __init__(self, armar):
        self.armar = armar

    def items(self):
        return self.armar()

    def location(self, item):
        return item[0]

    def lastmod(self, item):
        return item[1]


def _fijas():
    from domicilio.models import MecanicoDomicilio
    nombres = ["talleres:inicio", "talleres:directorio", "talleres:emergencias", "cupones:lista"]
    if ajuste("foro_activo"):
        nombres += ["foro:lista", "foro:rodadas"]
    rutas = [reverse(n) for n in nombres]
    if ajuste("mecanicos_activo"):
        rutas.append(reverse("domicilio:listado"))
        rutas += [m.get_absolute_url() for m in MecanicoDomicilio.objects.publicados().only("slug")]
    return [(r, None) for r in rutas]


def _talleres():
    from talleres.models import Taller
    from talleres.seo import slug_barrio, slug_servicio
    rutas, barrios, servicios, combos = [], set(), set(), set()
    for t in Taller.objects.filter(activo=True).select_related("barrio").prefetch_related("servicios"):
        rutas.append(t.get_absolute_url())
        barrios.add(slug_barrio(t.barrio))
        for s in t.servicios.all():
            servicios.add(slug_servicio(s))
            combos.add((slug_servicio(s), slug_barrio(t.barrio)))
    rutas += [reverse("talleres:barrio", args=[x]) for x in sorted(barrios)]
    rutas += [reverse("talleres:servicio", args=[x]) for x in sorted(servicios)]
    rutas += [reverse("talleres:servicio_barrio", args=[a, b]) for a, b in sorted(combos)]
    return [(r, None) for r in rutas]


def _foro():
    from foro.models import Pregunta, Rodada
    if not ajuste("foro_activo"):
        return []
    salida = [(p.get_absolute_url(), p.ultima_actividad)
              for p in Pregunta.objects.filter(visible=True).only("id", "titulo", "ultima_actividad")]
    return salida + [(r.get_absolute_url(), None)
                     for r in Rodada.objects.filter(pregunta__visible=True).select_related("pregunta")]


def _motos():
    from garaje import fallas, motos_publico as mp
    from garaje.models import TareaMantenimiento
    tareas = list(TareaMantenimiento.objects.filter(activo=True).order_by("orden", "pk"))
    salida = [(reverse("garaje:motos_publicas"), None)]
    for linea in mp.lineas():
        datos = fallas.de_linea(linea) if ajuste("fallas_activo") else None
        revisado = parse_date(datos.get("revisado", "")) if datos else None
        salida.append((linea.url_publica, revisado))
        salida += [(f["url"], revisado) for f in mp.fallas_de(linea)]
        salida += [(t["url"], None) for t in mp.tareas_de(linea, tareas)]
    return salida


def _despiece():
    from garaje import despiece_publico as dp
    salida = [(reverse("garaje:despiece_indice"), None)]
    lista = dp.despieces()
    indices = dp.indices(lista)
    for d in lista:
        salida.append((d.url_publica, None))
        # Sin índice (falta correr precalentar_despiece): solo la moto; aquí nunca se arma un despiece
        indice = indices.get(d.pk, {"laminas": [], "piezas": []})
        salida += [(reverse("garaje:despiece_sistema", args=[d.slug, s]), None) for s in indice["laminas"]]
        salida += [(reverse("garaje:despiece_pieza", args=[d.slug, s]), None) for s in indice["piezas"]]
    return salida


def secciones():
    return {nombre: Rutas(armar) for nombre, armar in (
        ("principales", _fijas), ("talleres", _talleres), ("foro", _foro), ("motos", _motos),
        ("despiece", _despiece))}
