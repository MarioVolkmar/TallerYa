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
        self.assertRedirects(r, moto.get_absolute_url())
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
        self.assertEqual(self.client.get(ajena.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(reverse("garaje:registrar_km", args=[ajena.pk]), {"km": 10}).status_code, 404)

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
        self.assertEqual([p["ref"] for p in partes], [2, 9])
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
        self.assertEqual(fila, {"ref": 9, "codigo": "2DP-F5805-00", "descripcion": "BRAKE PAD KIT", "nivel": 1, "cantidad": 1})

    def test_glosario(self):
        from .despiece_glosario import traducir
        self.assertEqual(traducir("BRAKE PAD KIT"), "Kit de pastillas de freno")
        self.assertEqual(traducir("TIRE (110/70-13M/C 48P)"), "Llanta")
        self.assertEqual(traducir("BOLT, FLANGE"), "Tornillo")
        self.assertEqual(traducir("SOMETHING RARE"), "")
