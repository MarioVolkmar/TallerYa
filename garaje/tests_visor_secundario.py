"""Las piezas blancas con tono de fábrica (tapas de la XR 190L) siguen al color secundario de Personalizar."""
import json
import struct
from pathlib import Path

from django.test import SimpleTestCase

RAIZ = Path(__file__).resolve().parent / "static" / "garaje"


class SecundarioEnGlbTests(SimpleTestCase):
    def test_xr190l_tiene_tapas_blancas_con_tono(self):
        d = (RAIZ / "modelos" / "xr190l_tripo4.glb").read_bytes()
        n = struct.unpack("<I", d[12:16])[0]
        nodos = json.loads(d[20:20 + n])["nodes"]
        tapas = [x for x in nodos if x["name"].startswith("blanco.tapa_lateral")]
        self.assertEqual(len(tapas), 2)
        self.assertTrue(all(x["extras"].get("tono") for x in tapas))

    def test_visor_repinta_materiales_secundarios(self):
        glb = (RAIZ / "js" / "moto3d" / "glb.js").read_text(encoding="utf-8")
        visor = (RAIZ / "js" / "moto3d.js").read_text(encoding="utf-8")
        self.assertIn("M.secundarios", glb)
        self.assertIn("moto.M.secundarios", visor)
