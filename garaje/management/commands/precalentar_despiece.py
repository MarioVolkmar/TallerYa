"""Arma y guarda en caché el despiece de todas las motos, para que nadie espere al abrirlo tras un despliegue.

Idempotente: lo que ya está en caché (con el código y los datos de hoy) se salta. Con --max-segundos para a tiempo
y dice cuántos faltan, para que una llamada HTTP no supere el límite del servidor; se repite hasta que falten 0.
"""
import time

from django.core.cache import caches
from django.core.management import call_command
from django.core.management.base import BaseCommand

from garaje.models import Despiece
from garaje.views import base_despiece, clave_base_despiece


class Command(BaseCommand):
    help = "Precalienta la caché del despiece de todos los catálogos activos."

    def add_arguments(self, parser):
        parser.add_argument("--max-segundos", type=float, default=15,
                            help="Deja de armar despieces nuevos pasado este tiempo (por defecto 15, para caber en una petición HTTP; 0 = sin límite).")

    def handle(self, *args, max_segundos=15, **opciones):
        inicio = time.perf_counter()
        call_command("createcachetable")      # por si el despliegue no la creó (no hace nada si ya existe)
        cache = caches["despiece"]
        listos = armados = 0
        faltan = []
        for despiece in Despiece.objects.filter(activo=True, laminas__isnull=False).distinct().select_related("linea"):
            if cache.has_key(clave_base_despiece(despiece)):
                listos += 1
                continue
            if max_segundos and time.perf_counter() - inicio > max_segundos:
                faltan.append(despiece)
                continue
            t = time.perf_counter()
            base_despiece(despiece)
            armados += 1
            self.stdout.write(f"{despiece.linea} {despiece.version}: {time.perf_counter() - t:.1f} s")
        self.stdout.write(f"Armados {armados}, ya estaban {listos}, faltan {len(faltan)} "
                          f"({time.perf_counter() - inicio:.1f} s).")
