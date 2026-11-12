from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cupones.models import CodigoCupon, Cupon, Motociclista
from talleres.models import Barrio, Taller

from .models import Suscripcion

User = get_user_model()
CLAVE = "Moto-segura-2026"


def datos_registro(**extra):
    datos = {"nombre": "Laura", "email": "Laura@Correo.com", "celular": "300 555 1234",
             "password1": CLAVE, "password2": CLAVE}
    datos.update(extra)
    return datos


class RegistroYSesionTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registro_crea_usuario_y_motociclista(self):
        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertRedirects(r, reverse("cuentas:mi_cuenta"))
        u = User.objects.get()
        self.assertEqual(u.username, "laura@correo.com")
        self.assertEqual(u.motociclista.celular, "573005551234")

    def test_entrar_con_correo_sin_importar_mayusculas(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        r = self.client.post(reverse("cuentas:entrar"), {"username": "LAURA@correo.com", "password": CLAVE})
        self.assertRedirects(r, reverse("cuentas:mi_cuenta"))

    def test_next_externo_se_ignora(self):
        r = self.client.post(reverse("cuentas:registro") + "?next=https://malo.example/", datos_registro())
        self.assertRedirects(r, reverse("cuentas:mi_cuenta"))

    def test_celular_con_cupones_requiere_uno_de_sus_codigos(self):
        moto = Motociclista.objects.create(nombre="Laura", celular="573005551234")
        cupon = Cupon.objects.create(titulo="Lavado gratis")
        codigo = CodigoCupon.objects.create(cupon=cupon, motociclista=moto)

        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertContains(r, "Escribe uno de sus códigos")
        self.assertFalse(User.objects.exists())

        r = self.client.post(reverse("cuentas:registro"), datos_registro(codigo_existente=codigo.codigo.lower()))
        self.assertEqual(r.status_code, 302)
        moto.refresh_from_db()
        self.assertEqual(moto.usuario.email, "laura@correo.com")

    def test_celular_ya_vinculado_a_otra_cuenta(self):
        otro = User.objects.create_user("otro@correo.com", "otro@correo.com", CLAVE)
        Motociclista.objects.create(nombre="Otro", celular="573005551234", usuario=otro)
        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertContains(r, "ya está asociado a otra cuenta")

    def test_recuperar_contrasena_envia_correo(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        self.client.post(reverse("cuentas:recuperar"), {"email": "laura@correo.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/cuenta/recuperar/", mail.outbox[0].body)

    def test_cupon_con_celular_de_cuenta_pide_iniciar_sesion(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        cupon = Cupon.objects.create(titulo="Lavado gratis")
        r = self.client.post(reverse("cupones:obtener", args=[cupon.pk]), {"nombre": "X", "celular": "3005551234"})
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))
        self.assertFalse(CodigoCupon.objects.exists())


class PlusTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.moto = Motociclista.objects.get()
        barrio = Barrio.objects.create(nombre="Belén")
        self.taller = Taller.objects.create(nombre="Taller A", responsable="Ana", whatsapp="573001234567",
                                            direccion="Cra 1", barrio=barrio, activo=True)
        self.exclusivo = Cupon.objects.create(taller=self.taller, titulo="25% exclusivo", solo_plus=True)
        self.regalo = Cupon.objects.create(titulo="Regalo del mes", regalo_mensual=True)

    def test_solicitar_y_activar_plus(self):
        self.client.post(reverse("cuentas:solicitar_plus"))
        self.client.post(reverse("cuentas:solicitar_plus"))  # no duplica
        s = Suscripcion.objects.get()
        self.assertEqual(s.estado, Suscripcion.Estado.SOLICITADA)
        self.assertFalse(self.moto.es_plus)
        s.activar()
        self.assertTrue(self.moto.es_plus)
        self.assertEqual(s.vence, timezone.localdate() + timedelta(days=30))

    def test_renovar_suma_dias_al_vencimiento(self):
        s = Suscripcion.objects.create(motociclista=self.moto)
        s.activar()
        nueva = Suscripcion.objects.create(motociclista=self.moto)
        nueva.activar()
        s.refresh_from_db()
        self.assertEqual(s.estado, Suscripcion.Estado.CANCELADA)
        self.assertEqual(nueva.vence, timezone.localdate() + timedelta(days=60))

    def test_cupon_exclusivo_requiere_plus(self):
        r = self.client.post(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertRedirects(r, reverse("cuentas:plus"))
        self.assertFalse(CodigoCupon.objects.exists())

        Suscripcion.objects.create(motociclista=self.moto).activar()
        r = self.client.post(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertEqual(CodigoCupon.objects.get().cupon, self.exclusivo)

    def test_cupon_exclusivo_sin_sesion_pide_entrar(self):
        self.client.logout()
        r = self.client.get(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_regalo_mensual_una_vez_por_mes_y_solo_plus(self):
        self.client.post(reverse("cuentas:reclamar_regalo"))
        self.assertFalse(CodigoCupon.objects.exists())

        Suscripcion.objects.create(motociclista=self.moto).activar()
        self.client.post(reverse("cuentas:reclamar_regalo"))
        self.client.post(reverse("cuentas:reclamar_regalo"))
        codigo = CodigoCupon.objects.get()
        self.assertEqual(codigo.origen, CodigoCupon.Origen.REGALO)

    def test_regalo_no_aparece_en_la_lista_publica(self):
        self.assertNotContains(self.client.get(reverse("cupones:lista")), "Regalo del mes")

    def test_pagina_plus_muestra_precio(self):
        r = self.client.get(reverse("cuentas:plus"))
        self.assertContains(r, "9.900")
