from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista

from .colores_fabrica import color_por_defecto, colores_de_fabrica, paleta_personalizar
from .models import LineaMoto, Moto


class ColoresFabricaTests(TestCase):
    NUEVAS = ["Honda XR 190L", "Suzuki DR 150", "Yamaha XTZ 150", "TVS Raider 125", "Yamaha FZ 2.0", "Hero Hunk 125R",
              "Auteco Bajaj Boxer CT 125", "Hero Hunk 150"]

    def test_cada_linea_nueva_tiene_sus_colores(self):
        for nombre in self.NUEVAS:
            linea = LineaMoto.objects.select_related("marca").get(nombre=nombre.split(" ", 1)[1].replace("Bajaj ", ""))
            self.assertTrue(colores_de_fabrica(f"{linea} 2024"), nombre)

    def test_hunk_150_no_toma_los_de_la_125r(self):
        self.assertEqual(colores_de_fabrica("Hero Hunk 150 2012"), [("#1b1b1b", "Negro"), ("#b5121b", "Rojo")])
        self.assertIn(("#1f5fbf", "Azul y gris"), colores_de_fabrica("Hero Hunk 125R 2024"))
        # Las vecinas no se cruzan: FZ25 / FZ 2.0, Boxer CT 100 / CT 125, XTZ 125 / XTZ 150
        self.assertEqual(colores_de_fabrica("Yamaha FZ 25 2022")[0][1], "Azul y negro")
        self.assertEqual(colores_de_fabrica("Yamaha FZ 2.0 2024")[0][1], "Azul")
        self.assertEqual(colores_de_fabrica("Auteco Bajaj Boxer CT 100 2022")[0][1], "Negro y azul")
        self.assertEqual(colores_de_fabrica("Auteco Bajaj Boxer CT 125 2024")[0][1], "Blanco")
        self.assertNotIn(("#eeeeea", "Blanco"), colores_de_fabrica("Yamaha XTZ 150 2024")[:1])

    def test_todas_las_lineas_del_catalogo_tienen_colores(self):
        from .colores_fabrica import _REGLAS
        usadas = set()
        for linea in LineaMoto.objects.select_related("marca"):
            nombre = f"{linea} 2024"
            regla = next((i for i, (r, _) in enumerate(_REGLAS) if r.search(nombre)), None)
            self.assertIsNotNone(regla, nombre)
            usadas.add(regla)
        self.assertEqual(len(usadas), LineaMoto.objects.count())  # cada línea con su propia lista

    def test_paleta_con_los_de_fabrica_primero_y_sin_repetidos(self):
        paleta = paleta_personalizar("TVS Raider 125 2024")
        self.assertEqual(paleta[0], ("#9a9fa3", "Gris California (de fábrica)"))
        hexes = [h.lower() for h, _ in paleta]
        self.assertEqual(len(hexes), len(set(hexes)))
        self.assertEqual(color_por_defecto("Kawasaki Z900 2022"), "#c62828")  # línea sin lista: el rojo de siempre


class ColorAlRegistrarTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user("c@x.com", "c@x.com", "x")
        self.perfil = Motociclista.objects.create(nombre="C", celular="573004440001", usuario=usuario)
        self.client.force_login(usuario)

    def registrar(self, linea, **extra):
        datos = {"linea_catalogo": str(linea.pk), "modelo": 2024, "km_actual": 1000, "apodo": "", **extra}
        self.client.post(reverse("garaje:agregar"), datos)
        return Moto.objects.get(motociclista=self.perfil)

    def test_sin_elegir_color_queda_el_de_fabrica_mas_comun(self):
        moto = self.registrar(LineaMoto.objects.get(nombre="Raider 125"))
        self.assertEqual(moto.color, "#9a9fa3")

    def test_el_color_elegido_se_respeta(self):
        moto = self.registrar(LineaMoto.objects.get(nombre="Raider 125"), color="#1f4fa8")
        self.assertEqual(moto.color, "#1f4fa8")

    def test_personalizar_muestra_los_de_fabrica(self):
        moto = self.registrar(LineaMoto.objects.get(nombre="XR 190L"))
        r = self.client.get(moto.get_absolute_url())
        self.assertContains(r, "Rojo (de f")  # (dentro del JSON de la página, con la tilde escapada)
