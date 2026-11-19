"""SEO: páginas por barrio y servicio, sitemap.xml, robots.txt y reglas de indexación."""
import re
from xml.sax.saxutils import escape

from django.http import Http404, HttpResponse
from django.urls import reverse
from django.utils.text import slugify

from .models import Barrio, Servicio, Taller

# Rutas públicas que sí se indexan. Todo lo demás (cuenta, garaje, mi-taller, admin, tareas…) lleva noindex.
_PUBLICAS = re.compile(
    r"^/($|talleres/|taller/[^/]+/$|foro/$|foro/\d+/|foro/rodadas/$|foro/rodadas/\d+/$|cupones/$|cupones/\d+/$"
    r"|emergencias/$|despiece/|noticias/|registra-tu-taller/$|legal/|diagnostico/$|soat/$|tecnomecanica/$"
    r"|mecanicos/$|mecanicos/(?!registro/|mi-perfil/)[^/]+/$)"
)


def es_indexable(path):
    return bool(_PUBLICAS.match(path)) and not path.startswith("/foro/preguntar")


def slug_barrio(b):
    return slugify(b.nombre if b.ciudad == "Medellín" else f"{b.nombre} {b.ciudad}")


def slug_servicio(s):
    return slugify(s.nombre)


def barrios_con_talleres():
    return Barrio.objects.filter(talleres__activo=True).distinct()


def servicios_con_talleres():
    return Servicio.objects.filter(talleres__activo=True).distinct()


def barrio_por_slug(slug):
    for b in barrios_con_talleres():
        if slug_barrio(b) == slug:
            return b
    raise Http404


def servicio_por_slug(slug):
    for s in servicios_con_talleres():
        if slug_servicio(s) == slug:
            return s
    raise Http404


def _lugar(b):
    return b.nombre if b.ciudad == "Medellín" else f"{b.nombre} ({b.ciudad})"


def _plural(n):
    return f"{n} taller{'es' if n != 1 else ''}"


def textos_barrio(b, n):
    lugar = _lugar(b)
    return {
        "titulo": f"Talleres de motos en {lugar} · TallerYa",
        "h1": f"Talleres de motos en {lugar}",
        "descripcion": f"{_plural(n)} de motos en {lugar}: compara reseñas, servicios y precios, "
                       "y pide tu cita por WhatsApp en TallerYa.",
        "intro": f"Encuentra talleres de motos en {lugar}, {b.ciudad}. Mira las reseñas de otros moteros, los servicios "
                 "y rangos de precio que publica cada taller y agenda tu cita sin llamar.",
    }


def textos_servicio(s, n, b=None):
    nom = s.nombre
    if b:
        lugar = _lugar(b)
        return {
            "titulo": f"{nom} en {lugar} · Talleres de motos · TallerYa",
            "h1": f"{nom} en {lugar}",
            "descripcion": f"{nom} para tu moto en {lugar}: {_plural(n)} con reseñas, "
                           "precios de referencia y cita por WhatsApp.",
            "intro": f"Talleres de motos en {lugar} que ofrecen {nom.lower()}. Compara reseñas y precios y pide tu cita.",
        }
    return {
        "titulo": f"{nom} para motos en Medellín · TallerYa",
        "h1": f"{nom} para tu moto en Medellín",
        "descripcion": f"{nom} para motos en Medellín y el Valle de Aburrá: {_plural(n)} con reseñas, "
                       "precios de referencia y cita por WhatsApp.",
        "intro": f"Talleres de Medellín y el Valle de Aburrá que ofrecen {nom.lower()}. Compara reseñas y "
                 "precios publicados por cada taller y agenda tu cita.",
    }


def robots_txt(request):
    base = request.build_absolute_uri("/").rstrip("/")
    privadas = ("/admin/", "/cuenta/", "/garaje/", "/mi-taller/", "/tareas/", "/hoja-de-vida/", "/notificaciones/",
                "/cupon/", "/canjear/", "/r/", "/cita/", "/soat/pedido/", "/insignias/", "/plus/", "/media/",
                "/foro/preguntar/", "/foro/rodadas/nueva/", "/foro/usuarios/")
    lineas = ["User-agent: *"] + [f"Disallow: {p}" for p in privadas] + ["", f"Sitemap: {base}/sitemap.xml", ""]
    return HttpResponse("\n".join(lineas), content_type="text/plain; charset=utf-8")


def _url(base, ruta, fecha=None):
    lm = f"<lastmod>{fecha:%Y-%m-%d}</lastmod>" if fecha else ""
    return f"<url><loc>{escape(base + ruta)}</loc>{lm}</url>"


def sitemap_xml(request):
    from foro.models import Pregunta, Rodada
    base = request.build_absolute_uri("/").rstrip("/")
    u = [_url(base, reverse(n)) for n in (
        "talleres:inicio", "talleres:directorio", "talleres:emergencias", "foro:lista", "foro:rodadas", "cupones:lista")]
    from domicilio.models import MecanicoDomicilio
    u.append(_url(base, reverse("domicilio:listado")))
    u += [_url(base, m.get_absolute_url()) for m in MecanicoDomicilio.objects.publicados().only("slug")]
    talleres = list(Taller.objects.filter(activo=True).select_related("barrio").prefetch_related("servicios"))
    barrios, servicios, combos = set(), set(), set()
    for t in talleres:
        u.append(_url(base, t.get_absolute_url()))
        barrios.add(slug_barrio(t.barrio))
        for s in t.servicios.all():
            servicios.add(slug_servicio(s))
            combos.add((slug_servicio(s), slug_barrio(t.barrio)))
    u += [_url(base, reverse("talleres:barrio", args=[x])) for x in sorted(barrios)]
    u += [_url(base, reverse("talleres:servicio", args=[x])) for x in sorted(servicios)]
    u += [_url(base, reverse("talleres:servicio_barrio", args=[a, b])) for a, b in sorted(combos)]
    for p in Pregunta.objects.filter(visible=True).only("id", "titulo", "ultima_actividad"):
        u.append(_url(base, p.get_absolute_url(), p.ultima_actividad))
    for r in Rodada.objects.filter(pregunta__visible=True).select_related("pregunta"):
        u.append(_url(base, r.get_absolute_url()))
    from garaje import despiece_publico as dp  # despiece público: índice, cada moto y cada sistema
    u.append(_url(base, reverse("garaje:despiece_indice")))
    for d in dp.despieces():
        laminas = dp.laminas_de(d)
        if laminas:
            u.append(_url(base, d.url_publica))
            u += [_url(base, reverse("garaje:despiece_sistema", args=[d.slug, l["slug"]])) for l in laminas]
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + "".join(u) + "</urlset>")
    return HttpResponse(xml, content_type="application/xml")
