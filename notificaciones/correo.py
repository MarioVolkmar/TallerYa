"""Correo de respaldo para los avisos urgentes, solo a quien no recibió el push, con enlace para darse de baja."""
import logging

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)

# Cita nueva al taller, solicitud nueva al mecánico y su aceptación o rechazo al motero.
PREFIJOS_URGENTES = ("cita-nueva:", "visita-nueva:", "cita-confirmada:", "cita-cancelada:",
                     "visita-confirmada:", "visita-cancelada:")
SAL = "baja-correo-avisos"


def token_baja(usuario):
    return signing.dumps(usuario.pk, salt=SAL)


def usuario_de_token(token):
    from django.contrib.auth import get_user_model
    try:
        pk = signing.loads(token, salt=SAL)
    except signing.BadSignature:
        return None
    return get_user_model().objects.filter(pk=pk).first()


def _sitio():
    return (settings.SITIO_URL or "").rstrip("/")


def enviar_respaldo(notif):
    """Manda el correo si el aviso es urgente, la persona tiene correo y no se dio de baja. Devuelve True si se envió."""
    if not notif.clave.startswith(PREFIJOS_URGENTES):
        return False
    usuario = notif.usuario
    if not usuario.email or not usuario.is_active:
        return False
    from cuentas.models import Perfil
    if Perfil.objects.filter(usuario=usuario, correos_avisos=False).exists():  # consulta fresca: sin perfil = recibe
        return False
    try:
        enlace = _sitio() + reverse("notificaciones:ir", args=[notif.pk])
        baja = _sitio() + reverse("notificaciones:baja_correo", args=[token_baja(usuario)])
        send_mail(
            notif.titulo[:120],
            f"{notif.texto}\n\nMíralo aquí: {enlace}\n\n"
            "Activa los avisos en tu celular desde TallerYa y dejamos de escribirte.\n"
            f"Si no quieres recibir estos correos: {baja}\n\nTallerYa",
            None, [usuario.email])
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo de respaldo")
        return False
