import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import SuscripcionPush
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
