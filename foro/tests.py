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


class HiloYMencionesTests(TestCase):
    """Respuestas en hilo (máx. 2 niveles visuales), @menciones y sus notificaciones sin duplicar."""

    def setUp(self):
        cache.clear()
        from notificaciones.models import Notificacion
        self.Notificacion = Notificacion
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.caro = User.objects.create_user("caro@x.com", "caro@x.com", "x", first_name="Carolina")
        self.pregunta = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la Boxer?", cuerpo="Detalles")

    def _alias(self, u):
        from .menciones import alias
        return alias(u)

    def _notifs(self, u):
        return list(self.Notificacion.objects.filter(usuario=u).values_list("titulo", flat=True))

    def test_responder_a_un_mensaje_lo_anida_y_notifica_al_autor(self):
        r1 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.client.force_login(self.caro)
        r = self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Yo uso 10W-40", "padre": r1.pk})
        hija = Respuesta.objects.get(cuerpo="Yo uso 10W-40")
        self.assertRedirects(r, hija.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(hija.padre, r1)
        self.assertEqual(self._notifs(self.beto), ["Carolina respondió tu mensaje"])
        self.assertEqual(self._notifs(self.ana), [])  # la respuesta en hilo no avisa a quien preguntó

    def test_padre_de_otro_tema_no_se_acepta(self):
        otra = Pregunta.objects.create(autor=self.beto, titulo="Otra pregunta de prueba", cuerpo="x")
        ajena = Respuesta.objects.create(pregunta=otra, autor=self.beto, cuerpo="Ajena")
        self.client.force_login(self.caro)
        self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": "Hola", "padre": ajena.pk})
        self.assertFalse(Respuesta.objects.filter(cuerpo="Hola").exists())

    def test_mencion_notifica_y_se_muestra_como_nombre(self):
        self.client.force_login(self.beto)
        self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": f"Pregúntale a @{self._alias(self.caro)} que sabe"})
        self.assertEqual(self._notifs(self.caro), ["Beto te mencionó en ¿Qué aceite le echo a la Boxer?"])
        r = self.client.get(self.pregunta.get_absolute_url())
        self.assertContains(r, f'<a href="{reverse("foro:integrante", args=[self.caro.pk])}" class="fo-mencion">@Carolina</a>', html=True)
        self.assertNotContains(r, "caro@x.com")

    def test_mencion_y_respuesta_directa_no_duplican(self):
        r1 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.client.force_login(self.caro)
        self.client.post(self.pregunta.get_absolute_url(),
                         {"cuerpo": f"@{self._alias(self.beto)} ¿y sintético? @{self._alias(self.beto)}", "padre": r1.pk})
        self.assertEqual(self._notifs(self.beto), ["Carolina respondió tu mensaje"])

    def test_mencionar_a_quien_pregunto_en_respuesta_de_primer_nivel_no_duplica(self):
        self.client.force_login(self.beto)
        self.client.post(self.pregunta.get_absolute_url(), {"cuerpo": f"@{self._alias(self.ana)} usa 20W-50"})
        self.assertEqual(self._notifs(self.ana), ["Beto respondió tu pregunta"])

    def test_mencion_falsa_o_propia_no_notifica(self):
        self.client.force_login(self.beto)
        self.client.post(self.pregunta.get_absolute_url(),
                         {"cuerpo": f"@otronombre-{self.caro.pk} y yo mismo @{self._alias(self.beto)}"})
        self.assertEqual(self._notifs(self.caro), [])
        self.assertEqual(self._notifs(self.beto), [])

    def test_hilo_profundo_se_aplana_en_el_nivel_2(self):
        from .menciones import armar_hilo
        r1 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="1")
        r2 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.caro, cuerpo="2", padre=r1)
        r3 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.ana, cuerpo="3", padre=r2)
        r4 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="4", padre=r3)
        r5 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.caro, cuerpo="5", padre=r4)
        todas = list(self.pregunta.respuestas.select_related("autor"))
        raiz = armar_hilo(self.pregunta, todas, {r.pk: r.padre_id for r in todas})
        self.assertEqual([r.pk for r in raiz], [r1.pk])
        n2 = raiz[0].en_hilo[0]
        self.assertEqual((n2.pk, n2.nivel), (r2.pk, 1))
        n3 = n2.en_hilo[0]
        self.assertEqual((n3.pk, n3.nivel), (r3.pk, 2))
        self.assertEqual([(h.pk, h.nivel, h.responde_a) for h in n3.planas], [(r4.pk, 2, "Ana"), (r5.pk, 2, "Beto")])
        self.assertEqual(raiz[0].total_hilo, 4)
        html = self.client.get(self.pregunta.get_absolute_url()).content.decode()
        self.assertIn("en respuesta a", html)
        self.assertIn(f'aria-controls="hilo-{r1.pk}"', html)

    def test_respuesta_cuyo_padre_se_oculto_sube_de_nivel(self):
        r1 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="oculta", visible=False)
        r2 = Respuesta.objects.create(pregunta=self.pregunta, autor=self.caro, cuerpo="Sigo visible", padre=r1)
        r = self.client.get(self.pregunta.get_absolute_url())
        self.assertContains(r, "Sigo visible")
        self.assertNotContains(r, "oculta</p>")
        self.assertEqual([x.pk for x in r.context["hilo"]], [r2.pk])

    def test_sugerir_usuarios_sin_correos_y_con_sesion(self):
        Respuesta.objects.create(pregunta=self.pregunta, autor=self.caro, cuerpo="Hola")
        url = reverse("foro:sugerir_usuarios")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.beto)
        datos = self.client.get(url, {"q": "car", "pregunta": self.pregunta.pk}).json()["usuarios"]
        self.assertEqual(datos, [{"alias": self._alias(self.caro), "nombre": "Carolina", "detalle": "En este tema"}])
        self.assertNotIn("@x.com", str(self.client.get(url).json()))


class ListaAgrupadaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        for i in range(7):
            Pregunta.objects.create(autor=self.ana, titulo=f"Ruido raro en la moto número {i}", cuerpo="x", categoria="fallas")
        Pregunta.objects.create(autor=self.ana, titulo="¿Cada cuánto cambio el aceite?", cuerpo="x", categoria="mantenimiento")

    def test_vista_por_defecto_recientes_y_grupos(self):
        r = self.client.get(reverse("foro:lista"))
        self.assertTrue(r.context["agrupada"])
        self.assertEqual(len(r.context["recientes"]), 5)
        grupos = {g["clave"]: g for g in r.context["grupos"]}
        self.assertEqual((grupos["fallas"]["total"], len(grupos["fallas"]["temas"])), (7, 5))
        self.assertEqual(grupos["mantenimiento"]["total"], 1)
        self.assertEqual(grupos["rutas"]["total"], 0)
        self.assertContains(r, 'class="papel fo-grupo fo-grupo-fallas"')
        self.assertContains(r, "?categoria=fallas")

    def test_con_orden_o_filtro_lista_plana(self):
        for qs in ({"orden": "votados"}, {"filtro": "sin-respuesta"}, {"categoria": "fallas"}, {"q": "aceite"}):
            r = self.client.get(reverse("foro:lista"), qs)
            self.assertFalse(r.context["agrupada"], qs)
        self.assertEqual(len(self.client.get(reverse("foro:lista"), {"categoria": "fallas"}).context["pagina"]), 7)

    def test_estado_accesible_y_cifras_compactas(self):
        from .templatetags.foro_extras import cifra_corta
        self.assertEqual([cifra_corta(n) for n in (0, 999, 1000, 1234, 15500, 2_300_000)],
                         ["0", "999", "1 mil", "1,2 mil", "15,5 mil", "2,3 M"])
        self.assertContains(self.client.get(reverse("foro:lista")), '<span class="sr-only">Sin respuesta</span>')

    def test_fecha_en_una_sola_unidad(self):
        from datetime import timedelta
        from django.utils import timezone
        from .templatetags.foro_extras import hace_texto
        ahora = timezone.now()
        casos = {timedelta(seconds=20): "hace un momento", timedelta(minutes=5): "hace 5 min",
                 timedelta(hours=19, minutes=13): "hace 19 h", timedelta(days=1, hours=3): "hace 1 día",
                 timedelta(days=3): "hace 3 días", timedelta(days=70): "hace 2 meses", timedelta(days=800): "hace 2 años"}
        for delta, esperado in casos.items():
            self.assertEqual(hace_texto(ahora - delta, ahora), esperado)


class ReaccionesYMenuTests(TestCase):
    def setUp(self):
        cache.clear()
        from notificaciones.models import Notificacion
        self.Notificacion = Notificacion
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.caro = User.objects.create_user("caro@x.com", "caro@x.com", "x", first_name="Carolina")
        self.pregunta = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la Boxer?", cuerpo="Detalles")
        self.resp = Respuesta.objects.create(pregunta=self.pregunta, autor=self.beto, cuerpo="Usa 20W-50")
        self.url = reverse("foro:reaccionar", args=["respuesta", self.resp.pk])

    def _titulos(self, u):
        return list(self.Notificacion.objects.filter(usuario=u).values_list("titulo", flat=True))

    def test_reaccionar_requiere_sesion(self):
        r = self.client.post(self.url, {"reaccion": "gusta"})
        self.assertTrue(r.url.startswith(reverse("cuentas:entrar")))

    def test_poner_cambiar_y_quitar_con_fetch(self):
        from .models import Reaccion
        self.client.force_login(self.caro)
        cab = {"HTTP_X_REQUESTED_WITH": "fetch"}
        d = self.client.post(self.url, {"reaccion": "gusta"}, **cab).json()
        self.assertTrue(d["ok"])
        self.assertIn("👍", d["html"])
        self.client.post(self.url, {"reaccion": "encanta"}, **cab)
        self.assertEqual(list(Reaccion.objects.values_list("tipo", flat=True)), ["encanta"])
        self.client.post(self.url, {"reaccion": "encanta"}, **cab)
        self.assertFalse(Reaccion.objects.exists())

    def test_respaldo_sin_js_redirige(self):
        self.client.force_login(self.caro)
        r = self.client.post(self.url, {"reaccion": "gusta"})
        self.assertRedirects(r, self.resp.get_absolute_url(), fetch_redirect_response=False)

    def test_no_reacciona_a_lo_propio_ni_tipo_invalido(self):
        from .models import Reaccion
        self.client.force_login(self.beto)
        self.client.post(self.url, {"reaccion": "gusta"})
        self.client.force_login(self.caro)
        self.client.post(self.url, {"reaccion": "inapropiado"})
        self.assertFalse(Reaccion.objects.exists())

    def test_notificacion_agrupada(self):
        self.client.force_login(self.caro)
        self.client.post(self.url, {"reaccion": "gusta"})
        self.assertEqual(self._titulos(self.beto), ["A Carolina le gustó tu respuesta"])
        self.client.force_login(self.ana)
        self.client.post(self.url, {"reaccion": "gusta"})
        self.assertEqual(self._titulos(self.beto), ["A 2 personas les gustó tu respuesta"])
        self.client.post(self.url, {"reaccion": "divierte"})
        self.assertEqual(self._titulos(self.beto), ["2 personas reaccionaron a tu respuesta"])

    def test_reporte_con_motivo_y_sin_duplicar(self):
        url = reverse("foro:reportar", args=["respuesta", self.resp.pk])
        self.client.force_login(self.caro)
        d = self.client.post(url, {"motivo_tipo": "spam"}, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertTrue(d["ok"])
        self.assertEqual(Reporte.objects.get().motivo, "Spam o publicidad")
        d = self.client.post(url, {"motivo_tipo": "otro", "motivo": "x"}, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertFalse(d["ok"])
        self.assertEqual(Reporte.objects.count(), 1)
        self.assertContains(self.client.get(self.pregunta.get_absolute_url()), "Ya lo reportaste")

    def test_dialogo_de_reporte_sin_js(self):
        self.client.force_login(self.caro)
        r = self.client.get(self.pregunta.get_absolute_url(), {"reportar": f"respuesta-{self.resp.pk}"})
        self.assertContains(r, 'action="%s"' % reverse("foro:reportar", args=["respuesta", self.resp.pk]))
        self.assertContains(r, "Spam o publicidad")

    def test_editar_y_eliminar_solo_lo_propio(self):
        from .menciones import alias
        hija = Respuesta.objects.create(pregunta=self.pregunta, autor=self.caro, cuerpo="¿Y sintético?", padre=self.resp)
        editar = reverse("foro:editar", args=["respuesta", self.resp.pk])
        eliminar = reverse("foro:eliminar", args=["respuesta", self.resp.pk])
        self.client.force_login(self.caro)
        self.assertEqual(self.client.get(editar).status_code, 404)
        self.assertEqual(self.client.post(eliminar).status_code, 404)
        self.client.force_login(self.beto)
        self.client.post(editar, {"cuerpo": "Usa 20W-50, @" + alias(self.caro)})
        self.resp.refresh_from_db()
        self.assertTrue(self.resp.cuerpo.startswith("Usa 20W-50, @"))
        self.assertTrue(self.Notificacion.objects.filter(usuario=self.caro, titulo__contains="mencionó").exists())
        self.client.post(eliminar)
        self.assertFalse(Respuesta.objects.filter(pk=self.resp.pk).exists())
        hija.refresh_from_db()
        self.assertIsNone(hija.padre)  # sube al nivel de la respuesta eliminada

    def test_menu_muestra_editar_solo_al_autor(self):
        self.client.force_login(self.beto)
        r = self.client.get(self.pregunta.get_absolute_url())
        self.assertContains(r, reverse("foro:editar", args=["respuesta", self.resp.pk]))
        self.assertNotContains(r, reverse("foro:editar", args=["pregunta", self.pregunta.pk]))


class LoPropioNoSeVotaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.pregunta = Pregunta.objects.create(autor=self.ana, titulo="¿Qué aceite le echo a la Boxer?", cuerpo="x")
        self.resp = Respuesta.objects.create(pregunta=self.pregunta, autor=self.ana, cuerpo="Me respondo")

    def test_voto_y_reaccion_propios_se_rechazan(self):
        from .models import Reaccion, Voto
        self.client.force_login(self.ana)
        r = self.client.post(reverse("foro:votar", args=["respuesta", self.resp.pk]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 403)
        self.client.post(reverse("foro:votar", args=["pregunta", self.pregunta.pk]))
        r = self.client.post(reverse("foro:reaccionar", args=["pregunta", self.pregunta.pk]), {"reaccion": "gusta"},
                             HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Voto.objects.exists())
        self.assertFalse(Reaccion.objects.exists())

    def test_en_lo_propio_no_hay_botones_solo_conteos(self):
        from .models import Voto
        Voto.objects.create(usuario=self.beto, respuesta=self.resp)
        self.client.force_login(self.ana)
        html = self.client.get(self.pregunta.get_absolute_url()).content.decode()
        self.assertNotIn(reverse("foro:votar", args=["respuesta", self.resp.pk]), html)
        self.assertNotIn(reverse("foro:reaccionar", args=["respuesta", self.resp.pk]), html)
        self.assertNotIn(reverse("foro:votar", args=["pregunta", self.pregunta.pk]), html)
        self.assertIn('<span class="fo-votar-n">1</span>', html)


class ActividadEIntegranteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        self.vieja = Pregunta.objects.create(autor=self.ana, titulo="Pregunta vieja sobre frenos", cuerpo="x")
        self.nueva = Pregunta.objects.create(autor=self.ana, titulo="Pregunta nueva sobre cadena", cuerpo="x")

    def test_responder_sube_el_tema_en_recientes(self):
        self.assertEqual(self.client.get(reverse("foro:lista")).context["recientes"][0], self.nueva)
        Respuesta.objects.create(pregunta=self.vieja, autor=self.beto, cuerpo="Cambia las pastillas")
        r = self.client.get(reverse("foro:lista"))
        self.assertEqual(r.context["recientes"][0], self.vieja)
        self.assertContains(r, "última respuesta")
        self.assertEqual(r.context["grupos"][0]["temas"][0], self.vieja)
        self.vieja.refresh_from_db()
        self.assertEqual(self.vieja.ultimo_autor, self.beto)

    def test_eliminar_la_respuesta_recalcula(self):
        resp = Respuesta.objects.create(pregunta=self.vieja, autor=self.beto, cuerpo="Cambia las pastillas")
        self.client.force_login(self.beto)
        self.client.post(reverse("foro:eliminar", args=["respuesta", resp.pk]))
        self.vieja.refresh_from_db()
        self.assertIsNone(self.vieja.ultimo_autor)
        self.assertEqual(self.vieja.ultima_actividad, self.vieja.creado)

    def test_pagina_de_integrante_publica_y_sin_datos_privados(self):
        resp = Respuesta.objects.create(pregunta=self.vieja, autor=self.beto, cuerpo="Cambia las pastillas delanteras")
        self.vieja.mejor_respuesta = resp
        self.vieja.save(update_fields=["mejor_respuesta"])
        from .models import Voto
        Voto.objects.create(usuario=self.ana, respuesta=resp)
        r = self.client.get(reverse("foro:integrante", args=[self.beto.pk]))
        self.assertEqual(r.context["conteos"], {"preguntas": 0, "respuestas": 1, "soluciones": 1, "me_sirvio": 1})
        self.assertContains(r, f"#r{resp.pk}")
        self.assertContains(r, "Pregunta vieja sobre frenos")
        self.assertNotContains(r, "beto@x.com")
        r = self.client.get(reverse("foro:integrante", args=[self.ana.pk]), {"tab": "preguntas"})
        self.assertEqual(r.context["pestana"], "preguntas")
        self.assertEqual(len(r.context["pagina"]), 2)

    def test_integrante_pagina_de_20(self):
        for i in range(23):
            Respuesta.objects.create(pregunta=self.vieja, autor=self.beto, cuerpo=f"Respuesta {i}")
        r = self.client.get(reverse("foro:integrante", args=[self.beto.pk]))
        self.assertEqual(len(r.context["pagina"]), 20)
        self.assertEqual(len(self.client.get(reverse("foro:integrante", args=[self.beto.pk]), {"pagina": 2}).context["pagina"]), 3)

    def test_nombre_del_autor_lleva_a_su_actividad(self):
        r = self.client.get(self.vieja.get_absolute_url())
        self.assertContains(r, reverse("foro:integrante", args=[self.ana.pk]))


class ComentariosDeRodadaTests(TestCase):
    """Los comentarios de una rodada usan el mismo hilo, reacciones y menciones que las respuestas del foro."""

    def setUp(self):
        cache.clear()
        from datetime import timedelta
        from django.utils import timezone
        from .models import Rodada
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.beto = User.objects.create_user("beto@x.com", "beto@x.com", "x", first_name="Beto")
        p = Pregunta.objects.create(autor=self.ana, titulo="Rodada a Santa Elena", cuerpo="x", categoria="rutas")
        self.rodada = Rodada.objects.create(pregunta=p, organizador=self.ana, fecha_hora=timezone.now() + timedelta(days=3),
                                            punto_encuentro="Parque de El Poblado", destino="Santa Elena")
        self.pregunta = p
        self.comentario = Respuesta.objects.create(pregunta=p, autor=self.beto, cuerpo="¿A qué hora salimos?")

    def test_responder_a_lo_propio_en_hilo_y_notificar(self):
        from notificaciones.models import Notificacion
        self.client.force_login(self.beto)
        r = self.client.post(self.rodada.get_absolute_url(), {"cuerpo": "Y llevo herramienta", "padre": self.comentario.pk})
        hija = Respuesta.objects.get(cuerpo="Y llevo herramienta")
        self.assertRedirects(r, f"{self.rodada.get_absolute_url()}#r{hija.pk}", fetch_redirect_response=False)
        self.assertEqual(hija.padre, self.comentario)
        self.client.force_login(self.ana)
        self.client.post(self.rodada.get_absolute_url(), {"cuerpo": "A las 6", "padre": self.comentario.pk})
        self.assertTrue(Notificacion.objects.filter(usuario=self.beto, titulo="Ana respondió tu mensaje").exists())

    def test_comentario_de_primer_nivel_avisa_al_organizador(self):
        from notificaciones.models import Notificacion
        self.client.force_login(self.beto)
        self.client.post(self.rodada.get_absolute_url(), {"cuerpo": "¡Voy!"})
        self.assertTrue(Notificacion.objects.filter(usuario=self.ana, titulo="Beto comentó tu rodada").exists())

    def test_reaccionar_a_lo_propio_rechazado_y_barra_en_la_pagina(self):
        from .models import Reaccion
        self.client.force_login(self.beto)
        r = self.client.post(reverse("foro:reaccionar", args=["respuesta", self.comentario.pk]), {"reaccion": "gusta"},
                             HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Reaccion.objects.exists())
        html = self.client.get(self.rodada.get_absolute_url()).content.decode()
        self.assertIn(f'data-responder="{self.comentario.pk}"', html)  # sí puede responder lo suyo
        self.assertNotIn(reverse("foro:reaccionar", args=["respuesta", self.comentario.pk]), html)
        self.client.force_login(self.ana)
        html = self.client.get(self.rodada.get_absolute_url()).content.decode()
        self.assertIn(reverse("foro:reaccionar", args=["respuesta", self.comentario.pk]), html)
        self.assertIn('id="fo-plantilla-hilo"', html)
