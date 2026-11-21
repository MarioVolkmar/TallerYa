"""Piloto, paso 1: interruptor que oculta foro/Plus/referidos, botón de WhatsApp con mensaje y reporte en la consola."""
from datetime import date
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from cupones.models import Motociclista
from garaje.models import Moto
from talleres.models import Barrio, EventoDiario, Servicio, Taller

User = get_user_model()
NAV = {"HTTP_USER_AGENT": "Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile"}


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.taller = Taller.objects.create(nombre="Taller Uno", responsable="A", whatsapp="573001112233", direccion="X",
                                           barrio=cls.barrio, activo=True)
        cls.otro = Taller.objects.create(nombre="Taller Dos", responsable="B", whatsapp="573001112244", direccion="X",
                                         barrio=cls.barrio, activo=True)
        cls.servicio = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        cls.taller.servicios.add(cls.servicio)
        cls.admin = User.objects.create_user("a@t.co", "a@t.co", "clave-segura-123", is_staff=True)


@override_settings(PILOTO_OCULTAR_SOCIAL=True)
class OcultarSocialTests(Base):
    def test_urls_de_foro_plus_y_referidos_dan_404(self):
        for url in ("/foro/", "/foro/rodadas/", "/plus/", "/r/ABC123/", "/cuenta/regalo/"):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_menu_portada_y_pie_sin_foro_ni_plus(self):
        for url in ("/", "/talleres/"):
            html = self.client.get(url).content.decode()
            self.assertNotIn('href="/foro/', html, url)
            self.assertNotIn('href="/plus/', html, url)

    def test_sin_el_interruptor_siguen_funcionando(self):
        with override_settings(PILOTO_OCULTAR_SOCIAL=False):
            self.assertEqual(self.client.get("/foro/").status_code, 200)
            self.assertEqual(self.client.get("/plus/").status_code, 200)
            self.assertContains(self.client.get("/"), 'href="/foro/')

    def test_mi_cuenta_sin_preguntas_plus_ni_invita(self):
        u = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123", first_name="Mario")
        m = Motociclista.objects.create(nombre="Mario", celular="573009998877", usuario=u)
        Moto.objects.create(motociclista=m, marca_otra="Yamaha", linea_otra="NMAX", tipo_otra="scooter", modelo=2022, km_inicial=0, km_actual=0)
        self.client.force_login(u)
        html = self.client.get(reverse("cuentas:mi_cuenta")).content.decode()
        for malo in ("Mis preguntas", "TallerYa Plus", "Invita y gana", "/foro/", "/plus/"):
            self.assertNotIn(malo, html)


class WhatsAppConMensajeTests(Base):
    def _texto(self, r):
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("https://wa.me/573001112233?text="))
        return unquote(r["Location"].split("text=", 1)[1])

    def test_mensaje_basico(self):
        t = self._texto(self.client.get(reverse("talleres:ir_whatsapp", args=[self.taller.slug]), **NAV))
        self.assertEqual(t, "Hola Taller Uno, te encontré en TallerYa.")

    def test_con_moto_del_usuario_y_servicio(self):
        u = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123")
        m = Motociclista.objects.create(nombre="Mario", celular="573009998877", usuario=u)
        Moto.objects.create(motociclista=m, marca_otra="Yamaha", linea_otra="NMAX", tipo_otra="scooter", modelo=2022, km_inicial=0, km_actual=0)
        self.client.force_login(u)
        r = self.client.get(reverse("talleres:ir_whatsapp", args=[self.taller.slug]) + f"?servicio={self.servicio.pk}", **NAV)
        t = self._texto(r)
        self.assertIn("te encontré en TallerYa", t)
        self.assertIn("NMAX", t)
        self.assertIn("necesito: cambio de aceite", t)

    def test_servicio_ajeno_se_ignora_y_el_clic_se_mide(self):
        r = self.client.get(reverse("talleres:ir_whatsapp", args=[self.otro.slug]) + f"?servicio={self.servicio.pk}", **NAV)
        self.assertNotIn("necesito", unquote(r["Location"]))
        self.assertEqual(EventoDiario.objects.get(taller=self.otro, tipo="whatsapp").cantidad, 1)

    def test_el_perfil_trae_el_boton_medido(self):
        self.assertContains(self.client.get(self.taller.get_absolute_url() + f"?servicio={self.servicio.pk}"),
                            reverse("talleres:ir_whatsapp", args=[self.taller.slug]) + f"?servicio={self.servicio.pk}")


class ReporteConsolaTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        hoy = date.today()
        for tipo, n in (("visita", 7), ("whatsapp", 3), ("llamada", 2)):
            EventoDiario.objects.create(taller=cls.taller, fecha=hoy, tipo=tipo, cantidad=n)
        EventoDiario.objects.create(taller=cls.taller, fecha=date(2020, 1, 5), tipo="visita", cantidad=99)

    def test_reporte_del_mes_por_taller(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("consola:inicio") + "?seccion=reportes")
        self.assertEqual(r.status_code, 200)
        filas = {f["taller"].nombre: f for f in r.context["filas"]}
        self.assertEqual((filas["Taller Uno"]["vistas"], filas["Taller Uno"]["whatsapp"], filas["Taller Uno"]["llamadas"]), (7, 3, 2))
        self.assertEqual(filas["Taller Dos"]["vistas"], 0)
        self.assertEqual(r.context["total"]["vistas"], 7)

    def test_mes_invalido_cae_en_el_actual_y_exige_admin(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("consola:inicio") + "?seccion=reportes&mes=zzz").status_code, 200)
        self.client.logout()
        self.assertNotEqual(self.client.get(reverse("consola:inicio") + "?seccion=reportes").status_code, 200)


class MostrarPreciosTests(Base):
    def _con_precio(self, **extra):
        from talleres.models import PrecioServicio
        Taller.objects.filter(pk=self.taller.pk).update(**extra)
        PrecioServicio.objects.create(taller=self.taller, servicio=self.servicio, cilindraje="baja", desde=38000, hasta=60000)
        return self.client.get(self.taller.get_absolute_url())

    def test_apagado_por_defecto_cotiza_por_whatsapp_sin_precios(self):
        self.assertFalse(Taller.objects.get(pk=self.taller.pk).mostrar_precios)
        r = self._con_precio()
        self.assertContains(r, "Cotiza por WhatsApp")
        self.assertNotContains(r, "$38.000")
        self.assertEqual(r.context["tabla_precios"]["filas"], [])
        self.assertContains(r, "Cambio de aceite")  # el servicio sigue como chip para pedir cita

    def test_encendido_muestra_solo_mano_de_obra(self):
        r = self._con_precio(mostrar_precios=True)
        self.assertContains(r, "$38.000")
        self.assertContains(r, "Solo mano de obra, sin repuestos")
        self.assertNotContains(r, "repuestos típicos")
        self.assertNotContains(r, "Cotiza por WhatsApp")

    def test_consola_lo_activa_y_el_taller_lo_edita(self):
        self.client.force_login(self.admin)
        url = reverse("consola:accion", args=["talleres.precios", self.taller.pk])
        self.client.post(url, {"valor": "1"})
        self.assertTrue(Taller.objects.get(pk=self.taller.pk).mostrar_precios)
        self.client.post(url, {"valor": "0"})
        self.assertFalse(Taller.objects.get(pk=self.taller.pk).mostrar_precios)
        from talleres.forms import PerfilTallerForm
        self.assertIn("mostrar_precios", PerfilTallerForm().fields)
