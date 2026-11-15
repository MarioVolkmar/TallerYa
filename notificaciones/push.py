"""Avisos push (Web Push con VAPID). Sin claves en el entorno, todo esto no hace nada."""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def configurado():
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def enviar_a_usuario(usuario, titulo, texto="", url="/", clave=""):
    """Manda el push a todos los dispositivos de la persona. Devuelve cuántos se enviaron."""
    if not configurado():
        return 0
    from .models import SuscripcionPush
    suscripciones = list(SuscripcionPush.objects.filter(usuario=usuario))
    if not suscripciones:
        return 0
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush no está instalado: no se envían avisos push")
        return 0
    carga = json.dumps({"titulo": titulo, "texto": texto, "url": url, "tag": clave or "tallerya"})
    enviados = 0
    for s in suscripciones:
        try:
            webpush(
                subscription_info=s.como_dict(), data=carga,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT}, timeout=5, ttl=24 * 3600,
            )
            enviados += 1
        except WebPushException as e:
            estado = getattr(e.response, "status_code", None)
            if estado in (404, 410):  # la suscripción ya no existe: se limpia
                s.delete()
            else:
                logger.warning("Push falló (%s): %s", estado, e)
        except Exception:
            logger.exception("Push falló para la suscripción %s", s.pk)
    return enviados


def enviar_notificacion(notif):
    """Push de una notificación recién creada; el enlace pasa por 'ir' para marcarla leída."""
    if not configurado():
        return 0
    from django.urls import reverse
    return enviar_a_usuario(notif.usuario, notif.titulo, notif.texto,
                            reverse("notificaciones:ir", args=[notif.pk]), notif.clave)
