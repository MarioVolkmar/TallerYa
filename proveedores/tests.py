"""Proveedores: modelo y migración de datos, alta asistida con enlace (token), autoregistro con su interruptor,
consola (permisos, acciones y bitácora) y contador de clics."""
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from consola.models import Ajuste, Bitacora

from .models import Categoria, EventoProveedor, Proveedor

User = get_user_model()
SECCION = reverse("consola:inicio") + "?seccion=proveedores"
MEDIA = tempfile.mkdtemp()


def accion(clave, pk):
    return reverse("consola:accion", args=[clave, pk])


@override_settings(MEDIA_ROOT=MEDIA)
class ProveedoresTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("adm@t.co", "adm@t.co", "clave-segura-123", is_staff=True)
        cls.root = User.objects.create_user("root@t.co", "root@t.co", "clave-segura-123", is_staff=True, is_superuser=True)
        cls.motero = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123")
        cls.grua = Categoria.objects.get(slug="grua")
        cls.cda = Categoria.objects.get(slug="cda")
        cls.publicado = Proveedor.objects.create(categoria=cls.grua, nombre="Grúas Ya", whatsapp="3001112233",
                                                 zonas=["Bello"], estado="publicado", origen_alta="equipo")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def asistido(self, **k):
        p = Proveedor.objects.create(categoria=self.cda, nombre=k.pop("nombre", "CDA Nuevo"), whatsapp="3005556677",
                                     origen_alta="asistido", **k)
        p.generar_token()
        p.save()
        return p

    # ---------- Modelo y migración ----------
    def test_migracion_crea_categorias_y_copia_los_cda(self):
        self.assertEqual(set(Categoria.objects.values_list("slug", flat=True)) >= {"grua", "cda", "soat"}, True)
        self.assertIn("vehiculo", self.grua.campos)
        copiados = Proveedor.objects.filter(categoria=self.cda, origen_alta="equipo")
        self.assertEqual(copiados.count(), 2)  # los dos CDA de tramites 0002
        servisuper = copiados.get(nombre="CDA Servisuper Medellín")
        self.assertEqual((servisuper.precio_desde, servisuper.municipio, servisuper.estado), (242200, "Medellín", "publicado"))
        self.assertTrue(servisuper.precio_fuente)
        self.assertFalse(servisuper.falta_aprobacion)  # datos públicos del equipo: no espera aprobación

    def test_numeros_con_y_sin_indicativo(self):
        p = Proveedor(whatsapp="300 111 2233", telefono="")
        self.assertEqual((p.wa_numero, p.tel_numero), ("573001112233", "573001112233"))
        p.telefono = "6044445566"
        self.assertEqual(p.tel_numero, "576044445566")

    def test_slug_unico_de_categoria(self):
        a = Categoria.objects.create(nombre="Lavaderos", singular="Lavadero")
        b = Categoria.objects.create(nombre="Lavaderos de lujo", singular="Lavadero")
        self.assertEqual((a.slug, b.slug), ("lavadero", "lavadero-2"))

    # ---------- Permisos ----------
    def test_consola_solo_administradores(self):
        for url in (SECCION, reverse("proveedores:nuevo"), reverse("proveedores:categoria_nueva"),
                    reverse("proveedores:editar", args=[self.publicado.pk])):
            self.assertEqual(self.client.get(url).status_code, 302, url)  # sin sesión: al login
        self.client.force_login(self.motero)
        self.assertEqual(self.client.get(reverse("proveedores:nuevo")).status_code, 403)
        self.assertEqual(self.client.post(accion("proveedores.verificar", self.publicado.pk), {"valor": "1"}).status_code, 403)
        self.publicado.refresh_from_db()
        self.assertFalse(self.publicado.verificado)

    # ---------- Alta asistida ----------
    def test_alta_asistida_genera_enlace_y_bitacora(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse("proveedores:nuevo"), {
            "categoria": self.cda.pk, "nombre": "CDA Envigado", "responsable": "Luz Marina", "whatsapp": "300 123 4567",
            "municipio": "Envigado", "zonas": ["Envigado"], "precio_desde": "230000", "extra_agenda": "on"})
        p = Proveedor.objects.get(nombre="CDA Envigado")
        self.assertRedirects(r, reverse("proveedores:enlace", args=[p.pk]))
        self.assertEqual((p.estado, p.origen_alta, p.whatsapp, p.agenda), ("por_revisar", "asistido", "3001234567", True))
        self.assertTrue(p.token_revision)
        self.assertTrue(Bitacora.objects.filter(accion="proveedores.alta_asistida", objeto_id=p.pk).exists())
        h = self.client.get(reverse("proveedores:enlace", args=[p.pk])).content.decode()
        self.assertIn(f"/proveedores/ficha/{p.token_revision}/", h)
        self.assertIn("https://wa.me/573001234567?text=Hola%20Luz", h)

    def test_no_se_publica_sin_aprobacion_del_proveedor(self):
        p = self.asistido()
        self.client.force_login(self.admin)
        self.client.post(accion("proveedores.estado", p.pk), {"valor": "publicado"})
        p.refresh_from_db()
        self.assertEqual(p.estado, "por_revisar")
        self.assertNotContains(self.client.get(SECCION), "cs-pildora-aprobar")

    def test_revision_por_enlace_corrige_y_aprueba(self):
        p = self.asistido()
        url = reverse("proveedores:revisar", args=[p.token_revision])
        r = self.client.get(url)
        self.assertContains(r, "CDA Nuevo")
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        datos = {"nombre": "CDA Nuevo Sur", "whatsapp": "3005556677", "zonas": ["Itagüí"], "extra_agenda": "on"}
        self.client.post(url, datos)  # sin autorizar: solo guarda
        p.refresh_from_db()
        self.assertEqual((p.nombre, p.aprobado_por_proveedor, p.agenda), ("CDA Nuevo Sur", None, True))
        self.client.post(url, {**datos, "autoriza": "on"})
        p.refresh_from_db()
        self.assertTrue(p.aprobado_por_proveedor and p.autoriza_datos)
        self.assertContains(self.client.get(url), "Aprobaste tu ficha")  # queda de solo lectura
        # Ya aprobado: el equipo lo publica con la píldora «Aprobar»
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(SECCION), "cs-pildora-aprobar")
        self.client.post(accion("proveedores.estado", p.pk), {"valor": "publicado"})
        p.refresh_from_db()
        self.assertEqual(p.estado, "publicado")
        b = Bitacora.objects.get(accion="proveedores.estado", objeto_id=p.pk)
        self.assertEqual((b.cambios[0]["antes"], b.cambios[0]["despues"]), ("Por revisar", "Publicado"))

    def test_enlace_vencido_y_renovar(self):
        p = self.asistido()
        viejo = p.token_revision
        Proveedor.objects.filter(pk=p.pk).update(token_creado=timezone.now() - timedelta(days=31))
        self.assertEqual(self.client.get(reverse("proveedores:revisar", args=[viejo])).status_code, 410)
        self.client.force_login(self.admin)
        self.client.post(accion("proveedores.renovar_enlace", p.pk), {"valor": "1"})
        p.refresh_from_db()
        self.assertNotEqual(p.token_revision, viejo)
        self.assertEqual(self.client.get(reverse("proveedores:revisar", args=[viejo])).status_code, 404)
        self.assertEqual(self.client.get(reverse("proveedores:revisar", args=[p.token_revision])).status_code, 200)
        self.assertTrue(Bitacora.objects.filter(accion="proveedores.renovar_enlace", objeto_id=p.pk).exists())

    def test_proveedor_del_equipo_no_tiene_enlace(self):
        self.client.force_login(self.admin)
        r = self.client.post(accion("proveedores.renovar_enlace", self.publicado.pk), {"valor": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Bitacora.objects.filter(accion="proveedores.renovar_enlace").exists())

    # ---------- Autoregistro ----------
    def test_autoregistro_llega_por_revisar(self):
        r = self.client.post(reverse("proveedores:unete"), {
            "categoria": self.grua.pk, "nombre": "Planchones Aburrá", "whatsapp": "3104445566", "zonas": ["Medellín", "Bello"],
            "abierto_24h": "on", "extra_vehiculo": "planchon", "autoriza": "on"})
        p = Proveedor.objects.get(nombre="Planchones Aburrá")
        self.assertRedirects(r, reverse("proveedores:enviada", args=[p.token_revision]))
        self.assertEqual((p.estado, p.origen_alta, p.vehiculo, p.autoriza_datos), ("por_revisar", "autoregistro", "planchon", True))
        self.assertFalse(p.falta_aprobacion)
        self.assertNotIn(p, Proveedor.objects.publicados())

    def test_autoregistro_exige_autorizacion_y_contacto(self):
        r = self.client.post(reverse("proveedores:unete"), {"categoria": self.grua.pk, "nombre": "Sin datos"})
        self.assertFalse(Proveedor.objects.filter(nombre="Sin datos").exists())
        self.assertIn("autoriza", r.context["form"].errors)
        self.assertIn("whatsapp", r.context["form"].errors)

    def test_interruptor_apaga_el_autoregistro(self):
        self.assertEqual(self.client.get(reverse("proveedores:unete")).status_code, 200)
        self.assertContains(self.client.get("/"), reverse("proveedores:unete"))
        self.client.force_login(self.root)
        self.client.post(reverse("consola:ajuste", args=["proveedores_registro"]), {"valor": "0"})
        self.assertFalse(Ajuste.objects.get(clave="proveedores_registro").valor)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("proveedores:unete")).status_code, 404)
        self.assertEqual(self.client.post(reverse("proveedores:unete"), {"nombre": "X"}).status_code, 404)
        self.assertNotContains(self.client.get("/"), reverse("proveedores:unete"))
        p = self.asistido()  # el enlace de revisión no depende del interruptor
        self.assertEqual(self.client.get(reverse("proveedores:revisar", args=[p.token_revision])).status_code, 200)

    def test_autoregistro_limite_por_conexion(self):
        from .views import ALTAS_HORA_IP
        for i in range(ALTAS_HORA_IP + 1):
            self.client.post(reverse("proveedores:unete"), {"categoria": self.grua.pk, "nombre": f"G{i}",
                                                            "whatsapp": "3104445566", "autoriza": "on"})
        self.assertEqual(Proveedor.objects.filter(nombre__startswith="G", origen_alta="autoregistro").count(), ALTAS_HORA_IP)

    # ---------- Consola ----------
    def test_seccion_filtra_por_categoria_y_estado(self):
        self.asistido(nombre="CDA Pendiente")
        self.client.force_login(self.admin)
        r = self.client.get(SECCION + "&categoria=grua")
        self.assertContains(r, "Grúas Ya")
        self.assertNotContains(r, "CDA Pendiente")
        r = self.client.get(SECCION + "&estado=por_revisar")
        self.assertContains(r, "CDA Pendiente")
        self.assertNotContains(r, "Grúas Ya")
        r = self.client.get(SECCION)
        self.assertContains(r, "+ Nuevo proveedor")
        self.assertContains(r, "+ Categoría")
        self.assertContains(r, "Ver reporte")

    def test_verificar_pausar_eliminar_con_bitacora(self):
        self.client.force_login(self.admin)
        pk = self.publicado.pk
        self.client.post(accion("proveedores.verificar", pk), {"valor": "1"})
        self.client.post(accion("proveedores.estado", pk), {"valor": "pausado"})
        self.publicado.refresh_from_db()
        self.assertEqual((self.publicado.verificado, self.publicado.estado), (True, "pausado"))
        self.assertContains(self.client.get(SECCION), 'aria-label="Verificado"')
        EventoProveedor.objects.create(proveedor_id=pk, fecha=timezone.localdate(), tipo="whatsapp", cantidad=3)
        self.client.post(accion("proveedores.eliminar", pk))
        self.assertFalse(Proveedor.objects.filter(pk=pk).exists())
        claves = set(Bitacora.objects.filter(objeto_id=pk, objeto_tipo="proveedor").values_list("accion", flat=True))
        self.assertEqual(claves, {"proveedores.verificar", "proveedores.estado", "proveedores.eliminar"})

    def test_editar_registra_cambios(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("proveedores:editar", args=[self.publicado.pk]), {
            "categoria": self.grua.pk, "nombre": "Grúas Ya 24/7", "whatsapp": "3001112233", "zonas": ["Bello"],
            "extra_vehiculo": "ambos"})
        self.publicado.refresh_from_db()
        self.assertEqual((self.publicado.nombre, self.publicado.vehiculo), ("Grúas Ya 24/7", "ambos"))
        b = Bitacora.objects.get(accion="proveedores.editar")
        self.assertIn({"campo": "nombre", "etiqueta": "Nombre", "antes": "Grúas Ya", "despues": "Grúas Ya 24/7"}, b.cambios)

    def test_nueva_categoria(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse("proveedores:categoria_nueva"), {
            "nombre": "Lavaderos", "singular": "Lavadero", "icono": "🧽", "etiqueta_precio": "Lavada desde",
            "inscripcion": "on", "orden": "5"})
        cat = Categoria.objects.get(nombre="Lavaderos")
        self.assertRedirects(r, SECCION + "&categoria=lavadero", fetch_redirect_response=False)
        self.assertTrue(Bitacora.objects.filter(accion="proveedores.categoria", objeto_id=cat.pk).exists())
        self.assertContains(self.client.get(reverse("proveedores:unete")), "Lavaderos")

    # ---------- Clics y reporte ----------
    def test_clics_se_cuentan_y_salen_en_el_reporte(self):
        url = reverse("proveedores:clic", args=[self.publicado.pk, "whatsapp"])
        ua = {"HTTP_USER_AGENT": "Mozilla/5.0 (Linux; Android 14)"}
        self.assertEqual(self.client.post(url, **ua).status_code, 204)
        self.client.post(url, **ua)
        self.client.post(url, HTTP_USER_AGENT="Googlebot")  # los bots no cuentan
        self.assertEqual(EventoProveedor.objects.get(proveedor=self.publicado).cantidad, 2)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(reverse("proveedores:clic", args=[self.publicado.pk, "otro"]), **ua).status_code, 404)
        self.client.force_login(self.admin)
        r = self.client.get(SECCION + f"&reporte={self.publicado.pk}")
        self.assertContains(r, "Reporte de Grúas Ya")
        self.assertEqual(r.context["total"]["whatsapp"], 2)

    def test_barra_lateral_saca_del_formulario(self):
        """Los enlaces de la barra lateral son relativos (?seccion=X): desde un formulario llevan a esa sección."""
        self.client.force_login(self.admin)
        for url in (reverse("proveedores:nuevo"), reverse("proveedores:categoria_nueva"),
                    reverse("proveedores:enlace", args=[self.publicado.pk]), reverse("consola:alta_taller")):
            self.assertRedirects(self.client.get(url + "?seccion=talleres"), reverse("consola:inicio") + "?seccion=talleres",
                                 fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("proveedores:nuevo")).status_code, 200)
