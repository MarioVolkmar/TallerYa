"""Guía de bienvenida (primer uso). Se muestra a quien tiene perfil de motociclista, todavía no tiene motos y no la ha
terminado ni saltado. Las pantallas están en garaje/vista_bienvenida.py; aquí solo el «¿le toca?» y el «ya la vio»."""
from django.urls import reverse
from django.utils import timezone

from .models import Perfil


def pendiente(usuario):
    motero = getattr(usuario, "motociclista", None)
    if not usuario.is_authenticated or not motero:
        return False
    return Perfil.de(usuario).guia_terminada is None and not motero.motos.exists()


def marcar_vista(usuario):
    perfil = Perfil.de(usuario)
    if perfil.guia_terminada is None:
        perfil.guia_terminada = timezone.now()
        perfil.save(update_fields=["guia_terminada"])


def destino(usuario, por_defecto):
    """A dónde mandar a alguien que acaba de entrar o registrarse si no pidió una página concreta."""
    if getattr(usuario, "mecanico_domicilio", None) and not getattr(usuario, "taller", None):
        return reverse("domicilio:panel")  # el mecánico a domicilio entra a su panel
    return reverse("garaje:bienvenida") if pendiente(usuario) else por_defecto
