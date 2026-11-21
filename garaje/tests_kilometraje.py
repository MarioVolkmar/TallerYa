"""Kilometraje fácil: perfil de uso, km estimado, confirmación de un toque y botones de cotizar/domicilio."""
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .kilometraje import KM_DIA_PERFIL, km_estimado_hoy, km_valido, pregunta_km, registrar_lectura
from .models import LecturaKm
from .plan import ritmo_km
from .tests_avisos import crear_moto

HOY = date(2026, 11, 20)


class KilometrajeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moto = crear_moto(km_inicial=8000, km_actual=8000, perfil_uso="ciudad", modelo=2025)
        # dos lecturas: 10 km/día exactos, la última hace 40 días
        LecturaKm.objects.create(moto=cls.moto, km=7000, fecha=HOY - timedelta(days=140))
        LecturaKm.objects.create(moto=cls.moto, km=8000, fecha=HOY - timedelta(days=40))

    def test_perfil_da_ritmo_inicial(self):
        moto = crear_moto("b@x.com", "573001110001", perfil_uso="fines_semana", modelo=2025, km_actual=500)
        self.assertEqual(ritmo_km(moto, HOY), (KM_DIA_PERFIL["fines_semana"], True))

    def test_con_lecturas_el_ritmo_es_el_real(self):
        ritmo, estimado = ritmo_km(self.moto, HOY)
        self.assertFalse(estimado)
        self.assertAlmostEqual(ritmo, 10, delta=0.5)

    def test_km_estimado_hoy_redondeado(self):
        self.assertEqual(km_estimado_hoy(self.moto, HOY), 8400)

    def test_pregunta_solo_si_toca(self):
        self.assertEqual(pregunta_km(self.moto, HOY)["km"], 8400)
        self.assertIsNone(pregunta_km(self.moto, HOY - timedelta(days=20)))  # última lectura reciente

    def test_pospuesta_no_pregunta_unos_dias(self):
        self.moto.km_pregunta_pospuesta = HOY - timedelta(days=2)
        self.assertIsNone(pregunta_km(self.moto, HOY))
        self.moto.km_pregunta_pospuesta = HOY - timedelta(days=8)
        self.assertIsNotNone(pregunta_km(self.moto, HOY))

    def test_registrar_lectura_recalibra(self):
        moto = crear_moto("c@x.com", "573001110002", km_actual=1000, km_inicial=1000)
        self.assertIsNone(registrar_lectura(moto, 900))  # no baja
        registrar_lectura(moto, 1500, HOY, estimada=True)
        moto.refresh_from_db()
        self.assertEqual(moto.km_actual, 1500)
        self.assertTrue(moto.lecturas.get(km=1500).estimada)

    def test_km_valido(self):
        self.assertFalse(km_valido(self.moto, 8000))
        self.assertTrue(km_valido(self.moto, 8400))
        self.assertFalse(km_valido(self.moto, 9_000_000))


class ConfirmarKmVistaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moto = crear_moto(km_inicial=8000, km_actual=8000)
        hoy = date.today()
        LecturaKm.objects.create(moto=cls.moto, km=7000, fecha=hoy - timedelta(days=140))
        LecturaKm.objects.create(moto=cls.moto, km=8000, fecha=hoy - timedelta(days=40))
        cls.url = reverse("garaje:confirmar_km", args=[cls.moto.pk])

    def setUp(self):
        self.client.force_login(self.moto.motociclista.usuario)

    def test_la_ficha_muestra_la_pregunta_y_si_la_guarda(self):
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, "¿Vas por unos")
        self.client.post(self.url, {"accion": "si", "km": "8400"})
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 8400)
        self.assertTrue(self.moto.lecturas.filter(km=8400, estimada=True).exists())
        self.assertNotContains(self.client.get(self.moto.get_absolute_url()), "¿Vas por unos")

    def test_km_absurdo_se_rechaza(self):
        self.client.post(self.url, {"accion": "si", "km": "900000"})
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 8000)

    def test_ahora_no_la_pospone(self):
        self.client.post(self.url, {"accion": "despues"})
        self.assertNotContains(self.client.get(self.moto.get_absolute_url()), "¿Vas por unos")

    def test_otra_persona_no_puede(self):
        otra = crear_moto("z@x.com", "573001110009")
        self.client.force_login(otra.motociclista.usuario)
        self.assertEqual(self.client.post(self.url, {"accion": "si", "km": "8400"}).status_code, 404)
