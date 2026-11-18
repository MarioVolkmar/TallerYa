import io
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import agregacion, nucleo
from .models import ActividadSemanal, Evento, ResumenDiario, SalDiaria

User = get_user_model()
CELULAR = "Mozilla/5.0 (Linux; Android 14; SM-A145M) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"
ESCRITORIO = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
IP = "181.50.77.123"


@override_settings(METRICAS_ACTIVAS=True)
class MedicionTests(TestCase):
    def get(self, url, ua=ESCRITORIO, **extra):
        return self.client.get(url, HTTP_USER_AGENT=ua, REMOTE_ADDR=IP, **extra)

    def test_registra_la_vista_por_nombre_de_ruta(self):
        self.get(reverse("talleres:directorio"), ua=CELULAR, HTTP_REFERER="https://www.google.com.co/")
        e = Evento.objects.get()
        self.assertEqual((e.tipo, e.nombre, e.dispositivo, e.referente), ("v", "talleres:directorio", "c", "google"))
        self.assertEqual(e.dia, timezone.localdate())

    def test_referentes_agrupados(self):
        for ref, grupo in [("", "directo"), ("https://l.facebook.com/x", "redes"), ("https://web.whatsapp.com/", "whatsapp"),
                           ("https://duckduckgo.com/", "buscadores"), ("http://testserver/talleres/", "interno"),
                           ("https://ejemplo.org/", "otros")]:
            self.get("/", HTTP_REFERER=ref)
            self.assertEqual(Evento.objects.latest("id").referente, grupo, ref)

    def test_no_guarda_la_ip_en_claro_y_el_hash_cambia_cada_dia(self):
        self.get("/")
        e = Evento.objects.get()
        crudo = str(Evento.objects.values().get())
        self.assertNotIn(IP, crudo)
        self.assertNotIn("181.50", crudo)
        self.assertEqual(len(e.visitante), 16)
        # mismo visitante el mismo día → mismo código; otro día → otra sal y otro código
        self.get("/")
        self.assertEqual(Evento.objects.values("visitante").distinct().count(), 1)
        manana = timezone.localdate() + timedelta(days=1)
        otro, _ = nucleo.visitante(_peticion(), manana)
        self.assertNotEqual(otro, e.visitante)
        self.assertFalse(SalDiaria.objects.filter(dia__lt=manana).exists())  # la sal de ayer ya no existe

    def test_respeta_dnt_y_gpc(self):
        self.get("/", HTTP_DNT="1")
        self.get("/", HTTP_SEC_GPC="1")
        self.assertFalse(Evento.objects.exists())

    def test_excluye_estaticos_bots_admin_y_panel(self):
        self.get("/static/metricas/metricas.js")
        self.get("/admin/login/")
        self.get("/consola/")
        self.get("/", ua="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
        self.get("/", ua="WhatsApp/2.23.20.0 A")
        self.get("/", ua="")
        self.get("/no-existe-esta-pagina/")
        self.assertFalse(Evento.objects.exists())

    def test_no_cuenta_al_equipo_administrador(self):
        admin = User.objects.create_user("a@t.co", "a@t.co", "x", is_staff=True)
        self.client.force_login(admin)
        self.get("/")
        self.assertFalse(Evento.objects.exists())

    def test_con_sesion_usa_el_id_interno(self):
        u = User.objects.create_user("m@t.co", "m@t.co", "x")
        self.client.force_login(u)
        self.get("/")
        e = Evento.objects.get()
        self.assertEqual((e.visitante, e.usuario_id), (f"u{u.pk}", u.pk))

    @override_settings(METRICAS_ACTIVAS=False)
    def test_bandera_apagada_no_registra_nada(self):
        self.get("/")
        self.assertFalse(nucleo.registrar_evento(_peticion(), "contacto"))
        r = self.client.post(reverse("metricas:evento"), {"nombre": "visor_3d"}, HTTP_USER_AGENT=ESCRITORIO)
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Evento.objects.exists())

    def test_registrar_evento_descarta_datos_personales(self):
        nucleo.registrar_evento(_peticion(), "contacto", canal="whatsapp", celular="3001234567", correo="x@y.co",
                                nombre="Ana", taller=7)
        self.assertEqual(Evento.objects.get().datos, {"canal": "whatsapp", "taller": 7})

    def test_termino_de_busqueda_sin_datos_personales(self):
        self.assertEqual(nucleo.termino_busqueda("  Cambio   de ACEITE "), "cambio de aceite")
        for malo in ("3001234567", "ana@correo.co", "https://x.co"):
            self.assertEqual(nucleo.termino_busqueda(malo), "")

    def test_busqueda_de_talleres(self):
        self.get(reverse("talleres:directorio") + "?q=Frenos")
        self.assertEqual(Evento.objects.get(nombre="busqueda_talleres").datos["q"], "frenos")

    def test_endpoint_del_navegador_con_csrf_y_lista_blanca(self):
        from django.test import Client
        estricto = Client(enforce_csrf_checks=True)
        r = estricto.post(reverse("metricas:evento"), {"nombre": "visor_3d"}, HTTP_USER_AGENT=ESCRITORIO)
        self.assertEqual(r.status_code, 403)
        r = self.client.post(reverse("metricas:evento"), {"nombre": "borrar_todo"}, HTTP_USER_AGENT=ESCRITORIO)
        self.assertEqual(r.status_code, 400)
        r = self.client.post(reverse("metricas:evento"), '{"nombre": "pieza_vista", "datos": {"ref": 12}}',
                             content_type="application/json", HTTP_USER_AGENT=ESCRITORIO)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Evento.objects.get().datos, {"ref": 12})

    def test_registro_cuenta_registro_y_no_inicio_de_sesion(self):
        from django.contrib.auth import login
        r = _peticion()
        u = User.objects.create_user("n@t.co", "n@t.co", "x")
        nucleo.registrar_evento(r, "registro", metodo="correo")
        r.session = self.client.session
        login(r, u, backend="django.contrib.auth.backends.ModelBackend")
        self.assertTrue(r._metricas_registro)
        self.assertEqual(list(Evento.objects.values_list("nombre", flat=True)), ["registro"])

    def test_inicio_de_sesion_con_correo(self):
        User.objects.create_user("e@t.co", "e@t.co", "clave-segura-123")
        self.client.post(reverse("cuentas:entrar"), {"username": "e@t.co", "password": "clave-segura-123"},
                         HTTP_USER_AGENT=ESCRITORIO, REMOTE_ADDR=IP)
        e = Evento.objects.get(nombre="inicio_sesion")
        self.assertEqual(e.datos, {"metodo": "correo"})
        self.assertIsNotNone(e.usuario_id)

    def test_middleware_cuesta_pocos_ms(self):
        """Promedio del costo de medir una página (hash + INSERT). En SQLite en memoria ronda 0,3-1 ms."""
        r = _peticion()
        nucleo.guardar(r, Evento.VISTA, "calentar")
        n = 200
        inicio = time.perf_counter()
        for _ in range(n):
            nucleo.guardar(r, Evento.VISTA, "talleres:inicio")
        ms = (time.perf_counter() - inicio) * 1000 / n
        self.assertLess(ms, 5, f"medir una página costó {ms:.2f} ms")


def _peticion(**extra):
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory
    r = RequestFactory().get("/", HTTP_USER_AGENT=ESCRITORIO, REMOTE_ADDR=IP, **extra)
    r.user = AnonymousUser()
    return r


@override_settings(METRICAS_ACTIVAS=True)
class AgregacionTests(TestCase):
    def crear(self, dia, nombre="talleres:inicio", tipo="v", visitante="a", usuario_id=None, **kw):
        return Evento.objects.create(dia=dia, tipo=tipo, nombre=nombre, visitante=visitante, usuario_id=usuario_id, **kw)

    def test_agrega_por_dia_y_purga_lo_crudo_de_mas_de_90_dias(self):
        hoy = timezone.localdate()
        viejo, ayer = hoy - timedelta(days=95), hoy - timedelta(days=1)
        self.crear(viejo, visitante="a")
        self.crear(viejo, visitante="b", dispositivo="c", referente="google")
        self.crear(ayer, visitante="u5", usuario_id=5)
        self.crear(ayer, tipo="e", nombre="contacto", visitante="u5", usuario_id=5)
        self.crear(ayer, tipo="e", nombre="busqueda_talleres", visitante="x", datos={"q": "frenos"})
        self.crear(hoy)
        call_command("agregar_metricas", stdout=io.StringIO())
        # lo crudo viejo se borró; ayer y hoy siguen
        self.assertFalse(Evento.objects.filter(dia=viejo).exists())
        self.assertEqual(Evento.objects.filter(dia__gte=ayer).count(), 4)
        # pero sus conteos quedaron
        v = ResumenDiario.objects.get(dia=viejo, clave="vista", valor="talleres:inicio")
        self.assertEqual((v.total, v.unicos), (2, 2))
        self.assertEqual(ResumenDiario.objects.get(dia=viejo, clave="referente", valor="google").unicos, 1)
        self.assertEqual(ResumenDiario.objects.get(dia=ayer, clave="evento", valor="contacto").total, 1)
        self.assertEqual(ResumenDiario.objects.get(dia=ayer, clave="busqueda", valor="frenos").total, 1)
        self.assertEqual(ResumenDiario.objects.get(dia=ayer, clave="activos", valor="dia").unicos, 1)
        self.assertTrue(ActividadSemanal.objects.filter(usuario_id=5, semana=agregacion.lunes(ayer)).exists())
        self.assertFalse(ResumenDiario.objects.filter(dia=hoy).exists())  # hoy no está cerrado
        # idempotente
        antes = ResumenDiario.objects.count()
        call_command("agregar_metricas", stdout=io.StringIO())
        self.assertEqual(ResumenDiario.objects.count(), antes)


@override_settings(METRICAS_ACTIVAS=True)
class PanelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin@t.co", "admin@t.co", "x", is_staff=True)
        cls.motero = User.objects.create_user("m@t.co", "m@t.co", "x")
        hoy = timezone.localdate()
        for i in range(3):
            Evento.objects.create(dia=hoy - timedelta(days=i), tipo="v", nombre="talleres:inicio", visitante=f"v{i}")
        Evento.objects.create(dia=hoy, tipo="e", nombre="registro", visitante=f"u{cls.motero.pk}", usuario_id=cls.motero.pk)
        Evento.objects.create(dia=hoy, tipo="e", nombre="moto_creada", visitante=f"u{cls.motero.pk}", usuario_id=cls.motero.pk)

    def test_solo_el_administrador_ve_el_panel_y_el_csv(self):
        url = reverse("consola:inicio") + "?seccion=metricas"
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.get(reverse("metricas:exportar")).status_code, 302)
        self.client.force_login(self.motero)
        self.assertIn(self.client.get(url).status_code, (302, 403))
        self.assertIn(self.client.get(reverse("metricas:exportar")).status_code, (302, 403))
        self.client.force_login(self.admin)
        r = self.client.get(url + "&periodo=7")
        self.assertContains(r, "Métricas de uso")
        self.assertContains(r, "<svg", html=False)
        self.assertContains(r, "Crearon una moto")
        csv = self.client.get(reverse("metricas:exportar") + "?periodo=90")
        self.assertEqual(csv["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("talleres:inicio", csv.content.decode("utf-8-sig"))
