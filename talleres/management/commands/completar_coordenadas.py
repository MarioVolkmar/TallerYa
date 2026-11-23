"""Calcula las coordenadas de los talleres que no las tienen (o solo las tienen aproximadas) desde su dirección y barrio."""
import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from talleres.geocodificar import completar_ubicacion
from talleres.models import Taller


class Command(BaseCommand):
    help = "Completa latitud/longitud de los talleres sin ubicación exacta (Nominatim, 1 consulta por segundo)."

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Solo muestra lo que haría")

    def handle(self, *args, simular=False, **opciones):
        hechos = 0
        for t in Taller.objects.select_related("barrio").filter(Q(ubicacion_exacta=False) | Q(latitud__isnull=True)):
            if simular:
                self.stdout.write(f"{t.nombre}: {t.direccion}, {t.barrio}")
                continue
            if completar_ubicacion(t):
                t.save(update_fields=["latitud", "longitud", "ubicacion_exacta"])
                hechos += 1
                self.stdout.write(f"{t.nombre}: {'exacta' if t.ubicacion_exacta else 'del barrio'}")
            else:
                self.stdout.write(f"{t.nombre}: sin resultado")
            time.sleep(1.1)  # política de Nominatim
        self.stdout.write(self.style.SUCCESS(f"{hechos} taller(es) actualizados."))
