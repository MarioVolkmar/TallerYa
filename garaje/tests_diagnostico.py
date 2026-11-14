from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from talleres.models import Barrio, Servicio, Taller

from . import diagnostico as dx
from .despiece_sistemas import SISTEMAS
from .models import Despiece, Lamina, LineaMoto, Moto, ParteDespiece

User = get_user_model()


def _caminos(sintoma, contexto):
    """Todas las combinaciones de respuestas de un síntoma, con su resultado."""
    for p in dx.preguntas_visibles(sintoma, contexto):
        if contexto.get(p["clave"]) not in {v for v, _ in p["opciones"]}:
            for valor, _ in p["opciones"]:
                yield from _caminos(sintoma, {**contexto, p["clave"]: valor})
            return
    yield contexto, dx.resultado(sintoma, contexto)


class DatosDiagnosticoTests(TestCase):
    def test_todo_camino_termina_en_un_resultado_con_sentido(self):
        propios = {"cadena": {"Caja de cambios y clutch", "Kit de arrastre"}, "cvt": {"Transmisión CVT", "Transmisión final"}}
        for t in ("cadena", "cvt"):
            ajenos = propios["cvt" if t == "cadena" else "cadena"]
            for r in ("", "aire", "liquido"):
                for sintoma, _ in dx.sintomas_para(t):
                    for contexto, clave in _caminos(sintoma, {"t": t, "r": r}):
                        self.assertIsNotNone(clave, (sintoma, contexto))
                        res = dx.RESULTADOS[clave]
                        self.assertIn(res["sistema"], SISTEMAS[t])
                        self.assertNotIn(res["sistema"], ajenos, (sintoma, contexto))
                        if r == "aire":
                            self.assertNotEqual(res["sistema"], "Refrigeración", (sintoma, contexto))
                        self.assertIn(res["urgencia"], dx.URGENCIAS)

    def test_sintomas_por_transmision(self):
        self.assertIn("cambios", dict(dx.sintomas_para("cadena")))
        self.assertNotIn("cvt", dict(dx.sintomas_para("cadena")))
        self.assertIn("cvt", dict(dx.sintomas_para("cvt")))
        self.assertNotIn("cambios", dict(dx.sintomas_para("cvt")))

    def test_frenos_y_fuga_de_gasolina_no_se_ruedan(self):
        self.assertEqual(dx.RESULTADOS[dx.resultado("frena_mal", {"t": "cadena", "cual": "del", "como": "poco"})]["urgencia"], "parar")
        self.assertEqual(dx.RESULTADOS[dx.resultado("fuga", {"t": "cvt", "que": "gasolina"})]["urgencia"], "parar")

    def test_servicio_por_sistema(self):
        self.assertEqual(dx.servicio_de("frenos_gastados"), "Frenos")
        self.assertEqual(dx.servicio_de("carga"), "Sistema eléctrico")
        self.assertEqual(dx.servicio_de("kit_arrastre"), "Mantenimiento general")


class VistaDiagnosticoTests(TestCase):
    def setUp(self):
        self.url = reverse("garaje:diagnostico")
        self.frenos, _ = Servicio.objects.get_or_create(nombre="Frenos")
        barrio, _ = Barrio.objects.get_or_create(nombre="Laureles")
        self.taller = Taller.objects.create(nombre="Frenos Don Jairo", responsable="Jairo", whatsapp="573001234567",
                                            direccion="Cl 1", barrio=barrio, activo=True)
        self.taller.servicios.add(self.frenos)
        self.nmax = LineaMoto.objects.get(nombre="NMAX 155")
        despiece = Despiece.objects.create(linea=self.nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=despiece, figura=22, titulo="FRONT BRAKE CALIPER", titulo_es="Freno delantero",
                                       pieza="freno_del", diagrama="freno_disco")
        self.pastilla = ParteDespiece.objects.create(lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT",
                                                     nombre_es="Pastillas de freno")
        ParteDespiece.objects.create(lamina=lamina, ref=2, codigo="90109-08232", descripcion="BOLT")
        self.usuario = User.objects.create_user("ana@x.com", "ana@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Ana", celular="573001112244", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=self.nmax, modelo=2024, km_inicial=1000, km_actual=1000)

    def test_anonimo_elige_tipo_luego_sintoma(self):
        r = self.client.get(self.url)
        self.assertContains(r, "¿Tu moto es de cambios o automática?")
        self.assertContains(r, "no reemplaza la revisión de un mecánico")
        r = self.client.get(self.url, {"t": "cvt"})
        self.assertContains(r, "Transmisión CVT")
        self.assertNotContains(r, "Cambios o clutch")

    def test_pregunta_y_resultado_con_talleres(self):
        r = self.client.get(self.url, {"t": "cadena", "s": "frena_mal"})
        self.assertContains(r, "¿Cuál freno?")
        r = self.client.get(self.url, {"t": "cadena", "s": "frena_mal", "cual": "del", "como": "poco"})
        self.assertContains(r, "No la ruedes")
        self.assertContains(r, "Sistema probable: <strong>Frenos</strong> · Delantero", html=False)
        self.assertContains(r, "Frenos Don Jairo")
        self.assertContains(r, f"{reverse('talleres:directorio')}?servicio={self.frenos.pk}")

    def test_respuesta_invalida_vuelve_a_preguntar(self):
        r = self.client.get(self.url, {"t": "cadena", "s": "frena_mal", "cual": "x"})
        self.assertEqual(r.context["paso"], "pregunta")

    def test_con_moto_resalta_piezas_de_su_despiece(self):
        self.client.force_login(self.usuario)
        r = self.client.get(self.url)  # una sola moto: se usa la suya y su transmisión (NMAX = cvt)
        self.assertEqual(r.context["paso"], "sintoma")
        self.assertContains(r, "Transmisión CVT")
        r = self.client.get(self.url, {"s": "frena_mal", "cual": "del", "como": "poco"})
        ids = [p["id"] for p in r.context["piezas"]]
        self.assertIn(self.pastilla.pk, ids)
        self.assertEqual(len(ids), 1)  # el tornillo no entra
        self.assertContains(r, f"{self.moto.get_absolute_url()}?pieza={self.pastilla.pk}#despiece")

    def test_moto_ajena_no_se_usa(self):
        otro = User.objects.create_user("b@x.com", "b@x.com", "x")
        Motociclista.objects.create(nombre="B", celular="573000000001", usuario=otro)
        self.client.force_login(otro)
        r = self.client.get(self.url, {"moto": self.moto.pk})
        self.assertIsNone(r.context["moto"])
        self.assertEqual(r.context["paso"], "tipo")
