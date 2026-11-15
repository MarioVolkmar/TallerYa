"""Único punto de cambio del pago del SOAT.

Hoy no hay aseguradora ni agencia aliada: el botón "Pagar" lleva a una página propia de PAGO DE PRUEBA que no
cobra nada ni pide datos de tarjeta. Para conectar el aliado: poner SOAT_PAGO_SIMULADO = False en settings y
completar `url_pago` (enlace del aliado) y `confirmar_pago` (lo llamaría el webhook o retorno del aliado).
"""
from django.conf import settings
from django.urls import reverse


def simulado():
    return getattr(settings, "SOAT_PAGO_SIMULADO", True)


def url_pago(pedido):
    """A dónde lleva el botón "Pagar"."""
    if not simulado() and pedido.enlace_pago:
        return pedido.enlace_pago
    return reverse("tramites:pago_prueba", args=[pedido.pk])


def confirmar_pago(pedido, simulado_=True):
    """Marca el pedido como pagado (desde la página de prueba o, más adelante, desde el aliado)."""
    pedido.pago_simulado = simulado_
    pedido.cambiar_estado(pedido.Estado.PAGADA)
