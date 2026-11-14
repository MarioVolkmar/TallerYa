from django import template

from ..avatares import html_avatar

register = template.Library()


@register.simple_tag
def avatar(usuario, tam=40):
    """{% avatar user 32 %} → foto, avatar prediseñado o inicial."""
    return html_avatar(usuario, tam)
