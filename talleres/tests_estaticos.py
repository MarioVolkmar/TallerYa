import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase, override_settings

from talleres.estaticos import EstaticosComprimidos, minificar_css


class MinificarCssTests(SimpleTestCase):
    def test_quita_comentarios_y_espacios_sobrantes(self):
        css = "/* titulo */\n.a {\n  color: red;\n  margin: 0 auto;\n}\n\n@media (min-width: 768px) {\n  .b { top: 0; }\n}\n"
        self.assertEqual(minificar_css(css), ".a{color: red;margin: 0 auto}@media (min-width: 768px){.b{top: 0}}")

    def test_no_toca_lo_que_cambia_el_significado(self):
        css = ('.a :hover, .b > .c { width: calc(100% - 2rem); content: "  /* no */ ; } "; '
               "background: url('x y.png') , var(--c, #fff); }")
        m = minificar_css(css)
        self.assertIn(".a :hover, .b > .c{", m)            # espacio de descendiente y comas intactos
        self.assertIn("calc(100% - 2rem)", m)
        self.assertIn('"  /* no */ ; } "', m)                # cadenas tal cual
        self.assertIn("url('x y.png') , var(--c, #fff)}", m)

    def test_comentario_entre_palabras_deja_un_espacio(self):
        self.assertEqual(minificar_css(".a{margin:0/**/auto}"), ".a{margin:0 auto}")

    def test_es_idempotente(self):
        css = ".a { color: red; } /* x */ .b{ }"
        self.assertEqual(minificar_css(minificar_css(css)), minificar_css(css))


class AlmacenEstaticosTests(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.almacen = EstaticosComprimidos(location=self.dir)

    def _guardar(self, nombre, texto):
        self.almacen._save(nombre, ContentFile(texto.encode()))
        with self.almacen.open(nombre) as f:
            return f.read().decode()

    def test_minifica_el_css_propio(self):
        self.assertEqual(self._guardar("talleres/css/x.css", "/* c */\n.a {\n  top: 0;\n}\n"), ".a{top: 0}")

    def test_deja_admin_min_y_js(self):
        texto = "/* c */\n.a {\n  top: 0;\n}\n"
        self.assertEqual(self._guardar("admin/css/base.css", texto), texto)
        self.assertEqual(self._guardar("lib/x.min.css", texto), texto)
        self.assertEqual(self._guardar("talleres/js/x.js", "/* c */ var a = 1;\n"), "/* c */ var a = 1;\n")


class MediaCacheTests(TestCase):
    def test_fotos_subidas_con_cache(self):
        dir_media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dir_media, ignore_errors=True)
        with open(f"{dir_media}/foto.jpg", "wb") as f:
            f.write(b"\xff\xd8\xff")
        from django.urls import clear_url_caches
        import importlib
        import config.urls
        with override_settings(MEDIA_ROOT=dir_media):
            importlib.reload(config.urls)
            clear_url_caches()
            try:
                r = self.client.get("/media/foto.jpg", HTTP_HOST="localhost")
                self.assertEqual(r.status_code, 200)
                self.assertIn("max-age=604800", r["Cache-Control"])
                self.assertIn("public", r["Cache-Control"])
            finally:
                importlib.reload(config.urls)
                clear_url_caches()
