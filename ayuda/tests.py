from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from . import motor


class FaqTests(TestCase):
    def test_ids_unicos_y_relacionadas_validas(self):
        ids = [p["id"] for _, p in motor.preguntas()]
        self.assertEqual(len(ids), len(set(ids)))
        todas = set(ids)
        for _, p in motor.preguntas():
            for r in p.get("relacionadas", []):
                self.assertIn(r, todas, f"{p['id']} → {r}")
        for r in motor.datos()["sin_respuesta"].get("relacionadas", []):
            self.assertIn(r, todas)

    def test_todas_las_acciones_resuelven(self):
        acciones = [a for _, p in motor.preguntas() for a in p.get("acciones", [])] + motor.datos()["sin_respuesta"]["acciones"]
        for a in acciones:
            nombres = [a["url_nombre"]] + ([a.get("sin_moto", "garaje:bienvenida")] if a.get("con_moto") else [])
            for nombre in nombres:
                try:
                    reverse(nombre, args=[1] if a.get("con_moto") and nombre == a["url_nombre"] else [])
                except NoReverseMatch:
                    self.fail(f"No existe la URL {nombre}")


class BuscadorTests(TestCase):
    def test_encuentra_por_palabras_clave(self):
        casos = {
            "¿Cuándo vence el SOAT?": "soat",
            "hoy tengo pico y placa?": "pico-placa",
            "me vare y necesito grua": "emergencia",
            "como se calcula el kilometraje": "km-estimado",
            "quiero instalar la app en el iphone": "instalar-app",
            "tecnomecanica de moto nueva": "tecnomecanica",
        }
        for texto, esperado in casos.items():
            r = motor.responder(texto=texto)
            self.assertEqual(r["fuente"], "faq", texto)
            self.assertEqual(r["id"], esperado, texto)

    def test_sin_respuesta_lleva_al_foro(self):
        r = motor.responder(texto="receta de arepas con queso")
        self.assertEqual(r["fuente"], "sin_respuesta")
        self.assertIn(reverse("foro:preguntar"), [a["url"] for a in r["acciones"]])

    def test_forma_de_respuesta(self):
        r = motor.responder(pregunta_id="lo-urgente")
        self.assertEqual(set(r), {"fuente", "id", "pregunta", "respuesta", "acciones", "relacionadas"})
        self.assertTrue(all(isinstance(t, str) for t in r["respuesta"]))
        # sin sesión, la acción de la moto lleva a agregar una
        self.assertEqual(r["acciones"][0]["url"], reverse("garaje:bienvenida"))


class VistasTests(TestCase):
    def test_catalogo_anonimo(self):
        r = self.client.get(reverse("ayuda:catalogo"))
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("Chispa", d["saludo"])
        self.assertGreaterEqual(len(d["temas"]), 7)
        self.assertNotIn("respuesta", d["temas"][0]["preguntas"][0])

    def test_catalogo_con_nombre(self):
        u = get_user_model().objects.create_user(username="ana", email="ana@x.co", password="clave-segura-123", first_name="Ana María")
        self.client.force_login(u)
        self.assertIn("Ana", self.client.get(reverse("ayuda:catalogo")).json()["saludo"])

    def test_preguntar(self):
        r = self.client.get(reverse("ayuda:preguntar"), {"id": "pico-placa"})
        self.assertEqual(r.json()["id"], "pico-placa")
        r = self.client.get(reverse("ayuda:preguntar"), {"q": "cupón de descuento"})
        self.assertEqual(r.json()["id"], "cupones")
        self.assertEqual(self.client.get(reverse("ayuda:preguntar")).status_code, 400)
        self.assertEqual(self.client.post(reverse("ayuda:preguntar"), {"q": "soat"}).status_code, 405)

    def test_boton_en_todas_las_paginas(self):
        r = self.client.get(reverse("talleres:directorio"))
        self.assertContains(r, 'id="chispa-chat"')
        self.assertContains(r, "chispa-chat.js")
