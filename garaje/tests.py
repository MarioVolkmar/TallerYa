from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from talleres.models import Barrio, Servicio, Taller

from .models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from .plan import calcular_plan


from .utiles_pruebas import usar_intervalos_generales  # noqa: E402

User = get_user_model()


class GarajeTests(TestCase):
    """El catálogo y las tareas vienen de la migración de datos 0002."""

    def setUp(self):
        self.usuario = User.objects.create_user("sofia@x.com", "sofia@x.com", "x", first_name="Sofía")
        self.perfil = Motociclista.objects.create(nombre="Sofía", celular="573001112233", usuario=self.usuario)
        self.client.force_login(self.usuario)
        self.nkd = LineaMoto.objects.get(nombre="NKD 125")
        self.nmax = LineaMoto.objects.get(nombre="NMAX 155")

    def crear_moto(self, linea=None, km=1000, **extra):
        return Moto.objects.create(motociclista=self.perfil, linea=linea or self.nkd, modelo=2022,
                                   km_inicial=km, km_actual=km, **extra)

    def claves(self, moto):
        return {t.tarea.clave for t in calcular_plan(moto).tareas}

    # --- Alta y permisos ---

    def test_agregar_moto_del_catalogo(self):
        r = self.client.post(reverse("garaje:agregar"), {
            "linea_catalogo": str(self.nkd.pk), "modelo": 2022, "color": "#1f4fa8", "km_actual": 15000,
        })
        moto = Moto.objects.get()
        self.assertRedirects(r, moto.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual((moto.km_inicial, moto.km_actual), (15000, 15000))
        self.assertEqual(moto.lecturas.count(), 1)

    def test_agregar_moto_fuera_del_catalogo_exige_datos(self):
        r = self.client.post(reverse("garaje:agregar"), {"linea_catalogo": "otra", "modelo": 2020, "color": "#1b1b1b", "km_actual": 0})
        self.assertContains(r, "Completa este dato")
        self.client.post(reverse("garaje:agregar"), {
            "linea_catalogo": "otra", "marca_otra": "Victory", "linea_otra": "MRX 150", "tipo_otra": "enduro",
            "modelo": 2020, "color": "#1b1b1b", "km_actual": 500,
        })
        moto = Moto.objects.get()
        self.assertIsNone(moto.linea)
        self.assertEqual(moto.specs()["rin_delantero"], 21)  # ficha por defecto de enduro

    def test_no_se_ve_la_moto_de_otro(self):
        otro = User.objects.create_user("otro@x.com", "otro@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Otro", celular="573009998877", usuario=otro)
        ajena = Moto.objects.create(motociclista=perfil, linea=self.nkd, modelo=2020, km_inicial=0, km_actual=0)
        r = self.client.get(ajena.get_absolute_url())
        self.assertRedirects(r, reverse("garaje:garaje") + "?lista=1")
        self.assertNotContains(self.client.get(r.url), "NKD 125 2020")
        self.assertEqual(self.client.post(reverse("garaje:registrar_km", args=[ajena.pk]), {"km": 10}).status_code, 404)
        self.client.post(reverse("garaje:eliminar", args=[ajena.pk]))
        self.assertTrue(Moto.objects.filter(pk=ajena.pk).exists())  # no se puede eliminar la moto de otro

    def test_eliminar_desde_el_garaje(self):
        moto = Moto.objects.create(motociclista=self.perfil, linea=self.nkd, modelo=2021, km_inicial=0, km_actual=0)
        url = reverse("garaje:eliminar", args=[moto.pk])
        self.assertContains(self.client.get(reverse("garaje:garaje") + "?lista=1"), f'data-eliminar="{url}"')
        # En la ficha ya no hay botón: se elimina desde la zona de peligro de "Datos de la moto".
        self.assertNotContains(self.client.get(moto.get_absolute_url()), f'data-eliminar="{url}"')
        self.assertContains(self.client.get(reverse("garaje:editar", args=[moto.pk])), f'action="{url}"')
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), f'data-eliminar="{url}"')
        r = self.client.post(url)
        self.assertRedirects(r, reverse("garaje:garaje") + "?lista=1", fetch_redirect_response=False)
        self.assertFalse(Moto.objects.filter(pk=moto.pk).exists())

    def test_garaje_requiere_sesion(self):
        self.client.logout()
        r = self.client.get(reverse("garaje:garaje"))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    # --- Kilometraje ---

    def test_kilometraje_no_puede_bajar(self):
        moto = self.crear_moto(km=5000)
        self.client.post(reverse("garaje:registrar_km", args=[moto.pk]), {"km": 4000})
        moto.refresh_from_db()
        self.assertEqual(moto.km_actual, 5000)
        self.client.post(reverse("garaje:registrar_km", args=[moto.pk]), {"km": 5600})
        moto.refresh_from_db()
        self.assertEqual(moto.km_actual, 5600)
        self.assertEqual(moto.lecturas.count(), 1)  # la de crear_moto no crea lectura; esta sí

    # --- Plan según la ficha ---

    def test_tareas_dependen_de_la_ficha(self):
        nkd, nmax = self.claves(self.crear_moto(self.nkd)), self.claves(self.crear_moto(self.nmax))
        self.assertIn("cadena-lubricar", nkd)
        self.assertNotIn("correa-cvt", nkd)
        self.assertIn("bandas-tras", nkd)          # NKD: freno trasero de tambor
        self.assertNotIn("refrigerante", nkd)      # refrigerada por aire
        self.assertIn("correa-cvt", nmax)
        self.assertNotIn("cadena-lubricar", nmax)
        self.assertIn("pastillas-tras", nmax)      # NMAX: disco atrás
        self.assertIn("refrigerante", nmax)        # radiador

    def test_estados_por_kilometraje(self):
        moto = self.crear_moto(km=20000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")  # cada 2500 km
        Mantenimiento.objects.create(moto=moto, tarea=aceite, km=18000, fecha=timezone.localdate())
        estado = lambda: next(t for t in calcular_plan(moto).tareas if t.tarea.clave == "aceite")
        moto.km_actual = 19500  # 1500/2500 = 60 %
        self.assertEqual(estado().estado, "ok")
        moto.km_actual = 20100  # 2100/2500 = 84 %
        self.assertEqual(estado().estado, "pronto")
        moto.km_actual = 20600
        self.assertEqual(estado().estado, "vencido")
        self.assertEqual(estado().km_restantes, -100)

    def test_estado_por_tiempo(self):
        moto = self.crear_moto(km=20000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")  # o cada 120 días
        Mantenimiento.objects.create(moto=moto, tarea=aceite, km=19900, fecha=timezone.localdate() - timedelta(days=130))
        t = next(t for t in calcular_plan(moto).tareas if t.tarea.clave == "aceite")
        self.assertEqual(t.estado, "vencido")

    def test_sin_registro_en_moto_usada_y_supuesto_en_moto_nueva(self):
        usada = next(t for t in calcular_plan(self.crear_moto(km=30000)).tareas if t.tarea.clave == "aceite")
        self.assertEqual(usada.estado, "desconocido")
        nueva = next(t for t in calcular_plan(self.crear_moto(km=300)).tareas if t.tarea.clave == "aceite")
        self.assertEqual(nueva.estado, "ok")
        self.assertTrue(nueva.supuesto)

    def test_ritmo_y_fecha_estimada(self):
        moto = self.crear_moto(km=10000)
        hoy = timezone.localdate()
        LecturaKm.objects.create(moto=moto, km=10000, fecha=hoy - timedelta(days=20))
        LecturaKm.objects.create(moto=moto, km=10600, fecha=hoy)
        moto.km_actual = 10600
        plan = calcular_plan(moto)
        self.assertAlmostEqual(plan.km_por_dia, 30)

    def test_registrar_mantenimiento_reinicia_el_conteo(self):
        moto = self.crear_moto(km=30000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        self.client.post(reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
                         {"tarea": aceite.pk, "km": 30000, "fecha": timezone.localdate().isoformat()})
        t = next(t for t in calcular_plan(moto).tareas if t.tarea.clave == "aceite")
        self.assertEqual(t.estado, "ok")
        # No se puede registrar con más kilómetros que los actuales
        self.client.post(reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
                         {"tarea": aceite.pk, "km": 99999, "fecha": timezone.localdate().isoformat()})
        self.assertEqual(moto.mantenimientos.count(), 1)

    def test_piezas_resumen_el_peor_estado(self):
        moto = self.crear_moto(km=30000)
        frenos = TareaMantenimiento.objects.get(clave="pastillas-del")
        Mantenimiento.objects.create(moto=moto, tarea=frenos, km=29900, fecha=timezone.localdate())
        # pastillas al día, pero el líquido de frenos (misma pieza) no tiene registro
        self.assertEqual(calcular_plan(moto).piezas()["freno_del"]["estado"], "desconocido")

    # --- Página ---

    def test_detalle_incluye_datos_3d_y_talleres_sugeridos(self):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        taller = Taller.objects.create(nombre="Llantas Ya", responsable="X", whatsapp="573001234567",
                                       direccion="X", barrio=barrio, activo=True)
        taller.servicios.add(Servicio.objects.get(nombre="Llantas"))
        moto = self.crear_moto(km=14000)
        moto.km_actual = 16000  # llantas (asumidas de fábrica) pasan su intervalo
        moto.save()
        r = self.client.get(moto.get_absolute_url())
        self.assertContains(r, 'id="datos-moto"')
        self.assertContains(r, '"rin_delantero": 18')  # NKD 125: rines de 18 (migración 0026)
        self.assertContains(r, "Llantas Ya")
        # Al tocar la llanta en el 3D se ofrece el taller recomendado y el directorio filtrado por su servicio
        llanta = r.context["datos_3d"]["piezas"]["llanta_tras"]["acciones"]
        self.assertEqual(llanta["taller"]["nombre"], "Llantas Ya")
        self.assertIn("wa.me/573001234567", llanta["taller"]["whatsapp"])
        self.assertIn(f"?servicio={Servicio.objects.get(nombre='Llantas').pk}", llanta["talleres"])


@tag("lenta")
class DespieceTests(TestCase):
    def setUp(self):
        import tempfile
        from django.core.files.base import ContentFile
        from django.test import override_settings

        self.tmp = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.tmp)
        self.override.enable()
        self.nmax = LineaMoto.objects.get(nombre="NMAX 155")
        from .models import Despiece, Lamina, ParteDespiece
        self.d2024 = Despiece.objects.create(linea=self.nmax, version="BBE4", anio=2024)
        self.d2020 = Despiece.objects.create(linea=self.nmax, version="BDG1", anio=2020)
        self.lamina = Lamina(despiece=self.d2024, figura=22, titulo="FRONT BRAKE CALIPER",
                             titulo_es="Freno delantero", pieza="freno_del", ancho=10, alto=10)
        self.lamina.imagen.save("fig22.png", ContentFile(b"\x89PNG"), save=False)
        self.lamina.save()
        pastillas = TareaMantenimiento.objects.get(clave="pastillas-del")
        self.parte = ParteDespiece.objects.create(lamina=self.lamina, ref=9, codigo="2DP-F5805-00",
                                                  descripcion="BRAKE PAD KIT", tarea=pastillas, x=.6, y=.6)
        ParteDespiece.objects.create(lamina=self.lamina, ref=2, codigo="90109-08232", descripcion="BOLT", x=.2, y=.7)
        ParteDespiece.objects.create(lamina=self.lamina, ref=3, codigo="X", descripcion="CALIPER ASSY")  # sin marcar

        self.usuario = User.objects.create_user("ana@x.com", "ana@x.com", "x")
        perfil = Motociclista.objects.create(nombre="Ana", celular="573001112244", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=self.nmax, modelo=2024, km_inicial=30000, km_actual=30000)

    def tearDown(self):
        self.override.disable()

    def test_precalentar_despiece_es_idempotente(self):
        from io import StringIO
        from unittest import mock
        from django.core.cache import caches
        from django.core.management import call_command
        from . import views
        caches["despiece"].clear()
        primera, segunda = StringIO(), StringIO()
        call_command("precalentar_despiece", "--max-segundos", "0", stdout=primera)
        call_command("precalentar_despiece", stdout=segunda)
        self.assertIn("Armados 1, ya estaban 0, faltan 0", primera.getvalue())   # solo el catálogo con láminas
        self.assertIn("Armados 0, ya estaban 1, faltan 0", segunda.getvalue())
        self.client.force_login(self.usuario)
        with mock.patch.object(views, "_laminas_base", side_effect=AssertionError("debía salir de la caché")):
            self.assertEqual(self.client.get(reverse("garaje:despiece_json", args=[self.moto.pk])).status_code, 200)

    def test_elige_el_catalogo_del_anio_mas_cercano(self):
        from .models import Despiece
        self.assertEqual(Despiece.para(self.moto), self.d2024)
        self.moto.modelo = 2021
        self.assertEqual(Despiece.para(self.moto), self.d2020)  # prefiere el de su año o anterior
        self.moto.linea = LineaMoto.objects.get(nombre="NKD 125")
        self.assertIsNone(Despiece.para(self.moto))

    def test_datos_del_visor_solo_partes_marcadas_y_con_estado(self):
        from .views import datos_despiece
        datos = datos_despiece(self.d2024, calcular_plan(self.moto))
        partes = datos["laminas"][0]["partes"]
        self.assertEqual([p["ref"] for p in partes], [2, 3, 9])  # todas las partes van a la lista
        self.assertIsNone(next(p for p in partes if p["ref"] == 3)["x"])  # sin marcar: no aparece en el dibujo
        pastillas = next(p for p in partes if p["ref"] == 9)
        self.assertEqual(pastillas["estado"], "desconocido")  # moto usada sin registro
        self.assertEqual(datos["laminas"][0]["estado"], "desconocido")

    def test_a_400_km_es_roja_en_plan_3d_despiece_y_campana(self):
        """Un solo criterio de color: pastillas (cada 6.000 km) a 400 km es "urgente" → roja en todas partes."""
        from garaje.avisos import es_urgente
        from notificaciones.servicios import generar_para
        from .views import _grupos_agenda, datos_despiece
        pastillas = TareaMantenimiento.objects.get(clave="pastillas-del")
        Mantenimiento.objects.create(moto=self.moto, tarea=pastillas, km=30000 - 5600, fecha=timezone.localdate())
        plan = calcular_plan(self.moto)
        t = next(t for t in plan.tareas if t.tarea == pastillas)
        self.assertEqual((t.estado, t.nivel, t.color, t.km_restantes), ("pronto", "urgente", "vencido", 400))
        self.assertIn(t, _grupos_agenda(plan)["atencion"])                       # plan: Requiere atención
        self.assertEqual(plan.piezas()["freno_del"]["estado"], "vencido")         # 3D
        datos = datos_despiece(self.d2024, plan)                                   # despiece
        lamina = datos["laminas"][0]
        self.assertEqual((lamina["estado"], lamina["inicial"]), ("vencido", self.parte.pk))
        self.assertEqual(next(p for p in lamina["partes"] if p["ref"] == 9)["estado"], "vencido")
        generar_para(self.usuario)                                                 # campana
        claves = list(self.usuario.notificaciones.values_list("clave", flat=True))
        self.assertTrue(any(c.startswith(f"plan:{self.moto.pk}:vencido:") and es_urgente(c) for c in claves))

    def test_pagina_de_la_moto_muestra_el_despiece(self):
        self.client.force_login(self.usuario)
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, 'data-datos="/garaje/%d/despiece.json"' % self.moto.pk)
        self.assertNotContains(r, 'id="datos-despiece"')  # las láminas ya no van incrustadas
        r = self.client.get(reverse("garaje:despiece_json", args=[self.moto.pk]))
        self.assertContains(r, "2DP-F5805-00")

    def test_marcar_desde_el_admin(self):
        from django.urls import reverse as rev
        admin = User.objects.create_superuser("admin", "admin@x.com", "x")
        url = rev("admin:garaje_lamina_marcar", args=[self.lamina.pk])
        self.client.force_login(self.usuario)  # no es staff
        self.assertNotEqual(self.client.post(url, {}, content_type="application/json").status_code, 200)
        self.client.force_login(admin)
        r = self.client.post(url, {"parte": self.parte.pk, "x": 1.7, "y": 0.25}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.parte.refresh_from_db()
        self.assertEqual((self.parte.x, self.parte.y), (1.0, 0.25))  # se limita a la imagen
        self.client.post(url, {"parte": self.parte.pk, "quitar": True}, content_type="application/json")
        self.parte.refresh_from_db()
        self.assertIsNone(self.parte.x)
        self.assertEqual(self.client.get(rev("admin:garaje_lamina_change", args=[self.lamina.pk])).status_code, 200)

    def test_lectura_de_filas_del_catalogo(self):
        from .management.commands.importar_despiece import _filas
        palabras = [
            (422, 65, 426, 74, "9", 0, 0, 0), (431, 65, 479, 74, "2DP�F5805�00", 0, 0, 1),
            (503, 65, 521, 74, ".BRAKE", 0, 0, 2), (523, 65, 547, 74, "PAD", 0, 0, 3), (549, 65, 575, 74, "KIT", 0, 0, 4),
            (666, 65, 670, 74, "1", 0, 0, 5),
        ]
        fila = _filas(palabras)[0]
        self.assertEqual(fila, {"ref": 9, "codigo": "2DP-F5805-00", "descripcion": "BRAKE PAD KIT", "nivel": 1, "cantidad": 1,
                                "espanol": ""})

    def test_lectura_de_catalogo_bilingue(self):
        # Catálogos Yamaha de Colombia: español en la fila y el inglés justo debajo.
        from .management.commands.importar_despiece import _filas
        palabras = [
            (422, 116, 426, 124, "4", 0, 0, 0), (431, 116, 479, 124, "1FD–F580U–01", 0, 0, 1),
            (503, 116, 533, 124, "CALIBRE", 0, 0, 2), (535, 116, 574, 124, "COMPLETO", 0, 0, 3), (666, 116, 670, 124, "1", 0, 0, 4),
            (503, 124, 533, 132, "CALIPER", 0, 0, 5), (535, 124, 554, 132, "ASSY", 0, 0, 6),
            (422, 133, 426, 142, "5", 0, 0, 7), (431, 133, 479, 142, "2BM–F5802–00", 0, 0, 8),
            (503, 133, 531, 141, "PISTON", 0, 0, 9), (666, 133, 670, 142, "1", 0, 0, 10),
        ]
        filas = _filas(palabras)
        self.assertEqual((filas[0]["descripcion"], filas[0]["espanol"], filas[0]["codigo"]),
                         ("CALIPER ASSY", "CALIBRE COMPLETO", "1FD-F580U-01"))
        self.assertEqual((filas[1]["descripcion"], filas[1]["espanol"]), ("PISTON", ""))

    def test_lectura_de_catalogo_auteco(self):
        from .management.commands.importar_despiece import _filas_auteco
        w = lambda x, y, texto: (x, y, x + 10, y + 8, texto, 0, 0, 0)
        palabras = [w(333, 45, "FIG."), w(353, 45, "REFERENCIA"), w(452, 45, "DESCRIPCIÓN"), w(552, 45, "CANT."),
                    w(591, 45, "OBSERVACIÓN"),
                    w(335, 65, "6"), w(351, 65, "JW131807"), w(416, 65, "Pastas"), w(446, 65, "Freno"), w(470, 65, "Delantero"),
                    w(563, 65, "1"),
                    w(351, 78, "JW131899"), w(416, 78, "Pastas"), w(446, 78, "Freno"), w(563, 78, "2"), w(582, 78, "Para"),
                    w(120, 90, "14")]  # número del dibujo, fuera de la tabla
        enc = {p[4].upper().rstrip("."): p for p in palabras[:5]}
        filas = _filas_auteco(palabras, enc)
        self.assertEqual([(f["ref"], f["codigo"], f["descripcion"], f["cantidad"]) for f in filas],
                         [(6, "JW131807", "Pastas Freno Delantero", 1), (6, "JW131899", "Pastas Freno", 2)])

    def test_glosario(self):
        from .despiece_glosario import ayuda_para, traducir
        self.assertEqual(traducir("BRAKE PAD KIT"), "Pastillas de freno (juego)")
        self.assertEqual(traducir("TIRE (110/70-13M/C 48P)"), "Llanta 110/70-13")
        self.assertEqual(traducir("DISK, BRAKE (RIGHT)"), "Disco de freno (lado derecho)")
        self.assertEqual(traducir("FUSE (7.5A BL)"), "Fusible 7,5 A")
        self.assertEqual(traducir("PLUG, SPARK (NGK CPR8EA)"), "Bujía NGK CPR8EA")
        self.assertEqual(traducir("BOLT, FLANGE DEEP RECESS"), "Tornillo con arandela")
        self.assertEqual(traducir("INNER TUBE COMP.1"), "Barra cromada de la suspensión")
        self.assertEqual(traducir("BOLT 1"), "Tornillo")
        self.assertEqual(traducir("SOMETHING RARE"), "")
        self.assertIn("disco", ayuda_para("BRAKE PAD KIT"))
        self.assertTrue(ayuda_para("V-BELT"))
        self.assertEqual(ayuda_para("BOLT"), "")


class GuiaPiezasTests(TestCase):
    def test_guias_especificas_genericas_y_por_sistema(self):
        from .despiece_fichas import ficha_para
        pastillas = ficha_para("BRAKE PAD KIT", "freno_del")
        self.assertIn("disco", pastillas["que_hace"])
        self.assertTrue(pastillas["senales"] and pastillas["tips"])
        self.assertEqual(ficha_para("PLUG, SPARK (NGK CPR8EA)")["dificultad"], "facil")
        self.assertIn("Sujeta", ficha_para("BOLT, FLANGE DEEP RECESS")["que_hace"])        # categoría tornillería
        self.assertIn("Sella", ficha_para("O-RING")["que_hace"])                            # categoría empaques
        self.assertIn("rueda", ficha_para("OIL SEAL", "llanta_del")["que_hace"])            # retenedor de rueda
        self.assertIn("aceite", ficha_para("OIL SEAL", "suspension_del")["que_hace"])       # retenedor de barra
        self.assertTrue(ficha_para("ALGO RARISIMO")["que_hace"])                            # nunca queda vacía

    def test_intervalo_en_texto(self):
        from .views import intervalo_texto
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        self.assertEqual(intervalo_texto(aceite), "Cada 2.500 km o cada 4 meses")
        liquido = TareaMantenimiento.objects.get(clave="liquido-frenos")
        self.assertEqual(intervalo_texto(liquido), "Cada 20.000 km o cada 2 años")


@tag("lenta")
class DiagramasPropiosTests(TestCase):
    def test_todos_los_diagramas_se_dibujan_con_sus_puestos(self):
        from . import diagramas
        for clave in diagramas.DIAGRAMAS:
            svg, puestos = diagramas.dibujar(clave)
            self.assertTrue(svg.startswith("<svg"), clave)
            self.assertTrue(puestos, clave)
            for puesto, (x, y) in puestos.items():
                self.assertTrue(0 <= x <= 1 and 0 <= y <= 1, f"{clave}.{puesto} fuera del dibujo")
            # Toda regla apunta a un puesto que existe en el dibujo
            for _, puesto in diagramas.REGLAS[clave]:
                if puesto is not None:
                    self.assertIn(puesto, puestos, f"{clave}: la regla apunta a '{puesto}', que no está dibujado")
            # La franja de tornillería va en todos los dibujos
            for puesto, _, _ in diagramas.HERRAJES:
                self.assertIn(puesto, puestos, f"{clave}: falta '{puesto}' en la franja")

    def test_piezas_de_mantenimiento_tienen_puesto(self):
        from .diagramas import puesto_para
        casos = [("freno_disco", "BRAKE PAD KIT", "pastillas"), ("freno_disco", "DISK, BRAKE (RIGHT)", "disco"),
                 ("cvt", "V-BELT", "correa"), ("cvt", "WEIGHT SET", "rodillos"), ("cvt", ".CLUTCH WEIGHT SHOE SET", "zapatas"),
                 ("aceite", "PLUG,DRAIN 1", "tapon"), ("aceite", "STRAINER, OIL", "malla"), ("admision", "ELEMENT, AIR CLEANER", "filtro"),
                 ("culata", "PLUG, SPARK (NGK CPR8EA)", "bujia"), ("valvulas", "VALVE, INTAKE", "valvula_admision"),
                 ("radiador", ".CAP, RADIATOR", "tapa"), ("rueda", "TIRE (110/70-13M/C 48P)", "llanta"),
                 ("suspension_delantera", "...OIL SEAL", "retenedor"), ("amortiguadores", "SHOCK ABSORBER ASSY, REAR", "amortiguador"),
                 ("electrico", "BATTERY ASSY (YUASA YTZ6V)", "bateria"), ("bomba_freno", ".CAP, RESERVOIR", "tapa")]
        for clave, descripcion, esperado in casos:
            self.assertEqual(puesto_para(clave, descripcion), esperado, descripcion)

    def test_piezas_en_espanol_tienen_puesto(self):
        from . import diagramas
        casos = [("freno_disco", "Pastas Freno Delantero", "pastillas"), ("freno_disco", "Resorte Pasta Freno", "resorte_pastillas"),
                 ("rueda", "Rodamiento Bolas 6302C3", "rodamientos"), ("rueda", "LLANTA DEL. 90X90 R17", "llanta"),
                 ("culata", "Bujía UR4AC", "bujia"), ("valvulas", "Válvula Admisión", "valvula_admision"),
                 ("suspension_delantera", "Reten Tubo Telescópico", "retenedor"), ("electrico", "Batería 12V (Gel)", "bateria"),
                 ("rueda", "BEARING", "rodamientos"),  # el inglés sigue igual
                 ("rueda_trasera", "SPROCKET, DRIVEN (41T)", "corona"), ("transmision", "SPROCKET, DRIVE (14T)", "pinon"),
                 ("transmision", "Piñón Salida 14T", "pinon"), ("rueda_trasera", "Cadena 520x108L (Con O'ring)", "cadena"),
                 ("transmision", "Buje Caja", "h_buje"), ("transmision", "Kit Guías Cadenilla", "h_soporte"),  # a la franja
                 # La tornillería menuda va a la franja, salvo las piezas pequeñas con lugar propio en el dibujo
                 ("freno_disco", "Tornillo Caliper", "h_tornillo"), ("freno_disco", "Pasador de las Pastillas", "pasador"),
                 ("freno_disco", "PIN, PAD", "pasador"), ("valvulas", "Tuerca Calibración Válvula", "tornillo_calibracion"),
                 ("freno_tambor", "Bandas Freno Trasero", "bandas"), ("freno_tambor", "Indicador Desgaste Bandas", "indicador"),
                 ("encendido", "Bujía RG6HCC", "bujia"), ("encendido", "Capuchón Bujía Izquierdo", "capuchon")]
        for clave, descripcion, esperado in casos:
            self.assertEqual(diagramas.puesto_para(clave, descripcion), esperado, descripcion)
        # Dibujos nuevos y franja de tornillería
        casos = [("transmision", "Eje Clutch Completo", "eje_principal"), ("transmision", "Piñón de 3a. (28T)", "engranajes"),
                 ("transmision", "Eje de Salida", "eje_salida"), ("transmision", "GEAR, 2ND WHEEL (28T)", "engranajes_salida"),
                 ("carcasa", "Carcasa Izquierda", "carcasa_izq"), ("carcasa", "Swiche Neutra", "swiche"),
                 ("carcasa", "Visor Nivel Aceite", "visor"), ("carcasa", "Anillo Retenedor 17.5x1.5", "h_seguro"),
                 ("rueda_trasera", "Corona (Sprocket Trasero)", "corona"), ("rueda_trasera", "Porta Sprocket", "porta_sprocket"),
                 ("rueda_tambor", "Bandas de Freno (Juego)", "bandas"), ("rueda_tambor", "Disco Freno Trasero", "h_otros"),
                 ("freno_disco", "Arandela 6 mm.", "h_arandela"), ("rueda", "RING, SNAP", "h_seguro"),
                 ("culata", "O-Ring (Empaque Redondo)", "h_empaque"), ("rueda", "Piñón Velocímetro", "h_engranaje")]
        for clave, descripcion, esperado in casos:
            self.assertEqual(diagramas.puesto_para(clave, descripcion), esperado, descripcion)
        for clave, reglas in diagramas.REGLAS_ES.items():
            puestos = diagramas.dibujar(clave)[1]
            for _, puesto in reglas:
                if puesto is not None:
                    self.assertIn(puesto, puestos, f"{clave}: '{puesto}' no está dibujado")

    def test_vista_svg(self):
        r = self.client.get(reverse("garaje:diagrama", args=["freno_disco"]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertEqual(self.client.get("/garaje/diagrama/no-existe.svg").status_code, 404)

    def test_lamina_dibuja_solo_sus_piezas_y_la_guia_muestra_la_pieza_sola(self):
        from . import diagramas
        completo = diagramas.dibujar_lamina("freno_disco", ())
        solo_caliper = diagramas.dibujar_lamina("freno_disco", (), frozenset({"caliper", "pastillas"}))
        self.assertIn("disco", completo["puestos"])
        # Las piezas sin número quedan tenues como contexto (no se pierde el detalle del conjunto)
        self.assertIn("disco", solo_caliper["puestos"])
        self.assertIn('opacity="0.42"', solo_caliper["svg"])
        # ...pero las opcionales que la moto no trae no se dibujan (el pedal en un freno delantero)
        delantero = diagramas.dibujar_lamina("freno_completo", (), frozenset({"bomba", "caliper"}))
        self.assertNotIn("pedal", delantero["puestos"])
        self.assertIn("<svg", diagramas.dibujar_pieza("freno_disco", "caliper"))
        self.assertIn("<svg", diagramas.dibujar_pieza("freno_disco", "h_tornillo"))
        self.assertIsNone(diagramas.dibujar_pieza("freno_disco", "no-existe"))
        self.assertIsNone(diagramas.dibujar_pieza("cvt", "clutch"))          # puesto que es solo un ancla, sin formas
        # Freno completo (láminas que traen bomba, manguera, caliper y pedal juntos)
        for clave, descripcion, esperado in [("freno_completo", "Bomba Freno Delantero Completa", "bomba"),
                                             ("freno_completo", "Tanque Bomba Freno Trasero", "deposito"),
                                             ("freno_completo", "Tapa Tanque Bomba Freno", "tapa"),
                                             ("freno_completo", "Manguera Freno Trasero", "manguera"),
                                             ("freno_completo", "Tornillo Manguera Freno", "banjo"),
                                             ("freno_completo", "Swiche Freno Delantero", "interruptor"),
                                             ("freno_completo", "Pedal Freno con Bujes", "pedal"),
                                             ("freno_completo", "Juego Pastas Freno Trasero", "pastillas"),
                                             ("freno_completo", "Soporte Tanque Bomba Freno", "soporte_deposito")]:
            self.assertEqual(diagramas.puesto_para(clave, descripcion), esperado, descripcion)
        r = self.client.get("/garaje/diagrama/freno_disco/caliper.svg")
        self.assertEqual(r["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertEqual(self.client.get("/garaje/diagrama/freno_disco/no-existe.svg").status_code, 404)

    def test_variantes_sin_descripcion_se_unen_a_su_pieza(self):
        """Las filas "- -" (otra versión de la moto) y "x Desde Modelo" no son piezas aparte: son otra referencia."""
        from .models import Despiece, Lamina, ParteDespiece
        from .views import _unir_variantes
        despiece = Despiece.objects.create(linea=LineaMoto.objects.get(nombre="NMAX 155"), version="X", anio=2020)
        lamina = Lamina.objects.create(despiece=despiece, figura=13, titulo="CLUTCH COVER", pieza="aceite", diagrama="carcasa")
        tapa = ParteDespiece.objects.create(lamina=lamina, ref=1, codigo="DU101013", descripcion="Cubierta Clutch -")
        ParteDespiece.objects.create(lamina=lamina, ref=1, codigo="DF101018", descripcion="- - -")
        kit = ParteDespiece.objects.create(lamina=lamina, ref=99, codigo="A1", descripcion="Kit Rin x Hasta Modelo", cantidad=2014)
        ParteDespiece.objects.create(lamina=lamina, ref=99, codigo="A2", descripcion="x Desde Modelo", cantidad=2015)
        otra = ParteDespiece.objects.create(lamina=lamina, ref=2, codigo="B1", descripcion="Empaque")
        piezas, alternos = _unir_variantes(list(lamina.partes.all()))
        self.assertEqual([p.pk for p in piezas], [tapa.pk, otra.pk, kit.pk])
        self.assertEqual(alternos[tapa.pk], [{"codigo": "DF101018", "nota": "otra versión"}])
        self.assertEqual(alternos[kit.pk], [{"codigo": "A2", "nota": "Desde Modelo 2015"}])

    def test_datos_usan_el_dibujo_propio_aunque_no_haya_plano_original(self):
        from .models import Despiece, Lamina, ParteDespiece
        from . import diagramas
        from .views import datos_despiece
        nmax = LineaMoto.objects.get(nombre="NMAX 155")
        despiece = Despiece.objects.create(linea=nmax, version="BBE4", anio=2024)
        lamina = Lamina.objects.create(despiece=despiece, figura=22, titulo="FRONT BRAKE CALIPER", pieza="freno_del",
                                       diagrama="freno_disco")  # sin imagen: como en producción
        ParteDespiece.objects.create(lamina=lamina, ref=9, codigo="2DP-F5805-00", descripcion="BRAKE PAD KIT",
                                     tarea=TareaMantenimiento.objects.get(clave="pastillas-del"))
        ParteDespiece.objects.create(lamina=lamina, ref=2, codigo="90109-08232", descripcion="BOLT")
        ParteDespiece.objects.create(lamina=lamina, ref=3, codigo="9", descripcion="BOLT")
        ParteDespiece.objects.create(lamina=lamina, ref=20, codigo="0", descripcion="SOMETHING ODD")
        usuario = User.objects.create_user("b@x.com", "b@x.com", "x")
        perfil = Motociclista.objects.create(nombre="B", celular="573001119999", usuario=usuario)
        moto = Moto.objects.create(motociclista=perfil, linea=nmax, modelo=2024, km_inicial=100, km_actual=100)
        datos = datos_despiece(despiece, calcular_plan(moto))
        lam = datos["laminas"][0]
        # La franja lleva solo los grupos usados; los tornillos siempre van a la franja aunque el dibujo los tenga
        self.assertIn("freno_disco.svg?h=h_tornillo:2,h_otros:1&v=", lam["imagen"])
        self.assertIsNone(lam["original"])
        partes = {p["ref"]: p for p in lam["partes"]}
        self.assertIsNotNone(partes[9]["x"])                                   # pastillas en su puesto
        self.assertNotEqual((partes[2]["x"], partes[2]["y"]), (partes[3]["x"], partes[3]["y"]))  # dos tornillos: dos casillas en la franja
        franja = diagramas.dibujar_lamina("freno_disco", (("h_tornillo", 2), ("h_otros", 1)))
        self.assertEqual((partes[20]["x"], partes[20]["y"]), franja["casillas"]["h_otros"][0])  # sin puesto: "Otras piezas"
        self.assertGreater(partes[2]["y"], 0)
        # Ningún par de números del dibujo queda montado
        lugares = [(p["x"], p["y"]) for p in lam["partes"]]
        for i, a in enumerate(lugares):
            for b in lugares[i + 1:]:
                if a != b:
                    self.assertGreater(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** .5, 0.03)
        r = self.client.get("/garaje/diagrama/freno_disco.svg?h=h_otros:1,h_tornillo:2,raro:9")
        self.assertContains(r, "Otras piezas")
        self.assertNotContains(r, "Arandelas")

    def test_kit_muestra_sus_piezas_y_la_valvula_tenue(self):
        from . import diagramas
        kit = diagramas.puestos_kit("valvulas", "Kit Resorte y Arandela Válvulas")
        self.assertEqual(kit, ("base_resorte", "cunas", "platillo", "resortes"))
        self.assertIsNone(diagramas.puestos_kit("valvulas", "Kit Arandelas de Ajuste"))      # lainas: no son esas piezas
        self.assertIsNone(diagramas.puestos_kit("valvulas", "Resorte válvula"))              # no es kit
        texto = diagramas.clave_kit("valvulas", kit)
        self.assertIn("--valvula_admision", texto)
        r = self.client.get(f"/garaje/diagrama/valvulas/{texto}.svg")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'opacity="0.42"')                                              # la válvula, de referencia
        self.assertEqual(self.client.get("/garaje/diagrama/valvulas/nada-raro.svg").status_code, 404)

    def test_kit_de_arrastre_se_separa_de_la_rueda(self):
        from . import diagramas
        for texto in ("Sprocket Trasero 44 Dientes", "Cadena 428 X 120L", "Caucho Porta Sprocket", "Empate Cadena",
                      "Kit Sprocket y Cadena"):
            self.assertTrue(diagramas.es_arrastre("rueda_tambor", texto), texto)
        for texto in ("Eje Rueda Trasera", "Bandas Freno Trasero", "Leva Portabandas Freno", "Tornillo Disco Freno Trasero",
                      "Rodamiento Bolas 6302C3"):
            self.assertFalse(diagramas.es_arrastre("rueda_trasera", texto), texto)

    def test_sistemas_nuevos_ubican_sus_piezas(self):
        from . import diagramas
        casos = {"caja_secundaria": [("MAIN AXLE COMP.", "eje_intermedio"), ("AXLE, DRIVE", "eje_salida"),
                                     ("GEAR, PRIMARY DRIVE", "pinon_primario"), ("OIL SEAL", "retenes")],
                 "cilindro_piston": [("PISTON RING SET", "anillos"), ("PISTON", "piston"), ("Biela", "biela"),
                                     ("Cilindro", "cilindro")],
                 "distribucion": [("CAMSHAFT", "arbol_levas"), ("Eje de levas", "arbol_levas"), ("Cadenilla distribución", "cadenilla"),
                                  ("Balancín", "balancin")],
                 "carburador": [("Boquerel altas #105", "chicles"), ("Flotador", "flotador")],
                 "inyeccion": [("THROTTLE BODY ASSY", "cuerpo"), ("Inyector", "inyector")],
                 "escape": [("MUFFLER ASSY", "silenciador"), ("Protector silenciador", "protector")]}
        for clave, reglas in casos.items():
            for texto, puesto in reglas:
                self.assertEqual(diagramas.puesto_en_dibujo(clave, texto), puesto, f"{clave}: {texto}")


class GuiaCompletaTests(TestCase):
    def test_guia_completa_trae_revision_consecuencias_compra_y_contexto(self):
        from .despiece_fichas import ficha_completa
        pastillas = ficha_completa("BRAKE PAD KIT", "freno_del")
        self.assertTrue(pastillas["como_revisar"] and pastillas["si_no"] and pastillas["al_comprar"])
        self.assertEqual(pastillas["contexto"], "En tu moto hace parte del freno delantero.")
        tornillo = ficha_completa("BOLT, FLANGE", "suspension_del")
        self.assertIn("torque", tornillo["contexto"])                      # tornillo de una parte de seguridad
        self.assertNotIn("torque", ficha_completa("BOLT", "filtro_aire")["contexto"])
        rara = ficha_completa("ALGO RARISIMO", "bateria")
        self.assertTrue(rara["como_revisar"] and rara["si_no"])            # nunca queda sin contenido


class QueHaceEspecificoTests(TestCase):
    def test_piezas_sin_guia_propia_tienen_descripcion_especifica(self):
        from .despiece_fichas import CATEGORIAS, ficha_completa
        genericos = {v["que_hace"] for v in CATEGORIAS.values()}
        casos = [("MAIN SWITCH STEERING LOCK", "bateria", "switch de encendido"),
                 ("NUT, SELF-LOCKING", "llanta_del", "seguridad"),
                 ("BOLT, UNION", "freno_del", "banjo"),
                 ("BOLT, FLANGE DEEP RECESS", "suspension_tras", "basculante"),
                 ("O-RING", "refrigeracion", "refrigeración"),
                 ("SECONDARY SLIDING SHEAVE", "correa", "polea móvil trasera"),
                 ("DISK, REAR BRAKE 2", "freno_tras", "disco")]
        for descripcion, pieza, esperado in casos:
            texto = ficha_completa(descripcion, pieza)["que_hace"]
            self.assertNotIn(texto, genericos, descripcion)
            self.assertIn(esperado, texto, descripcion)


class PersonalizacionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("p@x.com", "p@x.com", "x")
        perfil = Motociclista.objects.create(nombre="P", celular="573001110000", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                        modelo=2024, km_inicial=0, km_actual=0)
        self.url = reverse("garaje:personalizar", args=[self.moto.pk])
        self.client.force_login(self.usuario)

    def enviar(self, datos):
        import json
        return self.client.post(self.url, json.dumps(datos), content_type="application/json")

    def test_guarda_colores_y_calcas_limpias(self):
        r = self.enviar({"color": "#112233", "color_secundario": "#c0c4c8", "calcas": [
            {"diseno": "numero", "zona": "frontal", "color": "#ffffff", "tamano": 9, "posicion": -5, "texto": "1234567890123456789"},
            {"diseno": "llamas", "zona": "lateral", "color": "#f2611d"},
        ]})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual((self.moto.color, self.moto.color_secundario), ("#112233", "#c0c4c8"))
        numero = self.moto.calcas[0]
        self.assertEqual((numero["tamano"], numero["posicion"]), (1.6, -1.0))  # se limitan a rangos válidos
        self.assertEqual(len(numero["texto"]), 14)
        self.assertEqual(self.moto.calcas[1]["texto"], "")

    def test_guarda_estilo_limpio(self):
        r = self.enviar({"color": "#112233", "color_secundario": "#c0c4c8", "calcas": [], "estilo": {
            "acabado": "mate", "color2": "#FFFFFF", "chasis": "", "rin": "estrella",
            "accesorios": ["sliders", "baul", "baul"]}})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        # Lo vacío o de fábrica no se guarda; colores en minúscula; accesorios sin repetir y ordenados
        self.assertEqual(self.moto.estilo, {"acabado": "mate", "color2": "#ffffff", "rin": "estrella",
                                            "accesorios": ["baul", "sliders"]})
        self.assertContains(self.client.get(self.moto.get_absolute_url()), '"acabado": "mate"')

    def test_calca_con_imagen_propia(self):
        import base64
        png = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 40).decode()
        r = self.enviar({"calcas": [{"diseno": "imagen", "zona": "lateral", "color": "#ffffff", "imagen": png}]})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.calcas[0]["imagen"], png)
        # Sin imagen, con algo que no es imagen o demasiado pesada: se rechaza
        falso = "data:image/png;base64," + base64.b64encode(b"<script>alert(1)</script>").decode()
        for imagen in (None, "javascript:alert(1)", falso, "data:image/png;base64," + "A" * 200_001):
            calca = {"diseno": "imagen", "zona": "lateral", "color": "#ffffff", "imagen": imagen}
            self.assertEqual(self.enviar({"calcas": [calca]}).status_code, 400)

    def test_guarda_piezas_de_cambio(self):
        r = self.enviar({"estilo": {"espejos": "puntas", "led": "#FF00AA", "accesorios": ["led", "escape", "protector"]}})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.estilo, {"led": "#ff00aa", "espejos": "puntas", "accesorios": ["escape", "led", "protector"]})

    def test_guarda_calcas_de_fabrica_quitadas(self):
        r = self.enviar({"estilo": {"sin_fabrica": ["franja", "nombre", "franja"]}})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.estilo, {"sin_fabrica": ["franja", "nombre"]})
        self.assertEqual(self.enviar({"estilo": {"sin_fabrica": []}}).status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.estilo, {})

    def test_guarda_colores_de_calcas_de_fabrica(self):
        r = self.enviar({"estilo": {"color_fabrica": {"franja": {"p": "#FF0000", "s": "#00ff00"}, "nombre": {}}}})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.estilo, {"color_fabrica": {"franja": {"p": "#ff0000", "s": "#00ff00"}}})

    def test_rechaza_estilo_invalido(self):
        for estilo in ({"acabado": "neon"}, {"rin": "madera"}, {"accesorios": ["cohete"]}, {"chasis": "azul"}, ["mate"],
                       {"espejos": "gigantes"}, {"led": "rosa"}, {"sin_fabrica": "nombre"}, {"sin_fabrica": ["<b>"]},
                       {"sin_fabrica": ["x"] * 9}, {"color_fabrica": {"franja": {"p": "rojo"}}},
                       {"color_fabrica": {"franja": {"q": "#ffffff"}}}, {"color_fabrica": ["#fff"]}):
            self.assertEqual(self.enviar({"estilo": estilo}).status_code, 400, estilo)

    def test_rechaza_datos_invalidos(self):
        self.assertEqual(self.enviar({"color": "rojo"}).status_code, 400)
        self.assertEqual(self.enviar({"calcas": [{"diseno": "virus", "zona": "lateral"}]}).status_code, 400)
        self.assertEqual(self.enviar({"calcas": [{"diseno": "rayo", "zona": "lateral", "color": "#fff"}]}).status_code, 400)
        cinco = [{"diseno": "rayo", "zona": "lateral", "color": "#ffffff"}] * 5
        self.assertEqual(self.enviar({"calcas": cinco}).status_code, 400)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.calcas, [])

    def test_calca_ubicada_con_un_punto_sobre_la_moto(self):
        r = self.enviar({"calcas": [{"diseno": "rayo", "color": "#ffffff", "punto": [0.1234567, 0.6, 0.21],
                                     "normal": [0, 0, 1], "giro": 400, "ambos": 1, "zona": "inventada"}]})
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        c = self.moto.calcas[0]
        self.assertEqual(c["punto"], [0.1235, 0.6, 0.21])
        self.assertEqual((c["giro"], c["ambos"]), (180.0, True))
        self.assertNotIn("zona", c)  # con punto, la zona del formato anterior sobra

    def test_rechaza_puntos_invalidos(self):
        malos = [
            {"punto": [0, 0], "normal": [0, 0, 1]},              # faltan coordenadas
            {"punto": [0, 0, 99], "normal": [0, 0, 1]},          # fuera de la moto
            {"punto": [0, 0, "NaN"], "normal": [0, 0, 1]},       # no es un número
            {"punto": [0, 0.5, 0], "normal": [0, 0, 0]},         # normal sin dirección
            {"punto": [0, 0.5, 0]},                              # sin normal
        ]
        for extra in malos:
            with self.subTest(extra=extra):
                self.assertEqual(self.enviar({"calcas": [{"diseno": "rayo", "color": "#ffffff", **extra}]}).status_code, 400)

    def test_solo_el_dueno_puede_personalizar(self):
        otro = User.objects.create_user("o@x.com", "o@x.com", "x")
        Motociclista.objects.create(nombre="O", celular="573001119998", usuario=otro)
        self.client.force_login(otro)
        self.assertEqual(self.enviar({"color": "#000000"}).status_code, 404)

    def test_la_pagina_lleva_la_personalizacion_al_visor(self):
        self.moto.calcas = [{"diseno": "texto", "zona": "lateral", "color": "#ffffff", "tamano": 1, "posicion": 0, "texto": "SOFI"}]
        self.moto.save()
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, 'id="datos-personalizacion"')
        self.assertContains(r, "SOFI")


class DocumentosTests(TestCase):
    """SOAT y técnico-mecánica: opcionales, privados y servidos solo al dueño."""

    PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64

    def setUp(self):
        import tempfile
        from django.test import override_settings
        self.carpeta = tempfile.mkdtemp()
        self.ajuste = override_settings(PRIVADO_ROOT=self.carpeta)
        self.ajuste.enable()
        self.usuario = User.objects.create_user("d@x.com", "d@x.com", "x")
        perfil = Motociclista.objects.create(nombre="D", celular="573001114455", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                        modelo=2024, km_inicial=0, km_actual=0)
        self.client.force_login(self.usuario)

    def tearDown(self):
        import shutil
        self.ajuste.disable()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def editar(self, **extra):
        from django.core.files.uploadedfile import SimpleUploadedFile
        datos = {"linea_catalogo": str(self.moto.linea_id), "modelo": 2024, "color": "#c62828", "apodo": ""}
        for clave, valor in extra.items():
            datos[clave] = SimpleUploadedFile(*valor) if isinstance(valor, tuple) else valor
        return self.client.post(reverse("garaje:editar", args=[self.moto.pk]), datos)

    def test_crear_moto_no_exige_documentos(self):
        r = self.editar()
        self.assertEqual(r.status_code, 302)
        self.moto.refresh_from_db()
        self.assertIsNone(self.moto.soat_vence)
        self.assertFalse(self.moto.soat_archivo)

    def test_guarda_fecha_y_archivo_en_carpeta_privada(self):
        import os
        r = self.editar(soat_vence="2027-03-12", soat_archivo=("mi soat.png", self.PNG, "image/png"))
        self.assertEqual(r.status_code, 302)
        self.moto.refresh_from_db()
        self.assertEqual(str(self.moto.soat_vence), "2027-03-12")
        ruta = self.moto.soat_archivo.path
        from pathlib import Path
        from django.conf import settings
        self.assertTrue(Path(ruta).resolve().is_relative_to(Path(self.carpeta).resolve()))
        self.assertFalse(Path(ruta).resolve().is_relative_to(Path(settings.MEDIA_ROOT).resolve()))  # fuera de /media/
        self.assertNotIn("mi soat", self.moto.soat_archivo.name)  # nombre aleatorio
        self.assertTrue(os.path.exists(ruta))

    def test_solo_el_dueno_ve_el_documento(self):
        self.editar(soat_archivo=("s.png", self.PNG, "image/png"))
        url = reverse("garaje:documento", args=[self.moto.pk, "soat"])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Control"], "private, no-store")
        self.assertEqual(b"".join(r.streaming_content), self.PNG)
        otro = User.objects.create_user("o2@x.com", "o2@x.com", "x")
        Motociclista.objects.create(nombre="O", celular="573001117777", usuario=otro)
        self.client.force_login(otro)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.assertNotEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("garaje:documento", args=[self.moto.pk, "cedula"])).status_code, 302)

    def test_rechaza_archivos_que_no_son_imagen_ni_pdf(self):
        r = self.editar(soat_archivo=("virus.exe", b"MZ" + b"0" * 20, "application/octet-stream"))
        self.assertEqual(r.status_code, 200)
        r = self.editar(soat_archivo=("falso.png", b"<html>no</html>", "image/png"))
        self.assertEqual(r.status_code, 200)
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.soat_archivo)

    def test_reemplazar_quitar_y_eliminar_borran_del_disco(self):
        import os
        self.editar(tecno_archivo=("a.png", self.PNG, "image/png"))
        self.moto.refresh_from_db()
        primera = self.moto.tecno_archivo.path
        self.editar(tecno_archivo=("b.pdf", b"%PDF-1.4 hola", "application/pdf"))
        self.moto.refresh_from_db()
        segunda = self.moto.tecno_archivo.path
        self.assertFalse(os.path.exists(primera))
        self.editar(quitar_tecno="on")
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.tecno_archivo)
        self.assertFalse(os.path.exists(segunda))
        self.editar(soat_archivo=("c.png", self.PNG, "image/png"))
        self.moto.refresh_from_db()
        tercera = self.moto.soat_archivo.path
        self.client.post(reverse("garaje:eliminar", args=[self.moto.pk]))
        self.assertFalse(os.path.exists(tercera))

    def test_estado_de_vencimiento(self):
        hoy = timezone.localdate()
        self.moto.soat_vence = hoy - timedelta(days=3)
        self.moto.tecno_vence = hoy + timedelta(days=10)
        estados = {d["clave"]: d["estado"] for d in self.moto.documentos(hoy)}
        self.assertEqual(estados, {"soat": "vencido", "tecno": "pronto"})
        self.moto.soat_vence = hoy + timedelta(days=200)
        self.moto.tecno_vence = None
        estados = {d["clave"]: d["estado"] for d in self.moto.documentos(hoy)}
        self.assertEqual(estados, {"soat": "ok", "tecno": "desconocido"})
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, "Documentos")


class KilometrajeSinRecargarTests(TestCase):
    def setUp(self):
        usar_intervalos_generales(self)
        self.usuario = User.objects.create_user("k@x.com", "k@x.com", "x")
        perfil = Motociclista.objects.create(nombre="K", celular="573001118888", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                        modelo=2024, km_inicial=1000, km_actual=1000)
        self.url = reverse("garaje:registrar_km", args=[self.moto.pk])
        self.client.force_login(self.usuario)

    def enviar(self, km):
        return self.client.post(self.url, {"km": km}, HTTP_X_REQUESTED_WITH="fetch")

    def test_responde_json_con_lo_que_cambia_en_el_tablero(self):
        r = self.enviar(2200)
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertEqual(datos["km"], 2200)
        self.assertIn("2.200 km", datos["mensaje"])
        self.assertEqual(set(datos["conteos"]), {"atencion", "proximos", "al_dia", "sin_registro"})  # los grupos de la agenda
        self.assertIn("Cambio de aceite", datos["cambiaron"])  # se cuenta desde 0 km: 2.200 de 2.500 la deja en "pronto"
        self.assertTrue(datos["aceite"]["dato"].startswith("Faltan"))
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 2200)

    def test_un_kilometraje_menor_no_cambia_nada(self):
        r = self.enviar(900)
        self.assertEqual(r.status_code, 400)
        self.assertIn("No puede ser menor", r.json()["error"])
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 1000)
        self.assertEqual(self.moto.lecturas.count(), 0)

    def test_sin_javascript_sigue_redirigiendo(self):
        r = self.client.post(self.url, {"km": 1500})
        self.assertEqual(r.status_code, 302)


class RegistroDesdeDespieceTests(TestCase):
    def setUp(self):
        usar_intervalos_generales(self)
        self.usuario = User.objects.create_user("r@x.com", "r@x.com", "x")
        perfil = Motociclista.objects.create(nombre="R", celular="573001119999", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                        modelo=2024, km_inicial=0, km_actual=2500)
        self.aceite = TareaMantenimiento.objects.get(clave="aceite")
        self.url = reverse("garaje:registrar_mantenimiento", args=[self.moto.pk])
        self.client.force_login(self.usuario)

    def test_justo_en_el_limite_dice_que_toca_ahora(self):
        t = next(t for t in calcular_plan(self.moto).tareas if t.tarea == self.aceite)
        self.assertEqual(t.km_restantes, 0)
        self.assertEqual(t.detalle, "Toca justo ahora.")

    def test_registrar_sin_recargar_devuelve_el_estado_nuevo(self):
        hoy = timezone.localdate().isoformat()
        r = self.client.post(self.url, {"tarea": self.aceite.pk, "km": 2500, "fecha": hoy}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertEqual(datos["tarea"]["id"], self.aceite.pk)
        self.assertEqual(datos["tarea"]["estado"], "ok")
        self.assertIn("2.500 km", datos["mensaje"])
        self.assertEqual(Mantenimiento.objects.filter(moto=self.moto).count(), 1)

    def test_kilometraje_mayor_al_actual_se_rechaza(self):
        hoy = timezone.localdate().isoformat()
        r = self.client.post(self.url, {"tarea": self.aceite.pk, "km": 9000, "fecha": hoy}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 400)
        self.assertIn("No puede ser mayor", r.json()["error"])
        self.assertFalse(Mantenimiento.objects.filter(moto=self.moto).exists())

    def test_otro_taller_fuera_de_tallerya(self):
        hoy = timezone.localdate().isoformat()
        base = {"tarea": self.aceite.pk, "km": 2500, "fecha": hoy}
        self.client.post(self.url, {**base, "taller": "otro", "taller_otro": "  Motos El Paisa "}, HTTP_X_REQUESTED_WITH="fetch")
        m = Mantenimiento.objects.get(moto=self.moto)
        self.assertIsNone(m.taller)
        self.assertEqual(m.donde, "Motos El Paisa")
        m.delete()
        self.client.post(self.url, {**base, "taller": "otro"}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(Mantenimiento.objects.get(moto=self.moto).donde, "Otro taller")  # sin nombre


class PonerAlDiaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("al@x.com", "al@x.com", "x")
        self.perfil = Motociclista.objects.create(nombre="Al", celular="573004440000", usuario=self.usuario)
        self.client.force_login(self.usuario)

    def test_filas_del_paso_2_sin_crear_la_moto(self):
        nkd = LineaMoto.objects.get(nombre="NKD 125")
        r = self.client.get(reverse("garaje:tareas_alta"), {"linea": nkd.pk, "km": "18000"})
        self.assertContains(r, "Cambio de aceite")
        self.assertContains(r, "18.000 km")
        self.assertFalse(Moto.objects.exists())  # solo se crea al guardar

    def test_agregar_crea_moto_y_mantenimientos_juntos(self):
        nkd = LineaMoto.objects.get(nombre="NKD 125")
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        filtro = TareaMantenimiento.objects.filter(pieza="filtro_aire").first()
        datos = {"linea_catalogo": str(nkd.pk), "modelo": 2020, "km_actual": 18000, "color": "#c62828", "apodo": "",
                 f"estado_{aceite.pk}": "poco", f"estado_{filtro.pk}": "km", f"km_{filtro.pk}": "99999"}
        r = self.client.post(reverse("garaje:agregar"), datos)
        self.assertContains(r, "Escribe un kilometraje entre 0 y")  # error en el paso 2: no se crea nada
        self.assertFalse(Moto.objects.exists())
        datos[f"km_{filtro.pk}"] = "15500"
        r = self.client.post(reverse("garaje:agregar"), datos)
        moto = Moto.objects.get(motociclista=self.perfil)
        self.assertRedirects(r, moto.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(moto.mantenimientos.count(), 2)

    def test_guarda_lo_que_se_sabe(self):
        moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                   modelo=2020, km_inicial=18000, km_actual=18000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        filtro = TareaMantenimiento.objects.filter(pieza="filtro_aire").first()
        r = self.client.post(reverse("garaje:poner_al_dia", args=[moto.pk]),
                             {f"estado_{aceite.pk}": "poco", f"estado_{filtro.pk}": "km", f"km_{filtro.pk}": "15500"})
        self.assertRedirects(r, moto.get_absolute_url() + "#plan", fetch_redirect_response=False)
        m_aceite = Mantenimiento.objects.get(moto=moto, tarea=aceite)
        m_filtro = Mantenimiento.objects.get(moto=moto, tarea=filtro)
        self.assertEqual(m_aceite.km, 18000)
        self.assertEqual(m_filtro.km, 15500)
        from .plan import fecha_en_km
        self.assertEqual(m_filtro.fecha, fecha_en_km(moto, 15500))  # 2.500 km al ritmo estimado de la moto
        self.assertEqual(Mantenimiento.objects.filter(moto=moto).count(), 2)  # lo demás quedó en "No sé"

    def test_pendientes_y_actualizar_todo(self):
        moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                   modelo=2020, km_inicial=18000, km_actual=18000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        filtro = TareaMantenimiento.objects.filter(pieza="filtro_aire").first()
        Mantenimiento.objects.create(moto=moto, tarea=aceite, km=16000, fecha=timezone.localdate())
        url = reverse("garaje:poner_al_dia", args=[moto.pk])
        # Desde el aviso: solo los que no tienen registro
        r = self.client.get(url + "?solo=pendientes")
        self.assertNotContains(r, f'name="estado_{aceite.pk}"')
        self.assertContains(r, f'name="estado_{filtro.pk}"')
        # Actualizar todo: viene con el km que ya tenía, y si no se cambia no se duplica
        r = self.client.get(url)
        self.assertContains(r, f'name="km_{aceite.pk}" value="16000"')
        self.client.post(url, {f"estado_{aceite.pk}": "km", f"km_{aceite.pk}": "16000",
                               f"estado_{filtro.pk}": "km", f"km_{filtro.pk}": "17000"})
        self.assertEqual(moto.mantenimientos.filter(tarea=aceite).count(), 1)
        self.assertEqual(moto.mantenimientos.filter(tarea=filtro).count(), 1)

    def test_km_mayor_al_actual_no_guarda_nada(self):
        moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                   modelo=2020, km_inicial=5000, km_actual=5000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        r = self.client.post(reverse("garaje:poner_al_dia", args=[moto.pk]), {f"estado_{aceite.pk}": "km", f"km_{aceite.pk}": "9000"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Escribe un kilometraje entre 0 y 5.000 km.")
        self.assertFalse(Mantenimiento.objects.filter(moto=moto).exists())

    def test_fecha_tentativa_estima_fecha_y_km(self):
        moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                   modelo=2020, km_inicial=18000, km_actual=18000)
        aceite = TareaMantenimiento.objects.get(clave="aceite")
        bujia = TareaMantenimiento.objects.get(pieza="bujia")
        self.client.post(reverse("garaje:poner_al_dia", args=[moto.pk]),
                         {f"estado_{aceite.pk}": "nose", f"hace_{aceite.pk}": "3", f"estado_{bujia.pk}": "nose", f"hace_{bujia.pk}": ""})
        m = Mantenimiento.objects.get(moto=moto, tarea=aceite)
        self.assertEqual((timezone.localdate() - m.fecha).days, 90)
        from .plan import km_en_fecha
        self.assertEqual(m.km, km_en_fecha(moto, m.fecha))  # al ritmo de la moto (aquí, estimado por su modelo)
        self.assertFalse(Mantenimiento.objects.filter(moto=moto, tarea=bujia).exists())  # "Ni idea": sin registro


class PlacaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("placa@x.com", "placa@x.com", "x")
        self.perfil = Motociclista.objects.create(nombre="Pla", celular="573008889999", usuario=self.usuario)
        self.client.force_login(self.usuario)

    def test_placa_opcional_se_normaliza(self):
        nkd = LineaMoto.objects.get(nombre="NKD 125")
        datos = {"linea_catalogo": str(nkd.pk), "modelo": 2021, "km_actual": 100, "color": "#1f4fa8"}
        self.client.post(reverse("garaje:agregar"), {**datos, "placa": " abc-12d "})
        self.assertEqual(Moto.objects.get().placa, "ABC12D")
        Moto.objects.all().delete()
        self.client.post(reverse("garaje:agregar"), datos)  # sin placa también se puede
        self.assertEqual(Moto.objects.get().placa, "")

    def test_placa_muy_corta_no_se_guarda(self):
        nkd = LineaMoto.objects.get(nombre="NKD 125")
        r = self.client.post(reverse("garaje:agregar"), {"linea_catalogo": str(nkd.pk), "modelo": 2021, "km_actual": 100,
                                                         "color": "#1f4fa8", "placa": "AB1"})
        self.assertContains(r, "Revisa la placa")
        self.assertFalse(Moto.objects.exists())


class LectoresDespieceTests(TestCase):
    """Tablas de partes de los formatos de garaje/despiece_lectores.py."""

    def test_suzuki_referencia_con_sufijo_descripcion_partida_y_palabras_cortas(self):
        from garaje.despiece_lectores import _filas
        filas = _filas([" 1-1 ", "12200-34J02-0A0", "CRANKSHAFT ASSY", "  1",
                        " 2-1 ", "12661-34J00-0A0", "GEAR,CRANK BALANCER DRIVE (NT:", "  1", "44)",
                        "31   ", "01500-0610A-000", "BOLT", "  2",
                        "5   ", "12345-AB1-000", ".PAD SET", "  1"])
        self.assertEqual([(f["ref"], f["descripcion"], f["cantidad"], f["nivel"]) for f in filas], [
            (1, "CRANKSHAFT ASSY", 1, 0),
            (2, "GEAR,CRANK BALANCER DRIVE (NT:44)", 1, 0),
            (31, "BOLT", 2, 0),          # "BOLT" es una descripción, no un código de modelo
            (5, "PAD SET", 1, 1),        # el punto inicial es el nivel dentro del conjunto
        ])

    def test_honda_referencia_pegada_y_variantes(self):
        from garaje.despiece_lectores import _decodificar, _filas
        self.assertEqual(_decodificar("\uf041\uf042"), "AB")
        filas = _filas(["1 11100-KWP-900", "CRANKCASE COMP., R. •••••••••  1   -   1",
                        "11100-KWP-D01", " ••••••••••••••••  -   1   -",
                        "20 16163-KCS-920", "GASKET, FLOAT CHAMBER ······· 2 2 2"])
        self.assertEqual([(f["ref"], f["codigo"], f["descripcion"], f["cantidad"]) for f in filas], [
            (1, "11100-KWP-900", "CRANKCASE COMP., R.", 1),
            (1, "11100-KWP-D01", "CRANKCASE COMP., R.", 1),
            (20, "16163-KCS-920", "GASKET, FLOAT CHAMBER", 2),
        ])

    def test_suzuki_y_hero_referencia_en_linea_aparte(self):
        from garaje.despiece_lectores import _filas
        filas = _filas(["1", "11171-34J00-000", "COVER, CYLINDER HEAD", "  1",
                        "2", "09106-07011-000", "BOLT (7X37)", "  2"])
        self.assertEqual([(f["ref"], f["descripcion"], f["cantidad"]) for f in filas],
                         [(1, "COVER, CYLINDER HEAD", 1), (2, "BOLT (7X37)", 2)])


class PicoPlacaTests(TestCase):
    def setUp(self):
        from .models import ReglaPicoPlaca
        ReglaPicoPlaca.objects.all().delete()
        ReglaPicoPlaca.objects.create(vigente_desde=date(2026, 8, 3), lunes="5,8", martes="1,4", miercoles="0,2",
                                      jueves="3,6", viernes="7,9")

    def test_festivos_y_restriccion(self):
        from .pico_placa import es_festivo, tiene_pico_placa
        self.assertTrue(es_festivo(date(2026, 4, 3)))    # viernes santo
        self.assertTrue(es_festivo(date(2026, 11, 16)))  # 11 de noviembre corrido al lunes
        moto = Moto(placa="ABC51D")
        self.assertFalse(tiene_pico_placa(moto, date(2026, 11, 16))[0])  # lunes festivo
        self.assertTrue(tiene_pico_placa(moto, date(2026, 11, 23))[0])   # lunes, primer dígito 5
        self.assertFalse(tiene_pico_placa(moto, date(2026, 11, 24))[0])  # martes
        self.assertFalse(tiene_pico_placa(Moto(placa=""), date(2026, 11, 23))[0])



class RitmoKmTests(TestCase):
    def setUp(self):
        from cupones.models import Motociclista
        self.dueno = Motociclista.objects.create(nombre="R", celular="573009998877")

    def _moto(self, **kw):
        datos = dict(motociclista=self.dueno, modelo=2022, km_inicial=10000, km_actual=10000)
        datos.update(kw)
        return Moto.objects.create(**datos)

    def test_un_salto_el_mismo_dia_no_lo_descuadra(self):
        from .plan import ritmo_km
        moto = self._moto()
        hoy = timezone.localdate()
        for dias, km in ((60, 10000), (40, 10600), (20, 11200), (0, 11800)):
            LecturaKm.objects.create(moto=moto, km=km, fecha=hoy - timedelta(days=dias))
        LecturaKm.objects.create(moto=moto, km=11500, fecha=hoy)  # lectura más baja el mismo día: no resta
        LecturaKm.objects.create(moto=moto, km=17800, fecha=hoy + timedelta(days=1))  # corrección del odómetro: no cuenta
        ritmo, estimado = ritmo_km(moto)
        self.assertFalse(estimado)
        self.assertAlmostEqual(ritmo, 30, delta=1.5)

    def test_sin_historial_se_estima_por_el_modelo(self):
        from .plan import ritmo_km
        moto = self._moto(km_actual=20000)
        LecturaKm.objects.create(moto=moto, km=20000, fecha=timezone.localdate())
        ritmo, estimado = ritmo_km(moto, hoy=date(2026, 7, 1))
        self.assertTrue(estimado)
        self.assertAlmostEqual(ritmo, 20000 / (date(2026, 7, 1) - date(2021, 7, 1)).days)


class SistemasDespieceTests(TestCase):
    """Una sola lista de sistemas por tipo de transmisión; la clasificación vive en el servidor."""

    def test_listas_por_transmision(self):
        from types import SimpleNamespace
        from .despiece_sistemas import sistemas_de
        cadena = sistemas_de(SimpleNamespace(transmision="cadena", refrigeracion="aire"))
        cvt = sistemas_de(SimpleNamespace(transmision="cvt", refrigeracion="liquido"))
        self.assertIn("Caja de cambios y clutch", cadena)
        self.assertIn("Kit de arrastre", cadena)
        self.assertNotIn("Refrigeración", cadena)
        self.assertNotIn("Kit de arrastre", cvt)
        self.assertEqual(cvt[4:6], ["Transmisión CVT", "Transmisión final"])
        self.assertIn("Refrigeración", cvt)

    def test_clasificacion(self):
        from .despiece_sistemas import sistema_de
        self.assertEqual(sistema_de("carcasa", "aceite", "Cubierta del clutch"), ("Lubricación", ""))
        self.assertEqual(sistema_de("transmision", "motor", "Caja de cambios"), ("Caja de cambios y clutch", "Caja de cambios"))
        self.assertEqual(sistema_de("clutch", "motor", "Clutch"), ("Caja de cambios y clutch", "Clutch"))
        self.assertEqual(sistema_de("cvt", "correa", "Variador"), ("Transmisión CVT", ""))
        self.assertEqual(sistema_de("caja_secundaria", "aceite_caja", "Caja"), ("Transmisión final", ""))
        self.assertEqual(sistema_de("carcasa", "motor", "Embrague del arranque"), ("Eléctrico", "Arranque"))
        self.assertEqual(sistema_de("rueda_trasera", "cadena", "Kit de arrastre", "5-arrastre"), ("Kit de arrastre", ""))

    def test_clutch_dibujo_y_reglas(self):
        from .diagramas import DIAGRAMAS, puesto_para
        piezas, _ = DIAGRAMAS["clutch"][1]()
        puestos = [p.puesto for p in piezas]
        self.assertLess(puestos.index("canasta"), puestos.index("centro"))
        self.assertLess(puestos.index("centro"), puestos.index("discos_friccion"))
        self.assertLess(puestos.index("separadores"), puestos.index("plato_presion"))
        self.assertLess(puestos.index("plato_presion"), puestos.index("resortes"))
        for texto, puesto in [("PLATE, FRICTION", "discos_friccion"), ("PLATE, CLUTCH", "separadores"), ("GEAR ASSY, PRIMARY DRIVEN", "canasta"),
                              ("DISCO FRICCION", "discos_friccion"), ("PLATO PRESION", "plato_presion"), ("CAMPANA CLUTCH", "canasta")]:
            self.assertEqual(puesto_para("clutch", texto), puesto, texto)


class PuestosFijosTests(TestCase):
    def test_puestos_escritos_a_mano_coinciden_con_el_dibujo(self):
        from . import diagramas
        for clave, fijos in diagramas.PUESTOS_FIJOS.items():
            dibujados = {q.puesto for q in diagramas.DIAGRAMAS[clave][1]()[0] if q.puesto}
            self.assertEqual(fijos, dibujados, clave)


class PiezaPorPrimeraPalabraTests(TestCase):
    def test_primera_palabra_y_tapon_con_varilla(self):
        from . import diagramas as d
        self.assertEqual(d.puesto_para("carcasa", "PLUG, OIL LEVEL"), "tapon_llenado")   # NMAX: tapón con varilla, no visor
        self.assertEqual(d.puesto_para("carcasa", "LENS,OIL LEVEL CHECK"), "visor")
        self.assertEqual(d.puesto_para("aceite", "O-RING, OIL PUMP"), "oring")           # el o-ring de la bomba, no la bomba
        self.assertEqual(d.puesto_para("culata", "GASKET, CYLINDER HEAD"), "empaque_culata")
        self.assertEqual(d.puesto_para("freno_trasero", "Resorte Pedal Freno"), "h_resorte")

    def test_la_tarea_pasa_al_empaque_del_tapon(self):
        from types import SimpleNamespace as N
        from .management.commands.importar_despiece import tarea_al_sello
        tapon, oring = N(ref=14, descripcion="PLUG, OIL LEVEL", tarea_id=7), N(ref=15, descripcion="O-RING", tarea_id=None)
        filtro, sello = N(ref=3, descripcion="FILTER, OIL", tarea_id=7), N(ref=4, descripcion="O-RING", tarea_id=None)
        tarea_al_sello([tapon, oring, filtro, sello])
        self.assertEqual((tapon.tarea_id, oring.tarea_id), (None, 7))
        self.assertEqual((filtro.tarea_id, sello.tarea_id), (7, 7))

    def test_nombre_del_empaque_por_su_tapon(self):
        from .despiece_variantes import nombres_de_sellos
        partes = [{"ref": 14, "nombre": "Tapón con varilla del aceite"}, {"ref": 15, "nombre": "O ring"}]
        self.assertEqual(nombres_de_sellos(partes), {1: "Empaque del tapón con varilla del aceite"})


class LoteCriteriosTests(TestCase):
    def test_tapones_bujias_y_franja_por_primera_palabra(self):
        from . import diagramas as d
        self.assertEqual(d.puesto_para("culata", "PLUG,SPARK (CPR7EA-9)"), "bujia")
        self.assertEqual(d.puesto_para("electrico", "PLUG CAP ASSY"), "capuchon")
        self.assertEqual(d.puesto_para("carcasa", "CAP, OIL FILTER"), "tapa_filtro")
        self.assertEqual(d.puesto_para("freno_disco", "PLUG, PIN"), "h_tapa")
        self.assertEqual(d.puesto_para("freno_disco", "CAP, BLEEDER"), "purgador")
        self.assertEqual(d.puesto_para("distribucion", "O-RING TORNILLO TENSOR"), "h_empaque")

    def test_tarea_al_sello_anterior_y_tapa_del_filtro(self):
        from types import SimpleNamespace as N
        from .management.commands.importar_despiece import tarea_al_sello
        arandela, tornillo = N(ref=9, descripcion="Arandela Tapón Drenaje", tarea_id=None), N(ref=10, descripcion="Tornillo Drenaje", tarea_id=5)
        tapa, oring = N(ref=3, descripcion="TAPA FILTRO ACEITE", tarea_id=5), N(ref=4, descripcion="O-RING TAPA 52X2.4", tarea_id=None)
        sola = N(ref=17, descripcion="Cubierta Filtro Aceite", tarea_id=5)
        tarea_al_sello([arandela, tornillo, tapa, oring])
        tarea_al_sello([sola])
        self.assertEqual((arandela.tarea_id, tornillo.tarea_id), (5, None))
        self.assertEqual((tapa.tarea_id, oring.tarea_id), (None, 5))
        self.assertIsNone(sola.tarea_id)

    def test_empaques_con_dueno(self):
        from .despiece_variantes import nombres_de_empaques
        partes = [{"ref": 1, "nombre": "Culata", "descripcion": "CYLINDER HEAD", "_puesto": "culata"},
                  {"ref": 2, "nombre": "O ring", "descripcion": "O-RING", "_puesto": "h_empaque"},
                  {"ref": 3, "nombre": "Empaque culata", "descripcion": "Empaque Culata", "_puesto": "empaque_culata"}]
        self.assertEqual(nombres_de_empaques(partes, "Culata"), {1: "Empaque de la culata", 2: "Empaque de la culata"})


class PiezaInicialTests(TestCase):
    """El visor abre cada sistema en la pieza que explica su estado (vencida > pronto > más avanzada > menor número)."""

    def test_estado_del_sistema_sale_de_sus_piezas_y_abre_en_la_que_lo_explica(self):
        from types import SimpleNamespace as N
        from unittest import mock
        from . import views
        t1, t2 = N(pk=1, nombre="A", clave="a", servicio_id=None, hazlo_tu=False), N(pk=2, nombre="B", clave="b", servicio_id=None, hazlo_tu=False)
        base = {"laminas": [
            {"id": 1, "pieza": "motor", "partes": [{"id": 10, "ref": 1, "_tarea": None}, {"id": 11, "ref": 4, "_tarea": 2},
                                                   {"id": 12, "ref": 7, "_tarea": 1}]},
            {"id": 2, "pieza": "motor", "partes": [{"id": 20, "ref": 1, "_tarea": None}]},   # sin piezas con tarea
        ], "sistemas": []}
        plan = N(moto=N(pk=1, km_actual=0, nombre_completo="x"), piezas=lambda: {"motor": {"estado": "vencido"}}, tareas=[
            N(tarea=t1, estado="vencido", color="vencido", etiqueta="", detalle="", progreso=120, porcentaje=100),
            N(tarea=t2, estado="pronto", color="pronto", etiqueta="", detalle="", progreso=80, porcentaje=80)])
        with mock.patch.object(views, "_laminas_base", return_value=base), mock.patch.object(views.caches["despiece"], "get", return_value=None), \
                mock.patch.object(views.caches["despiece"], "set"), mock.patch.object(views, "intervalo_texto", return_value=""):
            datos = views.datos_despiece(views.Despiece(pk=1, version="", anio=0), plan)
        motor, sin_tareas = sorted(datos["laminas"], key=lambda l: l["id"])
        self.assertEqual((motor["estado"], motor["inicial"]), ("vencido", 12))
        self.assertEqual((sin_tareas["estado"], sin_tareas["inicial"]), (None, None))  # no hereda el estado de la zona


class DespiecePorAnioTests(TestCase):
    """Una línea con despieces de varios años: cada moto usa el de su año (o el anterior más cercano)."""

    def test_elige_el_catalogo_del_anio_de_la_moto(self):
        from talleres.models import Marca
        from .models import Despiece
        marca = Marca.objects.get_or_create(nombre="Suzuki")[0]
        linea = LineaMoto.objects.create(marca=marca, nombre="Prueba 150", cilindraje=150)
        d2015 = Despiece.objects.create(linea=linea, version="CARB", anio=2015, variante="Carburador")
        d2020 = Despiece.objects.create(linea=linea, version="FI", anio=2020, variante="FI ABS")
        Despiece.objects.create(linea=linea, version="VIEJO-INACTIVO", anio=2010, activo=False)
        moto = lambda anio: Moto(linea=linea, modelo=anio)
        self.assertEqual(Despiece.para(moto(2017)), d2015)
        self.assertEqual(Despiece.para(moto(2021)), d2020)
        self.assertEqual(Despiece.para(moto(2020)), d2020)
        self.assertEqual(Despiece.para(moto(2012)), d2015)   # más vieja que todos los activos: el más antiguo


class EstimacionKmTests(TestCase):
    """Registros sin kilometraje exacto: fecha sin km, "hace unos meses" y "no sé" (criterio en garaje/plan.py)."""

    def setUp(self):
        usar_intervalos_generales(self)  # aceite: 2.500 km o 120 días
        self.usuario = User.objects.create_user("e@x.com", "e@x.com", "x")
        self.perfil = Motociclista.objects.create(nombre="E", celular="573001117777", usuario=self.usuario)
        self.client.force_login(self.usuario)
        self.aceite = TareaMantenimiento.objects.get(clave="aceite")
        self.hoy = timezone.localdate()

    def _moto(self, km_inicial=10000, km_actual=10000, lecturas=(), **extra):
        moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"), modelo=2022,
                                   km_inicial=km_inicial, km_actual=km_actual, **extra)
        for dias, km in lecturas:
            LecturaKm.objects.create(moto=moto, km=km, fecha=self.hoy - timedelta(days=dias))
        return moto

    def _aceite(self, moto):
        return next(t for t in calcular_plan(moto).tareas if t.tarea == self.aceite)

    def test_fecha_entre_lecturas_se_interpola(self):
        from .plan import km_en_fecha
        moto = self._moto(km_actual=12000, lecturas=((60, 10000), (20, 11000), (0, 12000)))
        self.assertEqual(km_en_fecha(moto, self.hoy - timedelta(days=40)), 10500)
        self.assertEqual(km_en_fecha(moto, self.hoy - timedelta(days=10)), 11500)

    def test_fecha_antes_de_las_lecturas_sigue_el_ritmo_y_no_baja_de_cero(self):
        from .plan import km_en_fecha
        moto = self._moto(km_actual=12000, lecturas=((60, 10000), (20, 11000), (0, 12000)))  # ≈ 33 km/día
        km = km_en_fecha(moto, self.hoy - timedelta(days=90))
        self.assertAlmostEqual(km, 10000 - 30 * 33.3, delta=60)
        self.assertEqual(km_en_fecha(moto, self.hoy - timedelta(days=5000)), 0)

    def test_registrar_con_fecha_y_sin_km_lo_estima(self):
        moto = self._moto(km_actual=12000, lecturas=((60, 10000), (20, 11000), (0, 12000)))
        fecha = (self.hoy - timedelta(days=40)).isoformat()
        r = self.client.post(reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
                             {"tarea": self.aceite.pk, "km": "", "fecha": fecha}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 200, r.content)
        m = Mantenimiento.objects.get(moto=moto)
        self.assertEqual(m.km, 10500)
        self.assertIn("km estimado", m.notas)
        datos = r.json()
        self.assertIn("estimados por la fecha", datos["mensaje"])
        self.assertEqual(datos["tarea"]["km"]["origen"], "aproximado")
        self.assertEqual(datos["tarea"]["km"]["desde"], 1500)
        self.assertIn("Estimado", datos["tarea"]["km"]["texto_origen"])

    def test_sin_km_ni_fecha_pide_uno_de_los_dos(self):
        moto = self._moto()
        r = self.client.post(reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
                             {"tarea": self.aceite.pk, "km": "", "fecha": ""}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Mantenimiento.objects.exists())

    def test_hace_unos_meses_usa_las_lecturas_y_no_25_km_por_dia(self):
        moto = self._moto(km_inicial=8000, km_actual=11000, lecturas=((100, 8000), (0, 11000)))  # 30 km/día
        r = self.client.post(reverse("garaje:poner_al_dia", args=[moto.pk]),
                             {f"estado_{self.aceite.pk}": "nose", f"hace_{self.aceite.pk}": "3"})
        self.assertEqual(r.status_code, 302)
        m = Mantenimiento.objects.get(moto=moto, tarea=self.aceite)
        self.assertEqual(m.fecha, self.hoy - timedelta(days=90))
        self.assertEqual(m.km, 8300)                       # 25 km/día habría dado 8.750
        self.assertEqual(self._aceite(moto).origen, "aproximado")

    def test_no_se_cuenta_desde_nueva_pero_solo_marca_pronto(self):
        moto = self._moto(km_inicial=300, km_actual=5000)  # el doble del intervalo (2.500), sin ningún registro
        t = self._aceite(moto)
        self.assertTrue(t.supuesto)
        self.assertEqual(t.origen, "supuesto")
        self.assertEqual(t.km_desde, 5000)
        self.assertEqual((t.estado, t.nivel), ("pronto", "pronto"))  # no "Toca ya": la única evidencia es la edad
        self.assertIn("revísalo pronto", t.detalle)
        self.assertIn("era nueva", t.texto_origen)

    def test_interpolacion_sin_las_correcciones_del_odometro(self):
        from .plan import km_en_fecha
        # 900 km por tramo y, el último día, una corrección del odómetro de 4.000 km (no son km rodados)
        moto = self._moto(km_actual=15800, lecturas=((60, 10000), (30, 10900), (1, 11800), (1, 15800)))
        km = km_en_fecha(moto, self.hoy - timedelta(days=15))
        self.assertEqual(km, 15366)                        # hoy menos lo rodado desde entonces (≈ 434 km)
        self.assertEqual(km_en_fecha(moto, self.hoy - timedelta(days=60)), 15800 - 1800)


class RegistrarCuandoTests(TestCase):
    """Diálogo "Registrar mantenimiento": Hace poco · A los … km · No sé, guardado igual que "Poner al día"."""

    def setUp(self):
        usar_intervalos_generales(self)
        self.usuario = User.objects.create_user("c@x.com", "c@x.com", "x")
        perfil = Motociclista.objects.create(nombre="C", celular="573001116666", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NKD 125"), modelo=2022,
                                        km_inicial=11000, km_actual=11000)
        self.hoy = timezone.localdate()
        for dias, km in ((100, 8000), (0, 11000)):  # 30 km/día
            LecturaKm.objects.create(moto=self.moto, km=km, fecha=self.hoy - timedelta(days=dias))
        self.aceite = TareaMantenimiento.objects.get(clave="aceite")
        self.url = reverse("garaje:registrar_mantenimiento", args=[self.moto.pk])
        self.client.force_login(self.usuario)

    def enviar(self, **datos):
        return self.client.post(self.url, {"tarea": self.aceite.pk, **datos}, HTTP_X_REQUESTED_WITH="fetch")

    def registro(self):
        return Mantenimiento.objects.get(moto=self.moto, tarea=self.aceite)

    def test_el_dialogo_trae_las_opciones_y_el_km_vacio(self):
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, 'name="cuando" value="nose"')
        self.assertContains(r, 'name="km" min="0"')       # sin value: sale vacío, con placeholder
        self.assertContains(r, 'value="sin_idea"')
        html = r.content.decode()
        # Un solo campo por dato: el km solo en "A los … km"; en "No sé", una sola fecha (desplegable) y ningún km
        nose = html[html.index('data-panel-cuando="nose"'):html.index('registrar-taller')]
        km = html[html.index('data-panel-cuando="km"'):html.index('data-panel-cuando="nose"')]
        self.assertNotIn('name="km"', nose)
        self.assertEqual((nose.count('name="fecha"'), km.count('name="fecha"'), km.count('name="km"')), (1, 1, 1))
        dialogo = html[html.index('id="dialogo-registrar"'):]
        self.assertEqual(dialogo[:dialogo.index("</dialog>")].count('name="km" '), 1)

    def test_hace_poco(self):
        self.assertEqual(self.enviar(cuando="poco").status_code, 200)
        self.assertEqual((self.registro().km, self.registro().fecha), (11000, self.hoy))

    def test_a_los_km_sin_fecha_la_estima(self):
        from .plan import fecha_en_km
        self.enviar(cuando="km", km="10100")
        self.assertEqual(self.registro().fecha, fecha_en_km(self.moto, 10100))
        self.assertIn("fecha estimada", self.registro().notas)

    def test_no_se_hace_unos_meses_igual_que_poner_al_dia(self):
        self.enviar(cuando="nose", hace="3", notas="Aceite 20W-50")
        m = self.registro()
        self.assertEqual((m.fecha, m.km), (self.hoy - timedelta(days=90), 8300))
        self.assertEqual(m.notas, "Aceite 20W-50 (fecha y km estimados)")

    def test_no_se_con_fecha_estima_el_km(self):
        self.enviar(cuando="nose", fecha=(self.hoy - timedelta(days=50)).isoformat())
        self.assertEqual(self.registro().km, 9500)

    def test_no_se_sin_nada_pide_cuando(self):
        r = self.enviar(cuando="nose")
        self.assertEqual(r.status_code, 400)
        self.assertIn("hace cuánto", r.json()["error"])
        self.assertFalse(Mantenimiento.objects.exists())

    def test_sin_idea_cuenta_desde_la_matricula_como_supuesto(self):
        from .models import RegistroServicio
        self.moto.matricula = self.hoy - timedelta(days=400)
        self.moto.save(update_fields=["matricula"])
        r = self.enviar(cuando="nose", hace="sin_idea")
        self.assertEqual(r.status_code, 200)
        self.assertIn("desde que la moto era nueva", r.json()["mensaje"])
        m = self.registro()
        self.assertEqual((m.km, m.fecha), (0, self.moto.matricula))
        self.assertFalse(RegistroServicio.objects.filter(moto=self.moto).exists())  # no es un servicio hecho
        t = next(t for t in calcular_plan(self.moto).tareas if t.tarea == self.aceite)
        self.assertEqual((t.supuesto, t.origen, t.km_desde), (True, "supuesto", 11000))
        self.assertEqual((t.estado, t.nivel, t.etiqueta), ("pronto", "pronto", "Pronto (estimado)"))  # nunca "Toca ya"

    def test_sin_idea_sin_matricula_usa_el_anio_del_modelo(self):
        self.enviar(cuando="nose", hace="sin_idea")
        self.assertEqual(self.registro().fecha, date(2021, 7, 1))


class RitmoMatriculaTests(TestCase):
    def test_sin_lecturas_ni_registro_usa_la_matricula_antes_que_el_modelo(self):
        from .plan import ritmo_km
        dueno = Motociclista.objects.create(nombre="M", celular="573009991111")
        hoy = timezone.localdate()
        moto = Moto.objects.create(motociclista=dueno, modelo=2015, km_inicial=20000, km_actual=20000,
                                   matricula=hoy - timedelta(days=1000))
        ritmo, estimado = ritmo_km(moto, hoy)
        self.assertTrue(estimado)
        self.assertAlmostEqual(ritmo, 20)
        moto.matricula = None
        self.assertLess(ritmo_km(moto, hoy)[0], 20)          # por el año del modelo (2015): más días, menos km/día
