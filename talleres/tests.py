from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Barrio, Servicio, SolicitudCita, Taller


class TalleresTests(TestCase):
    def setUp(self):
        self.barrio = Barrio.objects.create(nombre="Belén")
        self.servicio = Servicio.objects.create(nombre="Frenos")
        self.taller = Taller.objects.create(
            nombre="Taller Prueba", responsable="Ana", whatsapp="573001234567",
            direccion="Cra 1", barrio=self.barrio, activo=True,
        )
        self.taller.servicios.add(self.servicio)

    def test_inicio_lista_solo_activos(self):
        Taller.objects.create(nombre="Oculto", responsable="X", whatsapp="573000000000",
                              direccion="X", barrio=self.barrio, activo=False)
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, "Taller Prueba")
        self.assertNotContains(r, "Oculto")

    def test_filtro_por_servicio(self):
        otro = Servicio.objects.create(nombre="Llantas")
        r = self.client.get(reverse("talleres:inicio"), {"servicio": otro.id})
        self.assertNotContains(r, "Taller Prueba")

    def test_slug_unico(self):
        t2 = Taller.objects.create(nombre="Taller Prueba", responsable="B", whatsapp="573000000000",
                                   direccion="X", barrio=self.barrio)
        self.assertEqual(t2.slug, "taller-prueba-2")

    def test_solicitar_cita(self):
        r = self.client.post(self.taller.get_absolute_url(), {
            "accion": "cita", "nombre": "Juan", "telefono": "3001112233", "moto": "NKD 125",
            "servicio": self.servicio.id, "fecha_preferida": date.today() + timedelta(days=1),
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(SolicitudCita.objects.count(), 1)

    def test_resena_y_calificacion(self):
        self.client.post(self.taller.get_absolute_url(),
                         {"accion": "resena", "nombre": "Pedro", "estrellas": 4, "comentario": "Bien"})
        self.assertEqual(self.taller.calificacion, 4)

    def test_registro_queda_inactivo_y_normaliza_whatsapp(self):
        r = self.client.post(reverse("talleres:registro"), {
            "nombre": "Nuevo Taller", "responsable": "Luis", "whatsapp": "300 123 4567",
            "direccion": "Cll 2", "barrio": self.barrio.id, "servicios": [self.servicio.id],
        })
        self.assertEqual(r.status_code, 302)
        t = Taller.objects.get(nombre="Nuevo Taller")
        self.assertFalse(t.activo)
        self.assertEqual(t.whatsapp, "573001234567")
