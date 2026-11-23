from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from garaje.avisos import avisos_documentos
from django.core.files.uploadedfile import SimpleUploadedFile

from garaje.models import LineaMoto, Moto
from notificaciones.models import Notificacion
from talleres.models import Marca

from proveedores.models import Categoria, Proveedor

from .models import PedidoSoat, TarifaSoat


class TramitesTests(TestCase):
    def test_migracion_carga_tarifas_oficiales_2026(self):
        self.assertEqual(TarifaSoat.objects.get(anio=2026, categoria="moto_100_200").valor, 343300)

    def setUp(self):
        self.usuario = get_user_model().objects.create_user("m@m.co", "m@m.co", "clave-larga-123")
        self.motero = Motociclista.objects.create(usuario=self.usuario, nombre="Ana", celular="573001234567")
        marca = Marca.objects.get_or_create(nombre="Pruebas")[0]
        linea = LineaMoto.objects.create(marca=marca, nombre="P 150", cilindraje=150)
        self.moto = Moto.objects.create(motociclista=self.motero, linea=linea, modelo=2022, placa="ABC12D", km_actual=1000, km_inicial=0,
                                        soat_vence=date.today() + timedelta(days=2),
                                        tecno_vence=date.today() + timedelta(days=10))

    def _vaciar(self):
        TarifaSoat.objects.all().delete()
        Proveedor.objects.filter(categoria__slug="cda").delete()

    def test_categoria_por_cilindraje(self):
        C = TarifaSoat.Categoria
        self.assertEqual(TarifaSoat.categoria_para(99), C.MENOS_100)
        self.assertEqual(TarifaSoat.categoria_para(200), C.DE_100_A_200)
        self.assertEqual(TarifaSoat.categoria_para(201), C.MAS_200)
        self.assertIsNone(TarifaSoat.categoria_para(None))

    def test_soat_sin_tarifa_no_inventa_precio(self):
        self._vaciar()
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("tramites:soat"))
        self.assertContains(r, "Motos de 100 a 200 cc")
        self.assertContains(r, "Por confirmar")

    def test_soat_con_tarifa_y_visitante_por_cilindraje(self):
        self._vaciar()
        TarifaSoat.objects.create(anio=date.today().year, categoria="moto_200", valor=500000, fuente="https://ejemplo.co")
        r = self.client.get(reverse("tramites:soat") + "?cc=250")
        self.assertContains(r, "500.000")
        self.assertContains(r, "Crear cuenta y pedir mi SOAT")

    DATOS = {"placa": "ABC12D", "tipo_documento": "CC", "numero_documento": "1.020.304.050",
             "nombre_completo": "Ana Pérez", "chasis_motor": "9fbx123456", "correo": "ana@correo.co",
             "direccion": "Cra 70 #44-10, Medellín", "celular": "300 123 4567", "acepta_datos": "on"}

    def _pedir(self, **cambios):
        self.client.force_login(self.usuario)
        return self.client.post(reverse("tramites:pedir_soat", args=[self.moto.pk]), {**self.DATOS, **cambios})

    def test_pedido_guarda_datos_y_precio_de_ley(self):
        self._pedir()
        pedido = PedidoSoat.objects.get()
        self.assertEqual((pedido.estado, pedido.valor, pedido.numero_documento, pedido.celular, pedido.chasis_motor),
                         ("recibido", 343300, "1020304050", "3001234567", "9FBX123456"))
        self.assertIsNotNone(pedido.acepta_datos_en)
        r = self.client.get(reverse("tramites:soat") + f"?moto={self.moto.pk}")
        self.assertContains(r, "Recibido")
        self.assertContains(r, "Te avisamos cuando tu póliza esté lista para pagar")

    def test_sin_autorizacion_de_datos_no_crea_pedido(self):
        datos = dict(self.DATOS); datos.pop("acepta_datos")
        self.client.force_login(self.usuario)
        self.client.post(reverse("tramites:pedir_soat", args=[self.moto.pk]), datos)
        self.assertFalse(PedidoSoat.objects.exists())
        r = self.client.get(reverse("tramites:soat") + f"?moto={self.moto.pk}")
        self.assertContains(r, "necesitamos tu autorización")

    def test_pide_chasis_o_foto_de_tarjeta(self):
        self._pedir(chasis_motor="")
        self.assertFalse(PedidoSoat.objects.exists())
        foto = SimpleUploadedFile("tarjeta.jpg", b"\xff\xd8\xffJPEG de prueba", content_type="image/jpeg")
        self._pedir(chasis_motor="", tarjeta_propiedad=foto)
        pedido = PedidoSoat.objects.get()
        self.assertTrue(pedido.tarjeta_propiedad.name.startswith("soat/"))
        self.assertEqual(self.client.get(reverse("tramites:tarjeta", args=[pedido.pk])).status_code, 302)  # solo equipo
        pedido.tarjeta_propiedad.delete(save=False)

    def test_un_solo_pedido_activo(self):
        self._pedir(); self._pedir()
        self.assertEqual(PedidoSoat.objects.count(), 1)

    def test_no_pide_soat_de_moto_ajena(self):
        otro = get_user_model().objects.create_user("o@o.co", "o@o.co", "clave-larga-123")
        Motociclista.objects.create(usuario=otro, nombre="Otro", celular="573009999999")
        self.client.force_login(otro)
        r = self.client.post(reverse("tramites:pedir_soat", args=[self.moto.pk]), self.DATOS)
        self.assertEqual(r.status_code, 404)
        self.assertFalse(PedidoSoat.objects.exists())

    def test_flujo_completo_con_pago_de_prueba(self):
        self._pedir()
        pedido = PedidoSoat.objects.get()
        url_pago = reverse("tramites:pago_prueba", args=[pedido.pk])
        self.client.post(url_pago)                                   # aún no está lista para pagar: no hace nada
        pedido.refresh_from_db(); self.assertEqual(pedido.estado, "recibido")
        pedido.cambiar_estado(PedidoSoat.Estado.LISTA_PAGAR)
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, clave=f"pedido-soat:{pedido.pk}:lista").exists())
        r = self.client.get(reverse("tramites:soat") + f"?moto={self.moto.pk}")
        self.assertContains(r, url_pago)
        self.assertContains(self.client.get(url_pago), "Simulación")
        self.client.post(url_pago)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, "pagada"); self.assertTrue(pedido.pago_simulado)
        pedido.inicio_vigencia = date(2026, 11, 20)
        pedido.cambiar_estado(PedidoSoat.Estado.EMITIDA)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.soat_vence, date(2027, 11, 20))
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, clave=f"pedido-soat:{pedido.pk}:emitida").exists())

    def test_ficha_de_la_moto_muestra_el_estado(self):
        self._pedir()
        r = self.client.get(reverse("garaje:moto", args=[self.moto.pk]))
        self.assertContains(r, "SOAT: recibido")

    def test_pago_de_otro_no_se_puede(self):
        self._pedir()
        pedido = PedidoSoat.objects.get(); pedido.cambiar_estado(PedidoSoat.Estado.LISTA_PAGAR)
        otro = get_user_model().objects.create_user("x@x.co", "x@x.co", "clave-larga-123")
        Motociclista.objects.create(usuario=otro, nombre="X", celular="573008888888")
        self.client.force_login(otro)
        self.assertEqual(self.client.post(reverse("tramites:pago_prueba", args=[pedido.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("tramites:poliza", args=[pedido.pk])).status_code, 404)

    def test_admin_cambia_estado_con_avisos(self):
        self._pedir()
        pedido = PedidoSoat.objects.get()
        staff = get_user_model().objects.create_superuser("s@s.co", "s@s.co", "clave-larga-123")
        self.client.force_login(staff)
        r = self.client.post(reverse("admin:tramites_pedidosoat_changelist"),
                             {"action": "pasar_a_lista_pagar", "_selected_action": [pedido.pk]})
        self.assertEqual(r.status_code, 302)
        pedido.refresh_from_db(); self.assertEqual(pedido.estado, "lista_pagar")
        self.assertEqual(self.client.get(reverse("admin:tramites_pedidosoat_change", args=[pedido.pk])).status_code, 200)

    def test_cda_aliado_primero_y_whatsapp_con_placa(self):
        self._vaciar()
        cda = lambda nombre, **k: Proveedor.objects.create(categoria=Categoria.objects.get(slug="cda"), nombre=nombre,
                                                           municipio="Medellín", origen_alta="equipo", **k)
        cda("CDA Norte", direccion="Cra 1", whatsapp="573001112233", estado="publicado")
        cda("CDA Aliado", direccion="Cra 2", aliado=True, whatsapp="3004445566", estado="publicado")
        cda("CDA Inactivo", direccion="Cra 3", estado="pausado")
        self.client.force_login(self.usuario)
        h = self.client.get(reverse("tramites:tecnomecanica")).content.decode()
        self.assertLess(h.index("CDA Aliado"), h.index("CDA Norte"))
        self.assertNotIn("CDA Inactivo", h)
        self.assertIn("placa%20ABC12D", h)
        self.assertIn("https://wa.me/573004445566?text=", h)  # número sin indicativo: se completa con 57

    def test_tecno_sin_cda_muestra_aviso(self):
        self._vaciar()
        r = self.client.get(reverse("tramites:tecnomecanica"))
        self.assertContains(r, "Estamos sumando CDA aliados")

    def test_avisos_llevan_a_la_solucion(self):
        urls = {a["url"] for a in avisos_documentos(self.moto)}
        self.assertIn(f"/soat/?moto={self.moto.pk}", urls)
        self.assertIn(f"/tecnomecanica/?moto={self.moto.pk}", urls)


class TramitesAbiertosTests(TestCase):
    """Los trámites se abren sin cuenta y sin moto; el menú y la portada los enlazan."""

    def test_soat_sin_sesion_por_categoria_muestra_precio_de_ley(self):
        r = self.client.get(reverse("tramites:soat"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Pide tu")
        r = self.client.get(reverse("tramites:soat") + "?cat=moto_200")
        self.assertContains(r, "Motos de más de 200 cc")
        self.assertContains(r, "761.400")                 # tarifa 2026 cargada por la migración
        self.assertContains(r, "next=/soat/%3Fcat%3Dmoto_200")
        self.assertEqual(self.client.get(reverse("tramites:soat") + "?cat=inventada&moto=99").status_code, 200)

    def test_tecnomecanica_sin_sesion_ni_moto(self):
        r = self.client.get(reverse("tramites:tecnomecanica") + "?moto=abc")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "CDA")

    def test_menu_y_portada_enlazan_los_tramites(self):
        h = self.client.get(reverse("talleres:inicio")).content.decode()
        for nombre in ("tramites:soat", "tramites:tecnomecanica", "garaje:diagnostico", "talleres:emergencias"):
            self.assertIn(reverse(nombre), h)
        self.assertIn("data-diag-portada", h)  # el diagnóstico salió del menú: acceso en la portada
        self.assertIn(">Diagnóstico</a>", h)   # y en el pie
        self.assertIn("Resuelve sin salir de TallerYa", h)
