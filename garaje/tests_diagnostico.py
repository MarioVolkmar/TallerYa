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
        self.despiece = despiece = Despiece.objects.create(linea=self.nmax, version="BBE4", anio=2024)
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
        r = self.resultado({"s": "frena_mal", "cual": "del", "como": "poco"})
        ids = [p["id"] for p in r.context["piezas"]]
        self.assertIn(self.pastilla.pk, ids)
        self.assertEqual(len(ids), 1)  # el tornillo no entra
        # La pieza abre la guía ahí mismo: ya no enlaza a la ficha de la moto
        self.assertNotContains(r, f"?pieza={self.pastilla.pk}")
        self.assertContains(r, f'data-guia-pieza="{self.pastilla.pk}"')

    def test_moto_ajena_no_se_usa(self):
        otro = User.objects.create_user("b@x.com", "b@x.com", "x")
        Motociclista.objects.create(nombre="B", celular="573000000001", usuario=otro)
        self.client.force_login(otro)
        r = self.client.get(self.url, {"moto": self.moto.pk})
        self.assertIsNone(r.context["moto"])
        self.assertEqual(r.context["paso"], "tipo")

    RESULTADO_FRENO = {"s": "frena_mal", "cual": "del", "como": "poco"}

    def resultado(self, params):
        """El resultado con el esquema ya en caché: primero se pide aparte (?parte=esquema), como hace el navegador."""
        self.client.get(self.url, {**params, "parte": "esquema"})
        return self.client.get(self.url, params)

    def test_sin_cache_el_esquema_llega_aparte_con_aviso(self):
        datos = {"despiece": self.despiece.pk, **self.RESULTADO_FRENO}
        r = self.client.get(self.url, datos)              # caché fría: la página sale ya, sin armar los dibujos
        self.assertEqual(r.context["esquemas"], [])
        self.assertContains(r, "data-diferido=")
        self.assertContains(r, "Preparando el esquema")
        self.assertContains(r, "garaje/js/diagnostico.js")
        parte = self.client.get(r.context["esquema_diferido"])
        self.assertContains(parte, 'id="diag-esquema"')
        self.assertContains(parte, f'data-guia-pieza="{self.pastilla.pk}"')
        self.assertNotContains(parte, "<html")
        r = self.client.get(self.url, datos)              # ya en caché: el esquema va en la misma página
        self.assertNotContains(r, "data-diferido=")
        self.assertEqual(len(r.context["esquemas"]), 1)

    def test_motero_con_moto_ve_esquema_y_no_la_leyenda_de_agregar(self):
        self.client.force_login(self.usuario)
        r = self.resultado(self.RESULTADO_FRENO)
        self.assertNotContains(r, "Agrega tu moto al garaje")
        self.assertNotContains(r, "Agrega esta moto a tu garaje")
        self.assertEqual(len(r.context["esquemas"]), 1)
        esquema = r.context["esquemas"][0]
        # Todas las piezas dibujadas del sistema, numeradas; la sospechosa marcada y primero en la lista
        self.assertGreater(len(esquema["marcas"]), 1)
        self.assertEqual([m["id"] for m in esquema["sospechosas"]], [self.pastilla.pk])
        self.assertTrue(esquema["resto"])
        self.assertContains(r, "Puede ser una de estas")
        self.assertContains(r, "Resto del sistema")
        self.assertContains(r, "Toca un número para ver la pieza")
        # Ya no sale la sección de piezas aparte
        self.assertNotContains(r, "Piezas a revisar")
        self.assertNotContains(r, "Ver en el esquema")

    def test_visitante_con_moto_del_catalogo(self):
        r = self.client.get(self.url)
        self.assertContains(r, f'<option value="{self.despiece.pk}"')
        r = self.client.get(self.url, {"despiece": self.despiece.pk})
        self.assertEqual(r.context["paso"], "sintoma")  # la transmisión sale de la línea (NMAX = cvt)
        self.assertContains(r, "Transmisión CVT")
        r = self.resultado({"despiece": self.despiece.pk, **self.RESULTADO_FRENO})
        self.assertEqual([p["id"] for p in r.context["piezas"]], [self.pastilla.pk])
        self.assertEqual(len(r.context["esquemas"]), 1)
        self.assertContains(r, "Crea tu cuenta gratis")
        self.assertContains(r, reverse("cuentas:registro"))

    def test_motero_elige_moto_del_catalogo_aunque_tenga_una_en_el_garaje(self):
        self.client.force_login(self.usuario)
        r = self.client.get(self.url, {"despiece": self.despiece.pk, **self.RESULTADO_FRENO})
        self.assertIsNone(r.context["moto"])
        self.assertContains(r, "Agrega esta moto a tu garaje")
        self.assertContains(r, reverse("garaje:agregar"))

    def test_sin_moto_no_sale_esquema(self):
        r = self.client.get(self.url, {"t": "cadena", **self.RESULTADO_FRENO})
        self.assertEqual(r.context["esquemas"], [])
        self.assertNotContains(r, "Esquema del sistema")
        self.assertNotContains(r, "diag-esquema-dibujo")
        self.assertContains(r, "para ver el esquema con las piezas a revisar")

    def test_motero_abre_la_guia_del_despiece_con_sus_datos(self):
        self.client.force_login(self.usuario)
        r = self.client.get(self.url, self.RESULTADO_FRENO)
        # El visor real del despiece (su guía de pieza), con los datos de la moto del garaje
        self.assertContains(r, "garaje/js/despiece.js")
        self.assertContains(r, f'data-datos="{reverse("garaje:despiece_json", args=[self.moto.pk])}"')
        self.assertContains(r, 'id="guia"')
        self.assertNotContains(r, 'id="diag-guia"')        # ya no hay guía propia del diagnóstico

    def test_visitante_abre_la_guia_con_el_json_publico_del_despiece(self):
        r = self.client.get(self.url, {"despiece": self.despiece.pk, **self.RESULTADO_FRENO})
        url = reverse("garaje:diagnostico_despiece", args=[self.despiece.pk])
        self.assertContains(r, f'data-datos="{url}"')
        datos = self.client.get(url).json()
        self.assertIn("laminas", datos)
        self.assertNotIn("registro", datos)
        ids = {p["id"] for l in datos["laminas"] for p in l["partes"]}
        self.assertIn(self.pastilla.pk, ids)
        self.assertGreater(len(ids), 1)                    # el sistema completo, no solo la sospechosa
        self.assertEqual(self.client.get(reverse("garaje:diagnostico_despiece", args=[99999])).status_code, 404)

    def test_sin_moto_no_hay_guia(self):
        r = self.client.get(self.url, {"t": "cadena", **self.RESULTADO_FRENO})
        self.assertNotContains(r, 'id="diag-guia"')

    def test_esquema_una_fila_por_numero(self):
        from .models import ParteDespiece
        # Otra fila con el mismo número (variante de código): en el esquema sale una sola vez
        ParteDespiece.objects.create(lamina=self.pastilla.lamina, ref=2, codigo="90109-08299", descripcion="BOLT")
        self.client.force_login(self.usuario)
        r = self.resultado(self.RESULTADO_FRENO)
        refs = [m["ref"] for m in r.context["esquemas"][0]["marcas"]]
        self.assertEqual(len(refs), len(set(refs)))

    def test_buscador_sin_anio_y_combobox(self):
        r = self.client.get(self.url)
        nombre = f"{self.nmax.marca.nombre} {self.nmax.nombre}"
        self.assertContains(r, f">{nombre}</option>")
        self.assertNotContains(r, f"{nombre} · 2024")
        self.assertContains(r, 'role="combobox"')
        self.assertContains(r, 'role="listbox"')
        self.assertContains(r, "diag_buscador.js")
        r = self.client.get(self.url, {"despiece": self.despiece.pk})
        self.assertContains(r, f"{nombre}<small>del catálogo</small>")

    def test_no_la_ruedes_enlaza_a_te_varaste(self):
        url = reverse("talleres:emergencias") + "?necesito=grua"
        r = self.client.get(self.url, {"t": "cadena", **self.RESULTADO_FRENO})   # frenos gastados: "No la ruedes"
        self.assertContains(r, url)
        r = self.client.get(self.url, {"t": "cadena", "s": "electrico", "que": "tablero"})   # "Puedes seguir rodando"
        self.assertNotContains(r, url)


class SeguridadDiagnosticoTests(TestCase):
    """Correcciones del Auditor mecánico: los casos que no se deben rodar."""

    def test_llanta_baja_no_se_rueda(self):
        clave = dx.resultado("inestable", {"t": "cvt", "como": "pinchada"})
        self.assertEqual(clave, "llanta_baja")
        self.assertEqual(dx.RESULTADOS[clave]["urgencia"], "parar")
        self.assertEqual(dx.servicio_de(clave), "Llantas")

    def test_inestable_lleva_a_direccion_y_alineacion(self):
        self.assertEqual(dx.resultado("inestable", {"t": "cadena", "como": "bambolea"}), "direccion")
        self.assertEqual(dx.resultado("inestable", {"t": "cadena", "como": "pesada"}), "direccion_dura")
        self.assertEqual(dx.resultado("inestable", {"t": "cadena", "como": "lado"}), "alineacion")

    def test_humo_del_motor_con_olor_a_cable_es_corto(self):
        self.assertIsNone(dx.resultado("humo", {"t": "cadena", "color": "motor"}))   # falta preguntar el olor
        clave = dx.resultado("humo", {"t": "cadena", "color": "motor", "olor": "cable"})
        self.assertEqual(clave, "corto_electrico")
        self.assertEqual(dx.RESULTADOS[clave]["urgencia"], "parar")
        self.assertEqual(dx.resultado("humo", {"t": "cadena", "color": "motor", "olor": "aceite"}), "aceite_en_escape")


class EsquemaPorLaminaTests(TestCase):
    """Freno de tambor dibujado con la rueda, nombres de taller ("pastas"), pestañas por lámina y aviso sin dibujo."""

    def setUp(self):
        self.url = reverse("garaje:diagnostico")
        self.linea = LineaMoto.objects.get(nombre="NKD 125")
        self.despiece = Despiece.objects.create(linea=self.linea, version="X1", anio=2022)

    def lamina(self, figura, diagrama, pieza, titulo, partes):
        lamina = Lamina.objects.create(despiece=self.despiece, figura=figura, titulo=titulo, titulo_es=titulo,
                                       pieza=pieza, diagrama=diagrama)
        return [ParteDespiece.objects.create(lamina=lamina, ref=i + 1, codigo=f"{figura}-{i}", descripcion=d, nombre_es=n)
                for i, (d, n) in enumerate(partes)]

    def resultado(self, params):
        datos = {"despiece": self.despiece.pk, "t": "cadena", **params}
        parte = self.client.get(self.url, {**datos, "parte": "esquema"})
        return self.client.get(self.url, datos), parte

    def test_freno_de_tambor_en_la_lamina_de_la_rueda(self):
        banda, = self.lamina(30, "rueda_tambor", "llanta_tras", "Rueda trasera y freno de tambor",
                             [("SHOE, BRAKE", "Banda de freno")])
        r, _ = self.resultado({"s": "frena_mal", "cual": "tras", "como": "poco"})
        self.assertEqual(len(r.context["esquemas"]), 1)
        self.assertIn(banda.pk, [m["id"] for m in r.context["esquemas"][0]["sospechosas"]])

    def test_pastas_de_freno_cuentan_como_pastillas(self):
        pasta, = self.lamina(31, "freno_disco", "freno_del", "Caliper delantero", [("PASTAS FRENO DELANTERO", "Pastas freno delantero")])
        r, _ = self.resultado({"s": "frena_mal", "cual": "del", "como": "poco"})
        self.assertIn(pasta.pk, [m["id"] for m in r.context["esquemas"][0]["sospechosas"]])

    def test_varias_causas_una_pestana_por_lamina_y_las_demas_al_tocarlas(self):
        filtro, = self.lamina(40, "admision", "filtro_aire", "Filtro de aire", [("ELEMENT, AIR CLEANER", "Filtro de aire")])
        carb, = self.lamina(41, "carburador", "", "Carburador", [("CARBURETOR ASSY", "Carburador")])
        clave = "minimo_inestable"   # varias causas: filtro de aire, carburación, cuerpo de aceleración
        from .vista_diagnostico import _laminas_de
        res = dx.RESULTADOS[clave]
        laminas = _laminas_de(self.despiece, None, dx.sistemas_a_armar(res))
        esquemas = dx.esquemas(dx.piezas_candidatas(clave, laminas, limite=16), laminas, maximo=4)
        self.assertEqual([e["nombre"] for e in esquemas][:2], ["Filtro de aire", "Carburador"])
        from django.template.loader import render_to_string
        html = render_to_string("garaje/_diag_esquema.html", {"esquemas": esquemas, "esquema_url": "/x/?parte=esquema"})
        self.assertIn('role="tablist"', html)
        self.assertEqual(html.count('role="tab"'), len(esquemas))
        self.assertIn(f'data-url="/x/?parte=esquema&amp;lamina={esquemas[1]["id"]}"', html)
        self.assertEqual(html.count("<figure"), 1)            # solo la primera viene dibujada

    def test_pestana_diferida_devuelve_solo_su_dibujo(self):
        banda, = self.lamina(30, "rueda_tambor", "llanta_tras", "Rueda trasera y freno de tambor", [("SHOE, BRAKE", "Banda de freno")])
        datos = {"despiece": self.despiece.pk, "t": "cadena", "s": "frena_mal", "cual": "tras", "como": "poco"}
        parte = self.client.get(self.url, {**datos, "parte": "esquema"})
        lamina_id = parte.context["esquemas"][0]["id"]
        sola = self.client.get(self.url, {**datos, "parte": "esquema", "lamina": lamina_id})
        self.assertContains(sola, f'data-esquema="{lamina_id}"')
        self.assertNotContains(sola, "Esquema del sistema")

    def test_sin_dibujo_del_sistema_sale_un_aviso_y_no_un_hueco(self):
        self.lamina(50, "admision", "filtro_aire", "Filtro de aire", [("ELEMENT, AIR CLEANER", "Filtro de aire")])
        r, parte = self.resultado({"s": "frena_mal", "cual": "tras", "como": "poco"})
        self.assertEqual(r.context["esquemas"], [])
        self.assertContains(r, "no encontramos un dibujo de")
        self.assertContains(parte, "no encontramos un dibujo de")
