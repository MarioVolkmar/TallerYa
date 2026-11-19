"""Talleres demo completos (cargar_demo) y videos en la galería del taller."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag
from django.urls import reverse

from garaje.models import LineaMoto, RegistroServicio, ServicioTaller
from garaje.tests_avisos import crear_moto

from . import demo_talleres
from .models import Barrio, FotoTaller, Servicio, Taller

MEDIOS = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIOS)
class TalleresDemoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIOS, ignore_errors=True)

    def test_perfiles_completos_e_idempotentes(self):
        creados = demo_talleres.cargar()
        self.assertEqual([t.nombre for t in creados], ["Taller Doble Leva", "Torque Sur Motos"])
        self.assertEqual(demo_talleres.cargar(), [])  # la segunda vez no duplica
        for t in creados:
            self.assertTrue(t.foto and t.activo and t.usuario and not t.usuario.has_usable_password())
            self.assertEqual(t.fotos.exclude(video="").count(), 1)
            self.assertGreaterEqual(t.precios.count(), 10)
            self.assertGreaterEqual(t.resenas.count(), 5)
            self.assertTrue(t.horarios.exists() and t.cupones.exists())
            r = self.client.get(t.get_absolute_url())
            self.assertContains(r, "perfil-video")
            self.assertContains(r, "Kit de arrastre")
        self.assertFalse(ServicioTaller.objects.exists())  # sin motos demo no hay servicios

    def test_citas_con_servicio_verificado_en_las_motos_demo(self):
        lineas = {n: LineaMoto.objects.filter(nombre=n).first() for n in ("NKD 125", "NMAX 155")}
        if not all(lineas.values()):
            self.skipTest("La base de pruebas no trae las líneas sembradas")
        nkd = crear_moto(celular="573009990001", linea=lineas["NKD 125"], km_actual=16050)
        perfil = nkd.motociclista
        nkd.__class__.objects.create(motociclista=perfil, linea=lineas["NMAX 155"], modelo=2024, km_inicial=3000,
                                     km_actual=4300)
        demo_talleres.cargar()
        self.assertEqual(set(ServicioTaller.objects.values_list("estado", flat=True)), {"verificado"})
        self.assertEqual(ServicioTaller.objects.count(), 2)
        self.assertTrue(RegistroServicio.objects.filter(moto=nkd, verificado=True, taller__nombre="Taller Doble Leva").exists())


@tag("lenta")  # carga el demo completo dos veces (~3 s): corre en la suite completa
@override_settings(MEDIA_ROOT=MEDIOS)
class ComandoCargarDemoTests(TestCase):
    def test_aguanta_cupones_repetidos_y_no_borra_nada(self):
        from io import StringIO

        from django.core.management import call_command

        from cupones.models import Cupon
        titulo = "$20.000 de descuento en cualquier taller aliado"
        Cupon.objects.create(titulo=titulo, condiciones="Mío")
        Cupon.objects.create(titulo=titulo, condiciones="Mío también")
        call_command("cargar_demo", stdout=StringIO())
        total = Cupon.objects.count()
        call_command("cargar_demo", stdout=StringIO())  # dos veces: no duplica
        self.assertEqual(Cupon.objects.count(), total)
        self.assertEqual(Cupon.objects.filter(condiciones__startswith="Mío").count(), 2)  # no borra lo del usuario
        self.assertEqual(Taller.objects.filter(nombre="Taller Doble Leva").count(), 1)
        self.assertEqual(Taller.objects.filter(nombre="Torque Sur Motos").count(), 1)
        self.assertEqual(Taller.objects.filter(nombre="Frenos y Más").count(), 1)


@override_settings(MEDIA_ROOT=MEDIOS)
class VideoGaleriaTests(TestCase):
    def setUp(self):
        self.u = get_user_model().objects.create_user("v@t.co", "v@t.co", "x")
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        self.taller = Taller.objects.create(nombre="Video Motos", responsable="A", whatsapp="573000000000",
                                            direccion="X", barrio=barrio, activo=True, usuario=self.u)
        self.client.force_login(self.u)

    def _post(self, archivo):
        servicio = Servicio.objects.get_or_create(nombre="Frenos")[0]
        datos = {"descripcion": "x", "horario": "", "servicios": [servicio.pk], "video": archivo}
        return self.client.post(reverse("talleres:editar_perfil"), datos, follow=True)

    def test_sube_video_mp4_y_sale_en_el_perfil(self):
        self._post(SimpleUploadedFile("taller.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4"))
        f = self.taller.fotos.get()
        self.assertTrue(f.video and not f.imagen)
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "perfil-video")

    def test_rechaza_video_que_no_es_mp4_ni_webm(self):
        r = self._post(SimpleUploadedFile("taller.avi", b"RIFF", content_type="video/x-msvideo"))
        self.assertContains(r, "no se subió")
        self.assertFalse(FotoTaller.objects.exists())

    def test_maximo_de_videos(self):
        for i in range(FotoTaller.MAXIMO_VIDEOS):
            FotoTaller.objects.create(taller=self.taller, video=f"talleres/videos/v{i}.mp4")
        r = self._post(SimpleUploadedFile("otro.mp4", b"x", content_type="video/mp4"))
        self.assertContains(r, "máximo")
        self.assertEqual(self.taller.fotos.count(), FotoTaller.MAXIMO_VIDEOS)
