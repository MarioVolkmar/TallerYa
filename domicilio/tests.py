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
from .models import MecanicoDomicilio, ResenaMecanico, TallerDomicilio, TipoServicio, Zona

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
                "descripcion": "Voy a domicilio.", "cedula": "1.020.304.050", **extra}

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

    def test_mi_perfil_requiere_sesion_y_mi_cuenta_es_la_del_mecanico(self):
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertIn(reverse("cuentas:entrar"), r["Location"])
        self.client.force_login(self.dueno)
        cuenta = self.client.get(reverse("cuentas:mi_cuenta"))
        self.assertContains(cuenta, 'id="seguridad"')
        self.assertContains(cuenta, reverse("domicilio:mi_perfil"))

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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
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
        self.consultas()  # calienta la caché de ajustes (una consulta única)
        antes = self.consultas()
        for i in range(8):
            self.crear(f"Extra {i}", zona=self.envigado, servicio=self.llantas)
        self.assertEqual(self.consultas(), antes)
        self.assertLess(antes, 20)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AltaYVerificacionTests(Base):
    """Alta por pasos: cédula sin guardar en claro, fotos de trabajos, estado y lo que falta en Mi perfil."""

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def datos(self, **extra):
        return {"nombre": "Nuevo Mec", "whatsapp": "3001234567", "zonas": [self.robledo.pk],
                "servicios": [self.frenos.pk], "anios_experiencia": 5, "cedula": "1.020.304.050", **extra}

    def test_cedula_solo_huella_y_ultimos_digitos(self):
        self.client.force_login(self.otro)
        r = self.client.post(reverse("domicilio:registro"), self.datos())
        self.assertRedirects(r, reverse("domicilio:mi_perfil"))
        m = MecanicoDomicilio.objects.get(usuario=self.otro)
        self.assertEqual(m.cedula_ultimos, "4050")
        self.assertEqual(len(m.cedula_huella), 64)
        self.assertEqual(m.cedula_huella, MecanicoDomicilio.huella_cedula("1020304050"))
        guardado = " ".join(str(v) for v in MecanicoDomicilio.objects.filter(pk=m.pk).values().get().values())
        self.assertNotIn("1020304050", guardado)  # nunca en claro

    def test_cedula_obligatoria_y_valida(self):
        self.client.force_login(self.otro)
        for valor in ("", "abc123", "12"):
            r = self.client.post(reverse("domicilio:registro"), self.datos(cedula=valor))
            self.assertEqual(r.status_code, 200)
            self.assertIn("cedula", r.context["form"].errors)
        self.assertFalse(MecanicoDomicilio.objects.filter(usuario=self.otro).exists())

    def test_registro_muestra_pasos(self):
        r = self.client.get(reverse("domicilio:registro"))
        self.assertEqual([p[0] for p in r.context["pasos"]], ["cuenta", "trabajo", "verificacion", "opcional"])
        self.assertContains(r, "rt-seccion")  # secciones como el registro de taller, sin pasos por JS
        self.client.force_login(self.otro)  # con sesión no se pide la cuenta
        r = self.client.get(reverse("domicilio:registro"))
        self.assertEqual([p[0] for p in r.context["pasos"]], ["trabajo", "verificacion", "opcional"])

    def registrar(self, **cambios):
        self.client.force_login(self.otro)
        datos = {k: v for k, v in {**self.datos(), **cambios}.items() if v is not None}
        return self.client.post(reverse("domicilio:registro"), datos)

    def test_zonas_toda_medellin_guarda_solo_las_comunas(self):
        self.assertRedirects(self.registrar(zona_modo="medellin", zonas=None), reverse("domicilio:mi_perfil"))
        m = MecanicoDomicilio.objects.get(usuario=self.otro)
        self.assertEqual(set(m.zonas.all()), set(Zona.objects.filter(ciudad="Medellín")))
        self.assertGreater(m.zonas.count(), 10)

    def test_zonas_todo_el_valle_guarda_todas_aunque_marque_algunas(self):
        self.registrar(zona_modo="valle")
        self.assertEqual(MecanicoDomicilio.objects.get(usuario=self.otro).zonas.count(), Zona.objects.count())

    def test_zonas_elegir_guarda_las_marcadas_y_sin_ninguna_avisa(self):
        self.registrar(zona_modo="elegir")
        self.assertEqual(list(MecanicoDomicilio.objects.get(usuario=self.otro).zonas.all()), [self.robledo])
        MecanicoDomicilio.objects.filter(usuario=self.otro).delete()
        for modo in ("elegir", None):  # sin atajo y sin zonas tampoco pasa
            r = self.registrar(zona_modo=modo, zonas=None)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.context["form"].errors["zonas"], ["Elige dónde atiendes."])

    def test_selector_de_zonas_agrupado(self):
        r = self.client.get(reverse("domicilio:registro"))
        medellin, valle = [g[2] for g in r.context["grupos_zonas"]]
        self.assertEqual(len(medellin) + len(valle), Zona.objects.count())
        self.assertContains(r, 'name="zona_modo"', count=3)
        self.assertContains(r, f"Medellín y {len(valle)} municipios")

    def test_alta_solo_con_lo_minimo(self):
        r = self.registrar(anios_experiencia="")  # sin foto, descripción, marcas, horario, referencias ni años
        self.assertRedirects(r, reverse("domicilio:mi_perfil"))
        m = MecanicoDomicilio.objects.get(usuario=self.otro)
        self.assertEqual((m.anios_experiencia, m.descripcion, m.horario, m.marcas.count()), (0, "", "", 0))

    def test_tarifa_con_puntos_de_miles(self):
        self.registrar(tarifa_visita="$ 25.000")
        self.assertEqual(MecanicoDomicilio.objects.get(usuario=self.otro).tarifa_visita, 25000)

    def test_bloque_opcional_plegado_se_abre_si_trae_datos(self):
        self.client.force_login(self.otro)
        self.assertNotContains(self.client.get(reverse("domicilio:registro")), 'rm-opcional" open')
        r = self.client.post(reverse("domicilio:registro"), {**self.datos(cedula=""), "horario": "Lun-Sáb"})
        self.assertContains(r, 'rm-opcional" open')  # vuelve con error y no esconde lo que escribió

    def test_editar_perfil_sigue_con_la_lista_de_zonas(self):
        from .forms import EdicionMecanicoForm
        self.assertIn("zona_modo", EdicionMecanicoForm().fields)
        self.assertFalse(EdicionMecanicoForm().fields["zonas"].required)  # con los atajos de zona_modo

    def test_fotos_de_trabajos_validadas_y_maximo(self):
        self.client.force_login(self.otro)
        falsa = SimpleUploadedFile("x.jpg", b"<html></html>", content_type="image/jpeg")
        fotos = [jpg() for _ in range(5)] + [falsa]
        self.client.post(reverse("domicilio:registro"), {**self.datos(), "trabajos": fotos})
        m = MecanicoDomicilio.objects.get(usuario=self.otro)
        self.assertEqual(m.fotos_trabajo.count(), 4)  # máximo 4; las demás se ignoran
        self.assertTrue(all(f.imagen.name.startswith("domicilio/trabajos/") for f in m.fotos_trabajo.all()))

    def test_foto_de_trabajo_falsa_se_rechaza(self):
        self.client.force_login(self.otro)
        falsa = SimpleUploadedFile("x.jpg", b"<html></html>", content_type="image/jpeg")
        self.client.post(reverse("domicilio:registro"), {**self.datos(), "trabajos": [falsa]})
        self.assertEqual(MecanicoDomicilio.objects.get(usuario=self.otro).fotos_trabajo.count(), 0)

    def test_borrar_foto_solo_la_propia(self):
        from .models import FotoTrabajo
        foto = FotoTrabajo.objects.create(mecanico=self.aprobado, imagen=jpg())
        self.client.force_login(self.otro)
        MecanicoDomicilio.objects.create(nombre="Otro", whatsapp="573000000998", usuario=self.otro)
        url = reverse("domicilio:borrar_trabajo", args=[foto.pk])
        self.assertEqual(self.client.post(url).status_code, 404)  # sin IDOR
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(url).status_code, 405)  # solo POST
        self.client.post(url)
        self.assertFalse(FotoTrabajo.objects.filter(pk=foto.pk).exists())

    def test_mi_perfil_estado_y_lo_que_falta(self):
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertContains(r, "Publicado")
        self.assertIn("Cédula registrada (para verificar tu identidad)", r.context["faltan_obligatorios"])
        self.aprobado.estado = MecanicoDomicilio.Estado.PENDIENTE
        self.aprobado.nota_al_mecanico = "Sube una foto tuya"
        self.aprobado.save()
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertContains(r, "En revisión")
        self.assertContains(r, "Sube una foto tuya")
        self.aprobado.estado = MecanicoDomicilio.Estado.SUSPENDIDO
        self.aprobado.save()
        self.assertContains(self.client.get(reverse("domicilio:mi_perfil")), "Suspendido")

    def test_editar_conserva_cedula_si_queda_vacia(self):
        self.aprobado.poner_cedula("98765432")
        self.aprobado.save()
        self.client.force_login(self.dueno)
        r = self.client.post(reverse("domicilio:mi_perfil"), self.datos(nombre="Wilson Frenos", cedula=""))
        self.assertRedirects(r, reverse("domicilio:mi_perfil"))
        self.aprobado.refresh_from_db()
        self.assertEqual(self.aprobado.cedula_ultimos, "5432")

    def test_eleccion_de_rol_ofrece_mecanico(self):
        self.assertContains(self.client.get(reverse("cuentas:registro") + "?tipo=aliado"), reverse("domicilio:registro"))
        self.assertRedirects(self.client.get(reverse("cuentas:registro") + "?tipo=mecanico"),
                             reverse("domicilio:registro"), fetch_redirect_response=False)
        sin_rol = User.objects.create_user("g@prueba.com", "g@prueba.com", "clave-segura-123")
        self.client.force_login(sin_rol)
        self.assertContains(self.client.get(reverse("cuentas:completar") + "?tipo=aliado"), "Mecánico a domicilio")
        self.assertRedirects(self.client.get(reverse("cuentas:completar") + "?tipo=mecanico"),
                             reverse("domicilio:registro"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("domicilio:registro")).status_code, 200)


class TallerDomicilioTests(Base):
    """Talleres que también van a domicilio: activación propia, distintivo y listado mixto."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        barrio = Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]
        cls.cuenta_taller = User.objects.create_user("taller@prueba.com", "taller@prueba.com", "clave-segura-123")
        cls.taller = Taller.objects.create(nombre="Taller Prueba Dom", responsable="R", whatsapp="573000000001",
                                           direccion="Cra 1", barrio=barrio, usuario=cls.cuenta_taller, activo=True)
        cls.otra_cuenta = User.objects.create_user("t2@prueba.com", "t2@prueba.com", "clave-segura-123")
        cls.otro_taller = Taller.objects.create(nombre="Otro Taller", responsable="R", whatsapp="573000000002",
                                                direccion="Cra 2", barrio=barrio, usuario=cls.otra_cuenta, activo=True)

    def activar(self, **extra):
        self.client.force_login(self.cuenta_taller)
        return self.client.post(reverse("domicilio:mi_taller"), {
            "activo": "on", "zonas": [self.envigado.pk], "servicios": [self.llantas.pk], "tarifa_visita": 20000, **extra})

    def nombres(self, **params):
        return [x.nombre for x in self.client.get(reverse("domicilio:listado"), params).context["pagina"]]

    def test_mi_taller_atajo_de_zonas_y_tarifa_con_puntos(self):
        self.activar(zona_modo="valle", zonas=[], tarifa_visita="$ 30.000")
        d = TallerDomicilio.objects.get(taller=self.taller)
        self.assertEqual((d.zonas.count(), d.tarifa_visita), (Zona.objects.count(), 30000))
        self.assertEqual(d.zonas_texto, "todo el Valle de Aburrá")
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "Servicio a domicilio</strong> en todo el Valle de Aburrá")
        self.activar(zona_modo="medellin", zonas=[])
        self.assertEqual(TallerDomicilio.objects.get(taller=self.taller).zonas_texto, "toda Medellín")
        r = self.client.get(reverse("domicilio:mi_taller"))
        self.assertEqual(r.context["form"].initial["zona_modo"], "medellin")  # al volver, el atajo queda marcado

    def test_mi_taller_un_solo_interruptor_y_texto_nuevo(self):
        self.client.force_login(self.cuenta_taller)
        r = self.client.get(reverse("domicilio:mi_taller"))
        self.assertContains(r, 'name="activo"', count=1)
        self.assertContains(r, "rm-estado-off")
        self.assertContains(r, "Atiende motos donde estén")
        self.assertNotContains(r, "dom-estado")  # sin el aviso suelto de estado
        self.assertContains(r, 'name="zona_modo"', count=3)
        # Apagado se guarda sin pedir zonas ni servicios
        r = self.client.post(reverse("domicilio:mi_taller"), {"zona_modo": "elegir"})
        self.assertRedirects(r, reverse("domicilio:mi_taller"))

    def test_activar_y_sale_en_listado_mixto(self):
        self.assertRedirects(self.activar(), reverse("domicilio:mi_taller"))
        self.assertTrue(TallerDomicilio.objects.get(taller=self.taller).activo)
        self.assertIn("Taller Prueba Dom", self.nombres())
        self.assertIn("Yeison Llantas", self.nombres())  # junto a los independientes
        # los filtros de zona y servicio aplican a los dos
        self.assertEqual(set(self.nombres(zona=self.envigado.pk)), {"Taller Prueba Dom", "Yeison Llantas"})
        self.assertNotIn("Taller Prueba Dom", self.nombres(zona=self.robledo.pk))
        self.assertNotIn("Taller Prueba Dom", self.nombres(servicio=self.frenos.pk))
        self.assertEqual(self.nombres(tipo="talleres"), ["Taller Prueba Dom"])
        self.assertNotIn("Taller Prueba Dom", self.nombres(tipo="independientes"))
        self.assertContains(self.client.get(reverse("domicilio:listado")), "Taller en Belén")

    def test_activo_exige_zona_y_servicio(self):
        r = self.activar(zonas=[], servicios=[])
        self.assertEqual(r.status_code, 200)
        self.assertIn("zonas", r.context["form"].errors)
        self.assertFalse(TallerDomicilio.objects.filter(taller=self.taller, activo=True).exists())

    def test_taller_no_aprobado_o_apagado_no_sale(self):
        self.activar()
        Taller.objects.filter(pk=self.taller.pk).update(activo=False)
        self.assertNotIn("Taller Prueba Dom", self.nombres())
        Taller.objects.filter(pk=self.taller.pk).update(activo=True)
        self.activar(activo="")
        self.assertNotIn("Taller Prueba Dom", self.nombres())

    def test_distintivo_en_ficha_y_directorio(self):
        self.activar()
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "Servicio a domicilio")
        self.assertNotContains(self.client.get(self.otro_taller.get_absolute_url()), "Servicio a domicilio")
        self.assertContains(self.client.get(reverse("talleres:directorio")), "tc-chapa-dom", count=1)

    def test_solo_su_propio_taller_y_csrf(self):
        # Sin id en la URL: cada cuenta edita el de su taller; un motero no entra
        self.activar()
        self.client.force_login(self.otra_cuenta)
        self.client.post(reverse("domicilio:mi_taller"), {"activo": "", "zonas": [], "servicios": []})
        self.assertTrue(TallerDomicilio.objects.get(taller=self.taller).activo)
        self.client.force_login(self.otro)
        self.assertRedirects(self.client.get(reverse("domicilio:mi_taller")), reverse("cuentas:mi_cuenta"),
                             fetch_redirect_response=False)
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.cuenta_taller)
        self.assertEqual(c.post(reverse("domicilio:mi_taller"), {"activo": ""}).status_code, 403)

    def test_demo_talleres_idempotente(self):
        Taller.objects.filter(pk=self.taller.pk).update(nombre="MotoServicio El Paisa")
        self.assertEqual(demo.cargar_talleres(), 1)
        self.assertEqual(demo.cargar_talleres(), 0)
        self.assertIn("MotoServicio El Paisa", self.nombres(tipo="talleres"))

    def test_listado_mixto_no_crece_con_talleres(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.activar()
        self.client.logout()  # anónimo: sin mensajes ni sesión que cambien entre una visita y otra

        def consultas():
            with CaptureQueriesContext(connection) as c:
                self.client.get(reverse("domicilio:listado"))
            return len(c)
        antes = consultas()
        self.assertEqual(consultas(), antes)
        for i in range(5):
            t = Taller.objects.create(nombre=f"Extra {i}", responsable="R", whatsapp="573000000003", direccion="C",
                                      barrio=self.taller.barrio, activo=True)
            d = TallerDomicilio.objects.create(taller=t, activo=True)
            d.zonas.add(self.envigado)
            d.servicios.add(self.llantas)
        self.assertEqual(consultas(), antes)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FichaCompletaTests(Base):
    """La ficha del mecánico con las secciones del detalle del taller: visita, favoritos, cómo trabaja, verificaciones."""

    def test_secciones_y_datos(self):
        m = self.aprobado
        m.especialidades, m.compromisos, m.garantia_meses = ["frenos", "inventada"], ["presupuesto"], 2
        m.herramientas, m.horario, m.tarifa_visita, m.anios_experiencia = "escáner, multímetro", "Lun-Sáb 7-6", 30000, 9
        m.poner_cedula("123456789")
        m.save()
        r = self.client.get(m.get_absolute_url())
        for texto in ("Solicitar visita", "WhatsApp", "Llamar", "Guardar", "Frenos y ABS", "Garantía de 2 meses",
                      "Presupuesto antes de empezar", "Escáner", "Multímetro",
                      "Zona de cobertura", "Robledo", "Visita desde", "Lun-Sáb 7-6", "9 años"):
            self.assertContains(r, texto)
        self.assertNotContains(r, "inventada")
        self.assertNotContains(r, "123456789")
        self.assertContains(r, "domicilio/js/ficha.js")

    def test_no_publicado_sin_visita_ni_favorito(self):
        self.client.force_login(self.dueno)
        self.aprobado.estado = MecanicoDomicilio.Estado.PENDIENTE
        self.aprobado.save()
        r = self.client.get(self.aprobado.get_absolute_url())
        self.assertNotContains(r, "dialogo-visita")
        self.assertContains(r, "Editar mi perfil")
        self.assertEqual(self.client.get(reverse("domicilio:visita", args=[self.aprobado.slug])).status_code, 404)

    def test_visita_arma_whatsapp_solo_con_datos_del_mecanico(self):
        from urllib.parse import unquote
        url = reverse("domicilio:visita", args=[self.aprobado.slug])
        r = self.client.get(url, {"servicio": self.frenos.pk, "zona": self.robledo.pk, "moto": "NMAX  2022",
                                  "cuando": "hoy", "detalle": "chilla al frenar"})
        self.assertEqual(r.status_code, 302)
        destino = unquote(r["Location"])
        self.assertTrue(r["Location"].startswith("https://wa.me/573000000999?text="))
        for texto in ("Servicio: Frenos", "Zona: Robledo", "Moto: NMAX 2022", "Cuándo: Hoy", "chilla al frenar"):
            self.assertIn(texto, destino)
        # Un servicio o zona que el mecánico no ofrece se ignora; valores raros no rompen nada
        r = self.client.get(url, {"servicio": self.llantas.pk, "zona": self.envigado.pk, "cuando": "<x>"})
        destino = unquote(r["Location"])
        self.assertNotIn("Llantas", destino)
        self.assertNotIn("Envigado", destino)
        self.assertNotIn("<x>", destino)

    def test_favorito_con_cuenta_y_post(self):
        from .models import MecanicoFavorito
        url = reverse("domicilio:favorito", args=[self.aprobado.slug])
        self.assertIn(reverse("cuentas:entrar"), self.client.post(url)["Location"])
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(url).status_code, 405)
        r = self.client.post(url, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.json(), {"favorito": True})
        self.assertContains(self.client.get(self.aprobado.get_absolute_url()), "En favoritos")
        self.client.post(url, {"next": "https://malo.example/"})
        self.assertFalse(MecanicoFavorito.objects.exists())
        self.assertEqual(self.client.post(reverse("domicilio:favorito", args=[self.pendiente.slug])).status_code, 404)

    def test_resena_desde_ventana(self):
        self.client.force_login(self.otro)
        r = self.client.post(self.aprobado.get_absolute_url(), {"estrellas": "4", "comentario": "Muy cumplido"})
        self.assertEqual(r.status_code, 302)
        self.assertContains(self.client.get(self.aprobado.get_absolute_url()), "Muy cumplido")

    def test_mi_perfil_edita_lo_de_la_ficha(self):
        self.client.force_login(self.dueno)
        datos = {"nombre": "Wilson Frenos", "whatsapp": "3001234567", "zonas": [self.robledo.pk],
                 "servicios": [self.frenos.pk], "anios_experiencia": 5, "cedula": "11223344",
                 "especialidades": ["frenos", "electrico"], "compromisos": ["fotos"], "garantia_meses": "3",
                 "herramientas": "escáner, gato"}
        self.assertRedirects(self.client.post(reverse("domicilio:mi_perfil"), datos), reverse("domicilio:mi_perfil"))
        self.aprobado.refresh_from_db()
        self.assertEqual((self.aprobado.especialidades, self.aprobado.compromisos, self.aprobado.garantia_meses,
                          self.aprobado.herramientas_lista), (["frenos", "electrico"], ["fotos"], 3, ["Escáner", "Gato"]))
        r = self.client.post(reverse("domicilio:mi_perfil"), {**datos, "especialidades": ["noexiste"]})
        self.assertEqual(r.status_code, 200)

    def test_demo_rellena_la_ficha(self):
        demo.cargar()
        m = MecanicoDomicilio.objects.get(nombre="Luz Dary Gómez (demo)")
        self.assertTrue(m.especialidades and m.compromisos and m.herramientas)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FichaAjustesTests(Base):
    """Ronda 3: aviso discreto, sello «Verificado por TallerYa» solo con lo verificado, mayúsculas e ilustraciones demo."""

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def ficha(self, m=None):
        return self.client.get((m or self.aprobado).get_absolute_url())

    def test_aviso_discreto_y_completo_en_la_visita(self):
        r = self.ficha()
        self.assertContains(r, "dom-aviso-mini")
        self.assertContains(r, "TallerYa conecta; el acuerdo y el pago son con el mecánico.")
        self.assertContains(r, "dom-aviso-visita")  # texto completo dentro de «Solicitar visita»
        self.assertNotContains(r, 'class="dom-aviso ')  # ya no la caja amarilla grande
        self.assertNotContains(r, "Toca uno para pedir la visita")
        self.assertContains(r, "dom-chip-accion")

    def test_sin_verificar_no_hay_sello(self):
        self.assertNotContains(self.ficha(), "Verificado por TallerYa")
        self.assertNotContains(self.ficha(), "Lo que revisó TallerYa")

    def test_sello_solo_con_lo_verificado(self):
        m = self.aprobado
        m.verificado, m.anios_experiencia = True, 8
        m.poner_cedula("10203040")
        m.save()
        r = self.ficha()
        self.assertContains(r, "Verificado por TallerYa")
        self.assertContains(r, "Identidad confirmada")
        self.assertContains(r, "Experiencia revisada")
        self.assertNotContains(r, "Referencias comprobadas")  # no dio referencias: no se lista
        self.assertContains(r, "Revisamos cada perfil antes de publicarlo")
        m.referencias = "Carlos, 3001112233"
        m.save()
        r = self.ficha()
        self.assertContains(r, "Referencias comprobadas")
        self.assertNotContains(r, "3001112233")  # las referencias nunca se publican

    def test_herramientas_con_mayuscula_al_guardar_y_al_mostrar(self):
        self.client.force_login(self.dueno)
        datos = {"nombre": "Wilson Frenos", "whatsapp": "3001234567", "zonas": [self.robledo.pk],
                 "servicios": [self.frenos.pk], "anios_experiencia": 5, "cedula": "11223344",
                 "herramientas": "escáner básico,  multímetro , escáner básico, , gato de moto"}
        self.client.post(reverse("domicilio:mi_perfil"), datos)
        self.aprobado.refresh_from_db()
        self.assertEqual(self.aprobado.herramientas, "Escáner básico, Multímetro, Gato de moto")
        MecanicoDomicilio.objects.filter(pk=self.aprobado.pk).update(herramientas="compresor, llaves")  # datos viejos
        self.assertContains(self.ficha(), "Compresor")

    def test_ilustraciones_demo_propias(self):
        from PIL import Image
        demo.cargar()
        m = MecanicoDomicilio.objects.get(nombre="Wilson Arango (demo)")
        self.assertTrue(m.foto.name.endswith(".jpg"))
        self.assertEqual(Image.open(m.foto.path).size, (480, 480))
        self.assertEqual(m.fotos_trabajo.count(), 3)
        self.assertEqual(demo.imagenes(), 0)  # idempotente: no repite
        self.assertEqual(m.fotos_trabajo.count(), 3)
        r = self.client.get(reverse("domicilio:listado"))
        self.assertContains(r, m.foto.url)  # avatar en la tarjeta del listado
        self.assertContains(self.ficha(m), "perfil-franja")  # galería en la ficha


class PreciosYRespuestasTests(Base):
    """Ronda 4: «Precios desde» (como el taller) con la visita a domicilio, y respuesta del mecánico a reseñas."""

    def test_tabla_precios_en_la_ficha(self):
        from .models import PrecioMecanico
        self.aprobado.servicios.add(self.llantas)
        self.aprobado.tarifa_visita = 25000
        self.aprobado.mostrar_precios = True
        self.aprobado.save()
        PrecioMecanico.objects.create(mecanico=self.aprobado, servicio=self.frenos, cilindraje="baja", desde=35000, hasta=60000)
        PrecioMecanico.objects.create(mecanico=self.aprobado, servicio=self.frenos, cilindraje="media", desde=50000, hasta=80000)
        r = self.client.get(self.aprobado.get_absolute_url())
        for texto in ("Precios desde", "orientativos, no son una cotización", "Hasta 150 cc", "150–400 cc",
                      "$35.000", "$50.000", "Visita a domicilio", "desde $25.000", "También hace:", "Llantas y despinche"):
            self.assertContains(r, texto)
        self.assertNotContains(r, "Más de 400 cc")  # solo las columnas usadas

    def test_precios_ocultos_invita_a_cotizar(self):
        from .models import PrecioMecanico
        PrecioMecanico.objects.create(mecanico=self.aprobado, servicio=self.frenos, cilindraje="baja", desde=35000, hasta=60000)
        r = self.client.get(self.aprobado.get_absolute_url())
        self.assertContains(r, "Cotizar por WhatsApp")
        self.assertContains(r, "Servicios a domicilio")
        self.assertNotContains(r, "$35.000")

    def test_mis_precios_interruptor_mostrar(self):
        """El interruptor de «Mis precios» guarda al instante (fetch, 204) y la pantalla trae el editor por tarjetas."""
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:mis_precios"))
        self.assertContains(r, "data-mis-precios")
        self.assertContains(r, "¿Cómo se usan?")
        url = reverse("domicilio:alternar_precios")
        r = self.client.post(url, {"valor": "1"}, headers={"x-requested-with": "fetch"})
        self.assertEqual(r.status_code, 204)
        self.aprobado.refresh_from_db()
        self.assertTrue(self.aprobado.mostrar_precios)
        self.client.post(url, {"valor": "0"}, headers={"x-requested-with": "fetch"})
        self.aprobado.refresh_from_db()
        self.assertFalse(self.aprobado.mostrar_precios)

    def test_multimarca_en_la_ficha(self):
        self.assertNotContains(self.client.get(self.aprobado.get_absolute_url()), "Multimarca")
        self.aprobado.multimarca = True
        self.aprobado.save()
        self.assertContains(self.client.get(self.aprobado.get_absolute_url()), "Multimarca")

    def test_sin_precios_muestra_servicios(self):
        r = self.client.get(self.aprobado.get_absolute_url())
        self.assertContains(r, "Servicios a domicilio")
        self.assertNotContains(r, "orientativos, no son una cotización")

    def test_mis_precios_solo_sus_servicios_y_validado(self):
        url = reverse("domicilio:mis_precios")
        self.assertIn(reverse("cuentas:entrar"), self.client.get(url)["Location"])
        self.client.force_login(self.dueno)
        base = {"precios-TOTAL_FORMS": "1", "precios-INITIAL_FORMS": "0", "precios-MIN_NUM_FORMS": "0",
                "precios-MAX_NUM_FORMS": "40"}
        fila = {"precios-0-servicio": self.frenos.pk, "precios-0-cilindraje": "baja", "precios-0-desde": "30000",
                "precios-0-hasta": "50000"}
        self.assertRedirects(self.client.post(url, {**base, **fila}), url)
        self.assertEqual(self.aprobado.precios.get().desde, 30000)
        # Un servicio que no ofrece, o un «hasta» menor, no se guardan
        r = self.client.post(url, {**base, **fila, "precios-0-servicio": self.llantas.pk})
        self.assertEqual(r.status_code, 200)
        r = self.client.post(url, {**base, **fila, "precios-0-cilindraje": "media", "precios-0-hasta": "100"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.aprobado.precios.count(), 1)

    def test_responder_resena_solo_las_propias(self):
        r1 = ResenaMecanico.objects.create(mecanico=self.aprobado, usuario=self.otro, nombre="Ana", estrellas=5, comentario="Bien")
        r2 = ResenaMecanico.objects.create(mecanico=self.envigadeno, usuario=self.otro, nombre="Ana", estrellas=4, comentario="Ok")
        self.client.force_login(self.dueno)
        url = reverse("domicilio:responder_resena", args=[r1.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {"respuesta": "¡Gracias, Ana!"})
        r1.refresh_from_db()
        self.assertEqual(r1.respuesta, "¡Gracias, Ana!")
        self.assertIsNotNone(r1.respondida_en)
        self.assertContains(self.client.get(self.aprobado.get_absolute_url()), "Respuesta de Wilson Frenos")
        self.assertEqual(self.client.post(reverse("domicilio:responder_resena", args=[r2.pk]),
                                          {"respuesta": "x"}).status_code, 404)  # sin IDOR
        self.client.post(url, {"respuesta": ""})
        r1.refresh_from_db()
        self.assertEqual((r1.respuesta, r1.respondida_en), ("", None))

    def test_mi_perfil_enlaza_precios_y_resenas(self):
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertContains(r, reverse("domicilio:mis_precios"))
        self.assertContains(r, reverse("domicilio:resenas"))

    def test_panel_y_pagina_de_resenas(self):
        ResenaMecanico.objects.create(mecanico=self.aprobado, usuario=self.otro, nombre="Ana", estrellas=5, comentario="Muy bien")
        self.client.force_login(self.dueno)
        self.assertContains(self.client.get(reverse("domicilio:panel")), "Muy bien")
        r = self.client.get(reverse("domicilio:resenas") + "?ver=sin_responder")
        self.assertContains(r, "Muy bien")
        self.client.post(reverse("domicilio:responder_resena", args=[1]), {"respuesta": "Gracias", "volver": "https://malo.com/"})
        r = self.client.get(reverse("domicilio:resenas") + "?ver=sin_responder")
        self.assertEqual(self.client.get(reverse("domicilio:resenas")).status_code, 200)


class SolicitudVisitaTests(Base):
    """Solicitar visita guarda la solicitud; el mecánico la cotiza y el motero la acepta o la rechaza (como las citas)."""
    def pedir(self, **extra):
        datos = {"nombre": "Camilo", "telefono": "300 555 1234", "servicio": self.frenos.pk, "zona": self.robledo.pk,
                 "moto": "Yamaha NMAX", "cuando": "hoy", "detalle": "Frena mal", **extra}
        return self.client.post(reverse("domicilio:visita", args=[self.aprobado.slug]), datos)

    def cotizar(self, s, **extra):
        from datetime import date, timedelta
        datos = {"desde": "80.000", "hasta": "80.000", "incluye": "Pastillas y mano de obra",
                 "fecha": (date.today() + timedelta(days=1)).isoformat(), "hora": "10:00", **extra}
        return self.client.post(reverse("domicilio:solicitud_cotizar", args=[s.pk]), datos)

    def test_pedir_guarda_la_solicitud_y_abre_whatsapp_con_el_enlace(self):
        from .models import SolicitudVisita
        r = self.pedir()
        s = SolicitudVisita.objects.get()
        self.assertEqual((s.mecanico, s.telefono, s.estado), (self.aprobado, "573005551234", "pendiente"))
        # Queda en TallerYa, en la página de su visita, con el botón de WhatsApp (que lleva el enlace) a un toque
        self.assertEqual(r["Location"], s.get_absolute_url())
        pagina = self.client.get(r["Location"])
        self.assertContains(pagina, "Avisarle también por WhatsApp")
        self.assertContains(pagina, s.token)
        self.assertNotContains(self.client.get(r["Location"]), "Avisarle también por WhatsApp")  # solo la primera vez

    def test_sin_celular_no_guarda_pero_abre_whatsapp(self):
        from .models import SolicitudVisita
        r = self.pedir(telefono="")
        self.assertFalse(SolicitudVisita.objects.exists())
        self.assertTrue(r["Location"].startswith("https://wa.me/"))

    def test_cotizar_aceptar_y_marcar_atendida(self):
        from .models import SolicitudVisita
        self.pedir()
        s = SolicitudVisita.objects.get()
        self.client.force_login(self.dueno)
        self.assertContains(self.client.get(reverse("domicilio:solicitudes")), "Camilo")
        self.cotizar(s)
        s.refresh_from_db()
        self.assertEqual((s.estado, s.precio_texto), ("cotizada", "$80.000"))
        self.client.logout()
        self.assertContains(self.client.get(s.get_absolute_url()), "Aceptar y agendar")
        self.client.post(s.get_absolute_url(), {"accion": "aceptar"})
        s.refresh_from_db()
        self.assertEqual(s.estado, "confirmada")
        self.client.force_login(self.dueno)
        self.client.post(reverse("domicilio:solicitud_estado", args=[s.pk]), {"estado": "atendida"})
        s.refresh_from_db()
        self.assertEqual(s.estado, "atendida")

    def test_rechazar_y_no_tocar_solicitudes_ajenas(self):
        from .models import SolicitudVisita
        self.pedir()
        s = SolicitudVisita.objects.get()
        self.client.force_login(self.dueno)
        self.cotizar(s, desde="90.000", hasta="70.000")  # hasta menor: no cotiza
        s.refresh_from_db()
        self.assertEqual(s.estado, "pendiente")
        self.cotizar(s)
        self.client.post(s.get_absolute_url(), {"accion": "rechazar"})
        s.refresh_from_db()
        self.assertEqual((s.estado, s.rechazada), ("pendiente", True))
        MecanicoDomicilio.objects.create(nombre="Otro", whatsapp="573000000998", usuario=self.otro)
        self.client.force_login(self.otro)
        self.assertEqual(self.cotizar(s).status_code, 404)
        self.assertEqual(self.client.post(reverse("domicilio:solicitud_estado", args=[s.pk]), {"estado": "cancelada"}).status_code, 404)


class PanelMecanicoTests(Base):
    """Panel «Mi panel» del mecánico: por hacer, precios con interruptor, menú y entrada directa."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.dueno)

    def test_panel_con_por_hacer_y_accesos(self):
        from .models import SolicitudVisita
        SolicitudVisita.objects.create(mecanico=self.aprobado, nombre="Luis", telefono="573001112233", moto="NMAX", servicio=self.frenos)
        r = self.client.get(reverse("domicilio:panel"))
        for texto in ("Mi panel", "Responder solicitudes", "Por hacer", "1 solicitud</strong> por cotizar", "Mi ficha",
                      "Perfil", "Reporte", "aún no has cargado precios", "Armar mi tabla"):
            self.assertContains(r, texto)

    def test_mis_servicios_vacio_con_boton_y_visita_sin_registrar(self):
        from .models import SolicitudVisita
        r = self.client.get(reverse("domicilio:servicios"))
        self.assertContains(r, "Aún no has registrado servicios")
        self.assertContains(r, reverse("garaje:servicio_mecanico"))
        v = SolicitudVisita.objects.create(mecanico=self.aprobado, nombre="Luis", telefono="573001112233", moto="NMAX",
                                           servicio=self.frenos, estado="atendida")
        r = self.client.get(reverse("domicilio:servicios"))
        self.assertContains(r, "Visitas atendidas sin registrar")
        self.assertContains(r, reverse("garaje:servicio_visita", args=[v.pk]))

    def test_mis_servicios_pide_perfil_y_barra_apunta_a_la_vista(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("domicilio:servicios")).status_code, 302)
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:panel"))
        self.assertContains(r, f'href="{reverse("domicilio:servicios")}" class="bi-item"')

    def test_interruptor_de_precios(self):
        from .models import PrecioMecanico
        PrecioMecanico.objects.create(mecanico=self.aprobado, servicio=self.frenos, cilindraje="baja", desde=35000, hasta=60000)
        r = self.client.get(reverse("domicilio:panel"))
        self.assertContains(r, "ocultos: tu ficha dice")
        self.assertContains(r, "Mostrar precios en mi perfil")
        self.client.post(reverse("domicilio:alternar_precios"), {"valor": "1"})
        self.aprobado.refresh_from_db()
        self.assertTrue(self.aprobado.mostrar_precios)
        self.assertContains(self.client.get(reverse("domicilio:panel")), "visibles en tu ficha")

    def test_solo_el_propio_perfil_y_sin_perfil(self):
        self.client.force_login(self.otro)  # sin perfil de mecánico
        self.assertRedirects(self.client.get(reverse("domicilio:panel")), reverse("domicilio:registro"))
        self.assertEqual(self.client.post(reverse("domicilio:alternar_precios"), {"valor": "1"}).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("domicilio:panel")).status_code, 302)

    def test_pausado_y_en_revision_avisan(self):
        self.aprobado.estado = MecanicoDomicilio.Estado.SUSPENDIDO
        self.aprobado.save()
        self.assertContains(self.client.get(reverse("domicilio:panel")), "pausado")

    def test_menu_y_entrada_al_panel(self):
        r = self.client.get(reverse("domicilio:panel"))
        self.assertContains(r, 'class="av-item" aria-current="page">Mi panel')
        r = self.client.post(reverse("cuentas:entrar"), {"username": "mec@prueba.com", "password": "clave-segura-123"})
        self.assertRedirects(r, reverse("domicilio:panel"), fetch_redirect_response=False)
