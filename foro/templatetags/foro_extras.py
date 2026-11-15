"""Etiquetas del foro: cifras compactas ("1,2 mil") y fechas relativas en una sola unidad ("hace 19 h")."""
from django import template
from django.utils import timezone
from django.utils.dateformat import format as formato_fecha
from django.utils.html import format_html

register = template.Library()


@register.filter
def cifra_corta(n):
    """1–999 tal cual; 1.000+ como "1,2 mil"; millones como "1,2 M" (formato es-CO)."""
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return n
    if n < 1000:
        return str(n)
    valor, unidad = (n / 1_000_000, "M") if n >= 1_000_000 else (n / 1000, "mil")
    texto = f"{valor:.1f}".rstrip("0").rstrip(".").replace(".", ",") if valor < 100 else str(int(valor))
    return f"{texto} {unidad}"


def hace_texto(fecha, ahora=None):
    segundos = max(0, int(((ahora or timezone.now()) - fecha).total_seconds()))
    if segundos < 60:
        return "hace un momento"
    for limite, divisor, singular, plural in (
        (3600, 60, "min", "min"), (86400, 3600, "h", "h"), (30 * 86400, 86400, "día", "días"),
        (365 * 86400, 30 * 86400, "mes", "meses"), (None, 365 * 86400, "año", "años"),
    ):
        if limite is None or segundos < limite:
            n = segundos // divisor
            return f"hace {n} {singular if n == 1 else plural}"


@register.simple_tag
def hace(fecha):
    """<time> con "hace 19 h" y la fecha exacta al pasar el mouse."""
    if not fecha:
        return ""
    local = timezone.localtime(fecha)
    return format_html('<time datetime="{}" title="{}">{}</time>', local.isoformat(),
                       formato_fecha(local, r"j \d\e F \d\e Y, g:i a"), hace_texto(fecha))


# Ícono de trazo por categoría (las categorías son opciones fijas de Pregunta.categoria). Las nuevas usan el de "general".
ICONOS_CATEGORIA = {
    # llave inglesa
    "fallas": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L3.6 17.2a1.6 1.6 0 0 0 2.3 2.3l5.7-5.7a4 4 0 0 0 5.2-5.4l-2.4 2.4-2.1-.5-.5-2.1z"/>',
    # gota de aceite
    "mantenimiento": '<path d="M12 3s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>',
    # pin con ruta
    "rutas": '<path d="M12 21s6-5.3 6-10a6 6 0 0 0-12 0c0 4.7 6 10 6 10z"/><circle cx="12" cy="11" r="2"/>',
    # etiqueta de precio
    "repuestos": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.3"/>',
    # casa con llave
    "talleres": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    # globo de diálogo
    "general": '<path d="M4 5h16v11H9l-5 4z"/>',
}


@register.simple_tag
def icono_categoria(clave, tam=14):
    """<svg> del ícono de la categoría (trazo, color heredado)."""
    from django.utils.safestring import mark_safe
    trazos = ICONOS_CATEGORIA.get(clave, ICONOS_CATEGORIA["general"])
    return mark_safe(f'<svg class="fo-ico-cat" viewBox="0 0 24 24" width="{int(tam)}" height="{int(tam)}" fill="none" '
                     f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                     f'aria-hidden="true">{trazos}</svg>')
