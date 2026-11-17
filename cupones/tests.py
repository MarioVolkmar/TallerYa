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
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        self.taller = Taller.objects.create(nombre="Taller A", responsable="Ana", whatsapp="573001234567",
                                            direccion="Cra 1", barrio=barrio, activo=True)
        self.otro = Taller.objects.create(nombre="Taller B", responsable="Beto", whatsapp="573007654321",
                                          direccion="Cra 2", barrio=barrio, activo=True)
        self.cupon = Cupon.objects.create(taller=self.taller, titulo="15% en aceite")
        self.premio = Cupon.objects.create(titulo="$20.000 de premio", publico=False, premio_referido=True)
        self.pin, self.pin_otro = self.taller.nuevo_pin(), self.otro.nuevo_pin()

    def obtener(self, cupon=None, celular="300 111 2233", nombre="Juan"):
        cupon = cupon or self.cupon
        return self.client.post(reverse("cupones:obtener", args=[cupon.pk]), {"nombre": nombre, "celular": celular})

    def canjear(self, codigo, pin=None, taller=None):
        """Sin sesión: el taller elegido en el formulario y su PIN."""
        taller = taller or self.taller
        pin = pin or (self.pin if taller == self.taller else self.pin_otro)
        return self.client.post(reverse("cupones:canjear"), {"codigo": codigo, "pin": pin, "taller": taller.slug})

    # --- Obtener ---

    def test_pin_se_guarda_con_hash_y_solo_vale_para_su_taller(self):
        self.assertRegex(self.pin, r"^\d{6}$")
        self.taller.refresh_from_db()
        self.assertNotIn(self.pin, self.taller.pin_hash)
        self.assertTrue(self.taller.pin_correcto(self.pin))
        self.assertFalse(self.otro.pin_correcto(self.pin) and self.pin != self.pin_otro)
        viejo = self.pin
        self.pin = self.taller.nuevo_pin()
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.pin_correcto(self.pin))
        if viejo != self.pin:
            self.assertFalse(self.taller.pin_correcto(viejo))

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
        self.assertContains(r, "Cupón validado")
        codigo.refresh_from_db()
        self.assertTrue(codigo.canjeado)
        self.assertEqual(codigo.canjeado_taller, self.taller)
        self.assertContains(self.canjear(codigo.codigo), "no se volvió a marcar")  # reenvío: idempotente
        general = Cupon.objects.create(titulo="Lavado gratis")
        self.obtener(cupon=general)
        otro_codigo = CodigoCupon.objects.get(cupon=general)
        self.canjear(otro_codigo.codigo)
        self.assertContains(self.canjear(otro_codigo.codigo, taller=self.otro), "ya se usó")

    def test_canje_con_pin_incorrecto_o_de_otro_taller(self):
        self.obtener()
        codigo = CodigoCupon.objects.get()
        malo = "000000" if self.pin != "000000" else "111111"
        self.assertContains(self.canjear(codigo.codigo, pin=malo), "El código o el PIN no son correctos")
        # El PIN de otro taller no sirve para este taller (nunca se busca el taller por el PIN)
        if self.pin_otro != self.pin:
            self.assertContains(self.canjear(codigo.codigo, pin=self.pin_otro), "El código o el PIN no son correctos")
        self.assertContains(self.canjear(codigo.codigo, taller=self.otro), "es de otro taller")
        codigo.refresh_from_db()
        self.assertFalse(codigo.canjeado)

    def test_cupon_general_vale_en_cualquier_taller(self):
        general = Cupon.objects.create(titulo="Lavado gratis")
        self.obtener(cupon=general)
        codigo = CodigoCupon.objects.get()
        self.assertContains(self.canjear(codigo.codigo, taller=self.otro), "Cupón validado")

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


class CanjeConQRTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from talleres.models import Barrio, Taller
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        self.duenio = get_user_model().objects.create_user("qr@t.co", "qr@t.co", "x")
        self.taller = Taller.objects.create(nombre="QR Taller", responsable="A", whatsapp="573001112233", direccion="X",
                                            barrio=barrio, activo=True, usuario=self.duenio)
        cupon = Cupon.objects.create(taller=self.taller, titulo="10% en frenos")
        moto = Motociclista.objects.create(nombre="Pedro", celular="573009998877")
        self.codigo = CodigoCupon.objects.create(cupon=cupon, motociclista=moto)

    def test_el_cupon_trae_qr_con_la_direccion_de_canje(self):
        r = self.client.get(self.codigo.get_absolute_url())
        self.assertContains(r, f"/canjear/?codigo={self.codigo.codigo}")

    def test_taller_con_sesion_ve_vista_previa_y_canjea_sin_pin(self):
        self.client.force_login(self.duenio)
        r = self.client.get(reverse("cupones:canjear"), {"codigo": self.codigo.codigo})
        self.assertContains(r, "Cupón vigente")
        r = self.client.post(reverse("cupones:canjear"), {"codigo": self.codigo.codigo})
        self.assertContains(r, "Cupón validado")
        self.codigo.refresh_from_db()
        self.assertEqual(self.codigo.canjeado_taller, self.taller)

    def test_sin_sesion_sigue_pidiendo_pin(self):
        r = self.client.post(reverse("cupones:canjear"), {"codigo": self.codigo.codigo})
        self.assertContains(r, "PIN de tu taller")

