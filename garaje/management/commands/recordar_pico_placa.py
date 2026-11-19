"""Recordatorio de pico y placa por WhatsApp para mañana. Programarlo una vez al día por la tarde (p. ej. 6 p. m.).

TallerYa Ruta (con DOMICILIARIOS_ACTIVO): a las motos de trabajo les deja además el aviso dentro de TallerYa la noche
anterior (misma clave que el aviso al navegar, así que nunca se repite), aunque no tengan WhatsApp activado."""
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
        self.stdout.write(f"Avisos de pico y placa a domiciliarios: {self.avisar_domiciliarios(manana)}")

    def avisar_domiciliarios(self, manana):
        from domiciliarios.bandera import activo
        if not activo():
            return 0
        from domiciliarios.models import PerfilDomiciliario
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        avisos = 0
        for perfil in (PerfilDomiciliario.objects.filter(moto__isnull=False, motociclista__usuario__isnull=False)
                       .exclude(moto__placa="").select_related("moto", "motociclista__usuario")):
            moto = perfil.moto
            aplica, regla = tiene_pico_placa(moto, manana)
            if aplica and notificar(perfil.motociclista.usuario, f"pyp:{moto.pk}:{manana}", "Mañana tienes pico y placa",
                                    f"{moto} · placa {moto.placa} · {regla.horario}. Planea tu jornada.",
                                    f"{moto.get_absolute_url()}#mi-ruta", Notificacion.Tipo.GENERAL):
                avisos += 1
        return avisos
