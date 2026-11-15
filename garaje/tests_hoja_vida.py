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
                                        "servicios": "Cambio de aceite", "costo": "45.000", "taller_otro": "Motos Ya"})
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

    def test_tarjeta_compartir_como_la_del_codigo(self):
        self.client.post(self.url, {"accion": "compartir"})
        enlace = self.moto.enlaces_hoja_vida.get()
        r = self.client.get(self.url)
        self.assertContains(r, "Enlace activo</p>")
        self.assertNotContains(r, enlace.token[:6].upper() + "</p>")  # no parece un código para escribir
        self.assertContains(r, 'aria-label="QR de la hoja de vida"')
        self.assertContains(r, 'type="hidden" id="hv-url"')  # la URL larga ya no se ve
        self.assertContains(r, 'class="hv-desactivar">Desactivar')
        self.assertNotContains(r, 'class="campo mt-3 hv-url"')


class MantenimientoAHojaVidaTests(TestCase):
    """'Ya le hice este mantenimiento' (despiece) también queda en la hoja de vida, sin duplicarse al verificarlo."""
    setUp = HojaVidaTests.setUp

    def registrar(self, **extra):
        from .models import TareaMantenimiento
        self.tarea = TareaMantenimiento.objects.get(clave="aceite")
        datos = {"tarea": self.tarea.pk, "km": 8000, "fecha": timezone.localdate().isoformat(), **extra}
        return self.client.post(reverse("garaje:registrar_mantenimiento", args=[self.moto.pk]), datos,
                                HTTP_X_REQUESTED_WITH="fetch")

    def test_crea_registro_sin_verificar_y_enlaza(self):
        r = self.registrar(taller=self.taller.pk).json()
        self.assertTrue(r["ok"])
        self.assertEqual(r["hoja_vida"], self.url)
        reg = RegistroServicio.objects.get()
        self.assertEqual((reg.km, reg.servicios, reg.taller, reg.verificado), (8000, self.tarea.nombre, self.taller, False))
        # 1 a 1: cada mantenimiento del plan tiene exactamente un registro en la hoja de vida
        self.registrar(taller=self.taller.pk)
        self.assertEqual(RegistroServicio.objects.count(), self.moto.mantenimientos.count())
        self.assertFalse(RegistroServicio.objects.filter(mantenimiento__isnull=True).exists())

    def test_al_verificarlo_el_taller_no_queda_dos_veces(self):
        self.registrar(taller=self.taller.pk)
        cod = generar_codigo(self.moto)
        registrar_verificado(self.taller, cod.codigo, fecha=timezone.localdate(), km=8000, servicios="Aceite y filtro",
                             costo=60000)
        reg = RegistroServicio.objects.get()
        self.assertTrue(reg.verificado)
        self.assertEqual((reg.servicios, reg.costo), ("Aceite y filtro", 60000))

    def test_otro_taller_no_se_toma_como_el_mismo(self):
        self.registrar()  # "Lo hice yo"
        cod = generar_codigo(self.moto)
        registrar_verificado(self.taller, cod.codigo, fecha=timezone.localdate(), km=8000, servicios="Aceite")
        self.assertEqual(RegistroServicio.objects.filter(verificado=True).count(), 1)
        self.assertEqual(RegistroServicio.objects.count(), 2)

    def test_mostrar_mi_codigo_no_anula_el_vigente(self):
        cod = generar_codigo(self.moto)
        self.client.post(self.url, {"accion": "codigo", "solo_si_falta": "1"})
        cod.refresh_from_db()
        self.assertTrue(cod.vigente)
        self.client.post(self.url, {"accion": "codigo"})  # "Generar otro" sí lo reemplaza
        cod.refresh_from_db()
        self.assertFalse(cod.vigente)



class UnaSolaFuenteTests(TestCase):
    """Ficha/plan → hoja de vida, hoja de vida → plan, mantenimientos existentes, y el precio en Gastos sin duplicar."""
    setUp = HojaVidaTests.setUp

    def aceite(self):
        from .models import TareaMantenimiento
        return TareaMantenimiento.objects.get(clave="aceite")

    def registrar(self, **extra):
        datos = {"tarea": self.aceite().pk, "km": 8000, "fecha": timezone.localdate().isoformat(), **extra}
        return self.client.post(reverse("garaje:registrar_mantenimiento", args=[self.moto.pk]), datos,
                                HTTP_X_REQUESTED_WITH="fetch")

    def gastos(self):
        from .gastos import movimientos
        return [(m.tipo, m.valor) for m in movimientos(self.moto)]

    def test_ficha_con_taller_y_precio_llega_a_gastos_una_vez(self):
        self.assertTrue(self.registrar(taller=self.taller.pk, precio="85.000").json()["ok"])
        reg = RegistroServicio.objects.get()
        self.assertEqual((reg.costo, reg.mantenimiento.tarea, reg.verificado), (85000, self.aceite(), False))
        self.assertEqual(self.gastos(), [("servicio", 85000)])

    def test_lo_hice_yo_no_guarda_precio_y_sin_precio_no_hay_gasto(self):
        self.registrar(precio="50000")  # "Lo hice yo"
        self.registrar(taller="otro", km=7990)  # otro taller, sin precio
        self.assertEqual(RegistroServicio.objects.count(), 2)
        self.assertFalse(RegistroServicio.objects.filter(costo__isnull=False).exists())
        self.assertEqual(self.gastos(), [])

    def test_precio_invalido(self):
        r = self.registrar(taller=self.taller.pk, precio="-5")
        self.assertEqual(r.status_code, 400)
        self.assertIn("negativo", r.json()["error"])

    def test_poner_al_dia_tambien_llega(self):
        r = self.client.post(reverse("garaje:poner_al_dia", args=[self.moto.pk]),
                             {f"estado_{self.aceite().pk}": "poco"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(RegistroServicio.objects.get().mantenimiento.moto, self.moto)

    def test_hoja_de_vida_pone_al_dia_el_plan(self):
        from .plan import calcular_plan
        r = self.client.post(self.url, {"accion": "agregar", "tarea": self.aceite().pk, "fecha": timezone.localdate().isoformat(),
                                        "km": 8000, "servicios": "", "taller": self.taller.pk, "costo": "60.000"})
        self.assertRedirects(r, self.url)
        reg = RegistroServicio.objects.get()  # uno solo, enlazado
        self.assertEqual((reg.servicios, reg.costo), (self.aceite().nombre, 60000))
        self.assertEqual(self.moto.mantenimientos.get().registro_hoja, reg)
        t = next(t for t in calcular_plan(self.moto).tareas if t.tarea.clave == "aceite")
        self.assertEqual(t.estado, "ok")
        # Al borrarlo de la hoja de vida, también sale del plan
        self.client.post(self.url, {"accion": "eliminar", "registro": reg.pk})
        self.assertFalse(self.moto.mantenimientos.exists())

    def test_texto_libre_solo_en_hoja_de_vida_y_yo_sin_costo(self):
        self.client.post(self.url, {"accion": "agregar", "fecha": timezone.localdate().isoformat(), "km": 7900,
                                    "servicios": "Lavé el carburador", "costo": "30000"})
        reg = RegistroServicio.objects.get()
        self.assertIsNone(reg.costo)
        self.assertIsNone(reg.mantenimiento)
        self.assertFalse(self.moto.mantenimientos.exists())

    def test_migracion_lleva_los_existentes_sin_duplicar(self):
        from importlib import import_module
        from django.apps import apps as apps_reales
        from .models import Mantenimiento
        m = Mantenimiento.objects.create(moto=self.moto, tarea=self.aceite(), km=7000, fecha=timezone.localdate())
        RegistroServicio.objects.all().delete()  # como antes de la migración
        migracion = import_module("garaje.migrations.0020_hoja_vida_mantenimientos")
        migracion.enlazar_existentes(apps_reales, None)
        migracion.enlazar_existentes(apps_reales, None)  # dos veces: no duplica
        self.assertEqual(RegistroServicio.objects.get().mantenimiento, m)


class PendienteAVerificadoTests(TestCase):
    """Ciclo completo: registrar con taller → pendiente → el taller usa el código → el mismo registro verificado."""
    setUp = HojaVidaTests.setUp

    def test_ciclo_desde_la_ficha_con_codigo_del_aviso(self):
        from .models import TareaMantenimiento
        # 1) Al elegir el taller en el despiece se pide el código (JSON con QR); repetirlo reutiliza el mismo
        url_codigo = reverse("garaje:codigo_taller", args=[self.moto.pk])
        c1 = self.client.post(url_codigo).json()
        self.assertEqual(self.client.post(url_codigo).json()["codigo"], c1["codigo"])
        self.assertIn("<svg", c1["qr"])
        self.assertTrue(c1["vence_texto"])
        # 2) Registra el mantenimiento con ese taller → pendiente, ligado al código
        self.client.post(reverse("garaje:registrar_mantenimiento", args=[self.moto.pk]),
                         {"tarea": TareaMantenimiento.objects.get(clave="aceite").pk, "km": 8000,
                          "fecha": timezone.localdate().isoformat(), "taller": self.taller.pk},
                         HTTP_X_REQUESTED_WITH="fetch")
        reg = RegistroServicio.objects.get()
        self.assertEqual(reg.estado_verificacion, "pendiente")
        pagina = self.client.get(self.url)
        self.assertContains(pagina, 'data-origen="pendiente"')
        self.assertContains(pagina, "Pendiente · Motos El Paisa")
        RegistroServicio.objects.create(moto=self.moto, km=6000, servicios="Lavada")  # con 2+ aparecen los filtros
        self.assertContains(self.client.get(self.url), 'data-valor="pendiente"')
        # 3) El taller usa el código → ese mismo registro pasa a verificado (fecha lejana: lo encuentra por el vínculo)
        registrar_verificado(self.taller, c1["codigo"], fecha=timezone.localdate() - timedelta(days=20), km=8000,
                             servicios="Cambio de aceite")
        self.assertEqual(RegistroServicio.objects.count(), 2)  # el pendiente pasó a verificado; no se creó otro
        reg.refresh_from_db()
        self.assertEqual(reg.estado_verificacion, "verificado")
        self.assertIsNotNone(reg.mantenimiento)

    def test_mostrar_codigo_de_un_pendiente_lo_liga(self):
        reg = RegistroServicio.objects.create(moto=self.moto, km=7000, servicios="Frenos", taller=self.taller,
                                              fecha=timezone.localdate() - timedelta(days=40))
        self.client.post(self.url, {"accion": "codigo", "registro": reg.pk})
        from .models import CodigoServicio
        cod = CodigoServicio.objects.get()
        self.assertEqual(cod.registro, reg)
        registrar_verificado(self.taller, cod.codigo, fecha=timezone.localdate(), km=7000, servicios="Frenos")
        self.assertEqual(RegistroServicio.objects.get().pk, reg.pk)
        self.assertTrue(RegistroServicio.objects.get().verificado)

    def test_sin_taller_de_tallerya_es_propio(self):
        reg = RegistroServicio.objects.create(moto=self.moto, km=7000, servicios="Lavada", taller_otro="El Paisa")
        self.assertEqual(reg.estado_verificacion, "propio")

    def test_ventana_del_pendiente_liga_el_codigo_sin_recargar(self):
        from .models import CodigoServicio
        reg = RegistroServicio.objects.create(moto=self.moto, km=7000, servicios="Frenos", taller=self.taller)
        pagina = self.client.get(self.url)
        url_codigo = reverse("garaje:codigo_taller", args=[self.moto.pk])
        self.assertContains(pagina, f'data-codigo-ventana="{url_codigo}" data-registro="{reg.pk}"')
        self.assertContains(pagina, "garaje/js/codigo_taller.js")
        datos = self.client.post(url_codigo, {"registro": reg.pk}).json()
        self.assertEqual(datos["puntos"], 25)
        self.assertEqual(CodigoServicio.objects.get(codigo=datos["codigo"]).registro, reg)
        # Reutiliza el vigente; "Generar otro" (nuevo) crea otro, también ligado
        self.assertEqual(self.client.post(url_codigo, {"registro": reg.pk}).json()["codigo"], datos["codigo"])
        otro = self.client.post(url_codigo, {"registro": reg.pk, "nuevo": "1"}).json()
        self.assertNotEqual(otro["codigo"], datos["codigo"])
        self.assertEqual(CodigoServicio.objects.get(codigo=otro["codigo"]).registro, reg)

    def test_ventana_registrar_del_plan_usa_el_mismo_componente(self):
        pagina = self.client.get(self.moto.get_absolute_url())
        self.assertContains(pagina, f'data-codigo-url="{reverse("garaje:codigo_taller", args=[self.moto.pk])}"')
        self.assertContains(pagina, "garaje/js/codigo_taller.js")
        self.assertContains(pagina, 'name="precio"')
