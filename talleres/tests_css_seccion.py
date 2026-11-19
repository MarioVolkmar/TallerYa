from django.template import Context, Template
from django.test import SimpleTestCase

from talleres.templatetags.css_seccion import seccion_de, secciones


class CssSeccionTests(SimpleTestCase):
    def test_existen_las_hojas_por_seccion(self):
        self.assertTrue({"garaje", "foro", "talleres"} <= secciones())

    def test_la_seccion_sale_de_la_plantilla_raiz(self):
        self.assertEqual(seccion_de("garaje/moto.html"), "garaje")
        self.assertEqual(seccion_de("foro/lista.html"), "foro")
        self.assertEqual(seccion_de("404.html"), "")
        self.assertEqual(seccion_de("consola/consola.html"), "")  # sin hoja propia: solo la base
        self.assertEqual(seccion_de(None), "")

    def test_etiqueta_pone_el_enlace_solo_en_su_seccion(self):
        t = Template("{% load css_seccion %}{% css_seccion %}", name="garaje/moto.html")
        self.assertIn("talleres/css/secciones/garaje.css", t.render(Context()))
        t = Template("{% load css_seccion %}{% css_seccion %}", name="404.html")
        self.assertEqual(t.render(Context()), "")
