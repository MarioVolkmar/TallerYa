"""Consultas SQL de las páginas del foro, la portada y los talleres: no deben crecer con la cantidad de temas,
respuestas, asistentes o talleres (sin N+1). Se mide con pocos datos y se exige el mismo número con muchos."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from foro.models import Asistencia, Categoria, Pregunta, Respuesta, Rodada
from talleres.models import Barrio, Resena, Taller

User = get_user_model()


class SinNmasUnoTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.n = 0

    def _usuario(self):
        self.n += 1
        return User.objects.create_user(f"u{self.n}@x.com", f"u{self.n}@x.com", "x", first_name=f"U{self.n}")

    def _consultas(self, url, cliente=None):
        cliente = cliente or self.client
        cliente.get(url)  # calienta sesión, vistas contadas y avisos
        with CaptureQueriesContext(connection) as c:
            self.assertEqual(cliente.get(url).status_code, 200)
        return len(c)

    def _igual_con_mas(self, url, agregar):
        antes = self._consultas(url)
        agregar()
        self.client.get(url)
        with self.assertNumQueries(antes):
            self.client.get(url)

    def test_pregunta_con_muchas_respuestas_en_hilo(self):
        self.client.force_login(self.ana)
        p = Pregunta.objects.create(autor=self._usuario(), titulo="¿Aceite?", cuerpo="Hola @ana-1")
        Respuesta.objects.create(pregunta=p, autor=self._usuario(), cuerpo="Uno")

        def agregar():
            padre = None
            for i in range(12):
                padre = Respuesta.objects.create(pregunta=p, autor=self._usuario(), cuerpo=f"R{i} @ana-{self.ana.pk}",
                                                 padre=padre if i % 3 else None)
        self._igual_con_mas(p.get_absolute_url(), agregar)

    def test_lista_del_foro(self):
        Pregunta.objects.create(autor=self.ana, titulo="Uno", cuerpo="x")

        def agregar():
            for i, c in enumerate(Categoria.values * 3):
                Pregunta.objects.create(autor=self._usuario(), titulo=f"T{i}", cuerpo="x", categoria=c)
        self._igual_con_mas(reverse("foro:lista"), agregar)

    def _rodada(self, autor):
        p = Pregunta.objects.create(autor=autor, titulo="Rodada", cuerpo="x", categoria=Categoria.RUTAS)
        return Rodada.objects.create(pregunta=p, organizador=autor, fecha_hora=timezone.now() + timedelta(days=3),
                                     punto_encuentro="Parque", destino="Santa Fe", nivel="principiante", cupo=50)

    def test_rodadas_y_rodada_con_asistentes(self):
        rodada = self._rodada(self.ana)
        self.client.force_login(self.ana)

        def agregar():
            for _ in range(6):
                u = self._usuario()
                Asistencia.objects.create(rodada=rodada, usuario=u)
                Respuesta.objects.create(pregunta=rodada.pregunta, autor=u, cuerpo="Voy")
                self._rodada(u)
        self._igual_con_mas(rodada.get_absolute_url(), agregar)
        self._igual_con_mas(reverse("foro:rodadas"), lambda: [self._rodada(self._usuario()) for _ in range(4)])

    def test_portada_y_directorio_de_talleres(self):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]

        def taller(i):
            t = Taller.objects.create(nombre=f"Taller {i}", responsable="X", whatsapp="573001234567", direccion="Cra 1",
                                      barrio=barrio, activo=True, usuario=self._usuario())
            Resena.objects.create(taller=t, nombre="Pepe", estrellas=4, comentario="Bien")
            return t
        primero = taller(0)
        self._igual_con_mas(reverse("talleres:inicio"), lambda: [taller(i) for i in range(1, 7)])
        self._igual_con_mas(reverse("talleres:directorio"), lambda: [taller(i) for i in range(7, 12)])
        self._igual_con_mas(primero.get_absolute_url(),
                            lambda: [Resena.objects.create(taller=primero, nombre="A", estrellas=5, comentario="x")
                                     for _ in range(5)])
