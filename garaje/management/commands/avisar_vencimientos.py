"""Avisos dentro de TallerYa: SOAT y técnico-mecánica 30, 15 y 3 días antes (y vencidos), y pico y placa del día.

Idempotente: cada aviso tiene una clave única por persona, así que correrlo varias veces no repite nada.
Se dispara una vez al día temprano (5:30 a. m.): con cron, o gratis con GitHub Actions llamando a
POST /tareas/avisos/ (ver garaje/vista_tareas.py y .github/workflows/avisos.yml).
"""
from datetime import date

from django.core.management.base import BaseCommand

from garaje.avisos import notificar_todas


class Command(BaseCommand):
    help = "Crea las notificaciones de vencimientos y de pico y placa de hoy, sin repetir las ya creadas."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=date.fromisoformat, help="Día a revisar (AAAA-MM-DD). Por defecto, hoy.")

    def handle(self, *args, **opciones):
        self.stdout.write(f"Avisos nuevos: {notificar_todas(opciones['fecha'])}")
