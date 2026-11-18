import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas import roles
from talleres.models import Barrio, Taller

from . import demo
from .estados import cambiar_estado
from .models import MecanicoDomicilio, ResenaMecanico, TipoServicio, Zona

User = get_user_model()


def jpg():
    from PIL import Image
    salida = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 80, 20)).save(salida, "JPEG")
    return SimpleUploadedFile("yo.jpg", salida.getvalue(), content_type="image/jpeg")


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Zonas y servicios los siembra la migración 0002
        cls.robledo = Zona.objects.get(nombre="Robledo")
        cls.envigado = Zona.objects.get(nombre="Envigado")
        cls.frenos = TipoServicio.objects.get(nombre="Frenos")
        cls.llantas = TipoServicio.objects.get(nombre="Llantas y despinche")
        cls.dueno = User.objects.create_user("mec@prueba.com", "mec@prueba.com", "clave-segura-123", first_name="Wil")
        cls.otro = User.objects.create_user("otro@prueba.com", "otro@prueba.com", "clave-segura-123", first_name="Ana")
        cls.aprobado = cls.crear("Wilson Frenos", zona=cls.robledo, servicio=cls.frenos, usuario=cls.dueno)
        cls.pendiente = cls.crear("Pepe Pendiente", estado=MecanicoDomicilio.Estado.PENDIENTE)
        cls.suspendido = cls.crear("Sergio Suspendido", estado=MecanicoDomicilio.Estado.SUSPENDIDO)
        cls.envigadeno = cls.crear("Yeison Llantas", zona=cls.envigado, servicio=cls.llantas, urgencias=True)

    @classmethod
    def crear(cls, nombre, zona=None, servicio=None, estado=MecanicoDomicilio.Estado.APROBADO, **extra):
        m = MecanicoDomicilio.objects.create(nombre=nombre, whatsapp="573000000999", estado=estado, **extra)
        m.zonas.add(zona or cls.robledo)
        m.servicios.add(servicio or cls.frenos)
        return m

    def setUp(self):
        cache.clear()  # los límites de frecuencia viven en la caché


class ListadoTests(Base):
    def nombres(self, **params):
        r = self.client.get(reverse("domicilio:listado"), params)
        self.assertEqual(r.status_code, 200)
        return {m.nombre for m in r.context["pagina"]}

    def test_solo_aprobados(self):
        self.assertEqual(self.nombres(), {"Wilson Frenos", "Yeison Llantas"})

    def test_filtro_zona_y_servicio(self):
        self.assertEqual(self.nombres(zona=self.envigado.pk), {"Yeison Llantas"})
        self.assertEqual(self.nombres(servicio=self.frenos.pk), {"Wilson Frenos"})
        self.assertEqual(self.nombres(zona=self.envigado.pk, servicio=self.frenos.pk), set())

    def test_busqueda_y_urgencias(self):
        self.assertEqual(self.nombres(q="despinche"), {"Yeison Llantas"})  # por nombre del servicio
        self.assertEqual(self.nombres(q="wilson"), {"Wilson Frenos"})
        self.assertEqual(self.nombres(urgencias="1"), {"Yeison Llantas"})
        self.assertEqual(self.nombres(zona="no-numero"), {"Wilson Frenos", "Yeison Llantas"})  # se ignora

    def test_aviso_y_whatsapp(self):
        r = self.client.get(reverse("domicilio:listado"))
        self.assertContains(r, "TallerYa solo los promociona")
        self.assertContains(r, "https://wa.me/573000000999")


class FichaTests(Base):
    def test_publica_aprobado(self):
        r = self.client.get(self.aprobado.get_absolute_url())
        self.assertContains(r, "Wilson Frenos")
        self.assertContains(r, "el pago y la garantía")
        self.assertContains(r, "https://wa.me/573000000999?text=")

    def test_no_aprobados_404_salvo_dueno_y_staff(self):
        for m in (self.pendiente, self.suspendido):
            self.assertEqual(self.client.get(m.get_absolute_url()).status_code, 404)
        self.pendiente.usuario = self.otro
        self.pendiente.save()
        self.client.force_login(self.otro)
        self.assertContains(self.client.get(self.pendiente.get_absolute_url()), "en revisión")
        staff = User.objects.create_user("staff@prueba.com", password="x", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.suspendido.get_absolute_url()).status_code, 200)

    def test_resena_requiere_cuenta(self):
        url = self.aprobado.get_absolute_url()
        r = self.client.post(url, {"estrellas": 5, "comentario": "Bien"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("cuentas:entrar"), r["Location"])
        self.assertFalse(ResenaMecanico.objects.exists())

    def test_resena_una_por_cuenta_y_se_actualiza(self):
        self.client.force_login(self.otro)
        url = self.aprobado.get_absolute_url()
        self.client.post(url, {"estrellas": 5, "comentario": "Llegó rápido"})
        self.client.post(url, {"estrellas": 3, "comentario": "Cambio de opinión"})
        r = ResenaMecanico.objects.get()
        self.assertEqual((r.estrellas, r.nombre, r.usuario), (3, "Ana", self.otro))
        self.assertContains(self.client.get(url), "Cambio de opinión")

    def test_no_se_califica_a_si_mismo_ni_a_no_publicados(self):
        self.client.force_login(self.dueno)
        self.client.post(self.aprobado.get_absolute_url(), {"estrellas": 5, "comentario": "Soy el mejor"})
        self.pendiente.usuario = self.otro
        self.pendiente.save()
        staff = User.objects.create_user("staff@prueba.com", password="x", is_staff=True)
        self.client.force_login(staff)
        self.client.post(self.pendiente.get_absolute_url(), {"estrellas": 1, "comentario": "x"})
        self.assertFalse(ResenaMecanico.objects.exists())

    def test_limite_de_resenas(self):
        self.client.force_login(self.otro)
        url = self.aprobado.get_absolute_url()
        for i in range(5):
            self.client.post(url, {"estrellas": 4, "comentario": f"Intento {i}"})
        self.assertEqual(ResenaMecanico.objects.get().comentario, "Intento 2")  # 3 por hora; el resto se frena


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RegistroYEdicionTests(Base):
    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def datos(self, **extra):
        return {"nombre": "Carlos Nuevo", "whatsapp": "300 123 4567", "zonas": [self.robledo.pk],
                "servicios": [self.frenos.pk], "anios_experiencia": 7, "horario": "Lun-Sáb", "tarifa_visita": 30000,
                "descripcion": "Voy a domicilio.", **extra}

    def test_registro_con_cuenta_nueva_queda_pendiente(self):
        datos = self.datos(**{"cuenta-email": "Nuevo@Prueba.com", "cuenta-password1": "una-clave-larga-9",
                              "cuenta-password2": "una-clave-larga-9", "cuenta-acepto": "on"})
        datos["foto"] = jpg()
        r = self.client.post(reverse("domicilio:registro"), datos)
        self.assertRedirects(r, reverse("domicilio:mi_perfil"))
        m = MecanicoDomicilio.objects.get(nombre="Carlos Nuevo")
        self.assertEqual((m.estado, m.verificado, m.whatsapp, m.usuario.email),
                         ("pendiente", False, "573001234567", "nuevo@prueba.com"))
        self.assertTrue(m.foto.name.startswith("domicilio/") and m.foto.name.endswith(".jpg"))
        self.assertEqual(roles.rol_de(User.objects.get(pk=m.usuario_id)), roles.MECANICO)
        listado = self.client.get(reverse("domicilio:listado")).context["pagina"]
        self.assertNotIn("Carlos Nuevo", {x.nombre for x in listado})

    def test_no_puede_ponerse_aprobado_ni_verificado(self):
        self.client.force_login(self.otro)
        self.client.post(reverse("domicilio:registro"), self.datos(estado="aprobado", verificado="on"))
        m = MecanicoDomicilio.objects.get(usuario=self.otro)
        self.assertEqual((m.estado, m.verificado), ("pendiente", False))

    def test_foto_falsa_se_rechaza(self):
        self.client.force_login(self.otro)
        falsa = SimpleUploadedFile("x.jpg", b"<html><script>alert(1)</script></html>", content_type="image/jpeg")
        r = self.client.post(reverse("domicilio:registro"), self.datos(foto=falsa))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(MecanicoDomicilio.objects.filter(usuario=self.otro).exists())

    def test_taller_no_se_registra_como_mecanico(self):
        barrio = Barrio.objects.get_or_create(nombre="Centro", ciudad="Medellín")[0]
        Taller.objects.create(nombre="T", responsable="R", whatsapp="573000000000", direccion="C", barrio=barrio,
                              usuario=self.otro)
        self.client.force_login(self.otro)
        self.client.post(reverse("domicilio:registro"), self.datos())
        self.assertFalse(MecanicoDomicilio.objects.filter(usuario=self.otro).exists())

    def test_con_perfil_registro_lleva_a_editar(self):
        self.client.force_login(self.dueno)
        self.assertRedirects(self.client.get(reverse("domicilio:registro")), reverse("domicilio:mi_perfil"))

    def test_edicion_solo_del_propio_perfil(self):
        # /mecanicos/mi-perfil/ no lleva id: cada cuenta solo puede llegar al suyo
        self.client.force_login(self.dueno)
        r = self.client.post(reverse("domicilio:mi_perfil"), self.datos(nombre="Wilson Editado", estado="aprobado"))
        self.assertRedirects(r, reverse("domicilio:mi_perfil"))
        self.aprobado.refresh_from_db()
        self.assertEqual(self.aprobado.nombre, "Wilson Editado")
        self.assertEqual(MecanicoDomicilio.objects.filter(nombre="Wilson Editado").count(), 1)
        # Una cuenta sin perfil va al registro, no a editar el de otro
        self.client.force_login(self.otro)
        self.assertRedirects(self.client.get(reverse("domicilio:mi_perfil")), reverse("domicilio:registro"))

    def test_mi_perfil_requiere_sesion_y_mi_cuenta_redirige(self):
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertIn(reverse("cuentas:entrar"), r["Location"])
        self.client.force_login(self.dueno)
        self.assertRedirects(self.client.get(reverse("cuentas:mi_cuenta")), reverse("domicilio:mi_perfil"))

    def test_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.dueno)
        self.assertEqual(c.post(reverse("domicilio:mi_perfil"), self.datos()).status_code, 403)


class ModeracionTests(Base):
    def test_cambiar_estado_avisa(self):
        self.pendiente.usuario = self.otro
        self.pendiente.save()
        self.assertTrue(cambiar_estado(self.pendiente, MecanicoDomicilio.Estado.APROBADO))
        self.assertTrue(self.otro.notificaciones.filter(titulo__icontains="publicado").exists())
        self.assertFalse(cambiar_estado(self.pendiente, MecanicoDomicilio.Estado.APROBADO))

    def test_consola_aprobar_solo_admin(self):
        url = reverse("consola:accion", args=["mecanicos.estado", self.pendiente.pk])
        self.client.force_login(self.otro)
        self.assertEqual(self.client.post(url, {"valor": "aprobado"}).status_code, 403)
        admin = User.objects.create_user("admin@prueba.com", password="x", is_staff=True)
        self.client.force_login(admin)
        self.client.post(url, {"valor": "aprobado"})
        self.pendiente.refresh_from_db()
        self.assertEqual(self.pendiente.estado, "aprobado")
        r = self.client.get(reverse("consola:inicio"), {"seccion": "mecanicos"})
        self.assertContains(r, "Mecánicos a domicilio")

    def test_admin_django_accion_aprobar(self):
        admin = User.objects.create_superuser("root@prueba.com", "root@prueba.com", "x")
        self.client.force_login(admin)
        self.client.post(reverse("admin:domicilio_mecanicodomicilio_changelist"),
                         {"action": "aprobar", "_selected_action": [self.pendiente.pk]})
        self.pendiente.refresh_from_db()
        self.assertEqual(self.pendiente.estado, "aprobado")


class DemoTests(TestCase):
    def test_demo_idempotente(self):
        self.assertEqual(demo.cargar(), len(demo.MECANICOS))
        self.assertEqual(demo.cargar(), 0)
        self.assertTrue(all(m.whatsapp.startswith("5730000001") for m in MecanicoDomicilio.objects.all()))
        self.assertEqual(MecanicoDomicilio.objects.publicados().count(), len(demo.MECANICOS) - 1)


class VelocidadTests(Base):
    def consultas(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as c:
            self.assertEqual(self.client.get(reverse("domicilio:listado")).status_code, 200)
        return len(c)

    def test_listado_no_crece_con_mecanicos(self):
        antes = self.consultas()
        for i in range(8):
            self.crear(f"Extra {i}", zona=self.envigado, servicio=self.llantas)
        self.assertEqual(self.consultas(), antes)
        self.assertLess(antes, 20)
