from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cupones.models import CodigoCupon, Cupon, Motociclista
from foro.models import Asistencia, Categoria, Pregunta, Respuesta, Rodada, Voto
from talleres.models import Barrio, Resena, Taller

from . import reglas
from .models import Canje, Logro

User = get_user_model()


def _usuario(n):
    return User.objects.create_user(f"{n}@l.com", f"{n}@l.com", "x", first_name=n)


class ReglasTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = _usuario("ana")
        self.otros = [_usuario(f"u{i}") for i in range(4)]

    def claves(self):
        return list(self.ana.logros.values_list("clave", flat=True))

    def test_posts_en_bruto_no_cuentan(self):
        p = Pregunta.objects.create(autor=self.otros[0], titulo="¿Qué llanta compro?", cuerpo="x")
        for i in range(5):
            Respuesta.objects.create(pregunta=p, autor=self.ana, cuerpo=f"respuesta {i}")
            Pregunta.objects.create(autor=self.ana, titulo=f"Pregunta {i} de Ana", cuerpo="x")
        self.assertEqual(reglas.evaluar(self.ana), 0)

    def test_aporte_util_por_votos_o_solucion_con_tope_mensual(self):
        p = Pregunta.objects.create(autor=self.otros[0], titulo="¿Qué llanta compro?", cuerpo="x")
        resp = [Respuesta.objects.create(pregunta=p, autor=self.ana, cuerpo=f"r{i}") for i in range(5)]
        Voto.objects.create(usuario=self.otros[1], respuesta=resp[0])  # un solo voto: no alcanza
        self.assertEqual(reglas.evaluar(self.ana), 0)
        Voto.objects.create(usuario=self.otros[2], respuesta=resp[0])
        p.mejor_respuesta = resp[1]
        p.save()
        for r in resp[2:]:
            for u in self.otros[1:3]:
                Voto.objects.create(usuario=u, respuesta=r)
        self.assertEqual(reglas.evaluar(self.ana), 3)  # 5 útiles, tope 3 al mes
        self.assertEqual(reglas.evaluar(self.ana), 0)  # idempotente
        self.assertEqual(self.claves().count("aporte"), 3)

    def test_respuesta_a_pregunta_propia_u_oculta_no_cuenta(self):
        propia = Pregunta.objects.create(autor=self.ana, titulo="Mi pregunta propia", cuerpo="x")
        r1 = Respuesta.objects.create(pregunta=propia, autor=self.ana, cuerpo="me respondo")
        ajena = Pregunta.objects.create(autor=self.otros[0], titulo="Pregunta ajena", cuerpo="x")
        r2 = Respuesta.objects.create(pregunta=ajena, autor=self.ana, cuerpo="oculta", visible=False)
        for r in (r1, r2):
            for u in self.otros[1:3]:
                Voto.objects.create(usuario=u, respuesta=r)
        self.assertEqual(reglas.evaluar(self.ana), 0)

    def _rodada(self, organizador, dias, asistentes):
        p = Pregunta.objects.create(autor=organizador, titulo="Rodada", cuerpo="x", categoria=Categoria.RUTAS)
        r = Rodada.objects.create(pregunta=p, organizador=organizador, fecha_hora=timezone.now() + timedelta(days=dias),
                                  punto_encuentro="Parque", destino="El Retiro")
        for u in asistentes:
            Asistencia.objects.create(rodada=r, usuario=u)
        return r

    def test_rodadas_asistidas(self):
        self._rodada(self.otros[0], -1, [self.otros[0], self.otros[1], self.ana])   # cuenta
        self._rodada(self.otros[0], -1, [self.otros[0], self.ana])                  # pocos asistentes
        self._rodada(self.ana, -1, [self.ana, self.otros[1], self.otros[2]])        # la organizó ella
        self._rodada(self.otros[0], 2, [self.otros[0], self.otros[1], self.ana])    # aún no pasa
        self.assertEqual(reglas.evaluar(self.ana), 1)
        self.assertEqual(self.claves(), ["rodada"])

    def test_resenas_una_por_taller_y_con_texto(self):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        t1, t2 = [Taller.objects.create(nombre=f"T{i}", responsable="X", whatsapp="573000000000", direccion="X",
                                        barrio=barrio, activo=True) for i in range(2)]
        largo = "Me atendieron rápido, explicaron todo y el precio fue justo."
        Resena.objects.create(taller=t1, usuario=self.ana, nombre="Ana", estrellas=5, comentario=largo)
        Resena.objects.create(taller=t1, usuario=self.ana, nombre="Ana", estrellas=4, comentario=largo + " Otra vez.")
        Resena.objects.create(taller=t2, usuario=self.ana, nombre="Ana", estrellas=5, comentario="Bien")
        self.assertEqual(reglas.evaluar(self.ana), 1)

    def test_mantenimiento_al_dia_lee_el_plan(self):
        from garaje.models import LineaMoto, Mantenimiento, Moto, TareaMantenimiento
        perfil = Motociclista.objects.create(nombre="Ana", celular="573001110000", usuario=self.ana)
        moto = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre="NKD 125"), modelo=2022,
                                   km_inicial=1000, km_actual=1000)
        self.assertEqual(reglas.evaluar(self.ana), 0)  # sin registros recientes
        Mantenimiento.objects.create(moto=moto, tarea=TareaMantenimiento.objects.get(clave="aceite"), km=1000)
        vencido = SimpleNamespace(urgentes=[1], sin_registro=[], tareas=[1, 2])
        al_dia = SimpleNamespace(urgentes=[], sin_registro=[1], tareas=[1, 2])
        with mock.patch("garaje.plan.calcular_plan", return_value=vencido):
            self.assertEqual(reglas.evaluar(self.ana), 0)
        with mock.patch("garaje.plan.calcular_plan", return_value=al_dia):
            self.assertEqual(reglas.evaluar(self.ana), 1)
            self.assertEqual(reglas.evaluar(self.ana), 0)  # una vez por mes
        self.assertEqual(Logro.objects.get().referencia, timezone.localdate().strftime("%Y-%m"))


class CanjeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = _usuario("ana")
        self.perfil = Motociclista.objects.create(nombre="Ana", celular="573001110001", usuario=self.ana)
        self.cupon = Cupon.objects.create(titulo="10% en aceite", publico=False, puntos_logros=40)
        self.client.force_login(self.ana)

    def _dar_puntos(self, n):
        Logro.objects.create(usuario=self.ana, clave="aporte", referencia=f"x{n}", puntos=n)

    def test_pagina_muestra_puntos_insignias_y_cupones(self):
        self._dar_puntos(20)
        r = self.client.get(reverse("logros:mis_insignias"))
        self.assertContains(r, "Aporte útil")
        self.assertContains(r, "Canjear por 40 puntos")
        self.assertEqual(r.context["puntos"], 20)

    def test_canje_sin_puntos_suficientes_falla(self):
        self._dar_puntos(20)
        self.client.post(reverse("logros:canjear", args=[self.cupon.pk]))
        self.assertFalse(CodigoCupon.objects.exists())

    def test_canje_descuenta_puntos_y_uno_por_mes(self):
        self._dar_puntos(100)
        r = self.client.post(reverse("logros:canjear", args=[self.cupon.pk]))
        codigo = CodigoCupon.objects.get()
        self.assertRedirects(r, codigo.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(codigo.origen, CodigoCupon.Origen.LOGROS)
        self.assertEqual(reglas.puntos_disponibles(self.ana), 60)
        self.client.post(reverse("logros:canjear", args=[self.cupon.pk]))  # mismo cupón, mismo mes
        self.assertEqual(CodigoCupon.objects.count(), 1)
        self.assertEqual(Canje.objects.count(), 1)

    def test_cupon_sin_puntos_no_se_canjea(self):
        self._dar_puntos(100)
        normal = Cupon.objects.create(titulo="Normal")
        self.assertEqual(self.client.post(reverse("logros:canjear", args=[normal.pk])).status_code, 404)

    def test_etiqueta_insignias_para_perfil(self):
        from django.template import Context, Template
        self._dar_puntos(20)
        html = Template("{% load logros %}{% insignias u %}").render(Context({"u": self.ana}))
        self.assertIn("Aporte útil", html)
