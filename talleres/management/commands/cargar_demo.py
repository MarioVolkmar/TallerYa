"""Carga datos de ejemplo: python manage.py cargar_demo"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cupones.models import Cupon

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
        hoy = timezone.localdate()
        cupones = [
            ("MotoServicio El Paisa", "15% de descuento en cambio de aceite",
             "Aplica para aceite mineral o semisintético. No acumulable.", hoy + timedelta(days=60), 100, True, False),
            ("Frenos y Más", "Revisión de frenos gratis",
             "Al comprar pastillas o bandas en el taller.", hoy + timedelta(days=30), 50, True, False),
            ("Taller Rueda Libre", "Diagnóstico eléctrico a mitad de precio",
             "Lunes a viernes.", None, None, True, False),
            (None, "$20.000 de descuento en cualquier taller aliado",
             "Premio por invitar amigos. Servicios desde $60.000.", None, None, False, True),
        ]
        for taller, titulo, condiciones, hasta, cupo, publico, premio in cupones:
            Cupon.objects.get_or_create(titulo=titulo, defaults={
                "taller": Taller.objects.filter(nombre=taller).first() if taller else None,
                "condiciones": condiciones, "valido_hasta": hasta, "cupo": cupo,
                "publico": publico, "premio_referido": premio,
            })

        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))
        self.stdout.write("PIN de canje por taller (solo para pruebas):")
        for nombre, pin in Taller.objects.values_list("nombre", "pin_canje"):
            self.stdout.write(f"  {nombre}: {pin}")
