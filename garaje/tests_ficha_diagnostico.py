"""Piloto, paso 4: enviar el diagnóstico a un taller o mecánico a domicilio por WhatsApp + ficha pública con token."""
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from urllib.parse import parse_qs, unquote, urlparse

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from cupones.models import Motociclista
from domicilio.models import MecanicoDomicilio
from talleres.models import Barrio, EventoDiario, Marca, Servicio, Taller

from .models import FichaDiagnostico, LineaMoto, Moto

User = get_user_model()
NAV = {"HTTP_USER_AGENT": "Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile"}
CONSULTA = {"t": "cvt", "s": "fuga", "que": "gasolina"}  # resultado «parar»: es la fuga de gasolina


def _png(nombre="a.png", color="red"):
    b = BytesIO()
    Image.new("RGB", (40, 30), color).save(b, "PNG")
    return SimpleUploadedFile(nombre, b.getvalue(), "image/png")


class FichaBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.taller = Taller.objects.create(nombre="Taller Uno", responsable="A", whatsapp="573001112233", direccion="X",
                                           barrio=barrio, activo=True)
        cls.servicio = Servicio.objects.get_or_create(nombre="Mantenimiento general")[0]
        cls.taller.servicios.add(cls.servicio)
        cls.mecanico = MecanicoDomicilio.objects.create(nombre="Don Pedro", whatsapp="573004445566",
                                                        estado=MecanicoDomicilio.Estado.APROBADO)
        cls.url = reverse("garaje:diagnostico_enviar")

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        sobre = override_settings(MEDIA_ROOT=self.media)
        sobre.enable()
        self.addCleanup(sobre.disable)

    def enviar(self, datos=None, consulta=None, **extra):
        q = "&".join(f"{k}={v}" for k, v in (consulta or CONSULTA).items())
        return self.client.post(f"{self.url}?{q}", datos or {}, **NAV, **extra)

    def texto_wa(self, r):
        return unquote(parse_qs(urlparse(r["Location"]).query)["text"][0])


class EnviarTests(FichaBase):
    def test_pagina_ofrece_talleres_y_mecanicos(self):
        r = self.client.get(f"{self.url}?t=cvt&s=fuga&que=gasolina")
        self.assertContains(r, "Taller Uno")
        self.assertContains(r, "Don Pedro")
        self.assertContains(r, 'content="noindex"')

    def test_orden_especialista_verificado_nota_y_destacado_limitado(self):
        from types import SimpleNamespace as N
        from .vista_ficha_diagnostico import ordenar
        mk = lambda pk, nombre, esp=(), ver=False, prom=None, n=0: N(pk=pk, nombre=nombre, especialidades=list(esp), verificado=ver, prom=prom, n_resenas=n)
        lista = [mk(1, "Zeta", ver=True, prom=5, n=40), mk(2, "Beta", ["frenos"]), mk(3, "Alfa", ver=True, prom=4.9, n=1),
                 mk(4, "Pro1"), mk(5, "Pro2"), mk(6, "Pro3"), mk(7, "Omega", ["frenos"], True, 4.5, 10)]
        r = ordenar(lista, "Frenos", {4, 5, 6})
        self.assertEqual([c.nombre for c in r], ["Pro1", "Pro2", "Omega", "Beta", "Zeta", "Alfa", "Pro3"])
        self.assertEqual([c.es_destacado for c in r], [True, True] + [False] * 5)
        # sin destacados: la nota con muchas reseñas pesa más que 4,9 con una sola
        self.assertEqual([c.nombre for c in ordenar(lista[:1] + lista[2:3], "", set())], ["Zeta", "Alfa"])

    def test_pagina_ordena_por_nota_y_muestra_estrellas(self):
        from talleres.models import Resena
        b = Barrio.objects.get(nombre="Belén")
        otro = Taller.objects.create(nombre="Aaa Taller", responsable="A", whatsapp="573001110000", direccion="Y", barrio=b, activo=True)
        otro.servicios.add(self.servicio)
        Resena.objects.create(taller=self.taller, nombre="X", estrellas=5, comentario="Muy bien")
        r = self.client.get(f"{self.url}?t=cvt&s=fuga&que=gasolina")
        nombres = [t.nombre for t in r.context["talleres"]]
        self.assertEqual(nombres, ["Taller Uno", "Aaa Taller"])
        self.assertContains(r, "1 reseña")

    def test_consulta_invalida_es_404(self):
        self.assertEqual(self.client.get(f"{self.url}?t=cvt&s=nada").status_code, 404)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_taller_abre_whatsapp_con_ficha_y_se_mide(self):
        r = self.enviar({"destino": f"t:{self.taller.pk}", "km": "12.500"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("https://wa.me/573001112233?text="))
        f = FichaDiagnostico.objects.get()
        self.assertEqual((f.destino, f.taller, f.km), ("taller", self.taller, 12500))
        texto = self.texto_wa(r)
        self.assertIn(f.get_absolute_url(), texto)
        self.assertIn("Taller Uno", texto)
        self.assertEqual(EventoDiario.objects.get(taller=self.taller, tipo="whatsapp").cantidad, 1)

    def test_mecanico_a_domicilio(self):
        r = self.enviar({"destino": f"m:{self.mecanico.pk}"})
        self.assertTrue(r["Location"].startswith("https://wa.me/573004445566?text="))
        self.assertIn("visita a domicilio", self.texto_wa(r))
        self.assertEqual(FichaDiagnostico.objects.get().mecanico, self.mecanico)

    def test_destino_ajeno_o_vacio_no_crea_ficha(self):
        otro = Taller.objects.create(nombre="Sin WhatsApp", responsable="B", whatsapp="", direccion="X", barrio=self.taller.barrio, activo=True)
        for destino in ("", "t:99999", f"t:{otro.pk}", "x:1", "m:abc"):
            self.assertEqual(self.enviar({"destino": destino}).status_code, 400, destino)
        self.assertFalse(FichaDiagnostico.objects.exists())

    def test_km_absurdo_se_ignora(self):
        self.enviar({"destino": f"t:{self.taller.pk}", "km": "99999999999"})
        self.assertIsNone(FichaDiagnostico.objects.get().km)

    def test_solo_claves_del_diagnostico_viajan_a_la_ficha(self):
        self.enviar({"destino": f"t:{self.taller.pk}"}, consulta={**CONSULTA, "placa": "ABC12D", "x": "y"})
        self.assertEqual(FichaDiagnostico.objects.get().consulta, "t=cvt&s=fuga&que=gasolina")


class FotosTests(FichaBase):
    def test_sube_fotos_validas_como_jpeg(self):
        r = self.enviar({"destino": f"t:{self.taller.pk}", "fotos": [_png("a.png"), _png("b.png", "blue")]})
        self.assertEqual(r.status_code, 302)
        f = FichaDiagnostico.objects.get()
        self.assertEqual(f.fotos.count(), 2)
        for foto in f.fotos.all():
            self.assertTrue(foto.imagen.name.startswith("diagnosticos/") and foto.imagen.name.endswith(".jpg"))
        self.assertIn("2 fotos", self.texto_wa(r))

    def test_mas_de_tres_fotos_se_rechaza(self):
        r = self.enviar({"destino": f"t:{self.taller.pk}", "fotos": [_png(f"{i}.png") for i in range(4)]})
        self.assertEqual(r.status_code, 400)
        self.assertContains(r, "Máximo 3 fotos", status_code=400)
        self.assertFalse(FichaDiagnostico.objects.exists())

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile("virus.png", b"<script>alert(1)</script>", "image/png")
        r = self.enviar({"destino": f"t:{self.taller.pk}", "fotos": [falso]})
        self.assertEqual(r.status_code, 400)
        self.assertFalse(FichaDiagnostico.objects.exists())

    def test_foto_demasiado_grande_se_rechaza(self):
        grande = SimpleUploadedFile("g.png", _png().read() + b"0" * (5 * 1024 * 1024), "image/png")
        self.assertEqual(self.enviar({"destino": f"t:{self.taller.pk}", "fotos": [grande]}).status_code, 400)


class FichaPublicaTests(FichaBase):
    def crear(self, **kw):
        self.enviar({"destino": f"t:{self.taller.pk}", "fotos": [_png()]})
        f = FichaDiagnostico.objects.get()
        if kw:
            FichaDiagnostico.objects.filter(pk=f.pk).update(**kw)
            f.refresh_from_db()
        return f

    def test_se_abre_sin_cuenta_noindex_y_cuenta_vistas(self):
        f = self.crear()
        r = self.client.get(f.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f.causa)
        self.assertContains(r, 'content="noindex, nofollow"')
        self.assertIn("noindex", r["X-Robots-Tag"])
        self.assertContains(r, "Foto 1 de la moto")
        f.refresh_from_db()
        self.assertEqual(f.vistas, 1)

    def test_token_largo_y_distinto(self):
        a = self.crear()
        self.enviar({"destino": f"t:{self.taller.pk}"})
        b = FichaDiagnostico.objects.exclude(pk=a.pk).get()
        self.assertGreaterEqual(len(a.token), 30)
        self.assertNotEqual(a.token, b.token)
        self.assertEqual(self.client.get(reverse("garaje:ficha_diagnostico", args=["no-existe"])).status_code, 404)

    def test_vigencia_de_30_dias_y_vencida_responde_410(self):
        f = self.crear()
        self.assertAlmostEqual((f.vence - f.creado).days, 30, delta=1)
        FichaDiagnostico.objects.all().delete()
        f = self.crear(vence=timezone.now() - timedelta(minutes=1))
        r = self.client.get(f.get_absolute_url())
        self.assertEqual(r.status_code, 410)
        self.assertContains(r, "ya venció", status_code=410)
        self.assertNotContains(r, f.causa, status_code=410)


class ConMotoTests(FichaBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.linea = LineaMoto.objects.create(marca=Marca.objects.get_or_create(nombre="Yamaha")[0], nombre="NMAX", cilindraje=155, transmision="cvt")
        cls.usuario = User.objects.create_user("ana@x.com", "ana@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Ana Pérez", celular="573009998877", usuario=cls.usuario)
        cls.moto = Moto.objects.create(motociclista=perfil, linea=cls.linea, modelo=2022, km_inicial=0, km_actual=8000,
                                       placa="ABC12D")

    def test_ficha_sin_datos_personales(self):
        self.client.force_login(self.usuario)
        r = self.enviar({"destino": f"t:{self.taller.pk}", "km": "8000"}, consulta={**CONSULTA, "moto": self.moto.pk})
        self.assertEqual(r.status_code, 302)
        f = FichaDiagnostico.objects.get()
        self.assertIn("NMAX", f.moto)
        pagina = self.client.get(f.get_absolute_url()).content.decode()
        for privado in ("ABC12D", "Ana Pérez", "573009998877", "ana@x.com"):
            self.assertNotIn(privado, pagina + self.texto_wa(r))

    def test_moto_ajena_no_se_puede_enviar(self):
        otra = User.objects.create_user("b@x.com", "b@x.com", "x")
        self.client.force_login(otra)
        r = self.client.get(f"{self.url}?moto={self.moto.pk}&t=cvt&s=fuga&que=gasolina")
        self.assertEqual(r.status_code, 404)

    def test_boton_en_el_resultado_del_diagnostico(self):
        r = self.client.get(reverse("garaje:diagnostico") + "?t=cvt&s=fuga&que=gasolina")
        self.assertContains(r, "Enviar a un taller o a un mecánico a domicilio")
        self.assertContains(r, reverse("garaje:diagnostico_enviar"))


class NotaTests(FichaBase):
    def test_nota_es_opcional(self):
        self.enviar({"destino": f"t:{self.taller.pk}"})
        self.assertEqual(FichaDiagnostico.objects.get().nota, "")

    def test_nota_se_guarda_y_aparece_en_ficha_y_whatsapp(self):
        r = self.enviar({"destino": f"t:{self.taller.pk}", "nota": "Suena al frenar en bajada, desde hace una semana"})
        f = FichaDiagnostico.objects.get()
        self.assertEqual(f.nota, "Suena al frenar en bajada, desde hace una semana")
        self.assertIn("Nota del motero: Suena al frenar", self.texto_wa(r))
        self.assertContains(self.client.get(f.get_absolute_url()), "Suena al frenar en bajada")

    def test_nota_sin_html_y_escapada(self):
        self.enviar({"destino": f"t:{self.taller.pk}", "nota": "<script>alert(1)</script>ruido &lt;b&gt;"})
        f = FichaDiagnostico.objects.get()
        self.assertNotIn("<script>", f.nota)
        html = self.client.get(f.get_absolute_url()).content.decode()
        self.assertNotIn("<script>alert", html)

    def test_nota_con_tope_y_recortada_en_whatsapp(self):
        r = self.enviar({"destino": f"t:{self.taller.pk}", "nota": "ruido " * 200})
        self.assertEqual(len(FichaDiagnostico.objects.get().nota), 500)
        linea = [x for x in self.texto_wa(r).split("\n") if x.startswith("Nota del motero")][0]
        self.assertLessEqual(len(linea), 190)
        self.assertTrue(linea.endswith("…"))

    def test_formulario_muestra_caja_con_ejemplo(self):
        self.assertContains(self.client.get(f"{self.url}?t=cvt&s=fuga&que=gasolina"), 'name="nota"')
