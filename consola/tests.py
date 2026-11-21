from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cupones.models import Motociclista
from foro.models import Pregunta
from talleres.models import Barrio, SolicitudCita, Taller

from . import reloj, secciones
from .acciones import ACCIONES
from .forms import UsuarioForm
from .limites import LIMITES
from .models import Bitacora

User = get_user_model()
INICIO = reverse("consola:inicio")


def accion(clave, pk):
    return reverse("consola:accion", args=[clave, pk])


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin@t.co", "admin@t.co", "clave-segura-123", first_name="Ana", is_staff=True)
        cls.otro_admin = User.objects.create_user("jefe@t.co", "jefe@t.co", "clave-segura-123", is_staff=True)
        cls.motero = User.objects.create_user("m@t.co", "m@t.co", "clave-segura-123", first_name="Mario")
        Motociclista.objects.create(nombre="Mario", celular="573001112233", usuario=cls.motero)
        cls.barrio, _ = Barrio.objects.get_or_create(nombre="Laureles")
        cls.taller = Taller.objects.create(nombre="Motos Ya", responsable="B", whatsapp="573000000000",
                                           direccion="Cra 1", barrio=cls.barrio)

    def setUp(self):
        self.client.force_login(self.admin)

    def post(self, clave, pk, fetch=True, **datos):
        extra = {"HTTP_X_REQUESTED_WITH": "fetch"} if fetch else {}
        return self.client.post(accion(clave, pk), datos, **extra)


class PermisosTests(Base):
    def test_anonimo_va_al_login(self):
        self.client.logout()
        r = self.client.get(INICIO)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("cuentas:entrar"), r["Location"])

    def test_no_admin_no_entra_ni_ejecuta(self):
        self.client.force_login(self.motero)
        self.assertEqual(self.client.get(INICIO).status_code, 403)
        self.assertEqual(self.client.get(INICIO + "?seccion=bitacora").status_code, 403)
        r = self.post("usuarios.cambiar_rol", self.motero.pk, rol="admin")
        self.assertEqual(r.status_code, 403)
        self.motero.refresh_from_db()
        self.assertFalse(self.motero.is_staff)
        self.assertFalse(Bitacora.objects.exists())

    def test_cada_accion_registrada_exige_admin(self):
        self.client.force_login(self.motero)
        for clave in ACCIONES:
            self.assertEqual(self.post(clave, self.admin.pk).status_code, 403, clave)

    def test_acciones_solo_por_post(self):
        self.assertEqual(self.client.get(accion("usuarios.estado", self.motero.pk)).status_code, 405)


class LayoutTests(Base):
    def test_seccion_en_la_url_y_titulo(self):
        r = self.client.get(INICIO + "?seccion=bitacora")
        self.assertContains(r, "<title>Bitácora · Consola</title>", html=False)
        self.assertContains(r, 'href="?seccion=bitacora" class="cs-nav-item"\n         aria-current="page"', html=False)
        self.assertContains(self.client.get(INICIO), "<title>Usuarios · Consola</title>", html=False)

    def test_seccion_desconocida_404_y_planificada_muestra_proximamente(self):
        self.assertEqual(self.client.get(INICIO + "?seccion=nada").status_code, 404)
        self.assertContains(self.client.get(INICIO + "?seccion=catalogos"), "fase 2")

    def test_insignias_de_pendientes(self):
        filas, total = secciones.con_pendientes()
        self.assertEqual(dict((s.key, n) for s, n in filas)["talleres"], 1)  # el taller sin aprobar
        r = self.client.get(INICIO)
        self.assertContains(r, 'aria-label="1 pendiente"')
        self.assertContains(r, f"{total} pendiente")

    def test_secciones_declaradas_tienen_claves_unicas(self):
        claves = [s.key for s in secciones.SECCIONES]
        self.assertEqual(len(claves), len(set(claves)))
        self.assertIn(secciones.PREDETERMINADA, claves)


class UsuariosTests(Base):
    def test_busqueda_y_ficha(self):
        r = self.client.get(INICIO, {"seccion": "usuarios", "q": "mario"})
        self.assertContains(r, "m@t.co")
        self.assertNotContains(r, "jefe@t.co")
        r = self.client.get(INICIO, {"seccion": "usuarios", "id": self.motero.pk})
        self.assertContains(r, "Motos")
        self.assertContains(r, "Citas")

    def test_cambiar_rol_registra_frase_y_detalle(self):
        r = self.post("usuarios.cambiar_rol", self.motero.pk, rol="admin")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        b = Bitacora.objects.get()
        self.assertEqual(b.frase, f"Cambió el rol del usuario #{self.motero.pk} a Administrador")
        self.assertEqual(b.actor, self.admin)
        self.assertEqual(b.cambios, [{"campo": "rol", "etiqueta": "Rol", "antes": "Motero", "despues": "Administrador"}])

    def test_rol_taller_vincula_el_taller(self):
        self.post("usuarios.cambiar_rol", self.motero.pk, rol="taller", taller=self.taller.pk)
        self.taller.refresh_from_db()
        self.assertEqual(self.taller.usuario, self.motero)
        cambios = {c["campo"]: c for c in Bitacora.objects.get().cambios}
        self.assertEqual(cambios["taller"]["despues"], "Motos Ya")
        self.assertEqual(cambios["rol"]["despues"], "Taller")

    def test_error_no_registra(self):
        r = self.post("usuarios.cambiar_rol", self.motero.pk, rol="taller")  # sin taller
        self.assertEqual(r.status_code, 400)
        self.assertIn("taller", r.json()["error"])
        self.assertFalse(Bitacora.objects.exists())

    def test_no_puede_quitarse_admin_ni_desactivarse(self):
        self.assertEqual(self.post("usuarios.cambiar_rol", self.admin.pk, rol="motero").status_code, 400)
        self.assertEqual(self.post("usuarios.estado", self.admin.pk, activa="0").status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff and self.admin.is_active)

    def test_ultimo_admin_activo_protegido(self):
        User.objects.filter(pk=self.admin.pk).update(is_superuser=True)
        self.client.force_login(User.objects.get(pk=self.admin.pk))
        self.post("usuarios.estado", self.otro_admin.pk, activa="0")
        self.otro_admin.refresh_from_db()
        self.assertFalse(self.otro_admin.is_active)  # quedaba el admin actual

    def test_desactivar_y_activar_sin_js(self):
        r = self.post("usuarios.estado", self.motero.pk, fetch=False, activa="0", volver="/consola/?seccion=usuarios")
        self.assertRedirects(r, "/consola/?seccion=usuarios", fetch_redirect_response=False)
        self.motero.refresh_from_db()
        self.assertFalse(self.motero.is_active)
        self.assertEqual(Bitacora.objects.get().frase, f"Desactivó la cuenta del usuario #{self.motero.pk}")

    def test_volver_externo_se_ignora(self):
        r = self.post("usuarios.estado", self.motero.pk, fetch=False, activa="0", volver="https://malo.com/")
        self.assertEqual(r["Location"], INICIO)

    def test_editar_nombre_y_correo(self):
        r = self.post("usuarios.editar", self.motero.pk, first_name="Mario José", last_name="", email="NUEVO@t.co")
        self.assertTrue(r.json()["ok"])
        self.motero.refresh_from_db()
        self.assertEqual((self.motero.email, self.motero.username), ("nuevo@t.co", "nuevo@t.co"))
        cambios = {c["campo"]: (c["antes"], c["despues"]) for c in Bitacora.objects.get().cambios}
        self.assertEqual(cambios, {"nombre": ("Mario", "Mario José"), "correo": ("m@t.co", "nuevo@t.co")})

    def test_editar_correo_repetido(self):
        r = self.post("usuarios.editar", self.motero.pk, first_name="Mario", email="jefe@t.co")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Bitacora.objects.exists())

    def test_sin_cambios_no_registra(self):
        r = self.post("usuarios.editar", self.motero.pk, first_name="Mario", email="m@t.co")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Bitacora.objects.exists())

    def test_restablecer_contrasena(self):
        r = self.post("usuarios.contrasena", self.motero.pk)
        clave = r.json()["contrasena"]
        self.motero.refresh_from_db()
        self.assertTrue(self.motero.check_password(clave))
        b = Bitacora.objects.get()
        self.assertNotIn(clave, str(b.cambios) + b.frase)
        self.assertEqual(b.cambios[0]["etiqueta"], "Contraseña")


class EliminacionSeguraTests(Base):
    def test_con_citas_no_se_borra_y_ofrece_desactivar(self):
        for _ in range(3):
            SolicitudCita.objects.create(taller=self.taller, nombre="M", telefono="3001112233", moto="NMAX",
                                         fecha_preferida=date(2026, 12, 1), usuario=self.motero)
        r = self.client.get(INICIO, {"seccion": "usuarios", "id": self.motero.pk})
        self.assertContains(r, "Tiene 3 citas")
        self.assertContains(r, "Desactivarla en su lugar")
        r = self.post("usuarios.eliminar", self.motero.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("3 citas", r.json()["error"])
        self.assertIn("desactivarla", r.json()["error"])
        self.assertTrue(User.objects.filter(pk=self.motero.pk).exists())
        self.assertFalse(Bitacora.objects.exists())

    def test_sin_bloqueos_se_borra_y_queda_en_bitacora(self):
        Pregunta.objects.create(autor=self.motero, titulo="¿Aceite?", cuerpo="x")
        r = self.client.get(INICIO, {"seccion": "usuarios", "id": self.motero.pk})
        self.assertContains(r, "se borran con sus respuestas")
        pk = self.motero.pk
        r = self.post("usuarios.eliminar", pk)
        self.assertTrue(r.json()["ok"])
        self.assertFalse(User.objects.filter(pk=pk).exists())
        self.assertFalse(Motociclista.objects.filter(celular="573001112233").exists())
        b = Bitacora.objects.get()
        self.assertEqual(b.frase, f"Eliminó la cuenta del usuario #{pk} (m@t.co)")
        self.assertEqual(b.objeto_id, pk)

    def test_admin_y_taller_vinculado_bloquean(self):
        self.assertEqual(self.post("usuarios.eliminar", self.otro_admin.pk).status_code, 400)
        self.taller.usuario = self.motero
        self.taller.save()
        self.assertIn("taller", self.post("usuarios.eliminar", self.motero.pk).json()["error"])


class BitacoraTests(Base):
    def test_filtros_y_detalle(self):
        self.post("usuarios.estado", self.motero.pk, activa="0")
        self.post("usuarios.cambiar_rol", self.motero.pk, rol="admin")
        r = self.client.get(INICIO, {"seccion": "bitacora", "accion": "usuarios.estado"})
        self.assertContains(r, "Desactivó la cuenta")
        self.assertNotContains(r, "Cambió el rol del usuario")
        r = self.client.get(INICIO, {"seccion": "bitacora", "objeto": f"user:{self.motero.pk}"})
        self.assertContains(r, "Cambió el rol del usuario")
        b = Bitacora.objects.get(accion="usuarios.cambiar_rol")
        r = self.client.get(INICIO, {"seccion": "bitacora", "id": b.pk})
        self.assertContains(r, "Detalle campo por campo")
        self.assertContains(r, '<td class="cs-antes">Motero</td>', html=True)
        self.assertContains(r, '<td class="cs-despues">Administrador</td>', html=True)

    def test_reloj_fijo_y_filtro_de_fechas(self):
        with reloj.fijar(datetime(2026, 1, 15, 10, 0)):
            self.post("usuarios.estado", self.motero.pk, activa="0")
            self.assertEqual(reloj.hoy(), date(2026, 1, 15))
        b = Bitacora.objects.get()
        self.assertEqual(b.creado.date(), date(2026, 1, 15))
        r = self.client.get(INICIO, {"seccion": "bitacora", "desde": "2026-02-01"})
        self.assertNotContains(r, "Desactivó la cuenta")
        r = self.client.get(INICIO, {"seccion": "bitacora", "desde": "2026-01-01", "hasta": "2026-01-31"})
        self.assertContains(r, "Desactivó la cuenta")


class LimitesTests(Base):
    def test_formulario_y_plantilla_usan_el_mismo_limite(self):
        maximo = LIMITES["nombre"]["max"]
        f = UsuarioForm({"first_name": "x" * (maximo + 1), "email": "a@t.co"}, instance=self.motero)
        self.assertIn("first_name", f.errors)
        f = UsuarioForm({"first_name": "x", "email": "a@t.co"}, instance=self.motero)  # bajo el mínimo
        self.assertIn("first_name", f.errors)
        r = self.client.get(INICIO, {"seccion": "usuarios", "id": self.motero.pk})
        self.assertContains(r, f'maxlength="{maximo}" minlength="{LIMITES["nombre"]["min"]}"')
        self.assertContains(r, f'maxlength="{LIMITES["correo"]["max"]}"')

    def test_servidor_rechaza_aunque_se_salte_el_formulario(self):
        r = self.post("usuarios.editar", self.motero.pk, first_name="x" * 151, email="m@t.co")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Nombre", r.json()["error"])

    def test_busqueda_larga_se_ignora(self):
        r = self.client.get(INICIO, {"seccion": "usuarios", "q": "x" * (LIMITES["busqueda"]["max"] + 1)})
        self.assertEqual(r.status_code, 200)


class RegistroIncompletoTests(Base):
    def test_filtro_y_ficha_dicen_registro_incompleto(self):
        nuevo = User.objects.create_user("g@t.co", "g@t.co", None, first_name="Google")
        r = self.client.get(INICIO, {"seccion": "usuarios", "rol": "sin_perfil"})
        self.assertContains(r, "g@t.co")
        self.assertNotContains(r, "m@t.co")
        self.assertContains(r, "Registro incompleto")
        self.assertContains(r, "Cuentas que se crearon pero no terminaron el registro")
        self.assertNotContains(r, "Sin perfil")
        r = self.client.get(INICIO, {"seccion": "usuarios", "id": nuevo.pk})
        self.assertContains(r, "no tiene perfil de motero (nombre y celular) ni un taller vinculado")

    def test_rol_en_la_url_filtra_y_conserva_busqueda(self):
        r = self.client.get(INICIO, {"seccion": "usuarios", "rol": "motero", "q": "t.co"})
        self.assertContains(r, "m@t.co")
        self.assertNotContains(r, "admin@t.co")
        self.assertContains(r, 'value="t.co"')
        self.assertContains(r, '<option value="motero" selected>', html=False)


class AdminTecnicoTests(Base):
    def test_enlace_a_django_solo_para_superusuarios(self):
        for url in (INICIO, reverse("cuentas:administracion")):
            r = self.client.get(url)
            self.assertNotContains(r, "Admin técnico (Django)")
            self.assertNotContains(r, "Panel completo de Django")
        User.objects.filter(pk=self.admin.pk).update(is_superuser=True)
        for url in (INICIO, reverse("cuentas:administracion")):
            self.assertContains(self.client.get(url), 'title="Editar tablas directamente; solo para el equipo técnico">Admin técnico (Django)</a>', html=False)


class PaginacionTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User.objects.bulk_create([User(username=f"u{i}@t.co", email=f"u{i}@t.co") for i in range(30)])

    def test_tamano_por_defecto_y_elegido(self):
        r = self.client.get(INICIO, {"seccion": "usuarios"})
        self.assertEqual(len(r.context["filas"]), 10)
        self.assertContains(r, "Mostrando <strong>1–10</strong> de <strong>33</strong>", html=False)
        self.assertContains(r, 'aria-current="page">1</span>', html=False)
        r = self.client.get(INICIO, {"seccion": "usuarios", "por": "25", "pagina": "2"})
        self.assertEqual(len(r.context["filas"]), 8)
        self.assertContains(r, '<input type="hidden" name="por" value="25">', html=False)  # el filtro conserva el tamaño

    def test_tamano_fuera_de_las_opciones_usa_el_defecto(self):
        r = self.client.get(INICIO, {"seccion": "usuarios", "por": "1000"})
        self.assertEqual(r.context["por"], 10)
