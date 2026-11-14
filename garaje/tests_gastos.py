"""Pruebas de gastos y consumo: km/galón entre tanqueos llenos, costo por km, mes, tipo y la hoja de vida sin duplicar."""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .gastos import rendimiento, resumen
from .models import Gasto, RegistroServicio
from .tests_avisos import crear_moto

HOY = date(2026, 11, 14)


class GastosTests(TestCase):
    def setUp(self):
        self.moto = crear_moto(km_inicial=1000, km_actual=1500)

    def tanqueo(self, km, galones, lleno=True, valor=30000, fecha=HOY):
        return Gasto.objects.create(moto=self.moto, tipo="tanqueo", km=km, galones=Decimal(galones),
                                    tanque_lleno=lleno, valor=valor, fecha=fecha)

    def test_km_por_galon_entre_tanqueos_llenos(self):
        self.tanqueo(1000, "2")         # arranque: lleno
        self.tanqueo(1100, "1", False)  # parcial: suma galones
        self.tanqueo(1300, "2")         # 300 km / 3 gal = 100
        self.tanqueo(1500, "2.5")       # 200 / 2.5 = 80
        r = rendimiento(self.moto.gastos.all())
        self.assertEqual([t["km_galon"] for t in r["tramos"]], [100.0, 80.0])
        self.assertEqual(r["promedio"], 90.9)  # 500 km / 5.5 gal
        self.assertEqual(r["ultimo"], 80.0)

    def test_tanqueo_sin_galones_rompe_la_cadena(self):
        self.tanqueo(1000, "2")
        Gasto.objects.create(moto=self.moto, tipo="tanqueo", km=1100, valor=10000)
        self.tanqueo(1300, "2")
        self.assertEqual(rendimiento(self.moto.gastos.all())["tramos"], [])

    def test_resumen_mes_tipo_y_hoja_de_vida_sin_duplicar(self):
        self.tanqueo(1000, "2", valor=30000)
        self.tanqueo(1500, "2.5", valor=40000)
        Gasto.objects.create(moto=self.moto, tipo="soat", valor=200000, fecha=date(2026, 9, 1))
        RegistroServicio.objects.create(moto=self.moto, km=1400, servicios="Aceite", costo=50000, fecha=HOY)
        RegistroServicio.objects.create(moto=self.moto, km=1450, servicios="Sin costo", fecha=HOY)
        r = resumen(self.moto, HOY)
        self.assertEqual(r["total"], 320000)
        self.assertEqual(r["mes_total"], 120000)
        self.assertEqual({t["clave"]: t["total"] for t in r["tipos"]}, {"soat": 200000, "tanqueo": 70000, "servicio": 50000})
        self.assertEqual(len(r["movimientos"]), 4)  # el servicio sin costo no cuenta
        self.assertEqual(r["costo_km"], 640)  # 320.000 / 500 km
        self.assertEqual(r["combustible_km"], 80)  # 40.000 / 500 km del tramo
        self.assertEqual([s["etiqueta"] for s in r["serie"]], ["jun", "jul", "ago", "sep", "oct", "nov"])
        self.assertEqual(max(s["alto"] for s in r["serie"]), 100)

    def test_pagina_registrar_y_borrar(self):
        self.client.force_login(self.moto.motociclista.usuario)
        url = reverse("garaje:gastos", args=[self.moto.pk])
        r = self.client.post(url, {"tipo": "tanqueo", "fecha": "2026-11-01", "valor": 28000, "galones": "1.9",
                                   "km": 1600, "tanque_lleno": "on"})
        self.assertRedirects(r, url)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 1600)
        # Un repuesto no guarda galones aunque lleguen
        self.client.post(url, {"tipo": "repuesto", "fecha": "2026-11-02", "valor": 15000, "galones": "3"})
        self.assertIsNone(Gasto.objects.get(tipo="repuesto").galones)
        pagina = self.client.get(url)
        self.assertContains(pagina, "gs-barras")
        self.assertContains(pagina, "$43.000")
        gasto = Gasto.objects.get(tipo="repuesto")
        self.client.post(url, {"accion": "eliminar", "gasto": gasto.pk})
        self.assertFalse(Gasto.objects.filter(pk=gasto.pk).exists())

    def test_valida_valores(self):
        self.client.force_login(self.moto.motociclista.usuario)
        r = self.client.post(reverse("garaje:gastos", args=[self.moto.pk]),
                             {"tipo": "tanqueo", "fecha": "2099-01-01", "valor": 1000, "galones": "50"})
        self.assertContains(r, "no puede ser futura")
        self.assertContains(r, "galones")
        self.assertFalse(Gasto.objects.exists())

    def test_ficha_enlaza_hoja_gastos_y_diagnostico(self):
        self.client.force_login(self.moto.motociclista.usuario)
        r = self.client.get(self.moto.get_absolute_url())
        for url in (reverse("garaje:hoja_vida", args=[self.moto.pk]), reverse("garaje:gastos", args=[self.moto.pk]),
                    f"{reverse('garaje:diagnostico')}?moto={self.moto.pk}"):
            self.assertContains(r, f'href="{url}"')

    def test_gastos_ajenos_no_se_ven(self):
        otra = crear_moto("b@x.com", "573009")
        self.client.force_login(self.moto.motociclista.usuario)
        self.assertEqual(self.client.get(reverse("garaje:gastos", args=[otra.pk])).status_code, 404)
