"""Pruebas del traspaso de la moto al venderla y del certificado imprimible de la hoja de vida."""
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from cupones.models import Motociclista
from notificaciones.models import Notificacion
from talleres.models import Barrio, Taller
from tramites.models import PedidoSoat

from . import traspaso
from .hoja_vida import crear_enlace, generar_codigo
from .models import EnlaceHojaVida, Gasto, Moto, RegistroServicio
from .tests_avisos import crear_moto


def crear_taller():
    barrio = Barrio.objects.first() or Barrio.objects.create(nombre="El Poblado")
    return Taller.objects.create(nombre="Motos El Poblado", responsable="X", whatsapp="573001234567",
                                 direccion="Cra 1", barrio=barrio, activo=True)


def crear_comprador(correo="beto@x.com", celular="573002220000"):
    usuario = get_user_model().objects.create_user(correo, correo, "x")
    Motociclista.objects.create(nombre="Beto", celular=celular, usuario=usuario)
    return usuario


class TraspasoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.taller = crear_taller()

    def setUp(self):
        self.privado = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.privado, ignore_errors=True)
        ajuste = override_settings(PRIVADO_ROOT=self.privado)
        ajuste.enable()
        self.addCleanup(ajuste.disable)
        self.moto = crear_moto(placa="ABC12D", apodo="La Negra", pico_placa_whatsapp=True,
                               soat_vence=timezone.localdate() + timedelta(days=90))
        self.vendedor = self.moto.motociclista.usuario
        self.comprador = crear_comprador()
        self.verificado = RegistroServicio.objects.create(moto=self.moto, km=4000, servicios="Cambio de aceite",
                                                          taller=self.taller, costo=85000)
        RegistroServicio.objects.filter(pk=self.verificado.pk).update(verificado=True)
        self.propio = RegistroServicio.objects.create(moto=self.moto, km=4500, servicios="Lavada de cadena",
                                                      costo=12000)
        Gasto.objects.create(moto=self.moto, valor=20000)

    def _enlace(self):
        self.client.force_login(self.vendedor)
        self.client.post(reverse("garaje:hoja_vida", args=[self.moto.pk]), {"accion": "vender"})
        return traspaso.vigente(self.moto)

    def _aceptar(self, t, usuario=None):
        self.client.force_login(usuario or self.comprador)
        return self.client.post(reverse("garaje:traspaso", args=[t.token]))

    def test_solo_el_dueno_crea_el_enlace(self):
        self.client.force_login(self.comprador)
        r = self.client.post(reverse("garaje:hoja_vida", args=[self.moto.pk]), {"accion": "vender"})
        self.assertEqual(r.status_code, 404)
        self.assertIsNone(traspaso.vigente(self.moto))

    def test_traspaso_completo(self):
        self.moto.soat_archivo.save("soat.pdf", ContentFile(b"%PDF-1"), save=True)
        ruta = Path(self.moto.soat_archivo.path)
        enlace = crear_enlace(self.moto)
        codigo = generar_codigo(self.moto)
        t = self._enlace()
        self.assertTrue(t.vigente)
        self.assertEqual(t.vence.date(), (timezone.now() + timedelta(days=7)).date())
        # El comprador ve qué recibe sin costos
        self.client.force_login(self.comprador)
        pagina = self.client.get(reverse("garaje:traspaso", args=[t.token]))
        self.assertContains(pagina, "Aceptar la moto")
        self.assertContains(pagina, "A••••D")
        self.assertNotContains(pagina, "85.000")
        self.assertNotContains(pagina, "ABC12D")

        r = self._aceptar(t)
        self.assertRedirects(r, reverse("garaje:hoja_vida", args=[self.moto.pk]))
        moto = Moto.objects.get(pk=self.moto.pk)
        self.assertEqual(moto.motociclista.usuario, self.comprador)
        self.assertIsNotNone(moto.dueno_desde)
        # Viaja el historial (verificado y propio) y la placa; SOAT y técnico-mecánica no (ni sus fechas)
        self.assertEqual(set(moto.hoja_vida.values_list("pk", flat=True)), {self.verificado.pk, self.propio.pk})
        self.assertTrue(moto.hoja_vida.get(pk=self.verificado.pk).verificado)
        self.assertEqual(moto.placa, "ABC12D")
        self.assertIsNone(moto.soat_vence)
        self.assertIsNone(moto.tecno_vence)
        # No viaja lo personal
        self.assertFalse(moto.gastos.exists())
        self.assertFalse(moto.hoja_vida.exclude(costo=None).exists())
        self.assertFalse(moto.soat_archivo)
        self.assertFalse(ruta.exists())
        self.assertEqual(moto.apodo, "")
        self.assertFalse(moto.pico_placa_whatsapp)
        # Enlaces públicos y códigos del taller revocados
        self.assertIsNotNone(EnlaceHojaVida.objects.get(pk=enlace.pk).revocado)
        codigo.refresh_from_db()
        self.assertFalse(codigo.vigente)
        self.assertEqual(self.client.get(enlace.get_absolute_url()).status_code, 404)
        # Avisos a los dos
        self.assertTrue(Notificacion.objects.filter(usuario=self.comprador, clave=f"traspaso-recibido:{t.pk}").exists())
        self.assertTrue(Notificacion.objects.filter(usuario=self.vendedor, clave=f"traspaso-entregado:{t.pk}").exists())

    def test_vendedor_ya_no_accede_y_comprador_si(self):
        self._aceptar(self._enlace())
        self.client.force_login(self.vendedor)
        # La ficha manda al garaje sin decir de quién es; las demás dan 404
        self.assertRedirects(self.client.get(reverse("garaje:moto", args=[self.moto.pk])),
                             reverse("garaje:garaje") + "?lista=1", fetch_redirect_response=False)
        for nombre in ("hoja_vida", "gastos", "editar"):
            self.assertEqual(self.client.get(reverse(f"garaje:{nombre}", args=[self.moto.pk])).status_code, 404,
                             nombre)
        self.assertNotContains(self.client.get(reverse("garaje:garaje")), "NMAX")
        self.client.force_login(self.comprador)
        r = self.client.get(reverse("garaje:hoja_vida", args=[self.moto.pk]))
        self.assertContains(r, "Cambio de aceite")
        self.assertContains(r, "Lavada de cadena")

    def test_un_solo_uso(self):
        t = self._enlace()
        self._aceptar(t)
        otro = crear_comprador("caro@x.com", "573003330000")
        r = self._aceptar(t, otro)
        self.assertEqual(r.status_code, 410)
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.comprador)
        self.assertEqual(self.client.get(reverse("garaje:traspaso", args=[t.token])).status_code, 410)

    def test_vencido_o_cancelado_no_sirve(self):
        t = self._enlace()
        t.vence = timezone.now() - timedelta(minutes=1)
        t.save()
        self._aceptar(t)
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.vendedor)
        t2 = self._enlace()
        self.client.post(reverse("garaje:hoja_vida", args=[self.moto.pk]), {"accion": "cancelar_traspaso"})
        self.assertEqual(self._aceptar(t2).status_code, 410)
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.vendedor)

    def test_generar_otro_anula_el_anterior(self):
        t1 = self._enlace()
        t2 = self._enlace()
        self.assertNotEqual(t1.token, t2.token)
        self.assertIsNone(traspaso.buscar(t1.token))

    def test_pide_sesion(self):
        t = self._enlace()
        self.client.logout()
        r = self.client.get(reverse("garaje:traspaso", args=[t.token]))
        self.assertEqual(r.status_code, 302)
        self.assertIn("next=", r.url)
        self.client.post(reverse("garaje:traspaso", args=[t.token]))
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.vendedor)

    def test_el_vendedor_no_se_la_acepta_a_si_mismo(self):
        t = self._enlace()
        self.assertContains(self.client.get(reverse("garaje:traspaso", args=[t.token])), "Este es tu enlace")
        self._aceptar(t, self.vendedor)
        self.assertTrue(traspaso.buscar(t.token))

    def test_comprador_sin_perfil_o_con_garaje_lleno(self):
        t = self._enlace()
        sin_perfil = get_user_model().objects.create_user("x@x.com", "x@x.com", "x")
        self._aceptar(t, sin_perfil)
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.vendedor)
        for i in range(5):
            Moto.objects.create(
                motociclista=self.comprador.motociclista, marca_otra="Honda", linea_otra=f"CB{i}", tipo_otra="calle",
                modelo=2020, km_inicial=1, km_actual=1)
        self.client.force_login(self.comprador)
        self.assertContains(self.client.get(reverse("garaje:traspaso", args=[t.token])), "Tu garaje está lleno")
        self._aceptar(t)
        self.assertEqual(Moto.objects.get(pk=self.moto.pk).motociclista.usuario, self.vendedor)
        self.assertTrue(traspaso.buscar(t.token))

    def test_pedido_de_soat_en_curso_bloquea_y_los_viejos_no_se_ven(self):
        datos = {"moto": self.moto, "placa": "ABC12D", "linea": "NMAX", "cilindraje": 155,
                 "categoria": "moto_100_200", "numero_documento": "71234567", "nombre_completo": "Ana Vendedora",
                 "correo": "ana@x.com", "direccion": "Calle 1", "celular": "3001110000",
                 "acepta_datos_en": timezone.now()}
        pedido = PedidoSoat.objects.create(**datos)
        self._enlace()
        self.assertIsNone(traspaso.vigente(self.moto))
        pedido.estado = PedidoSoat.Estado.EMITIDA
        pedido.save()
        self._aceptar(self._enlace())
        moto = Moto.objects.get(pk=self.moto.pk)
        self.assertFalse(moto.pedidos_soat_del_dueno().exists())
        self.client.force_login(self.comprador)
        r = self.client.get(reverse("tramites:poliza", args=[pedido.pk]))
        self.assertEqual(r.status_code, 404)


class CertificadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.taller = crear_taller()
        cls.moto = crear_moto(placa="XYZ98A", apodo="Mi Bebé", km_actual=12345,
                              linea_otra="NMAX Conectada", tecno_vence=timezone.localdate() + timedelta(days=200))
        r = RegistroServicio.objects.create(moto=cls.moto, km=10000, servicios="Kit de arrastre", taller=cls.taller,
                                            costo=350000)
        RegistroServicio.objects.filter(pk=r.pk).update(verificado=True)
        RegistroServicio.objects.create(moto=cls.moto, km=11000, servicios="Cambio de bujía", costo=25000)
        cls.enlace = crear_enlace(cls.moto)

    def test_certificado_publico_sin_datos_privados(self):
        url = reverse("garaje:hoja_vida_certificado", args=[self.enlace.token])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        html = r.content.decode()
        for esperado in ("TallerYa", "Imprimir / Guardar PDF", "X••••A", "Yamaha", "2022", "12.345",
                         "Kit de arrastre", "Motos El Poblado", "Verificado", "Propio", "Emitido el", "<svg",
                         self.enlace.get_absolute_url()):
            self.assertIn(esperado, html)
        for privado in ("XYZ98A", "350.000", "25.000", "Mi Bebé", "Ana", "ana@x.com", "573001110000",
                        'id="tecno"', "/documento/"):
            self.assertNotIn(privado, html)

    def test_enlace_revocado_no_da_certificado(self):
        enlace = EnlaceHojaVida.objects.create(moto=self.moto, revocado=timezone.now())
        self.assertEqual(self.client.get(reverse("garaje:hoja_vida_certificado", args=[enlace.token])).status_code,
                         404)

    def test_pagina_publica_y_del_dueno_enlazan_el_certificado(self):
        url = reverse("garaje:hoja_vida_certificado", args=[self.enlace.token])
        self.assertContains(self.client.get(self.enlace.get_absolute_url()), url)
        self.client.force_login(self.moto.motociclista.usuario)
        self.assertContains(self.client.get(reverse("garaje:hoja_vida", args=[self.moto.pk])), url)

    def test_pagina_publica_sin_precio_ni_tecno(self):
        html = self.client.get(self.enlace.get_absolute_url()).content.decode()
        for privado in ("350.000", "25.000", 'id="tecno"', "/documento/", "XYZ98A"):
            self.assertNotIn(privado, html)

    def test_dueno_ve_la_tecno_pero_no_el_precio(self):
        self.client.force_login(self.moto.motociclista.usuario)
        r = self.client.get(reverse("garaje:hoja_vida", args=[self.moto.pk]))
        self.assertContains(r, 'id="tecno"')
        self.assertContains(r, "Vigente")
        html = r.content.decode()
        self.assertNotIn("350.000", html)
        self.assertNotIn("25.000", html)
        self.assertNotIn("hv-costo", html)


class PapelesAlDiaTests(TestCase):
    """En lo compartido sale hasta cuándo están vigentes el SOAT y la técnico-mecánica (solo fecha y estado)."""
    def _html(self, moto):
        enlace = crear_enlace(moto)
        return [self.client.get(enlace.get_absolute_url()).content.decode(),
                self.client.get(reverse("garaje:hoja_vida_certificado", args=[enlace.token])).content.decode()]

    def test_vigente_y_vencido(self):
        hoy = timezone.localdate()
        moto = crear_moto(soat_vence=hoy + timedelta(days=30), tecno_vence=hoy - timedelta(days=3))
        soat, tecno = date_format(moto.soat_vence, "j M Y").lower(), date_format(moto.tecno_vence, "j M Y").lower()
        publica, cert = self._html(moto)
        self.assertIn(f"SOAT vigente hasta {soat}", publica)
        self.assertIn(f"Técnico-mecánica vencida desde {tecno}", publica)
        self.assertIn(f"Vigente hasta {soat}", cert)
        self.assertIn(f"Vencida desde {tecno}", cert)

    def test_sin_fecha_no_hay_linea_ni_archivos(self):
        moto = crear_moto("b@x.com", "573009990000")
        for html in self._html(moto):
            for texto in ("vigente hasta", "Vigente hasta", "vencido desde", "Vencido desde", "vencida desde", "Vencida desde", "sin dato", "Sin dato",
                          "/documento/"):
                self.assertNotIn(texto, html)
