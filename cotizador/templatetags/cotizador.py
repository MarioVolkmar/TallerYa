"""Ganchos del piloto en las plantillas de garaje. Con COTIZADOR_ACTIVO apagado no pintan nada."""
from django import template
from consola.ajustes import ajuste
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def cotizador_script():
    if not ajuste("cotizador_activo"):
        return ""
    return format_html(
        '<link rel="stylesheet" href="{}"><script src="{}" defer data-url-parte="{}" data-url-codigo="{}"></script>',
        static("cotizador/css/cotizador.css") + "?v=1", static("cotizador/js/cotizar.js") + "?v=1",
        reverse("cotizador:parte", args=[0]), reverse("cotizador:codigo"),
    )


@register.simple_tag
def cotizador_boton(codigo):
    if not ajuste("cotizador_activo") or not codigo:
        return ""
    return format_html('<button type="button" class="accion-copiar cotizador-boton" data-cotizar-codigo="{}">'
                       'Cotizar</button>', codigo)


@register.filter
def pesos(valor):
    """1234567 → $1.234.567"""
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return ""


@register.filter
def enlace_seguro(url):
    return url if isinstance(url, str) and url.startswith("https://") else ""
