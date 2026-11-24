"""Descuentos de los mecánicos a domicilio: por dentro son cupones (cupones.Cupon con `mecanico`), con código y canje
para el reporte; por fuera se llaman «descuentos». El mecánico los canjea con su sesión: al marcar la visita
«Atendida» o escribiendo el código."""
from django.db import IntegrityError, transaction
from django.urls import reverse

from cupones.models import CodigoCupon, Cupon, Motociclista
from cupones.servicios import ErrorCanje, canjear
from talleres.models import Barrio, Taller

from .models import MecanicoDomicilio, SolicitudVisita
from .tests import Base, User


class DescuentosBase(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        barrio = Barrio.objects.get_or_create(nombre="Barrio de prueba")[0]
        cls.taller = Taller.objects.create(nombre="Taller A", responsable="Ana", whatsapp="573001234567",
                                           direccion="Cra 1", barrio=barrio, activo=True)
        cls.descuento = Cupon.objects.create(mecanico=cls.aprobado, titulo="10% en frenos si lo pides por TallerYa")
        cls.de_otro = Cupon.objects.create(mecanico=cls.envigadeno, titulo="Despinche gratis")
        cls.del_taller = Cupon.objects.create(taller=cls.taller, titulo="15% en aceite")
        cls.del_pendiente = Cupon.objects.create(mecanico=cls.pendiente, titulo="No se ve")
        cls.motero = User.objects.create_user("moto@prueba.com", "moto@prueba.com", "clave-segura-123", first_name="Camilo")
        cls.moto = Motociclista.objects.create(nombre="Camilo", celular="573005551234", usuario=cls.motero)

    def codigo(self, cupon=None):
        return CodigoCupon.objects.create(cupon=cupon or self.descuento, motociclista=self.moto)


class ModeloYListasTests(DescuentosBase):
    def test_un_cupon_no_puede_ser_de_taller_y_de_mecanico(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cupon.objects.create(taller=self.taller, mecanico=self.aprobado, titulo="Doble")

    def test_disponibles_solo_de_mecanicos_publicados(self):
        ids = set(Cupon.objects.disponibles().values_list("pk", flat=True))
        self.assertIn(self.descuento.pk, ids)
        self.assertNotIn(self.del_pendiente.pk, ids)

    def test_pagina_de_descuentos_filtra_por_tipo_servicio_y_zona(self):
        url = reverse("cupones:lista")
        r = self.client.get(url)
        self.assertContains(r, "10% en frenos")
        self.assertContains(r, "A domicilio")
        r = self.client.get(url, {"tipo": "domicilio"})
        self.assertContains(r, "10% en frenos")
        self.assertNotContains(r, "15% en aceite")
        r = self.client.get(url, {"tipo": "talleres"})
        self.assertNotContains(r, "10% en frenos")
        self.assertContains(r, "15% en aceite")
        r = self.client.get(url, {"donde": f"z-{self.envigado.pk}"})
        self.assertContains(r, "Despinche gratis")
        self.assertNotContains(r, "10% en frenos")
        r = self.client.get(url, {"servicio": "Frenos"})
        self.assertContains(r, "10% en frenos")
        self.assertNotContains(r, "Despinche gratis")

    def test_ficha_del_mecanico_muestra_sus_descuentos(self):
        r = self.client.get(self.aprobado.get_absolute_url())
        self.assertContains(r, "Cupones si lo pides por TallerYa")
        self.assertContains(r, "10% en frenos")
        self.assertNotContains(r, "Despinche gratis")

    def test_listado_con_descuento(self):
        r = self.client.get(reverse("domicilio:listado"), {"descuento": "1", "tipo": "independientes"})
        nombres = {m.nombre for m in r.context["pagina"]}
        self.assertEqual(nombres, {"Wilson Frenos", "Yeison Llantas"})
        Cupon.objects.filter(mecanico=self.envigadeno).update(activo=False)
        r = self.client.get(reverse("domicilio:listado"), {"descuento": "1", "tipo": "independientes"})
        self.assertEqual({m.nombre for m in r.context["pagina"]}, {"Wilson Frenos"})

    def test_tomar_el_descuento_y_verlo(self):
        self.client.force_login(self.motero)
        r = self.client.post(reverse("cupones:obtener", args=[self.descuento.pk]))
        codigo = CodigoCupon.objects.get(cupon=self.descuento)
        self.assertRedirects(r, codigo.get_absolute_url())
        r = self.client.get(codigo.get_absolute_url())
        self.assertContains(r, "Muéstraselo al mecánico")
        self.assertContains(r, "Wilson Frenos")


class PanelDelMecanicoTests(DescuentosBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.dueno)

    def test_panel_lleva_a_mis_descuentos_sin_alargar_los_accesos(self):
        r = self.client.get(reverse("domicilio:panel"))
        self.assertContains(r, "Tus cupones")
        self.assertContains(r, reverse("domicilio:descuentos"))
        self.assertEqual(r.content.decode().count('class="pt-acceso"'), 6)

    def test_crear_editar_y_pausar(self):
        r = self.client.post(reverse("domicilio:descuento_nuevo"), {"titulo": "Revisión gratis", "condiciones": "", "cupo": "5"})
        self.assertRedirects(r, reverse("domicilio:descuentos"))
        nuevo = Cupon.objects.get(titulo="Revisión gratis")
        self.assertEqual((nuevo.mecanico, nuevo.taller, nuevo.publico, nuevo.solo_plus), (self.aprobado, None, True, False))
        self.client.post(reverse("domicilio:descuento_editar", args=[nuevo.pk]), {"titulo": "Revisión a mitad", "cupo": ""})
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.titulo, nuevo.cupo), ("Revisión a mitad", None))
        self.client.post(reverse("domicilio:descuento_pausar", args=[nuevo.pk]))
        nuevo.refresh_from_db()
        self.assertFalse(nuevo.activo)
        self.assertContains(self.client.get(reverse("domicilio:descuentos")), "Revisión a mitad")

    def test_no_edita_descuentos_ajenos(self):
        self.assertEqual(self.client.get(reverse("domicilio:descuento_editar", args=[self.de_otro.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("domicilio:descuento_pausar", args=[self.del_taller.pk])).status_code, 404)

    def test_validar_codigo(self):
        codigo = self.codigo()
        r = self.client.post(reverse("domicilio:descuentos"), {"codigo": codigo.codigo.lower()})
        self.assertRedirects(r, reverse("domicilio:descuentos"))
        codigo.refresh_from_db()
        self.assertEqual((codigo.canjeado_mecanico, codigo.canje_via, codigo.canjeado_taller), (self.aprobado, "codigo", None))
        r = self.client.post(reverse("domicilio:descuentos"), {"codigo": codigo.codigo})
        self.assertContains(r, "ya se usó")

    def test_no_valida_codigos_de_otros(self):
        for cupon in (self.de_otro, self.del_taller):
            codigo = self.codigo(cupon)
            r = self.client.post(reverse("domicilio:descuentos"), {"codigo": codigo.codigo})
            self.assertContains(r, "no es de tus cupones")
            codigo.refresh_from_db()
            self.assertFalse(codigo.canjeado)

    def test_pendiente_no_puede_validar(self):
        MecanicoDomicilio.objects.filter(pk=self.pendiente.pk).update(usuario=self.otro)
        codigo = self.codigo(self.del_pendiente)
        self.client.force_login(self.otro)
        r = self.client.post(reverse("domicilio:descuentos"), {"codigo": codigo.codigo})
        self.assertContains(r, "aún no está publicado")

    def test_el_taller_no_canjea_descuentos_de_mecanicos(self):
        codigo = self.codigo()
        with self.assertRaisesMessage(ErrorCanje, "no vale en talleres"):
            canjear(codigo.codigo, taller=self.taller)


class VisitaConDescuentoTests(DescuentosBase):
    def pedir(self):
        datos = {"nombre": "Camilo", "telefono": "300 555 1234", "servicio": self.frenos.pk, "zona": self.robledo.pk}
        return self.client.post(reverse("domicilio:visita", args=[self.aprobado.slug]), datos)

    def estado(self, s, estado):
        return self.client.post(reverse("domicilio:solicitud_estado", args=[s.pk]), {"estado": estado})

    def test_el_descuento_del_motero_queda_anotado_y_se_usa_al_atender(self):
        codigo = self.codigo()
        self.client.force_login(self.motero)
        self.assertContains(self.client.get(self.aprobado.get_absolute_url()), "Tu cupón")
        r = self.pedir()
        self.assertIn(codigo.codigo, r["Location"])  # va en el mensaje de WhatsApp
        s = SolicitudVisita.objects.get()
        self.assertEqual(s.codigo_cupon, codigo)
        self.assertContains(self.client.get(s.get_absolute_url()), "Tu cupón")
        self.client.force_login(self.dueno)
        self.assertContains(self.client.get(reverse("domicilio:solicitudes")), "Trae cupón")
        self.estado(s, "confirmada")
        codigo.refresh_from_db()
        self.assertFalse(codigo.canjeado)
        self.estado(s, "atendida")
        codigo.refresh_from_db()
        self.assertEqual((codigo.canjeado_mecanico, codigo.canje_via), (self.aprobado, "visita"))

    def test_cancelar_libera_el_codigo(self):
        codigo = self.codigo()
        self.client.force_login(self.motero)
        self.pedir()
        s = SolicitudVisita.objects.get()
        self.client.force_login(self.dueno)
        self.estado(s, "cancelada")
        s.refresh_from_db()
        codigo.refresh_from_db()
        self.assertIsNone(s.codigo_cupon)
        self.assertFalse(codigo.canjeado)

    def test_el_mecanico_anota_el_codigo_que_le_dieron(self):
        self.pedir()  # sin sesión: no hay descuento anotado
        s = SolicitudVisita.objects.get()
        self.assertIsNone(s.codigo_cupon)
        codigo, ajeno = self.codigo(), self.codigo(self.de_otro)
        self.client.force_login(self.dueno)
        url = reverse("domicilio:solicitud_descuento", args=[s.pk])
        self.client.post(url, {"codigo": ajeno.codigo})
        s.refresh_from_db()
        self.assertIsNone(s.codigo_cupon)
        self.client.post(url, {"codigo": codigo.codigo})
        s.refresh_from_db()
        self.assertEqual(s.codigo_cupon, codigo)


class ConsolaYReporteTests(DescuentosBase):
    def setUp(self):
        super().setUp()
        root = User.objects.create_user("root@t.co", "root@t.co", "clave-segura-123", is_staff=True, is_superuser=True)
        self.client.force_login(root)

    def test_consola_cupones_filtra_por_mecanicos(self):
        r = self.client.get(reverse("consola:inicio"), {"seccion": "cupones", "de": "mecanicos"})
        self.assertContains(r, "10% en frenos")
        self.assertContains(r, "Descuento a domicilio")
        self.assertNotContains(r, "15% en aceite")
        r = self.client.get(reverse("consola:inicio"), {"seccion": "cupones", "q": "Wilson"})
        self.assertContains(r, "10% en frenos")

    def test_reporte_del_mecanico_cuenta_descuentos(self):
        from cupones.servicios import canjear_con_mecanico
        canjear_con_mecanico(self.codigo().codigo, self.aprobado)
        r = self.client.get(reverse("consola:inicio"), {"seccion": "reportes", "mecanico": self.aprobado.pk})
        self.assertContains(r, "Descuentos tomados")
        self.assertContains(r, "Descuentos usados")
        self.assertEqual(r.context["total"]["canjes"], 1)
        self.assertEqual(r.context["total"]["descuentos"], 1)
