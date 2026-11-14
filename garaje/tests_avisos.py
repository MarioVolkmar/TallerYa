"""Pruebas de los avisos de pico y placa y vencimientos (franja de Mi garaje, notificaciones y comando)."""
from datetime import date, timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from notificaciones.models import Notificacion

from .avisos import avisos_moto, notificar_moto, umbral
from .models import Moto, ReglaPicoPlaca

LUNES = date(2026, 11, 9)  # lunes sin festivo; rotación 2026-2: lunes 5 y 8


def crear_moto(correo="ana@x.com", celular="573001110000", **campos):
    usuario = get_user_model().objects.create_user(correo, correo, "x")
    perfil = Motociclista.objects.create(nombre="Ana", celular=celular, usuario=usuario)
    datos = {"marca_otra": "Yamaha", "linea_otra": "NMAX", "tipo_otra": "scooter", "modelo": 2022,
             "km_inicial": 1000, "km_actual": 5000, **campos}
    return Moto.objects.create(motociclista=perfil, **datos)


class AvisosTests(TestCase):
    def test_umbrales(self):
        self.assertEqual([umbral(d) for d in (40, 30, 20, 15, 10, 3, 0)], [None, 30, 30, 15, 15, 3, 3])

    def test_regla_2026_2_cargada_con_fin_por_verificar(self):
        regla = ReglaPicoPlaca.objects.get(ciudad="Medellín", vigente_desde=date(2026, 8, 3))
        self.assertEqual(regla.vigente_hasta, date(2027, 1, 29))
        self.assertTrue(regla.fin_por_verificar)
        self.assertEqual((regla.lunes, regla.viernes), ("5,8", "7,9"))

    def test_pico_y_placa_hoy_y_soat(self):
        moto = crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=12))
        titulos = [a["titulo"] for a in avisos_moto(moto, LUNES)]
        self.assertEqual(titulos, ["Hoy tienes pico y placa", "Tu SOAT vence en 12 días"])
        self.assertEqual(avisos_moto(moto, LUNES + timedelta(days=1))[0]["titulo"], "Tu SOAT vence en 11 días")

    def test_tecno_por_matricula(self):
        moto = crear_moto(matricula=date(2024, 11, 20))  # primera revisión: 20/11/2026
        aviso = avisos_moto(moto, LUNES)[0]
        self.assertEqual(aviso["titulo"], "Tu técnico-mecánica vence en 11 días")
        self.assertIn("matrícula", aviso["texto"])
        # Si la primera ya pasó, no inventamos una fecha.
        self.assertEqual(avisos_moto(crear_moto("b@x.com", "573002", matricula=date(2020, 1, 1)), LUNES), [])

    def test_notificaciones_30_15_3_sin_repetir(self):
        vence = LUNES + timedelta(days=30)
        moto = crear_moto(soat_vence=vence)
        creadas = []
        for faltan in (30, 29, 15, 14, 3, 2, 0, -1, -5):
            creadas.append(notificar_moto(moto, vence - timedelta(days=faltan)))
        self.assertEqual(creadas, [1, 0, 1, 0, 1, 0, 0, 1, 0])
        self.assertEqual(Notificacion.objects.filter(clave__startswith=f"doc:{moto.pk}:soat").count(), 4)

    def test_pico_y_placa_respeta_preferencia(self):
        moto = crear_moto(placa="ABC58D", aviso_pico_placa=False)
        self.assertEqual(notificar_moto(moto, LUNES), 0)
        moto.aviso_pico_placa = True
        self.assertEqual(notificar_moto(moto, LUNES), 1)
        self.assertEqual(notificar_moto(moto, LUNES), 0)

    def test_comando_idempotente(self):
        crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=3))
        for esperado in ("Avisos nuevos: 2", "Avisos nuevos: 0"):
            salida = StringIO()
            call_command("avisar_vencimientos", "--fecha", LUNES.isoformat(), stdout=salida)
            self.assertIn(esperado, salida.getvalue())

    def test_franja_en_mi_garaje(self):
        moto = crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=5))
        crear_otra = Moto.objects.create(motociclista=moto.motociclista, marca_otra="Honda", linea_otra="CB",
                                         tipo_otra="calle", modelo=2020, km_inicial=0, km_actual=0)
        self.client.force_login(moto.motociclista.usuario)
        with mock.patch("django.utils.timezone.localdate", return_value=LUNES):
            lista = self.client.get(reverse("garaje:garaje") + "?lista=1")
            ficha = self.client.get(crear_otra.get_absolute_url())
            propia = self.client.get(moto.get_absolute_url())
        self.assertContains(propia, "Hoy tienes pico y placa")
        self.assertContains(propia, "(por verificar)")
        self.assertContains(lista, "Hoy tienes pico y placa")
        self.assertContains(lista, "Tu SOAT vence en 5 días")
        self.assertNotContains(ficha, "avisos-hoy")  # la otra moto no tiene avisos

    def test_matricula_no_futura(self):
        moto = crear_moto()
        self.client.force_login(moto.motociclista.usuario)
        r = self.client.post(reverse("garaje:editar", args=[moto.pk]), {
            "linea_catalogo": "otra", "marca_otra": "Yamaha", "linea_otra": "NMAX", "tipo_otra": "scooter",
            "modelo": 2022, "matricula": "2099-01-01"})
        self.assertContains(r, "no puede ser futura")
