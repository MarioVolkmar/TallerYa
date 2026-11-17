from django import template
from django.utils.safestring import mark_safe

from consola.limites import LIMITES

register = template.Library()

# Trazos propios (24x24, stroke). Mismo estilo que los íconos de la cabecera de TallerYa.
ICONOS = {
    "tablero": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "personas": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "taller": '<path d="M3 21V9l9-5 9 5v12"/><path d="M8 21v-7h8v7"/><path d="M8 17h8"/>',
    "calendario": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "estrella": '<path d="m12 3 2.7 5.6 6.1.8-4.4 4.3 1 6.1L12 17l-5.4 2.8 1-6.1-4.4-4.3 6.1-.8z"/>',
    "cupon": '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M10 6v12" stroke-dasharray="2 2"/>',
    "bandera": '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    "grafica": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "lista": '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
    "campana": '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    "ajustes": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    "libro": '<path d="M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4z"/><path d="M20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z"/>',
    "lupa": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "atras": '<path d="M15 18l-6-6 6-6"/>',
}


@register.simple_tag
def icono(nombre, tam=18):
    trazo = ICONOS.get(nombre, ICONOS["lista"])
    return mark_safe(f'<svg viewBox="0 0 24 24" width="{tam}" height="{tam}" fill="none" stroke="currentColor" '
                     f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazo}</svg>')


@register.simple_tag
def limite(campo):
    """Atributos minlength/maxlength desde consola/limites.py (los mismos que valida el servidor)."""
    l = LIMITES[campo]
    attrs = f'maxlength="{l["max"]}"'
    if l["min"]:
        attrs += f' minlength="{l["min"]}"'
    return mark_safe(attrs)


@register.filter
def get_item(diccionario, clave):
    return diccionario.get(clave, "")
