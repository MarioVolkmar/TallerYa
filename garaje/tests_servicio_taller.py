"""Lado del taller: citas con aviso al motero, servicio hecho → hoja de vida verificada + plan, placa con consentimiento."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from notificaciones.models import Notificacion
from talleres.models import Barrio, Resena, SolicitudCita, Taller

from . import servicio_taller as st
from .hoja_vida import generar_codigo
from .models import Mantenimiento, RegistroServicio, ServicioTaller, TareaMantenimiento
from .tests_avisos import crear_moto


class LadoTallerTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.duenio_taller = User.objects.create_user("t@taller.co", "t@taller.co", "x")
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        self.taller = Taller.objects.create(nombre="Motos Belén", responsable="A", whatsapp="573001112233",
                                            direccion="X", barrio=barrio, activo=True, usuario=self.duenio_taller)
        self.moto = crear_moto(placa="ABC12D", km_actual=5000)
        self.motero = self.moto.motociclista.usuario
        self.hoy = timezone.localdate()
        self.cita = SolicitudCita.objects.create(taller=self.taller, nombre="Ana", telefono="3001110000", moto="Yamaha NMAX",
                                                 fecha_preferida=self.hoy, usuario=self.motero,
                                                 estado=SolicitudCita.Estado.CONFIRMADA)
        self.tareas = st.tareas_de(self.moto)[:2]
        if len(self.tareas) < 2:  # por si la base de pruebas no trae el plan sembrado
            self.tareas = [TareaMantenimiento.objects.create(clave=f"t{i}", nombre=f"Tarea {i}", pieza="aceite",
                                                             intervalo_km=3000) for i in range(2)]
        self.client.force_login(self.duenio_taller)

    def _avisos(self, usuario):
        return list(Notificacion.objects.filter(usuario=usuario).values_list("titulo", flat=True))

    def test_confirmar_cita_avisa_al_motero(self):
        self.cita.estado = SolicitudCita.Estado.PENDIENTE
        self.cita.save()
        self.client.post(reverse("talleres:cita_estado", args=[self.cita.pk]), {"estado": "confirmada"})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "confirmada")
        self.assertIn("Motos Belén confirmó tu cita", self._avisos(self.motero))

    def test_citas_hoy_proximas_pasadas(self):
        SolicitudCita.objects.create(taller=self.taller, nombre="Luis", telefono="3002220000", moto="Pulsar",
                                     fecha_preferida=self.hoy + timedelta(days=3))
        SolicitudCita.objects.create(taller=self.taller, nombre="Rosa", telefono="3003330000", moto="Boxer",
                                     fecha_preferida=self.hoy - timedelta(days=3), estado="atendida")
        url = reverse("talleres:citas_taller")
        r = self.client.get(url)  # hay citas hoy: arranca en «Hoy»
        self.assertContains(r, "Ana")
        self.assertNotContains(r, "Luis")
        self.assertContains(self.client.get(url, {"estado": "proximas"}), "Luis")
        r = self.client.get(url, {"estado": "pasadas"})
        self.assertContains(r, "Rosa")
        self.assertNotContains(r, "Luis")

    def test_servicio_desde_cita_verifica_y_pone_al_dia_el_plan(self):
        url = reverse("talleres:servicio_cita", args=[self.cita.pk])
        r = self.client.get(url)
        self.assertContains(r, self.tareas[0].nombre)
        r = self.client.post(url, {"guardar": "1", "moto": self.moto.pk, "tareas": [t.pk for t in self.tareas],
                                   "otros": "Ajuste de clutch", "km": 5400, "fecha": self.hoy.isoformat(),
                                   "costo": "120.000", "notas": "Pastillas traseras a la mitad"}, follow=True)
        self.assertContains(r, "Registrado y verificado")
        s = ServicioTaller.objects.get()
        self.assertEqual((s.estado, s.origen), ("verificado", "cita"))
        registros = RegistroServicio.objects.filter(moto=self.moto)
        self.assertEqual(registros.count(), 3)  # una por tarea del plan + otros trabajos
        self.assertTrue(all(r.verificado and r.taller_id == self.taller.pk for r in registros))
        self.assertEqual(sum(r.costo or 0 for r in registros), 120000)  # el valor no se duplica en los gastos
        self.assertEqual(Mantenimiento.objects.filter(moto=self.moto, taller=self.taller).count(), 2)
        self.moto.refresh_from_db()
        self.cita.refresh_from_db()
        self.assertEqual((self.moto.km_actual, self.cita.estado), (5400, "atendida"))
        self.assertIn("Motos Belén registró el servicio de tu moto", self._avisos(self.motero))
        # El dueño ve el detalle con la invitación a calificar, y el enlace abre la reseña
        self.client.force_login(self.motero)
        r = self.client.get(s.get_absolute_url())
        self.assertContains(r, "Calificar a Motos Belén")
        self.assertContains(self.client.get(self.taller.get_absolute_url(), {"calificar": "1"}),
                            'document.getElementById("dialogo-resena").showModal()')
        Resena.objects.create(taller=self.taller, usuario=self.motero, nombre="Ana", estrellas=5, comentario="Bien")
        self.assertNotContains(self.client.get(s.get_absolute_url()), "Calificar a Motos Belén")

    def test_verifica_el_ya_lo_hice_del_dueno_sin_duplicar(self):
        previo = Mantenimiento.objects.create(moto=self.moto, tarea=self.tareas[0], km=5300, fecha=self.hoy)
        st.crear(self.taller, self.moto, origen="cita", cita=self.cita, fecha=self.hoy, km=5400,
                 tareas=[self.tareas[0]])
        self.assertEqual(Mantenimiento.objects.filter(moto=self.moto, tarea=self.tareas[0]).count(), 1)
        previo.refresh_from_db()
        self.assertEqual((previo.km, previo.taller_id), (5400, self.taller.pk))
        self.assertTrue(RegistroServicio.objects.get(moto=self.moto).verificado)

    def test_sin_tareas_ni_otros_no_se_guarda(self):
        r = self.client.post(reverse("talleres:servicio_cita", args=[self.cita.pk]),
                             {"guardar": "1", "km": 5400, "fecha": self.hoy.isoformat()})
        self.assertContains(r, "Marca al menos un trabajo")
        self.assertFalse(ServicioTaller.objects.exists())

    def test_codigo_qr_verifica_y_gasta_el_codigo(self):
        codigo = generar_codigo(self.moto).codigo
        url = reverse("talleres:registrar_servicio")
        self.assertContains(self.client.get(url, {"codigo": codigo}), "NMAX")
        datos = {"guardar": "1", "codigo": codigo, "otros": "Cambio de aceite", "km": 5100, "fecha": self.hoy.isoformat()}
        self.assertContains(self.client.post(url, datos, follow=True), "Registrado y verificado")
        self.assertTrue(RegistroServicio.objects.get(moto=self.moto).verificado)
        self.assertEqual(self.client.post(url, datos).status_code, 200)  # el código ya se usó
        self.assertEqual(ServicioTaller.objects.count(), 1)

    def test_placa_espera_al_dueno_y_el_dueno_confirma(self):
        url = reverse("talleres:registrar_servicio")
        r = self.client.get(url, {"placa": "abc-12d"})
        self.assertContains(r, "El dueño recibe un aviso")
        self.assertNotContains(r, "ana@x.com")
        self.client.post(url, {"guardar": "1", "placa": "ABC12D", "moto": self.moto.pk, "tareas": [self.tareas[0].pk],
                               "km": 5200, "fecha": self.hoy.isoformat()})
        s = ServicioTaller.objects.get()
        self.assertEqual(s.estado, "por_confirmar")
        self.assertFalse(RegistroServicio.objects.filter(moto=self.moto).exists())  # nada sin consentimiento
        self.assertIn("Motos Belén quiere anotar un servicio en tu moto", self._avisos(self.motero))
        self.client.force_login(self.motero)
        self.client.post(s.get_absolute_url(), {"accion": "confirmar"})
        s.refresh_from_db()
        self.assertEqual(s.estado, "verificado")
        self.assertTrue(RegistroServicio.objects.get(moto=self.moto).verificado)
        self.assertTrue(Notificacion.objects.filter(usuario=self.duenio_taller, clave=f"servicio-confirmado:{s.pk}").exists())

    def test_dueno_no_reconoce_y_se_quita_de_hoja_y_plan(self):
        s = st.crear(self.taller, self.moto, origen="cita", cita=self.cita, fecha=self.hoy, km=5400,
                     tareas=self.tareas, otros="Lavado")
        self.client.force_login(self.motero)
        self.client.post(s.get_absolute_url(), {"accion": "rechazar"})
        s.refresh_from_db()
        self.assertEqual(s.estado, "rechazado")
        self.assertFalse(RegistroServicio.objects.filter(moto=self.moto).exists())
        self.assertFalse(Mantenimiento.objects.filter(moto=self.moto).exists())

    def test_otro_usuario_no_ve_el_servicio_ni_otro_taller_la_cita(self):
        s = st.crear(self.taller, self.moto, origen="cita", cita=self.cita, fecha=self.hoy, km=5400, otros="Lavado",
                     tareas=[])
        self.assertEqual(self.client.get(s.get_absolute_url()).status_code, 404)  # el taller no es el dueño
        otro = get_user_model().objects.create_user("o@x.co", "o@x.co", "x")
        Taller.objects.create(nombre="Otro", responsable="B", whatsapp="573001112244", direccion="X",
                              barrio=self.taller.barrio, usuario=otro)
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse("talleres:servicio_cita", args=[self.cita.pk])).status_code, 404)

    def test_panel_resume_semana_servicios_y_calificacion(self):
        st.crear(self.taller, self.moto, origen="cita", cita=self.cita, fecha=self.hoy, km=5400, otros="Lavado", tareas=[])
        Resena.objects.create(taller=self.taller, nombre="Ana", estrellas=4, comentario="Bien")
        r = self.client.get(reverse("talleres:panel"))
        self.assertEqual(r.context["resumen"]["citas_semana"], 1)
        self.assertEqual(r.context["resumen"]["servicios_mes"], 1)
        self.assertContains(r, "Servicios registrados")
        self.assertContains(self.client.get(reverse("talleres:servicios_taller")), "Lavado")
