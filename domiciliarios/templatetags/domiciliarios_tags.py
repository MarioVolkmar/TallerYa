"""{% aviso_domiciliarios %}: tarjeta de entrada al plan (en Mi garaje). Con la bandera apagada no pinta nada."""
from django import template

from ..bandera import activo

register = template.Library()


@register.inclusion_tag("domiciliarios/_aviso.html", takes_context=True)
def aviso_domiciliarios(context):
    if not activo():
        return {"mostrar": False}
    request = context.get("request")
    motociclista = getattr(request.user, "motociclista", None) if request and request.user.is_authenticated else None
    es = bool(motociclista) and hasattr(motociclista, "domiciliario")
    return {"mostrar": True, "es_domiciliario": es}
