"""Detalle del taller rediseñado e información estandarizada del perfil (equipo, especialidades, garantía, compromisos)."""
import json
import re
import shutil
import tempfile
from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import demo_talleres, perfil
from .models import Barrio, HorarioTaller, PrecioServicio, Servicio, Taller

MEDIOS = tempfile.mkdtemp()


def _taller(**extra):
    barrio = Barrio.objects.get_or_create(nombre="Laureles", ciudad="Medellín")[0]
    usuario = get_user_model().objects.create_user("t@x.co", "t@x.co", "x")
    datos = dict(nombre="Motos Laureles", responsable="A", whatsapp="573001112233", direccion="Cra 70 # 1-2",
                 barrio=barrio, activo=True, usuario=usuario)
    datos.update(extra)
    return Taller.objects.create(**datos)


@override_settings(MEDIA_ROOT=MEDIOS)
class DetalleRediseñoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIOS, ignore_errors=True)

    def test_orden_secciones_sin_fotos_duplicadas_ni_leyendas_en_miniaturas(self):
        taller = demo_talleres.cargar()[0]
        Taller.objects.filter(pk=taller.pk).update(mostrar_precios=True)
        html = self.client.get(taller.get_absolute_url()).content.decode()
        # La ubicación va justo después de los precios (pedido del usuario, 23-nov)
        claves = ["Mano de obra desde", "Ubicación", "Fotos del taller", "Quiénes te atienden", "Cómo trabajamos",
                  "id=\"resenas\""]
        posiciones = [html.index(k) for k in claves]
        self.assertEqual(posiciones, sorted(posiciones))
        self.assertIn("Ver las 5 fotos", html)
        self.assertNotIn("perfil-galeria", html)  # la sección «Fotos» repetida ya no está
        franja = html[html.index('class="perfil-franja'):html.index("Quiénes te atienden")]
        self.assertNotIn("Banco de trabajo</span>", franja)  # la leyenda solo sale en el visor
        self.assertIn("Jhon Fredy Ospina", html)
        self.assertIn("Garantía de 1 mes en mano de obra", html)
        self.assertIn("Inyección electrónica", html)
        ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertIn("Inyección electrónica", ld["knowsAbout"])
        self.assertEqual(ld["employee"][0]["name"], "Jhon Fredy Ospina")
        self.assertTrue(any(o["itemOffered"]["name"] == "Cambio de aceite" for o in ld["makesOffer"]))

    def test_taller_sin_datos_estandarizados_se_ve_bien(self):
        taller = _taller(descripcion="")
        r = self.client.get(taller.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Quiénes te atienden")
        self.assertNotContains(r, "Cómo trabajamos")
        self.assertContains(r, "aún no ha listado sus servicios")
        self.assertContains(r, "Ubicación")

    def test_tabla_de_precios_desde_por_cilindraje(self):
        taller = _taller(mostrar_precios=True)
        aceite = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        PrecioServicio.objects.create(taller=taller, servicio=aceite, cilindraje="baja", desde=38000, hasta=60000)
        PrecioServicio.objects.create(taller=taller, servicio=aceite, cilindraje="media", desde=70000, hasta=130000)
        r = self.client.get(taller.get_absolute_url())
        self.assertEqual(r.context["tabla_precios"]["columnas"], ["Hasta 150 cc", "150–400 cc"])
        self.assertContains(r, "$38.000")
        self.assertNotContains(r, "$60.000")  # solo el «desde»


class EstadoHorarioTests(TestCase):
    def test_abierto_cerrado_y_proxima_apertura(self):
        taller = _taller()
        turnos = [HorarioTaller(taller=taller, dia=d, abre=time(8), cierra=time(18)) for d in range(5)]
        lunes = timezone.make_aware(datetime(2026, 11, 16, 10, 0))
        self.assertEqual(perfil.estado_horario(taller, turnos, lunes),
                         {"abierto": True, "texto": "Abierto ahora · cierra a las 6:00 p. m."})
        self.assertEqual(perfil.estado_horario(taller, turnos, lunes.replace(hour=7))["texto"],
                         "Cerrado · abre hoy a las 8:00 a. m.")
        viernes_noche = timezone.make_aware(datetime(2026, 11, 20, 19, 0))
        self.assertEqual(perfil.estado_horario(taller, turnos, viernes_noche)["texto"],
                         "Cerrado · abre el lunes a las 8:00 a. m.")
        self.assertIsNone(perfil.estado_horario(taller, []))


class EditarPerfilEstandarizadoTests(TestCase):
    def setUp(self):
        self.taller = _taller()
        self.servicio = Servicio.objects.get_or_create(nombre="Frenos")[0]
        self.client.force_login(self.taller.usuario)
        self.url = reverse("talleres:editar_perfil")

    def _datos(self, **extra):
        datos = {"descripcion": "Taller de barrio desde 2015, motos de trabajo.", "horario": "Lun-Sáb 8am-6pm",
                 "servicios": [self.servicio.pk], "especialidades": ["frenos", "scooters"], "garantia_meses": "3",
                 "compromisos": ["fotos", "presupuesto"],
                 "equipo-TOTAL_FORMS": "3", "equipo-INITIAL_FORMS": "0", "equipo-MIN_NUM_FORMS": "0",
                 "equipo-MAX_NUM_FORMS": "6",
                 "equipo-0-nombre": "Carlos", "equipo-0-rol": "Jefe de taller", "equipo-0-anios": "12",
                 "equipo-0-especialidad": str(self.servicio.pk), "equipo-1-nombre": "", "equipo-2-nombre": ""}
        datos.update(extra)
        return datos

    def test_guarda_campos_estructurados_y_sube_el_indicador(self):
        antes = self.client.get(self.url).context["completitud"]["pct"]
        self.assertContains(self.client.post(self.url, self._datos(), follow=True), "¡Perfil actualizado!")
        self.taller.refresh_from_db()
        self.assertEqual(self.taller.equipo, [{"nombre": "Carlos", "rol": "Jefe de taller", "anios": 12,
                                               "especialidad": self.servicio.nombre, "servicio": self.servicio.pk}])
        self.assertEqual((self.taller.especialidades, self.taller.garantia_meses, self.taller.compromisos),
                         (["frenos", "scooters"], 3, ["fotos", "presupuesto"]))
        self.assertGreater(self.client.get(self.url).context["completitud"]["pct"], antes)

    def test_descripcion_maximo_300_y_fila_sin_nombre(self):
        r = self.client.post(self.url, self._datos(descripcion="x" * 301))
        self.assertContains(r, "300")
        r = self.client.post(self.url, self._datos(**{"equipo-1-rol": "Técnico"}))
        self.assertContains(r, "Escribe el nombre o borra la fila.")
        self.taller.refresh_from_db()
        self.assertEqual(self.taller.equipo, [])


class EquipoCatalogoTests(EditarPerfilEstandarizadoTests):
    def test_otra_pide_texto_y_lo_guarda(self):
        r = self.client.post(self.url, self._datos(**{"equipo-0-especialidad": "otra"}))
        self.assertContains(r, "Escribe la especialidad")
        self.client.post(self.url, self._datos(**{"equipo-0-especialidad": "otra", "equipo-0-especialidad_otra": "Scooters"}))
        self.taller.refresh_from_db()
        self.assertEqual((self.taller.equipo[0]["especialidad"], self.taller.equipo[0]["servicio"]), ("Scooters", None))
        self.assertContains(self.client.get(self.url), 'value="Scooters"')

    def test_reglas_de_cercania(self):
        from talleres import perfil
        self.assertEqual(perfil.rol_cercano("Técnica SENA"), "Técnico")
        self.assertEqual(perfil.rol_cercano("Dueño"), "Jefe de taller")
        serv = [(1, "Frenos"), (2, "Suspensión"), (3, "Sincronización")]
        self.assertEqual(perfil.servicio_cercano("Suspensiones y horquillas", serv), 2)
        self.assertEqual(perfil.servicio_cercano("Inyección electrónica", serv), 3)
        self.assertIsNone(perfil.servicio_cercano("Scooters y CVT", serv))


class CompletarPerfilDemoTests(TestCase):
    def test_no_pisa_lo_editado_y_cambia_la_descripcion_larga_vieja(self):
        datos = demo_talleres.TALLERES[0]["datos"]
        taller = _taller(nombre=datos["nombre"], garantia_meses=6,
                         descripcion="Algo largo. Quiénes te atienden: " + "x" * 300)
        cambios = demo_talleres.completar_perfil(taller, datos)
        taller.refresh_from_db()
        self.assertNotIn("garantia_meses", cambios)
        self.assertEqual(taller.garantia_meses, 6)
        self.assertEqual(taller.equipo[0]["nombre"], "Jhon Fredy Ospina")
        self.assertEqual(taller.descripcion, datos["descripcion"])
        self.assertEqual(demo_talleres.completar_perfil(taller, datos), [])  # idempotente
