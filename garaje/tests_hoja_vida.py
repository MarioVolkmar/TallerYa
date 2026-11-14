"""Pruebas de la hoja de vida verificada (código de un solo uso, enlace público revocable) y del QR propio."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from talleres.models import Barrio, Taller

from . import qr
from .forms_hoja_vida import ServicioTallerForm
from .hoja_vida import (CodigoInvalido, buscar_codigo, crear_enlace, generar_codigo, placa_enmascarada,
                        registrar_verificado, revocar_enlaces)
from .models import RegistroServicio
from .tests_avisos import crear_moto


def leer_qr(m):
    """Lector mínimo para la prueba: formato → quitar máscara → leer en zigzag → texto (modo byte)."""
    n = len(m)
    formato = 0
    pos = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(14 - i, 8) for i in range(9, 15)]
    for i, (x, y) in enumerate(pos):
        formato |= int(m[y][x]) << i
    formato ^= 0x5412
    mascara = (formato >> 10) & 7
    version = (n - 17) // 4
    fijo = qr._Matriz(version).fijo
    f = qr._MASCARAS[mascara]
    bits, derecha = [], n - 1
    while derecha >= 1:
        if derecha == 6:
            derecha = 5
        for vert in range(n):
            for j in range(2):
                x = derecha - j
                y = n - 1 - vert if ((derecha + 1) & 2) == 0 else vert
                if not fijo[y][x]:
                    bits.append(int(m[y][x]) ^ int(f(x, y)))
        derecha -= 2
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - 7, 8)]
    ec, grupos = qr._NIVEL_M[version]
    largos = [d for k, d in grupos for _ in range(k)]
    datos = [[] for _ in largos]
    k = 0
    for i in range(max(largos)):
        for b, largo in enumerate(largos):
            if i < largo:
                datos[b].append(cw[k])
                k += 1
    for b, largo in enumerate(largos):  # la corrección de cada bloque debe cuadrar
        corr = [cw[sum(largos) + i * len(largos) + b] for i in range(ec)]
        assert qr._resto(datos[b], qr._divisor(ec)) == corr
    flujo = "".join(f"{c:08b}" for bloque in datos for c in bloque)
    assert flujo[:4] == "0100"
    ancho = 8 if version < 10 else 16
    largo = int(flujo[4:4 + ancho], 2)
    inicio = 4 + ancho
    return bytes(int(flujo[inicio + 8 * i:inicio + 8 * i + 8], 2) for i in range(largo)).decode("utf-8")


class QrTests(TestCase):
    def test_codifica_y_se_lee(self):
        for texto in ("HOLA", "https://tallerya.co/hoja-de-vida/abcdefghijklmnopqrstuvwxyz012345/",
                      "ñandú " * 20, "x" * 200):
            self.assertEqual(leer_qr(qr.matriz(texto)), texto)

    def test_vectores_de_la_norma(self):
        # Corrección Reed-Solomon del ejemplo clásico "HELLO WORLD" 1-M.
        datos = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17]
        self.assertEqual(qr._resto(datos, qr._divisor(10)), [196, 35, 39, 119, 235, 215, 231, 226, 93, 23])
        self.assertIn("<svg", qr.svg("hola"))


class HojaVidaTests(TestCase):
    def setUp(self):
        self.moto = crear_moto(placa="ABC12D", km_actual=8000)
        cuenta = get_user_model().objects.create_user("taller@x.com", "taller@x.com", "x")
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        self.taller = Taller.objects.create(nombre="Motos El Paisa", responsable="X", whatsapp="573001234567",
                                            direccion="Cl 1", barrio=barrio, usuario=cuenta, activo=True)
        self.client.force_login(self.moto.motociclista.usuario)
        self.url = reverse("garaje:hoja_vida", args=[self.moto.pk])

    def test_registro_propio_queda_sin_verificar(self):
        r = self.client.post(self.url, {"accion": "agregar", "fecha": timezone.localdate().isoformat(), "km": 7900,
                                        "servicios": "Cambio de aceite", "costo": 45000})
        self.assertRedirects(r, self.url)
        registro = RegistroServicio.objects.get()
        self.assertFalse(registro.verificado)
        self.assertEqual(registro.costo, 45000)
        # verificado no se puede forzar desde el formulario
        self.client.post(self.url, {"accion": "agregar", "fecha": timezone.localdate().isoformat(), "km": 7900,
                                    "servicios": "Truco", "verificado": "on"})
        self.assertFalse(RegistroServicio.objects.filter(verificado=True).exists())

    def test_codigo_de_un_solo_uso_y_caduca(self):
        codigo = generar_codigo(self.moto)
        self.assertEqual(len(codigo.codigo), 6)
        self.assertEqual(buscar_codigo(codigo.codigo.lower()), codigo)
        registro = registrar_verificado(self.taller, codigo.codigo, fecha=timezone.localdate(), km=8500,
                                        servicios="Kit de arrastre", costo=320000)
        self.assertTrue(registro.verificado)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.km_actual, 8500)
        with self.assertRaises(CodigoInvalido):  # ya se usó
            registrar_verificado(self.taller, codigo.codigo, fecha=timezone.localdate(), km=8500, servicios="x")
        viejo = generar_codigo(self.moto)
        viejo.vence = timezone.now() - timedelta(minutes=1)
        viejo.save()
        self.assertIsNone(buscar_codigo(viejo.codigo))

    def test_generar_otro_anula_el_anterior(self):
        primero = generar_codigo(self.moto)
        generar_codigo(self.moto)
        self.assertIsNone(buscar_codigo(primero.codigo))

    def test_formulario_del_taller(self):
        codigo = generar_codigo(self.moto)
        datos = {"codigo": codigo.codigo, "fecha": timezone.localdate().isoformat(), "km": 8100, "servicios": "Frenos"}
        malo = ServicioTallerForm({**datos, "codigo": "ZZZZZZ"}, taller=self.taller)
        self.assertFalse(malo.is_valid())
        form = ServicioTallerForm(datos, taller=self.taller)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.codigo_obj.moto, self.moto)
        self.assertTrue(form.guardar().verificado)

    def test_pagina_muestra_codigo_qr_y_sello(self):
        self.client.post(self.url, {"accion": "codigo"})
        codigo = self.moto.codigos_servicio.get()
        registrar_verificado(self.taller, codigo.codigo, fecha=timezone.localdate(), km=8100, servicios="Frenos")
        self.client.post(self.url, {"accion": "codigo"})
        r = self.client.get(self.url)
        self.assertContains(r, "Hecho en Motos El Paisa")
        self.assertContains(r, 'aria-label="QR del código para el taller"')
        self.assertContains(r, self.moto.codigos_servicio.order_by("-creado").first().codigo)

    def test_no_se_borra_lo_verificado(self):
        codigo = generar_codigo(self.moto)
        verificado = registrar_verificado(self.taller, codigo.codigo, fecha=timezone.localdate(), km=8100, servicios="F")
        self.client.post(self.url, {"accion": "eliminar", "registro": verificado.pk})
        self.assertTrue(RegistroServicio.objects.filter(pk=verificado.pk).exists())

    def test_enlace_publico_sin_nombre_placa_enmascarada_y_revocable(self):
        self.assertEqual(placa_enmascarada("ABC12D"), "A••••D")
        enlace = crear_enlace(self.moto)
        self.assertGreaterEqual(len(enlace.token), 30)
        self.client.logout()
        r = self.client.get(enlace.get_absolute_url())
        self.assertContains(r, "A••••D")
        self.assertNotContains(r, "ABC12D")
        self.assertNotContains(r, "Ana")
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        revocar_enlaces(self.moto)
        self.assertEqual(self.client.get(enlace.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(reverse("garaje:hoja_vida_publica", args=["adivinado"])).status_code, 404)

    def test_hoja_ajena_no_se_ve(self):
        otra = crear_moto("b@x.com", "573009")
        self.assertEqual(self.client.get(reverse("garaje:hoja_vida", args=[otra.pk])).status_code, 404)

    def test_qr_del_codigo_lleva_al_taller(self):
        codigo = generar_codigo(self.moto)
        url = reverse("garaje:servicio_codigo", args=[codigo.codigo])
        self.assertRedirects(self.client.get(url), reverse("garaje:garaje"), fetch_redirect_response=False)
        self.client.force_login(self.taller.usuario)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(codigo.codigo, r["Location"])
