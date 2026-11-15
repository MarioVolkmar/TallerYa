"""Pruebas de gastos: categorías, galones estimados, km por lecturas, costo por km y hoja de vida sin duplicar."""
from datetime import date, timedelta
from importlib import import_module

from django.apps import apps as apps_reales
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import combustible
from .gastos import CATEGORIAS, km_periodo, resumen
from .models import Gasto, LecturaKm, RegistroServicio
from .tests_avisos import crear_moto

HOY = date(2026, 11, 14)


class GastosTests(TestCase):
    def setUp(self):
        self.moto = crear_moto(km_inicial=1000, km_actual=1500)
        # La moto se "registró" en septiembre con 1000 km
        type(self.moto).objects.filter(pk=self.moto.pk).update(
            creado=timezone.make_aware(timezone.datetime(2026, 9, 1, 12)))
        self.moto.refresh_from_db()

    def test_categorias_en_un_solo_lugar(self):
        self.assertEqual(len(CATEGORIAS), 12)
        self.assertEqual(set(CATEGORIAS), {c for c, _ in Gasto.Tipo.choices})
        self.assertTrue(all(c["color"].startswith("#") and c["icono"] for c in CATEGORIAS.values()))

    def test_migracion_pasa_tanqueo_a_gasolina(self):
        migracion = import_module("garaje.migrations.0019_categorias_gasto")
        g = Gasto.objects.create(moto=self.moto, tipo="gasolina", valor=1000)
        Gasto.objects.filter(pk=g.pk).update(tipo="tanqueo")
        migracion.mapear(apps_reales, None)
        g.refresh_from_db()
        self.assertEqual(g.tipo, "gasolina")

    def test_km_por_lecturas(self):
        self.assertIsNone(km_periodo(self.moto, date(2026, 11, 1), HOY))  # sin lecturas en noviembre
        LecturaKm.objects.create(moto=self.moto, km=1300, fecha=date(2026, 10, 25))
        LecturaKm.objects.create(moto=self.moto, km=1500, fecha=date(2026, 11, 10))
        self.assertEqual(km_periodo(self.moto, date(2026, 11, 1), HOY), 200)   # 1500 − 1300 (última antes)
        self.assertEqual(km_periodo(self.moto, date(2026, 10, 1), date(2026, 10, 31)), 300)  # desde el registro

    def test_resumen_del_mes_galones_estimados_y_hoja_de_vida(self):
        LecturaKm.objects.create(moto=self.moto, km=1300, fecha=date(2026, 10, 25))
        LecturaKm.objects.create(moto=self.moto, km=1500, fecha=date(2026, 11, 10))
        precio = combustible.PRECIO_GALON_CORRIENTE
        Gasto.objects.create(moto=self.moto, tipo="gasolina", valor=precio * 2, fecha=date(2026, 11, 3))
        Gasto.objects.create(moto=self.moto, tipo="lavada", valor=15000, fecha=date(2026, 11, 4))
        Gasto.objects.create(moto=self.moto, tipo="soat", valor=200000, fecha=date(2026, 9, 1))
        RegistroServicio.objects.create(moto=self.moto, km=1400, servicios="Aceite", costo=50000, fecha=HOY)
        RegistroServicio.objects.create(moto=self.moto, km=1450, servicios="Sin costo", fecha=HOY)
        r = resumen(self.moto, HOY)
        mes = precio * 2 + 15000 + 50000
        self.assertEqual(r["mes_total"], mes)
        self.assertEqual(r["total"], mes + 200000)
        self.assertEqual(len(r["movimientos"]), 4)  # el servicio sin costo no cuenta
        self.assertEqual({c["clave"]: c["total"] for c in r["categorias"]},
                         {"soat": 200000, "gasolina": precio * 2, "servicio": 50000, "lavada": 15000})
        self.assertEqual(r["km_mes"], 200)
        self.assertEqual(r["costo_km"], round(mes / 200))
        self.assertEqual(r["km_galon"], 100.0)  # 200 km / 2 gal estimados
        gasolina = next(m for m in r["movimientos"] if m.tipo == "gasolina")
        self.assertEqual(gasolina.galones_texto, "≈ 2,0 gal estimados")
        self.assertEqual(max(s["alto"] for s in r["serie"]), 100)

    def test_pagina_formulario_simple_y_tarjetas(self):
        self.client.force_login(self.moto.motociclista.usuario)
        url = reverse("garaje:gastos", args=[self.moto.pk])
        pagina = self.client.get(url)
        for campo in ('name="galones"', 'name="tanque_lleno"', 'name="km"'):
            self.assertNotContains(pagina, campo)
        self.assertContains(pagina, "Registra el kilometraje para calcularlo")
        self.assertContains(pagina, f'{self.moto.get_absolute_url()}#form-km')
        self.assertContains(pagina, 'class="gs-hv"')
        r = self.client.post(url, {"tipo": "gasolina", "valor": 32502, "fecha": timezone.localdate().isoformat()})
        self.assertRedirects(r, url)
        pagina = self.client.get(url)
        self.assertContains(pagina, "≈ 2,0 gal estimados")
        self.assertContains(pagina, "$32.502")
        gasto = Gasto.objects.get()
        self.client.post(url, {"accion": "eliminar", "gasto": gasto.pk})
        self.assertFalse(Gasto.objects.exists())

    def test_valida_valores(self):
        self.client.force_login(self.moto.motociclista.usuario)
        r = self.client.post(reverse("garaje:gastos", args=[self.moto.pk]),
                             {"tipo": "multa", "fecha": "2099-01-01", "valor": ""})
        self.assertContains(r, "no puede ser futura")
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

    def test_detalle_del_movimiento_y_editar(self):
        from talleres.models import Barrio, Taller
        from django.contrib.auth import get_user_model
        self.client.force_login(self.moto.motociclista.usuario)
        url = reverse("garaje:gastos", args=[self.moto.pk])
        LecturaKm.objects.create(moto=self.moto, km=1300, fecha=date(2026, 10, 25))
        g = Gasto.objects.create(moto=self.moto, tipo="lavada", valor=15000, fecha=date(2026, 11, 1), notas="Lavadero 80")
        taller = Taller.objects.create(nombre="Garaje 70", responsable="X", whatsapp="573001112233", direccion="Cl 1",
                                       barrio=Barrio.objects.get_or_create(nombre="Belén")[0], activo=True,
                                       usuario=get_user_model().objects.create_user("t@x.com", "t@x.com", "x"))
        r = RegistroServicio.objects.create(moto=self.moto, km=1400, servicios="Frenos", costo=70000, taller=taller,
                                            fecha=date(2026, 11, 2))
        RegistroServicio.objects.filter(pk=r.pk).update(verificado=True)
        pagina = self.client.get(url)
        self.assertContains(pagina, 'class="gs-fila"', count=2)
        self.assertNotContains(pagina, 'class="gs-borrar"')  # el × salió de la fila: eliminar está en el detalle
        self.assertContains(pagina, f'href="?editar={g.pk}#agregar"')
        self.assertContains(pagina, "≈ 1.300 km")  # km aproximado de esa fecha según las lecturas
        self.assertContains(pagina, "Hecho en Garaje 70 · verificado")
        self.assertContains(pagina, "Ver en la hoja de vida")
        # Editar: el formulario carga el gasto y lo actualiza (no crea otro)
        self.assertContains(self.client.get(url, {"editar": g.pk}), "Editar gasto")
        self.client.post(url, {"gasto": g.pk, "tipo": "lavada", "valor": 18000, "fecha": "2026-11-01", "notas": ""})
        g.refresh_from_db()
        self.assertEqual((Gasto.objects.count(), g.valor), (1, 18000))
