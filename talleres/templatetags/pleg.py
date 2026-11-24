"""Sección plegable numerada: {% pleg "clave" numero="01" titulo="Mis citas" dato="3 citas" %}…{% endpleg %}.

Genera <details class="seccion-pleg" data-pleg> con el resumen de parciales/seccion_resumen.html;
el JS (talleres/js/secciones-pleg.js, cargado en base.html) recuerda lo abierto y abre por anclaje.
Opciones: id, clase (de la tarjeta, p. ej. "papel p-6"), tam (tamaño del título),
cerrada_movil (cerrada la primera vez en el celular), cerrada (cerrada por defecto en todos lados).
"""
from django import template
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


class PlegNode(template.Node):
    def __init__(self, clave, opciones, cuerpo):
        self.clave, self.opciones, self.cuerpo = clave, opciones, cuerpo

    def render(self, contexto):
        clave = self.clave.resolve(contexto)
        o = {k: v.resolve(contexto) for k, v in self.opciones.items()}
        resumen = render_to_string("parciales/seccion_resumen.html", {
            "numero": o.get("numero", ""), "titulo": o.get("titulo", ""),
            "dato": o.get("dato", ""), "tam": o.get("tam", "text-2xl md:text-3xl"),
        })
        attrs = format_html(' id="{}"', o["id"]) if o.get("id") else ""
        attrs += format_html(' data-pleg="{}"', clave)
        if o.get("cerrada_movil"):
            attrs += " data-movil-cerrada"
        if not o.get("cerrada"):
            attrs += " open"
        return format_html(
            '<details class="seccion-pleg {}"{}>{}<div class="seccion-cuerpo-pleg">{}</div></details>',
            o.get("clase", ""), mark_safe(attrs), mark_safe(resumen), mark_safe(self.cuerpo.render(contexto)),
        )


@register.tag
def pleg(parser, token):
    partes = token.split_contents()[1:]
    if not partes:
        raise template.TemplateSyntaxError("pleg necesita una clave")
    clave = parser.compile_filter(partes[0])
    opciones = {}
    for p in partes[1:]:
        k, _, v = p.partition("=")
        opciones[k] = parser.compile_filter(v)
    cuerpo = parser.parse(("endpleg",))
    parser.delete_first_token()
    return PlegNode(clave, opciones, cuerpo)


@register.filter
def cuenta(n, formas):
    """3|cuenta:"cita,citas" → «3 citas»; 1 → «1 cita»; solo para el dato del resumen."""
    uno, varios = formas.split(",")
    n = int(n or 0)
    return f"{n} {uno if n == 1 else varios}"
