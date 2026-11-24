import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Notificacion, SuscripcionPush
from .servicios import notificar

User = get_user_model()
SUB = {"endpoint": "https://push.example.com/abc", "keys": {"p256dh": "P" * 20, "auth": "A" * 10}}


class PwaTests(TestCase):
    def test_manifiesto_y_service_worker(self):
        r = self.client.get("/manifest.webmanifest")
        self.assertEqual(r.status_code, 200)
        datos = json.loads(r.content)
        self.assertEqual(datos["display"], "standalone")
        self.assertTrue(any(i["purpose"] == "maskable" for i in datos["icons"]))
        r = self.client.get("/sw.js")
        self.assertEqual(r.status_code, 200)
        self.assertIn("javascript", r["Content-Type"])
        self.assertContains(self.client.get("/sin-conexion/"), "Sin conexión")

    def test_base_enlaza_manifiesto(self):
        self.assertContains(self.client.get("/"), "manifest.webmanifest")


class PushTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("p@x.com", "p@x.com", "x")
        self.client.force_login(self.u)

    @override_settings(VAPID_PUBLIC_KEY="", VAPID_PRIVATE_KEY="")
    def test_sin_claves_todo_sigue_funcionando(self):
        self.assertFalse(self.client.get(reverse("notificaciones:push_estado")).json()["disponible"])
        with mock.patch("pywebpush.webpush") as w:
            self.assertIsNotNone(notificar(self.u, "k1", "Hola"))
        w.assert_not_called()

    @override_settings(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv")
    def test_suscribir_y_enviar_al_crear_aviso(self):
        r = self.client.post(reverse("notificaciones:push_suscribir"), json.dumps(SUB), content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SuscripcionPush.objects.filter(usuario=self.u).count(), 1)
        self.assertTrue(self.client.get(reverse("notificaciones:push_estado")).json()["activa"])
        with mock.patch("pywebpush.webpush") as w:
            notificar(self.u, "doc:1:soat:3", "SOAT vence pronto", "en 3 días", "/garaje/")
            notificar(self.u, "doc:1:soat:3", "SOAT vence pronto")  # repetido: no vuelve a enviar
        self.assertEqual(w.call_count, 1)
        carga = json.loads(w.call_args.kwargs["data"])
        self.assertEqual(carga["titulo"], "SOAT vence pronto")

    @override_settings(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv")
    def test_no_envia_a_quien_no_activo(self):
        with mock.patch("pywebpush.webpush") as w:
            notificar(self.u, "k2", "Algo")
        w.assert_not_called()

    def test_suscripcion_invalida_y_desactivar(self):
        url = reverse("notificaciones:push_suscribir")
        self.assertEqual(self.client.post(url, "no json", content_type="application/json").status_code, 400)
        mala = dict(SUB, endpoint="http://inseguro")
        self.assertEqual(self.client.post(url, json.dumps(mala), content_type="application/json").status_code, 400)
        self.client.post(url, json.dumps(SUB), content_type="application/json")
        self.client.post(reverse("notificaciones:push_desactivar"), json.dumps({"endpoint": SUB["endpoint"]}),
                         content_type="application/json")
        self.assertEqual(SuscripcionPush.objects.count(), 0)

    def test_requiere_sesion(self):
        self.client.logout()
        r = self.client.post(reverse("notificaciones:push_suscribir"), json.dumps(SUB), content_type="application/json")
        self.assertEqual(r.status_code, 302)


class PushRealTests(TestCase):
    """pywebpush de verdad (cifrado y firma VAPID) con la red simulada: la carga sale bien armada."""

    def test_webpush_completo_sin_red(self):
        import base64
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from py_vapid import Vapid01
        b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()  # noqa: E731
        clave = ec.generate_private_key(ec.SECP256R1())
        cliente = clave.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        vapid = Vapid01()
        vapid.generate_keys()
        privada = b64(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))
        publica = b64(vapid.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
        u = User.objects.create_user("r@x.com", "r@x.com", "x")
        SuscripcionPush.objects.create(usuario=u, endpoint="https://push.example.com/real", p256dh=b64(cliente), auth=b64(b"0123456789abcdef"))
        respuesta = mock.Mock(status_code=201)
        with override_settings(VAPID_PUBLIC_KEY=publica, VAPID_PRIVATE_KEY=privada), \
                mock.patch("requests.post", return_value=respuesta) as post:
            notificar(u, "k:real", "Hola", "texto", "/x/")
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.args[0], "https://push.example.com/real")
        self.assertIn("vapid", post.call_args.kwargs["headers"]["authorization"].lower())


@override_settings(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv", SITIO_URL="https://tallerya.co")
class CorreoRespaldoTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("c@x.com", "c@x.com", "x")

    def test_urgente_sin_push_manda_correo_con_baja(self):
        from django.core import mail
        with mock.patch("pywebpush.webpush"):
            notificar(self.u, "cita-nueva:1", "Ana pidió una cita", "12/12", "/mi-taller/citas/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["c@x.com"])
        self.assertIn("/avisos-correo/", mail.outbox[0].body)

    def test_no_urgente_no_manda_correo(self):
        from django.core import mail
        notificar(self.u, "foro-respuesta:1", "Te respondieron")
        self.assertEqual(len(mail.outbox), 0)

    def test_con_push_no_duplica(self):
        from django.core import mail
        SuscripcionPush.objects.create(usuario=self.u, endpoint="https://p.example.com/1", p256dh="P", auth="A")
        with mock.patch("pywebpush.webpush"):
            notificar(self.u, "visita-nueva:1", "Te pidieron una visita")
        self.assertEqual(len(mail.outbox), 0)

    def test_baja_y_reactivar(self):
        from django.core import mail
        from .correo import token_baja
        url = reverse("notificaciones:baja_correo", args=[token_baja(self.u)])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, {"accion": "desactivar"})
        notificar(self.u, "cita-cancelada:1", "Cancelaron tu cita")
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(url, {"accion": "activar"})
        notificar(self.u, "cita-cancelada:2", "Cancelaron tu cita")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.get(reverse("notificaciones:baja_correo", args=["falso"])).status_code, 404)


class AvisarAdminsTests(TestCase):
    def test_solo_admins_activos(self):
        from .servicios import avisar_admins
        a = User.objects.create_user("a@x.com", "a@x.com", "x", is_staff=True)
        User.objects.create_user("i@x.com", "i@x.com", "x", is_staff=True, is_active=False)
        User.objects.create_user("n@x.com", "n@x.com", "x")
        avisar_admins("registro-taller:1", "Taller nuevo por revisar", "Mi taller")
        avisar_admins("registro-taller:1", "Taller nuevo por revisar", "Mi taller")  # no se repite
        self.assertEqual(a.notificaciones.count(), 1)
        self.assertEqual(a.notificaciones.first().url, "/consola/")
        self.assertEqual(Notificacion.objects.count(), 1)


class TarjetaPushTests(TestCase):
    def test_una_vez_consume_la_bandera(self):
        from django.template import Context, Template
        from django.test import RequestFactory
        u = User.objects.create_user("t@x.com", "t@x.com", "x")
        r = RequestFactory().get("/")
        r.user = u
        r.session = {"sugerir_push": True}
        plantilla = Template('{% load push %}{% tarjeta_push "motero" una_vez=True %}')
        self.assertIn("data-push-tarjeta", plantilla.render(Context({"request": r})))
        self.assertNotIn("data-push-tarjeta", plantilla.render(Context({"request": r})))
        r.user = type("A", (), {"is_authenticated": False})()
        self.assertNotIn("data-push-tarjeta", Template('{% load push %}{% tarjeta_push "taller" %}').render(Context({"request": r})))
