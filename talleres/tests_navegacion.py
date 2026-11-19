"""Menú de base.html por rol: motociclista, taller, visitante y staff; «Mi ruta» solo cuando aplica; barra inferior del celular."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from cupones.models import Motociclista
from talleres.models import Barrio, Taller

from .templatetags.navegacion import seccion_de

User = get_user_model()


class Base(TestCase):
    def setUp(self):
        barrio = Barrio.objects.first() or Barrio.objects.get_or_create(nombre="Laureles")[0]
        self.motero = User.objects.create_user("m@x.com", "m@x.com", "x", first_name="Mara")
        self.motociclista = Motociclista.objects.create(nombre="Mara", celular="573005550000", usuario=self.motero)
        self.cuenta_taller = User.objects.create_user("t@x.com", "t@x.com", "x")
        Taller.objects.create(nombre="Taller Prueba", responsable="Tomás", whatsapp="573005551111",
                              direccion="Cra 1", barrio=barrio, usuario=self.cuenta_taller)
        self.admin = User.objects.create_user("a@x.com", "a@x.com", "x", is_staff=True)

    def cabecera(self, url=None):
        html = self.client.get(url or reverse("talleres:directorio")).content.decode()
        return html[html.index('id="cabecera"'):html.index("</header>")]

    def barra(self, url=None):
        html = self.client.get(url or reverse("talleres:directorio")).content.decode()
        if 'class="barra-inferior' not in html:
            return ""
        i = html.index('class="barra-inferior')
        return html[i:html.index("</nav>", i)]


class MenuPorRolTests(Base):
    def test_motociclista_cuatro_secciones_con_submenu(self):
        self.client.force_login(self.motero)
        c = self.cabecera()
        for control in ("sub-talleres", "sub-garaje", "sub-comunidad", "sub-cuenta"):
            self.assertIn(f'aria-controls="{control}"', c)
        self.assertEqual(c.count('aria-expanded="false"'), 5)  # 3 secciones + campana + avatar
        for texto in ("Mecánicos a domicilio", "¿Qué le pasa a tu moto?", "SOAT", "Técnico-mecánica", "Rodadas", ">Cupones<",
                      "¿Te varaste?", "Mis insignias", "Plus", "Instalar app", "Mi cuenta"):
            self.assertIn(texto, c)
        self.assertNotIn("Validar cupón", c)
        self.assertNotIn("Consola", c)
        self.assertNotIn("Mi ruta", c)  # sin Ruta activo
        self.assertNotIn("Diagnóstico</a>", c)  # ya no es entrada principal

    def test_taller_menu_propio(self):
        self.client.force_login(self.cuenta_taller)
        c = self.cabecera()
        for texto in (">Panel<", ">Citas<", "Validar cupón", "Mi perfil", 'nav-cuenta-nombre">Taller Prueba<', 'id="campana"'):
            self.assertIn(texto, c)
        for texto in ("sub-garaje", "¿Te varaste?", "Mis insignias", "Consola"):
            self.assertNotIn(texto, c)
        b = self.barra()
        for texto in ("Panel", "Citas", "Validar", "Mi perfil"):
            self.assertIn(texto, b)

    def test_visitante(self):
        c = self.cabecera()
        for texto in ("sub-talleres", "sub-comunidad", ">Diagnóstico</a>", "¿Te varaste?", ">Entrar<", "Crear cuenta"):
            self.assertIn(texto, c)
        self.assertLess(c.index("sub-comunidad"), c.index(">Diagnóstico</a>"))  # Diagnóstico va entre Comunidad y ¿Te varaste?
        self.assertLess(c.index(">Diagnóstico</a>"), c.index("¿Te varaste?"))
        for texto in ("sub-garaje", "sub-cuenta", ">Cupones<", 'id="campana"'):
            self.assertNotIn(texto, c)
        b = self.barra()
        for texto in ("Inicio", "Talleres", "Diagnóstico", "Comunidad", "Emergencia"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        self.assertNotIn("Mi garaje", b)
        self.assertIn('href="/diagnostico/" class="bi-item" aria-current="page"', self.barra(reverse("garaje:diagnostico")))

    def test_staff_conserva_la_consola(self):
        self.client.force_login(self.admin)
        c = self.cabecera()
        self.assertIn('class="nav-plus nav-consola', c)
        self.assertIn('aria-controls="sub-cuenta"', c)  # avatar con menú, con Consola dentro
        self.assertEqual(self.barra(), "")  # el staff no lleva barra inferior

    def test_barra_inferior_motociclista(self):
        self.client.force_login(self.motero)
        b = self.barra(reverse("garaje:garaje"))
        for texto in ("Inicio", "Talleres", "Mi garaje", "Comunidad", "Emergencia"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        self.assertIn('href="/garaje/" class="bi-item" aria-current="page"', b)

    def test_seccion_activa(self):
        self.client.force_login(self.motero)
        c = self.cabecera(reverse("tramites:soat"))
        self.assertIn('aria-controls="sub-garaje" aria-current="true"', c)
        self.assertIn('href="/soat/" class="ns-item" aria-current="page"', c)
        self.assertEqual([seccion_de(r) for r in ("/", "/taller/x/", "/mecanicos/", "/foro/rodadas/", "/mi-taller/citas/", "/canjear/", "/legal/x/")],
                         ["inicio", "talleres", "talleres", "comunidad", "taller_citas", "taller_canjear", ""])

    def test_saltar_al_contenido(self):
        self.assertContains(self.client.get(reverse("talleres:inicio")), 'href="#contenido" class="saltar-contenido"')


class MiRutaTests(Base):
    def domiciliario(self):
        from domiciliarios.models import PerfilDomiciliario
        PerfilDomiciliario.objects.create(motociclista=self.motociclista, km_semana=1200)
        self.client.force_login(self.motero)

    @override_settings(DOMICILIARIOS_ACTIVO=True)
    def test_mi_ruta_con_perfil_y_bandera(self):
        self.domiciliario()
        c = self.cabecera()
        self.assertEqual(c.count(">Mi ruta<"), 2)  # submenú Mi garaje (<strong>) y menú del avatar
        self.assertIn(reverse("domiciliarios:panel"), c)

    @override_settings(DOMICILIARIOS_ACTIVO=False)
    def test_sin_bandera_no_sale(self):
        self.domiciliario()
        self.assertNotIn("Mi ruta", self.cabecera())

    @override_settings(DOMICILIARIOS_ACTIVO=True)
    def test_sin_perfil_no_sale(self):
        self.client.force_login(self.motero)
        self.assertNotIn("Mi ruta", self.cabecera())


class DiagnosticoVisibleTests(Base):
    def test_accesos_fuera_del_menu(self):
        self.assertContains(self.client.get(reverse("talleres:inicio")), "data-diag-portada")
        self.assertContains(self.client.get(reverse("talleres:emergencias")), reverse("garaje:diagnostico"))
