"""Tráfico de prueba para ver el panel de Métricas en local (solo con DEBUG).

1) Peticiones reales con el cliente de pruebas (pasan por el middleware y las vistas): eventos de hoy.
2) Historia sintética de N días (por defecto 45) con usuarios que se registran y vuelven, para el gráfico,
   los embudos y la retención. Luego resume los días cerrados.
"""
import random
import secrets
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.test.utils import override_settings
from django.utils import timezone

from metricas.agregacion import agregar_pendientes
from metricas.models import Evento

CEL = "Mozilla/5.0 (Linux; Android 14; SM-A145M) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"
PC = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
REFERENTES = ["", "", "https://www.google.com/", "https://l.facebook.com/", "https://web.whatsapp.com/",
              "https://instagram.com/"]
PAGINAS = [("talleres:inicio", 30), ("talleres:directorio", 22), ("talleres:detalle", 18), ("garaje:moto", 10),
           ("foro:lista", 8), ("cupones:lista", 6), ("talleres:emergencias", 3), ("tramites:inicio", 1)]
EVENTOS = [("taller_visto", 18), ("busqueda_talleres", 12), ("contacto", 6), ("plan_visto", 8),
           ("despiece_abierto", 4), ("pieza_vista", 5), ("visor_3d", 6), ("cupon_obtenido", 2),
           ("foro_respuesta", 1), ("inicio_sesion", 3)]


class Command(BaseCommand):
    help = "Genera tráfico de prueba para el panel de Métricas (solo en local, con DEBUG)."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=45, help="Días de historia sintética (por defecto 45).")
        parser.add_argument("--visitas", type=int, default=40, help="Visitantes reales con el cliente de pruebas.")

    def handle(self, *args, dias, visitas, **opciones):
        if not settings.DEBUG:
            raise CommandError("demo_metricas solo funciona con DEBUG=1 (crea usuarios y eventos falsos).")
        random.seed(7)
        reales = self.reales(visitas)
        sinteticos = self.historia(dias)
        resumidos = agregar_pendientes()
        self.stdout.write(self.style.SUCCESS(
            f"Eventos reales hoy: {reales} · sintéticos: {sinteticos} · días resumidos: {resumidos}"))

    def reales(self, visitas):
        from talleres.models import Taller
        slugs = list(Taller.objects.filter(activo=True).values_list("slug", flat=True)[:6])
        host = "127.0.0.1"
        with override_settings(METRICAS_ACTIVAS=True):
            for i in range(visitas):
                c = Client(HTTP_HOST=host, HTTP_USER_AGENT=random.choice([CEL, CEL, CEL, PC]),
                           REMOTE_ADDR=f"10.0.0.{i % 250}")
                c.get("/", HTTP_REFERER=random.choice(REFERENTES))
                c.get("/talleres/", {"q": random.choice(["frenos", "aceite", "llantas", "", "kit de arrastre"])})
                if slugs:
                    s = random.choice(slugs)
                    c.get(f"/taller/{s}/")
                    if random.random() < .4:
                        c.get(f"/taller/{s}/whatsapp/")
                if random.random() < .3:
                    c.get("/emergencias/")
                if random.random() < .3:
                    c.get("/foro/")
        return Evento.objects.filter(dia=timezone.localdate()).count()

    def historia(self, dias):
        User = get_user_model()
        hoy = timezone.localdate()
        usuarios, filas = [], []
        for d in range(dias, 0, -1):
            dia = hoy - timedelta(days=d)
            crecimiento = 1 + (dias - d) / 30
            for _ in range(random.randint(0, 3)):
                correo = f"demo-metricas-{secrets.token_hex(4)}@tallerya.local"
                u = User.objects.create_user(correo, correo, password=None)
                alta = timezone.make_aware(datetime.combine(dia, time(12)))
                User.objects.filter(pk=u.pk).update(date_joined=alta)
                usuarios.append((u.pk, dia))
                filas.append(Evento(dia=dia, tipo="e", nombre="registro", visitante=f"u{u.pk}", usuario_id=u.pk,
                                    datos={"metodo": random.choice(["correo", "google"])}))
                if random.random() < .6:
                    filas.append(Evento(dia=dia, tipo="e", nombre="moto_creada", visitante=f"u{u.pk}",
                                        usuario_id=u.pk))
                    if random.random() < .8:
                        filas.append(Evento(dia=dia, tipo="e", nombre="plan_visto", visitante=f"u{u.pk}",
                                            usuario_id=u.pk))
            for pk, alta in usuarios:  # usuarios que vuelven (decae con las semanas)
                if dia > alta and random.random() < .35 * (0.75 ** ((dia - alta).days // 7)):
                    filas.append(Evento(dia=dia, tipo="v", nombre="garaje:moto", visitante=f"u{pk}", usuario_id=pk,
                                        dispositivo="c"))
            for _ in range(int(random.randint(25, 40) * crecimiento)):
                quien = secrets.token_hex(8)
                disp = random.choices("cet", [70, 25, 5])[0]
                ref = random.choices(["directo", "google", "whatsapp", "redes", "otros"], [35, 30, 20, 12, 3])[0]
                for _ in range(random.randint(1, 4)):
                    nombre = random.choices([p for p, _ in PAGINAS], [w for _, w in PAGINAS])[0]
                    filas.append(Evento(dia=dia, tipo="v", nombre=nombre, visitante=quien, dispositivo=disp,
                                        referente=ref))
                    ref = "interno"
                if random.random() < .5:
                    nombre = random.choices([e for e, _ in EVENTOS], [w for _, w in EVENTOS])[0]
                    datos = ({"q": random.choice(["frenos", "aceite", "cadena", "llantas"])}
                             if nombre == "busqueda_talleres" else {})
                    filas.append(Evento(dia=dia, tipo="e", nombre=nombre, visitante=quien, dispositivo=disp,
                                        datos=datos))
                    if nombre == "contacto" and random.random() < .2:
                        filas.append(Evento(dia=dia, tipo="e", nombre="cupon_canjeado", visitante=quien))
        Evento.objects.bulk_create(filas, batch_size=500)
        return len(filas)
