"""Herramientas del negocio («Mi día»): agenda, motos en el taller y recordatorios, para taller y mecánico a domicilio."""
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from consola.models import Ajuste
from cupones.models import Motociclista
from domicilio.models import MecanicoDomicilio, SolicitudVisita
from garaje.models import Moto, ServicioTaller, TrabajoEnCurso
from notificaciones.models import Notificacion
from talleres import herramientas as h
from talleres.models import Barrio, Servicio, SolicitudCita, Taller

User = get_user_model()


def plan_falso(*tareas):
    """calcular_plan de mentiras: las tareas dadas «tocan ya»."""
    items = [SimpleNamespace(tarea=SimpleNamespace(pk=i, nombre=n, servicio_id=None), ultimo_km=0) for i, n in enumerate(tareas, 1)]
    return lambda moto, hoy=None, **k: SimpleNamespace(urgentes=items, pronto=[])


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.frenos = Servicio.objects.get_or_create(nombre="Frenos")[0]
        cls.u_taller = User.objects.create_user("t@x.co", "t@x.co", "clave-larga-t1")
        cls.taller = Taller.objects.create(nombre="Taller Uno", responsable="T", whatsapp="573001112233", direccion="Cra 1",
                                           barrio=barrio, activo=True, usuario=cls.u_taller)
        cls.taller.servicios.add(cls.frenos)
        cls.u_mec = User.objects.create_user("m@x.co", "m@x.co", "clave-larga-m1")
        cls.mec = MecanicoDomicilio.objects.create(usuario=cls.u_mec, nombre="Mecánico Uno", whatsapp="573009998877",
                                                   estado=MecanicoDomicilio.Estado.APROBADO)
        cls.u_motero = User.objects.create_user("a@x.co", "a@x.co", "clave-larga-a1")
        cls.motero = Motociclista.objects.create(usuario=cls.u_motero, nombre="Ana", celular="573001110001")
        cls.moto = Moto.objects.create(motociclista=cls.motero, placa="AAA11A", marca_otra="Yamaha", linea_otra="NMAX",
                                       tipo_otra="scooter", modelo=2022, km_inicial=1000, km_actual=5000)
        cls.hoy = timezone.localdate()

    def setUp(self):
        from consola.ajustes import invalidar
        invalidar()  # el interruptor va a una caché corta: que una prueba que lo apaga no afecte a las demás


class InterruptorTests(Base):
    def test_apagado_da_404_y_sale_del_menu(self):
        self.client.force_login(self.u_taller)
        self.assertContains(self.client.get(reverse("talleres:panel")), 'href="/mi-negocio/"')
        Ajuste.objects.create(clave="herramientas_activo", valor=False)
        from consola.ajustes import invalidar
        invalidar()
        self.assertEqual(self.client.get(reverse("talleres:mi_dia")).status_code, 404)
        self.assertNotContains(self.client.get(reverse("talleres:panel")), 'href="/mi-negocio/"')

    def test_motero_no_entra(self):
        self.client.force_login(self.u_motero)
        self.assertEqual(self.client.get(reverse("talleres:mi_dia")).status_code, 404)

    def test_sin_sesion_va_a_entrar(self):
        self.assertEqual(self.client.get(reverse("talleres:mi_dia")).status_code, 302)


class AgendaTests(Base):
    def test_taller_ve_sus_citas_por_dia(self):
        SolicitudCita.objects.create(taller=self.taller, nombre="Beto", telefono="3001110002", moto="FZ", servicio=self.frenos,
                                     fecha_preferida=self.hoy, estado="confirmada")
        SolicitudCita.objects.create(taller=self.taller, nombre="Caro", telefono="3001110003", moto="CB",
                                     fecha_preferida=self.hoy + timedelta(days=2))
        SolicitudCita.objects.create(taller=self.taller, nombre="Vieja", telefono="3001110004", moto="CB",
                                     fecha_preferida=self.hoy + timedelta(days=9))
        ag = h.agenda(self.taller, self.hoy)
        self.assertEqual(ag["total"], 2)
        self.assertEqual([i["nombre"] for i in ag["dias"][0]["items"]], ["Beto"])
        self.client.force_login(self.u_taller)
        r = self.client.get(reverse("talleres:mi_dia"))
        self.assertContains(r, "Beto")
        self.assertContains(r, "Llegó: recibir moto")
        self.assertNotContains(r, "Vieja")

    def test_taller_anota_cita_y_avisa_al_motero_con_cuenta(self):
        self.client.force_login(self.u_taller)
        r = self.client.post(reverse("talleres:mi_dia_cita"), {
            "nombre": "Ana", "telefono": "300 111 0001", "moto": "NMAX", "servicio": str(self.frenos.pk),
            "fecha": (self.hoy + timedelta(days=1)).isoformat(), "hora": "09:30"})
        self.assertRedirects(r, reverse("talleres:mi_dia") + "#agenda", fetch_redirect_response=False)
        c = SolicitudCita.objects.get(taller=self.taller)
        self.assertEqual((c.estado, c.usuario, c.servicio, c.telefono), ("confirmada", self.u_motero, self.frenos, "3001110001"))
        self.assertTrue(c.token)
        self.assertTrue(Notificacion.objects.filter(usuario=self.u_motero, clave=f"cita-agendada:{c.pk}").exists())

    def test_no_anota_en_dias_pasados(self):
        self.client.force_login(self.u_taller)
        self.client.post(reverse("talleres:mi_dia_cita"), {"nombre": "X", "telefono": "3001110009", "moto": "NMAX",
                                                           "fecha": (self.hoy - timedelta(days=1)).isoformat()})
        self.assertFalse(SolicitudCita.objects.exists())

    def test_mecanico_anota_visita_y_ve_las_sin_fecha(self):
        SolicitudVisita.objects.create(mecanico=self.mec, nombre="Sin fecha", telefono="3001110005", moto="Boxer")
        self.client.force_login(self.u_mec)
        self.client.post(reverse("talleres:mi_dia_cita"), {"nombre": "Dani", "telefono": "3001110006", "moto": "Pulsar",
                                                           "fecha": self.hoy.isoformat()})
        v = SolicitudVisita.objects.get(nombre="Dani")
        self.assertEqual((v.estado, v.fecha_propuesta), ("confirmada", self.hoy))
        r = self.client.get(reverse("talleres:mi_dia"))
        self.assertContains(r, "Por acordar fecha")
        self.assertContains(r, "Trabajos en curso")
        self.assertContains(r, "Empezar trabajo")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TrabajosTests(Base):
    def test_recibir_desde_cita_y_marcar_lista_avisa_con_correo_de_respaldo(self):
        cita = SolicitudCita.objects.create(taller=self.taller, nombre="Ana", telefono="3001110001", moto="NMAX",
                                            fecha_preferida=self.hoy, estado="confirmada", usuario=self.u_motero, token="tok-1")
        self.client.force_login(self.u_taller)
        self.client.post(reverse("talleres:mi_dia_recibir"), {"cita": cita.pk})
        self.client.post(reverse("talleres:mi_dia_recibir"), {"cita": cita.pk})  # doble toque: no duplica
        t = TrabajoEnCurso.objects.get()
        self.assertEqual((t.taller, t.cita, t.usuario, t.estado), (self.taller, cita, self.u_motero, "recibida"))
        self.client.post(reverse("talleres:mi_dia_trabajo", args=[t.pk]), {"estado": "reparacion"})
        self.client.post(reverse("talleres:mi_dia_trabajo", args=[t.pk]), {"estado": "lista", "nota": "Le cambiamos pastillas"})
        t.refresh_from_db()
        self.assertEqual(t.estado, "lista")
        self.assertIsNotNone(t.avisado_en)
        n = Notificacion.objects.get(usuario=self.u_motero, clave=f"trabajo-listo:{t.pk}")
        self.assertIn("Le cambiamos pastillas", n.texto)
        self.assertEqual(n.url, reverse("cuentas:cita", args=[cita.pk]))  # con cuenta: el detalle en «Mis citas»
        self.assertEqual(len(mail.outbox), 1)  # sin push activo: correo de respaldo
        # volver a «lista» no repite el aviso
        h.cambiar_estado(t, "reparacion"); h.cambiar_estado(t, "lista")
        self.assertEqual(Notificacion.objects.filter(clave__startswith="trabajo-listo:").count(), 1)

    def test_entregar_lleva_a_registrar_servicio_de_la_cita(self):
        cita = SolicitudCita.objects.create(taller=self.taller, nombre="Ana", telefono="3001110001", moto="NMAX",
                                            fecha_preferida=self.hoy, estado="confirmada")
        t = h.recibir(self.taller, cita=cita)
        h.cambiar_estado(t, "lista")
        self.client.force_login(self.u_taller)
        r = self.client.post(reverse("talleres:mi_dia_trabajo", args=[t.pk]), {"estado": "entregada"})
        self.assertRedirects(r, reverse("talleres:servicio_cita", args=[cita.pk]), fetch_redirect_response=False)
        t.refresh_from_db()
        self.assertIsNotNone(t.entregada_en)

    def test_mecanico_recibe_sin_cita_y_otro_negocio_no_lo_toca(self):
        self.client.force_login(self.u_mec)
        self.client.post(reverse("talleres:mi_dia_recibir"), {"nombre": "Ana", "telefono": "3001110001", "moto": "NMAX", "que": "Aceite"})
        t = TrabajoEnCurso.objects.get()
        self.assertEqual((t.mecanico, t.usuario), (self.mec, self.u_motero))
        self.client.force_login(self.u_taller)
        self.assertEqual(self.client.post(reverse("talleres:mi_dia_trabajo", args=[t.pk]), {"estado": "lista"}).status_code, 404)
        # el taller tampoco puede recibir una visita del mecánico
        v = SolicitudVisita.objects.create(mecanico=self.mec, nombre="X", telefono="3001110005", estado="confirmada")
        self.assertEqual(self.client.post(reverse("talleres:mi_dia_recibir"), {"visita": v.pk}).status_code, 404)

    def test_sin_cuenta_no_avisa_y_ofrece_whatsapp(self):
        t = h.recibir(self.taller, datos={"nombre": "Pepe", "telefono": "3209998877", "moto": "AKT"})
        self.assertEqual(h.cambiar_estado(t, "lista"), [])
        self.assertFalse(Notificacion.objects.filter(clave__startswith="trabajo-listo:").exists())
        self.client.force_login(self.u_taller)
        r = self.client.get(reverse("talleres:mi_dia"))
        self.assertContains(r, "wa.me/573209998877")
        self.assertEqual(h.tareas_panel(self.taller)[0]["boton"], "Ver")


class RecordatoriosTests(Base):
    def test_avisa_a_los_clientes_del_ultimo_negocio_una_vez(self):
        ServicioTaller.objects.create(taller=self.taller, moto=self.moto, km=4000, origen="cita", estado="verificado",
                                      fecha=self.hoy - timedelta(days=200))
        with mock.patch("garaje.plan.calcular_plan", plan_falso("Cambio de aceite")):
            self.assertEqual(len(h.clientes_que_les_toca(self.taller)), 1)
            self.assertEqual(h.clientes_que_les_toca(self.mec), [])
            call_command("recordar_clientes", stdout=StringIO())
            call_command("recordar_clientes", stdout=StringIO())
        n = Notificacion.objects.get(usuario=self.u_motero, clave__startswith="negocio-recordatorio:")
        self.assertIn("Taller Uno", n.texto)
        self.assertIn("?agendar=1", n.url)

    def test_si_el_ultimo_servicio_fue_con_otro_no_le_escribe(self):
        ServicioTaller.objects.create(taller=self.taller, moto=self.moto, km=4000, origen="cita", estado="verificado",
                                      fecha=self.hoy - timedelta(days=200))
        ServicioTaller.objects.create(mecanico=self.mec, moto=self.moto, km=4500, origen="visita", estado="verificado",
                                      fecha=self.hoy - timedelta(days=100))
        with mock.patch("garaje.plan.calcular_plan", plan_falso("Frenos")):
            self.assertEqual(h.clientes_que_les_toca(self.taller), [])
            self.client.force_login(self.u_mec)
            r = self.client.post(reverse("talleres:mi_dia_recordar", args=[self.moto.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Notificacion.objects.filter(usuario=self.u_motero, clave__startswith="negocio-recordatorio:mecanico").exists())

    def test_apagado_el_comando_no_envia(self):
        Ajuste.objects.create(clave="herramientas_activo", valor=False)
        from consola.ajustes import invalidar
        invalidar()
        ServicioTaller.objects.create(taller=self.taller, moto=self.moto, km=4000, origen="cita", estado="verificado")
        with mock.patch("garaje.plan.calcular_plan", plan_falso("Frenos")):
            call_command("recordar_clientes", stdout=StringIO())
        self.assertFalse(Notificacion.objects.filter(clave__startswith="negocio-recordatorio:").exists())
