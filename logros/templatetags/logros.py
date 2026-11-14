"""{% load logros %}{% insignias usuario %}: fila de insignias ganadas, para Mi cuenta y el perfil público."""
from django import template

from ..reglas import resumen

register = template.Library()


@register.inclusion_tag("logros/_insignias.html", takes_context=True)
def insignias(context, usuario, enlace=False):
    """enlace=True agrega el acceso a "Mis insignias" (solo en Mi cuenta)."""
    return {"items": resumen(usuario) if usuario and usuario.pk else [], "enlace": enlace}
