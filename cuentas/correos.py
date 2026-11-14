"""Envío de correos de TallerYa: HTML estilizado (plantillas en templates/correos/) + versión en texto plano.

El servidor de correo se configura con las variables EMAIL_* (en local salen por la consola).
"""
import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

log = logging.getLogger(__name__)


class TokenVerificacion(PasswordResetTokenGenerator):
    """Enlace de verificación de correo: deja de servir al verificar o si cambia el correo. Vence como el de contraseña (3 días)."""
    key_salt = "tallerya.cuentas.verificar-correo"

    def _make_hash_value(self, usuario, momento):
        from .models import Perfil
        verificado = Perfil.objects.filter(usuario=usuario, correo_verificado=True).exists()
        return f"{usuario.pk}{usuario.email}{momento}{verificado}"


token_verificacion = TokenVerificacion()


def sitio(request=None):
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return getattr(settings, "SITIO_URL", "").rstrip("/")


def enviar(destinatario, asunto, plantilla, contexto=None, request=None):
    """Envía correos/<plantilla>.html y .txt. Devuelve True si salió (un fallo del servidor de correo no rompe la página)."""
    datos = {"sitio": sitio(request), "asunto": asunto, **(contexto or {})}
    mensaje = EmailMultiAlternatives(asunto, render_to_string(f"correos/{plantilla}.txt", datos).strip(),
                                     settings.DEFAULT_FROM_EMAIL, [destinatario])
    mensaje.attach_alternative(render_to_string(f"correos/{plantilla}.html", datos), "text/html")
    try:
        mensaje.send()
        return True
    except Exception:
        log.exception("No se pudo enviar el correo '%s' a %s", plantilla, destinatario)
        return False


def enviar_verificacion(request, usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    url = sitio(request) + reverse("cuentas:verificar", args=[uid, token_verificacion.make_token(usuario)])
    return enviar(usuario.email, "Confirma tu correo en TallerYa", "verificar", {"usuario": usuario, "url": url}, request)


def avisar_contrasena_cambiada(request, usuario):
    return enviar(usuario.email, "Tu contraseña de TallerYa cambió", "contrasena_cambiada",
                  {"usuario": usuario, "url": sitio(request) + reverse("cuentas:recuperar")}, request)
