"""Con un módulo apagado en /consola/, ninguna página principal enlaza a sus rutas (no solo da 404)."""
import re

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from cupones.models import Motociclista
from garaje.models import Moto
from notificaciones.models import Notificacion
from talleres.models import Barrio, Taller

from .ajustes import MODULOS
from .models import Ajuste

User = get_user_model()
PAGINAS = ("/", "/talleres/", "/cupones/", "/cuenta/", "/garaje/", "/diagnostico/", "/cuenta/registro/",
           "/cuenta/registro/?tipo=taller", "/mi-taller/", "/mi-taller/perfil/", "/notificaciones/", "/bienvenida/")
CON_RUTAS = [m for m in MODULOS if m.prefijos]


@override_settings(PILOTO_OCULTAR_SOCIAL=False)
class EnlacesDeModulosApagadosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.dueno = User.objects.create_user("t@t.co", "t@t.co", "clave-segura-123")
        Taller.objects.create(nombre="Taller Uno", responsable="A", whatsapp="573001112233", direccion="X",
                              barrio=barrio, activo=True, usuario=cls.dueno)
        cls.motero = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123", first_name="Mario")
        m = Motociclista.objects.create(nombre="Mario", celular="573009998877", usuario=cls.motero)
        cls.moto = Moto.objects.create(motociclista=m, marca_otra="Yamaha", linea_otra="NMAX", tipo_otra="scooter", modelo=2022,
                            km_inicial=0, km_actual=0)
        for u in ("/foro/", "/plus/", "/r/X/", "/mecanicos/"):
            Notificacion.objects.create(usuario=cls.motero, clave=f"t:{u}", titulo="Aviso", texto="x", url=u)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_cada_modulo_apagado_no_deja_enlaces(self):
        for modulo in CON_RUTAS:
            Ajuste.objects.all().delete()
            Ajuste.objects.create(clave=modulo.clave, valor=False)
            cache.clear()
            patron = re.compile(r'(?:href|action)="(?:%s)' % "|".join(re.escape(p) for p in modulo.prefijos))
            for usuario in (None, self.motero, self.dueno):
                self.client.logout()
                if usuario:
                    self.client.force_login(usuario)
                for pagina in PAGINAS + (f"/garaje/{self.moto.pk}/", f"/garaje/{self.moto.pk}/hoja-de-vida/"):
                    r = self.client.get(pagina)
                    if r.status_code != 200:
                        continue
                    html = r.content.decode()
                    malos = patron.findall(html)
                    self.assertFalse(malos, f"{modulo.clave}: {pagina} ({usuario}) aún enlaza {malos[:2]}")

    def test_control_con_todo_prendido_si_hay_enlaces(self):
        """Evita que la prueba pase en vacío: prendido, el menú sí enlaza a cada módulo."""
        self.client.force_login(self.motero)
        html = self.client.get("/").content.decode()
        for ruta in ("/foro/", "/plus/", "/mecanicos/"):
            self.assertIn(f'href="{ruta}', html)
        self.assertEqual(self.client.get("/cuenta/").status_code, 200)
        self.assertEqual(self.client.get(f"/garaje/{self.moto.pk}/").status_code, 200)


@override_settings(PILOTO_OCULTAR_SOCIAL=False)
class NumeracionSinForoTest(TestCase):
    """Con el foro apagado la numeración de secciones sigue seguida (sin saltar el 03 del foro)."""
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123", first_name="Mario")
        m = Motociclista.objects.create(nombre="Mario", celular="573009998877", usuario=cls.u)
        Moto.objects.create(motociclista=m, marca_otra="Yamaha", linea_otra="NMAX", tipo_otra="scooter", modelo=2022,
                            km_inicial=0, km_actual=0)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def numeros(self, url):
        html = self.client.get(url).content.decode()
        return re.findall(r'class="numero">(\d\d)<', html) + re.findall(r'class="ib-numero">(\d\d)<', html)

    def test_portada_sigue_01_02_03(self):
        Ajuste.objects.create(clave="foro_activo", valor=False)
        cache.clear()
        html = self.client.get("/").content.decode()
        nums = re.findall(r'class="numero">(\d\d)<', html)
        self.assertEqual(nums[:3], ["01", "02", "03"], nums)
        self.assertNotIn("04", nums[:3])

    def test_mi_cuenta_sin_foro_no_salta(self):
        Ajuste.objects.create(clave="foro_activo", valor=False)
        cache.clear()
        self.client.force_login(self.u)
        nums = [int(n) for n in self.numeros("/cuenta/")]
        self.assertEqual(sorted(set(nums)), list(range(min(nums), max(nums) + 1)), nums)
