"""Consultas de Mi garaje y de la ficha de la moto: no crecen con la cantidad de motos, mantenimientos o lecturas."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from garaje.models import Despiece, LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from talleres.models import Marca


class GarajeConsultasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("m@m.co", "m@m.co", "clave-larga-123")
        self.motero = Motociclista.objects.create(usuario=self.usuario, nombre="Ana", celular="573001234567")
        self.marca = Marca.objects.get_or_create(nombre="Pruebas")[0]
        self.client.force_login(self.usuario)
        self.n = 0

    def _moto(self):
        self.n += 1
        linea = LineaMoto.objects.create(marca=self.marca, nombre=f"P {self.n}", cilindraje=150)
        Despiece.objects.create(linea=linea, version=f"V{self.n}", anio=2020)
        return Moto.objects.create(motociclista=self.motero, linea=linea, modelo=2022, placa=f"ABC1{self.n}D",
                                   km_actual=5000, km_inicial=0)

    def _contar(self, url):
        self.client.get(url)  # calienta avisos y cachés
        with CaptureQueriesContext(connection) as c:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(c)

    def test_mi_garaje_no_crece_con_las_motos(self):
        url = reverse("garaje:garaje") + "?lista=1"
        self._moto(); self._moto()
        dos = self._contar(url)
        self._moto(); self._moto()
        self.client.get(url)
        with self.assertNumQueries(dos):
            self.client.get(url)

    def test_ficha_no_crece_con_mantenimientos_ni_lecturas(self):
        moto = self._moto()
        url = moto.get_absolute_url()
        antes = self._contar(url)
        hoy = timezone.localdate()
        for i, tarea in enumerate(TareaMantenimiento.objects.filter(activo=True)[:6]):
            Mantenimiento.objects.create(moto=moto, tarea=tarea, km=1000 + i * 100, fecha=hoy - timedelta(days=60 - i))
        for i in range(8):
            LecturaKm.objects.create(moto=moto, km=1000 + i * 500, fecha=hoy - timedelta(days=40 - i * 5))
        self.client.get(url)
        with self.assertNumQueries(antes):
            self.client.get(url)
