"""Cupones de ejemplo que se canjean con los puntos de las insignias (datos demo, no borra ni duplica)."""
from django.core.management.base import BaseCommand

from cupones.models import Cupon
from talleres.models import Taller

CONDICIONES = "Se canjea con puntos de TallerYa. No acumulable con otras promociones. Un uso por código."
CUPONES = (
    # (título, taller demo o None = todos los talleres, puntos)
    ("Lavado completo de la moto gratis", "Garaje 70", 40),
    ("10% en cambio de aceite", "MotoServicio El Paisa", 50),
    ("Revisión y ajuste de frenos gratis", "Frenos y Más", 70),
    ("Diagnóstico eléctrico gratis", "Electromotos Envigado", 90),
    ("$20.000 de descuento en cualquier taller aliado", None, 120),
)


class Command(BaseCommand):
    help = "Crea cupones canjeables con puntos de insignias (solo los que falten)."

    def handle(self, *args, **opciones):
        nuevos = 0
        for titulo, nombre_taller, puntos in CUPONES:
            taller = Taller.objects.filter(nombre=nombre_taller).first() if nombre_taller else None
            if nombre_taller and not taller:
                continue  # sin ese taller demo no se inventa otro
            _, creado = Cupon.objects.get_or_create(
                titulo=titulo, taller=taller, puntos_logros=puntos,
                defaults={"condiciones": CONDICIONES, "publico": False, "cupo": 50},
            )
            nuevos += creado
        self.stdout.write(self.style.SUCCESS(f"Cupones por puntos: {nuevos} nuevos."))
