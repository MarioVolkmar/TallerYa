from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from . import ajustes
from .models import Ajuste, Bitacora

User = get_user_model()
SECCION = reverse("consola:inicio") + "?seccion=configuracion"


class AjustesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_user("root@t.co", "root@t.co", "clave-segura-123", is_staff=True, is_superuser=True)
        cls.staff = User.objects.create_user("st@t.co", "st@t.co", "clave-segura-123", is_staff=True)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def apagar(self, clave, valor="0"):
        return self.client.post(reverse("consola:ajuste", args=[clave]), {"valor": valor})

    def test_valor_inicial_viene_de_settings(self):
        with override_settings(PILOTO_OCULTAR_SOCIAL=True):
            self.assertFalse(ajustes.ajuste("foro_activo"))
        cache.clear()
        with override_settings(PILOTO_OCULTAR_SOCIAL=False):
            self.assertTrue(ajustes.ajuste("foro_activo"))

    def test_apagar_foro_da_404_y_prender_lo_devuelve(self):
        self.client.force_login(self.root)
        self.assertEqual(self.client.get("/foro/").status_code, 200)
        self.assertEqual(self.apagar("foro_activo").status_code, 302)
        self.assertEqual(self.client.get("/foro/").status_code, 404)
        self.assertNotContains(self.client.get("/"), 'href="/foro/"')
        self.assertEqual(self.client.get("/plus/").status_code, 200)  # los demás módulos siguen
        self.apagar("foro_activo", "1")
        self.assertEqual(self.client.get("/foro/").status_code, 200)

    def test_cada_modulo_es_independiente(self):
        self.client.force_login(self.root)
        self.apagar("plus_activo")
        self.assertEqual(self.client.get("/plus/").status_code, 404)
        self.assertEqual(self.client.get("/foro/").status_code, 200)
        self.apagar("mecanicos_activo")
        self.assertEqual(self.client.get("/mecanicos/").status_code, 404)

    def test_domiciliarios_y_bandera(self):
        from domiciliarios.bandera import activo
        self.client.force_login(self.root)
        self.apagar("domiciliarios_activo", "1")
        self.assertTrue(activo())
        self.apagar("domiciliarios_activo", "0")
        self.assertFalse(activo())

    def test_bitacora_con_antes_y_despues(self):
        self.client.force_login(self.root)
        self.apagar("foro_activo")
        b = Bitacora.objects.get(accion="ajustes.cambiar")
        self.assertEqual(b.frase, "Apagó «Foro y rodadas»")
        self.assertEqual(b.cambios[0]["antes"], "Prendido")
        self.assertEqual(b.cambios[0]["despues"], "Apagado")
        self.assertEqual(b.actor, self.root)

    def test_sin_cambio_no_registra(self):
        self.client.force_login(self.root)
        self.apagar("foro_activo", "1")  # ya estaba prendido
        self.assertFalse(Bitacora.objects.exists())

    def test_staff_no_superusuario_no_puede(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(SECCION).status_code, 403)
        self.assertEqual(self.apagar("foro_activo").status_code, 403)
        fila = Ajuste.objects.create(clave="foro_activo", valor=True)
        r = self.client.post(reverse("consola:accion", args=["ajustes.cambiar", fila.pk]), {"valor": "0"})
        self.assertEqual(r.status_code, 403)
        fila.refresh_from_db()
        self.assertTrue(fila.valor)
        self.assertNotContains(self.client.get(reverse("consola:inicio")), "Configuración")

    def test_anonimo_y_modulo_desconocido(self):
        self.assertEqual(self.apagar("foro_activo").status_code, 302)
        self.assertFalse(Ajuste.objects.exists())
        self.client.force_login(self.root)
        self.assertEqual(self.apagar("no_existe").status_code, 404)

    def test_get_no_cambia_nada(self):
        self.client.force_login(self.root)
        self.assertEqual(self.client.get(reverse("consola:ajuste", args=["foro_activo"])).status_code, 405)

    def test_la_seccion_lista_los_modulos(self):
        self.client.force_login(self.root)
        r = self.client.get(SECCION)
        self.assertContains(r, "Foro y rodadas")
        self.assertContains(r, "Mecánicos a domicilio")
        self.assertContains(r, "TallerYa Ruta")


class CifrasDirectorioTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_user("root@t.co", "root@t.co", "clave-segura-123", is_staff=True, is_superuser=True)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_apagado_por_defecto_no_pinta_ni_consulta(self):
        r = self.client.get("/talleres/")
        self.assertNotContains(r, "dir-stats")
        self.assertIsNone(r.context["stats"])

    def test_encendido_pinta_la_caja(self):
        Ajuste.objects.create(clave="cifras_directorio", valor=True)
        cache.clear()
        r = self.client.get("/talleres/")
        self.assertContains(r, "dir-stats")
        self.assertIn("total", r.context["stats"])

    def test_interruptor_en_configuracion_y_bitacora(self):
        self.client.force_login(self.root)
        self.assertContains(self.client.get(SECCION), "Mostrar cifras en el directorio")
        self.client.post(reverse("consola:ajuste", args=["cifras_directorio"]), {"valor": "1"})
        self.assertTrue(ajustes.ajuste("cifras_directorio"))
        self.assertTrue(Bitacora.objects.filter(accion="ajustes.cambiar").exists())


class PrecioTipicoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_user("root2@t.co", "root2@t.co", "clave-segura-123", is_staff=True, is_superuser=True)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_apagado_por_defecto(self):
        self.assertFalse(ajustes.ajuste("precio_tipico"))

    def test_interruptor_en_configuracion_y_bitacora(self):
        self.client.force_login(self.root)
        self.assertContains(self.client.get(SECCION), "Mostrar precio típico por servicio")
        self.client.post(reverse("consola:ajuste", args=["precio_tipico"]), {"valor": "1"})
        self.assertTrue(ajustes.ajuste("precio_tipico"))
        self.assertTrue(Bitacora.objects.filter(accion="ajustes.cambiar").exists())


class PrecioTipicoAyudaTest(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_la_ayuda_solo_habla_del_precio_tipico_si_esta_encendido(self):
        from ayuda import motor
        r = motor.responder(pregunta_id="buscar-taller")
        self.assertNotIn("precio típico", " ".join(r["respuesta"]).lower())
        Ajuste.objects.create(clave="precio_tipico", valor=True)
        cache.clear()
        self.assertIn("precio típico", " ".join(motor.responder(pregunta_id="buscar-taller")["respuesta"]).lower())
