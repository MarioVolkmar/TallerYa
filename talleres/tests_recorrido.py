"""Ajustes del recorrido de usuario: horario público desde la agenda y mínimo de la descripción."""
from datetime import time

from django.test import TestCase

from . import agenda
from .models import Barrio, Taller
from .views import _completitud


def _barrio():
    return Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]


class HorarioDesdeAgendaTests(TestCase):
    def test_texto_junta_dias_seguidos(self):
        turnos = [(d, time(8), time(18)) for d in range(5)] + [(5, time(8), time(14))]
        self.assertEqual(agenda.texto_horario(turnos), "Lun-Vie 8am-6pm · Sáb 8am-2pm")
        self.assertEqual(agenda.texto_horario([(0, time(7, 30), time(18, 30))]), "Lun 7:30am-6:30pm")
        self.assertEqual(agenda.texto_horario([(2, time(8), time(12)), (2, time(14), time(18))]), "Mié 8am-12pm y 2pm-6pm")

    def test_guardar_turnos_actualiza_el_horario_publico(self):
        t = Taller.objects.create(nombre="T", slug="t", horario="Lun-Sáb 8am-6pm", barrio=_barrio())
        agenda.guardar_turnos(t, [(d, time(9), time(17)) for d in range(3)])
        t.refresh_from_db()
        self.assertEqual(t.horario, "Lun-Mié 9am-5pm")


class CompletitudTests(TestCase):
    def test_descripcion_corta_dice_cuantos_caracteres_faltan(self):
        t = Taller.objects.create(nombre="T2", slug="t2", descripcion="Taller de prueba.", barrio=_barrio())
        faltan = _completitud(t)["faltan"]
        self.assertTrue(any(f.startswith("Descripción (mínimo 40 caracteres: te faltan 23)") for f in faltan), faltan)


class KmMenorTests(TestCase):
    class _Moto:
        km_actual = 9500

    def _form(self, **extra):
        from garaje.forms_servicio_taller import ServicioHechoForm
        from django.utils import timezone
        datos = {"otros": "Cambio de aceite", "km": "100", "fecha": timezone.localdate().isoformat(), **extra}
        return ServicioHechoForm(datos, moto=self._Moto())

    def test_km_menor_avisa_y_pide_confirmar(self):
        f = self._form()
        self.assertFalse(f.is_valid())
        self.assertIn("¿Es un servicio antiguo?", f.errors["km"][0])
        self.assertIn("km_antiguo", f.fields)

    def test_km_menor_confirmado_se_guarda(self):
        self.assertTrue(self._form(km_antiguo="on").is_valid())
