"""Verificación de identidad del mecánico: subida, permisos de las fotos, estados e insignia «Verificado»."""
import io
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from consola.acciones import ACCIONES
from notificaciones.models import Notificacion

from . import identidad as servicio
from .models import IdentidadMecanico
from .tests import Base, User

E = IdentidadMecanico.Estado


def imagen(nombre="c.png", ancho=3000, alto=2000):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), (120, 90, 60)).save(buf, "PNG")
    return SimpleUploadedFile(nombre, buf.getvalue(), content_type="image/png")


class IdentidadBase(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_user("admin@prueba.com", "admin@prueba.com", "clave-segura-123", is_staff=True)

    def setUp(self):
        super().setUp()
        self.privado = tempfile.mkdtemp()
        ajuste = override_settings(PRIVADO_ROOT=Path(self.privado))
        ajuste.enable()
        self.addCleanup(ajuste.disable)
        self.addCleanup(shutil.rmtree, self.privado, True)

    def datos(self, **extra):
        d = {"frente": imagen("f.png"), "respaldo": imagen("r.png"), "autorizo": "on"}
        d.update(extra)
        return d

    def subir(self, **extra):
        self.client.force_login(self.dueno)
        return self.client.post(reverse("domicilio:identidad"), self.datos(**extra))


class SubidaTests(IdentidadBase):
    def test_sin_enviar_el_panel_pide_verificar(self):
        self.client.force_login(self.dueno)
        r = self.client.get(reverse("domicilio:panel"))
        self.assertContains(r, "Verifica tu identidad")
        self.assertEqual(servicio.estado_para_panel(self.aprobado), "pendiente")

    def test_subida_valida_guarda_en_privado_reducida_y_avisa_a_admins(self):
        r = self.subir(selfie=imagen("s.png"))
        self.assertRedirects(r, reverse("domicilio:identidad"))
        ident = IdentidadMecanico.objects.get(mecanico=self.aprobado)
        self.assertEqual(ident.estado, E.ENVIADA)
        for campo in ("frente", "respaldo", "selfie"):
            ruta = Path(getattr(ident, campo).path)
            self.assertTrue(str(ruta).startswith(str(Path(self.privado).resolve())))
            from PIL import Image
            with Image.open(ruta) as img:
                self.assertEqual(img.format, "JPEG")
                self.assertLessEqual(max(img.size), 1600)
        self.assertTrue(Notificacion.objects.filter(usuario=self.admin).exists())
        self.assertEqual(servicio.estado_para_panel(self.aprobado), "enviada")

    def test_selfie_es_opcional(self):
        self.subir()
        self.assertFalse(IdentidadMecanico.objects.get().selfie)

    def test_rechaza_archivo_falso_aunque_tenga_extension_de_imagen(self):
        falsa = SimpleUploadedFile("c.jpg", b"<html><script>alert(1)</script></html>", content_type="image/jpeg")
        r = self.subir(frente=falsa)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(IdentidadMecanico.objects.exists())

    def test_rechaza_archivo_muy_pesado(self):
        grande = SimpleUploadedFile("g.png", b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024), content_type="image/png")
        self.subir(respaldo=grande)
        self.assertFalse(IdentidadMecanico.objects.exists())

    def test_exige_frente_respaldo_y_autorizacion(self):
        self.client.force_login(self.dueno)
        url = reverse("domicilio:identidad")
        self.client.post(url, {"frente": imagen(), "autorizo": "on"})
        self.client.post(url, {"frente": imagen(), "respaldo": imagen()})
        self.assertFalse(IdentidadMecanico.objects.exists())

    def test_anonimo_va_a_entrar_y_quien_no_es_mecanico_al_registro(self):
        r = self.client.get(reverse("domicilio:identidad"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuenta/entrar/", r["Location"])
        sin_perfil = User.objects.create_user("x@prueba.com", "x@prueba.com", "clave-segura-123")
        self.client.force_login(sin_perfil)
        self.assertRedirects(self.client.get(reverse("domicilio:identidad")), reverse("domicilio:registro"))

    def test_en_revision_no_se_puede_reenviar(self):
        self.subir()
        antes = IdentidadMecanico.objects.get().frente.name
        self.client.post(reverse("domicilio:identidad"), self.datos())
        self.assertEqual(IdentidadMecanico.objects.get().frente.name, antes)


class PermisosFotosTests(IdentidadBase):
    def url(self, campo="frente"):
        return reverse("domicilio:identidad_foto", args=[IdentidadMecanico.objects.get().pk, campo])

    def test_solo_admin_ve_las_fotos(self):
        self.subir()
        self.client.logout()
        self.assertIn(self.client.get(self.url()).status_code, (302, 404))  # anónimo
        for usuario in (self.otro, self.dueno):  # otro usuario y hasta el dueño
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.admin)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/jpeg")
        self.assertIn("no-store", r["Cache-Control"])

    def test_foto_inexistente_o_campo_invalido_da_404(self):
        self.subir()
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url("selfie")).status_code, 404)  # no la subió
        self.assertEqual(self.client.get("/mecanicos/identidad/1/otro/").status_code, 404)

    def test_las_fotos_no_estan_en_media(self):
        from django.conf import settings
        self.subir()
        ident = IdentidadMecanico.objects.get()
        self.assertFalse(Path(ident.frente.path).is_relative_to(Path(settings.MEDIA_ROOT).resolve()))
        with self.assertRaises(ValueError):
            ident.frente.url


class EstadosEInsigniaTests(IdentidadBase):
    def consola(self, clave, mecanico, **post):
        self.client.force_login(self.admin)
        return self.client.post(reverse("consola:accion", args=[clave, mecanico.pk]), post)

    def test_sin_identidad_aprobada_no_hay_insignia_y_sigue_en_el_listado(self):
        self.assertFalse(self.aprobado.verificado)
        r = self.client.get(reverse("domicilio:listado"))
        self.assertContains(r, "Wilson Frenos")
        self.assertNotContains(r, "tc-chapa-verif")

    def test_enviar_no_da_insignia(self):
        self.subir()
        self.aprobado.refresh_from_db()
        self.assertFalse(self.aprobado.verificado)

    def test_aprobar_da_insignia_borra_fotos_y_avisa(self):
        self.subir()
        ident = IdentidadMecanico.objects.get()
        rutas = [Path(ident.frente.path), Path(ident.respaldo.path)]
        r = self.consola("mecanicos.identidad_aprobar", self.aprobado)
        self.assertIn(r.status_code, (200, 302))
        self.aprobado.refresh_from_db()
        ident.refresh_from_db()
        self.assertTrue(self.aprobado.verificado)
        self.assertEqual(ident.estado, E.APROBADA)
        self.assertEqual(ident.revisado_por, self.admin)
        self.assertFalse(any(p.exists() for p in rutas))
        self.assertFalse(ident.frente)
        self.assertTrue(Notificacion.objects.filter(usuario=self.dueno, titulo__icontains="Identidad verificada").exists())
        self.assertContains(self.client.get(reverse("domicilio:listado")), "tc-chapa-verif")

    def test_rechazar_pide_motivo_borra_fotos_y_avisa(self):
        self.subir()
        self.consola("mecanicos.identidad_rechazar", self.aprobado)  # sin motivo
        self.assertEqual(IdentidadMecanico.objects.get().estado, E.ENVIADA)
        self.consola("mecanicos.identidad_rechazar", self.aprobado, motivo="La foto sale borrosa")
        ident = IdentidadMecanico.objects.get()
        self.assertEqual((ident.estado, ident.motivo), (E.RECHAZADA, "La foto sale borrosa"))
        self.assertFalse(ident.frente)
        self.aprobado.refresh_from_db()
        self.assertFalse(self.aprobado.verificado)
        self.assertTrue(Notificacion.objects.filter(usuario=self.dueno, texto__contains="borrosa").exists())
        self.client.force_login(self.dueno)
        self.assertContains(self.client.get(reverse("domicilio:panel")), "borrosa")
        # puede volver a enviar
        self.client.post(reverse("domicilio:identidad"), self.datos())
        self.assertEqual(IdentidadMecanico.objects.get().estado, E.ENVIADA)

    def test_no_se_puede_dar_insignia_a_mano_sin_identidad(self):
        self.consola("mecanicos.verificar", self.aprobado, valor="1")
        self.aprobado.refresh_from_db()
        self.assertFalse(self.aprobado.verificado)
        servicio.enviar(self.aprobado, imagen(), imagen())
        servicio.aprobar(IdentidadMecanico.objects.get(), self.admin)
        self.consola("mecanicos.verificar", self.aprobado, valor="0")
        self.consola("mecanicos.verificar", self.aprobado, valor="1")
        self.aprobado.refresh_from_db()
        self.assertTrue(self.aprobado.verificado)

    def test_no_admin_no_puede_aprobar(self):
        self.subir()
        self.client.force_login(self.otro)
        r = self.client.post(reverse("consola:accion", args=["mecanicos.identidad_aprobar", self.aprobado.pk]))
        self.assertIn(r.status_code, (302, 403))
        self.aprobado.refresh_from_db()
        self.assertFalse(self.aprobado.verificado)

    def test_acciones_registradas_y_ficha_muestra_fotos_solo_a_admin(self):
        self.assertIn("mecanicos.identidad_aprobar", ACCIONES)
        self.subir()
        self.client.force_login(self.admin)
        r = self.client.get(reverse("consola:inicio"), {"seccion": "aprobaciones", "revisar": f"mecanicos-{self.aprobado.pk}"})
        self.assertContains(r, "Aprobar identidad")
        self.assertContains(r, "Rechazar con motivo")
        self.assertContains(r, reverse("domicilio:identidad_foto", args=[IdentidadMecanico.objects.get().pk, "frente"]))
        self.assertContains(self.client.get(reverse("consola:inicio"), {"seccion": "aprobaciones"}), "Wilson Frenos")

    def test_heredados_conservan_la_insignia(self):
        m = self.crear("Veterano", verificado=True)
        IdentidadMecanico.objects.create(mecanico=m, estado=E.APROBADA, heredada=True)
        self.assertEqual(servicio.estado_para_panel(m), "aprobada_heredada")
        self.assertTrue(servicio.puede_tener_insignia(m))
        m.refresh_from_db()
        self.assertTrue(m.verificado)
