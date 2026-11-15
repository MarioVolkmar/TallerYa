"""Subir la foto del SOAT o la técnico-mecánica desde la ficha, sin pasar por "Datos de la moto"."""
import shutil
import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import Motociclista
from garaje.models import LineaMoto, Moto


class SubirDocumentoTests(TestCase):
    PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()
        self.ajuste = override_settings(PRIVADO_ROOT=self.carpeta)
        self.ajuste.enable()
        self.usuario = User.objects.create_user("s@x.com", "s@x.com", "x")
        perfil = Motociclista.objects.create(nombre="S", celular="573001114466", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"), modelo=2024,
                                        km_inicial=0, km_actual=0, soat_vence=date.today() + timedelta(days=1))
        self.client.force_login(self.usuario)

    def tearDown(self):
        self.ajuste.disable()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def subir(self, nombre="soat.png", contenido=None, clave="soat"):
        url = reverse("garaje:subir_documento", args=[self.moto.pk, clave])
        return self.client.post(url, {"archivo": SimpleUploadedFile(nombre, contenido or self.PNG, "image/png")})

    def test_la_ficha_sube_aqui_mismo(self):
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, reverse("garaje:subir_documento", args=[self.moto.pk, "soat"]))

    def test_guarda_y_vuelve_a_la_ficha(self):
        r = self.subir()
        self.assertRedirects(r, f"{self.moto.get_absolute_url()}#documentos", fetch_redirect_response=False)
        self.moto.refresh_from_db()
        self.assertTrue(self.moto.soat_archivo)

    def test_reemplazar_borra_el_anterior(self):
        import os
        self.subir()
        self.moto.refresh_from_db()
        viejo = self.moto.soat_archivo.path
        self.subir("otro.png")
        self.assertFalse(os.path.exists(viejo))

    def test_rechaza_lo_que_no_es_imagen_ni_pdf(self):
        self.subir("virus.png", b"MZ" + b"0" * 64)
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.soat_archivo)

    def test_no_sirve_para_motos_ajenas(self):
        otro = User.objects.create_user("o@x.com", "o@x.com", "x")
        Motociclista.objects.create(nombre="O", celular="573001114477", usuario=otro)
        self.client.force_login(otro)
        self.assertEqual(self.subir().status_code, 404)

    def test_solo_post(self):
        self.assertEqual(self.client.get(reverse("garaje:subir_documento", args=[self.moto.pk, "soat"])).status_code, 405)
