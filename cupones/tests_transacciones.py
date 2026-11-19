"""Transacciones donde un tercero confirma algo sobre la cuenta de otro: canje de cupones (PIN por taller) y servicios
que el taller anota en la hoja de vida con el código del dueño. Una prueba por criterio de la revisión del 17-nov-2026."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, tag
from django.utils import timezone

from cupones.models import CodigoCupon, Cupon
from cupones.servicios import ErrorCanje, PIN_FALLOS_MAX, canjear
from garaje import hoja_vida
from garaje.models import Moto, Motociclista, ServicioTaller
from notificaciones.models import Notificacion
from talleres.models import Barrio, Taller

User = get_user_model()


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.u_a = User.objects.create_user("ta@x.co", "ta@x.co", "x")
        cls.u_b = User.objects.create_user("tb@x.co", "tb@x.co", "x")
        cls.ta = Taller.objects.create(nombre="Taller A", responsable="A", whatsapp="573001112233", direccion="X",
                                        barrio=barrio, activo=True, usuario=cls.u_a)
        cls.tb = Taller.objects.create(nombre="Taller B", responsable="B", whatsapp="573001112244", direccion="Y",
                                        barrio=barrio, activo=True, usuario=cls.u_b)
        cls.pin_a, cls.pin_b = cls.ta.nuevo_pin(), cls.tb.nuevo_pin()
        cls.ta.refresh_from_db()
        cls.tb.refresh_from_db()
        cls.u_m = User.objects.create_user("m@x.co", "m@x.co", "x")
        cls.motero = Motociclista.objects.create(usuario=cls.u_m, nombre="Ana", celular="573001110001")
        cls.general = Cupon.objects.create(titulo="Lavado gratis")
        cls.codigo = CodigoCupon.objects.create(cupon=cls.general, motociclista=cls.motero)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def post_canje(self, codigo, taller, pin):
        return self.client.post("/canjear/", {"codigo": codigo, "taller": taller.slug, "pin": pin})


class PinPorTallerTests(Base):
    def test_el_pin_de_otro_taller_no_sirve(self):
        if self.pin_a == self.pin_b:
            self.pin_b = self.tb.nuevo_pin()
        r = self.post_canje(self.codigo.codigo, self.ta, self.pin_b)
        self.assertContains(r, "El código o el PIN no son correctos")
        self.codigo.refresh_from_db()
        self.assertFalse(self.codigo.canjeado)

    def test_pin_en_la_base_solo_como_hash(self):
        self.assertTrue(self.ta.pin_hash.startswith(("pbkdf2", "md5", "argon2", "bcrypt", "scrypt")))
        self.assertNotIn(self.pin_a, self.ta.pin_hash)
        self.assertFalse(Taller._meta.get_field("pin_hash").editable)

    def test_sin_taller_elegido_no_valida(self):
        r = self.client.post("/canjear/", {"codigo": self.codigo.codigo, "pin": self.pin_a})
        self.assertContains(r, "Elige tu taller")

    def test_taller_sin_pin_no_valida_con_pin(self):
        Taller.objects.filter(pk=self.ta.pk).update(pin_hash="")
        self.assertContains(self.post_canje(self.codigo.codigo, self.ta, self.pin_a), "El código o el PIN no son correctos")

    def test_bloqueo_del_pin_del_taller_tras_fallos(self):
        malo = "000000" if self.pin_a != "000000" else "111111"
        self.ta.refresh_from_db()
        for i in range(PIN_FALLOS_MAX):
            with self.assertRaises(ErrorCanje):
                canjear(self.codigo.codigo, malo, taller_elegido=self.ta)
        with self.assertRaisesMessage(ErrorCanje, "Demasiados PIN errados"):  # ni con el PIN bueno
            canjear(self.codigo.codigo, self.pin_a, taller_elegido=self.ta)
        # el otro taller no queda bloqueado, y con la sesión del taller A sí se puede
        canjear(CodigoCupon.objects.create(cupon=self.general, motociclista=Motociclista.objects.create(
            nombre="Otro", celular="573001110009")).codigo, self.pin_b, taller_elegido=self.tb)
        canjear(self.codigo.codigo, taller=self.ta)

    def test_regenerar_pin_desde_mi_taller(self):
        self.client.force_login(self.u_a)
        self.assertContains(self.client.get("/mi-taller/pin/"), "ya tiene PIN")
        r = self.client.post("/mi-taller/pin/")
        self.assertEqual(r["Cache-Control"], "no-store")
        nuevo = r.context["pin"]
        self.ta.refresh_from_db()
        self.assertTrue(self.ta.pin_correcto(nuevo))
        if nuevo != self.pin_a:
            self.assertFalse(self.ta.pin_correcto(self.pin_a))
        self.client.force_login(self.u_m)  # un motero no tiene PIN que generar
        self.assertEqual(self.client.post("/mi-taller/pin/").status_code, 302)

    def test_el_taller_elegido_se_recuerda_en_el_dispositivo(self):
        r = self.post_canje(self.codigo.codigo, self.ta, self.pin_a)
        self.assertContains(r, "Cupón validado")
        self.assertIn("taller_canje", r.cookies)
        self.assertContains(self.client.get("/canjear/"), f'value="{self.ta.slug}" selected')


class CanjeAtomicoTests(Base):
    def test_doble_clic_es_idempotente(self):
        with self.captureOnCommitCallbacks(execute=True):
            canjear(self.codigo.codigo, taller=self.ta)
        with self.captureOnCommitCallbacks(execute=True):
            otra = canjear(self.codigo.codigo, taller=self.ta)
        self.assertTrue(otra.repetido)
        self.assertEqual(Notificacion.objects.filter(usuario=self.u_m, clave__startswith="canje:").count(), 1)

    def test_otro_taller_no_canjea_lo_ya_canjeado(self):
        canjear(self.codigo.codigo, taller=self.ta)
        with self.assertRaisesMessage(ErrorCanje, "ya se usó"):
            canjear(self.codigo.codigo, taller=self.tb)

    def test_dos_talleres_a_la_vez_solo_uno_gana(self):
        """Carrera: B ya lo canjeó en la base, pero A leyó el código antes (copia vieja). La actualización
        condicional lo detecta y A no lo pisa."""
        viejo = CodigoCupon.objects.select_related("cupon", "cupon__taller", "motociclista").get(pk=self.codigo.pk)
        CodigoCupon.objects.filter(pk=self.codigo.pk).update(canjeado_en=timezone.now(), canjeado_taller=self.tb)
        with mock.patch("cupones.servicios.CodigoCupon.objects.select_for_update") as sfu:
            sfu.return_value.select_related.return_value.filter.return_value.first.return_value = viejo
            with self.assertRaisesMessage(ErrorCanje, "se acaba de usar"):
                canjear(self.codigo.codigo, taller=self.ta)
        self.codigo.refresh_from_db()
        self.assertEqual(self.codigo.canjeado_taller, self.tb)

    def test_reenvio_pasado_el_rato_no_es_idempotente(self):
        canjear(self.codigo.codigo, taller=self.ta)
        CodigoCupon.objects.filter(pk=self.codigo.pk).update(canjeado_en=timezone.now() - timedelta(hours=1))
        with self.assertRaisesMessage(ErrorCanje, "ya se usó"):
            canjear(self.codigo.codigo, taller=self.ta)


class BitacoraYAvisoTests(Base):
    def test_canje_queda_con_quien_como_y_desde_donde_y_avisa_al_dueno(self):
        self.client.force_login(self.u_a)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post("/canjear/", {"codigo": self.codigo.codigo}, REMOTE_ADDR="10.1.2.3")
        self.codigo.refresh_from_db()
        self.assertEqual((self.codigo.canjeado_taller, self.codigo.canjeado_por, self.codigo.canje_via,
                          self.codigo.canje_ip), (self.ta, self.u_a, "cuenta", "10.1.2.3"))
        self.assertTrue(Notificacion.objects.filter(usuario=self.u_m, clave=f"canje:{self.codigo.pk}").exists())

    def test_canje_con_pin_registra_via_pin(self):
        self.post_canje(self.codigo.codigo, self.ta, self.pin_a)
        self.codigo.refresh_from_db()
        self.assertEqual((self.codigo.canje_via, self.codigo.canjeado_por), ("pin", None))


class SinFugasTests(Base):
    def test_vista_previa_sin_sesion_no_muestra_al_dueno_ni_el_estado(self):
        canjear(self.codigo.codigo, taller=self.tb)
        r = self.client.get("/canjear/", {"codigo": self.codigo.codigo})
        self.assertNotContains(r, "Ana")
        self.assertNotContains(r, "ya se usó")
        self.client.force_login(self.u_a)  # con la sesión del taller sí
        self.assertContains(self.client.get("/canjear/", {"codigo": self.codigo.codigo}), "Ana")

    def test_con_pin_malo_no_se_sabe_si_el_codigo_existe(self):
        malo = "000000" if self.pin_a != "000000" else "111111"
        existe = self.post_canje(self.codigo.codigo, self.ta, malo).content.decode()
        no_existe = self.post_canje("TY-ZZZZZZ", self.ta, malo).content.decode()
        self.assertIn("El código o el PIN no son correctos", existe)
        self.assertIn("El código o el PIN no son correctos", no_existe)


class CodigoServicioTests(Base):
    """El taller escribe en la hoja de vida solo con el código vigente que le dio el dueño."""

    def setUp(self):
        super().setUp()
        self.moto = Moto.objects.create(motociclista=self.motero, marca_otra="Yamaha", linea_otra="NMAX",
                                        tipo_otra="scooter", modelo=2022, km_inicial=1000, km_actual=5000)
        otro = Motociclista.objects.create(nombre="Beto", celular="573001110002")
        self.moto_otra = Moto.objects.create(motociclista=otro, marca_otra="Honda", linea_otra="CB", tipo_otra="calle",
                                             modelo=2020, km_inicial=0, km_actual=100)
        self.client.force_login(self.u_a)

    def guardar(self, codigo, moto=None):
        datos = {"codigo": codigo, "guardar": "1", "moto": (moto or self.moto).pk, "km": "5200",
                 "fecha": timezone.localdate().isoformat(), "otros": "Revisión general"}
        return self.client.post("/mi-taller/registrar-servicio/", datos, REMOTE_ADDR="10.9.8.7")

    def test_registro_con_codigo_queda_verificado_con_bitacora_y_aviso(self):
        cod = hoja_vida.generar_codigo(self.moto)
        self.guardar(cod.codigo)
        s = ServicioTaller.objects.get()
        self.assertEqual((s.estado, s.taller, s.registrado_por, s.ip), ("verificado", self.ta, self.u_a, "10.9.8.7"))
        self.assertTrue(Notificacion.objects.filter(usuario=self.u_m, clave=f"servicio-taller:{s.pk}").exists())
        cod.refresh_from_db()
        self.assertIsNotNone(cod.usado)

    def test_codigo_reusado_no_sirve(self):
        cod = hoja_vida.generar_codigo(self.moto)
        self.guardar(cod.codigo)
        self.guardar(cod.codigo)
        self.assertEqual(ServicioTaller.objects.count(), 1)

    def test_codigo_vencido_no_sirve(self):
        cod = hoja_vida.generar_codigo(self.moto)
        type(cod).objects.filter(pk=cod.pk).update(vence=timezone.now() - timedelta(minutes=1))
        r = self.client.get("/mi-taller/registrar-servicio/", {"codigo": cod.codigo})
        self.assertContains(r, "no es válido o ya caducó")
        self.guardar(cod.codigo)
        self.assertFalse(ServicioTaller.objects.exists())

    def test_codigo_de_una_moto_no_escribe_en_otra(self):
        cod = hoja_vida.generar_codigo(self.moto)
        self.guardar(cod.codigo, moto=self.moto_otra)
        self.assertFalse(ServicioTaller.objects.filter(moto=self.moto_otra).exists())

    def test_fuerza_bruta_de_codigos_frenada(self):
        from talleres.vista_servicios import CODIGOS_FALLIDOS_HORA
        for i in range(CODIGOS_FALLIDOS_HORA):
            self.client.get("/mi-taller/registrar-servicio/", {"codigo": f"ZZZZ{i:02d}"})
        cod = hoja_vida.generar_codigo(self.moto)
        r = self.client.get("/mi-taller/registrar-servicio/", {"codigo": cod.codigo})
        self.assertContains(r, "Demasiados códigos no válidos")

    def test_el_dueno_puede_rechazar_lo_registrado(self):
        from garaje import servicio_taller as st
        cod = hoja_vida.generar_codigo(self.moto)
        self.guardar(cod.codigo)
        s = ServicioTaller.objects.get()
        self.assertTrue(st.rechazar(s))
        self.assertFalse(s.registros.exists())

    def test_codigos_aleatorios_sin_ambiguos(self):
        cod = hoja_vida.generar_codigo(self.moto)
        self.assertRegex(cod.codigo, r"^[A-HJ-NP-Z2-9]{6}$")
        self.assertLessEqual(cod.vence - timezone.now(), timedelta(minutes=hoja_vida.MINUTOS_CODIGO))


@tag("lenta")
class MigracionPinTests(TransactionTestCase):
    """Los PIN que había en claro siguen sirviendo después de la migración, ya con hash."""

    def test_hashea_sin_perder_el_pin(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        antes, despues = [("talleres", "0018_perfil_estandarizado")], [("talleres", "0019_pin_con_hash")]
        ex = MigrationExecutor(connection)
        ex.migrate(antes)
        viejo = ex.loader.project_state(antes).apps
        Barrio_ = viejo.get_model("talleres", "Barrio")
        Taller_ = viejo.get_model("talleres", "Taller")
        t = Taller_.objects.create(nombre="Viejo", slug="viejo", responsable="X", whatsapp="573000000000",
                                   direccion="X", barrio=Barrio_.objects.create(nombre="Zona X"), pin_canje="482913")
        ex = MigrationExecutor(connection)
        ex.loader.build_graph()
        ex.migrate(despues)
        ex = MigrationExecutor(connection)
        ex.loader.build_graph()
        ex.migrate(ex.loader.graph.leaf_nodes())
        nuevo = Taller.objects.get(pk=t.pk)
        self.assertTrue(nuevo.pin_correcto("482913"))
        self.assertNotIn("482913", nuevo.pin_hash)
