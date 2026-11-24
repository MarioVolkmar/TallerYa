from django.template import Context, Template
from django.test import SimpleTestCase


class PlegTests(SimpleTestCase):
    def render(self, plantilla, **ctx):
        return Template("{% load pleg %}" + plantilla).render(Context(ctx))

    def test_estructura_y_dato(self):
        html = self.render('{% pleg "k" id="x" numero="01" titulo="Citas" dato=n|cuenta:"cita,citas" cerrada_movil=True %}hola{% endpleg %}', n=3)
        self.assertIn('<details class="seccion-pleg "', html)
        self.assertIn('id="x" data-pleg="k" data-movil-cerrada open', html)
        self.assertIn("3 citas", html)
        self.assertIn('<div class="seccion-cuerpo-pleg">hola</div>', html)

    def test_cerrada_y_singular(self):
        html = self.render('{% pleg "k" numero="1" titulo="T" dato=n|cuenta:"cita,citas" cerrada=True %}x{% endpleg %}', n=1)
        self.assertNotIn(" open", html)
        self.assertIn("1 cita<", html)
