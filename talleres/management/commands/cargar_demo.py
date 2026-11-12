"""Carga datos de ejemplo: python manage.py cargar_demo"""
from django.core.management.base import BaseCommand

from talleres.models import Barrio, Marca, Resena, Servicio, Taller

BARRIOS = ["Belén", "Laureles", "Envigado", "Itagüí", "Robledo", "Buenos Aires", "Bello", "Centro"]
SERVICIOS = ["Mantenimiento general", "Cambio de aceite", "Frenos", "Sistema eléctrico",
             "Suspensión", "Latonería y pintura", "Llantas", "Revisión técnico-mecánica"]
MARCAS = ["AKT", "Auteco Bajaj", "Honda", "Suzuki", "Yamaha", "TVS", "KTM", "Hero"]

DEMO = [
    ("MotoServicio El Paisa", "Belén", [0, 1, 2], [4, 2], True, True),
    ("Taller Rueda Libre", "Laureles", [0, 3, 4], [3, 2, 0], True, False),
    ("Electromotos Envigado", "Envigado", [3, 7], [1, 5], False, False),
    ("Frenos y Más", "Itagüí", [2, 6], [0, 1, 7], True, False),
]


class Command(BaseCommand):
    help = "Carga barrios, servicios, marcas y talleres de ejemplo"

    def handle(self, *args, **opts):
        barrios = {n: Barrio.objects.get_or_create(nombre=n)[0] for n in BARRIOS}
        servicios = [Servicio.objects.get_or_create(nombre=n)[0] for n in SERVICIOS]
        marcas = [Marca.objects.get_or_create(nombre=n)[0] for n in MARCAS]

        for nombre, barrio, s_idx, m_idx, verificado, destacado in DEMO:
            t, creado = Taller.objects.get_or_create(nombre=nombre, defaults={
                "responsable": "Demo", "whatsapp": "573000000000",
                "direccion": "Calle 00 # 00-00", "barrio": barrios[barrio],
                "horario": "Lun-Sáb 8am-6pm", "descripcion": "Taller de ejemplo.",
                "verificado": verificado, "activo": True, "destacado": destacado,
            })
            if creado:
                t.servicios.set([servicios[i] for i in s_idx])
                t.marcas.set([marcas[i] for i in m_idx])
                Resena.objects.create(taller=t, nombre="Carlos", estrellas=5, comentario="Muy buen servicio y precio justo.")
                Resena.objects.create(taller=t, nombre="Laura", estrellas=4, comentario="Rápidos y cumplidos.")
        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))
