"""Rechazar con motivo, avisos al solicitante y la bandeja «Por aprobar»."""
from django.contrib.auth import get_user_model
from django.urls import reverse

from domicilio.models import MecanicoDomicilio
from proveedores.models import Categoria, Proveedor
from talleres.models import Taller

from .models import Bitacora
from .tests import INICIO, Base

User = get_user_model()
E = MecanicoDomicilio.Estado


class RechazoTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.dueno = User.objects.create_user("meca@t.co", "meca@t.co", "clave-segura-123")
        cls.mecanico = MecanicoDomicilio.objects.create(nombre="Beto", whatsapp="573000000111", usuario=cls.dueno)
        cls.taller_nuevo = Taller.objects.create(nombre="Taller Nuevo", responsable="R", whatsapp="573000000222", direccion="Cra 2",
                                                 barrio=cls.barrio, usuario=User.objects.create_user("t@t.co", "t@t.co", "clave-segura-123"))
        cls.proveedor = Proveedor.objects.create(categoria=Categoria.objects.get(slug="grua"), nombre="Grúas X", whatsapp="3001112233")

    def test_rechazar_mecanico_exige_motivo_y_avisa(self):
        self.assertEqual(self.post("mecanicos.rechazar", self.mecanico.pk).status_code, 400)
        self.assertEqual(self.post("mecanicos.rechazar", self.mecanico.pk, motivo="abc").status_code, 400)
        self.assertTrue(self.post("mecanicos.rechazar", self.mecanico.pk, motivo="Falta tu cédula").json()["ok"])
        self.mecanico.refresh_from_db()
        self.assertEqual((self.mecanico.estado, self.mecanico.motivo_rechazo), (E.RECHAZADO, "Falta tu cédula"))
        n = self.dueno.notificaciones.get()
        self.assertIn("Falta tu cédula", n.texto)
        self.assertIn("Motivo: Falta tu cédula", Bitacora.objects.get().frase)

    def test_mecanico_rechazado_lo_ve_en_mi_perfil_y_al_corregir_vuelve_a_revision(self):
        self.post("mecanicos.rechazar", self.mecanico.pk, motivo="Foto borrosa")
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:mi_perfil"))
        self.assertContains(r, "Rechazado")
        self.assertContains(r, "Foto borrosa")
        self.assertNotContains(r, "Suspendido")
        # al guardar el perfil corregido vuelve a la fila de revisión
        from domicilio.models import Zona, TipoServicio
        zona, servicio = Zona.objects.first(), TipoServicio.objects.first()
        datos = {"nombre": "Beto", "whatsapp": "3001234567", "zonas": [zona.pk] if zona else [],
                 "servicios": [servicio.pk] if servicio else [], "anios_experiencia": 5, "cedula": "1.020.304.050"}
        r = self.client.post(reverse("domicilio:mi_perfil"), datos)
        self.assertEqual(r.status_code, 302, getattr(getattr(r, "context", None), "get", lambda k: None)("form") and r.context["form"].errors)
        self.mecanico.refresh_from_db()
        self.assertEqual((self.mecanico.estado, self.mecanico.motivo_rechazo), (E.PENDIENTE, ""))

    def test_estado_generico_no_rechaza_sin_motivo(self):
        self.assertEqual(self.post("mecanicos.estado", self.mecanico.pk, valor="rechazado").status_code, 400)
        self.assertEqual(self.post("proveedores.estado", self.proveedor.pk, valor="rechazado").status_code, 400)

    def test_rechazar_taller_avisa_y_sale_de_pendientes(self):
        from . import secciones
        antes = secciones._talleres_pendientes()
        self.assertTrue(self.post("talleres.rechazar", self.taller_nuevo.pk, motivo="Dirección que no existe").json()["ok"])
        self.taller_nuevo.refresh_from_db()
        self.assertFalse(self.taller_nuevo.activo)
        self.assertEqual(secciones._talleres_pendientes(), antes - 1)
        self.assertIn("Dirección que no existe", self.taller_nuevo.usuario.notificaciones.get().texto)
        lista = self.client.get(INICIO, {"seccion": "talleres"})
        self.assertContains(lista, "Rechazado")
        # aprobarlo después limpia el motivo y avisa
        self.post("talleres.publicar", self.taller_nuevo.pk, valor="1")
        self.taller_nuevo.refresh_from_db()
        self.assertTrue(self.taller_nuevo.activo)
        self.assertEqual(self.taller_nuevo.motivo_rechazo, "")
        self.assertEqual(self.taller_nuevo.usuario.notificaciones.count(), 2)

    def test_pausar_taller_publicado_avisa(self):
        self.taller.usuario = self.dueno
        self.taller.activo = True
        self.taller.save()
        self.post("talleres.publicar", self.taller.pk, valor="0")
        self.assertIn("pausado", self.dueno.notificaciones.get().titulo)

    def test_no_se_rechaza_un_taller_publicado(self):
        Taller.objects.filter(pk=self.taller.pk).update(activo=True)
        self.assertEqual(self.post("talleres.rechazar", self.taller.pk, motivo="Sin razón").status_code, 400)

    def test_rechazar_proveedor_guarda_motivo(self):
        self.assertTrue(self.post("proveedores.rechazar", self.proveedor.pk, motivo="No tiene permiso de grúa").json()["ok"])
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.estado, Proveedor.Estado.RECHAZADO)
        self.assertEqual(self.proveedor.motivo_rechazo, "No tiene permiso de grúa")
        r = self.client.get(INICIO, {"seccion": "proveedores"})
        self.assertContains(r, "No tiene permiso de grúa")

    def test_solo_admin_rechaza(self):
        self.client.force_login(self.motero)
        self.assertEqual(self.post("mecanicos.rechazar", self.mecanico.pk, motivo="Nada de nada").status_code, 403)


class BandejaTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mecanico = MecanicoDomicilio.objects.create(nombre="Beto", whatsapp="573000000111")
        cls.pendiente = Taller.objects.create(nombre="Taller Pendiente", responsable="R", whatsapp="573000000222",
                                              direccion="Cra 2", barrio=cls.barrio, origen_alta=Taller.Alta.CUENTA)
        cls.proveedor = Proveedor.objects.create(categoria=Categoria.objects.get(slug="grua"), nombre="Grúas X", whatsapp="3001112233")

    def test_lista_los_tipos_con_antiguedad_y_botones(self):
        r = self.client.get(INICIO, {"seccion": "aprobaciones"})
        for texto in ("Beto", "Taller Pendiente", "Esperando", "Revisar y aprobar", "Rechazar"):
            self.assertContains(r, texto)
        self.assertContains(r, 'data-motivo="Rechazar a Beto"')

    def test_ficha_de_revision_muestra_datos_faltantes_y_confirma_con_el_nombre(self):
        r = self.client.get(INICIO, {"seccion": "aprobaciones", "revisar": f"mecanicos-{self.mecanico.pk}"})
        self.assertContains(r, "Qué revisar antes de aprobar")
        self.assertContains(r, "Falta")  # cédula, zonas, etc. vacíos
        self.assertContains(r, 'data-confirmar="¿Aprobar a Beto?')
        self.assertContains(r, 'data-motivo="Rechazar a Beto"')
        for tipo, obj in (("talleres", self.pendiente), ("proveedores", self.proveedor)):
            self.assertContains(self.client.get(INICIO, {"seccion": "aprobaciones", "revisar": f"{tipo}-{obj.pk}"}), obj.nombre)
        self.assertEqual(self.client.get(INICIO, {"seccion": "aprobaciones", "revisar": "x-1"}).status_code, 404)

    def test_proveedor_sin_ficha_aprobada_no_se_aprueba_desde_la_bandeja(self):
        from .vistas.aprobaciones import pendientes_por_tipo
        items = pendientes_por_tipo()["proveedores"]
        self.assertEqual(items[0]["aprobar"] is None, self.proveedor.falta_aprobacion)

    def test_filtra_por_tipo(self):
        r = self.client.get(INICIO, {"seccion": "aprobaciones", "tipo": "mecanicos"})
        self.assertContains(r, "Beto")
        self.assertNotContains(r, "Taller Pendiente")

    def test_la_insignia_suma_las_cuatro_sin_contar_doble(self):
        from . import secciones
        filas, total = secciones.con_pendientes()
        n = dict((s.key, n) for s, n in filas)
        self.assertEqual(n["aprobaciones"], n["mecanicos"] + n["talleres"] + n["proveedores"] + n["usuarios"])
        self.assertEqual(total, n["aprobaciones"] + sum(v for k, v in n.items() if k not in secciones.AGRUPADAS | {"aprobaciones"}))

    def test_aprobar_desde_la_bandeja_publica(self):
        self.post("mecanicos.estado", self.mecanico.pk, valor="aprobado")
        self.mecanico.refresh_from_db()
        self.assertEqual(self.mecanico.estado, E.APROBADO)
