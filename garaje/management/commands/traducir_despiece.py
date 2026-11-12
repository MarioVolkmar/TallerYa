"""Vuelve a calcular nombres en español y explicaciones de las piezas, sin tocar las marcas.

Uso: python manage.py traducir_despiece   (útil después de mejorar garaje/despiece_glosario.py)
"""
from django.core.management.base import BaseCommand

from garaje.despiece_glosario import ayuda_para, traducir
from garaje.models import ParteDespiece


class Command(BaseCommand):
    help = "Actualiza nombre_es y ayuda de todas las piezas del despiece con el glosario"

    def handle(self, **opts):
        cambiadas, sin_nombre = 0, set()
        for parte in ParteDespiece.objects.all():
            nombre, ayuda = traducir(parte.descripcion), ayuda_para(parte.descripcion)
            if not nombre:
                sin_nombre.add(parte.descripcion)
            if (nombre, ayuda) != (parte.nombre_es, parte.ayuda):
                parte.nombre_es, parte.ayuda = nombre, ayuda
                parte.save(update_fields=["nombre_es", "ayuda"])
                cambiadas += 1
        self.stdout.write(self.style.SUCCESS(f"{cambiadas} piezas actualizadas."))
        if sin_nombre:
            self.stdout.write("Sin traducción (se muestra el texto original): " + ", ".join(sorted(sin_nombre)))
