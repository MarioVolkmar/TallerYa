"""Camino del motero (talleres/ciclo.py): cada paso deja el siguiente a un toque, para taller y mecánico a domicilio."""
from django.urls import reverse

from domicilio.models import ResenaMecanico, SolicitudVisita
from garaje import servicio_taller as st
from garaje.models import ServicioTaller, TrabajoEnCurso
from notificaciones.models import Notificacion
from talleres import ciclo
from talleres import herramientas as h
from talleres.models import Resena, SolicitudCita
from talleres.tests_herramientas import Base


class CicloTallerTests(Base):
    def _cita(self, **kw):
        datos = {"taller": self.taller, "nombre": "Ana", "telefono": "3001110001", "moto": "NMAX", "servicio": self.frenos,
                 "fecha_preferida": self.hoy, "usuario": self.u_motero, "token": "tok-cita-1"}
        datos.update(kw)
        return SolicitudCita.objects.create(**datos)

    def _pasos(self, pedido):
        e = ciclo.estado(pedido, self.u_motero)
        return {p["clave"]: ("hecho" if p["hecho"] else "actual" if p["actual"] else "") for p in e["pasos"]}, e

    def test_confirmar_avisa_con_enlace_a_mis_citas(self):
        cita = self._cita()
        self.client.force_login(self.u_taller)
        self.client.post(reverse("talleres:cita_estado", args=[cita.pk]), {"estado": "confirmada"})
        n = Notificacion.objects.get(usuario=self.u_motero, clave__startswith="cita-confirmada")
        self.assertEqual(n.url, reverse("cuentas:cita", args=[cita.pk]))

    def test_atendida_sin_servicio_pide_resena(self):
        cita = self._cita(estado="confirmada")
        self.client.force_login(self.u_taller)
        self.client.post(reverse("talleres:cita_estado", args=[cita.pk]), {"estado": "atendida"})
        n = Notificacion.objects.get(usuario=self.u_motero, clave=f"cita-atendida:{cita.pk}")
        self.assertEqual(n.url, self.taller.get_absolute_url() + "?calificar=1")

    def test_pasos_de_punta_a_punta(self):
        cita = self._cita(estado="reprogramada", fecha_propuesta=self.hoy, cotizacion_desde=50000, cotizacion_hasta=60000)
        pasos, e = self._pasos(cita)
        self.assertEqual(pasos["confirmada"], "actual")
        self.assertEqual(e["siguiente"]["url"], reverse("talleres:cita_publica", args=[cita.token]))
        cita.estado = "confirmada"
        cita.save()
        trabajo = h.recibir(self.taller, cita=cita)
        self.assertEqual(self._pasos(cita)[0]["taller"], "actual")
        h.cambiar_estado(trabajo, "lista")
        pasos, e = self._pasos(cita)
        self.assertEqual(pasos["lista"], "actual")
        self.assertIn("está lista", e["siguiente"]["nota"])
        # el aviso «lista» lleva al detalle de la cita en Mis citas
        self.assertEqual(Notificacion.objects.get(clave=f"trabajo-listo:{trabajo.pk}").url, reverse("cuentas:cita", args=[cita.pk]))
        st.crear(self.taller, self.moto, origen=ServicioTaller.Origen.CITA, fecha=self.hoy, km=5000, tareas=[], cita=cita)
        trabajo.refresh_from_db()
        self.assertEqual(trabajo.estado, TrabajoEnCurso.Estado.ENTREGADA)  # sale del tablero de «Mi día»
        pasos, e = self._pasos(cita)
        self.assertEqual(pasos["hoja"], "hecho")
        self.assertEqual(pasos["resena"], "actual")
        self.assertIn("?calificar=1", e["siguiente"]["url"])
        self.assertTrue(e["url_hoja"])
        Resena.objects.create(taller=self.taller, usuario=self.u_motero, nombre="Ana", estrellas=5, comentario="Bien")
        pasos, e = self._pasos(cita)
        self.assertEqual(pasos["resena"], "hecho")
        self.assertIsNone(e["siguiente"])

    def test_detalle_de_la_cita_muestra_pasos_y_calificar(self):
        cita = self._cita(estado="confirmada")
        st.crear(self.taller, self.moto, origen=ServicioTaller.Origen.CITA, fecha=self.hoy, km=5000, tareas=[], cita=cita)
        self.client.force_login(self.u_motero)
        r = self.client.get(reverse("cuentas:cita", args=[cita.pk]))
        self.assertContains(r, 'class="ciclo"')
        self.assertContains(r, f"Calificar a {self.taller.nombre}")
        self.assertContains(r, "Ver mi hoja de vida")
        r = self.client.get(reverse("talleres:cita_publica", args=[cita.token]))
        self.assertContains(r, "Cita atendida")
        self.assertContains(r, "Ver en Mis citas")

    def test_garaje_y_mis_citas_muestran_la_moto_en_el_taller(self):
        cita = self._cita(estado="confirmada")
        h.recibir(self.taller, cita=cita)
        self.client.force_login(self.u_motero)
        self.assertContains(self.client.get(reverse("garaje:moto", args=[self.moto.pk])), "Ver en qué va")
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), "Ver en qué va")


class CicloMecanicoTests(Base):
    def _visita(self, **kw):
        datos = {"mecanico": self.mec, "usuario": self.u_motero, "nombre": "Ana", "telefono": "3001110001", "moto": "NMAX"}
        datos.update(kw)
        return SolicitudVisita.objects.create(**datos)

    def test_visita_sale_en_mis_citas(self):
        v = self._visita(estado="cotizada", fecha_propuesta=self.hoy)
        self.client.force_login(self.u_motero)
        r = self.client.get(reverse("cuentas:mi_cuenta"))
        self.assertContains(r, v.get_absolute_url())
        self.assertContains(r, self.mec.nombre)

    def test_atendida_sin_servicio_pide_resena(self):
        v = self._visita(estado="confirmada", fecha_propuesta=self.hoy)
        self.client.force_login(self.u_mec)
        self.client.post(reverse("domicilio:solicitud_estado", args=[v.pk]), {"estado": "atendida"})
        n = Notificacion.objects.get(usuario=self.u_motero, clave=f"visita-atendida:{v.pk}")
        self.assertEqual(n.url, self.mec.get_absolute_url() + "?calificar=1")

    def test_ficha_abre_la_resena_con_calificar(self):
        self.client.force_login(self.u_motero)
        r = self.client.get(self.mec.get_absolute_url() + "?calificar=1")
        self.assertContains(r, 'data-abrir-resena="1"')
        self.assertContains(self.client.get(self.mec.get_absolute_url()), 'data-abrir-resena=""')

    def test_pagina_de_la_visita_lleva_a_calificar(self):
        v = self._visita(estado="confirmada", fecha_propuesta=self.hoy)
        st.crear(None, self.moto, origen=ServicioTaller.Origen.VISITA, fecha=self.hoy, km=5000, tareas=[],
                 mecanico=self.mec, solicitud=v)
        r = self.client.get(v.get_absolute_url())
        self.assertContains(r, "Visita atendida")
        self.assertContains(r, "?calificar=1")
        ResenaMecanico.objects.create(mecanico=self.mec, usuario=self.u_motero, nombre="Ana", estrellas=5, comentario="Bien")
        self.assertNotContains(self.client.get(v.get_absolute_url()), "?calificar=1")
