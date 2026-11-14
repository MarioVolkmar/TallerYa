from unittest import mock

from django.test import TestCase
from django.urls import reverse

from .importar import clasificar, importar
from .models import Articulo, FuenteNoticias

RSS = b"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Prueba</title>
<item><title>Medell\xc3\xadn cambia el pico y placa para motos</title><link>https://ejemplo.co/pyp</link>
<description>&lt;p&gt;La rotaci\xc3\xb3n nueva&lt;/p&gt;</description><pubDate>Fri, 13 Nov 2026 10:00:00 -0500</pubDate></item>
<item><title>El papa visita Chiclayo</title><link>https://ejemplo.co/papa</link><description>Visita pastoral</description>
<pubDate>Fri, 13 Nov 2026 09:00:00 -0500</pubDate></item>
</channel></rss>"""


class NoticiasTests(TestCase):
    def test_lista_y_articulo_propio(self):
        a = Articulo.objects.create(titulo="Cadena al d\u00eda", resumen="Lubr\u00edcala.", cuerpo="Uno.\n\nDos.")
        oculto = Articulo.objects.create(titulo="Borrador", resumen="x", cuerpo="x", publicado=False)
        r = self.client.get(reverse("noticias:lista"))
        self.assertContains(r, "Cadena al d\u00eda")
        self.assertNotContains(r, "Borrador")
        self.assertContains(self.client.get(a.get_absolute_url()), "Dos.")
        self.assertEqual(self.client.get(oculto.get_absolute_url()).status_code, 404)

    def test_inicio_muestra_el_noticiero(self):
        Articulo.objects.create(titulo="Nueva moto el\u00e9ctrica", resumen="Llega.", fuente="Medio", fuente_url="https://ejemplo.co/n")
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, "Nueva moto el\u00e9ctrica")
        self.assertContains(r, 'href="https://ejemplo.co/n"')

    @mock.patch("noticias.importar.descargar", return_value=RSS)
    def test_importa_solo_lo_motero_y_clasifica(self, _descarga):
        Articulo.objects.all().delete()
        fuente = FuenteNoticias.objects.create(nombre="Diario", url="https://ejemplo.co/rss")
        with mock.patch("noticias.importar.timezone.now") as ahora:
            from datetime import datetime, timezone as tz
            ahora.return_value = datetime(2026, 11, 13, 18, 0, tzinfo=tz.utc)
            self.assertEqual(importar(fuente), 1)
            self.assertEqual(importar(fuente), 0)  # no repite
        a = Articulo.objects.get()
        self.assertEqual((a.categoria, a.fuente, a.resumen), ("transito", "Diario", "La rotaci\u00f3n nueva"))
        self.assertTrue(a.externo)

    def test_clasificar(self):
        self.assertEqual(clasificar("Ya puede hacer el traspaso de su moto en l\u00ednea"), "tramites")
        self.assertEqual(clasificar("Yamaha lanza la nueva MT-15"), "lanzamiento")
        self.assertEqual(clasificar("Multas de tr\u00e1fico de la DGT", internacional=True), "actualidad")
