"""Pruebas de la revisión de seguridad (nov. 2026): límites de intentos, IP real tras el proxy y reseñas propias."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from cuentas.limites import ip_cliente
from talleres.models import Barrio, Resena, Taller

User = get_user_model()


class IpClienteTests(TestCase):
    def test_sin_proxy_usa_remote_addr(self):
        r = RequestFactory().get("/", REMOTE_ADDR="1.2.3.4", HTTP_X_FORWARDED_FOR="9.9.9.9")
        self.assertEqual(ip_cliente(r), "1.2.3.4")

    @override_settings(PROXIES_DE_CONFIANZA=1)
    def test_tras_proxy_ignora_lo_que_inventa_el_cliente(self):
        r = RequestFactory().get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.6, 200.1.2.3")
        self.assertEqual(ip_cliente(r), "200.1.2.3")


class LoginLimiteTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user("ana@correo.co", "ana@correo.co", "clave-larga-123")

    def _entrar(self, clave):
        return self.client.post(reverse("cuentas:entrar"), {"username": "ana@correo.co", "password": clave})

    def test_bloquea_tras_10_fallos_aunque_la_clave_sea_buena(self):
        for _ in range(10):
            self._entrar("mala")
        r = self._entrar("clave-larga-123")
        self.assertContains(r, "Demasiados intentos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_clave_buena_entra_y_limpia_fallos(self):
        for _ in range(3):
            self._entrar("mala")
        self.assertEqual(self._entrar("clave-larga-123").status_code, 302)


class ResenasTests(TestCase):
    def setUp(self):
        cache.clear()
        self.dueno = User.objects.create_user("t@t.co", "t@t.co", "clave-larga-123")
        self.taller = Taller.objects.create(nombre="Taller Sec", responsable="Ana", whatsapp="573001234567",
                                            direccion="Cra 1", barrio=Barrio.objects.get_or_create(nombre="Belén")[0],
                                            activo=True, usuario=self.dueno)

    def _resenar(self):
        return self.client.post(reverse("talleres:detalle", args=[self.taller.slug]),
                                {"accion": "resena", "nombre": "Pepe", "estrellas": 5, "comentario": "Bien"})

    def test_anonimo_no_puede_inundar_de_resenas(self):
        for _ in range(6):
            self._resenar()
        self.assertEqual(Resena.objects.filter(taller=self.taller).count(), 3)

    def test_dueno_no_resena_su_taller(self):
        self.client.force_login(self.dueno)
        self._resenar()
        self.client.post(reverse("cuentas:calificar_taller", args=[self.taller.pk]), {"estrellas": 5})
        self.assertFalse(Resena.objects.filter(taller=self.taller).exists())


class TarjetaPropiedadTests(TestCase):
    def test_rechaza_archivo_que_no_es_imagen_ni_pdf(self):
        from tramites.forms import PedidoSoatForm
        falso = SimpleUploadedFile("tarjeta.pdf", b"<html><script>alert(1)</script>", content_type="application/pdf")
        form = PedidoSoatForm(data={}, files={"tarjeta_propiedad": falso})
        form.is_valid()
        self.assertIn("tarjeta_propiedad", form.errors)


class RecuperarLimiteTests(TestCase):
    def test_freno_de_solicitudes_de_recuperacion(self):
        from django.core import mail
        from django.core.cache import cache
        cache.clear()
        get_user_model().objects.create_user("lim", "lim@x.com", "x")
        for _ in range(5):
            r = self.client.post(reverse("cuentas:recuperar"), {"email": "lim@x.com"})
            self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 3)  # tope por correo: 3 por hora; el resto responde igual, sin enviar
        cache.clear()
