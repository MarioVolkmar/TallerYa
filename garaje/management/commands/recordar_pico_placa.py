"""Recordatorio de pico y placa por WhatsApp para mañana. Programarlo una vez al día por la tarde (p. ej. 6 p. m.)."""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from garaje.models import Moto
from garaje.pico_placa import DIAS_LARGOS, tiene_pico_placa
from garaje.whatsapp import enviar_plantilla


class Command(BaseCommand):
    help = "Envía por WhatsApp el recordatorio de pico y placa de mañana a quienes lo activaron."

    def handle(self, *args, **opciones):
        manana = timezone.localdate() + timedelta(days=1)
        enviados = 0
        motos = (Moto.objects.filter(pico_placa_whatsapp=True).exclude(placa="")
                 .exclude(pico_placa_enviado=manana).select_related("motociclista", "linea", "linea__marca"))
        for moto in motos:
            aplica, regla = tiene_pico_placa(moto, manana)
            if not aplica:
                continue
            parametros = [str(moto), f"{DIAS_LARGOS[manana.weekday()]} {manana.day}", regla.horario]
            if enviar_plantilla(moto.motociclista.celular, settings.WHATSAPP_PLANTILLA_PICO_PLACA, parametros):
                moto.pico_placa_enviado = manana
                moto.save(update_fields=["pico_placa_enviado"])
                enviados += 1
        self.stdout.write(f"Recordatorios de pico y placa enviados: {enviados}")
