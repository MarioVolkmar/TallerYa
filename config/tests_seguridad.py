"""Pruebas de autorización de todo el sitio (skill revisar-seguridad).

1. IDOR: con dos moteros (A y B) y dos talleres (TA y TB), cada URL con <pk> se pide con el objeto de A (o del taller TA)
   siendo B / TB, por GET y por POST. Nunca debe responder 200 ni cambiar nada en la base.
2. Barrido anónimo: toda URL sin parámetros se pide sin sesión. Las que respondan 200 deben estar en PUBLICAS; si aparece
   una nueva, la prueba falla para obligar a decidir si es pública a propósito.
3. Panel: /consola/, administración de talleres y acciones solo para el equipo (staff).

Si agregas una vista con <pk>, súmala a CASOS. Si agregas una página pública, súmala a PUBLICAS.
"""
from datetime import date

from django.utils import timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver

from cupones.models import Cupon
from foro.models import Pregunta, Respuesta
from garaje.models import Moto, Motociclista, ServicioTaller
from notificaciones.models import Notificacion
from talleres.models import Barrio, FotoTaller, Resena, SolicitudCita, Taller
from tramites.models import PedidoSoat

User = get_user_model()

# Páginas sin parámetros que cualquiera puede ver sin sesión (revisadas a mano).
PUBLICAS = {
    "", "ayuda/catalogo.json", "canjear/", "cuenta/entrar/", "cuenta/recuperar/", "cuenta/recuperar/enviado/",
    "cuenta/recuperar/listo/", "cuenta/registro/", "cupones/", "diagnostico/", "emergencias/", "foro/", "foro/rodadas/",
    "manifest.webmanifest", "noticias/", "plus/", "robots.txt", "sin-conexion/", "sitemap.xml", "soat/", "sw.js",
    "talleres/", "tecnomecanica/",
}


def _rutas(patrones=None, prefijo=""):
    for p in patrones if patrones is not None else get_resolver().url_patterns:
        if isinstance(p, URLResolver):
            yield from _rutas(p.url_patterns, prefijo + str(p.pattern))
        elif isinstance(p, URLPattern):
            yield prefijo + str(p.pattern), p


class Escenario(TestCase):
    @classmethod
    def setUpTestData(cls):
        barrio = Barrio.objects.get_or_create(nombre="Belén")[0]
        cls.ua = User.objects.create_user("a@x.co", "a@x.co", "clave-larga-a1")
        cls.ub = User.objects.create_user("b@x.co", "b@x.co", "clave-larga-b1")
        cls.uta = User.objects.create_user("ta@x.co", "ta@x.co", "clave-larga-ta")
        cls.utb = User.objects.create_user("tb@x.co", "tb@x.co", "clave-larga-tb")
        cls.staff = User.objects.create_user("st@x.co", "st@x.co", "clave-larga-st", is_staff=True)
        ma = Motociclista.objects.create(usuario=cls.ua, nombre="Ana", celular="573001110001")
        mb = Motociclista.objects.create(usuario=cls.ub, nombre="Beto", celular="573001110002")
        datos = {"marca_otra": "Yamaha", "linea_otra": "NMAX", "tipo_otra": "scooter", "modelo": 2022,
                 "km_inicial": 1000, "km_actual": 5000}
        cls.moto_a = Moto.objects.create(motociclista=ma, placa="AAA11A", **datos)
        cls.moto_b = Moto.objects.create(motociclista=mb, placa="BBB22B", **datos)
        cls.taller_a = Taller.objects.create(nombre="Taller A", responsable="A", whatsapp="573001112233",
                                             direccion="X", barrio=barrio, activo=True, usuario=cls.uta)
        cls.taller_b = Taller.objects.create(nombre="Taller B", responsable="B", whatsapp="573001112244",
                                             direccion="Y", barrio=barrio, activo=True, usuario=cls.utb)
        cls.taller_inactivo = Taller.objects.create(nombre="Taller C", responsable="C", whatsapp="573001112255",
                                                    direccion="Z", barrio=barrio, activo=False)
        cls.cita = SolicitudCita.objects.create(taller=cls.taller_a, nombre="Ana", telefono="3001110001", moto="NMAX",
                                                fecha_preferida=date.today(), usuario=cls.ua)
        cls.resena = Resena.objects.create(taller=cls.taller_a, usuario=cls.ua, nombre="Ana", estrellas=5, comentario="ok")
        cls.cupon = Cupon.objects.create(taller=cls.taller_a, titulo="10 %")
        cls.foto = FotoTaller.objects.create(taller=cls.taller_a)
        cls.servicio = ServicioTaller.objects.create(taller=cls.taller_a, moto=cls.moto_a, km=5000, origen="cita")
        cls.pedido = PedidoSoat.objects.create(moto=cls.moto_a, placa="AAA11A", linea="NMAX", cilindraje=155,
                                               categoria="moto_100_200", acepta_datos_en=timezone.now())
        cls.notif = Notificacion.objects.create(usuario=cls.ua, titulo="Hola", url="/", clave="x")
        cls.pregunta = Pregunta.objects.create(autor=cls.ua, titulo="¿Aceite?", cuerpo="Cuál uso")
        cls.respuesta = Respuesta.objects.create(pregunta=cls.pregunta, autor=cls.ua, cuerpo="Este")

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # los frenos de intentos viven en la caché: que ninguna prueba herede contadores de otra
        self.addCleanup(cache.clear)

    def _foto_base(self):
        """Estado de lo que un intruso podría tocar: si cambia algo, hubo escritura no autorizada."""
        modelos = [(Moto, self.moto_a.pk), (SolicitudCita, self.cita.pk), (Resena, self.resena.pk),
                   (Cupon, self.cupon.pk), (Taller, self.taller_a.pk), (Taller, self.taller_inactivo.pk),
                   (ServicioTaller, self.servicio.pk), (PedidoSoat, self.pedido.pk), (Notificacion, self.notif.pk),
                   (Pregunta, self.pregunta.pk), (Respuesta, self.respuesta.pk), (User, self.ua.pk)]
        foto = {}
        for modelo, pk in modelos:
            fila = modelo.objects.filter(pk=pk).values().first()
            if fila:
                for volatil in ("last_login", "vistas", "actualizado"):
                    fila.pop(volatil, None)
            foto[(modelo.__name__, pk)] = fila
        foto["fotos"] = FotoTaller.objects.filter(taller=self.taller_a).count()
        return foto


class IdorTests(Escenario):
    """B (motero) y TB (otro taller) intentan ver o cambiar lo de A y del taller A."""

    def _casos(self):
        """Rutas directas (no nombres) para que un cambio de nombre no esconda una vista."""
        m, c, p, r = self.moto_a.pk, self.cita.pk, self.pregunta.pk, self.respuesta.pk
        motero = [f"/garaje/{m}/{x}" for x in ("", "editar/", "eliminar/", "documento/soat/", "documento/soat/subir/",
                                               "km/", "al-dia/", "ajustar/", "personalizar/", "pico-y-placa/",
                                               "vista-3d/", "despiece.json", "mantenimiento/", "hoja-de-vida/",
                                               "codigo-taller/", "gastos/")]
        motero += [f"/bienvenida/{m}/", f"/bienvenida/{m}/listo/", f"/garaje/servicio-taller/{self.servicio.pk}/",
                   f"/cuenta/citas/{c}/", f"/cuenta/citas/{c}/cancelar/", f"/cuenta/citas/{c}/calendario.ics",
                   f"/notificaciones/{self.notif.pk}/ir/", f"/soat/{m}/pedir/",
                   f"/soat/pedido/{self.pedido.pk}/pago-de-prueba/", f"/soat/pedido/{self.pedido.pk}/poliza/",
                   f"/soat/pedido/{self.pedido.pk}/tarjeta/", f"/foro/editar/pregunta/{p}/", f"/foro/eliminar/pregunta/{p}/",
                   f"/foro/editar/respuesta/{r}/", f"/foro/eliminar/respuesta/{r}/", f"/foro/respuesta/{r}/mejor/"]
        taller = [f"/mi-taller/cita/{c}/servicio/", f"/mi-taller/cita/{c}/estado/", f"/mi-taller/cita/{c}/reprogramar/",
                  f"/mi-taller/resena/{self.resena.pk}/responder/", f"/mi-taller/cupones/{self.cupon.pk}/",
                  f"/mi-taller/cupones/{self.cupon.pk}/pausar/", f"/mi-taller/foto/{self.foto.pk}/eliminar/"]
        solo_equipo = [f"/cuenta/administracion/taller/{self.taller_inactivo.pk}/aprobar/",
                       f"/consola/accion/taller_activo/{self.taller_inactivo.pk}/"]
        return motero, taller, solo_equipo

    def _intentar(self, intruso, casos):
        fallas = []
        for url in casos:
            if self.client.get(url).status_code == 404 and not self._existe(url):
                fallas.append(f"{url}: la ruta ya no existe; actualizar CASOS")
                continue
            for metodo in ("get", "post"):
                r = getattr(self.client, metodo)(url, {"estado": "cancelada", "valor": "1", "texto": "x", "km": "9",
                                                         "cuerpo": "hackeado", "titulo": "hackeado"})
                if r.status_code == 200:
                    fallas.append(f"{metodo.upper()} {url} → {r.status_code} {r.get('Location', '')}")
        return fallas

    def _revisar(self, intruso, casos):
        antes = self._foto_base()
        self.client.force_login(intruso)
        fallas = self._intentar(intruso, casos)
        self.assertEqual(self._foto_base(), antes, "Un intruso cambió datos ajenos")
        return fallas

    def test_otro_motero_no_ve_ni_cambia_lo_ajeno(self):
        motero, taller, equipo = self._casos()
        fallas = self._revisar(self.ub, motero + taller + equipo)
        self.assertEqual(self._sin_redirecciones_inocuas(fallas), [])

    def test_otro_taller_no_ve_ni_cambia_lo_ajeno(self):
        motero, taller, equipo = self._casos()
        fallas = self._revisar(self.utb, motero + taller + equipo)
        self.assertEqual(self._sin_redirecciones_inocuas(fallas), [])

    def test_anonimo_no_ve_ni_cambia_nada_privado(self):
        motero, taller, equipo = self._casos()
        antes = self._foto_base()
        fallas = self._intentar(None, motero + taller + equipo)
        self.assertEqual(self._foto_base(), antes)
        self.assertEqual(self._sin_redirecciones_inocuas(fallas), [])

    def test_el_dueno_si_entra(self):
        """Control: la prueba sirve solo si el dueño legítimo sí recibe 200 (si no, todo daría 404 por error)."""
        self.client.force_login(self.ua)
        for url in (f"/garaje/{self.moto_a.pk}/", f"/cuenta/citas/{self.cita.pk}/", f"/foro/editar/pregunta/{self.pregunta.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.force_login(self.uta)
        self.assertEqual(self.client.get(f"/mi-taller/cupones/{self.cupon.pk}/").status_code, 200)

    @staticmethod
    def _existe(url):
        from django.urls import Resolver404, resolve
        try:
            resolve(url)
            return True
        except Resolver404:
            return False

    @staticmethod
    def _sin_redirecciones_inocuas(fallas):
        """Solo cuentan los 200: un 302 sin cambios en la base (lo comprueba _foto_base) es un rechazo con mensaje."""
        return fallas


class BarridoAnonimoTests(Escenario):
    def test_paginas_sin_parametros_que_responden_200_sin_sesion(self):
        nuevas = []
        for ruta, patron in _rutas():
            if "<" in ruta or ruta.startswith(("admin/", "^media", "tareas/")) or "(?P" in ruta:
                continue
            r = self.client.get("/" + ruta)
            if r.status_code == 200 and ruta not in PUBLICAS:
                nuevas.append(ruta)
        self.assertEqual(nuevas, [], "Páginas que responden 200 sin sesión y no están en PUBLICAS: revisar")


class PanelTests(Escenario):
    def test_consola_solo_equipo(self):
        for intruso in (self.ub, self.uta):
            self.client.force_login(intruso)
            self.assertEqual(self.client.get("/consola/").status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get("/consola/").status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/consola/").status_code, 200)


class ArreglosRevisionTests(Escenario):
    """Arreglos de la revisión del 17-nov-2026 (informes_noche/revision-seguridad-velocidad.md)."""

    def test_galeria_rechaza_html_disfrazado_de_imagen(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.uta)
        falso = SimpleUploadedFile("hola.html", b"<script>alert(1)</script>", content_type="image/png")
        r = self.client.post("/mi-taller/perfil/", {"galeria": [falso]})
        self.assertContains(r, "no se subió")
        self.assertEqual(FotoTaller.objects.filter(taller=self.taller_a).count(), 1)

    def test_galeria_acepta_png_real_y_lo_renombra(self):
        import io
        from PIL import Image
        from talleres import subidas
        from django.core.files.uploadedfile import SimpleUploadedFile
        buf = io.BytesIO()
        Image.new("RGB", (4, 4)).save(buf, "PNG")
        f = SimpleUploadedFile("x.html", buf.getvalue(), content_type="text/html")
        self.assertEqual(subidas.tipo_real(f, subidas.IMAGENES), "png")
        self.assertTrue(subidas.renombrar(f, "png").name.endswith(".png"))
        self.assertIsNone(subidas.tipo_real(SimpleUploadedFile("v.mp4", b"<html>" * 4), subidas.VIDEOS))

    def test_media_solo_entrega_imagenes_y_videos(self):
        import tempfile
        from pathlib import Path
        from django.test import override_settings
        carpeta = tempfile.mkdtemp()
        Path(carpeta, "malo.html").write_text("<script>alert(1)</script>")
        Path(carpeta, "bien.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        with override_settings(MEDIA_ROOT=carpeta):
            self.assertEqual(self.client.get("/media/malo.html").status_code, 404)
            self.assertEqual(self.client.get("/media/malo.HTML").status_code, 404)
            r = self.client.get("/media/bien.png")
            self.assertEqual(r.status_code, 200)
            self.assertIn("sandbox", r["Content-Security-Policy"])

    def test_cabeceras_csp_y_permisos(self):
        r = self.client.get("/")
        self.assertIn("object-src 'none'", r["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])
        self.assertIn("camera=(self)", r["Permissions-Policy"])

    def test_registro_con_freno_por_ip(self):
        from cuentas.views import REGISTRO_MAX_POR_HORA
        for _ in range(REGISTRO_MAX_POR_HORA):
            self.assertEqual(self.client.post("/cuenta/registro/", {"email": "a@x.co"}).status_code, 200)
        r = self.client.post("/cuenta/registro/", {"email": "a@x.co"})
        self.assertEqual(r.status_code, 302)

    def test_vista_previa_del_canje_con_freno(self):
        from cupones.views import MAX_INTENTOS_CANJE
        for i in range(MAX_INTENTOS_CANJE):
            self.client.get("/canjear/", {"codigo": f"TY-ZZZZ{i:02d}"})
        r = self.client.get("/canjear/", {"codigo": "TY-ZZZZ99"})
        self.assertContains(r, "Demasiados intentos")

    def test_pago_de_prueba_del_soat_apagado_en_produccion(self):
        from django.test import override_settings
        from tramites.models import PedidoSoat
        PedidoSoat.objects.filter(pk=self.pedido.pk).update(estado=PedidoSoat.Estado.LISTA_PAGAR)
        self.client.force_login(self.ua)
        with override_settings(SOAT_PAGO_SIMULADO=False):
            self.client.post(f"/soat/pedido/{self.pedido.pk}/pago-de-prueba/")
        self.assertEqual(PedidoSoat.objects.get(pk=self.pedido.pk).estado, PedidoSoat.Estado.LISTA_PAGAR)

    def test_login_del_admin_con_freno(self):
        from cuentas.forms import FrenoIntentosMixin
        for _ in range(FrenoIntentosMixin.MAX_FALLOS_CORREO):
            self.client.post("/admin/login/", {"username": "st@x.co", "password": "mala"})
        r = self.client.post("/admin/login/", {"username": "st@x.co", "password": "clave-larga-st"})
        self.assertContains(r, "Demasiados intentos")

    def test_citas_anonimas_con_mi_celular_no_salen_en_mi_cuenta(self):
        """El celular no se verifica: una cita anónima con el mismo número no prueba que sea de esta persona."""
        SolicitudCita.objects.create(taller=self.taller_b, nombre="Otra persona", telefono="3001110002", moto="Pulsar",
                                     fecha_preferida=date.today())
        SolicitudCita.objects.create(taller=self.taller_b, nombre="Beto", telefono="3001110002", moto="NMAX",
                                     fecha_preferida=date.today(), usuario=self.ub)
        from cuentas.views import historial_servicios
        citas = [e for e in historial_servicios(self.ub.motociclista) if e["tipo"] == "cita"]
        self.assertEqual(len(citas), 1)
