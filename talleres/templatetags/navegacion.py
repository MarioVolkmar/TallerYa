"""Navegación de base.html: qué sección del menú está activa según la ruta.

Se usa como {% seccion_activa as sec %} y luego {% if sec == "garaje" %}aria-current="true"{% endif %}.
"""
from django import template

register = template.Library()

# Prefijo de ruta -> sección del menú. El primero que coincide gana (los más específicos van antes).
SECCIONES = (
    ("/mi-taller/citas", "taller_citas"),
    ("/mi-taller/perfil", "taller_perfil"),
    ("/mi-taller", "taller_panel"),
    ("/canjear", "taller_canjear"),
    ("/talleres", "talleres"),
    ("/taller/", "talleres"),
    ("/mecanicos", "talleres"),
    ("/garaje", "garaje"),
    ("/bienvenida", "garaje"),
    ("/diagnostico", "garaje"),
    ("/soat", "garaje"),
    ("/tecnomecanica", "garaje"),
    ("/domiciliarios", "garaje"),
    ("/foro", "comunidad"),
    ("/cupones", "cupones"),
    ("/cupon/", "cupones"),
    ("/emergencias", "emergencias"),
    ("/consola", "consola"),
)


def seccion_de(ruta):
    if ruta == "/":
        return "inicio"
    for prefijo, seccion in SECCIONES:
        if ruta.startswith(prefijo):
            return seccion
    return ""


@register.simple_tag(takes_context=True)
def seccion_activa(context):
    request = context.get("request")
    return seccion_de(request.path) if request else ""
