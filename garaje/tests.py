from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from talleres.models import Barrio, Servicio, Taller

from .models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from .plan import calcular_plan

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
        self.assertContains(self.client.get(moto.get_absolute_url()), f'data-eliminar="{url}"')
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
        barrio = Barrio.objects.create(nombre="Belén")
        taller = Taller.objects.create(nombre="Llantas Ya", responsable="X", whatsapp="573001234567",
                                       direccion="X", barrio=barrio, activo=True)
        taller.servicios.add(Servicio.objects.get(nombre="Llantas"))
        moto = self.crear_moto(km=14000)
        moto.km_actual = 16000  # llantas (asumidas de fábrica) pasan su intervalo
        moto.save()
        r = self.client.get(moto.get_absolute_url())
        self.assertContains(r, 'id="datos-moto"')
        self.assertContains(r, '"rin_delantero": 17')
        self.assertContains(r, "Llantas Ya")


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

    def test_pagina_de_la_moto_muestra_el_despiece(self):
        self.client.force_login(self.usuario)
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, 'id="datos-despiece"')
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
        self.assertEqual((timezone.localdate() - m_filtro.fecha).days, 100)  # 2.500 km a 25 km/día
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
        self.assertEqual(m.km, 18000 - 90 * 25)
        self.assertFalse(Mantenimiento.objects.filter(moto=moto, tarea=bujia).exists())  # "Ni idea": sin registro


class CotizarSoatTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("soat@x.com", "soat@x.com", "x")
        self.perfil = Motociclista.objects.create(nombre="Sol", celular="573006667777", usuario=self.usuario)
        self.moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NKD 125"),
                                        modelo=2020, km_inicial=0, km_actual=0)
        self.client.force_login(self.usuario)
        User.objects.create_user("admin@x.com", "admin@x.com", "x", is_staff=True)

    def test_pide_cotizacion_una_sola_vez_y_avisa_al_equipo(self):
        from garaje.models import SolicitudSoat
        from notificaciones.models import Notificacion
        url = reverse("garaje:cotizar_soat", args=[self.moto.pk])
        self.client.post(url, {"placa": "abc-12d", "celular": "573006667777"})
        self.client.post(url, {"placa": "XYZ99Z", "celular": "573006667777"})  # ya hay una en curso
        s = SolicitudSoat.objects.get()
        self.assertEqual(s.placa, "ABC12D")
        self.assertTrue(Notificacion.objects.filter(usuario__is_staff=True, titulo="Nueva cotización de SOAT").exists())
        self.assertContains(self.client.get(self.moto.get_absolute_url()), "Cotización solicitada")

    def test_exige_celular(self):
        from garaje.models import SolicitudSoat
        self.client.post(reverse("garaje:cotizar_soat", args=[self.moto.pk]), {"placa": "ABC12D", "celular": "12"})
        self.assertFalse(SolicitudSoat.objects.exists())


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
