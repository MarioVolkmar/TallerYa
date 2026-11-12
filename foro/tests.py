from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from talleres.models import Barrio, Taller

from .models import Pregunta, Reporte, Respuesta

User = get_user_model()


class ForoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.pregunta = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la Boxer?", cuerpo="Detalles")

    def test_lista_y_detalle_publicos(self):
        self.assertContains(self.client.get(reverse("foro:lista")), "Boxer")
        self.assertContains(self.client.get(self.pregunta.get_absolute_url()), "Detalles")

    def test_url_sin_slug_redirige_a_la_canonica(self):
        r = self.client.get(reverse("foro:pregunta_corta", args=[self.pregunta.pk]))
        self.assertRedirects(r, self.pregunta.get_absolute_url(), status_code=301)

    def test_preguntar_requiere_sesion(self):
        r = self.client.get(reverse("foro:preguntar"))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_preguntar_y_responder(self):
        self.client.force_login(self.beto)
        r = self.client.post(reverse("foro:preguntar"), {"titulo": "¿Cómo tensiono la cadena?", "cuerpo": "Ayuda"})
        p = Pregunta.objects.get(titulo__startswith="¿Cómo")
        self.assertRedirects(r, p.get_absolute_url())
        self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Usa 20W-50"})
        self.assertEqual(self.pregunta.respuestas.get().autor, self.beto)

    def test_responder_sin_sesion_redirige_a_entrar(self):
        r = self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Hola"})
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))
        self.assertFalse(Respuesta.objects.exists())

    def test_solo_el_autor_marca_la_mejor_respuesta(self):
        resp = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.client.force_login(self.beto)
        self.assertEqual(self.client.post(reverse("foro:marcar_mejor", args=[resp.pk])).status_code, 404)
        self.client.force_login(self.ana)
        self.client.post(reverse("foro:marcar_mejor", args=[resp.pk]))
        self.pregunta.refresh_from_db()
        self.assertEqual(self.pregunta.mejor_respuesta, resp)

    def test_tres_reportes_ocultan_la_publicacion(self):
        for i in range(3):
            u = User.objects.create_user(f"u{i}@x.com", f"u{i}@x.com", "x")
            self.client.force_login(u)
            self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))
            self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))  # duplicado ignorado
        self.assertEqual(Reporte.objects.count(), 3)
        self.pregunta.refresh_from_db()
        self.assertFalse(self.pregunta.visible)
        self.assertEqual(self.client.get(self.pregunta.get_absolute_url()).status_code, 404)

    def test_no_se_puede_reportar_lo_propio(self):
        self.client.force_login(self.ana)
        self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))
        self.assertFalse(Reporte.objects.exists())

    def test_respuesta_de_taller_lleva_insignia(self):
        barrio = Barrio.objects.create(nombre="Belén")
        Taller.objects.create(nombre="Taller Pro", responsable="X", whatsapp="573001234567", direccion="X",
                              barrio=barrio, activo=True, verificado=True, usuario=self.beto)
        Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.assertContains(self.client.get(self.pregunta.get_absolute_url()), "Taller verificado")

    def test_limite_de_publicaciones_por_hora(self):
        self.client.force_login(self.beto)
        for i in range(11):
            self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": f"Respuesta {i}"})
        self.assertEqual(Respuesta.objects.count(), 10)
