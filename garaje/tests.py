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
