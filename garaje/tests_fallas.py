"""Piloto «Tips y fallas frecuentes» (garaje/fallas.py)."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from cupones.models import Motociclista

from . import fallas
from .intervalos import slug_linea
from .models import LineaMoto, Moto

User = get_user_model()


class DatosFallasTests(TestCase):
    def test_todos_los_archivos_cargan_y_son_validos(self):
        archivos = [r for r in fallas.CARPETA.glob("*.json") if not r.name.startswith("_") and r.name != "generales.json"]
        self.assertGreaterEqual(len(archivos), 33)
        for ruta in archivos:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            fallas.validar(datos, ruta.name)
            self.assertTrue(3 <= len(datos["fallas"]) <= 6, ruta.name)
            self.assertTrue(3 <= len(datos["tips"]) <= 5, ruta.name)
        fallas.limpiar_cache()
        self.assertEqual(set(fallas._generales()), {"scooter", "calle", "enduro"})

    def test_slug_igual_que_intervalos(self):
        nmax = LineaMoto.objects.get(nombre="NMAX 155")
        self.assertEqual(slug_linea(nmax), "yamaha_nmax_155")
        self.assertEqual(fallas.de_linea(nmax)["linea"], "Yamaha NMAX 155")

    def test_validar_rechaza_gravedad_y_fuente_desconocidas(self):
        base = {"clave": "x", "titulo": "t", "sintoma": "s", "causa": "c", "que_hacer": "q", "alcance": "modelo",
                "fuentes": ["manual"]}
        with self.assertRaises(fallas.FallasInvalidas):
            fallas.validar({"fuentes": {"manual": {}}, "fallas": [{**base, "gravedad": "grave"}], "tips": []})
        with self.assertRaises(fallas.FallasInvalidas):
            fallas.validar({"fuentes": {}, "fallas": [{**base, "gravedad": "cuidado"}], "tips": []})


    def test_cada_linea_del_catalogo_tiene_archivo(self):
        sin = [slug_linea(l) for l in LineaMoto.objects.select_related("marca") if not fallas.de_linea(l)]
        self.assertEqual(sin, [])


class SeccionFallasTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user("ana@x.com", "ana@x.com", "Clave-segura-2026")
        self.motero = Motociclista.objects.create(nombre="Ana", celular="573001112222", usuario=usuario)
        self.client.force_login(usuario)

    def _moto(self, nombre_linea):
        linea = LineaMoto.objects.get(nombre=nombre_linea)
        return Moto.objects.create(motociclista=self.motero, linea=linea, modelo=2021, km_inicial=0, km_actual=20000)

    @override_settings(FALLAS_FRECUENTES_ACTIVO=True)
    def test_aparece_con_la_bandera(self):
        moto = self._moto("NMAX 155")
        r = self.client.get(reverse("garaje:moto", args=[moto.pk]))
        self.assertContains(r, 'id="fallas-frecuentes"')
        self.assertContains(r, "Lo que más les pasa a las Yamaha NMAX 155")
        self.assertContains(r, "¿Te está pasando?")
        self.assertContains(r, f"moto={moto.pk}&amp;s=cvt&amp;que=tiembla")
        self.assertContains(r, "garaje/css/fallas.css")

    @override_settings(FALLAS_FRECUENTES_ACTIVO=True)
    def test_resalta_la_tarea_vencida_del_plan(self):
        moto = self._moto("NMAX 155")  # 20.000 km sin registros: la correa (18.000 km) ya pasó
        r = self.client.get(reverse("garaje:moto", args=[moto.pk]))
        self.assertContains(r, "falla--toca")
        self.assertContains(r, "En tu agenda:")
        self.assertContains(r, "(requiere atención)")

    @override_settings(FALLAS_FRECUENTES_ACTIVO=False)
    def test_desaparece_sin_la_bandera(self):
        moto = self._moto("NMAX 155")
        r = self.client.get(reverse("garaje:moto", args=[moto.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "fallas-frecuentes")
        self.assertNotContains(r, "fallas.css")

    @override_settings(FALLAS_FRECUENTES_ACTIVO=True)
    def test_modelo_sin_datos_muestra_tips_generales(self):
        base = LineaMoto.objects.get(nombre="Duke 200")
        linea = LineaMoto.objects.create(marca=base.marca, nombre="Prueba Sin Datos 999", tipo="calle", cilindraje=125)
        moto = Moto.objects.create(motociclista=self.motero, linea=linea, modelo=2021, km_inicial=0, km_actual=1000)
        self.assertIsNone(fallas.de_linea(moto.linea))
        r = self.client.get(reverse("garaje:moto", args=[moto.pk]))
        self.assertContains(r, 'id="fallas-frecuentes"')
        self.assertContains(r, "Cadena después de la lluvia")
        self.assertNotContains(r, "¿Te está pasando?")
