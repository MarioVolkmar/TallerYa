"""Hoja de estilos de la sección: {% css_seccion %} en templates/base.html.

tallerya.css es la base común; las reglas que solo usan las páginas de una app (garaje, foro, cuentas...) viven en
talleres/static/talleres/css/secciones/<app>.css y se cargan solo en esas páginas. La sección sale del nombre de la
plantilla que pidió la vista (garaje/moto.html → garaje), que es la que trae las clases de esas reglas.
"""
from functools import lru_cache
from pathlib import Path

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()
CARPETA = Path(__file__).resolve().parent.parent / "static" / "talleres" / "css" / "secciones"


@lru_cache(maxsize=1)
def secciones():
    return frozenset(p.stem for p in CARPETA.glob("*.css"))


def seccion_de(nombre):
    nombre = nombre or ""
    sec = nombre.split("/", 1)[0] if "/" in nombre else ""
    return sec if sec in secciones() else ""


@register.simple_tag(takes_context=True)
def css_seccion(context):
    plantilla = getattr(context, "template", None)
    sec = seccion_de(getattr(plantilla, "name", ""))
    if not sec:
        return ""
    return format_html('<link rel="stylesheet" href="{}">', static(f"talleres/css/secciones/{sec}.css"))
