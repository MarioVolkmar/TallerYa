from django import template

register = template.Library()


@register.filter
def get_item(diccionario, clave):
    """Acceso a un diccionario con clave variable en plantillas: {{ d|get_item:clave }}."""
    return diccionario.get(clave) if hasattr(diccionario, "get") else None
