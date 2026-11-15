"""{% load logros %}{% insignias usuario %}: insignias del usuario, para Mi cuenta y el perfil público."""
from django import template

from ..reglas import INSIGNIAS, puntos_disponibles, resumen

register = template.Library()


@register.inclusion_tag("logros/_insignias.html", takes_context=True)
def insignias(context, usuario, enlace=False):
    """enlace=True (Mi cuenta): las 4 insignias, ganadas y por ganar, con los puntos y el acceso a "Mis insignias".
    Sin enlace (perfil público): solo las ganadas."""
    if not (usuario and usuario.pk):
        return {"items": [], "enlace": enlace}
    ganadas = {it["insignia"].clave: it["veces"] for it in resumen(usuario)}
    if not enlace:
        return {"items": [{"insignia": INSIGNIAS[c], "veces": n} for c, n in ganadas.items()], "enlace": False}
    return {
        "enlace": True,
        "todas": [{"insignia": i, "veces": ganadas.get(c, 0)} for c, i in INSIGNIAS.items()],
        "ganadas": len(ganadas),
        "total": len(INSIGNIAS),
        "puntos": puntos_disponibles(usuario),
    }
