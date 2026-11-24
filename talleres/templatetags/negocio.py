"""Vocabulario único de estados del negocio (taller y mecánico) en las plantillas: {{ c|estado_ui }}, chip-{{ c|estado_chip }}."""
from django import template

from talleres import negocio

register = template.Library()


@register.filter
def estado_ui(solicitud):
    return negocio.estado_texto(solicitud)


@register.filter
def estado_chip(solicitud):
    return negocio.estado_clase(solicitud)


@register.filter
def url_responder(resena):
    """Acción «Responder» de una reseña del taller o del mecánico."""
    from django.urls import reverse
    if getattr(resena, "mecanico_id", None):
        return reverse("domicilio:responder_resena", args=[resena.pk])
    return reverse("talleres:responder_resena", args=[resena.pk])


@register.filter
def url_cupon(cupon, accion):
    """Editar o pausar un cupón del taller o del mecánico: {{ cu|url_cupon:"editar" }}."""
    from django.urls import reverse
    if cupon.mecanico_id:
        return reverse(f"domicilio:descuento_{accion}", args=[cupon.pk])
    return reverse(f"talleres:cupon_{accion}", args=[cupon.pk])
