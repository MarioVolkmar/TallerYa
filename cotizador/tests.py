"""Pruebas del piloto del cotizador. Ninguna llama a internet: la red de Mercado Libre se simula con mock."""
import os
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from garaje.models import Despiece, Lamina, LineaMoto, Moto, ParteDespiece, TareaMantenimiento

from . import filtro, servicio
from .fuentes import mercadolibre
from .models import Cotizacion, TokenMercadoLibre

SIN_ML = {"ML_ACCESS_TOKEN": "", "ML_APP_ID": "", "ML_SECRET": "", "ML_REFRESH_TOKEN": ""}


def item(titulo, precio, ciudad="Medellín", iid="MCO123"):
    return {"id": iid, "title": titulo, "price": precio, "currency_id": "COP",
            "permalink": f"https://articulo.mercadolibre.com.co/{iid}", "condition": "new",
            "seller_address": {"city": {"name": ciudad}, "state": {"name": "Antioquia"}}, "seller": {"nickname": "x"}}


RESPUESTA_ML = {"results": [
    item("Pastillas Freno Delantero Yamaha Nmax 155 2DP-F5805-00", 48000, iid="MCO1"),
    item("Pastillas de freno Nmax 155 cerámicas", 39000, "Itagüí", iid="MCO2"),
    item("Pastillas Freno Nmax Connected", 42000, "Bogotá", iid="MCO3"),
    item("Pastillas freno Nmax kevlar", 45000, iid="MCO4"),
    item("Pastillas Freno Pulsar NS 200", 35000, iid="MCO5"),         # otra moto
    item("Llavero Pastilla Freno Nmax", 9000, iid="MCO6"),             # basura
    item("Disco De Freno Nmax 155", 120000, iid="MCO7"),               # otra pieza
    item("Pastillas Freno Nmax 155 Brembo", 950000, iid="MCO8"),       # precio atípico
]}


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.nmax = LineaMoto.objects.get(nombre="NMAX 155")
        despiece = Despiece.objects.create(linea=self.nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=despiece, figura=22, titulo="FRONT BRAKE CALIPER",
                                       titulo_es="Freno delantero", pieza="freno_del")
        self.parte = ParteDespiece.objects.create(
            lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT", nombre_es="Pastillas de freno",
            tarea=TareaMantenimiento.objects.get(clave="pastillas-del"), x=.6, y=.6)
        User = get_user_model()
        self.usuario = User.objects.create_user("ana@x.com", "ana@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Ana", celular="573001112244", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=self.nmax, modelo=2024, km_inicial=30000,
                                        km_actual=30000)


class FiltroTests(TestCase):
    def test_quita_basura_otra_pieza_otra_moto_y_atipicos(self):
        crudos = [mercadolibre._normalizar(i) for i in RESPUESTA_ML["results"]]
        ok, descartes = filtro.filtrar(crudos, nombre="Pastillas de freno", codigo="2DP-F5805-00",
                                       linea="NMAX 155", otras_lineas=["NS", "Pulsar", "NMAX"])
        self.assertEqual({r["precio"] for r in ok}, {48000, 39000, 42000, 45000})
        motivos = {r["precio"]: m for r, m in descartes}
        self.assertIn("otra moto", motivos[35000])
        self.assertIn("llavero", motivos[9000])
        self.assertEqual(motivos[120000], "es otra pieza")
        self.assertEqual(motivos[950000], "precio atípico")
        self.assertEqual(ok[0]["precio"], 39000)  # compatibles primero, del más barato al más caro
        self.assertEqual(filtro.resumen(ok), (39000, 43500, 48000))

    def test_codigo_exacto_basta_aunque_el_titulo_no_diga_la_pieza(self):
        ok, _ = filtro.filtrar([{"titulo": "Yamaha 2DPF580500 original", "precio": 50000}],
                               nombre="Pastillas de freno", codigo="2DP-F5805-00", linea="NMAX 155")
        self.assertEqual(len(ok), 1)

    def test_palabra_clave_usa_la_primera_palabra_con_sentido(self):
        self.assertEqual(filtro.palabra_clave("Kit de arrastre"), "arrast")
        self.assertEqual(filtro.palabra_clave("Filtro de aceite"), "filtro")


@mock.patch.dict(os.environ, SIN_ML)
class SinCredencialesTests(Base):
    def test_sin_token_usa_ejemplo_y_no_llama_a_la_red(self):
        with mock.patch.object(mercadolibre, "_pedir", side_effect=AssertionError("no debía llamar")):
            cot = servicio.cotizar(servicio.datos_parte(self.parte))
        self.assertTrue(cot.es_ejemplo)
        self.assertTrue(cot.minimo <= cot.tipico <= cot.maximo)
        self.assertGreaterEqual(cot.descartados, 3)  # el ejemplo trae basura a propósito
        self.assertLessEqual(len(cot.vendedores), 5)


@mock.patch.dict(os.environ, dict(SIN_ML, ML_ACCESS_TOKEN="APP_USR-prueba"))
class MercadoLibreTests(Base):
    def test_consulta_solo_lleva_la_pieza_y_la_moto_y_guarda_cache(self):
        llamadas = []

        def falso(url, datos=None, token=None):
            llamadas.append((url, datos, token))
            return 200, RESPUESTA_ML
        with mock.patch.object(mercadolibre, "_pedir", side_effect=falso):
            cot = servicio.cotizar(servicio.datos_parte(self.parte))
            otra = servicio.cotizar(servicio.datos_parte(self.parte))  # sale de la caché
        self.assertEqual(len(llamadas), 1)
        url, datos, token = llamadas[0]
        self.assertIn("/sites/MCO/search?q=2DP-F5805-00%20NMAX%20155", url)
        self.assertNotIn("ana", url.lower())
        self.assertEqual(token, "APP_USR-prueba")
        self.assertEqual((cot.minimo, cot.tipico, cot.maximo), (39000, 43500, 48000))
        self.assertEqual(cot.fuente, Cotizacion.Fuente.MERCADOLIBRE)
        self.assertEqual(cot.descartados, 4)
        self.assertEqual(otra.pk, cot.pk)
        self.assertEqual(Cotizacion.objects.get().pedidos, 2)
        self.assertTrue(all(v["enlace"].startswith("https://") for v in cot.vendedores))

    def test_dato_viejo_se_refresca_y_si_la_red_falla_se_sirve_el_viejo(self):
        with mock.patch.object(mercadolibre, "_pedir", return_value=(200, RESPUESTA_ML)):
            cot = servicio.cotizar(servicio.datos_parte(self.parte))
        Cotizacion.objects.filter(pk=cot.pk).update(consultado_en=timezone.now() - timedelta(hours=25))
        with mock.patch.object(mercadolibre, "_pedir", side_effect=mercadolibre.ErrorFuente("caído")):
            viejo = servicio.cotizar(servicio.datos_parte(self.parte))
        self.assertEqual(viejo.tipico, 43500)
        self.assertFalse(viejo.vigente)

    def test_si_la_busqueda_da_403_usa_el_catalogo(self):
        def falso(url, datos=None, token=None):
            if "/sites/MCO/search" in url:
                return 403, {"message": "forbidden"}
            if "/products/search" in url:
                return 200, {"results": [{"id": "MCO999", "name": "Pastillas freno Nmax 155"}]}
            return 200, {"results": [{"item_id": "MCO555", "price": 41000, "currency_id": "COP"},
                                     {"item_id": "MCO556", "price": 44000, "currency_id": "COP"}]}
        with mock.patch.object(mercadolibre, "_pedir", side_effect=falso):
            res = mercadolibre.buscar("pastillas nmax")
        self.assertEqual([r["precio"] for r in res], [41000, 44000])
        self.assertEqual(res[0]["enlace"], "https://articulo.mercadolibre.com.co/MCO-555")


@mock.patch.dict(os.environ, dict(SIN_ML, ML_APP_ID="1", ML_SECRET="s", ML_REFRESH_TOKEN="TG-1"))
class TokenTests(TestCase):
    def test_renueva_y_guarda_el_refresh_token_nuevo(self):
        with mock.patch.object(mercadolibre, "_pedir", return_value=(200, {
                "access_token": "APP_USR-nuevo", "refresh_token": "TG-2", "expires_in": 21600})) as pedir:
            self.assertEqual(mercadolibre._token(), "APP_USR-nuevo")
            self.assertEqual(mercadolibre._token(), "APP_USR-nuevo")  # el segundo sale de la tabla
        self.assertEqual(pedir.call_count, 1)
        self.assertEqual(pedir.call_args.kwargs["datos"]["refresh_token"], "TG-1")
        self.assertEqual(TokenMercadoLibre.objects.get().refresh_token, "TG-2")


@mock.patch.dict(os.environ, SIN_ML)
class VistasTests(Base):
    @override_settings(COTIZADOR_ACTIVO=False)
    def test_bandera_apagada_no_aparece_nada(self):
        self.client.force_login(self.usuario)
        html = self.client.get(reverse("garaje:moto", args=[self.moto.pk])).content.decode()
        self.assertNotIn("cotizador", html.lower())
        self.assertNotIn("Cotizar", html)
        self.assertEqual(self.client.get(reverse("cotizador:parte", args=[self.parte.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("cotizador:codigo") + "?c=2DP-F5805-00").status_code, 404)

    @override_settings(COTIZADOR_ACTIVO=True)
    def test_bandera_encendida_pone_ganchos_y_recuadro(self):
        self.client.force_login(self.usuario)
        html = self.client.get(reverse("garaje:moto", args=[self.moto.pk])).content.decode()
        self.assertIn("cotizador/js/cotizar.js", html)
        self.assertIn('data-cotizar-codigo="2DP-F5805-00"', html)  # botón en «Qué necesitas» del plan
        r = self.client.get(reverse("cotizador:parte", args=[self.parte.pk]))
        self.assertContains(r, "Precio aproximado")
        self.assertContains(r, "Precios de ejemplo")
        self.assertContains(r, "orientativos")
        r = self.client.get(reverse("cotizador:codigo") + "?c=2DP-F5805-00")
        self.assertContains(r, "Lo más común")
        self.assertEqual(self.client.get(reverse("cotizador:codigo") + "?c=NO-EXISTE").status_code, 404)

    @override_settings(COTIZADOR_ACTIVO=True)
    def test_freno_por_usuario(self):
        from . import views
        self.client.force_login(self.usuario)
        url = reverse("cotizador:parte", args=[self.parte.pk])
        with mock.patch.object(views, "MAX_POR_HORA_USUARIO", 2):
            estados = [self.client.get(url).status_code for _ in range(3)]
        self.assertEqual(estados, [200, 200, 429])


@mock.patch.dict(os.environ, dict(SIN_ML, ML_ACCESS_TOKEN="APP_USR-prueba"))
class ComandoTests(Base):
    def test_refresca_las_mas_pedidas_con_tope(self):
        with mock.patch.object(mercadolibre, "_pedir", return_value=(200, RESPUESTA_ML)):
            cot = servicio.cotizar(servicio.datos_parte(self.parte))
        Cotizacion.objects.filter(pk=cot.pk).update(consultado_en=timezone.now() - timedelta(hours=30))
        salida = StringIO()
        with mock.patch.object(mercadolibre, "_pedir", return_value=(200, RESPUESTA_ML)) as pedir:
            call_command("refrescar_cotizaciones", "--max", "0", stdout=salida)
            self.assertEqual(pedir.call_count, 0)
            call_command("refrescar_cotizaciones", "--max", "5", stdout=salida)
            self.assertEqual(pedir.call_count, 1)
        self.assertIn("refrescadas: 1", salida.getvalue())
        cot.refresh_from_db()
        self.assertTrue(cot.vigente)
        self.assertEqual(cot.pedidos, 1)  # el cron no cuenta como pedido
