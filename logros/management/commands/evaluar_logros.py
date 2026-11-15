"""Tarea diaria: insignias que dependen del tiempo (rodadas que ya pasaron).

Solo revisa a quienes asistieron a rodadas de los últimos 2 días. Es idempotente.
Las demás insignias se otorgan al momento (logros/signals.py).
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from logros import reglas


class Command(BaseCommand):
    help = "Otorga las insignias de rodadas que ya pasaron."

    def handle(self, *args, **opciones):
        ahora = timezone.now()
        Usuario = get_user_model()
        rodadores = Usuario.objects.filter(
            asistencias_rodada__rodada__fecha_hora__lt=ahora,
            asistencias_rodada__rodada__fecha_hora__gte=ahora - timedelta(days=2),
        ).distinct()
        nuevos = sum(reglas.evaluar(u, ["rodada"]) for u in rodadores)
        self.stdout.write(f"Insignias nuevas: {nuevos}")
