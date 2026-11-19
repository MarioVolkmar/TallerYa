"""Pruebas de las secciones Talleres, Cupones, Citas y Moderación, y del comando sembrar_demo."""
import os
import tempfile
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings, tag
from django.urls import reverse

from cupones.models import CodigoCupon, Cupon, Motociclista
from foro.models import Pregunta, Reporte, Respuesta
from talleres.models import Barrio, Resena, SolicitudCita, Taller

from . import reloj
from .models import Bitacora
from .tests import INICIO, Base

User = get_user_model()


def accion(clave, pk):
    return reverse("consola:accion", args=[clave, pk])


class TalleresTests(Base):
    def test_despublicar_sale_del_directorio_y_queda_en_bitacora(self):
        self.taller.activo = True
        self.taller.save()
        self.assertContains(self.client.get(reverse("talleres:directorio")), "Motos Ya")
        r = self.post("talleres.publicar", self.taller.pk, valor="0")
        self.assertTrue(r.json()["ok"])
        self.assertNotContains(self.client.get(reverse("talleres:directorio")), "Motos Ya")
        b = Bitacora.objects.get()
        self.assertEqual(b.frase, f"Despublicó el taller #{self.taller.pk} (Motos Ya)")
        self.assertEqual(b.cambios[0]["antes"], "Sí")

    def test_listado_filtra_por_aprobar(self):
        r = self.client.get(INICIO, {"seccion": "talleres", "estado": "por_aprobar"})
        self.assertContains(r, "Motos Ya")
        self.assertContains(self.client.get(INICIO, {"seccion": "talleres", "estado": "publicados"}), "No hay talleres")

    def test_eliminar_bloqueado_con_citas(self):
        SolicitudCita.objects.create(taller=self.taller, nombre="M", telefono="3001", moto="NKD",
                                     fecha_preferida=date(2026, 12, 1))
        r = self.post("talleres.eliminar", self.taller.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("1 cita", r.json()["error"])
        self.assertTrue(Taller.objects.filter(pk=self.taller.pk).exists())
        self.assertContains(self.client.get(INICIO, {"seccion": "talleres"}), "No se puede eliminar")

    def test_eliminar_sin_dependencias(self):
        pk = self.taller.pk
        self.assertTrue(self.post("talleres.eliminar", pk).json()["ok"])
        self.assertFalse(Taller.objects.filter(pk=pk).exists())
        self.assertEqual(Bitacora.objects.get().frase, f"Eliminó el taller #{pk} (Motos Ya)")


class CuponesTests(Base):
    def setUp(self):
        super().setUp()
        hoy = reloj.hoy()
        self.vigente = Cupon.objects.create(taller=self.taller, titulo="Vigente", valido_hasta=hoy + timedelta(days=5))
        self.vencido = Cupon.objects.create(taller=self.taller, titulo="Vencido", valido_hasta=hoy - timedelta(days=5))

    def test_filtros_y_desactivar(self):
        r = self.client.get(INICIO, {"seccion": "cupones", "estado": "vencidos"})
        self.assertContains(r, "Vencido")
        self.assertNotContains(r, "Vigente</span>")
        self.post("cupones.activo", self.vigente.pk, valor="0")
        self.vigente.refresh_from_db()
        self.assertFalse(self.vigente.activo)
        self.assertEqual(Bitacora.objects.get().frase, f"Desactivó el cupón #{self.vigente.pk} (Vigente)")
        self.assertContains(self.client.get(INICIO, {"seccion": "cupones", "estado": "desactivados"}), "Vigente")

    def test_con_codigos_no_se_borra(self):
        m = Motociclista.objects.get(usuario=self.motero)
        CodigoCupon.objects.create(cupon=self.vigente, motociclista=m)
        r = self.post("cupones.eliminar", self.vigente.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("desactívalo", r.json()["error"])
        self.assertTrue(self.post("cupones.eliminar", self.vencido.pk).json()["ok"])


class CitasTests(Base):
    def setUp(self):
        super().setUp()
        self.cita = SolicitudCita.objects.create(taller=self.taller, nombre="Mario", telefono="3001", moto="NKD",
                                                 fecha_preferida=date(2026, 12, 1), usuario=self.motero)

    def test_cancelar_exige_motivo_y_registra(self):
        self.assertEqual(self.post("citas.cancelar", self.cita.pk, motivo="x").status_code, 400)
        r = self.post("citas.cancelar", self.cita.pk, motivo="El taller cerró por obras")
        self.assertTrue(r.json()["ok"])
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "cancelada")
        b = Bitacora.objects.get()
        self.assertEqual(b.frase, f"Canceló la cita #{self.cita.pk} en Motos Ya")
        self.assertEqual({c["campo"] for c in b.cambios}, {"estado", "motivo"})
        self.assertEqual(self.post("citas.cancelar", self.cita.pk, motivo="Otra vez sí").status_code, 400)

    def test_filtro_por_estado(self):
        self.assertContains(self.client.get(INICIO, {"seccion": "citas", "estado": "pendiente"}), "#%d" % self.cita.pk)
        self.assertContains(self.client.get(INICIO, {"seccion": "citas", "estado": "atendida"}), "No hay citas")


class ModeracionTests(Base):
    def setUp(self):
        super().setUp()
        self.pregunta = Pregunta.objects.create(autor=self.motero, titulo="¿Aceite NKD?", cuerpo="x")
        self.respuesta = Respuesta.objects.create(pregunta=self.pregunta, autor=self.motero, cuerpo="Cada 2.000 km")
        self.resena = Resena.objects.create(taller=self.taller, nombre="Ana", estrellas=1, comentario="Malísimo")
        self.reporte = Reporte.objects.create(usuario=self.otro_admin, respuesta=self.respuesta, motivo="Spam")

    def test_reportes_ocultar_y_revisar(self):
        r = self.client.get(INICIO, {"seccion": "moderacion"})
        self.assertContains(r, "Reporte #%d" % self.reporte.pk)
        self.post("foro.respuesta_visible", self.respuesta.pk, valor="0")
        self.post("foro.reporte_revisado", self.reporte.pk)
        self.respuesta.refresh_from_db()
        self.assertFalse(self.respuesta.visible)
        frases = list(Bitacora.objects.order_by("pk").values_list("frase", flat=True))
        self.assertEqual(frases, [f"Ocultó la respuesta #{self.respuesta.pk} del foro",
                                  f"Marcó como revisado el reporte #{self.reporte.pk} del foro"])
        self.assertContains(self.client.get(INICIO, {"seccion": "moderacion"}), "No hay reportes sin revisar")

    def test_reporte_sobre_pregunta_se_muestra(self):
        otro = Reporte.objects.create(usuario=self.admin, pregunta=self.pregunta, motivo="Publicidad")
        r = self.client.get(INICIO, {"seccion": "moderacion"})
        self.assertContains(r, "Reporte #%d sobre" % otro.pk)
        self.assertContains(r, "¿Aceite NKD?")

    def test_resena_ocultar_y_eliminar(self):
        self.post("resenas.visible", self.resena.pk, valor="0")
        self.resena.refresh_from_db()
        self.assertFalse(self.resena.visible)
        r = self.client.get(INICIO, {"seccion": "moderacion", "tipo": "resenas", "estado": "ocultas"})
        self.assertContains(r, "Malísimo")
        self.assertTrue(self.post("resenas.eliminar", self.resena.pk).json()["ok"])
        self.assertFalse(Resena.objects.filter(pk=self.resena.pk).exists())

    def test_eliminar_pregunta_avisa_respuestas(self):
        r = self.client.get(INICIO, {"seccion": "moderacion", "tipo": "preguntas"})
        self.assertContains(r, "Tiene 1 respuesta: se borran.")
        self.assertTrue(self.post("foro.pregunta_eliminar", self.pregunta.pk).json()["ok"])
        self.assertFalse(Respuesta.objects.filter(pk=self.respuesta.pk).exists())

    def test_no_admin_no_modera(self):
        self.client.force_login(self.motero)
        self.assertEqual(self.post("foro.pregunta_visible", self.pregunta.pk, valor="0").status_code, 403)
        self.pregunta.refresh_from_db()
        self.assertTrue(self.pregunta.visible)


@tag("lenta")
class SembrarDemoTests(TestCase):
    @mock.patch.dict(os.environ, {"TALLERYA_CLAVE_PRUEBA": "clave-de-prueba-local"})
    def test_idempotente_y_cuentas_fijas(self):
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            call_command("sembrar_demo", "--forzar", verbosity=0)
            conteos = (Taller.objects.count(), Motociclista.objects.count(), SolicitudCita.objects.count(),
                       Cupon.objects.count(), Pregunta.objects.count(), User.objects.count())
            call_command("sembrar_demo", "--forzar", verbosity=0)
        self.assertEqual(conteos, (Taller.objects.count(), Motociclista.objects.count(), SolicitudCita.objects.count(),
                                   Cupon.objects.count(), Pregunta.objects.count(), User.objects.count()))
        self.assertGreaterEqual(conteos[0], 9)
        self.assertGreaterEqual(conteos[1], 18)
        admin = User.objects.get(email="admin@prueba.com")
        superadmin = User.objects.get(email="superadmin@prueba.com")
        self.assertTrue(admin.is_staff and not admin.is_superuser)
        self.assertTrue(superadmin.is_superuser)
        self.assertTrue(admin.check_password("clave-de-prueba-local"))
        self.assertTrue(Taller.objects.filter(usuario__email="taller@prueba.com").exists())
        self.assertTrue(Motociclista.objects.get(usuario__email="usuario@prueba.com").motos.exists())
        self.assertFalse(User.objects.filter(perfil__correo_verificado=False).exists())
        estados = set(SolicitudCita.objects.values_list("estado", flat=True))
        self.assertGreaterEqual(len(estados), 4)
        self.assertTrue(Cupon.objects.filter(activo=False).exists())

    def test_sin_debug_ni_forzar_se_niega(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("sembrar_demo", verbosity=0)


class CabeceraPorRolTests(Base):
    """La cabecera del administrador es corta; motero, taller y visitante tienen la suya (ver talleres/tests_navegacion.py)."""
    def cabecera(self):
        html = self.client.get(reverse("talleres:directorio")).content.decode()
        return html[html.index('id="cabecera"'):html.index("</header>")]

    def test_admin_ve_solo_lo_suyo(self):
        c = self.cabecera()
        for texto in ("Consola</a>", "?seccion=usuarios", "?seccion=talleres", "?seccion=moderacion", "Ver sitio"):
            self.assertIn(texto, c)
        for texto in ("Mi garaje", "Mis insignias", "SOAT", "Rodadas", "¿Te varaste?", "Diagnóstico", ">Plus", "Admin técnico"):
            self.assertNotIn(texto, c)

    def test_superadmin_ademas_ve_admin_tecnico(self):
        User.objects.filter(pk=self.admin.pk).update(is_superuser=True)
        self.assertIn("Admin técnico", self.cabecera())

    def test_motero_y_visitante_sin_cambios(self):
        self.client.force_login(self.motero)
        c = self.cabecera()
        self.assertIn("Mi garaje", c)
        self.assertIn("SOAT", c)
        self.assertNotIn("Consola", c)
        self.client.logout()
        c = self.cabecera()
        self.assertIn("Crear cuenta", c)
        self.assertNotIn("Mi garaje", c)  # el visitante ve Talleres, Comunidad, Emergencias, Entrar y Crear cuenta
        self.assertNotIn("Consola", c)

    def test_taller_sin_cambios(self):
        self.taller.usuario = self.motero
        self.taller.save()
        self.client.force_login(self.motero)
        c = self.cabecera()
        self.assertIn("Validar cupón", c)
        self.assertNotIn("Consola", c)
