"""preparar_demo_prueba: limpia lo demo, deja las cuentas @prueba.com al 100 % y es idempotente."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings, tag

from cupones.models import Cupon
from domicilio.models import MecanicoDomicilio
from talleres import demo_prueba
from talleres.models import Barrio, Taller

MEDIA = tempfile.mkdtemp()


@tag("lenta")
@override_settings(MEDIA_ROOT=MEDIA)
class PrepararDemoPruebaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        demo = U.objects.create_user("viejo@demo.tallerya.test", "viejo@demo.tallerya.test", "x")
        Taller.objects.create(nombre="Taller Viejo Demo", usuario=demo, responsable="X", whatsapp="573000000000",
                              direccion="Calle 1", barrio=Barrio.objects.get_or_create(nombre="Centro", ciudad="Medellín")[0])
        U.objects.create_user("gente@gmail.com", "gente@gmail.com", "x")
        call_command("preparar_demo_prueba", "--forzar", verbosity=0)

    def test_borra_lo_demo_y_conserva_lo_demas(self):
        U = get_user_model()
        self.assertFalse(U.objects.filter(email__endswith="@demo.tallerya.test").exists())
        self.assertFalse(Taller.objects.filter(nombre="Taller Viejo Demo").exists())
        self.assertTrue(U.objects.filter(email="gente@gmail.com").exists())

    def test_cuentas_al_cien_y_verificadas(self):
        filas = demo_prueba.verificar()
        self.assertEqual(len(filas), 14)
        for correo, rol, pct, falta in filas:
            self.assertEqual((pct, falta), (100, []), correo)
        for u in get_user_model().objects.filter(email__endswith="@prueba.com"):
            self.assertTrue(u.perfil.correo_verificado and u.perfil.avatar_foto, u.email)

    def test_cantidades_y_cupones(self):
        self.assertEqual(Taller.objects.count(), 3)
        self.assertEqual(MecanicoDomicilio.objects.count(), 3)
        for t in Taller.objects.all():
            self.assertTrue(Cupon.objects.vigentes().filter(taller=t).exists(), t.nombre)
        for m in MecanicoDomicilio.objects.all():
            self.assertTrue(Cupon.objects.vigentes().filter(mecanico=m).exists(), m.nombre)

    def test_idempotente(self):
        antes = (Taller.objects.count(), MecanicoDomicilio.objects.count(), Cupon.objects.count(),
                 get_user_model().objects.count(), demo_prueba.verificar())
        call_command("preparar_demo_prueba", "--forzar", verbosity=0)
        despues = (Taller.objects.count(), MecanicoDomicilio.objects.count(), Cupon.objects.count(),
                   get_user_model().objects.count(), demo_prueba.verificar())
        self.assertEqual(antes, despues)

    def test_se_niega_sin_debug(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("preparar_demo_prueba", verbosity=0)
