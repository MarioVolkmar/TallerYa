"""Páginas públicas del despiece (para Google): sin sesión, sin códigos de catálogo, en el sitemap e indexables."""
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from garaje.models import Despiece, Lamina, LineaMoto, ParteDespiece


class DespiecePublicoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        nmax = LineaMoto.objects.get(nombre="NMAX 155")
        cls.despiece = Despiece.objects.create(linea=nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=cls.despiece, figura=22, titulo="FRONT BRAKE CALIPER",
                                       titulo_es="Freno delantero", pieza="freno_del", diagrama="freno_disco")
        ParteDespiece.objects.create(lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT",
                                     nombre_es="Pastillas de freno")
        # Lámina sin dibujo propio: no se publica (solo existe el plano original de la marca)
        Lamina.objects.create(despiece=cls.despiece, figura=30, titulo="FRAME", titulo_es="Chasís", pieza="otro")

    def setUp(self):
        cache.clear()
        self.moto = reverse("garaje:despiece_moto", args=["yamaha-nmax-155"])
        self.sistema = reverse("garaje:despiece_sistema", args=["yamaha-nmax-155", "freno-delantero"])

    def test_indice_lista_la_moto_sin_sesion(self):
        r = self.client.get(reverse("garaje:despiece_indice"))
        self.assertContains(r, self.moto)
        self.assertContains(r, 'content="index,follow')

    def test_moto_lista_solo_laminas_con_dibujo_propio(self):
        r = self.client.get(self.moto)
        self.assertContains(r, self.sistema)
        self.assertNotContains(r, "Chasís")

    def test_sistema_muestra_piezas_y_guia_sin_codigos(self):
        r = self.client.get(self.sistema)
        self.assertContains(r, "Pastillas de freno")
        self.assertContains(r, "Señales de que está fallando")
        self.assertContains(r, f"?marca={self.despiece.linea.marca_id}")
        self.assertNotContains(r, "2DP-F5805-00")
        self.assertNotContains(r, "BRAKE PAD KIT")
        self.assertNotContains(r, "/media/")

    def test_slugs_desconocidos_dan_404(self):
        self.assertEqual(self.client.get(reverse("garaje:despiece_moto", args=["no-existe"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("garaje:despiece_sistema",
                                                 args=["yamaha-nmax-155", "no-existe"])).status_code, 404)

    def test_sitemap_incluye_moto_y_sistema(self):
        r = self.client.get(reverse("talleres:sitemap"))
        self.assertContains(r, self.moto)
        self.assertContains(r, self.sistema)
