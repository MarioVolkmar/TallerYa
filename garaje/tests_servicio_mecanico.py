"""Pruebas: el mecánico a domicilio deja servicios verificados en la hoja de vida, como un taller."""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from domicilio.models import MecanicoDomicilio, SolicitudVisita

from .hoja_vida import crear_enlace, generar_codigo
from .models import RegistroServicio, ServicioTaller
from .tests_avisos import crear_moto
from .tests_traspaso import crear_taller


def crear_mecanico(correo="meca@x.com", nombre="Andrés Moto Rápida", estado=MecanicoDomicilio.Estado.APROBADO):
    usuario = get_user_model().objects.create_user(correo, correo, "x")
    return MecanicoDomicilio.objects.create(nombre=nombre, whatsapp="573000000999", estado=estado, usuario=usuario)


class ServicioMecanicoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moto = crear_moto(placa="ABC12D", km_actual=8000)
        cls.dueno = cls.moto.motociclista.usuario
        cls.mecanico = crear_mecanico()

    def _solicitud(self, mecanico=None, usuario=None, estado=SolicitudVisita.Estado.CONFIRMADA):
        return SolicitudVisita.objects.create(mecanico=mecanico or self.mecanico, usuario=usuario, nombre="Ana",
                                              telefono="573001110000", moto="NMAX", estado=estado)

    def _datos(self, **extra):
        return {"guardar": "1", "km": 9000, "fecha": timezone.localdate().isoformat(), "otros": "Cambio de pastillas",
                "costo": "120.000", **extra}

    def test_desde_solicitud_con_cuenta_queda_verificado(self):
        s = self._solicitud(usuario=self.dueno)
        self.client.force_login(self.mecanico.usuario)
        url = reverse("garaje:servicio_visita", args=[s.pk])
        self.assertContains(self.client.get(url), "Registrar y verificar")
        r = self.client.post(url, self._datos(moto=self.moto.pk))
        self.assertRedirects(r, reverse("domicilio:solicitudes"), fetch_redirect_response=False)
        servicio = ServicioTaller.objects.get(solicitud=s)
        self.assertIsNone(servicio.taller)
        self.assertEqual(servicio.mecanico, self.mecanico)
        self.assertEqual(servicio.estado, ServicioTaller.Estado.VERIFICADO)
        registro = RegistroServicio.objects.get(servicio_taller=servicio)
        self.assertTrue(registro.verificado)
        self.assertEqual(registro.mecanico, self.mecanico)
        self.assertEqual(registro.donde, "Mecánico a domicilio: Andrés Moto Rápida")
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudVisita.Estado.ATENDIDA)
        # No se registra dos veces la misma visita
        self.client.post(url, self._datos(moto=self.moto.pk))
        self.assertEqual(ServicioTaller.objects.filter(solicitud=s).count(), 1)
        # La bandeja ya no ofrece el botón
        bandeja = self.client.get(reverse("domicilio:solicitudes") + "?ver=todas")
        self.assertContains(bandeja, "Servicio en su hoja de vida")

    def test_no_registra_en_solicitudes_ajenas_ni_pendientes(self):
        otro = crear_mecanico("otro@x.com", "Otro")
        ajena = self._solicitud(mecanico=otro, usuario=self.dueno)
        self.client.force_login(self.mecanico.usuario)
        url = reverse("garaje:servicio_visita", args=[ajena.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self._datos(moto=self.moto.pk)).status_code, 404)
        pendiente = self._solicitud(usuario=self.dueno, estado=SolicitudVisita.Estado.PENDIENTE)
        self.assertEqual(self.client.get(reverse("garaje:servicio_visita", args=[pendiente.pk])).status_code, 404)
        self.assertFalse(ServicioTaller.objects.exists())

    def test_mecanico_sin_aprobar_o_motero_no_registran(self):
        sin_aprobar = crear_mecanico("nuevo@x.com", "Nuevo", MecanicoDomicilio.Estado.PENDIENTE)
        s = self._solicitud(mecanico=sin_aprobar, usuario=self.dueno)
        for usuario in (sin_aprobar.usuario, self.dueno):
            self.client.force_login(usuario)
            r = self.client.post(reverse("garaje:servicio_visita", args=[s.pk]), self._datos(moto=self.moto.pk))
            self.assertEqual(r.status_code, 302)
        self.assertFalse(ServicioTaller.objects.exists())

    def test_con_codigo_un_solo_uso_sin_solicitud(self):
        codigo = generar_codigo(self.moto)
        self.client.force_login(self.mecanico.usuario)
        url = reverse("garaje:servicio_mecanico") + f"?codigo={codigo.codigo}"
        self.assertContains(self.client.get(url), "Registrar y verificar")
        self.client.post(url, self._datos(codigo=codigo.codigo, moto=self.moto.pk))
        self.assertEqual(ServicioTaller.objects.filter(mecanico=self.mecanico, origen="codigo").count(), 1)
        codigo.refresh_from_db()
        self.assertIsNotNone(codigo.usado)
        # Segundo uso: ya no sirve
        self.client.post(url, self._datos(codigo=codigo.codigo, moto=self.moto.pk))
        self.assertEqual(ServicioTaller.objects.count(), 1)
        self.assertContains(self.client.get(url), "no es válido o ya caducó")

    def test_solicitud_sin_cuenta_pide_codigo_y_queda_ligada(self):
        s = self._solicitud(usuario=None)
        self.client.force_login(self.mecanico.usuario)
        r = self.client.get(reverse("garaje:servicio_visita", args=[s.pk]))
        self.assertContains(r, "pídele el código de su hoja de vida")
        self.assertContains(r, f'name="visita" value="{s.pk}"')
        codigo = generar_codigo(self.moto)
        url = reverse("garaje:servicio_mecanico") + f"?codigo={codigo.codigo}&visita={s.pk}"
        self.client.post(url, self._datos(codigo=codigo.codigo, moto=self.moto.pk, visita=s.pk))
        self.assertTrue(ServicioTaller.objects.filter(solicitud=s, mecanico=self.mecanico).exists())
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudVisita.Estado.ATENDIDA)

    def test_aparece_en_hoja_de_vida_publica_y_certificado_sin_precio(self):
        s = self._solicitud(usuario=self.dueno)
        self.client.force_login(self.mecanico.usuario)
        self.client.post(reverse("garaje:servicio_visita", args=[s.pk]), self._datos(moto=self.moto.pk))
        enlace = crear_enlace(self.moto)
        self.client.force_login(self.dueno)
        urls = [reverse("garaje:hoja_vida", args=[self.moto.pk]), enlace.get_absolute_url(),
                reverse("garaje:hoja_vida_certificado", args=[enlace.token])]
        for url in urls:
            html = self.client.get(url).content.decode()
            self.assertIn("Mecánico a domicilio: Andrés Moto Rápida", html, url)
            self.assertNotIn("120.000", html, url)
        # El detalle del servicio también lo nombra
        servicio = ServicioTaller.objects.get(solicitud=s)
        self.assertContains(self.client.get(servicio.get_absolute_url()), "Andrés Moto Rápida")

    def test_restricciones_taller_o_mecanico(self):
        taller = crear_taller()
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroServicio.objects.create(moto=self.moto, km=1, servicios="x", taller=taller, mecanico=self.mecanico)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ServicioTaller.objects.create(moto=self.moto, km=1, origen="codigo")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ServicioTaller.objects.create(moto=self.moto, km=1, origen="codigo", taller=taller, mecanico=self.mecanico)
