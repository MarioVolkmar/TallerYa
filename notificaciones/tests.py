from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from garaje.models import LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from talleres.models import Barrio, SolicitudCita, Taller

from .models import Notificacion
from .servicios import generar_para, notificar

User = get_user_model()


class NotificacionesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("n@x.com", "n@x.com", "x", first_name="Nora")
        self.perfil = Motociclista.objects.create(nombre="Nora", celular="573008880000", usuario=self.usuario)
        # 3.000 km desde nueva: el aceite (cada 2.500) ya toca.
        self.moto = Moto.objects.create(motociclista=self.perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                        modelo=2024, km_inicial=0, km_actual=3000,
                                        soat_vence=timezone.localdate() + timedelta(days=5))
        self.client.force_login(self.usuario)

    def test_no_repite_el_mismo_aviso(self):
        self.assertIsNotNone(notificar(self.usuario, "x:1", "Hola"))
        self.assertIsNone(notificar(self.usuario, "x:1", "Hola otra vez"))
        self.assertEqual(Notificacion.objects.filter(usuario=self.usuario).count(), 1)

    def test_genera_avisos_de_mantenimiento_y_documentos_agrupados(self):
        generar_para(self.usuario)
        generar_para(self.usuario)  # la segunda vez no duplica
        titulos = list(Notificacion.objects.filter(usuario=self.usuario).values_list("titulo", flat=True))
        self.assertTrue(any(t.startswith("Toca ya:") and "NMAX" in t for t in titulos))
        self.assertIn("Tu SOAT vence en 5 días", titulos)
        self.assertEqual(len(titulos), len(set(titulos)))
        # Registrar el aceite cambia la lista: vuelve a avisar con la lista nueva.
        antes = Notificacion.objects.count()
        Mantenimiento.objects.create(moto=self.moto, tarea=TareaMantenimiento.objects.get(clave="aceite"), km=3000)
        generar_para(self.usuario)
        self.assertGreaterEqual(Notificacion.objects.count(), antes)

    def test_campanita_y_panel(self):
        notificar(self.usuario, "x:2", "Prueba de aviso", "Detalle", "/garaje/")
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, 'id="campana"')
        datos = self.client.get(reverse("notificaciones:panel")).json()
        self.assertGreaterEqual(datos["sin_leer"], 1)
        self.assertIn("Prueba de aviso", [n["titulo"] for n in datos["notificaciones"]])

    def test_abrir_marca_leida_y_no_redirige_afuera(self):
        n = notificar(self.usuario, "x:3", "Externa", url="//malo.example/")
        r = self.client.get(reverse("notificaciones:ir", args=[n.pk]))
        self.assertRedirects(r, reverse("notificaciones:lista"))
        n.refresh_from_db()
        self.assertTrue(n.leida)
        otro = User.objects.create_user("o@x.com", "o@x.com", "x")
        ajena = notificar(otro, "x:4", "Ajena")
        self.assertEqual(self.client.get(reverse("notificaciones:ir", args=[ajena.pk])).status_code, 404)

    def test_marcar_todas(self):
        notificar(self.usuario, "x:5", "Uno")
        notificar(self.usuario, "x:6", "Dos")
        self.client.post(reverse("notificaciones:marcar_todas"), HTTP_X_REQUESTED_WITH="fetch")
        self.assertFalse(Notificacion.objects.filter(usuario=self.usuario, leida=False).exists())

    def test_respuesta_en_el_foro_avisa_al_autor(self):
        from foro.models import Pregunta
        pregunta = Pregunta.objects.create(autor=self.usuario, titulo="¿Cada cuánto cambio el aceite?", cuerpo="Tengo una duda sobre el aceite.")
        otro = User.objects.create_user("r@x.com", "r@x.com", "x", first_name="Rafa")
        self.client.force_login(otro)
        self.client.post(pregunta.get_absolute_url(), {"cuerpo": "Cada 2.500 km más o menos, según el manual."})
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, tipo="foro", titulo__startswith="Rafa").exists())


class HistorialServiciosTests(TestCase):
    def test_junta_mantenimientos_y_citas_del_celular(self):
        from cuentas.views import historial_servicios
        usuario = User.objects.create_user("h@x.com", "h@x.com", "x")
        perfil = Motociclista.objects.create(nombre="H", celular="573009990000", usuario=usuario)
        moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NMAX 155"),
                                   modelo=2024, km_inicial=0, km_actual=3000)
        barrio = Barrio.objects.first() or Barrio.objects.create(nombre="Belén")
        taller = Taller.objects.create(nombre="Taller H", responsable="X", whatsapp="573001110000", direccion="Cra 1",
                                       barrio=barrio, activo=True)
        Mantenimiento.objects.create(moto=moto, tarea=TareaMantenimiento.objects.get(clave="aceite"), km=2500,
                                     taller=taller)
        SolicitudCita.objects.create(taller=taller, nombre="H", telefono="300 999 0000", moto="NMAX",
                                     fecha_preferida=timezone.localdate())
        SolicitudCita.objects.create(taller=taller, nombre="Otro", telefono="311 222 3333", moto="NMAX",
                                     fecha_preferida=timezone.localdate())
        tipos = sorted(e["tipo"] for e in historial_servicios(perfil))
        self.assertEqual(tipos, ["cita", "mantenimiento"])  # la cita de otro celular no aparece
