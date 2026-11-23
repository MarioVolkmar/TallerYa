"""Coordenadas del taller desde su dirección: todo con el geocodificador simulado (sin red)."""
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from . import geocodificar
from .models import Barrio, Taller


def _taller(**kw):
    barrio, _ = Barrio.objects.get_or_create(nombre="Laureles", ciudad="Medellín")
    datos = dict(nombre="Geo Taller", responsable="Ana", whatsapp="573001112233", direccion="Calle 10 # 5-5", barrio=barrio)
    return Taller.objects.create(**{**datos, **kw})


@override_settings(GEOCODIFICAR_ACTIVO=True)
class GeocodificarTests(TestCase):
    def test_direccion_encontrada_es_exacta(self):
        with mock.patch.object(geocodificar, "_consultar", return_value=(6.2442, -75.5812)) as m:
            t = _taller()
        t.refresh_from_db()
        self.assertEqual((t.latitud, t.longitud, t.ubicacion_exacta), (Decimal("6.244200"), Decimal("-75.581200"), True))
        self.assertIn("Calle 10 # 5-5", m.call_args_list[0][0][0])

    def test_sin_la_direccion_usa_el_barrio_y_queda_aproximada(self):
        with mock.patch.object(geocodificar, "_consultar", side_effect=[None, (6.25, -75.59)]):
            t = _taller()
        t.refresh_from_db()
        self.assertEqual((float(t.latitud), t.ubicacion_exacta), (6.25, False))

    def test_sin_resultados_ni_red_el_taller_se_guarda_igual(self):
        with mock.patch.object(geocodificar, "_consultar", return_value=None):
            t = _taller()
        self.assertIsNone(t.latitud)

    def test_cambiar_la_direccion_recalcula_pero_el_gps_manda(self):
        with mock.patch.object(geocodificar, "_consultar", return_value=(6.20, -75.57)):
            t = _taller()
            t.direccion = "Carrera 70 # 1-1"
            t.save()
        t.refresh_from_db()
        self.assertEqual(float(t.latitud), 6.20)
        with mock.patch.object(geocodificar, "_consultar", return_value=(6.30, -75.50)):
            t.latitud, t.longitud = Decimal("6.244203"), Decimal("-75.581212")  # tomada con el GPS
            t.direccion = "Otra calle"
            t.save()
        t.refresh_from_db()
        self.assertEqual((str(t.latitud), t.ubicacion_exacta), ("6.244203", True))

    def test_resultado_fuera_del_valle_se_descarta(self):
        with mock.patch("urllib.request.urlopen") as u, mock.patch.object(geocodificar.cache, "get", return_value=None), \
                mock.patch.object(geocodificar.cache, "set"):
            u.return_value.__enter__.return_value = StringIO('[{"lat": "4.60", "lon": "-74.08"}]')
            self.assertIsNone(geocodificar._consultar("Bogotá"))

    def test_comando_completa_los_talleres_sin_ubicacion(self):
        with override_settings(GEOCODIFICAR_ACTIVO=False):
            t = _taller()
        self.assertIsNone(t.latitud)
        with mock.patch.object(geocodificar, "_consultar", return_value=(6.2, -75.6)), mock.patch("time.sleep"):
            call_command("completar_coordenadas", stdout=StringIO())
        t.refresh_from_db()
        self.assertEqual((float(t.latitud), t.ubicacion_exacta), (6.2, True))

    def test_editar_perfil_muestra_estado_de_ubicacion_y_horario(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        u = get_user_model().objects.create_user(username="geo", email="geo@x.co", password="x12345678")
        with mock.patch.object(geocodificar, "_consultar", return_value=None):
            t = _taller(usuario=u)
        self.client.force_login(u)
        r = self.client.get(reverse("talleres:editar_perfil"))
        self.assertContains(r, "Sin ubicación")
        Taller.objects.filter(pk=t.pk).update(latitud=Decimal("6.2"), longitud=Decimal("-75.6"), ubicacion_exacta=False)
        self.assertContains(self.client.get(reverse("talleres:editar_perfil")), "Aproximada por tu dirección")
        Taller.objects.filter(pk=t.pk).update(ubicacion_exacta=True)
        r = self.client.get(reverse("talleres:editar_perfil"))
        self.assertContains(r, "Exacta ✓")
        self.assertContains(r, "Cambiar horario")
        self.assertNotContains(r, 'name="horario"')

    def test_panel_avisa_si_falta_la_ubicacion(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        u = get_user_model().objects.create_user(username="geo2", email="geo2@x.co", password="x12345678")
        with mock.patch.object(geocodificar, "_consultar", return_value=None):
            t = _taller(usuario=u, nombre="Sin Geo")
        self.client.force_login(u)
        self.assertContains(self.client.get(reverse("talleres:panel")), "Confirma la ubicación exacta de tu taller")
        Taller.objects.filter(pk=t.pk).update(latitud=Decimal("6.2"), longitud=Decimal("-75.6"), ubicacion_exacta=True)
        self.assertNotContains(self.client.get(reverse("talleres:panel")), "Confirma la ubicación exacta de tu taller")
