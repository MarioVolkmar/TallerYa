from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cupones.models import CodigoCupon, Cupon, Motociclista
from talleres.models import Barrio, Taller

from .models import Suscripcion

User = get_user_model()
CLAVE = "Moto-segura-2026"


def datos_registro(**extra):
    datos = {"nombre": "Laura", "email": "Laura@Correo.com", "celular": "300 555 1234",
             "password1": CLAVE, "password2": CLAVE}
    datos.update(extra)
    return datos


class RegistroYSesionTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registro_crea_usuario_y_motociclista(self):
        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertRedirects(r, reverse("cuentas:mi_cuenta"))
        u = User.objects.get()
        self.assertEqual(u.username, "laura@correo.com")
        self.assertEqual(u.motociclista.celular, "573005551234")

    def test_entrar_con_correo_sin_importar_mayusculas(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        r = self.client.post(reverse("cuentas:entrar"), {"username": "LAURA@correo.com", "password": CLAVE})
        self.assertRedirects(r, reverse("talleres:inicio"))

    def test_next_externo_se_ignora(self):
        r = self.client.post(reverse("cuentas:registro") + "?next=https://malo.example/", datos_registro())
        self.assertRedirects(r, reverse("cuentas:mi_cuenta"))

    def test_celular_con_cupones_requiere_uno_de_sus_codigos(self):
        moto = Motociclista.objects.create(nombre="Laura", celular="573005551234")
        cupon = Cupon.objects.create(titulo="Lavado gratis")
        codigo = CodigoCupon.objects.create(cupon=cupon, motociclista=moto)

        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertContains(r, "Escribe uno de sus códigos")
        self.assertFalse(User.objects.exists())

        r = self.client.post(reverse("cuentas:registro"), datos_registro(codigo_existente=codigo.codigo.lower()))
        self.assertEqual(r.status_code, 302)
        moto.refresh_from_db()
        self.assertEqual(moto.usuario.email, "laura@correo.com")

    def test_celular_ya_vinculado_a_otra_cuenta(self):
        otro = User.objects.create_user("otro@correo.com", "otro@correo.com", CLAVE)
        Motociclista.objects.create(nombre="Otro", celular="573005551234", usuario=otro)
        r = self.client.post(reverse("cuentas:registro"), datos_registro())
        self.assertContains(r, "ya está asociado a otra cuenta")

    def test_recuperar_contrasena_envia_correo(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        self.client.post(reverse("cuentas:recuperar"), {"email": "laura@correo.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/cuenta/recuperar/", mail.outbox[0].body)

    def test_cupon_con_celular_de_cuenta_pide_iniciar_sesion(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.logout()
        cupon = Cupon.objects.create(titulo="Lavado gratis")
        r = self.client.post(reverse("cupones:obtener", args=[cupon.pk]), {"nombre": "X", "celular": "3005551234"})
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))
        self.assertFalse(CodigoCupon.objects.exists())


class PlusTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.moto = Motociclista.objects.get()
        barrio = Barrio.objects.create(nombre="Belén")
        self.taller = Taller.objects.create(nombre="Taller A", responsable="Ana", whatsapp="573001234567",
                                            direccion="Cra 1", barrio=barrio, activo=True)
        self.exclusivo = Cupon.objects.create(taller=self.taller, titulo="25% exclusivo", solo_plus=True)
        self.regalo = Cupon.objects.create(titulo="Regalo del mes", regalo_mensual=True)

    def test_solicitar_y_activar_plus(self):
        self.client.post(reverse("cuentas:solicitar_plus"))
        self.client.post(reverse("cuentas:solicitar_plus"))  # no duplica
        s = Suscripcion.objects.get()
        self.assertEqual(s.estado, Suscripcion.Estado.SOLICITADA)
        self.assertFalse(self.moto.es_plus)
        s.activar()
        self.assertTrue(self.moto.es_plus)
        self.assertEqual(s.vence, timezone.localdate() + timedelta(days=30))

    def test_renovar_suma_dias_al_vencimiento(self):
        s = Suscripcion.objects.create(motociclista=self.moto)
        s.activar()
        nueva = Suscripcion.objects.create(motociclista=self.moto)
        nueva.activar()
        s.refresh_from_db()
        self.assertEqual(s.estado, Suscripcion.Estado.CANCELADA)
        self.assertEqual(nueva.vence, timezone.localdate() + timedelta(days=60))

    def test_cupon_exclusivo_requiere_plus(self):
        r = self.client.post(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertRedirects(r, reverse("cuentas:plus"))
        self.assertFalse(CodigoCupon.objects.exists())

        Suscripcion.objects.create(motociclista=self.moto).activar()
        r = self.client.post(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertEqual(CodigoCupon.objects.get().cupon, self.exclusivo)

    def test_cupon_exclusivo_sin_sesion_pide_entrar(self):
        self.client.logout()
        r = self.client.get(reverse("cupones:obtener", args=[self.exclusivo.pk]))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_regalo_mensual_una_vez_por_mes_y_solo_plus(self):
        self.client.post(reverse("cuentas:reclamar_regalo"))
        self.assertFalse(CodigoCupon.objects.exists())

        Suscripcion.objects.create(motociclista=self.moto).activar()
        self.client.post(reverse("cuentas:reclamar_regalo"))
        self.client.post(reverse("cuentas:reclamar_regalo"))
        codigo = CodigoCupon.objects.get()
        self.assertEqual(codigo.origen, CodigoCupon.Origen.REGALO)

    def test_regalo_no_aparece_en_la_lista_publica(self):
        self.assertNotContains(self.client.get(reverse("cupones:lista")), "Regalo del mes")

    def test_pagina_plus_muestra_precio(self):
        r = self.client.get(reverse("cuentas:plus"))
        self.assertContains(r, "9.900")


class EntrarConSesionAbiertaTests(TestCase):
    def test_avisa_que_ya_hay_sesion_y_permite_cerrarla(self):
        u = User.objects.create_user("x@x.com", "x@x.com", CLAVE)
        self.client.force_login(u)
        r = self.client.get(reverse("cuentas:entrar"))
        self.assertContains(r, "Ya iniciaste sesión como")
        r = self.client.post(reverse("cuentas:salir"), {"next": reverse("cuentas:entrar")})
        self.assertRedirects(r, reverse("cuentas:entrar"))
        self.assertNotContains(self.client.get(reverse("cuentas:entrar")), "Ya iniciaste sesión como")


class RolesTests(TestCase):
    def setUp(self):
        from talleres.models import Barrio, Taller
        self.barrio = Barrio.objects.first() or Barrio.objects.create(nombre="Laureles")
        self.motero = User.objects.create_user("m@x.com", "m@x.com", "x", first_name="Mara")
        Motociclista.objects.create(nombre="Mara", celular="573005550000", usuario=self.motero)
        self.cuenta_taller = User.objects.create_user("t@x.com", "t@x.com", "x", first_name="Tomás")
        self.taller = Taller.objects.create(nombre="Taller Prueba", responsable="Tomás", whatsapp="573005551111",
                                            direccion="Cra 1", barrio=self.barrio, usuario=self.cuenta_taller)
        self.admin = User.objects.create_user("a@x.com", "a@x.com", "x", is_staff=True)

    def test_rol_de_cada_cuenta(self):
        from .roles import rol_de
        self.assertEqual([rol_de(self.motero), rol_de(self.cuenta_taller), rol_de(self.admin)], ["motero", "taller", "admin"])

    def test_navbar_segun_la_sesion(self):
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, "Crear cuenta")
        self.client.force_login(self.cuenta_taller)
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, 'nav-cuenta-nombre">Taller Prueba<')  # el taller ve su nombre en la cápsula
        self.assertContains(r, "Canjear cupón")
        self.assertNotContains(r, ">Crear cuenta<")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("talleres:inicio")), "Administración")

    def test_crear_cuenta_pregunta_el_tipo(self):
        r = self.client.get(reverse("cuentas:registro"))
        self.assertContains(r, "Soy motero")
        self.assertContains(r, "Tengo un taller")

    def test_administracion_solo_para_administradores(self):
        url = reverse("cuentas:administracion")
        self.client.force_login(self.motero)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.admin)
        r = self.client.get(url)
        self.assertContains(r, "Taller Prueba")  # aparece como pendiente
        self.client.post(reverse("cuentas:aprobar_taller", args=[self.taller.pk]))
        self.taller.refresh_from_db()
        self.assertTrue(self.taller.activo)

    def test_motero_no_puede_aprobar_talleres(self):
        self.client.force_login(self.motero)
        self.client.post(reverse("cuentas:aprobar_taller", args=[self.taller.pk]))
        self.taller.refresh_from_db()
        self.assertFalse(self.taller.activo)


class AvatarTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        self.carpeta = tempfile.mkdtemp()
        self.ajuste = override_settings(MEDIA_ROOT=self.carpeta)
        self.ajuste.enable()
        self.usuario = User.objects.create_user("av@x.com", "av@x.com", "x", first_name="Ana")
        Motociclista.objects.create(nombre="Ana", celular="573006660000", usuario=self.usuario)
        self.client.force_login(self.usuario)

    def tearDown(self):
        import shutil
        self.ajuste.disable()
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def foto(self, ancho=900, alto=500):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        img = Image.new("RGB", (ancho, alto), (200, 80, 30))
        exif = Image.Exif()
        exif[0x010F] = "Camara secreta"  # dato EXIF que debe desaparecer
        salida = BytesIO()
        img.save(salida, "JPEG", exif=exif)
        return SimpleUploadedFile("yo.jpg", salida.getvalue(), content_type="image/jpeg")

    def test_subir_foto_la_recorta_y_quita_exif(self):
        from PIL import Image
        from .models import Perfil
        r = self.client.post(reverse("cuentas:avatar"), {"eleccion": "foto", "foto": self.foto()})
        self.assertEqual(r.status_code, 302)
        perfil = Perfil.objects.get(usuario=self.usuario)
        with Image.open(perfil.avatar_foto.path) as img:
            self.assertEqual(img.size, (256, 256))
            self.assertEqual(len(img.getexif()), 0)
        self.assertNotIn("yo", perfil.avatar_foto.name)

    def test_elegir_predisenado_borra_la_foto(self):
        import os
        from .models import Perfil
        self.client.post(reverse("cuentas:avatar"), {"eleccion": "foto", "foto": self.foto()})
        ruta = Perfil.objects.get(usuario=self.usuario).avatar_foto.path
        self.client.post(reverse("cuentas:avatar"), {"eleccion": "casco-lava"})
        perfil = Perfil.objects.get(usuario=self.usuario)
        self.assertEqual(perfil.avatar_predisenado, "casco-lava")
        self.assertFalse(perfil.avatar_foto)
        self.assertFalse(os.path.exists(ruta))
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), 'aria-label="Casco lava"')

    def test_rechaza_eleccion_inventada_y_archivos_que_no_son_imagen(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Perfil
        self.client.post(reverse("cuentas:avatar"), {"eleccion": "<script>"})
        self.client.post(reverse("cuentas:avatar"), {"eleccion": "foto", "foto": SimpleUploadedFile("x.jpg", b"no soy imagen")})
        perfil = Perfil.de(self.usuario)
        self.assertEqual(perfil.avatar_predisenado, "")
        self.assertFalse(perfil.avatar_foto)

    def test_guardar_sin_recargar_devuelve_el_avatar_nuevo(self):
        r = self.client.post(reverse("cuentas:avatar"), {"eleccion": "rueda"}, HTTP_X_REQUESTED_WITH="fetch")
        datos = r.json()
        self.assertTrue(datos["ok"])
        self.assertIn('aria-label="Rueda"', datos["grande"])
        self.assertIsNone(datos["foto"])
        r = self.client.post(reverse("cuentas:avatar"), {"eleccion": "inventado"}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 400)


class GoogleTests(TestCase):
    def setUp(self):
        from unittest import mock
        from django.test import override_settings
        self.ajuste = override_settings(GOOGLE_CLIENT_ID="cliente-prueba", GOOGLE_CLIENT_SECRET="secreto-prueba")
        self.ajuste.enable()
        self.datos = {"sub": "1234567890", "email": "Nuevo@Gmail.com", "email_verified": True, "given_name": "Nico"}
        def falso(url, datos=None, token=None):
            return {"access_token": "token"} if datos else self.datos
        self.parche = mock.patch("cuentas.google._pedir", side_effect=falso)
        self.parche.start()

    def tearDown(self):
        self.parche.stop()
        self.ajuste.disable()

    def ida_y_vuelta(self, **extra):
        from urllib.parse import parse_qs, urlparse
        r = self.client.get(reverse("cuentas:google"))
        params = parse_qs(urlparse(r["Location"]).query)
        self.assertEqual(params["code_challenge_method"], ["S256"])
        state = extra.pop("state", params["state"][0])
        return self.client.get(reverse("cuentas:google_volver"), {"state": state, "code": "codigo", **extra})

    def test_cuenta_nueva_y_completar_como_motero(self):
        from .models import Perfil
        r = self.ida_y_vuelta()
        self.assertRedirects(r, reverse("cuentas:completar"))
        usuario = User.objects.get(username="nuevo@gmail.com")
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual(Perfil.objects.get(usuario=usuario).google_sub, "1234567890")
        r = self.client.post(reverse("cuentas:completar") + "?tipo=motero", {"celular": "300 777 8888"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(usuario.motociclista.celular, "573007778888")

    def test_vincula_cuenta_existente_por_correo(self):
        existente = User.objects.create_user("nuevo@gmail.com", "nuevo@gmail.com", "clave-vieja")
        Motociclista.objects.create(nombre="Nico", celular="573007779999", usuario=existente)
        r = self.ida_y_vuelta()
        self.assertRedirects(r, reverse("talleres:inicio"), fetch_redirect_response=False)
        self.assertEqual(User.objects.filter(username="nuevo@gmail.com").count(), 1)
        self.assertEqual(int(self.client.session["_auth_user_id"]), existente.pk)

    def test_state_falso_no_inicia_sesion(self):
        r = self.ida_y_vuelta(state="inventado")
        self.assertRedirects(r, reverse("cuentas:entrar"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_correo_sin_verificar_no_entra(self):
        self.datos["email_verified"] = False
        self.ida_y_vuelta()
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(User.objects.filter(username="nuevo@gmail.com").exists())

    def test_sin_credenciales_el_boton_avisa_que_llega_pronto(self):
        # Sin credenciales el botón se ve, pero no lleva a Google: avisa que llega pronto.
        from django.test import override_settings
        url_google = reverse("cuentas:google")
        with override_settings(GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET=""):
            r = self.client.get(reverse("cuentas:entrar"))
            self.assertContains(r, "Continuar con Google")
            self.assertContains(r, "data-google-pronto")
            self.assertNotContains(r, f'href="{url_google}')
        r = self.client.get(reverse("cuentas:entrar"))
        self.assertContains(r, f'href="{url_google}')


class ActividadConTalleresTests(TestCase):
    def test_agrupa_por_taller_y_deja_fuera_lo_hecho_por_uno_mismo(self):
        from datetime import date
        from cuentas.views import actividad_con_talleres
        eventos = [
            {"fecha": date(2026, 1, 5), "tipo": "mantenimiento", "titulo": "Aceite", "lugar": "", "taller": None},
            {"fecha": date(2026, 2, 1), "tipo": "mantenimiento", "titulo": "Frenos", "lugar": "Motos El Paisa", "taller": None},
            {"fecha": date(2026, 3, 1), "tipo": "cupon", "titulo": "15%", "lugar": "motos el paisa", "taller": None},
        ]
        a = actividad_con_talleres(eventos)
        self.assertEqual(a["resumen"], {"talleres": 1, "mantenimientos": 1, "cupones": 1, "citas": 0})
        self.assertEqual(a["talleres"][0]["visitas"], 2)
        self.assertEqual(a["talleres"][0]["ultimo"]["titulo"], "15%")


class CalificarTallerTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("cal@x.com", "cal@x.com", "x", first_name="Cami")
        self.client.force_login(self.usuario)
        barrio = Barrio.objects.create(nombre="Centro")
        self.taller = Taller.objects.create(nombre="Taller C", responsable="Ana", whatsapp="573001234567",
                                            direccion="Calle 1", barrio=barrio, activo=True)

    def test_califica_y_luego_actualiza_sin_duplicar(self):
        from talleres.models import Resena
        url = reverse("cuentas:calificar_taller", args=[self.taller.pk])
        self.client.post(url, {"estrellas": "4", "comentario": "Bien"})
        self.client.post(url, {"estrellas": "5", "comentario": ""})
        r = Resena.objects.get(taller=self.taller, usuario=self.usuario)
        self.assertEqual((r.estrellas, r.nombre), (5, "Cami"))
        self.assertEqual(Resena.objects.count(), 1)

    def test_rechaza_estrellas_fuera_de_rango(self):
        from talleres.models import Resena
        self.client.post(reverse("cuentas:calificar_taller", args=[self.taller.pk]), {"estrellas": "9"})
        self.assertFalse(Resena.objects.exists())
