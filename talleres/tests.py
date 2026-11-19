from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Barrio, Resena, Servicio, SolicitudCita, Taller


class TalleresTests(TestCase):
    def setUp(self):
        self.barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
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
        # El filtro vive en el directorio de talleres (el inicio solo muestra destacados)
        otro = Servicio.objects.get_or_create(nombre="Llantas")[0]
        r = self.client.get(reverse("talleres:directorio"), {"servicio": otro.id})
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
            "email": "Luis@Taller.com", "password1": "ClaveSegura-2026", "password2": "ClaveSegura-2026", "acepto": "on",
            "nombre": "Nuevo Taller", "responsable": "Luis", "whatsapp": "300 123 4567",
            "direccion": "Cll 2", "ciudad": "Medellín", "barrio": self.barrio.id, "servicios": [self.servicio.id],
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
        barrio = Barrio.objects.get_or_create(nombre="Centro", ciudad="Medellín")[0]
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
        self.assertContains(pagina, "perfil-franja-foto")  # franja de fotos de una fila
        self.assertContains(pagina, "Editar mi perfil")

    def test_otro_usuario_no_puede_borrar_fotos(self):
        from django.contrib.auth import get_user_model
        from .models import FotoTaller
        foto = FotoTaller.objects.create(taller=self.taller, imagen=self._imagen())
        otro = get_user_model().objects.create_user("o@x.com", "o@x.com", "x")
        self.client.force_login(otro)
        self.assertEqual(self.client.post(reverse("talleres:eliminar_foto", args=[foto.pk])).status_code, 404)
        self.assertTrue(FotoTaller.objects.filter(pk=foto.pk).exists())


class DirectorioTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        barrio = Barrio.objects.get_or_create(nombre="Laureles")[0]
        s = Servicio.objects.get_or_create(nombre="Frenos")[0]
        for i in range(10):
            t = Taller.objects.create(nombre=f"Taller {i:02d}", responsable="A", whatsapp="573000000000", direccion="X",
                                      barrio=barrio, activo=True, nivel_precio=(3 - i % 3))
            t.servicios.add(s)
        self.usuario = get_user_model().objects.create_user("m@x.com", "m@x.com", "x")

    def test_paginacion_y_orden_por_precio(self):
        r = self.client.get(reverse("talleres:directorio"), {"orden": "nombre"})
        self.assertEqual(len(r.context["pagina"].object_list), 8)
        r = self.client.get(reverse("talleres:directorio"), {"orden": "nombre", "pagina": 2})
        self.assertContains(r, "Taller 09")
        r = self.client.get(reverse("talleres:directorio"), {"orden": "precio"})
        self.assertEqual(r.context["pagina"].object_list[0].nivel_precio, 1)

    def test_favoritos(self):
        t = Taller.objects.get(nombre="Taller 03")
        url = reverse("talleres:favorito", args=[t.slug])
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").status_code, 401)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json(), {"favorito": True})
        r = self.client.get(reverse("talleres:directorio"), {"favoritos": 1})
        self.assertEqual([x.nombre for x in r.context["pagina"].object_list], ["Taller 03"])
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json(), {"favorito": False})


class CiudadYBarrioTests(TestCase):
    def test_barrio_debe_ser_de_la_ciudad_elegida(self):
        from .forms import RegistroTallerForm
        zuniga = Barrio.objects.get(nombre="Zúñiga", ciudad="Envigado")
        datos = {"nombre": "T", "responsable": "R", "whatsapp": "3001234567", "direccion": "Cra 1", "barrio": zuniga.pk,
                 "servicios": [Servicio.objects.get_or_create(nombre="Frenos")[0].pk]}
        self.assertIn("barrio", RegistroTallerForm({**datos, "ciudad": "Medellín"}).errors)
        self.assertTrue(RegistroTallerForm({**datos, "ciudad": "Envigado"}).is_valid())
        self.assertEqual(str(zuniga), "Zúñiga · Envigado")
        self.assertIn([zuniga.pk, "Zúñiga"], RegistroTallerForm.barrios_por_ciudad()["Envigado"])


class PanelTallerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        cls.duenio = User.objects.create_user("t@panel.co", "t@panel.co", "x")
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.taller = Taller.objects.create(nombre="Taller Panel", responsable="A", whatsapp="573001112233", direccion="X",
                                           barrio=barrio, activo=True, usuario=cls.duenio)
        cls.otro = Taller.objects.create(nombre="Otro", responsable="B", whatsapp="573001112244", direccion="X", barrio=barrio, activo=True)
        cls.cita = SolicitudCita.objects.create(taller=cls.taller, nombre="Camilo", telefono="300 555 1234", moto="NMAX",
                                                fecha_preferida=date.today() + timedelta(days=2))

    def setUp(self):
        self.client.force_login(self.duenio)

    def test_panel_muestra_citas_y_mi_cuenta_redirige(self):
        r = self.client.get(reverse("talleres:panel"))
        self.assertContains(r, "Camilo")
        self.assertContains(r, "https://wa.me/573005551234")
        self.assertRedirects(self.client.get(reverse("cuentas:mi_cuenta")), reverse("talleres:panel"))
        self.assertContains(r, 'id="seguridad"')  # la cuenta (correo, contraseña, Google) vive en el panel

    def test_cambiar_estado_solo_de_mis_citas(self):
        self.client.post(reverse("talleres:cita_estado", args=[self.cita.pk]), {"estado": "confirmada"})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "confirmada")
        ajena = SolicitudCita.objects.create(taller=self.otro, nombre="X", telefono="3000000000", moto="X", fecha_preferida=date.today())
        self.assertEqual(self.client.post(reverse("talleres:cita_estado", args=[ajena.pk]), {"estado": "cancelada"}).status_code, 404)

    def test_responder_resena_se_ve_en_la_pagina(self):
        resena = Resena.objects.create(taller=self.taller, nombre="Laura", estrellas=5, comentario="Muy bien")
        self.client.post(reverse("talleres:responder_resena", args=[resena.pk]), {"respuesta": "¡Gracias Laura!"})
        self.assertContains(self.client.get(self.taller.get_absolute_url()), "¡Gracias Laura!")

    def test_sin_taller_no_entra_al_panel(self):
        from django.contrib.auth import get_user_model
        self.client.force_login(get_user_model().objects.create_user("m@x.co", "m@x.co", "x"))
        self.assertEqual(self.client.get(reverse("talleres:panel")).status_code, 302)


class CuponesDelTallerTests(PanelTallerTests):
    def test_crea_edita_y_pausa_su_cupon(self):
        from cupones.models import Cupon
        r = self.client.post(reverse("talleres:cupon_nuevo"), {"titulo": "20% en frenos", "condiciones": "Lun a vie"})
        self.assertRedirects(r, reverse("talleres:panel") + "#cupones", fetch_redirect_response=False)
        cupon = Cupon.objects.get(titulo="20% en frenos")
        self.assertEqual((cupon.taller, cupon.publico, cupon.solo_plus), (self.taller, True, False))
        self.client.post(reverse("talleres:cupon_pausar", args=[cupon.pk]))
        cupon.refresh_from_db()
        self.assertFalse(cupon.activo)
        ajeno = Cupon.objects.create(taller=self.otro, titulo="Ajeno")
        self.assertEqual(self.client.get(reverse("talleres:cupon_editar", args=[ajeno.pk])).status_code, 404)


class InicioTallerTests(PanelTallerTests):
    def test_el_taller_ve_su_inicio_sin_la_lista_de_talleres(self):
        r = self.client.get(reverse("talleres:inicio"))
        self.assertTemplateUsed(r, "talleres/inicio_taller.html")
        self.assertContains(r, "Validar cupón")
        self.assertContains(r, "Camilo")
        self.assertNotContains(r, "Talleres destacados")
        self.assertNotContains(r, "Noticias moteras")


class ReprogramarCitaTests(PanelTallerTests):
    def test_reprogramar_y_el_motero_acepta(self):
        nueva = date.today() + timedelta(days=5)
        self.client.post(reverse("talleres:cita_reprogramar", args=[self.cita.pk]), {"fecha": nueva.isoformat(), "hora": "09:30", "nota": "Llega el repuesto"})
        self.cita.refresh_from_db()
        self.assertEqual((self.cita.estado, self.cita.fecha_propuesta), ("reprogramada", nueva))
        enlace = reverse("talleres:cita_publica", args=[self.cita.token])
        self.assertContains(self.client.get(reverse("talleres:panel")), enlace.replace("/", "%2F")[:10] if False else "Propusiste")
        self.client.logout()
        self.assertContains(self.client.get(enlace), "Aceptar nueva fecha")
        self.client.post(enlace, {"accion": "aceptar"})
        self.cita.refresh_from_db()
        self.assertEqual((self.cita.estado, self.cita.fecha_preferida, str(self.cita.hora)), ("confirmada", nueva, "09:30:00"))

    def test_el_motero_rechaza(self):
        self.client.post(reverse("talleres:cita_reprogramar", args=[self.cita.pk]), {"fecha": (date.today() + timedelta(days=3)).isoformat(), "hora": "10:00"})
        self.cita.refresh_from_db()
        self.client.post(reverse("talleres:cita_publica", args=[self.cita.token]), {"accion": "rechazar"})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "pendiente")
        self.assertTrue(self.cita.propuesta_rechazada)

    def test_no_reprograma_citas_ajenas_ni_fechas_pasadas(self):
        ajena = SolicitudCita.objects.create(taller=self.otro, nombre="X", telefono="3000000000", moto="X", fecha_preferida=date.today())
        r = self.client.post(reverse("talleres:cita_reprogramar", args=[ajena.pk]), {"fecha": date.today().isoformat()})
        self.assertEqual(r.status_code, 404)
        self.client.post(reverse("talleres:cita_reprogramar", args=[self.cita.pk]), {"fecha": (date.today() - timedelta(days=1)).isoformat()})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "pendiente")


class ListasLargasTests(PanelTallerTests):
    def test_panel_recorta_y_las_paginas_completas_paginan(self):
        for i in range(20):
            SolicitudCita.objects.create(taller=self.taller, nombre=f"Motero {i}", telefono="3000000000", moto="NKD",
                                         fecha_preferida=date.today() + timedelta(days=i + 1))
            Resena.objects.create(taller=self.taller, nombre=f"R{i}", estrellas=5 - i % 3, comentario="ok")
        r = self.client.get(reverse("talleres:panel"))
        self.assertEqual(len(r.context["citas"]), 6)
        self.assertContains(r, "Ver las 21 citas por atender")
        self.assertContains(r, "Ver las 20 reseñas")
        r = self.client.get(reverse("talleres:citas_taller"))
        self.assertEqual(len(r.context["pagina"].object_list), 15)
        r = self.client.get(reverse("talleres:citas_taller"), {"q": "Motero 7"})
        self.assertEqual([c.nombre for c in r.context["pagina"]], ["Motero 7"])
        r = self.client.get(reverse("talleres:resenas_taller"), {"estrellas": "5"})
        self.assertTrue(all(x.estrellas == 5 for x in r.context["pagina"]))


class CancelarYAvisosTests(PanelTallerTests):
    def test_reprogramar_sin_hora_no_se_guarda(self):
        self.client.post(reverse("talleres:cita_reprogramar", args=[self.cita.pk]), {"fecha": (date.today() + timedelta(days=2)).isoformat()})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "pendiente")

    def test_cancelar_guarda_motivo_y_avisa_al_motero_con_cuenta(self):
        from django.contrib.auth import get_user_model
        from cupones.models import Motociclista
        from notificaciones.models import Notificacion
        usuario = get_user_model().objects.create_user("cam@x.co", "cam@x.co", "x")
        Motociclista.objects.create(nombre="Camilo", celular="573005551234", usuario=usuario)
        self.client.post(reverse("talleres:cita_estado", args=[self.cita.pk]), {"estado": "cancelada", "motivo": "No llegó el repuesto"})
        self.cita.refresh_from_db()
        self.assertEqual((self.cita.estado, self.cita.motivo_cancelacion), ("cancelada", "No llegó el repuesto"))
        self.assertTrue(Notificacion.objects.filter(usuario=usuario, clave=f"cita-cancelada:{self.cita.pk}").exists())


class CuponPlusTests(PanelTallerTests):
    def test_el_taller_puede_crear_un_cupon_solo_plus(self):
        from cupones.models import Cupon
        self.client.post(reverse("talleres:cupon_nuevo"), {"titulo": "30% exclusivo", "solo_plus": "on"})
        self.assertTrue(Cupon.objects.get(titulo="30% exclusivo").solo_plus)



NAVEGADOR = {"HTTP_USER_AGENT": "Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile"}


class EstadisticasTallerTests(PanelTallerTests):
    """Punto 6: eventos agregados por día, sin bots ni visitas propias, y resumen contra el mes anterior."""

    def _cantidad(self, tipo):
        from .models import EventoDiario
        return sum(EventoDiario.objects.filter(taller=self.taller, tipo=tipo).values_list("cantidad", flat=True))

    def test_visitas_se_agregan_por_dia_sin_bots_ni_el_propio_taller(self):
        from .models import EventoDiario
        self.client.logout()
        for _ in range(3):
            self.client.get(self.taller.get_absolute_url(), **NAVEGADOR)
        self.client.get(self.taller.get_absolute_url(), HTTP_USER_AGENT="Googlebot/2.1")
        self.client.get(self.taller.get_absolute_url())  # sin navegador: no cuenta
        self.client.force_login(self.duenio)
        self.client.get(self.taller.get_absolute_url(), **NAVEGADOR)  # el propio taller
        self.assertEqual(self._cantidad("visita"), 3)
        self.assertEqual(EventoDiario.objects.filter(taller=self.taller).count(), 1)  # una fila por día y tipo

    def test_clics_a_whatsapp_y_llamar_redirigen_y_cuentan(self):
        self.client.logout()
        r = self.client.get(reverse("talleres:ir_whatsapp", args=[self.taller.slug]), **NAVEGADOR)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("https://wa.me/573001112233"))
        r = self.client.get(reverse("talleres:ir_llamar", args=[self.taller.slug]), **NAVEGADOR)
        self.assertEqual(r["Location"], "tel:+573001112233")
        self.assertEqual((self._cantidad("whatsapp"), self._cantidad("llamada")), (1, 1))
        self.assertContains(self.client.get(self.taller.get_absolute_url()), reverse("talleres:ir_llamar", args=[self.taller.slug]))

    def test_resumen_compara_con_el_mismo_tramo_del_mes_anterior(self):
        from django.utils import timezone
        from . import estadisticas
        from .models import EventoDiario
        hoy = timezone.localdate()
        (ini, _), (ini_a, fin_a) = estadisticas._periodos(hoy)
        EventoDiario.objects.create(taller=self.taller, fecha=hoy, tipo="visita", cantidad=6)
        EventoDiario.objects.create(taller=self.taller, fecha=ini_a, tipo="visita", cantidad=4)
        EventoDiario.objects.create(taller=self.taller, fecha=ini_a, tipo="whatsapp", cantidad=2)
        Resena.objects.create(taller=self.taller, nombre="L", estrellas=4, comentario="ok")
        datos = {c["clave"]: c for c in estadisticas.resumen(self.taller, hoy)["cifras"]}
        self.assertEqual((datos["visita"]["actual"], datos["visita"]["anterior"], datos["visita"]["variacion"]), (6, 4, 50))
        self.assertEqual(datos["whatsapp"]["variacion"], -100)
        self.assertEqual((datos["resenas"]["actual"], datos["nota"]["actual"]), (1, 4))
        self.assertLessEqual(fin_a - ini_a, hoy - ini)

    def test_pagina_de_estadisticas_con_pocas_consultas(self):
        url = reverse("talleres:estadisticas")
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as consultas:
            r = self.client.get(url)
        propias = [q for q in consultas.captured_queries if "eventodiario" in q["sql"] or "codigocupon" in q["sql"] or "talleres_resena" in q["sql"]]
        self.assertEqual(len(propias), 3)  # eventos, canjes y reseñas: una consulta cada uno
        self.assertLessEqual(len(consultas), 10)
        self.assertContains(r, "Visitas al perfil")
        self.assertContains(r, "Plus taller")
        self.assertContains(self.client.get(reverse("talleres:panel")), url)


class AgendaFranjasTests(PanelTallerTests):
    """Punto 7: horario del taller, franjas libres, reservas sin dobles y recordatorio idempotente."""

    def setUp(self):
        super().setUp()
        from datetime import time
        from .models import HorarioTaller
        self.dia = date.today() + timedelta(days=3)
        self.taller.agenda_activa, self.taller.duracion_franja, self.taller.cupo_franja = True, 60, 1
        self.taller.save()
        HorarioTaller.objects.create(taller=self.taller, dia=self.dia.weekday(), abre=time(8), cierra=time(11))
        self.servicio = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        self.taller.servicios.add(self.servicio)

    def _reservar(self, hora="09:00", **extra):
        datos = {"accion": "cita", "nombre": "Ana", "telefono": "3005550000", "moto": "NMAX", "servicio": self.servicio.pk,
                 "fecha_preferida": self.dia.isoformat(), "hora": hora, "detalle": ""}
        datos.update(extra)
        return self.client.post(self.taller.get_absolute_url(), datos)

    def test_franjas_libres_por_horario_y_cupo(self):
        r = self.client.get(reverse("talleres:franjas", args=[self.taller.slug]), {"fecha": self.dia.isoformat()})
        self.assertEqual([f["hora"] for f in r.json()["franjas"]], ["08:00", "09:00", "10:00"])
        self._reservar("09:00")
        r = self.client.get(reverse("talleres:franjas", args=[self.taller.slug]), {"fecha": self.dia.isoformat()})
        self.assertEqual([f["hora"] for f in r.json()["franjas"]], ["08:00", "10:00"])

    def test_no_hay_reserva_doble(self):
        self.client.logout()
        self.assertEqual(self._reservar("09:00").status_code, 302)
        r = self._reservar("09:00", nombre="Beto")
        self.assertEqual(r.status_code, 200)  # vuelve el formulario con el error
        self.assertEqual(SolicitudCita.objects.filter(taller=self.taller, fecha_preferida=self.dia).count(), 1)
        # Con cupo 2 sí cabe otra moto; una hora fuera del horario no se acepta
        self.taller.cupo_franja = 2
        self.taller.save()
        self.assertEqual(self._reservar("09:00", nombre="Beto").status_code, 302)
        self.assertEqual(self._reservar("12:00", nombre="Caro").status_code, 200)
        # Una cita cancelada libera la franja
        SolicitudCita.objects.filter(nombre="Ana").update(estado="cancelada")
        self.assertEqual(self._reservar("09:00", nombre="Dani").status_code, 302)

    def test_reservar_bloquea_y_revisa_el_cupo(self):
        from datetime import time
        from . import agenda
        cita = SolicitudCita(taller=self.taller, nombre="X", telefono="3000000000", moto="X", fecha_preferida=self.dia, hora=time(8))
        agenda.reservar(cita)
        otra = SolicitudCita(taller=self.taller, nombre="Y", telefono="3000000001", moto="Y", fecha_preferida=self.dia, hora=time(8))
        with self.assertRaises(agenda.FranjaOcupada):
            agenda.reservar(otra)

    def test_taller_guarda_su_horario(self):
        r = self.client.post(reverse("talleres:agenda"), {
            "agenda_activa": "on", "duracion_franja": 30, "cupo_franja": 2,
            "d0_1_abre": "08:00", "d0_1_cierra": "12:00", "d0_2_abre": "14:00", "d0_2_cierra": "18:00",
            "d5_1_abre": "09:00", "d5_1_cierra": "13:00"})
        self.assertRedirects(r, reverse("talleres:agenda"))
        self.assertEqual(self.taller.horarios.count(), 3)
        self.taller.refresh_from_db()
        self.assertEqual((self.taller.duracion_franja, self.taller.cupo_franja), (30, 2))
        r = self.client.post(reverse("talleres:agenda"), {"duracion_franja": 60, "cupo_franja": 1,
                                                         "d1_1_abre": "10:00", "d1_1_cierra": "09:00"})
        self.assertContains(r, "después de la de apertura")
        self.assertEqual(self.taller.horarios.count(), 3)

    def test_recordatorio_del_dia_antes_es_idempotente(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from notificaciones.models import Notificacion
        motero = get_user_model().objects.create_user("m@cita.co", "m@cita.co", "x")
        manana = date.today() + timedelta(days=1)
        SolicitudCita.objects.create(taller=self.taller, nombre="Ana", telefono="3005550000", moto="NMAX",
                                     fecha_preferida=manana, estado="confirmada", usuario=motero)
        SolicitudCita.objects.create(taller=self.taller, nombre="Cancelada", telefono="3005550001", moto="X",
                                     fecha_preferida=manana, estado="cancelada", usuario=motero)
        call_command("recordar_citas", stdout=__import__("io").StringIO())
        call_command("recordar_citas", stdout=__import__("io").StringIO())
        self.assertEqual(Notificacion.objects.filter(usuario=motero, clave__startswith="cita-recordatorio").count(), 1)
        self.assertEqual(Notificacion.objects.filter(usuario=self.duenio, clave__startswith="agenda-manana").count(), 1)

    def test_cita_de_usuario_conectado_guarda_su_cuenta(self):
        from django.contrib.auth import get_user_model
        motero = get_user_model().objects.create_user("c@cita.co", "c@cita.co", "x")
        self.client.force_login(motero)
        self._reservar("10:00")
        self.assertEqual(SolicitudCita.objects.get(nombre="Ana").usuario, motero)


class PreciosReferenciaTests(TestCase):
    """Punto 8: rangos por servicio y mediana de Medellín solo con 3 o más talleres."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        self.servicio = Servicio.objects.get_or_create(nombre="Cambio de aceite")[0]
        med = Barrio.objects.get_or_create(nombre="Laureles", ciudad="Medellín")[0]
        self.bello = Barrio.objects.get_or_create(nombre="Niquía", ciudad="Bello")[0]
        self.usuario = get_user_model().objects.create_user("p@t.co", "p@t.co", "x")
        self.talleres = [Taller.objects.create(nombre=f"T{i}", responsable="A", whatsapp=f"57300111220{i}", direccion="X",
                                               barrio=med, activo=True, usuario=self.usuario if i == 0 else None) for i in range(4)]
        for t in self.talleres:
            t.servicios.add(self.servicio)

    def _publicar(self, taller, desde, hasta, cilindraje=""):
        from .models import PrecioServicio
        return PrecioServicio.objects.create(taller=taller, servicio=self.servicio, cilindraje=cilindraje, desde=desde, hasta=hasta)

    def test_mediana_solo_con_tres_talleres_de_medellin(self):
        from .precios import medianas_medellin
        url = reverse("talleres:directorio") + f"?servicio={self.servicio.pk}"
        self._publicar(self.talleres[0], 50_000, 90_000)
        self._publicar(self.talleres[1], 60_000, 100_000)
        otro = Taller.objects.create(nombre="Bello", responsable="A", whatsapp="573001112299", direccion="X", barrio=self.bello, activo=True)
        self._publicar(otro, 10_000, 20_000)  # no es de Medellín: no cuenta
        self.assertEqual(medianas_medellin(self.servicio.pk), [])
        self.assertNotContains(self.client.get(url), "data-mediana")
        self._publicar(self.talleres[2], 80_000, 150_000)
        self._publicar(self.talleres[3], 70_000, 120_000, cilindraje="media")  # otro cilindraje: grupo aparte
        datos = medianas_medellin(self.servicio.pk)
        self.assertEqual([(d["desde"], d["hasta"], d["talleres"]) for d in datos], [(60_000, 100_000, 3)])
        r = self.client.get(url)
        self.assertContains(r, "$60.000 a $100.000")
        self.assertContains(r, "referencia, no oferta")

    def test_taller_publica_sus_rangos_y_se_ven_en_su_perfil(self):
        self.client.force_login(self.usuario)
        datos = {"precios-TOTAL_FORMS": 3, "precios-INITIAL_FORMS": 0, "precios-MIN_NUM_FORMS": 0, "precios-MAX_NUM_FORMS": 60,
                 "precios-0-servicio": self.servicio.pk, "precios-0-cilindraje": "baja", "precios-0-desde": 50000, "precios-0-hasta": 90000}
        self.assertRedirects(self.client.post(reverse("talleres:precios"), datos), reverse("talleres:precios"))
        self.assertContains(self.client.get(self.talleres[0].get_absolute_url()), "$50.000")  # el perfil muestra el «desde»
        # "hasta" menor que "desde" no se acepta
        datos.update({"precios-0-servicio": self.servicio.pk, "precios-0-cilindraje": "media", "precios-0-desde": 90000, "precios-0-hasta": 1000})
        self.assertContains(self.client.post(reverse("talleres:precios"), datos), "mayor o igual")
        self.assertEqual(self.talleres[0].precios.count(), 1)


class EmergenciasTests(TestCase):
    """Punto 5: /emergencias con abiertos ahora (horario o 24 h), orden por barrio y botones de contacto."""

    def setUp(self):
        from datetime import time
        from .models import HorarioTaller
        self.belen = Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]
        self.robledo = Barrio.objects.get_or_create(nombre="Robledo", ciudad="Medellín")[0]
        crear = lambda nombre, barrio, **k: Taller.objects.create(nombre=nombre, responsable="A", whatsapp="573001112233",
                                                                  direccion="X", barrio=barrio, activo=True, **k)
        self.veinticuatro = crear("Siempre Abierto", self.robledo, atiende_emergencias=True, abierto_24h=True, grua=True)
        self.con_horario = crear("Con Horario", self.belen, atiende_emergencias=True)
        self.sin_horario = crear("Sin Horario", self.belen, atiende_emergencias=True)
        crear("No Atiende", self.belen)
        for dia in range(7):
            HorarioTaller.objects.create(taller=self.con_horario, dia=dia, abre=time(0, 0), cierra=time(23, 59))

    def test_abierto_ahora_por_horario_o_24h(self):
        from datetime import datetime, time
        from .emergencias import abierto_ahora
        from .models import HorarioTaller
        lunes_10 = datetime(2026, 11, 16, 10, 0)
        HorarioTaller.objects.filter(taller=self.con_horario).delete()
        HorarioTaller.objects.create(taller=self.con_horario, dia=0, abre=time(8), cierra=time(12))
        self.assertTrue(abierto_ahora(self.con_horario, lunes_10))
        self.assertFalse(abierto_ahora(self.con_horario, lunes_10.replace(hour=12)))
        self.assertFalse(abierto_ahora(self.con_horario, datetime(2026, 11, 17, 10, 0)))  # martes
        self.assertIsNone(abierto_ahora(self.sin_horario, lunes_10))
        self.assertTrue(abierto_ahora(self.veinticuatro, lunes_10))

    def test_pagina_lista_y_ordena_por_barrio(self):
        r = self.client.get(reverse("talleres:emergencias"))
        self.assertEqual([t.nombre for t in r.context["abiertos"]], ["Siempre Abierto", "Con Horario"])
        self.assertEqual([t.nombre for t in r.context["sin_horario"]], ["Sin Horario"])
        self.assertNotContains(r, "No Atiende")
        self.assertContains(r, reverse("talleres:ir_llamar", args=[self.veinticuatro.slug]))
        self.assertContains(r, "Grúa")
        r = self.client.get(reverse("talleres:emergencias"), {"barrio": self.belen.pk})
        self.assertEqual([t.nombre for t in r.context["abiertos"]], ["Con Horario", "Siempre Abierto"])

    def test_pocas_consultas(self):
        with self.assertNumQueries(4):  # talleres, horarios (prefetch), barrios y grúas
            self.client.get(reverse("talleres:emergencias"))

    def test_taller_marca_emergencias_y_ubicacion(self):
        from django.contrib.auth import get_user_model
        u = get_user_model().objects.create_user("e@t.co", "e@t.co", "x")
        self.sin_horario.usuario = u
        self.sin_horario.save()
        self.client.force_login(u)
        base = {"duracion_franja": 60, "cupo_franja": 1, "atiende_emergencias": "on", "despinche_domicilio": "on"}
        self.client.post(reverse("talleres:agenda"), {**base, "latitud": "6.244203", "longitud": "-75.581212"})
        self.sin_horario.refresh_from_db()
        self.assertTrue(self.sin_horario.despinche_domicilio)
        self.assertEqual(str(self.sin_horario.latitud), "6.244203")
        r = self.client.post(reverse("talleres:agenda"), {**base, "latitud": "4.60", "longitud": "-74.08"})  # Bogotá
        self.assertContains(r, "Valle de Aburrá")


class RegistrarServicioTests(PanelTallerTests):
    """Punto 6: el taller registra un servicio verificado con el código del motero (lógica en garaje)."""

    def test_precarga_codigo_y_registra_verificado(self):
        from django.utils import timezone
        from garaje.hoja_vida import generar_codigo
        from garaje.models import RegistroServicio
        from garaje.tests_avisos import crear_moto
        moto = crear_moto(placa="XYZ12A", km_actual=5000)
        codigo = generar_codigo(moto).codigo
        url = reverse("talleres:registrar_servicio")
        self.assertContains(self.client.get(url, {"codigo": codigo}), f'value="{codigo}"')
        r = self.client.post(url, {"guardar": "1", "codigo": codigo, "fecha": timezone.localdate().isoformat(), "km": 5100,
                                   "otros": "Cambio de aceite", "costo": "", "notas": ""}, follow=True)
        self.assertContains(r, "Registrado y verificado en la hoja de vida de la moto")
        registro = RegistroServicio.objects.get(moto=moto)
        self.assertTrue(registro.verificado)
        r = self.client.post(url, {"guardar": "1", "codigo": codigo, "fecha": timezone.localdate().isoformat(), "km": 5200, "otros": "Otra"})
        self.assertEqual(r.status_code, 200)  # el código ya se usó
        self.assertEqual(RegistroServicio.objects.filter(moto=moto).count(), 1)


class GruasTeVarasteTests(TestCase):
    """Flujo "¿Te varaste?": opciones que filtran, grúas (modelo propio), números verificados y WhatsApp prellenado."""

    def setUp(self):
        from datetime import time
        from .models import Grua
        self.belen = Barrio.objects.get_or_create(nombre="Belén", ciudad="Medellín")[0]
        crear = lambda nombre, **k: Taller.objects.create(nombre=nombre, responsable="A", whatsapp="573001112233",
                                                          direccion="X", barrio=self.belen, activo=True,
                                                          atiende_emergencias=True, abierto_24h=True, **k)
        crear("Taller Grua", grua=True)
        crear("Taller Despinche", despinche_domicilio=True)
        crear("Taller Gasolina", gasolina_domicilio=True)
        self.g24 = Grua.objects.create(nombre="Grua Bello", telefono="570000000001", whatsapp="570000000001",
                                       municipios=["Bello"], abierto_24h=True, tarifa_desde=90000)
        self.gmed = Grua.objects.create(nombre="Grua Medellin", telefono="570000000002", whatsapp="570000000002",
                                        municipios=["Medellín"], abierto_24h=True)
        self.noche = Grua.objects.create(nombre="Grua Noche", telefono="570000000003", abre=time(20), cierra=time(4))
        Grua.objects.create(nombre="Grua Inactiva", telefono="570000000004", activo=False)

    def test_horario_de_grua_y_cierre_despues_de_medianoche(self):
        from datetime import datetime
        from .emergencias import grua_abierta
        self.assertTrue(grua_abierta(self.noche, datetime(2026, 11, 16, 23, 0)))
        self.assertTrue(grua_abierta(self.noche, datetime(2026, 11, 16, 3, 0)))
        self.assertFalse(grua_abierta(self.noche, datetime(2026, 11, 16, 12, 0)))
        self.noche.abre = None
        self.assertIsNone(grua_abierta(self.noche))

    def test_opcion_filtra_talleres(self):
        url = reverse("talleres:emergencias")
        r = self.client.get(url, {"necesito": "pinchazo"})
        self.assertEqual([t.nombre for t in r.context["abiertos"]], ["Taller Despinche"])
        self.assertFalse(r.context["mostrar_gruas"])
        r = self.client.get(url, {"necesito": "gasolina"})
        self.assertEqual([t.nombre for t in r.context["abiertos"]], ["Taller Gasolina"])
        r = self.client.get(url, {"necesito": "no_prende"})
        self.assertEqual(len(r.context["abiertos"]), 3)
        self.assertContains(r, reverse("garaje:diagnostico"))
        r = self.client.get(url, {"necesito": "inventado"})
        self.assertIsNone(r.context["necesito"])

    def test_orden_de_gruas_abiertas_primero_y_por_municipio(self):
        from datetime import datetime
        from .emergencias import ordenar_gruas
        gruas = ordenar_gruas([self.noche, self.g24, self.gmed], "Medellín", datetime(2026, 11, 16, 12, 0))
        self.assertEqual([g.nombre for g in gruas], ["Grua Medellin", "Grua Bello", "Grua Noche"])

    def test_pagina_de_grua(self):
        r = self.client.get(reverse("talleres:emergencias"), {"necesito": "grua", "barrio": self.belen.pk})
        nombres = [g.nombre for g in r.context["gruas"]]
        self.assertEqual(nombres[0], "Grua Medellin")
        self.assertNotIn("Grua Inactiva", nombres)
        self.assertEqual([t.nombre for t in r.context["abiertos"]], ["Taller Grua"])
        self.assertContains(r, "Desde $90.000")
        self.assertContains(r, "tel:+570000000001")
        self.assertContains(r, "https://wa.me/570000000001?text=Necesito%20gr%C3%BAa%20para%20mi%20moto")
        self.assertNotContains(r, "maps.google.com/?q=6")  # la ubicación solo la agrega el navegador

    def test_accidente_muestra_123_y_movilidad(self):
        r = self.client.get(reverse("talleres:emergencias"), {"necesito": "accidente"})
        self.assertContains(r, 'href="tel:123"')
        self.assertContains(r, "tel:+576044457777")
        self.assertTrue(r.context["mostrar_gruas"])

    def test_mensaje_incluye_moto_con_sesion(self):
        from .emergencias import mensaje_grua
        self.assertEqual(mensaje_grua("Yamaha NMAX 2022"), "Necesito grúa para mi moto Yamaha NMAX 2022")
        self.assertEqual(mensaje_grua(), "Necesito grúa para mi moto")

    def test_pocas_consultas(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as c:
            self.client.get(reverse("talleres:emergencias"), {"necesito": "grua"})
        propias = [q for q in c.captured_queries if "talleres_" in q["sql"]]
        self.assertLessEqual(len(propias), 5)  # talleres, horarios, barrios, grúas (+ menú del sitio)

    def test_admin_alta_de_grua(self):
        from .admin import GruaForm
        f = GruaForm({"nombre": "Nueva", "telefono": "570000000009", "municipios": ["Bello", "Medellín"],
                      "vehiculo": "cama", "activo": "on", "abre": "08:00"})
        self.assertFalse(f.is_valid())
        self.assertIn("cierra", f.errors)
        f = GruaForm({"nombre": "Nueva", "telefono": "570000000009", "municipios": ["Bello"], "vehiculo": "cama",
                      "activo": "on", "abierto_24h": "on"})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.save().municipios, ["Bello"])

    def test_boton_elegido_se_deselecciona_y_sin_emojis(self):
        r = self.client.get(reverse("talleres:emergencias"), {"necesito": "pinchazo", "barrio": self.belen.pk})
        html = r.content.decode()
        self.assertIn(f'href="?barrio={self.belen.pk}" role="button" aria-pressed="true"', html)
        self.assertEqual(html.count('aria-pressed="false"'), 4)
        self.assertEqual(html.count('class="em-icono"'), 5)
        self.assertNotIn("Ver todo", html)
        self.assertIn("Toca otra vez", html)
        self.assertNotIn("Toca otra vez", self.client.get(reverse("talleres:emergencias")).content.decode())
