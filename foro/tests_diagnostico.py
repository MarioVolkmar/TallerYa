"""Diagnósticos guiados citados en el foro: botón desde el resultado, adjuntar al preguntar o responder, tarjeta,
privacidad (sin placa ni dueño), sin IDOR y filtro por sistema."""
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from garaje.models import Despiece, Lamina, LineaMoto, Moto, ParteDespiece

from .models import DiagnosticoCompartido, Pregunta, Respuesta

User = get_user_model()
FRENO = {"s": "frena_mal", "cual": "del", "como": "poco"}


class DiagnosticoEnForoTests(TestCase):
    def setUp(self):
        self.diag = reverse("garaje:diagnostico")
        self.nmax = LineaMoto.objects.get(nombre="NMAX 155")
        self.despiece = Despiece.objects.create(linea=self.nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=self.despiece, figura=22, titulo="FRONT BRAKE CALIPER", titulo_es="Freno delantero",
                                       pieza="freno_del", diagrama="freno_disco")
        ParteDespiece.objects.create(lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT",
                                     nombre_es="Pastillas de freno")
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Ana Secreta", celular="573001112244", usuario=self.ana)
        self.moto = Moto.objects.create(motociclista=perfil, linea=self.nmax, modelo=2024, km_inicial=1000, km_actual=1000,
                                        placa="XYZ98K", apodo="La Negra")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x")
        self.client.force_login(self.ana)

    def _ver_resultado(self):
        r = self.client.get(self.diag, {"moto": self.moto.pk, **FRENO})
        self.assertEqual(r.context["paso"], "resultado")
        return r

    def _consulta(self):
        return self.client.session["diagnosticos"][0]["consulta"]

    def test_resultado_tiene_boton_y_queda_en_la_sesion(self):
        r = self._ver_resultado()
        self.assertContains(r, "Preguntar en el foro")
        url = r.context["compartir_url"]
        self.assertTrue(url.startswith(reverse("foro:preguntar")))
        self.assertEqual(parse_qs(urlparse(url).query)["diagnostico"][0], self._consulta())

    def test_preguntar_muestra_tarjeta_sin_datos_privados(self):
        self._ver_resultado()
        r = self.client.get(reverse("foro:preguntar"), {"diagnostico": self._consulta()})
        self.assertContains(r, "Diagnóstico TallerYa")
        self.assertContains(r, "Yamaha NMAX 155 2024")
        self.assertContains(r, "Pastillas de freno")
        self.assertEqual(r.context["form"]["categoria"].value(), "fallas")
        for privado in ("XYZ98K", "La Negra", "Ana Secreta"):
            self.assertNotContains(r, privado)

    def test_publicar_pregunta_guarda_resumen_inmutable_y_enlace_publico(self):
        self._ver_resultado()
        r = self.client.post(reverse("foro:preguntar"), {"titulo": "¿Me fallan los frenos de la NMAX?", "cuerpo": "Ayuda",
                                                         "categoria": "fallas", "diagnostico": self._consulta()})
        p = Pregunta.objects.get()
        self.assertRedirects(r, p.get_absolute_url())
        d = p.diagnostico
        self.assertEqual((d.autor, d.sistema, d.marca, d.modelo, d.anio, d.urgencia), (self.ana, "Frenos", "Yamaha", "NMAX 155", 2024, "parar"))
        self.assertIn("Pastillas de freno", d.piezas)
        self.assertIn(f"despiece={self.despiece.pk}", d.enlace)
        self.assertNotIn("moto=", d.enlace)  # el enlace no expone la moto del autor
        # Cualquiera ve la tarjeta y el enlace abre el mismo resultado
        self.client.logout()
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, 'class="fo-diag fo-diag-parar"')
        self.assertContains(r, d.enlace.replace("&", "&amp;"))
        self.assertNotContains(r, "XYZ98K")
        self.assertEqual(self.client.get(d.enlace).context["clave"], d.clave)

    def test_responder_con_diagnostico(self):
        p = Pregunta.objects.create(autor=self.beto, titulo="¿Qué le pasa a mi freno?", cuerpo="x")
        self._ver_resultado()
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "Adjuntar un diagnóstico tuyo")
        self.client.post(p.get_absolute_url(), {"cuerpo": "A mí me pasó esto", "diagnostico": self._consulta()})
        resp = Respuesta.objects.get()
        self.assertEqual(resp.diagnostico.causa, DiagnosticoCompartido.objects.get().causa)
        self.assertContains(self.client.get(p.get_absolute_url()), "Ver el diagnóstico")

    def test_sin_idor_no_se_adjunta_diagnostico_ajeno(self):
        self._ver_resultado()
        consulta = self._consulta()
        self.client.force_login(self.beto)
        datos = {"titulo": "¿Me fallan los frenos de la NMAX?", "cuerpo": "x", "diagnostico": consulta}
        # 1) Beto nunca vio ese diagnóstico: no está en su sesión
        self.client.post(reverse("foro:preguntar"), datos)
        # 2) Aunque lo meta en su sesión, la moto no es suya y no resuelve
        sesion = self.client.session
        sesion["diagnosticos"] = [{"consulta": consulta}]
        sesion.save()
        r = self.client.post(reverse("foro:preguntar"), datos)
        self.assertContains(r, "ya no está disponible")
        self.assertIsNone(r.context["diag_previa"])
        self.assertFalse(Pregunta.objects.exists())
        self.assertFalse(DiagnosticoCompartido.objects.exists())

    def test_contenido_escapado(self):
        moto = Moto.objects.create(motociclista=self.moto.motociclista, marca_otra="<script>x</script>", linea_otra="<b>Z</b>",
                                   modelo=2010, km_inicial=0, km_actual=0)
        self.client.get(self.diag, {"moto": moto.pk, "t": "cadena", **FRENO})
        r = self.client.get(reverse("foro:preguntar"), {"diagnostico": self._consulta()})
        self.assertNotContains(r, "<script>x</script>")
        self.assertContains(r, "&lt;script&gt;x&lt;/script&gt;")

    def test_filtro_por_sistema_y_parecidos(self):
        self._ver_resultado()
        d1 = DiagnosticoCompartido.objects.create(autor=self.ana, clave="pastillas", sintoma_clave="frena_mal", sintoma="Frena mal",
                                                  causa="Pastillas gastadas", sistema="Frenos", urgencia="parar", enlace="/diagnostico/")
        a = Pregunta.objects.create(autor=self.ana, titulo="Tema con diagnóstico de frenos", cuerpo="x", diagnostico=d1)
        b = Pregunta.objects.create(autor=self.beto, titulo="Otro tema de frenos parecido", cuerpo="x", diagnostico=d1)
        Pregunta.objects.create(autor=self.beto, titulo="Tema sin diagnóstico alguno", cuerpo="x")
        r = self.client.get(reverse("foro:lista"), {"sistema": "Frenos"})
        self.assertEqual({p.pk for p in r.context["pagina"]}, {a.pk, b.pk})
        self.assertContains(r, "Diagnóstico: Frenos")
        self.assertEqual(self.client.get(reverse("foro:lista"), {"sistema": "<x>"}).context["pagina"].paginator.count, 3)
        r = self.client.get(a.get_absolute_url())
        self.assertEqual(r.context["diag_parecidos"], [b])
