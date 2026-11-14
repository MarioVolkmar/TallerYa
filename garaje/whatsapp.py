"""Envío de mensajes de WhatsApp.

Por defecto (WHATSAPP_BACKEND=consola) solo se registran en el log: así funciona en local y en pruebas.
Con WHATSAPP_BACKEND=cloud se usa la API de WhatsApp Cloud de Meta. Para mensajes que inicia el negocio
Meta exige una plantilla aprobada: WHATSAPP_PLANTILLA_PICO_PLACA con 3 variables (moto, día, horario).
"""
import json
import logging
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)


def enviar_plantilla(numero, plantilla, parametros, idioma="es"):
    """Devuelve True si el mensaje salió (o quedó en el log con el backend de consola)."""
    if getattr(settings, "WHATSAPP_BACKEND", "consola") != "cloud":
        log.info("WhatsApp (consola) a %s · %s · %s", numero, plantilla, parametros)
        return True
    cuerpo = {
        "messaging_product": "whatsapp", "to": numero, "type": "template",
        "template": {"name": plantilla, "language": {"code": idioma},
                     "components": [{"type": "body", "parameters": [{"type": "text", "text": str(p)} for p in parametros]}]},
    }
    peticion = urllib.request.Request(
        f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_ID}/messages", data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=10):
            return True
    except Exception:
        log.exception("No se pudo enviar el WhatsApp a %s", numero)
        return False
