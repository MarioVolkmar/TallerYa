import json

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from talleres.seo import es_indexable

register = template.Library()

TITULO = "TallerYa · Talleres de motos en Medellín"
DESCRIPCION = ("Encuentra talleres de motos de confianza en Medellín y el Valle de Aburrá: reseñas reales, precios, "
               "cupones y cita por WhatsApp. Además, garaje, foro y rodadas para moteros.")


@register.inclusion_tag("talleres/_seo.html", takes_context=True)
def seo(context, titulo="", descripcion="", imagen="", tipo="website"):
    request = context["request"]
    absoluta = request.build_absolute_uri
    return {
        "titulo": titulo or TITULO,
        "descripcion": (descripcion or DESCRIPCION)[:300],
        "imagen": absoluta(imagen or static("talleres/img/og.png")),
        "canonical": absoluta(request.path),
        "tipo": tipo,
        # Con parámetros (?pagina, ?q, filtros) no se indexa; la canonical apunta a la página limpia.
        "noindex": not es_indexable(request.path) or bool(request.GET),
    }


_DIAS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@register.simple_tag(takes_context=True)
def json_ld_taller(context, taller):
    request = context["request"]
    d = {
        "@context": "https://schema.org", "@type": "AutoRepair", "name": taller.nombre,
        "url": request.build_absolute_uri(taller.get_absolute_url()),
        "telephone": "+" + taller.whatsapp.lstrip("+"),
        "address": {"@type": "PostalAddress", "streetAddress": taller.direccion,
                    "addressLocality": taller.barrio.ciudad, "addressRegion": "Antioquia", "addressCountry": "CO"},
    }
    if taller.descripcion:
        d["description"] = taller.descripcion[:300]
    if taller.foto:
        d["image"] = request.build_absolute_uri(taller.foto.url)
    if taller.latitud is not None and taller.longitud is not None:
        d["geo"] = {"@type": "GeoCoordinates", "latitude": float(taller.latitud), "longitude": float(taller.longitud)}
    h = [{"@type": "OpeningHoursSpecification", "dayOfWeek": _DIAS[x.dia], "opens": f"{x.abre:%H:%M}",
          "closes": f"{x.cierra:%H:%M}"} for x in taller.horarios.all()]
    if h:
        d["openingHoursSpecification"] = h
    n = len(context.get("resenas") or [])
    if n and getattr(taller, "calificacion", None):
        d["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": round(taller.calificacion, 1),
                                "reviewCount": n, "bestRating": 5, "worstRating": 1}
    txt = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(txt))
