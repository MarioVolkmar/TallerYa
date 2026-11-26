"""Páginas públicas por moto (para Google): sin sesión, con título y datos estructurados propios, en el sitemap y sin
nada de los usuarios."""
import json
import re
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from cupones.models import Motociclista
from garaje.models import Despiece, Lamina, LineaMoto, Moto, ParteDespiece


class MotosPublicasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.nmax = LineaMoto.objects.get(nombre="NMAX 155")
        despiece = Despiece.objects.create(linea=cls.nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=despiece, figura=22, titulo="FRONT BRAKE CALIPER",
                                       titulo_es="Freno delantero", pieza="freno_del", diagrama="freno_disco")
        ParteDespiece.objects.create(lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT",
                                     nombre_es="Pastillas de freno")
        dueno = get_user_model().objects.create_user("dueno@x.com", "dueno@x.com", "x")
        Moto.objects.create(motociclista=Motociclista.objects.create(nombre="Dueño", celular="573001112233", usuario=dueno), linea=cls.nmax, modelo=2023, placa="ZZZ99Z", km_actual=43210, km_inicial=40000)

    def setUp(self):
        cache.clear()
        caches["despiece"].clear()
        self.moto = reverse("garaje:moto_publica", args=["yamaha-nmax-155"])
        self.falla = reverse("garaje:moto_falla", args=["yamaha-nmax-155", "cvt-tiembla"])
        self.correa = reverse("garaje:moto_mantenimiento", args=["yamaha-nmax-155", "correa-cvt"])
        self.pieza = reverse("garaje:despiece_pieza", args=["yamaha-nmax-155", "pastillas-de-freno"])

    def _ld(self, html):
        return [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]

    def test_paginas_sin_sesion_con_titulo_h1_y_datos_propios(self):
        titulos = set()
        for url in (reverse("garaje:motos_publicas"), self.moto, self.falla, self.correa, self.pieza):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            html = r.content.decode()
            self.assertContains(r, 'content="index,follow')
            self.assertContains(r, f'<link rel="canonical" href="http://testserver{url}">')
            self.assertEqual(html.count("<h1"), 1, url)
            self.assertTrue(self._ld(html), url)
            titulos.add(re.search(r"<title>(.*?)</title>", html, re.S)[1])
            for privado in ("ZZZ99Z", "43.210", "43210", "dueno@x.com", "2DP-F5805-00", "entregada por el usuario"):
                self.assertNotIn(privado, html, url)
        self.assertEqual(len(titulos), 5)

    def test_respuesta_de_la_correa_y_enlaces(self):
        r = self.client.get(self.correa)
        self.assertContains(r, "¿Cada cuánto cambiar la correa CVT de la Yamaha NMAX 155?")
        self.assertContains(r, "Cada 18.000 km")
        self.assertContains(r, self.falla)
        self.assertIn("FAQPage", [x["@type"] for x in self._ld(r.content.decode())])
        moto = self.client.get(self.moto)
        self.assertContains(moto, self.falla)
        self.assertContains(moto, self.correa)
        self.assertContains(moto, reverse("garaje:despiece_moto", args=["yamaha-nmax-155"]))
        sistema = self.client.get(reverse("garaje:despiece_sistema", args=["yamaha-nmax-155", "freno-delantero"]))
        self.assertContains(sistema, self.pieza)

    def test_desconocidos_dan_404(self):
        for nombre, args in (("moto_publica", ["no-existe"]), ("moto_falla", ["yamaha-nmax-155", "no-existe"]),
                             ("moto_mantenimiento", ["yamaha-nmax-155", "kit-arrastre"]),
                             ("despiece_pieza", ["yamaha-nmax-155", "no-existe"])):
            self.assertEqual(self.client.get(reverse(f"garaje:{nombre}", args=args)).status_code, 404, nombre)

    def test_sitemap_no_arma_despieces_y_acota_consultas(self):
        with mock.patch("garaje.views._laminas_base", side_effect=AssertionError("el sitemap armó un despiece")):
            self.client.get("/sitemap.xml")              # calienta las cachés de ajustes
            with CaptureQueriesContext(connection) as consultas:
                xml = self.client.get("/sitemap.xml").content.decode()
            self.assertIn(reverse("garaje:despiece_moto", args=["yamaha-nmax-155"]), xml)
            self.assertNotIn(self.pieza, xml)             # sin índice: solo la moto
            self.assertLessEqual(len(consultas), 20)
            # Un despiece más no suma consultas
            otro = Despiece.objects.create(linea=LineaMoto.objects.get(nombre="Aerox 155"), version="X", anio=2024)
            Lamina.objects.create(despiece=otro, figura=1, titulo="T", pieza="freno_del", diagrama="freno_disco")
            with CaptureQueriesContext(connection) as despues:
                self.client.get("/sitemap.xml")
            self.assertEqual(len(despues), len(consultas))

    def test_sitemap_y_robots(self):
        call_command("precalentar_despiece", "--max-segundos", "0", verbosity=0, stdout=StringIO())
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r["Content-Type"], "application/xml")
        xml = r.content.decode()
        for url in (reverse("garaje:motos_publicas"), self.moto, self.falla, self.correa, self.pieza):
            self.assertIn(f"<loc>http://testserver{url}</loc>", xml)
        for privada in ("/garaje/", "/cuenta/", "/hoja-de-vida/", "ZZZ99Z"):
            self.assertNotIn(privada, xml)
        robots = self.client.get("/robots.txt").content.decode()
        self.assertNotIn("Disallow: /motos/", robots)
        self.assertNotIn("Disallow: /despiece/", robots)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", robots)

    def test_todas_las_paginas_de_todas_las_motos_abren(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        rutas = re.findall(r"<loc>http://testserver(/motos/[^<]+)</loc>", xml)
        self.assertGreater(len(rutas), 200)
        for ruta in rutas:
            self.assertEqual(self.client.get(ruta).status_code, 200, ruta)
