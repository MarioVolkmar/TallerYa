"""Avisos dentro de TallerYa: SOAT y técnico-mecánica 30, 15 y 3 días antes (y vencidos), y pico y placa del día.

Idempotente: cada aviso tiene una clave única por persona, así que correrlo varias veces no repite nada.
Para cron, una vez al día temprano (p. ej. 5:30 a. m.):  python manage.py avisar_vencimientos
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from garaje.avisos import notificar_moto
from garaje.models import Moto


class Command(BaseCommand):
    help = "Crea las notificaciones de vencimientos y de pico y placa de hoy, sin repetir las ya creadas."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=date.fromisoformat, help="Día a revisar (AAAA-MM-DD). Por defecto, hoy.")

    def handle(self, *args, **opciones):
        ahora = timezone.localtime()
        hoy = opciones["fecha"] or ahora.date()
        # El de pico y placa es del mismo día: después de las 8 p. m. ya no sirve.
        pico_placa = hoy != ahora.date() or ahora.hour < 20
        motos = Moto.objects.filter(motociclista__usuario__isnull=False).select_related(
            "motociclista__usuario", "linea", "linea__marca")
        creadas = sum(notificar_moto(m, hoy, pico_placa) for m in motos.iterator())
        self.stdout.write(f"Avisos nuevos: {creadas}")
