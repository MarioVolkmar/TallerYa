"""Paso 3 del piloto: alta asistida, autoregistro, precios con recordatorio, servicio rápido y reseña verificada."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from garaje.models import ServicioTaller
from garaje.tests_avisos import crear_moto

from . import precios
from .models import Barrio, PrecioServicio, Resena, Servicio, Taller

User = get_user_model()


def datos_ficha(barrio, servicio, **extra):
    return {"nombre": "Motos Belén", "responsable": "Luis", "whatsapp": "3001234567", "ciudad": "Medellín",
            "barrio": barrio.pk, "direccion": "Calle 1 # 2-3", "servicios": [servicio.pk], **extra}


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.barrio = Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]
        cls.servicio = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        cls.admin = User.objects.create_user("adm@t.co", "adm@t.co", "clave-segura-123", is_staff=True)


class AltaAsistidaTests(Base):
    def alta(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse("consola:alta_taller"), datos_ficha(self.barrio, self.servicio))
        self.assertEqual(r.status_code, 302)
        return Taller.objects.get(nombre="Motos Belén")

    def test_crea_sin_publicar_con_token(self):
        t = self.alta()
        self.assertFalse(t.activo)
        self.assertEqual(t.origen_alta, Taller.Alta.ASISTIDO)
        self.assertTrue(t.token_revision)
        self.assertTrue(t.pendiente_de_revision)

    def test_solo_admin(self):
        self.client.force_login(User.objects.create_user("m@t.co", "m@t.co", "x"))
        self.assertEqual(self.client.get(reverse("consola:alta_taller")).status_code, 403)

    def test_no_se_publica_sin_aprobacion_del_taller(self):
        t = self.alta()
        r = self.client.post(reverse("consola:accion", args=["talleres.publicar", t.pk]), {"valor": "1"},
                             headers={"X-Requested-With": "fetch"})
        self.assertEqual(r.status_code, 400)
        t.refresh_from_db()
        self.assertFalse(t.activo)

    def test_el_taller_revisa_corrige_y_aprueba(self):
        t = self.alta()
        self.client.logout()
        url = reverse("talleres:revisar_ficha", args=[t.token_revision])
        self.assertEqual(self.client.get(url).status_code, 200)
        # corregir sin autorizar: no aprueba
        self.client.post(url, datos_ficha(self.barrio, self.servicio, nombre="Motos Belén 2"))
        t.refresh_from_db()
        self.assertEqual(t.nombre, "Motos Belén 2")
        self.assertIsNone(t.aprobado_por_taller)
        # autorizar: aprueba y deja fecha e IP
        self.client.post(url, datos_ficha(self.barrio, self.servicio, nombre="Motos Belén 2", autoriza="on"),
                         REMOTE_ADDR="10.1.2.3")
        t.refresh_from_db()
        self.assertTrue(t.autoriza_datos)
        self.assertIsNotNone(t.aprobado_por_taller)
        self.assertEqual(t.aprobado_ip, "10.1.2.3")
        self.assertFalse(t.activo)  # sigue sin publicar hasta que el equipo lo publique
        # después de aprobar es de solo lectura
        self.client.post(url, datos_ficha(self.barrio, self.servicio, nombre="Otro"))
        t.refresh_from_db()
        self.assertEqual(t.nombre, "Motos Belén 2")
        # ahora sí se puede publicar
        self.client.force_login(self.admin)
        r = self.client.post(reverse("consola:accion", args=["talleres.publicar", t.pk]), {"valor": "1"},
                             headers={"X-Requested-With": "fetch"})
        self.assertEqual(r.status_code, 200)

    def test_token_invalido_404(self):
        self.assertEqual(self.client.get(reverse("talleres:revisar_ficha", args=["nada"])).status_code, 404)

    def test_revision_no_se_indexa(self):
        t = self.alta()
        self.client.logout()
        r = self.client.get(reverse("talleres:revisar_ficha", args=[t.token_revision]))
        self.assertIn("noindex", r["X-Robots-Tag"])


class AutoregistroTests(Base):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # el freno por IP vive en la caché

    def test_queda_pendiente_y_aprobado_por_el_taller(self):
        r = self.client.post(reverse("talleres:autoregistro"), datos_ficha(self.barrio, self.servicio, autoriza="on"))
        t = Taller.objects.get(nombre="Motos Belén")
        self.assertRedirects(r, reverse("talleres:alta_enviada", args=[t.token_revision]))
        self.assertFalse(t.activo)
        self.assertEqual(t.origen_alta, Taller.Alta.AUTOREGISTRO)
        self.assertTrue(t.autoriza_datos and t.aprobado_por_taller)

    def test_exige_autorizacion(self):
        r = self.client.post(reverse("talleres:autoregistro"), datos_ficha(self.barrio, self.servicio))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Taller.objects.exists())

    def test_freno_por_ip(self):
        for i in range(6):
            self.client.post(reverse("talleres:autoregistro"),
                             datos_ficha(self.barrio, self.servicio, nombre=f"T{i}", autoriza="on"))
        self.assertEqual(Taller.objects.count(), 5)


class PreciosTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user("t@t.co", "t@t.co", "x")
        cls.taller = Taller.objects.create(nombre="Taller", responsable="R", whatsapp="573000000001", direccion="x",
                                           barrio=cls.barrio, usuario=cls.user, activo=True, mostrar_precios=True)
        cls.taller.servicios.add(cls.servicio)
        cls.precio = PrecioServicio.objects.create(taller=cls.taller, servicio=cls.servicio, desde=20000, hasta=30000)

    def envejecer(self, dias):
        PrecioServicio.objects.filter(pk=self.precio.pk).update(actualizado=timezone.now() - timedelta(days=dias))

    def test_recordatorio_a_los_75_dias(self):
        self.assertFalse(precios.necesita_confirmar(self.taller))
        self.envejecer(80)
        self.assertTrue(precios.necesita_confirmar(self.taller))

    def test_siguen_vigentes_renueva_la_fecha(self):
        self.envejecer(80)
        self.client.force_login(self.user)
        self.client.post(reverse("talleres:precios"), {"siguen_vigentes": "1"})
        self.assertFalse(precios.necesita_confirmar(self.taller))

    def test_panel_avisa(self):
        self.envejecer(80)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("talleres:panel")), "más de 2 meses")

    def test_perfil_muestra_fecha_solo_si_mostrar_precios(self):
        self.envejecer(10)
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "confirmado el")
        Taller.objects.filter(pk=self.taller.pk).update(mostrar_precios=False)
        self.assertNotContains(self.client.get(self.taller.get_absolute_url()), "confirmado el")


class ServicioRapidoYResenaTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user("t@t.co", "t@t.co", "x")
        cls.taller = Taller.objects.create(nombre="Taller", responsable="R", whatsapp="573000000001", direccion="x",
                                           barrio=cls.barrio, usuario=cls.user, activo=True)
        cls.moto = crear_moto(placa="ABC12D", km_actual=5000)
        cls.dueno = cls.moto.motociclista.usuario

    def registrar(self, **extra):
        self.client.force_login(self.user)
        datos = {"placa": "abc-12d", "km": "5400", "otros": "Cambio de aceite", "costo": "45.000", **extra}
        return self.client.post(reverse("talleres:servicio_rapido"), datos)

    def test_crea_servicio_por_confirmar(self):
        self.registrar()
        s = ServicioTaller.objects.get()
        self.assertEqual((s.moto, s.km, s.costo, s.otros), (self.moto, 5400, 45000, "Cambio de aceite"))
        self.assertEqual(s.estado, ServicioTaller.Estado.POR_CONFIRMAR)

    def test_placa_desconocida_y_km_menor(self):
        self.registrar(placa="ZZZ99Z")
        self.registrar(km="100")
        self.assertFalse(ServicioTaller.objects.exists())

    def test_sin_taller_redirige(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse("talleres:servicio_rapido")).status_code, 302)

    def test_km_con_puntos_y_chips_del_plan(self):
        from garaje import servicio_taller as st
        tarea = st.tareas_de(self.moto)[0]
        self.registrar(km="5.400", otros="", tareas=[tarea.pk])
        s = ServicioTaller.objects.get()
        self.assertEqual((s.km, list(s.tareas.all()), s.estado), (5400, [tarea], ServicioTaller.Estado.POR_CONFIRMAR))

    def test_sin_trabajo_no_guarda(self):
        self.registrar(otros="")
        self.assertFalse(ServicioTaller.objects.exists())

    def test_km_menor_pide_marcar_servicio_antiguo(self):
        self.registrar(km="100")
        self.assertFalse(ServicioTaller.objects.exists())
        self.registrar(km="100", km_antiguo="on")
        self.assertEqual(ServicioTaller.objects.get().km, 100)

    def test_con_codigo_del_dueno_queda_verificado(self):
        from garaje.models import CodigoServicio
        from garaje.hoja_vida import generar_codigo
        c = generar_codigo(self.moto)
        self.registrar(placa="", codigo=c.codigo)
        s = ServicioTaller.objects.get()
        self.assertEqual((s.origen, s.estado), (ServicioTaller.Origen.CODIGO, ServicioTaller.Estado.VERIFICADO))
        self.assertTrue(CodigoServicio.objects.get(pk=c.pk).usado)
        self.registrar(placa="", codigo=c.codigo)  # ya usado
        self.assertEqual(ServicioTaller.objects.count(), 1)

    def test_consulta_en_vivo_de_la_placa(self):
        self.client.force_login(self.user)
        url = reverse("talleres:servicio_rapido_moto")
        d = self.client.get(url, {"placa": "abc-12d"}).json()
        self.assertEqual((d["estado"], d["km"]), ("ok", 5000))
        self.assertEqual(self.client.get(url, {"placa": "ZZZ99Z"}).json()["estado"], "no_esta")
        self.assertEqual(self.client.get(url, {"placa": "AB"}).json()["estado"], "corta")
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(url, {"placa": "ABC12D"}).status_code, 403)

    def test_resena_verificada_solo_con_servicio_verificado(self):
        self.registrar()
        s = ServicioTaller.objects.get()
        self.client.force_login(self.dueno)
        datos = {"accion": "resena", "nombre": "Ana", "estrellas": 5, "comentario": "Muy bien"}
        self.client.post(self.taller.get_absolute_url(), datos)  # servicio aún por confirmar
        self.assertFalse(Resena.objects.get().verificada)
        Resena.objects.all().delete()
        from garaje import servicio_taller as st
        st.confirmar(s)
        self.client.post(self.taller.get_absolute_url(), datos)
        r = Resena.objects.get()
        self.assertTrue(r.verificada)
        self.assertEqual(r.servicio_taller_id, s.pk)
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "Verificada")
        # el mismo servicio no sella una segunda reseña
        self.client.post(self.taller.get_absolute_url(), datos)
        self.assertEqual(Resena.objects.filter(verificada=True).count(), 1)

    def test_resena_abierta_sin_cuenta_no_es_verificada(self):
        self.client.post(self.taller.get_absolute_url(),
                         {"accion": "resena", "nombre": "X", "estrellas": 4, "comentario": "ok"})
        self.assertFalse(Resena.objects.get().verificada)


class DecisionesTests(Base):
    """Decisiones del coordinador: enlace con vencimiento, bloqueo en admin y cuentas, correo de precios."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.root = User.objects.create_superuser("root@t.co", "root@t.co", "clave-segura-123")
        cls.taller = Taller(nombre="Pend", responsable="R", whatsapp="573000000002", direccion="x", barrio=cls.barrio,
                            origen_alta=Taller.Alta.ASISTIDO)
        cls.taller.generar_token()
        cls.taller.save()

    def test_enlace_vence_a_los_30_dias_y_se_renueva(self):
        url = reverse("talleres:revisar_ficha", args=[self.taller.token_revision])
        self.assertEqual(self.client.get(url).status_code, 200)
        Taller.objects.filter(pk=self.taller.pk).update(token_creado=timezone.now() - timedelta(days=31))
        self.assertEqual(self.client.get(url).status_code, 410)
        self.client.force_login(self.admin)
        r = self.client.post(reverse("consola:accion", args=["talleres.renovar_enlace", self.taller.pk]), {"valor": "1"},
                             headers={"X-Requested-With": "fetch"})
        self.assertEqual(r.status_code, 200)
        self.taller.refresh_from_db()
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 404)  # el anterior ya no sirve
        self.assertEqual(self.client.get(reverse("talleres:revisar_ficha", args=[self.taller.token_revision])).status_code, 200)

    def test_admin_django_no_publica_sin_aprobacion(self):
        from .admin import TallerAdminForm
        form = TallerAdminForm(instance=self.taller, data={"activo": "on"})
        form.is_valid()
        self.assertIn("activo", form.errors)

    def test_cuentas_no_aprueba_sin_aprobacion(self):
        self.client.force_login(self.root)
        self.client.post(reverse("cuentas:aprobar_taller", args=[self.taller.pk]))
        self.taller.refresh_from_db()
        self.assertFalse(self.taller.activo)

    def test_registro_viejo_va_a_unete(self):
        self.assertRedirects(self.client.get(reverse("talleres:registro")), reverse("talleres:autoregistro"))


class CorreoPreciosTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        u = User.objects.create_user("dueno@t.co", "dueno@t.co", "x")
        cls.taller = Taller.objects.create(nombre="Taller", responsable="R", whatsapp="573000000003", direccion="x",
                                           barrio=cls.barrio, usuario=u, activo=True)
        cls.p = PrecioServicio.objects.create(taller=cls.taller, servicio=cls.servicio, desde=1, hasta=2)

    def correr(self):
        from django.core.management import call_command
        call_command("avisar_precios_vencidos", stdout=__import__("io").StringIO())

    def test_envia_una_vez_y_no_repite(self):
        from django.core import mail
        self.correr()
        self.assertEqual(len(mail.outbox), 0)  # precios al día
        PrecioServicio.objects.filter(pk=self.p.pk).update(actualizado=timezone.now() - timedelta(days=80))
        self.correr()
        self.correr()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["dueno@t.co"])
        # pasados 75 días de ese aviso y aún sin confirmar, vuelve a avisar
        Taller.objects.filter(pk=self.taller.pk).update(precios_aviso_enviado=timezone.now() - timedelta(days=80))
        self.correr()
        self.assertEqual(len(mail.outbox), 2)


class PanelPreciosTests(PreciosTests):
    """Panel del taller: estado de precios, interruptor rápido y «Por hacer»."""

    def test_panel_muestra_estado_e_interruptor(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("talleres:panel"))
        self.assertContains(r, "visibles en tu perfil")
        self.assertContains(r, "Servicio a domicilio") if r.context.get("mecanicos_activo") else None
        self.assertContains(r, "Registrar servicio")
        self.client.post(reverse("talleres:alternar_precios"), {"valor": "0"})
        self.taller.refresh_from_db()
        self.assertFalse(self.taller.mostrar_precios)
        self.assertContains(self.client.get(reverse("talleres:panel")), "Cotiza por WhatsApp")
        self.client.post(reverse("talleres:alternar_precios"), {"valor": "1"})
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.mostrar_precios)

    def test_panel_avisa_precios_por_vencer_y_exige_post(self):
        self.envejecer(80)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("talleres:panel")), "más de 2 meses")
        self.assertEqual(self.client.get(reverse("talleres:alternar_precios")).status_code, 405)
