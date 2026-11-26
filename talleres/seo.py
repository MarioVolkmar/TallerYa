"""SEO: páginas por barrio y servicio, sitemap.xml, robots.txt y reglas de indexación."""
import re

from django.http import Http404, HttpResponse
from django.urls import reverse
from django.utils.text import slugify

from .models import Barrio, Servicio, Taller

# Rutas públicas que sí se indexan. Todo lo demás (cuenta, garaje, mi-taller, admin, tareas…) lleva noindex.
_PUBLICAS = re.compile(
    r"^/($|talleres/|taller/[^/]+/$|foro/$|foro/\d+/|foro/rodadas/$|foro/rodadas/\d+/$|cupones/$|cupones/\d+/$"
    r"|emergencias/$|despiece/|motos/|noticias/|registra-tu-taller/$|legal/|diagnostico/$|soat/$|tecnomecanica/$"
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


def sitemap_xml(request):
    """El mapa se arma con django.contrib.sitemaps; las secciones están en config/sitemaps.py."""
    from django.contrib.sitemaps.views import sitemap

    from config.sitemaps import secciones
    return sitemap(request, sitemaps=secciones())
