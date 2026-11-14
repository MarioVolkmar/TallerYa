from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from talleres.models import Barrio, Taller

from .models import Pregunta, Reporte, Respuesta

User = get_user_model()


class ForoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.pregunta = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la Boxer?", cuerpo="Detalles")

    def test_lista_y_detalle_publicos(self):
        self.assertContains(self.client.get(reverse("foro:lista")), "Boxer")
        self.assertContains(self.client.get(self.pregunta.get_absolute_url()), "Detalles")

    def test_url_sin_slug_redirige_a_la_canonica(self):
        r = self.client.get(reverse("foro:pregunta_corta", args=[self.pregunta.pk]))
        self.assertRedirects(r, self.pregunta.get_absolute_url(), status_code=301)

    def test_preguntar_requiere_sesion(self):
        r = self.client.get(reverse("foro:preguntar"))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_preguntar_y_responder(self):
        self.client.force_login(self.beto)
        r = self.client.post(reverse("foro:preguntar"), {"titulo": "¿Cómo tensiono la cadena?", "cuerpo": "Ayuda"})
        p = Pregunta.objects.get(titulo__startswith="¿Cómo")
        self.assertRedirects(r, p.get_absolute_url())
        self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Usa 20W-50"})
        self.assertEqual(self.pregunta.respuestas.get().autor, self.beto)

    def test_responder_sin_sesion_redirige_a_entrar(self):
        r = self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Hola"})
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))
        self.assertFalse(Respuesta.objects.exists())

    def test_solo_el_autor_marca_la_mejor_respuesta(self):
        resp = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.client.force_login(self.beto)
        self.assertEqual(self.client.post(reverse("foro:marcar_mejor", args=[resp.pk])).status_code, 404)
        self.client.force_login(self.ana)
        self.client.post(reverse("foro:marcar_mejor", args=[resp.pk]))
        self.pregunta.refresh_from_db()
        self.assertEqual(self.pregunta.mejor_respuesta, resp)

    def test_tres_reportes_ocultan_la_publicacion(self):
        for i in range(3):
            u = User.objects.create_user(f"u{i}@x.com", f"u{i}@x.com", "x")
            self.client.force_login(u)
            self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))
            self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))  # duplicado ignorado
        self.assertEqual(Reporte.objects.count(), 3)
        self.pregunta.refresh_from_db()
        self.assertFalse(self.pregunta.visible)
        self.assertEqual(self.client.get(self.pregunta.get_absolute_url()).status_code, 404)

    def test_no_se_puede_reportar_lo_propio(self):
        self.client.force_login(self.ana)
        self.client.post(reverse("foro:reportar", args=["pregunta", self.pregunta.pk]))
        self.assertFalse(Reporte.objects.exists())

    def test_respuesta_de_taller_lleva_insignia(self):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        Taller.objects.create(nombre="Taller Pro", responsable="X", whatsapp="573001234567", direccion="X",
                              barrio=barrio, activo=True, verificado=True, usuario=self.beto)
        Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.assertContains(self.client.get(self.pregunta.get_absolute_url()), "Taller verificado")

    def test_limite_de_publicaciones_por_hora(self):
        self.client.force_login(self.beto)
        for i in range(11):
            self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": f"Respuesta {i}"})
        self.assertEqual(Respuesta.objects.count(), 10)


class ForoAmpliadoTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.ana = User.objects.create_user("ana@f.co", "ana@f.co", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@f.co", "beto@f.co", "x", first_name="Beto")
        self.p1 = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la moto?", cuerpo="x", categoria="mantenimiento")
        self.p2 = Pregunta.objects.create(autor=self.ana, titulo="Ruta para el domingo por Santa Elena", cuerpo="y", categoria="rutas")

    def test_filtro_por_tema_y_buscador_en_respuestas(self):
        Respuesta.objects.create(pregunta=self.p2, autor=self.beto, cuerpo="Pasa por Guarne")
        r = self.client.get(reverse("foro:lista"), {"categoria": "rutas"})
        self.assertEqual([p.pk for p in r.context["pagina"]], [self.p2.pk])
        r = self.client.get(reverse("foro:lista"), {"q": "Guarne"})
        self.assertEqual([p.pk for p in r.context["pagina"]], [self.p2.pk])

    def test_votar_y_ordenar_por_votos(self):
        self.client.force_login(self.beto)
        r = self.client.post(reverse("foro:votar", args=["pregunta", self.p1.pk]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.json(), {"votado": True, "votos": 1})
        r = self.client.get(reverse("foro:lista"), {"orden": "votados"})
        self.assertEqual(r.context["pagina"][0].pk, self.p1.pk)
        self.client.force_login(self.ana)  # lo propio no se vota
        self.client.post(reverse("foro:votar", args=["pregunta", self.p1.pk]))
        self.assertEqual(self.p1.votos.count(), 1)

    def test_vistas_una_por_sesion(self):
        url = self.p1.get_absolute_url()
        self.client.get(url)
        self.client.get(url)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.vistas, 1)

    def test_demo_del_foro_no_borra_y_no_duplica(self):
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for correo in ("andres.demo@tallerya.local", "camila.demo@tallerya.local", "paisa.demo@tallerya.local"):
            User.objects.create_user(correo, correo)
        call_command("cargar_foro_demo", stdout=open(__import__("os").devnull, "w"))
        n = Pregunta.objects.count()
        call_command("cargar_foro_demo", stdout=open(__import__("os").devnull, "w"))
        self.assertEqual(Pregunta.objects.count(), n)
        self.assertTrue(Pregunta.objects.filter(pk=self.p1.pk).exists())



class RodadaTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        cache.clear()
        self.ana = User.objects.create_user("ana@r.com", "ana@r.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@r.com", "beto@r.com", "x", first_name="Beto")
        self.manana = timezone.localtime() + timedelta(days=1)
        self.datos = {"titulo": "Rodada a Santa Elena", "fecha_hora": self.manana.strftime("%Y-%m-%dT%H:%M"),
                      "punto_encuentro": "Estación Poblado del metro", "destino": "Santa Elena por Las Palmas",
                      "nivel": "principiante", "cupo": "2", "cuerpo": ""}

    def _crear(self, **cambios):
        self.client.force_login(self.ana)
        return self.client.post(reverse("foro:rodada_crear"), {**self.datos, **cambios})

    def _rodada(self, dias, cupo=None, autor=None):
        from datetime import timedelta
        from django.utils import timezone
        from .models import Categoria, Rodada
        autor = autor or self.ana
        p = Pregunta.objects.create(autor=autor, titulo=f"Rodada {dias}", cuerpo="x", categoria=Categoria.RUTAS)
        return Rodada.objects.create(pregunta=p, organizador=autor, fecha_hora=timezone.now() + timedelta(days=dias),
                                     punto_encuentro="Parque de Envigado", destino="El Retiro", cupo=cupo)

    def test_crear_rodada_crea_hilo_del_foro_y_organizador_va(self):
        from .models import Rodada
        r = self._crear()
        rodada = Rodada.objects.get()
        self.assertRedirects(r, rodada.get_absolute_url())
        self.assertEqual(rodada.pregunta.categoria, "rutas")
        self.assertEqual(rodada.organizador, self.ana)
        self.assertTrue(rodada.asistencias.filter(usuario=self.ana).exists())
        # la pregunta del foro lleva a la página de la rodada
        self.assertRedirects(self.client.get(rodada.pregunta.get_absolute_url()), rodada.get_absolute_url())

    def test_rechaza_direcciones_privadas_y_fechas_pasadas(self):
        from .models import Rodada
        for punto in ["Calle 10 # 43-20", "Cra 45 No. 12-3", "Mi casa en Belén", "Torre 3 apto 501"]:
            r = self._crear(punto_encuentro=punto)
            self.assertContains(r, "dirección privada")
        r = self._crear(fecha_hora="2020-01-01T08:00")
        self.assertContains(r, "en el futuro")
        self.assertFalse(Rodada.objects.exists())

    def test_crear_requiere_sesion(self):
        r = self.client.get(reverse("foro:rodada_crear"))
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_voy_respeta_cupo_y_se_puede_bajar(self):
        rodada = self._rodada(2, cupo=2)
        rodada.asistencias.create(usuario=self.ana)
        url = reverse("foro:rodada_voy", args=[rodada.pk])
        self.client.force_login(self.beto)
        self.client.post(url)
        self.assertEqual(rodada.asistencias.count(), 2)
        carla = User.objects.create_user("c@r.com", "c@r.com", "x", first_name="Carla")
        self.client.force_login(carla)
        self.client.post(url)
        self.assertFalse(rodada.asistencias.filter(usuario=carla).exists())  # cupo lleno
        self.client.force_login(self.beto)
        self.client.post(url)
        self.assertFalse(rodada.asistencias.filter(usuario=self.beto).exists())
        self.client.force_login(self.ana)
        self.client.post(url)  # quien organiza no se baja
        self.assertTrue(rodada.asistencias.filter(usuario=self.ana).exists())

    def test_rodada_pasada_no_admite_voy(self):
        rodada = self._rodada(-1)
        self.client.force_login(self.beto)
        self.client.post(reverse("foro:rodada_voy", args=[rodada.pk]))
        self.assertFalse(rodada.asistencias.exists())

    def test_proximas_primero_y_pasadas_archivadas(self):
        self._rodada(5)
        self._rodada(1)
        self._rodada(-3)
        r = self.client.get(reverse("foro:rodadas"))
        html = r.content.decode()
        self.assertLess(html.index("Rodada 1"), html.index("Rodada 5"))
        self.assertNotIn("Rodada -3", html)
        self.assertContains(self.client.get(reverse("foro:rodadas") + "?ver=pasadas"), "Rodada -3")

    def test_comentarios_usan_respuestas_y_notifican(self):
        rodada = self._rodada(2)
        self.client.force_login(self.beto)
        self.client.post(rodada.get_absolute_url(), {"cuerpo": "¿Hay que tanquear antes?"})
        self.assertEqual(rodada.pregunta.respuestas.get().autor, self.beto)
        self.assertTrue(self.ana.notificaciones.filter(titulo__icontains="rodada").exists())
        self.assertContains(self.client.get(rodada.get_absolute_url()), "tanquear")

    def test_rodada_reportada_se_oculta(self):
        from .models import REPORTES_PARA_OCULTAR
        rodada = self._rodada(2)
        for i in range(REPORTES_PARA_OCULTAR):
            u = User.objects.create_user(f"r{i}@r.com", f"r{i}@r.com", "x")
            self.client.force_login(u)
            self.client.post(reverse("foro:reportar", args=["pregunta", rodada.pregunta.pk]))
        self.assertEqual(self.client.get(rodada.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("foro:rodadas")), "Rodada 2")
