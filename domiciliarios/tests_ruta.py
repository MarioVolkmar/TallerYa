"""TallerYa Ruta integrado a la página: verificación de domiciliario (flujo, permisos, borrado, renovación), moto de
trabajo, registro, avisos, cupones y bandera apagada."""
import io
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cupones.models import Cupon, Motociclista
from garaje.models import LineaMoto, Moto
from garaje.plan import calcular_plan
from garaje.utiles_pruebas import usar_intervalos_generales
from notificaciones.models import Notificacion

from . import verificacion as verif
from .models import Jornada, PerfilDomiciliario, Verificacion

User = get_user_model()


def imagen(nombre="foto.png", formato="PNG"):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 80, 40)).save(buf, formato)
    return SimpleUploadedFile(nombre, buf.getvalue(), content_type="image/png")


@override_settings(DOMICILIARIOS_ACTIVO=True)
class Base(TestCase):
    def setUp(self):
        self.privado = tempfile.mkdtemp()
        ajuste = override_settings(PRIVADO_ROOT=Path(self.privado))
        ajuste.enable()
        self.addCleanup(ajuste.disable)
        usar_intervalos_generales(self)
        self.usuario = User.objects.create_user("ana@x.com", "ana@x.com", "x", first_name="Ana")
        self.motero = Motociclista.objects.create(nombre="Ana Ruiz", celular="573001112222", usuario=self.usuario)
        self.linea = LineaMoto.objects.get(nombre="NKD 125")
        self.moto = Moto.objects.create(motociclista=self.motero, linea=self.linea, modelo=2022, km_inicial=10000,
                                        km_actual=10000, placa="ABC12D")
        self.perfil = PerfilDomiciliario.objects.create(motociclista=self.motero, moto=self.moto, km_semana=1200)
        self.client.force_login(self.usuario)

    def enviar(self, **extra):
        datos = {"plataforma": "rappi", "moto": self.moto.pk, "captura": imagen(), "foto_moto": imagen(), "autorizo": "on",
                 **extra}
        return self.client.post(reverse("domiciliarios:verificacion"), datos)

    def staff(self):
        return User.objects.create_user("admin@x.com", "admin@x.com", "x", is_staff=True)

    def archivos(self):
        return [p for p in Path(self.privado).rglob("*") if p.is_file()]


class FlujoVerificacionTests(Base):
    def test_sube_y_queda_pendiente_en_privado_con_nombre_aleatorio(self):
        r = self.enviar(foto_moto=imagen("mi moto placa ABC12D.png"))
        self.assertEqual(r.status_code, 302)
        v = Verificacion.objects.get()
        self.assertEqual(v.estado, Verificacion.Estado.PENDIENTE)
        self.assertIsNotNone(v.autorizacion)
        self.assertEqual(len(self.archivos()), 2)
        self.assertTrue(v.foto_moto.name.startswith("verificacion_ruta/") and "ABC12D" not in v.foto_moto.name)
        self.assertTrue(v.foto_moto.name.endswith(".jpg"))
        self.assertNotIn("media", str(self.archivos()[0]))
        self.assertContains(self.client.get(reverse("domiciliarios:verificacion")), "En revisión")

    def test_sin_autorizacion_no_recibe_nada(self):
        r = self.client.post(reverse("domiciliarios:verificacion"), {"plataforma": "rappi", "moto": self.moto.pk,
                                                                     "captura": imagen(), "foto_moto": imagen()})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Marca la autorización")
        self.assertFalse(Verificacion.objects.exists())
        self.assertEqual(self.archivos(), [])

    def test_solo_imagenes_de_menos_de_5_mb(self):
        falsa = SimpleUploadedFile("perfil.png", b"<html><script>alert(1)</script></html>", content_type="image/png")
        self.assertContains(self.enviar(captura=falsa), "Sube una foto (JPG, PNG o WebP)")
        grande = SimpleUploadedFile("g.png", b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024), content_type="image/png")
        self.assertContains(self.enviar(captura=grande), "menos de 5 MB")
        self.assertFalse(Verificacion.objects.exists())

    def test_las_dos_fotos_son_obligatorias(self):
        r = self.enviar(foto_moto="")
        self.assertContains(r, "Falta la foto de tu moto con la placa")
        r = self.enviar(captura="")
        self.assertContains(r, "Falta el pantallazo de tu perfil")
        self.assertFalse(Verificacion.objects.exists())

    def test_se_quita_el_exif(self):
        from PIL import Image
        buf = io.BytesIO()
        exif = Image.Exif()
        exif[0x010F] = "MarcaCelular"  # Make
        exif[0x0110] = "ModeloSecreto"  # Model
        Image.new("RGB", (50, 40), (10, 120, 200)).save(buf, "JPEG", exif=exif.tobytes())
        self.assertIn(b"ModeloSecreto", buf.getvalue())
        self.enviar(captura=SimpleUploadedFile("c.jpg", buf.getvalue(), content_type="image/jpeg"))
        v = Verificacion.objects.get()
        with v.captura.open("rb") as f:
            datos = f.read()
        self.assertNotIn(b"ModeloSecreto", datos)
        self.assertNotIn(b"Exif", datos[:200])

    def test_moto_ajena_no_pasa(self):
        otro = Motociclista.objects.create(nombre="Otro", celular="573009990000")
        ajena = Moto.objects.create(motociclista=otro, linea=self.linea, modelo=2020, km_inicial=1, km_actual=1, placa="ZZZ99Z")
        r = self.enviar(moto=ajena.pk)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Verificacion.objects.exists())

    def test_nunca_pide_contrasenas(self):
        r = self.client.get(reverse("domiciliarios:verificacion"))
        self.assertContains(r, "nunca te las pedimos")
        self.assertNotContains(r, 'type="password"')

    def test_aprobar_desde_consola_borra_fotos_y_avisa(self):
        self.enviar()
        v = Verificacion.objects.get()
        admin = self.staff()
        self.client.force_login(admin)
        r = self.client.post(reverse("consola:accion", args=["ruta.aprobar", v.pk]))
        self.assertEqual(r.status_code, 302)
        v.refresh_from_db()
        self.assertEqual((v.estado, v.revisado_por), (Verificacion.Estado.APROBADA, admin))
        self.assertEqual(v.vence, timezone.localdate() + timedelta(days=182))
        self.assertFalse(v.captura or v.foto_moto)
        self.assertEqual(self.archivos(), [])
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, clave__contains=":aprobada").exists())
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse("domiciliarios:panel")), "Domiciliario verificado")

    def test_rechazar_pide_motivo_borra_fotos_y_avisa(self):
        self.enviar()
        v = Verificacion.objects.get()
        self.client.force_login(self.staff())
        self.client.post(reverse("consola:accion", args=["ruta.rechazar", v.pk]), {"valor": ""})
        v.refresh_from_db()
        self.assertEqual(v.estado, Verificacion.Estado.PENDIENTE)  # sin motivo no se rechaza
        self.client.post(reverse("consola:accion", args=["ruta.rechazar", v.pk]), {"valor": "No se ve el nombre"})
        v.refresh_from_db()
        self.assertEqual((v.estado, v.motivo), (Verificacion.Estado.RECHAZADA, "No se ve el nombre"))
        self.assertEqual(self.archivos(), [])
        self.assertTrue(Notificacion.objects.filter(usuario=self.usuario, clave__contains=":rechazada").exists())
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse("domiciliarios:verificacion")), "No se ve el nombre")

    def test_retirar_solicitud_borra_fotos(self):
        self.enviar()
        self.client.post(reverse("domiciliarios:cancelar_verificacion"))
        self.assertFalse(Verificacion.objects.exists())
        self.assertEqual(self.archivos(), [])

    def test_cola_en_la_consola(self):
        self.enviar()
        self.client.force_login(self.staff())
        r = self.client.get(reverse("consola:inicio") + "?seccion=domiciliarios")
        self.assertContains(r, "Ana Ruiz")
        self.assertContains(r, "Por revisar")
        self.assertContains(r, "Placa en su garaje")
        self.assertContains(r, "ABC12D")
        self.assertContains(r, "/foto_moto/")


class PermisosFotosTests(Base):
    def setUp(self):
        super().setUp()
        self.enviar()
        self.v = Verificacion.objects.get()
        self.url = reverse("domiciliarios:verificacion_foto", args=[self.v.pk, "captura"])

    def test_el_dueno_y_el_staff_la_ven(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/jpeg")  # se recodifica al subir
        self.assertIn("no-store", r["Cache-Control"])
        r.close()
        self.client.force_login(self.staff())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        r.close()

    def test_nadie_mas_la_ve(self):
        otro = User.objects.create_user("b@x.com", "b@x.com", "x")
        Motociclista.objects.create(nombre="B", celular="573001113333", usuario=otro)
        self.client.force_login(otro)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)  # pide entrar
        self.assertEqual(self.client.get(reverse("domiciliarios:verificacion_foto", args=[self.v.pk, "otra"])).status_code, 302)

    def test_no_staff_no_entra_a_la_consola_ni_decide(self):
        self.assertEqual(self.client.get(reverse("consola:inicio") + "?seccion=domiciliarios").status_code, 403)
        self.assertEqual(self.client.post(reverse("consola:accion", args=["ruta.aprobar", self.v.pk])).status_code, 403)
        self.v.refresh_from_db()
        self.assertEqual(self.v.estado, Verificacion.Estado.PENDIENTE)

    def test_no_se_sirve_por_media(self):
        self.assertEqual(self.client.get("/media/" + self.v.captura.name).status_code, 404)


class VigenciaTests(Base):
    def aprobada(self, vence):
        return Verificacion.objects.create(perfil=self.perfil, plataforma="didi", autorizacion=timezone.now(),
                                           estado=Verificacion.Estado.APROBADA, vence=vence)

    def jornadas(self, dias, km_dia):
        hoy = timezone.localdate()
        km = 10000
        for atras in range(dias, -1, -1):
            km += km_dia
            Jornada.objects.create(perfil=self.perfil, fecha=hoy - timedelta(days=atras), ingreso=90000, km_fin=km)

    def test_se_renueva_sola_con_km_altos_y_constantes(self):
        v = self.aprobada(timezone.localdate() - timedelta(days=1))
        self.jornadas(20, 120)
        call_command("revisar_verificaciones", stdout=io.StringIO())
        v.refresh_from_db()
        self.assertEqual(v.estado, Verificacion.Estado.APROBADA)
        self.assertEqual(v.renovaciones, 1)
        self.assertGreater(v.vence, timezone.localdate() + timedelta(days=150))
        self.assertTrue(Notificacion.objects.filter(clave__contains=":renovada").exists())

    def test_sin_jornadas_suficientes_vence_y_pide_foto(self):
        v = self.aprobada(timezone.localdate() - timedelta(days=1))
        self.jornadas(20, 40)  # muchas jornadas, pero pocos km
        call_command("revisar_verificaciones", stdout=io.StringIO())
        v.refresh_from_db()
        self.assertEqual(v.estado, Verificacion.Estado.VENCIDA)
        self.assertTrue(Notificacion.objects.filter(clave__contains=":vencida").exists())
        self.assertContains(self.client.get(reverse("domiciliarios:verificacion")), "venció")

    @override_settings(RUTA_RENOVAR_DIAS=5, RUTA_RENOVAR_KM_DIA=30)
    def test_umbral_en_settings(self):
        self.jornadas(6, 40)
        self.assertTrue(verif.renovable(self.perfil))

    def test_vigente_no_se_toca(self):
        v = self.aprobada(timezone.localdate() + timedelta(days=10))
        verif.revisar_vencimientos()
        v.refresh_from_db()
        self.assertEqual((v.estado, v.renovaciones), (Verificacion.Estado.APROBADA, 0))


class MotoDeTrabajoTests(Base):
    def test_interruptor_y_plan_intensivo(self):
        self.perfil.delete()
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, "La uso para trabajar")
        self.assertNotContains(r, "data-dm-ruta")
        self.assertFalse(getattr(calcular_plan(Moto.objects.get(pk=self.moto.pk)), "de_trabajo", False))
        self.client.post(reverse("domiciliarios:moto_trabajo", args=[self.moto.pk]), {"valor": "1"})
        perfil = PerfilDomiciliario.objects.get(motociclista=self.motero)
        self.assertEqual(perfil.moto, self.moto)
        self.assertTrue(calcular_plan(Moto.objects.get(pk=self.moto.pk)).de_trabajo)
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, "data-dm-ruta")
        self.assertContains(r, "Cerrar jornada")
        self.assertContains(r, "Moto de trabajo")
        html = r.content.decode()
        # Discreta: la moto (3D) va primero; la franja de Ruta vive dentro de la agenda
        self.assertLess(html.index('id="visor"'), html.index("data-dm-ruta"))
        self.assertLess(html.index('id="plan-cuerpo"'), html.index("data-dm-ruta"))
        self.client.post(reverse("domiciliarios:moto_trabajo", args=[self.moto.pk]), {"valor": "0"})
        self.assertIsNone(PerfilDomiciliario.objects.get(pk=perfil.pk).moto)

    def test_no_puede_marcar_moto_ajena(self):
        otro = Motociclista.objects.create(nombre="Otro", celular="573009990001")
        ajena = Moto.objects.create(motociclista=otro, linea=self.linea, modelo=2020, km_inicial=1, km_actual=1)
        r = self.client.post(reverse("domiciliarios:moto_trabajo", args=[ajena.pk]), {"valor": "1"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(PerfilDomiciliario.objects.get(pk=self.perfil.pk).moto, self.moto)

    def test_usa_los_km_dia_reales(self):
        from garaje.models import LecturaKm
        hoy = timezone.localdate()
        for i, atras in enumerate(range(14, -1, -1)):
            LecturaKm.objects.create(moto=self.moto, km=10000 + i * 150, fecha=hoy - timedelta(days=atras))
        plan = calcular_plan(Moto.objects.get(pk=self.moto.pk))
        self.assertAlmostEqual(plan.km_por_dia, 150, delta=1)  # no los 1200/7 declarados

    def test_avisos_de_mantenimiento_en_dias(self):
        from notificaciones.servicios import generar_para
        generar_para(self.usuario)
        textos = list(Notificacion.objects.filter(usuario=self.usuario, clave__startswith="plan:").values_list("texto", flat=True))
        self.assertTrue(textos)
        self.assertTrue(all(("día" in t or "toca ya" in t or "hoy" in t) for t in textos), textos)

    def test_aviso_pico_placa_la_noche_anterior(self):
        regla = mock.Mock(horario="5:00 a. m. a 8:00 p. m.")
        with mock.patch("garaje.management.commands.recordar_pico_placa.tiene_pico_placa", return_value=(True, regla)):
            call_command("recordar_pico_placa", stdout=io.StringIO())
            call_command("recordar_pico_placa", stdout=io.StringIO())  # no repite
        avisos = Notificacion.objects.filter(usuario=self.usuario, titulo="Mañana tienes pico y placa")
        self.assertEqual(avisos.count(), 1)


class RegistroEIntegracionTests(Base):
    def test_registro_como_domiciliario_activa_ruta(self):
        self.client.logout()
        r = self.client.get(reverse("cuentas:registro"))
        self.assertContains(r, "Soy domiciliario")
        datos = {"nombre": "Pedro", "email": "pedro@x.com", "celular": "3004445566",
                 "password1": "Clave-segura-2026", "password2": "Clave-segura-2026", "acepto": "on"}
        self.client.post(reverse("cuentas:registro") + "?tipo=domiciliario", datos)
        pedro = Motociclista.objects.get(usuario__email="pedro@x.com")
        perfil = PerfilDomiciliario.objects.get(motociclista=pedro)
        self.assertIsNone(perfil.moto)
        moto = Moto.objects.create(motociclista=pedro, linea=self.linea, modelo=2023, km_inicial=5, km_actual=5)
        perfil.refresh_from_db()
        self.assertEqual(perfil.moto, moto)  # su primera moto queda como «La uso para trabajar»

    def test_portada_menu_foro_y_directorio(self):
        r = self.client.get(reverse("talleres:inicio"))
        self.assertContains(r, "data-dm-portada")
        self.assertContains(r, "Mi ruta")
        self.assertContains(self.client.get(reverse("foro:lista")), "categoria=domiciliarios")
        directorio = self.client.get(reverse("talleres:directorio"))
        self.assertNotContains(directorio, 'name="domiciliarios"')  # sin marca de talleres para domiciliarios
        self.assertNotContains(directorio, "Atiende domiciliarios")
        self.assertContains(self.client.get(reverse("domicilio:listado")), "¿Te varaste en ruta?")

    def test_cupon_solo_domiciliarios_verificados(self):
        from cupones.servicios import RequiereVerificacion, obtener_codigo_para
        cupon = Cupon.objects.create(titulo="10 % domiciliarios", condiciones="x", solo_domiciliarios=True)
        with self.assertRaises(RequiereVerificacion):
            obtener_codigo_para(self.motero, cupon)
        Verificacion.objects.create(perfil=self.perfil, plataforma="rappi", autorizacion=timezone.now(),
                                    estado=Verificacion.Estado.APROBADA, vence=timezone.localdate() + timedelta(days=9))
        codigo, nuevo = obtener_codigo_para(self.motero, cupon)
        self.assertTrue(nuevo)


@override_settings(DOMICILIARIOS_ACTIVO=False)
class BanderaApagadaRutaTests(Base):
    def test_nada_de_ruta_aparece_ni_responde(self):
        self.assertEqual(self.client.get(reverse("domiciliarios:verificacion")).status_code, 404)
        self.assertEqual(self.client.post(reverse("domiciliarios:moto_trabajo", args=[self.moto.pk]), {"valor": "1"}).status_code, 404)
        self.assertFalse(getattr(calcular_plan(Moto.objects.get(pk=self.moto.pk)), "de_trabajo", False))
        r = self.client.get(self.moto.get_absolute_url())
        self.assertNotContains(r, "La uso para trabajar")
        self.assertNotContains(r, "data-dm-ruta")
        inicio = self.client.get(reverse("talleres:inicio"))
        self.assertNotContains(inicio, "data-dm-portada")
        self.assertNotContains(inicio, "Mi ruta")
        self.assertNotContains(self.client.get(reverse("foro:lista")), "categoria=domiciliarios")
        self.assertNotContains(self.client.get(reverse("talleres:directorio")), 'name="domiciliarios"')
        self.assertNotContains(self.client.get(reverse("domicilio:listado")), "¿Te varaste en ruta?")
        self.client.logout()
        self.assertNotContains(self.client.get(reverse("cuentas:registro")), "Soy domiciliario")

    def test_cupones_de_domiciliarios_no_se_listan(self):
        Cupon.objects.create(titulo="Solo ruta", condiciones="x", solo_domiciliarios=True)
        self.assertFalse(Cupon.objects.disponibles().filter(titulo="Solo ruta").exists())


class AccionesSinDatosTests(Base):
    """Sin placa ni SOAT: cada tarjeta y la franja ofrecen su acción, no un «—» ni un enlace suelto."""

    def test_mi_ruta_y_franja_sin_placa(self):
        Moto.objects.filter(pk=self.moto.pk).update(placa="", soat_vence=None)
        r = self.client.get(reverse("domiciliarios:panel"))
        for texto in ("Agregar placa →", "Ver agenda →", "Registrar fecha →", "Verificarme", "Ver gastos y consumo →", "Ajustes"):
            self.assertContains(r, texto)
        r = self.client.get(self.moto.get_absolute_url())
        self.assertContains(r, "Agrega la placa para ver tu pico y placa")
        self.assertContains(r, reverse("garaje:editar", args=[self.moto.pk]))


class ChapasYModoEditarTests(Base):
    def test_chapa_de_verificacion_en_la_franja(self):
        url = self.moto.get_absolute_url()
        self.assertContains(self.client.get(url), "Sin verificar")
        self.enviar()
        self.assertContains(self.client.get(url), "En revisión")
        Verificacion.objects.update(estado=Verificacion.Estado.APROBADA, vence=timezone.localdate() + timedelta(days=9))
        r = self.client.get(url)
        self.assertContains(r, "dm-chapa-ok")
        self.assertNotContains(r, "Sin verificar")
        self.assertContains(self.client.get(reverse("domiciliarios:panel")), "dm-chapa-ok")

    def test_modo_editar_marca_la_moto_de_trabajo(self):
        otra = Moto.objects.create(motociclista=self.motero, linea=self.linea, modelo=2021, km_inicial=1, km_actual=1, placa="XYZ98A")
        r = self.client.get(reverse("garaje:garaje") + "?lista=1")
        self.assertContains(r, 'class="ficha-editar-trabajo"', count=2)
        self.assertContains(r, 'class="ficha-trabajo"', count=1)
        r = self.client.post(reverse("domiciliarios:moto_trabajo", args=[otra.pk]), {"valor": "1", "volver": "garaje"})
        self.assertRedirects(r, reverse("garaje:garaje") + "?lista=1", fetch_redirect_response=False)
        self.assertEqual(PerfilDomiciliario.objects.get(pk=self.perfil.pk).moto, otra)
        r = self.client.post(reverse("domiciliarios:moto_trabajo", args=[otra.pk]), {"valor": "0", "volver": "https://malo.com"})
        self.assertRedirects(r, otra.get_absolute_url(), fetch_redirect_response=False)  # nada de redirecciones abiertas
