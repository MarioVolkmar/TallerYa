from django.test import TestCase
from django.urls import reverse

from .models import Marca, PrecioServicio, Servicio, Taller
from .tests_perfil import EditarPerfilEstandarizadoTests


class PreciosPantallaTests(EditarPerfilEstandarizadoTests):
    """«Mis precios» por tarjetas, interruptor sin recargar, y «Multimarca» en perfil, tarjeta y filtro."""

    def test_mis_precios_agrupa_por_servicio_y_guarda_filas_nuevas(self):
        self.taller.servicios.add(self.servicio)
        PrecioServicio.objects.create(taller=self.taller, servicio=self.servicio, cilindraje="baja", desde=51000, hasta=74000)
        r = self.client.get(reverse("talleres:precios"))
        self.assertContains(r, "data-mis-precios")
        self.assertContains(r, "Rangos de mano de obra, sin repuestos")
        self.assertContains(r, 'data-card data-servicio="%d"' % self.servicio.pk)
        self.assertNotContains(r, "Guarda y aparecerán otras tres")
        base = {"precios-TOTAL_FORMS": "2", "precios-INITIAL_FORMS": "1", "precios-MIN_NUM_FORMS": "0", "precios-MAX_NUM_FORMS": "60"}
        pk = PrecioServicio.objects.get().pk
        datos = {**base, "precios-0-id": pk, "precios-0-servicio": self.servicio.pk, "precios-0-cilindraje": "baja",
                 "precios-0-desde": "51000", "precios-0-hasta": "74000",
                 "precios-1-servicio": self.servicio.pk, "precios-1-cilindraje": "media",
                 "precios-1-desde": "60000", "precios-1-hasta": "80000"}
        self.client.post(reverse("talleres:precios"), datos)
        self.assertEqual(PrecioServicio.objects.count(), 2)
        datos["precios-1-hasta"] = "50000"
        r = self.client.post(reverse("talleres:precios"), datos)
        self.assertContains(r, "mayor o igual")

    def test_interruptor_sin_recargar_responde_204(self):
        r = self.client.post(reverse("talleres:alternar_precios"), {"valor": "1"}, headers={"x-requested-with": "fetch"})
        self.assertEqual(r.status_code, 204)
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.mostrar_precios)

    def test_perfil_usa_la_tarjeta_de_estado_y_ya_no_el_check(self):
        r = self.client.get(self.url)
        self.assertContains(r, "data-estado-precios")
        self.assertNotContains(r, 'name="mostrar_precios"')
        # guardar el perfil no toca el interruptor
        Taller.objects.filter(pk=self.taller.pk).update(mostrar_precios=True)
        self.client.post(self.url, self._datos())
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.mostrar_precios)

    def test_multimarca_bandera_filtro_y_ficha(self):
        yamaha = Marca.objects.get_or_create(nombre="Yamaha")[0]
        otra = Marca.objects.get_or_create(nombre="Honda")[0]
        self.client.post(self.url, self._datos(multimarca="on"))
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.multimarca)
        Taller.objects.filter(pk=self.taller.pk).update(activo=True)
        for m in (yamaha, otra):
            r = self.client.get(reverse("talleres:inicio"), {"marca": m.pk})
            self.assertContains(r, self.taller.nombre)
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "Multimarca")
