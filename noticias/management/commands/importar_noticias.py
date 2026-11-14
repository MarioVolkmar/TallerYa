from django.core.management.base import BaseCommand

from noticias.importar import importar_todas
from noticias.models import FuenteNoticias


class Command(BaseCommand):
    help = "Trae los titulares nuevos de las fuentes de noticias (RSS/Atom)."

    def handle(self, *args, **opciones):
        total = importar_todas()
        for f in FuenteNoticias.objects.filter(activa=True):
            self.stdout.write(f"  {f.nombre}: {'ERROR ' + f.ultimo_error if f.ultimo_error else 'ok'}")
        self.stdout.write(f"Noticias nuevas: {total}")
