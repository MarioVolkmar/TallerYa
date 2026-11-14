from django import template

from ..avatares import html_avatar

register = template.Library()


@register.simple_tag
def avatar(usuario, tam=40):
    """{% avatar user 32 %} → foto, avatar prediseñado o inicial."""
    return html_avatar(usuario, tam)


@register.simple_tag
def logo_taller(taller, tam=64):
    """{% logo_taller taller 64 %} → foto del taller, o el avatar que eligió la cuenta del taller, o "" (la plantilla pone la inicial)."""
    from django.utils.html import format_html
    if taller.foto:
        return format_html('<img src="{}" width="{}" height="{}" class="avatar" alt="" loading="lazy">', taller.foto.url, tam, tam)
    dueno = taller.usuario
    perfil = getattr(dueno, "perfil", None) if dueno else None
    if perfil and (perfil.avatar_foto or perfil.avatar_predisenado):
        return html_avatar(dueno, tam)
    return ""
