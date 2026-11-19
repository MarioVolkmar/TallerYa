"""Revisa a diario las verificaciones de domiciliarios que vencieron: las renueva solas si hubo jornadas con km altos y
constantes (umbral en settings: RUTA_RENOVAR_*) o las marca vencidas y pide otra captura. Programarlo una vez al día."""
from django.core.management.base import BaseCommand

from domiciliarios.bandera import activo
from domiciliarios.verificacion import revisar_vencimientos


class Command(BaseCommand):
    help = "Renueva o vence las verificaciones de domiciliarios (TallerYa Ruta)."

    def handle(self, *args, **opciones):
        if not activo():
            self.stdout.write("TallerYa Ruta está apagado (DOMICILIARIOS_ACTIVO): no se revisa nada.")
            return
        renovadas, vencidas = revisar_vencimientos()
        self.stdout.write(f"Verificaciones renovadas: {renovadas} · vencidas: {vencidas}")
