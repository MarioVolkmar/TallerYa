"""Pruebas de los avisos de pico y placa y vencimientos (franja de Mi garaje, notificaciones y comando)."""
from datetime import date, timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from notificaciones.models import Notificacion

from .avisos import (aviso_pico_placa, avisos_documentos, es_urgente, nivel_documento, notificar_moto, texto_vence,
                     umbral)
from .models import Moto, ReglaPicoPlaca

LUNES = date(2026, 11, 9)  # lunes sin festivo; rotación 2026-2: lunes 5 y 8


def crear_moto(correo="ana@x.com", celular="573001110000", **campos):
    usuario = get_user_model().objects.create_user(correo, correo, "x")
    perfil = Motociclista.objects.create(nombre="Ana", celular=celular, usuario=usuario)
    datos = {"marca_otra": "Yamaha", "linea_otra": "NMAX", "tipo_otra": "scooter", "modelo": 2022,
             "km_inicial": 1000, "km_actual": 5000, **campos}
    return Moto.objects.create(motociclista=perfil, **datos)


class AvisosTests(TestCase):
    def test_umbrales(self):
        self.assertEqual([umbral(d) for d in (40, 30, 20, 15, 10, 3, 0)], [None, 30, 30, 15, 15, 3, 3])

    def test_regla_2026_2_cargada_con_fin_por_verificar(self):
        regla = ReglaPicoPlaca.objects.get(ciudad="Medellín", vigente_desde=date(2026, 8, 3))
        self.assertEqual(regla.vigente_hasta, date(2027, 1, 29))
        self.assertTrue(regla.fin_por_verificar)
        self.assertEqual((regla.lunes, regla.viernes), ("5,8", "7,9"))

    def test_escala_unica_en_los_limites(self):
        casos = {31: "ok", 30: "pronto", 8: "pronto", 7: "urgente", 1: "urgente", 0: "urgente", -1: "vencido",
                 None: "desconocido"}
        self.assertEqual({d: nivel_documento(d) for d in casos}, casos)
        self.assertEqual([texto_vence(d) for d in (7, 1, 0, -1, -3)],
                         ["Vence en 7 días", "Vence mañana", "Vence hoy", "Venció ayer", "Vencido hace 3 días"])
        # Caso de la NMAX: SOAT en 1 día y técnico-mecánica en 4 → los dos en rojo
        moto = crear_moto(soat_vence=LUNES + timedelta(days=1), tecno_vence=LUNES + timedelta(days=4))
        self.assertEqual([d["estado"] for d in moto.documentos(LUNES)], ["urgente", "urgente"])

    def test_pico_y_placa_hoy_y_soat(self):
        moto = crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=12))
        self.assertEqual(aviso_pico_placa(moto, LUNES)["titulo"], "Hoy tienes pico y placa")
        self.assertEqual([a["titulo"] for a in avisos_documentos(moto, LUNES)], ["Tu SOAT vence en 12 días"])
        self.assertIsNone(aviso_pico_placa(moto, LUNES + timedelta(days=1)))

    def test_tecno_por_matricula(self):
        moto = crear_moto(matricula=date(2024, 11, 20))  # primera revisión: 20/11/2026
        aviso = avisos_documentos(moto, LUNES)[0]
        self.assertEqual(aviso["titulo"], "Tu técnico-mecánica vence en 11 días")
        self.assertIn("matrícula", aviso["texto"])
        # Si la primera ya pasó, no inventamos una fecha.
        self.assertEqual(avisos_documentos(crear_moto("b@x.com", "573002", matricula=date(2020, 1, 1)), LUNES), [])

    def test_notificaciones_30_15_3_sin_repetir(self):
        vence = LUNES + timedelta(days=30)
        moto = crear_moto(soat_vence=vence)
        creadas = []
        for faltan in (30, 29, 15, 14, 3, 2, 0, -1, -5):
            creadas.append(notificar_moto(moto, vence - timedelta(days=faltan)))
        self.assertEqual(creadas, [1, 0, 1, 0, 1, 0, 0, 1, 0])
        self.assertEqual(Notificacion.objects.filter(clave__startswith=f"doc:{moto.pk}:soat").count(), 4)

    def test_pico_y_placa_respeta_preferencia(self):
        moto = crear_moto(placa="ABC58D", aviso_pico_placa=False)
        self.assertEqual(notificar_moto(moto, LUNES), 0)
        moto.aviso_pico_placa = True
        self.assertEqual(notificar_moto(moto, LUNES), 1)
        self.assertEqual(notificar_moto(moto, LUNES), 0)

    def test_comando_idempotente(self):
        crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=3))
        for esperado in ("Avisos nuevos: 2", "Avisos nuevos: 0"):
            salida = StringIO()
            call_command("avisar_vencimientos", "--fecha", LUNES.isoformat(), stdout=salida)
            self.assertIn(esperado, salida.getvalue())

    def test_colores_en_ficha_y_mi_garaje_sin_franjas(self):
        moto = crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=1), tecno_vence=LUNES + timedelta(days=4))
        Moto.objects.create(motociclista=moto.motociclista, marca_otra="Honda", linea_otra="CB", tipo_otra="calle",
                            modelo=2020, km_inicial=0, km_actual=0, soat_vence=LUNES + timedelta(days=20),
                            tecno_vence=LUNES - timedelta(days=2))
        self.client.force_login(moto.motociclista.usuario)
        with mock.patch("django.utils.timezone.localdate", return_value=LUNES):
            lista = self.client.get(reverse("garaje:garaje") + "?lista=1")
            ficha = self.client.get(moto.get_absolute_url())
        # Ficha: tarjetas de Documentos en rojo, con el texto de la escala; sin fila de chips de avisos.
        self.assertContains(ficha, 'class="doc-tarjeta doc-urgente"', count=2)
        self.assertContains(ficha, "Vence mañana")
        self.assertContains(ficha, "Vence en 4 días")
        self.assertContains(ficha, "Pedir SOAT")
        self.assertContains(ficha, "(por verificar)")
        self.assertNotContains(ficha, "avisos-hoy")
        # Mi garaje: los chips de cada moto con la misma escala, sin línea de resumen.
        for clase in ("doc-chip-urgente", "doc-chip-pronto", "doc-chip-vencido"):
            self.assertContains(lista, f"doc-chip {clase}")
        self.assertContains(lista, "mañana")
        self.assertNotContains(lista, "avisos-resumen")

    def test_campana_urgente_y_acciones(self):
        moto = crear_moto(placa="ABC12D", soat_vence=LUNES + timedelta(days=20), tecno_vence=LUNES + timedelta(days=6))
        from garaje.models import Mantenimiento, TareaMantenimiento
        # Un registro real y vencido (sin registro, lo pasado solo marca "Pronto": la edad de la moto no basta para "Toca ya")
        Mantenimiento.objects.create(moto=moto, tarea=TareaMantenimiento.objects.get(clave="aceite"), km=1000,
                                     fecha=LUNES - timedelta(days=10))
        notificar_moto(moto, LUNES)
        usuario = moto.motociclista.usuario
        acciones = {n.clave.split(":")[2]: n.accion for n in usuario.notificaciones.all()}
        self.assertEqual(acciones, {"soat": "Pedir SOAT", "tecno": "Ver CDA"})
        self.assertTrue(es_urgente(f"pyp:{moto.pk}:{LUNES}", LUNES))
        self.assertFalse(es_urgente(f"pyp:{moto.pk}:{LUNES - timedelta(days=1)}", LUNES))
        self.client.force_login(usuario)
        hoy = mock.patch("django.utils.timezone.localdate", return_value=LUNES)  # al navegar también se generan avisos
        hoy.start()
        self.addCleanup(hoy.stop)
        datos = self.client.get(reverse("notificaciones:panel")).json()
        self.assertEqual((datos["sin_leer"], datos["urgentes"]), (2, 1))  # solo la tecno (6 días: rojo en la escala) es urgente
        self.assertEqual(sorted(n["urgente"] for n in datos["notificaciones"]), [False, True])
        lista = self.client.get(reverse("notificaciones:lista"))
        self.assertContains(lista, "Pedir SOAT")
        # Al abrir la lista también se generan los avisos del plan: "Toca ya" (rojo) cuenta como urgente, igual que la agenda
        urgentes = [n.clave.split(":")[0] for n in usuario.notificaciones.all() if n.urgente]
        self.assertEqual(sorted(urgentes), ["doc", "plan"])
        self.assertContains(lista, "notif-urgente", count=2)
        self.assertEqual(lista.context["notificaciones_urgentes"], 2)
        usuario.notificaciones.update(leida=True)
        self.assertEqual(self.client.get(reverse("notificaciones:panel")).json()["urgentes"], 0)

    def test_notificacion_lleva_a_la_solucion(self):
        from garaje.models import TareaMantenimiento
        from notificaciones.servicios import notificar
        moto = crear_moto(placa="ABC58D")
        usuario = moto.motociclista.usuario
        tarea = TareaMantenimiento.objects.filter(servicio__isnull=False).first()
        ficha = moto.get_absolute_url()
        casos = {  # clave → destino; todas guardadas con el enlace viejo (la ficha), como las que ya existen
            f"doc:{moto.pk}:soat:3d:2026-11-12": f"{reverse('tramites:soat')}?moto={moto.pk}",
            f"doc:{moto.pk}:tecno:vencido:2026-11-01": f"{reverse('tramites:tecnomecanica')}?moto={moto.pk}",
            f"recordar:{moto.pk}:{tarea.pk}:2026-11-09": f"{reverse('talleres:inicio')}?servicio={tarea.servicio_id}",
            f"plan:{moto.pk}:nada:abc": f"{ficha}#plan",  # sin un servicio claro: el plan de la moto
            f"pyp:{moto.pk}:2026-11-09": f"{ficha}#pico-placa",  # nada que resolver: la ficha
        }
        self.client.force_login(usuario)
        for clave, destino in casos.items():
            n = notificar(usuario, clave, "x", url=f"{ficha}#pico-placa" if clave.startswith("pyp") else ficha)
            self.assertRedirects(self.client.get(reverse("notificaciones:ir", args=[n.pk])), destino,
                                 fetch_redirect_response=False)
        self.assertEqual(Notificacion.objects.get(clave__startswith="recordar").accion, "Buscar taller")

    def test_portada_sin_franja_de_avisos(self):
        moto = crear_moto(placa="ABC58D", soat_vence=LUNES + timedelta(days=5))
        self.client.force_login(moto.motociclista.usuario)
        with mock.patch("django.utils.timezone.localdate", return_value=LUNES):
            self.assertNotContains(self.client.get("/"), "avisos-hoy")

    def test_matricula_no_futura(self):
        moto = crear_moto()
        self.client.force_login(moto.motociclista.usuario)
        r = self.client.post(reverse("garaje:editar", args=[moto.pk]), {
            "linea_catalogo": "otra", "marca_otra": "Yamaha", "linea_otra": "NMAX", "tipo_otra": "scooter",
            "modelo": 2022, "matricula": "2099-01-01"})
        self.assertContains(r, "no puede ser futura")


class TareaAvisosTests(TestCase):
    """Endpoint que dispara GitHub Actions a diario (reemplaza un cron de pago)."""
    TOKEN = "t" * 32

    def llamar(self, token=None, nombre="avisos"):
        cabeceras = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        return self.client.post(reverse("garaje:tarea", args=[nombre]), **cabeceras)

    def test_sin_token_configurado_no_existe(self):
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": ""}):
            self.assertEqual(self.llamar(self.TOKEN).status_code, 404)

    def test_token_errado_y_get_rechazados(self):
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": self.TOKEN}):
            self.assertEqual(self.llamar("otro" * 8).status_code, 403)
            self.assertEqual(self.llamar().status_code, 403)
            self.assertEqual(self.client.get(reverse("garaje:tarea", args=["avisos"])).status_code, 405)

    def test_solo_tareas_de_la_lista_fija(self):
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": self.TOKEN}):
            for nombre in ("migrate", "flush", "shell", "recordar_pico_placa"):
                self.assertEqual(self.llamar(self.TOKEN, nombre).status_code, 404)

    def test_avisos_sin_repetir(self):
        crear_moto(soat_vence=date.today() + timedelta(days=3))
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": self.TOKEN}):
            self.assertEqual(self.llamar(self.TOKEN).json(), {"tarea": "avisos", "resultado": "Avisos nuevos: 1"})
            self.assertEqual(self.llamar(self.TOKEN).json()["resultado"], "Avisos nuevos: 0")

    def test_citas_con_el_mismo_token(self):
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": self.TOKEN}):
            r = self.llamar(self.TOKEN, "citas")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"tarea": "citas", "resultado": "Sin citas para recordar."})

    def test_logros_con_el_mismo_token(self):
        with mock.patch.dict("os.environ", {"TAREAS_TOKEN": self.TOKEN}):
            r = self.llamar(self.TOKEN, "logros")
        self.assertEqual((r.status_code, r.json()["tarea"]), (200, "logros"))


class NivelTareaTests(TestCase):
    """Escala de color del plan: rojo (vencido o último 10 % con tope de 500 km, o ≤ 7 días), amarillo, verde."""

    def test_limites(self):
        from .plan import nivel_tarea
        # Bujía cada 8.000 km: rojo con ≤ 500 km (10 % = 800, tope 500)
        self.assertEqual(nivel_tarea("vencido", -10, None, 8000), "vencido")
        self.assertEqual(nivel_tarea("pronto", 500, None, 8000), "urgente")   # en el umbral
        self.assertEqual(nivel_tarea("pronto", 501, None, 8000), "pronto")    # justo fuera
        self.assertEqual(nivel_tarea("pronto", 1500, None, 8000), "pronto")   # el caso de la captura: amarillo
        self.assertEqual(nivel_tarea("ok", 3000, None, 8000), "ok")
        # Aceite cada 2.500 km: 10 % = 250 km
        self.assertEqual(nivel_tarea("pronto", 250, None, 2500), "urgente")
        self.assertEqual(nivel_tarea("pronto", 251, None, 2500), "pronto")
        # Por días (como los documentos) y lo pospuesto
        self.assertEqual(nivel_tarea("pronto", 2000, 7, 8000), "urgente")
        self.assertEqual(nivel_tarea("pronto", 2000, 8, 8000), "pronto")
        self.assertEqual(nivel_tarea("vencido", -10, None, 8000, pospuesta=True), "pronto")

    def test_grupos_y_conteos_usan_el_mismo_nivel(self):
        from .models import TareaMantenimiento
        from .plan import calcular_plan
        from .views import _grupos_agenda
        moto = crear_moto(km_inicial=100, km_actual=100)
        plan = calcular_plan(moto)
        grupos = _grupos_agenda(plan)
        for t in grupos["atencion"]:
            self.assertIn(t.nivel, ("vencido", "urgente"))
        for t in grupos["proximos"]:
            self.assertEqual(t.nivel, "pronto")
        for t in grupos["al_dia"]:
            self.assertEqual(t.nivel, "ok")
        self.assertEqual(len(plan.urgentes), len(grupos["atencion"]))  # "N por hacer" de Mi garaje = Requiere atención


class IntervalosLineaTests(TestCase):
    """Intervalos del manual por línea (garaje/intervalos/*.json): con archivo usa el propio; sin archivo, el general."""

    def setUp(self):
        import json
        import tempfile
        from pathlib import Path
        from . import intervalos
        from .models import LineaMoto
        self.intervalos = intervalos
        self.nmax = LineaMoto.objects.select_related("marca").get(nombre="NMAX 155")
        carpeta = Path(tempfile.mkdtemp())
        (carpeta / f"{intervalos.slug_linea(self.nmax)}.json").write_text(json.dumps({"linea": "NMAX", "tareas": {
            "aceite": {"km": 4000, "dias": 200, "fuente": "Manual p. 7", "aproximado": False, "especificacion": "10W-40"}}}),
            encoding="utf-8")
        patron = mock.patch.object(intervalos, "CARPETA", carpeta)
        patron.start()
        self.addCleanup(patron.stop)
        intervalos.limpiar_cache()
        self.addCleanup(intervalos.limpiar_cache)

    def test_con_archivo_usa_el_propio_y_sin_archivo_el_general(self):
        from .models import TareaMantenimiento
        from .plan import calcular_plan
        self.assertEqual(self.intervalos.slug_linea(self.nmax), "yamaha_nmax_155")
        general = TareaMantenimiento.objects.get(clave="aceite").intervalo_km
        con = crear_moto(linea=self.nmax, km_inicial=100, km_actual=3700)
        t = next(t for t in calcular_plan(con).tareas if t.tarea.clave == "aceite")
        self.assertEqual((t.tarea.intervalo_km, t.tarea.intervalo_dias, t.km_restantes), (4000, 200, 300))
        self.assertEqual(t.nivel, "urgente")  # el nivel se recalcula con el intervalo propio (10 % de 4.000 = 400)
        self.assertEqual(TareaMantenimiento.objects.get(clave="aceite").intervalo_km, general)  # la base no cambia
        sin = crear_moto("b@x.com", "573002220000", km_inicial=100, km_actual=3700)  # sin línea del catálogo
        t2 = next(t for t in calcular_plan(sin).tareas if t.tarea.clave == "aceite")
        self.assertEqual(t2.tarea.intervalo_km, general)
        # La ficha muestra de dónde sale
        self.client.force_login(con.motociclista.usuario)
        self.assertContains(self.client.get(con.get_absolute_url()), "Según el manual: 10W-40")

    def test_intervalo_para_la_guia(self):
        from .intervalos import intervalo_para, texto
        propio = intervalo_para("aceite", self.nmax)
        self.assertEqual((propio["km"], propio["dias"], propio["texto"], propio["propio"]),
                         (4000, 200, "Cada 4.000 km o cada 7 meses", True))
        self.assertEqual(propio["especificacion"], "10W-40")
        general = intervalo_para("aceite")
        self.assertFalse(general["propio"])
        self.assertEqual(general["texto"], texto(general["km"], general["dias"]))
        self.assertIsNone(intervalo_para("no-existe"))
        self.assertEqual(texto(10000, 365), "Cada 10.000 km o cada 12 meses")

    def test_versiones_por_anio_ganan_sobre_la_linea(self):
        import json
        from .intervalos import IntervaloInvalido, de_linea, intervalo_para, validar
        ruta = self.intervalos.CARPETA / "yamaha_nmax_155.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos["versiones"] = [{"nombre": "Nueva", "desde": 2020, "hasta": None,
                               "tareas": {"aceite": {"km": 5000, "fuente": "Manual 2020", "aproximado": True}}}]
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        self.intervalos.limpiar_cache()
        self.assertEqual(de_linea(self.nmax, 2019)["aceite"]["km"], 4000)   # antes del rango: la de la línea
        self.assertEqual(de_linea(self.nmax, 2021)["aceite"]["km"], 5000)   # en el rango: la versión
        self.assertEqual(de_linea(self.nmax)["aceite"]["km"], 4000)         # sin año: la de la línea
        self.assertTrue(intervalo_para("aceite", self.nmax, 2022)["aproximado"])
        with self.assertRaises(IntervaloInvalido):  # rangos que se cruzan
            validar({"tareas": {}, "versiones": [{"desde": 2015, "hasta": 2020, "tareas": {}},
                                                 {"desde": 2019, "hasta": None, "tareas": {}}]})

    def test_valida_el_formato(self):
        from .intervalos import IntervaloInvalido, validar
        with self.assertRaises(IntervaloInvalido):
            validar({"tareas": {"aceite": {"km": 3000}}})  # sin fuente
        with self.assertRaises(IntervaloInvalido):
            validar({"tareas": {"aceite": {"km": "3000", "fuente": "x"}}})
        with self.assertRaises(IntervaloInvalido):
            validar({"tareas": {"aceite": {"km": 3000, "fuente": "x", "kms": 1}}})
        with self.assertRaises(IntervaloInvalido):
            validar({"tareas": {"aceite": {"km": 0, "dias": 0, "fuente": "x"}}})

    def test_null_usa_el_general_y_cero_es_sin_limite(self):
        from .intervalos import aplicar
        from .models import TareaMantenimiento
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        solo_km = aplicar(aceite, None, {"aceite": {"km": 4000, "dias": None, "fuente": "x"}})
        self.assertEqual((solo_km.intervalo_km, solo_km.intervalo_dias), (4000, aceite.intervalo_dias))
        ausente = aplicar(aceite, None, {"aceite": {"km": 4000, "fuente": "x"}})
        self.assertEqual(ausente.intervalo_dias, aceite.intervalo_dias)
        sin_dias = aplicar(aceite, None, {"aceite": {"km": 4000, "dias": 0, "fuente": "x"}})
        self.assertEqual((sin_dias.intervalo_km, sin_dias.intervalo_dias), (4000, None))


class ArchivosIntervalosTests(TestCase):
    """Todos los archivos reales de garaje/intervalos/ tienen formato válido y claves de tareas que existen."""

    def test_archivos_del_repo(self):
        import json
        from .intervalos import CARPETA, validar
        from .models import LineaMoto, TareaMantenimiento
        claves = set(TareaMantenimiento.objects.values_list("clave", flat=True))
        from .intervalos import slug_linea
        lineas = {slug_linea(l) for l in LineaMoto.objects.select_related("marca")}
        for ruta in CARPETA.glob("*.json"):
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            validar(datos, ruta.name)
            self.assertLessEqual(set(datos["tareas"]), claves, ruta.name)
            if not ruta.name.startswith("_"):
                self.assertIn(ruta.stem, lineas, f"{ruta.name}: no hay una línea con ese slug")


class AvisoPorCorreoTests(TestCase):
    def test_vencimiento_llega_por_correo_solo_con_correo_verificado(self):
        from django.core import mail
        from django.test import override_settings
        from cuentas.models import Perfil
        vence = LUNES + timedelta(days=30)
        moto = crear_moto(soat_vence=vence)
        with override_settings(SITIO_URL="https://tallerya.test"):
            notificar_moto(moto, LUNES)
            self.assertEqual(len(mail.outbox), 0)  # correo sin verificar: no se escribe
            Perfil.objects.update_or_create(usuario=moto.motociclista.usuario, defaults={"correo_verificado": True})
            notificar_moto(moto, vence - timedelta(days=15))
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn("SOAT", msg.subject)
        self.assertIn("https://tallerya.test/", msg.body)
        self.assertEqual(msg.alternatives[0][1], "text/html")
        notificar_moto(moto, vence - timedelta(days=14))
        self.assertEqual(len(mail.outbox), 1)  # sin repetir
