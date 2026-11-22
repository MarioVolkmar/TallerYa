import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from garaje import etiquetas_3d as e3d


class EtiquetarTresDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.staff = U.objects.create_user("staff@t.co", "staff@t.co", "clave-larga-123", is_staff=True)
        cls.motero = U.objects.create_user("motero@t.co", "motero@t.co", "clave-larga-123")

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        p = mock.patch.object(e3d, "CARPETA", self.dir)
        p.start(); self.addCleanup(p.stop)
        self.modelo = next(iter(e3d.modelos()))

    def test_solo_staff(self):
        url = reverse("garaje:etiquetar_3d", args=[self.modelo])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.motero)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(reverse("garaje:etiquetar_3d_guardar", args=[self.modelo]), "{}", content_type="application/json").status_code, 403)
        self.client.force_login(self.staff)
        r = self.client.get(url)
        self.assertContains(r, "Confirmar y seguir")
        self.assertEqual(self.client.get(reverse("garaje:etiquetar_3d_indice")).status_code, 200)
        self.assertEqual(self.client.get(reverse("garaje:etiquetar_3d", args=["no-existe..x"])).status_code, 404)

    def test_guardar_alimenta_glosario(self):
        self.client.force_login(self.staff)
        url = reverse("garaje:etiquetar_3d_guardar", args=[self.modelo])
        partes = [{"parte": "caucho.llanta_del", "pieza": "llanta_del", "acabado": "caucho", "pos": [0.9, 0.2, 0], "tam": [0.3, 0.3, 0.1], "confirmada": True},
                  {"parte": "x", "pieza": "otra", "acabado": "pintura", "pos": [0.5, 0.5, 0], "tam": [0.1, 0.1, 0.1], "confirmada": False}]
        r = self.client.post(url, json.dumps({"partes": partes}), content_type="application/json")
        j = r.json()
        self.assertEqual((j["ok"], j["partes"], j["glosario"]), (True, 2, 1))
        self.assertEqual(json.loads((self.dir / "glosario.json").read_text(encoding="utf-8"))["entradas"][0]["pieza"], "llanta_del")
        partes[0]["acabado"] = "inventado"
        r = self.client.post(url, json.dumps({"partes": partes}), content_type="application/json")
        self.assertEqual(r.status_code, 400)


class DeduccionTests(TestCase):
    def test_textos_comunes(self):
        from garaje.deduccion_3d import deducir
        casos = {
            "guardabarros delantero negro": ("guardabarros_del", "plastico_mate"),
            "Guardabarros trasero": ("guardabarros_tras", "plastico_mate"),
            "farola": ("frente", "pintura"),
            "tapa lateral azul": ("tapa_lateral", "pintura"),
            "llanta": ("llanta_del", "caucho"),
            "llanta trasera": ("llanta_tras", "caucho"),
            "rin trasero cromado": ("rin_tras", "cromo"),
            "mica del stop": ("stop", "mica_roja"),
            "direccional": ("direccional", "mica_ambar"),
            "asiento": ("asiento", "vinilo"),
            "escape": ("escape", "aluminio"),
        }
        for texto, esperado in casos.items():
            d = deducir(texto)
            self.assertEqual((d["pieza"], d["acabado"]), esperado, texto)
            self.assertFalse(d["por_revisar"], texto)

    def test_material_sin_pieza(self):
        from garaje.deduccion_3d import deducir
        for texto, ac in (("plástico mate", "plastico_mate"), ("plasticos brillantes", "plastico_brillo"), ("cromo", "cromo"), ("posapié metálico", "aluminio")):
            d = deducir(texto)
            self.assertEqual(d["acabado"], ac, texto)
            self.assertFalse(d["por_revisar"], texto)
        self.assertEqual(deducir("tijera trasera negro")["pieza"], "basculante")

    def test_no_inventa(self):
        from garaje.deduccion_3d import deducir
        for texto in ("", "xyzzy raro", "cosa"):
            self.assertTrue(deducir(texto)["por_revisar"], texto)
            self.assertIsNone(deducir(texto)["pieza"])

    def test_frase_aprendida(self):
        from garaje.deduccion_3d import deducir
        d = deducir("Cosa Rara!", {"cosa rara": {"pieza": "pata", "acabado": "chasis"}})
        self.assertEqual((d["pieza"], d["acabado"], d["por_revisar"]), ("pata", "chasis", False))


class GuardarTextoTests(EtiquetarTresDTests):
    test_solo_staff = test_guardar_alimenta_glosario = None  # ya probadas arriba
    def test_guardar_deduce_y_aprende(self):
        self.client.force_login(self.staff)
        url = reverse("garaje:etiquetar_3d_guardar", args=[self.modelo])
        base = {"pos": [0.5, 0.5, 0], "tam": [0.1, 0.1, 0.1], "confirmada": True, "editado": True, "pieza": "otra", "acabado": "pintura"}
        partes = [dict(base, parte="a", texto="guardabarros delantero negro"), dict(base, parte="b", texto="cosa rara")]
        r = self.client.post(url, json.dumps({"partes": partes}), content_type="application/json").json()
        a, b = r["partes_deducidas"]
        self.assertEqual((a["pieza"], a["acabado"], a["por_revisar"]), ("guardabarros_del", "plastico_mate", False))
        self.assertTrue(b["por_revisar"])
        gl = json.loads((self.dir / "glosario.json").read_text(encoding="utf-8"))
        self.assertEqual([f["texto"] for f in gl["frases"]], ["guardabarros delantero negro"])
        guardado = json.loads((self.dir / f"{self.modelo}.json").read_text(encoding="utf-8"))
        self.assertEqual(guardado["partes"][0]["texto"], "guardabarros delantero negro")


class ZonasTests(TestCase):
    def test_zonas_se_limpian_y_deducen(self):
        from garaje.etiquetas_3d import limpiar_zonas
        z = limpiar_zonas([{"grupo": 1, "texto": "mica roja", "vertices": [[0, 9]]}, {"grupo": 2, "texto": "xyzzy", "vertices": [[10, 12]]}])
        self.assertEqual((z[0]["pieza"], z[0]["acabado"], z[0]["por_revisar"]), ("otra", "mica_roja", False))  # material sin pieza vale
        self.assertTrue(z[1]["por_revisar"])
        r = limpiar_zonas([{"grupo": 0, "texto": "tapa lateral azul", "vertices": []}])[0]  # «lo sin pintar»
        self.assertEqual((r["grupo"], r["pieza"], r["acabado"], r["vertices"]), (0, "tapa_lateral", "pintura", []))
        for malo in ([{"grupo": 9, "vertices": [[0, 1]]}], [{"grupo": 1, "vertices": [[5, 1]]}], [{"grupo": 1, "vertices": "x"}]):
            with self.assertRaises(ValueError):
                limpiar_zonas(malo)
