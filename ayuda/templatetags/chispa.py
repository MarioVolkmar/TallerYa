"""Interruptor de Chispa en estados vacíos y páginas de error.

Se apaga en todo el sitio con CHISPA_EN_VACIOS = False en settings
(o la variable de entorno CHISPA_EN_VACIOS=0). No toca la base de datos,
así que sirve también en la página 500.
"""
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def chispa_en_vacios():
    return getattr(settings, "CHISPA_EN_VACIOS", True)
