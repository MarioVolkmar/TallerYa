from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Suscripcion
from cupones.models import Motociclista
from garaje.models import Gasto, LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from garaje.utiles_pruebas import usar_intervalos_generales

from . import comprobante
from .balance import balance
from .intensivo import intervalo_intensivo, plan_intensivo
from .models import Jornada, PerfilDomiciliario

User = get_user_model()


class Base(TestCase):
    def setUp(self):
        usar_intervalos_generales(self)
        self.usuario = User.objects.create_user("andres@x.com", "andres@x.com", "x", first_name="Andrés")
        self.motero = Motociclista.objects.create(nombre="Andrés Gómez", celular="573001110000", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=self.motero, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                        modelo=2022, km_inicial=20000, km_actual=20000, placa="KLM45F")
        self.client.force_login(self.usuario)

    def perfil(self, **extra):
        return PerfilDomiciliario.objects.create(motociclista=self.motero, moto=self.moto, km_semana=1050, **extra)

    def plus(self):
        Suscripcion.objects.create(motociclista=self.motero).activar()


URLS_GET = ["domiciliarios:inicio", "domiciliarios:activar", "domiciliarios:panel"]
URLS_POST = ["domiciliarios:salir", "domiciliarios:jornada", "domiciliarios:plus", "domiciliarios:anular_comprobante"]


@override_settings(DOMICILIARIOS_ACTIVO=False)
class BanderaApagadaTests(Base):
    """Con la bandera apagada la página queda igual que antes: nada responde y no aparece ningún enlace."""

    def test_todas_las_urls_dan_404(self):
        perfil = self.perfil()
        self.plus()
        for nombre in URLS_GET:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 404, nombre)
        for nombre in URLS_POST:
            self.assertEqual(self.client.post(reverse(nombre), {"ingreso": 1000}).status_code, 404, nombre)
        token = comprobante.token(perfil)
        self.assertEqual(self.client.get(reverse("domiciliarios:comprobante", args=[token])).status_code, 404)
        self.assertFalse(Jornada.objects.exists())

    def test_mi_garaje_y_moto_no_muestran_nada(self):
        for url in (reverse("garaje:garaje") + "?lista=1", self.moto.get_absolute_url()):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, "data-dm-aviso")
            self.assertNotContains(r, "/domiciliarios/")
            self.assertNotContains(r, "dm.css")


@override_settings(DOMICILIARIOS_ACTIVO=True)
class PresentacionYActivarTests(Base):
    def test_presentacion_publica(self):
        self.client.logout()
        r = self.client.get(reverse("domiciliarios:inicio"))
        self.assertContains(r, "TallerYa Ruta")
        self.assertContains(r, "Crear cuenta gratis")

    def test_mi_garaje_invita(self):
        for url in (reverse("garaje:garaje") + "?lista=1", self.moto.get_absolute_url()):
            r = self.client.get(url)
            self.assertContains(r, "data-dm-aviso")
            self.assertContains(r, reverse("domiciliarios:inicio"))
        self.perfil()
        self.assertContains(self.client.get(self.moto.get_absolute_url()), reverse("domiciliarios:panel"))

    def test_activar_crea_perfil(self):
        r = self.client.post(reverse("domiciliarios:activar"),
                             {"moto": self.moto.pk, "plataformas": ["rappi", "didi"], "km_semana": 1200, "dias_semana": 6})
        self.assertRedirects(r, reverse("domiciliarios:panel"))
        p = PerfilDomiciliario.objects.get(motociclista=self.motero)
        self.assertEqual((p.km_semana, p.plataformas, p.moto), (1200, ["rappi", "didi"], self.moto))

    def test_no_puede_elegir_moto_ajena(self):
        otro = User.objects.create_user("o@x.com", "o@x.com", "x")
        m2 = Motociclista.objects.create(nombre="Otro", celular="573009990000", usuario=otro)
        ajena = Moto.objects.create(motociclista=m2, linea=self.moto.linea, modelo=2020, km_inicial=1, km_actual=1)
        r = self.client.post(reverse("domiciliarios:activar"), {"moto": ajena.pk, "km_semana": 1200, "dias_semana": 6})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(PerfilDomiciliario.objects.exists())

    def test_panel_pide_login_y_perfil(self):
        self.assertRedirects(self.client.get(reverse("domiciliarios:panel")), reverse("domiciliarios:activar"))
        self.client.logout()
        r = self.client.get(reverse("domiciliarios:panel"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("cuentas:entrar"), r["Location"])

    def test_salir_borra_perfil_y_pide_post(self):
        self.perfil()
        self.assertEqual(self.client.get(reverse("domiciliarios:salir")).status_code, 405)
        self.client.post(reverse("domiciliarios:salir"))
        self.assertFalse(PerfilDomiciliario.objects.exists())
        self.assertTrue(Moto.objects.filter(pk=self.moto.pk).exists())


@override_settings(DOMICILIARIOS_ACTIVO=True)
class JornadaTests(Base):
    def test_cierra_jornada_con_km_y_gasolina(self):
        p = self.perfil()
        r = self.client.post(reverse("domiciliarios:jornada"), {"ingreso": 95000, "km": 20180, "gasolina": 15000})
        self.assertEqual(r.status_code, 302)
        j = Jornada.objects.get(perfil=p)
        self.assertEqual((j.ingreso, j.km_fin), (95000, 20180))
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 20180)
        self.assertTrue(LecturaKm.objects.filter(moto=self.moto, km=20180).exists())
        self.assertEqual(Gasto.objects.get(moto=self.moto).valor, 15000)

    def test_segunda_vez_reemplaza_ingreso(self):
        p = self.perfil()
        self.client.post(reverse("domiciliarios:jornada"), {"ingreso": 50000})
        self.client.post(reverse("domiciliarios:jornada"), {"ingreso": 90000, "gasolina": 8000})
        self.assertEqual(list(p.jornadas.values_list("ingreso", flat=True)), [90000])
        self.assertEqual(Gasto.objects.count(), 1)

    def test_km_menor_se_rechaza(self):
        self.perfil()
        self.client.post(reverse("domiciliarios:jornada"), {"ingreso": 50000, "km": 19000})
        self.assertFalse(Jornada.objects.exists())
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 20000)

    def test_sin_perfil_no_guarda(self):
        r = self.client.post(reverse("domiciliarios:jornada"), {"ingreso": 50000})
        self.assertRedirects(r, reverse("domiciliarios:activar"), fetch_redirect_response=False)
        self.assertFalse(Jornada.objects.exists())

    def test_get_no_permitido(self):
        self.perfil()
        self.assertEqual(self.client.get(reverse("domiciliarios:jornada")).status_code, 405)

    def test_panel_muestra_todo(self):
        self.perfil()
        r = self.client.get(reverse("domiciliarios:panel"))
        self.assertContains(r, "Cerrar jornada")
        self.assertContains(r, "Plan de uso intensivo")
        self.assertContains(r, "Pico y placa")
        self.assertContains(r, "Plus domiciliario")  # sin Plus: la oferta
        self.assertNotContains(r, "Ver comprobante")


@override_settings(DOMICILIARIOS_ACTIVO=True)
class CalculosTests(Base):
    def test_intervalos_adelantados(self):
        self.assertEqual(intervalo_intensivo(2500, TareaMantenimiento.Pieza.ACEITE), 1800)
        self.assertIsNone(intervalo_intensivo(10000, TareaMantenimiento.Pieza.BUJIA))

    def test_plan_en_dias_con_km_semana(self):
        aceite = TareaMantenimiento.objects.filter(activo=True, pieza="aceite").order_by("orden").first()
        hoy = timezone.localdate()
        Mantenimiento.objects.create(moto=self.moto, tarea=aceite, km=20000, fecha=hoy)
        plan = plan_intensivo(self.moto, 1050, hoy)  # 150 km/día
        t = next(t for t in plan.tareas if t.tarea.pk == aceite.pk)
        self.assertEqual(t.intervalo_intensivo, intervalo_intensivo(aceite.intervalo_km, "aceite"))
        self.assertEqual(t.dias_para, round(t.intervalo_intensivo / 150))

    def test_balance(self):
        p = self.perfil()
        hoy = timezone.localdate()
        LecturaKm.objects.create(moto=self.moto, km=20000, fecha=hoy - timedelta(days=1))
        LecturaKm.objects.create(moto=self.moto, km=20200, fecha=hoy)
        Jornada.objects.create(perfil=p, fecha=hoy, ingreso=100000)
        Gasto.objects.create(moto=self.moto, fecha=hoy, valor=20000)
        b = balance(p, hoy)["semana"]
        self.assertEqual((b["ingreso"], b["gasto"], b["neto"], b["pct_gasto"]), (100000, 20000, 80000, 20))
        self.assertEqual((b["costo_km"], b["ganancia_km"]), (100, 500))


@override_settings(DOMICILIARIOS_ACTIVO=True)
class PlusYComprobanteTests(Base):
    def url(self, perfil):
        return reverse("domiciliarios:comprobante", args=[comprobante.token(perfil)])

    def test_solicitar_plus_reutiliza_suscripcion(self):
        self.perfil()
        self.client.post(reverse("domiciliarios:plus"))
        self.client.post(reverse("domiciliarios:plus"))
        s = Suscripcion.objects.get(motociclista=self.motero)
        self.assertEqual(s.estado, Suscripcion.Estado.SOLICITADA)
        self.assertIn("Plan domiciliario", s.notas)

    def test_comprobante_solo_con_plus(self):
        p = self.perfil()
        self.client.logout()
        self.assertEqual(self.client.get(self.url(p)).status_code, 404)
        self.plus()
        r = self.client.get(self.url(p))
        self.assertContains(r, "Comprobante TallerYa")
        self.assertContains(r, "KLM•••")
        self.assertNotContains(r, "KLM45F")  # placa oculta
        self.assertNotContains(r, "Gómez")  # solo el primer nombre
        self.assertEqual(r["X-Robots-Tag"], "noindex")

    def test_token_alterado_o_de_otro(self):
        p = self.perfil()
        self.plus()
        malo = comprobante.token(p)[:-2] + "xx"
        self.assertEqual(self.client.get(reverse("domiciliarios:comprobante", args=[malo])).status_code, 404)
        # Cambiar el id dentro del token sin firmarlo no sirve
        from django.core import signing
        falso = signing.dumps({"p": p.pk + 1, "v": 1}, salt="otra-sal", compress=True)
        self.assertEqual(self.client.get(reverse("domiciliarios:comprobante", args=[falso])).status_code, 404)

    def test_anular_invalida_enlaces_viejos(self):
        p = self.perfil()
        self.plus()
        viejo = self.url(p)
        self.client.post(reverse("domiciliarios:anular_comprobante"))
        self.assertEqual(self.client.get(viejo).status_code, 404)
        p.refresh_from_db()
        self.assertEqual(self.client.get(self.url(p)).status_code, 200)

    def test_panel_con_plus_muestra_comprobante_y_descuentos(self):
        self.perfil()
        self.plus()
        r = self.client.get(reverse("domiciliarios:panel"))
        self.assertContains(r, "Ver comprobante")
        self.assertNotContains(r, "Quiero Plus domiciliario")
