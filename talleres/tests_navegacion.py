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
        self.assertIn('aria-controls="sub-taller-mas"', c)  # lo de vez en cuando va en «Más»
        for texto in (">Servicios<", ">Reseñas<", "Agenda y horario", "Precios de mano de obra", "Estadísticas", "Ver mi ficha pública"):
            self.assertIn(texto, c)
        b = self.barra()
        for texto in ("Panel", "Citas", "Registrar", "Servicios", "Mi ficha"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertNotIn("<span>Validar</span>", b)  # Validar cupón pasó a «Más»
        self.assertIn("Validar cupón", self.cabecera())
        self.assertNotIn("<span>Agenda</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        self.assertIn("bi-accion", b)  # registrar servicio, destacado

    def test_barra_inferior_mecanico(self):
        from domicilio.models import MecanicoDomicilio
        mec = User.objects.create_user("mec@x.com", "mec@x.com", "x")
        MecanicoDomicilio.objects.create(usuario=mec, nombre="Beto", whatsapp="573000000222")
        self.client.force_login(mec)
        b = self.barra(reverse("domicilio:panel"))
        for texto in ("Mi panel", "Solicitudes", "Registrar", "Servicios", "Mi ficha"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        self.assertIn("bi-accion", b)
        for texto in ("Precios", "Mi perfil"):
            self.assertNotIn(f"<span>{texto}</span>", b)

    def test_visitante(self):
        c = self.cabecera()
        for texto in ("sub-talleres", "sub-comunidad", ">Diagnóstico</a>", "¿Te varaste?", ">Entrar<", "Crear cuenta"):
            self.assertIn(texto, c)
        self.assertLess(c.index("sub-comunidad"), c.index(">Diagnóstico</a>"))  # Diagnóstico va entre Comunidad y ¿Te varaste?
        self.assertLess(c.index(">Diagnóstico</a>"), c.index("¿Te varaste?"))
        for texto in ("sub-garaje", "sub-cuenta", ">Cupones<", 'id="campana"'):
            self.assertNotIn(texto, c)
        b = self.barra()
        for texto in ("Inicio", "Talleres", "Diagnóstico", "Trámites", "Emergencia"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        self.assertNotIn("Mi garaje", b)
        self.assertNotIn("<span>Comunidad</span>", b)
        self.assertIn('href="/soat/" class="bi-item" aria-current="page"', self.barra(reverse("tramites:tecnomecanica")))
        self.assertIn('href="/diagnostico/" class="bi-item" aria-current="page"', self.barra(reverse("garaje:diagnostico")))

    def test_staff_conserva_la_consola(self):
        self.client.force_login(self.admin)
        c = self.cabecera()
        self.assertIn('class="nav-plus nav-consola', c)
        self.assertIn('aria-controls="sub-cuenta"', c)  # avatar con menú, con Consola dentro
        for texto in (">Aprobaciones", ">Usuarios", ">Moderación", ">Métricas"):
            self.assertIn(texto, c)
        self.assertNotIn('<span class="nav-separador"', c)  # Ver sitio y Admin técnico pasaron al menú del avatar
        self.assertIn('class="av-item" title="El directorio', c)
        b = self.barra(reverse("consola:inicio") + "?seccion=talleres")
        for texto in ("Resumen", "Aprobar", "Usuarios", "Moderación", "Métricas"):
            self.assertIn(f"<span>{texto}</span>", b)
        self.assertEqual(b.count('class="bi-item'), 5)
        # Aprobaciones lleva a la bandeja «Por aprobar» y queda activa en esa sección
        self.assertIn('?seccion=aprobaciones" class="bi-item" aria-current="page"', b)

    def test_aprobaciones_suma_pendientes_y_lleva_a_la_bandeja(self):
        from talleres.models import Barrio, Taller
        barrio = Barrio.objects.first() or Barrio.objects.create(nombre="Laureles")
        for i in range(2):
            Taller.objects.create(nombre=f"Pend {i}", responsable="R", whatsapp=f"57300555222{i}",
                                  direccion="Cra 1", barrio=barrio, activo=False)
        self.client.force_login(self.admin)
        b = self.barra(reverse("consola:inicio") + "?seccion=resumen")
        self.assertIn('?seccion=aprobaciones" class="bi-item"', b)
        self.assertIn(f'aria-label="{Taller.objects.filter(activo=False).count()} pendientes"', b)

    def test_barra_inferior_motociclista(self):
        self.client.force_login(self.motero)
        b = self.barra(reverse("garaje:garaje"))
        for texto in ("Inicio", "Talleres", "Mi garaje", "Trámites", "Emergencia"):
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


class InsigniasTests(Base):
    def test_citas_pendientes_en_el_menu_del_taller(self):
        from talleres.models import SolicitudCita
        taller = self.cuenta_taller.taller
        import datetime
        SolicitudCita.objects.create(taller=taller, nombre="Ana", telefono="573001112233", moto="Yamaha NMAX",
                                     fecha_preferida=datetime.date.today())
        self.client.force_login(self.cuenta_taller)
        self.assertIn('class="nav-contador"', self.cabecera())
        self.assertIn('class="bi-contador" aria-label="1 pendiente"', self.barra())

    def test_motero_sin_insignias(self):
        self.client.force_login(self.motero)
        self.assertNotIn("contador\" aria-label", self.barra())


class PiePorRolTests(Base):
    def pie(self):
        html = self.client.get(reverse("talleres:directorio")).content.decode()
        return html[html.index("<footer"):html.index("</footer>")]

    def test_sin_validar_cupon_ni_proximamente(self):
        for usuario in (None, self.motero, self.cuenta_taller):
            if usuario:
                self.client.force_login(usuario)
            p = self.pie()
            self.assertNotIn("Validar un cupón", p)
            self.assertNotIn("Próximamente", p)

    def test_visitante_y_motero_ven_negocios_y_tramites(self):
        p = self.pie()
        for texto in ("Registra tu taller", "Ya tengo cuenta: entrar", "SOAT", "Para tu moto"):
            self.assertIn(texto, p)
        self.client.force_login(self.motero)
        p = self.pie()
        self.assertIn("Mi garaje", p)
        self.assertNotIn("Ya tengo cuenta", p)

    def test_taller_pie_corto(self):
        self.client.force_login(self.cuenta_taller)
        p = self.pie()
        for texto in ("Registra tu taller", "SOAT", "Mi garaje", "Cupones<"):
            self.assertNotIn(texto, p)
        self.assertIn("Para tu moto", p)
