from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Barrio, Servicio, SolicitudCita, Taller


class TalleresTests(TestCase):
    def setUp(self):
        self.barrio = Barrio.objects.create(nombre="Belén")
        self.servicio = Servicio.objects.get_or_create(nombre="Frenos")[0]
        self.taller = Taller.objects.create(
            nombre="Taller Prueba", responsable="Ana", whatsapp="573001234567",
            direccion="Cra 1", barrio=self.barrio, activo=True,
        )
        self.taller.servicios.add(self.servicio)

    def test_inicio_lista_solo_activos(self):
        Taller.objects.create(nombre="Oculto", responsable="X", whatsapp="573000000000",
                              direccion="X", barrio=self.barrio, activo=False)
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, "Taller Prueba")
        self.assertNotContains(r, "Oculto")

    def test_filtro_por_servicio(self):
        otro = Servicio.objects.get_or_create(nombre="Llantas")[0]
        r = self.client.get(reverse("talleres:inicio"), {"servicio": otro.id})
        self.assertNotContains(r, "Taller Prueba")

    def test_slug_unico(self):
        t2 = Taller.objects.create(nombre="Taller Prueba", responsable="B", whatsapp="573000000000",
                                   direccion="X", barrio=self.barrio)
        self.assertEqual(t2.slug, "taller-prueba-2")

    def test_solicitar_cita(self):
        r = self.client.post(self.taller.get_absolute_url(), {
            "accion": "cita", "nombre": "Juan", "telefono": "3001112233", "moto": "NKD 125",
            "servicio": self.servicio.id, "fecha_preferida": date.today() + timedelta(days=1),
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(SolicitudCita.objects.count(), 1)

    def test_resena_y_calificacion(self):
        self.client.post(self.taller.get_absolute_url(),
                         {"accion": "resena", "nombre": "Pedro", "estrellas": 4, "comentario": "Bien"})
        self.assertEqual(self.taller.calificacion, 4)

    def test_registro_queda_inactivo_y_normaliza_whatsapp(self):
        # El registro de talleres ahora crea también la cuenta del taller.
        self.assertRedirects(self.client.get(reverse("talleres:registro")), reverse("cuentas:registro") + "?tipo=taller")
        r = self.client.post(reverse("cuentas:registro") + "?tipo=taller", {
            "email": "Luis@Taller.com", "password1": "ClaveSegura-2026", "password2": "ClaveSegura-2026",
            "nombre": "Nuevo Taller", "responsable": "Luis", "whatsapp": "300 123 4567",
            "direccion": "Cll 2", "barrio": self.barrio.id, "servicios": [self.servicio.id],
        })
        self.assertEqual(r.status_code, 302)
        t = Taller.objects.get(nombre="Nuevo Taller")
        self.assertFalse(t.activo)
        self.assertEqual(t.whatsapp, "573001234567")
        self.assertEqual(t.usuario.email, "luis@taller.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), t.usuario.pk)  # quedó con la sesión iniciada


class PaginasLegalesTests(TestCase):
    def test_paginas_legales_y_footer(self):
        for pagina in ("terminos", "privacidad", "cupones", "cookies"):
            with self.subTest(pagina=pagina):
                self.assertEqual(self.client.get(reverse("talleres:legal", args=[pagina])).status_code, 200)
        self.assertEqual(self.client.get("/legal/inventada/").status_code, 404)
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, reverse("talleres:legal", args=["privacidad"]))


class PerfilTallerTests(TestCase):
    def setUp(self):
        import tempfile
        from django.contrib.auth import get_user_model
        from django.test import override_settings
        self._media = override_settings(MEDIA_ROOT=tempfile.mkdtemp())
        self._media.enable()
        self.usuario = get_user_model().objects.create_user("t@x.com", "t@x.com", "x")
        barrio = Barrio.objects.create(nombre="Centro")
        self.taller = Taller.objects.create(nombre="Taller P", responsable="Ana", whatsapp="573001234567", direccion="Calle 1",
                                            barrio=barrio, activo=True, usuario=self.usuario)
        self.client.force_login(self.usuario)

    def tearDown(self):
        self._media.disable()

    def _imagen(self, nombre="f.png"):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        buf = BytesIO()
        Image.new("RGB", (4, 4), "red").save(buf, "PNG")
        return SimpleUploadedFile(nombre, buf.getvalue(), content_type="image/png")

    def test_edita_perfil_y_sube_fotos(self):
        s = Servicio.objects.get_or_create(nombre="Frenos")[0]
        r = self.client.post(reverse("talleres:editar_perfil"), {
            "descripcion": "Somos expertos", "horario": "Lun-Vie", "servicios": [s.pk],
            "galeria": [self._imagen("a.png"), self._imagen("b.png")]})
        self.assertRedirects(r, reverse("talleres:editar_perfil"))
        self.taller.refresh_from_db()
        self.assertEqual(self.taller.descripcion, "Somos expertos")
        self.assertEqual(self.taller.fotos.count(), 2)
        pagina = self.client.get(self.taller.get_absolute_url())
        self.assertContains(pagina, "perfil-galeria-foto")
        self.assertContains(pagina, "Editar mi perfil")

    def test_otro_usuario_no_puede_borrar_fotos(self):
        from django.contrib.auth import get_user_model
        from .models import FotoTaller
        foto = FotoTaller.objects.create(taller=self.taller, imagen=self._imagen())
        otro = get_user_model().objects.create_user("o@x.com", "o@x.com", "x")
        self.client.force_login(otro)
        self.assertEqual(self.client.post(reverse("talleres:eliminar_foto", args=[foto.pk])).status_code, 404)
        self.assertTrue(FotoTaller.objects.filter(pk=foto.pk).exists())
