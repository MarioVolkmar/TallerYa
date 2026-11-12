from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from talleres.models import Barrio, Taller

from .models import CodigoCupon, Cupon, Motociclista


class CuponesTests(TestCase):
    def setUp(self):
        cache.clear()
        barrio = Barrio.objects.create(nombre="Belén")
        self.taller = Taller.objects.create(nombre="Taller A", responsable="Ana", whatsapp="573001234567",
                                            direccion="Cra 1", barrio=barrio, activo=True)
        self.otro = Taller.objects.create(nombre="Taller B", responsable="Beto", whatsapp="573007654321",
                                          direccion="Cra 2", barrio=barrio, activo=True)
        self.cupon = Cupon.objects.create(taller=self.taller, titulo="15% en aceite")
        self.premio = Cupon.objects.create(titulo="$20.000 de premio", publico=False, premio_referido=True)

    def obtener(self, cupon=None, celular="300 111 2233", nombre="Juan"):
        cupon = cupon or self.cupon
        return self.client.post(reverse("cupones:obtener", args=[cupon.pk]), {"nombre": nombre, "celular": celular})

    def canjear(self, codigo, pin=None):
        return self.client.post(reverse("cupones:canjear"), {"codigo": codigo, "pin": pin or self.taller.pin_canje})

    # --- Obtener ---

    def test_taller_recibe_pin_unico(self):
        self.assertRegex(self.taller.pin_canje, r"^\d{6}$")
        self.assertNotEqual(self.taller.pin_canje, self.otro.pin_canje)

    def test_obtener_crea_codigo_y_normaliza_celular(self):
        r = self.obtener()
        codigo = CodigoCupon.objects.get()
        self.assertRedirects(r, codigo.get_absolute_url())
        self.assertRegex(codigo.codigo, r"^TY-[A-Z2-9]{6}$")
        self.assertEqual(codigo.motociclista.celular, "573001112233")

    def test_obtener_dos_veces_devuelve_el_mismo_codigo(self):
        self.obtener()
        self.obtener(celular="3001112233")
        self.assertEqual(CodigoCupon.objects.count(), 1)
        self.assertEqual(Motociclista.objects.count(), 1)

    def test_cupo_agotado(self):
        self.cupon.cupo = 1
        self.cupon.save()
        self.obtener()
        r = self.obtener(celular="3009998877")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(CodigoCupon.objects.count(), 1)

    def test_cupon_vencido_no_se_lista_ni_se_obtiene(self):
        self.cupon.valido_hasta = timezone.localdate() - timedelta(days=1)
        self.cupon.save()
        self.assertNotContains(self.client.get(reverse("cupones:lista")), "15% en aceite")
        self.assertEqual(self.obtener().status_code, 404)

    def test_cupon_de_premio_no_es_publico(self):
        self.assertNotContains(self.client.get(reverse("cupones:lista")), "$20.000 de premio")
        self.assertEqual(self.obtener(cupon=self.premio).status_code, 404)

    def test_perfil_del_taller_muestra_sus_cupones(self):
        r = self.client.get(self.taller.get_absolute_url())
        self.assertContains(r, "15% en aceite")
        self.assertNotContains(self.client.get(self.otro.get_absolute_url()), "15% en aceite")

    # --- Canjear ---

    def test_canje_exitoso_y_no_se_repite(self):
        self.obtener()
        codigo = CodigoCupon.objects.get()
        r = self.canjear(codigo.codigo.lower().replace("-", ""))  # tolera minúsculas y sin guion
        self.assertContains(r, "Canje exitoso")
        codigo.refresh_from_db()
        self.assertTrue(codigo.canjeado)
        self.assertEqual(codigo.canjeado_taller, self.taller)
        self.assertContains(self.canjear(codigo.codigo), "ya fue canjeado")

    def test_canje_con_pin_incorrecto_o_de_otro_taller(self):
        self.obtener()
        codigo = CodigoCupon.objects.get()
        self.assertContains(self.canjear(codigo.codigo, pin="000000" if self.taller.pin_canje != "000000" else "111111"), "PIN incorrecto")
        self.assertContains(self.canjear(codigo.codigo, pin=self.otro.pin_canje), "es de otro taller")
        codigo.refresh_from_db()
        self.assertFalse(codigo.canjeado)

    def test_cupon_general_vale_en_cualquier_taller(self):
        general = Cupon.objects.create(titulo="Lavado gratis")
        self.obtener(cupon=general)
        codigo = CodigoCupon.objects.get()
        self.assertContains(self.canjear(codigo.codigo, pin=self.otro.pin_canje), "Canje exitoso")

    def test_bloqueo_tras_intentos_fallidos(self):
        self.obtener()
        codigo = CodigoCupon.objects.get()
        for _ in range(8):
            self.canjear("TY-NOEXIS")
        r = self.canjear(codigo.codigo)
        self.assertContains(r, "Demasiados intentos")
        codigo.refresh_from_db()
        self.assertFalse(codigo.canjeado)

    # --- Referidos ---

    def test_referido_gana_premio_cuando_amigo_canjea(self):
        self.obtener(celular="3001112233", nombre="Juan")
        juan = Motociclista.objects.get(celular="573001112233")

        amigo = self.client_class()
        amigo.get(reverse("cupones:referido", args=[juan.codigo_referido]))
        amigo.post(reverse("cupones:obtener", args=[self.cupon.pk]), {"nombre": "Pedro", "celular": "3004445566"})
        pedro = Motociclista.objects.get(celular="573004445566")
        self.assertEqual(pedro.referido_por, juan)

        self.canjear(pedro.codigos.get().codigo)
        premio = juan.codigos.get(origen=CodigoCupon.Origen.PREMIO)
        self.assertEqual(premio.cupon, self.premio)
        self.assertEqual(premio.referido, pedro)

        # Un segundo canje de Pedro no genera otro premio
        otro_cupon = Cupon.objects.create(taller=self.taller, titulo="Frenos gratis")
        amigo.post(reverse("cupones:obtener", args=[otro_cupon.pk]), {"nombre": "Pedro", "celular": "3004445566"})
        self.canjear(pedro.codigos.get(cupon=otro_cupon).codigo)
        self.assertEqual(juan.codigos.filter(origen=CodigoCupon.Origen.PREMIO).count(), 1)

    def test_motociclista_existente_no_se_reasigna_como_referido(self):
        self.obtener(celular="3001112233", nombre="Juan")
        self.obtener(celular="3004445566", nombre="Pedro")
        juan = Motociclista.objects.get(celular="573001112233")
        self.client.get(reverse("cupones:referido", args=[juan.codigo_referido]))
        otro_cupon = Cupon.objects.create(taller=self.taller, titulo="Frenos gratis")
        self.obtener(cupon=otro_cupon, celular="3004445566", nombre="Pedro")
        self.assertIsNone(Motociclista.objects.get(celular="573004445566").referido_por)

    def test_pagina_del_codigo_muestra_enlace_de_referido(self):
        self.obtener()
        codigo = CodigoCupon.objects.get()
        r = self.client.get(codigo.get_absolute_url())
        self.assertContains(r, codigo.codigo)
        self.assertContains(r, reverse("cupones:referido", args=[codigo.motociclista.codigo_referido]))
        self.assertNotContains(r, "3001112233")  # el celular se muestra oculto
