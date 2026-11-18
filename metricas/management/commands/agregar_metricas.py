"""Resume por día los eventos de uso y borra los crudos de más de 90 días. Para el cron diario (ver render.yaml)."""
from django.core.management.base import BaseCommand

from metricas import agregacion


class Command(BaseCommand):
    help = "Agrega las métricas de uso por día y borra los eventos crudos de más de 90 días."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=agregacion.DIAS_CRUDOS,
                            help="Días de eventos crudos que se conservan (por defecto 90).")

    def handle(self, *args, dias, **opciones):
        resumidos = agregacion.agregar_pendientes()
        borrados = agregacion.purgar(dias=dias)
        self.stdout.write(self.style.SUCCESS(f"Días resumidos: {resumidos}. Eventos crudos borrados: {borrados}."))
