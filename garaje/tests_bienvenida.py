from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas import guia
from cuentas.models import Perfil
from cupones.models import Motociclista

from .models import LineaMoto, Moto

User = get_user_model()


class GuiaBienvenidaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("lia@x.com", "lia@x.com", "Clave-segura-2026", first_name="Lía")
        self.motero = Motociclista.objects.create(nombre="Lía", celular="573001110000", usuario=self.usuario)
        self.client.force_login(self.usuario)
        self.nkd = LineaMoto.objects.get(nombre="NKD 125")

    def test_arranque_lleva_al_formulario_en_modo_guia(self):
        r = self.client.get(reverse("garaje:bienvenida"))
        self.assertRedirects(r, reverse("garaje:agregar") + "?guia=1")
        r = self.client.get(reverse("garaje:agregar") + "?guia=1")
        self.assertContains(r, "Empecemos por tu")
        self.assertContains(r, "Saltar guía")
        self.assertContains(r, 'aria-current="step"')
        self.assertNotContains(r, "doc-tarjeta")  # los papeles se dejan para el paso 4

    def test_recorrido_completo(self):
        r = self.client.post(reverse("garaje:agregar") + "?guia=1", {
            "linea_catalogo": str(self.nkd.pk), "modelo": 2021, "color": "#c62828", "km_actual": 12000})
        moto = Moto.objects.get()
        self.assertRedirects(r, reverse("garaje:bienvenida_plan", args=[moto.pk]))
        r = self.client.get(reverse("garaje:bienvenida_plan", args=[moto.pk]))
        self.assertContains(r, "ya está en el garaje")
        self.assertContains(r, reverse("garaje:vista_3d", args=[moto.pk]))
        self.assertContains(r, "sin registro")
        self.assertTrue(guia.pendiente(self.usuario) is False)  # ya tiene moto
        self.assertIsNone(Perfil.de(self.usuario).guia_terminada)
        r = self.client.get(reverse("garaje:bienvenida_listo", args=[moto.pk]))
        for texto in ("SOAT", "Talleres", "Foro y rodadas", f"?marca={self.nkd.marca_id}"):
            self.assertContains(r, texto)
        self.assertNotContains(r, "Saltar guía")
        self.assertIsNotNone(Perfil.objects.get(usuario=self.usuario).guia_terminada)

    def test_con_hace_poco_sale_lo_que_viene_o_lo_urgente(self):
        filas = self.client.get(reverse("garaje:tareas_alta"), {"linea": self.nkd.pk, "km": 12000}).content.decode()
        import re
        ids = set(re.findall(r'name="estado_(\d+)"', filas))
        datos = {"linea_catalogo": str(self.nkd.pk), "modelo": 2021, "color": "#c62828", "km_actual": 12000, "guardar": "1"}
        datos.update({f"estado_{i}": "poco" for i in ids})
        self.client.post(reverse("garaje:agregar") + "?guia=1", datos)
        moto = Moto.objects.get()
        self.assertEqual(moto.mantenimientos.count(), len(ids))
        r = self.client.get(reverse("garaje:bienvenida_plan", args=[moto.pk]))
        self.assertRegex(r.content.decode(), "Todo al día|Lo urgente")

    def test_saltar_no_vuelve_a_salir(self):
        r = self.client.post(reverse("garaje:bienvenida_saltar"))
        self.assertRedirects(r, reverse("talleres:inicio"), fetch_redirect_response=False)
        self.assertFalse(guia.pendiente(self.usuario))
        self.client.logout()
        r = self.client.post(reverse("cuentas:entrar"), {"username": "lia@x.com", "password": "Clave-segura-2026"})
        self.assertRedirects(r, reverse("talleres:inicio"), fetch_redirect_response=False)

    def test_entrar_sin_motos_lleva_a_la_guia_y_respeta_next(self):
        self.client.logout()
        datos = {"username": "lia@x.com", "password": "Clave-segura-2026"}
        r = self.client.post(reverse("cuentas:entrar"), datos)
        self.assertRedirects(r, reverse("garaje:bienvenida"), fetch_redirect_response=False)
        self.client.logout()
        r = self.client.post(reverse("cuentas:entrar") + "?next=/foro/", datos)
        self.assertRedirects(r, "/foro/", fetch_redirect_response=False)

    def test_con_motos_no_sale(self):
        Moto.objects.create(motociclista=self.motero, linea=self.nkd, modelo=2020, km_inicial=0, km_actual=0)
        self.assertFalse(guia.pendiente(self.usuario))

    def test_no_ve_el_plan_de_otra_moto(self):
        otro = Motociclista.objects.create(nombre="Otro", celular="573009990000")
        ajena = Moto.objects.create(motociclista=otro, linea=self.nkd, modelo=2020, km_inicial=0, km_actual=0)
        self.assertEqual(self.client.get(reverse("garaje:bienvenida_plan", args=[ajena.pk])).status_code, 404)
