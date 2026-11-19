"""Filtro «Va a domicilio» del directorio (con búsqueda, orden, paginación y páginas SEO) e interruptor del taller."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from domicilio.models import TallerDomicilio, Zona

from .models import Barrio, Servicio, Taller
from .seo import slug_barrio, slug_servicio


def nombres(r):
    return [t.nombre for t in r.context["pagina"].object_list]


class FiltroDomicilioTests(TestCase):
    def setUp(self):
        self.laureles = Barrio.objects.create(nombre="Barrio Prueba Uno")
        self.centro = Barrio.objects.create(nombre="Barrio Prueba Dos")
        self.frenos = Servicio.objects.get_or_create(nombre="Frenos")[0]

        def taller(nombre, barrio, domicilio=None, activo=True):
            t = Taller.objects.create(nombre=nombre, responsable="A", whatsapp="573000000000", direccion="X",
                                      barrio=barrio, activo=activo)
            t.servicios.add(self.frenos)
            if domicilio is not None:
                TallerDomicilio.objects.create(taller=t, activo=domicilio)
            return t
        self.a = taller("Alfa Motos", self.laureles, domicilio=True)
        self.b = taller("Beta Motos", self.centro, domicilio=True)
        taller("Gamma Motos", self.laureles, domicilio=False)      # lo tiene apagado
        taller("Delta Motos", self.laureles)                        # nunca lo configuró
        taller("Épsilon Motos", self.laureles, domicilio=True, activo=False)  # taller sin aprobar
        for i in range(10):                                         # para la paginación
            taller(f"Zeta {i:02d}", self.centro, domicilio=True)

    def test_solo_talleres_activos_que_van_a_domicilio(self):
        r = self.client.get(reverse("talleres:directorio"), {"domicilio": 1, "orden": "nombre"})
        todos = list(r.context["pagina"].paginator.object_list.values_list("nombre", flat=True))
        self.assertIn("Alfa Motos", todos)
        self.assertNotIn("Gamma Motos", todos)
        self.assertNotIn("Delta Motos", todos)
        self.assertNotIn("Épsilon Motos", todos)  # inactivo: no sale aunque tenga domicilio activo
        self.assertEqual(r.context["pagina"].paginator.count, 12)
        self.assertContains(r, "Va a domicilio")
        self.assertEqual([f["nombre"] for f in r.context["filtros_activos"]], ["Va a domicilio"])

    def test_con_busqueda_orden_y_paginacion(self):
        r = self.client.get(reverse("talleres:directorio"), {"domicilio": 1, "q": "Motos", "orden": "nombre"})
        self.assertEqual(nombres(r), ["Alfa Motos", "Beta Motos"])
        r = self.client.get(reverse("talleres:directorio"), {"domicilio": 1, "orden": "nombre", "pagina": 2})
        self.assertTrue(all(n.startswith("Zeta") for n in nombres(r)))
        self.assertIn("domicilio=1", r.context["qs_pagina"])  # los enlaces de página conservan el filtro

    def test_en_paginas_seo_por_barrio_y_servicio(self):
        r = self.client.get(reverse("talleres:barrio", args=[slug_barrio(self.laureles)]), {"domicilio": 1})
        self.assertEqual(nombres(r), ["Alfa Motos"])
        r = self.client.get(reverse("talleres:servicio", args=[slug_servicio(self.frenos)]), {"domicilio": 1, "q": "Beta"})
        self.assertEqual(nombres(r), ["Beta Motos"])

    def test_coherente_con_mecanicos(self):
        r = self.client.get(reverse("domicilio:listado"), {"tipo": "talleres"})
        self.assertContains(r, "Alfa Motos")
        self.assertNotContains(r, "Gamma Motos")
        self.assertNotContains(r, "Épsilon Motos")


class InterruptorTallerTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user("t@x.com", "t@x.com", "x")
        barrio = Barrio.objects.create(nombre="Barrio Prueba Uno")
        self.taller = Taller.objects.create(nombre="Mi Taller", responsable="A", whatsapp="573000000000", direccion="X",
                                            barrio=barrio, activo=True, usuario=self.usuario)
        self.url = reverse("domicilio:alternar_taller")
        self.client.force_login(self.usuario)

    def test_prende_y_apaga_desde_el_panel(self):
        self.assertContains(self.client.get(reverse("talleres:panel")), 'aria-checked="false"')
        r = self.client.post(self.url, {"valor": "1"})
        self.assertRedirects(r, reverse("domicilio:mi_taller"))  # sin zonas: lo lleva a elegirlas
        self.assertTrue(TallerDomicilio.objects.get(taller=self.taller).activo)
        TallerDomicilio.objects.get(taller=self.taller).zonas.add(Zona.objects.create(nombre="Zona de prueba única"))
        self.assertContains(self.client.get(reverse("talleres:panel")), 'aria-checked="true"')
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "También va a domicilio")
        r = self.client.post(self.url, {"valor": "0"})
        self.assertRedirects(r, reverse("talleres:panel"))
        self.assertFalse(TallerDomicilio.objects.get(taller=self.taller).activo)
        self.assertNotContains(self.client.get(self.taller.get_absolute_url()), "También va a domicilio")

    def test_solo_post_y_solo_su_taller(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        otro = get_user_model().objects.create_user("o@x.com", "o@x.com", "x")
        self.client.force_login(otro)
        self.assertEqual(self.client.post(self.url, {"valor": "1"}).status_code, 404)
        self.assertFalse(TallerDomicilio.objects.filter(taller=self.taller).exists())
