import json
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from foro.models import Categoria, Pregunta, Rodada

from .models import Barrio, Resena, Servicio, Taller


class SeoTests(TestCase):
    def setUp(self):
        self.barrio = Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]
        self.servicio = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        self.taller = Taller.objects.create(
            nombre="Taller Belén", responsable="Ana", whatsapp="573001234567", descripcion="Mecánica de motos.",
            direccion="Cra 1 # 2-3", barrio=self.barrio, activo=True)
        self.taller.servicios.add(self.servicio)
        autor = get_user_model().objects.create_user("a@x.com", "a@x.com", "x")
        self.pregunta = Pregunta.objects.create(autor=autor, titulo="¿Qué aceite uso?", cuerpo="Detalles")
        p2 = Pregunta.objects.create(autor=autor, titulo="Rodada a Santa Elena", cuerpo="x", categoria=Categoria.RUTAS)
        self.rodada = Rodada.objects.create(pregunta=p2, organizador=autor, fecha_hora=timezone.now(),
                                            punto_encuentro="Metro", destino="Santa Elena")

    def test_robots(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r["Content-Type"].split(";")[0], "text/plain")
        for p in ("/cuenta/", "/garaje/", "/admin/", "/tareas/"):
            self.assertContains(r, f"Disallow: {p}")
        self.assertContains(r, "Sitemap: http://testserver/sitemap.xml")

    def test_sitemap(self):
        r = self.client.get("/sitemap.xml")
        t = r.content.decode()
        self.assertEqual(r["Content-Type"], "application/xml")
        for ruta in (self.taller.get_absolute_url(), "/talleres/en/belen/", "/talleres/servicio/cambio-de-aceite/",
                     "/talleres/servicio/cambio-de-aceite/belen/", self.pregunta.get_absolute_url(), self.rodada.get_absolute_url()):
            self.assertIn(f"<loc>http://testserver{ruta}</loc>", t)
        self.assertNotIn("/garaje/", t)

    def test_sitemap_omite_talleres_inactivos(self):
        Taller.objects.filter(pk=self.taller.pk).update(activo=False)
        self.assertNotIn(self.taller.get_absolute_url(), self.client.get("/sitemap.xml").content.decode())

    def test_pagina_barrio(self):
        r = self.client.get("/talleres/en/belen/")
        self.assertContains(r, "<title>Talleres de motos en Belén · TallerYa</title>", html=False)
        self.assertContains(r, "Taller Belén")
        self.assertContains(r, '<link rel="canonical" href="http://testserver/talleres/en/belen/">')
        self.assertContains(r, 'content="index,follow')
        self.assertEqual(self.client.get("/talleres/en/no-existe/").status_code, 404)

    def test_pagina_servicio_y_combinacion(self):
        r = self.client.get("/talleres/servicio/cambio-de-aceite/belen/")
        self.assertContains(r, "Cambio de aceite en Belén")
        self.assertContains(r, "Taller Belén")
        self.assertEqual(self.client.get("/talleres/servicio/cambio-de-aceite/").status_code, 200)
        otro = Barrio.objects.get_or_create(nombre="Laureles", ciudad="Medellín")[0]
        Taller.objects.create(nombre="Otro", responsable="B", whatsapp="573000000000", direccion="X", barrio=otro, activo=True)
        # Laureles tiene taller, pero ninguno con ese servicio: combinación vacía = 404
        self.assertEqual(self.client.get("/talleres/servicio/cambio-de-aceite/laureles/").status_code, 404)

    def test_barrio_filtra_solo_su_barrio(self):
        otro = Barrio.objects.get_or_create(nombre="Laureles", ciudad="Medellín")[0]
        Taller.objects.create(nombre="Taller Laureles", responsable="B", whatsapp="573000000000", direccion="X", barrio=otro, activo=True)
        self.assertNotContains(self.client.get("/talleres/en/belen/"), "Taller Laureles")

    def test_directorio_con_filtros_noindex_y_canonical_limpia(self):
        r = self.client.get("/talleres/?q=aceite")
        self.assertContains(r, "noindex,follow")
        self.assertContains(r, '<link rel="canonical" href="http://testserver/talleres/">')

    def test_detalle_json_ld(self):
        Resena.objects.create(taller=self.taller, nombre="Juan", estrellas=5, comentario="Excelente")
        r = self.client.get(self.taller.get_absolute_url())
        datos = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', r.content.decode(), re.S).group(1))
        self.assertEqual(datos["@type"], "AutoRepair")
        self.assertEqual(datos["name"], "Taller Belén")
        self.assertEqual(datos["telephone"], "+573001234567")
        self.assertEqual(datos["aggregateRating"]["reviewCount"], 1)
        self.assertContains(r, 'property="og:image"')
        self.assertContains(r, 'content="index,follow')

    def test_paginas_publicas_tienen_meta(self):
        for url in ("/", "/foro/", "/foro/rodadas/", "/cupones/", self.pregunta.get_absolute_url(), self.rodada.get_absolute_url()):
            r = self.client.get(url)
            self.assertContains(r, '<meta name="description"', msg_prefix=url)
            self.assertContains(r, 'property="og:title"', msg_prefix=url)
            self.assertContains(r, 'rel="canonical"', msg_prefix=url)

    def test_paginas_privadas_noindex(self):
        for url in ("/cuenta/entrar/", "/garaje/", "/cuenta/", "/mi-taller/", "/foro/preguntar/"):
            r = self.client.get(url, follow=True)
            self.assertContains(r, "noindex", msg_prefix=url)
