"""Carga datos de ejemplo: python manage.py cargar_demo"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from django.conf import settings
from django.contrib.auth import get_user_model

from cupones.models import Cupon
from foro.models import Pregunta, Respuesta

from talleres.models import Barrio, Marca, Resena, Servicio, Taller

BARRIOS = ["Belén", "Laureles", "Envigado", "Itagüí", "Robledo", "Buenos Aires", "Bello", "Centro"]
SERVICIOS = ["Mantenimiento general", "Cambio de aceite", "Frenos", "Sistema eléctrico",
             "Suspensión", "Latonería y pintura", "Llantas", "Revisión técnico-mecánica"]
MARCAS = ["AKT", "Auteco Bajaj", "Honda", "Suzuki", "Yamaha", "TVS", "KTM", "Hero"]

DEMO = [
    ("MotoServicio El Paisa", "Belén", [0, 1, 2], [4, 2], True, True),
    ("Taller Rueda Libre", "Laureles", [0, 3, 4], [3, 2, 0], True, False),
    ("Electromotos Envigado", "Envigado", [3, 7], [1, 5], False, False),
    ("Frenos y Más", "Itagüí", [2, 6], [0, 1, 7], True, False),
]


# Clave de la cuenta demo del garaje. Solo se crea con DEBUG activo (desarrollo local).
DEMO_CLAVE = "demo-garaje-2026"


class Command(BaseCommand):
    help = "Carga barrios, servicios, marcas y talleres de ejemplo"

    def handle(self, *args, **opts):
        barrios = {n: Barrio.objects.get_or_create(nombre=n)[0] for n in BARRIOS}
        servicios = [Servicio.objects.get_or_create(nombre=n)[0] for n in SERVICIOS]
        marcas = [Marca.objects.get_or_create(nombre=n)[0] for n in MARCAS]

        for nombre, barrio, s_idx, m_idx, verificado, destacado in DEMO:
            t, creado = Taller.objects.get_or_create(nombre=nombre, defaults={
                "responsable": "Demo", "whatsapp": "573000000000",
                "direccion": "Calle 00 # 00-00", "barrio": barrios[barrio],
                "horario": "Lun-Sáb 8am-6pm", "descripcion": "Taller de ejemplo.",
                "verificado": verificado, "activo": True, "destacado": destacado,
            })
            if creado:
                t.servicios.set([servicios[i] for i in s_idx])
                t.marcas.set([marcas[i] for i in m_idx])
                Resena.objects.create(taller=t, nombre="Carlos", estrellas=5, comentario="Muy buen servicio y precio justo.")
                Resena.objects.create(taller=t, nombre="Laura", estrellas=4, comentario="Rápidos y cumplidos.")
        hoy = timezone.localdate()
        cupones = [
            ("MotoServicio El Paisa", "15% de descuento en cambio de aceite",
             "Aplica para aceite mineral o semisintético. No acumulable.", hoy + timedelta(days=60), 100, True, False),
            ("Frenos y Más", "Revisión de frenos gratis",
             "Al comprar pastillas o bandas en el taller.", hoy + timedelta(days=30), 50, True, False),
            ("Taller Rueda Libre", "Diagnóstico eléctrico a mitad de precio",
             "Lunes a viernes.", None, None, True, False),
            (None, "$20.000 de descuento en cualquier taller aliado",
             "Premio por invitar amigos. Servicios desde $60.000.", None, None, False, True),
        ]
        plus = [
            ("Electromotos Envigado", "25% en revisión técnico-mecánica", "Exclusivo para suscriptores Plus.", True, False),
            (None, "Lavado y lubricación de cadena gratis", "Regalo mensual Plus en talleres aliados.", False, True),
        ]
        for taller, titulo, condiciones, solo_plus, regalo in plus:
            Cupon.objects.get_or_create(titulo=titulo, defaults={
                "taller": Taller.objects.filter(nombre=taller).first() if taller else None,
                "condiciones": condiciones, "solo_plus": solo_plus, "regalo_mensual": regalo,
            })
        for taller, titulo, condiciones, hasta, cupo, publico, premio in cupones:
            Cupon.objects.get_or_create(titulo=titulo, defaults={
                "taller": Taller.objects.filter(nombre=taller).first() if taller else None,
                "condiciones": condiciones, "valido_hasta": hasta, "cupo": cupo,
                "publico": publico, "premio_referido": premio,
            })

        self.cargar_foro()
        if settings.DEBUG:
            self.cargar_garaje()
        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))
        if settings.DEBUG:  # en producción los PIN se consultan en el admin, no en los logs
            self.stdout.write("PIN de canje por taller (solo para pruebas):")
            for nombre, pin in Taller.objects.values_list("nombre", "pin_canje"):
                self.stdout.write(f"  {nombre}: {pin}")

    def cargar_foro(self):
        """Usuarios demo sin contraseña utilizable: nadie puede iniciar sesión con ellos."""
        User = get_user_model()

        def usuario(email, nombre):
            u, creado = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": nombre})
            if creado:
                u.set_unusable_password()
                u.save()
            return u

        andres = usuario("andres.demo@tallerya.local", "Andrés")
        camila = usuario("camila.demo@tallerya.local", "Camila")
        cuenta_taller = usuario("paisa.demo@tallerya.local", "MotoServicio El Paisa")
        Taller.objects.filter(nombre="MotoServicio El Paisa", usuario__isnull=True).update(usuario=cuenta_taller)

        if Pregunta.objects.exists():
            return
        yamaha = Marca.objects.filter(nombre="Yamaha").first()
        akt = Marca.objects.filter(nombre="AKT").first()
        p1 = Pregunta.objects.create(
            autor=andres, marca=akt, titulo="¿Cada cuánto debo cambiar el aceite de una AKT NKD 125?",
            cuerpo="La uso todos los días para trabajar, unos 40 km diarios por Medellín. "
                   "En el manual dice una cosa y en el taller otra.",
        )
        r1 = Respuesta.objects.create(
            pregunta=p1, autor=cuenta_taller,
            cuerpo="Con ese uso diario y el tráfico de la ciudad, recomendamos cada 2.000 km con aceite mineral, "
                   "o cada 3.000 km si usas semisintético. Revisa el nivel cada semana.",
        )
        Respuesta.objects.create(pregunta=p1, autor=camila, cuerpo="Yo la cambio cada 2.500 km y me ha ido bien.")
        p1.mejor_respuesta = r1
        p1.save(update_fields=["mejor_respuesta"])
        Pregunta.objects.create(
            autor=camila, marca=yamaha, titulo="La NMAX hace un chillido al frenar, ¿son las pastillas?",
            cuerpo="Empezó hace una semana, sobre todo en las mañanas. Las pastillas tienen unos 8 meses.",
        )

    def cargar_garaje(self):
        """Cuenta de motociclista demo con dos motos. Solo en desarrollo (DEBUG), nunca en producción."""
        from cupones.models import Motociclista
        from garaje.models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento

        User = get_user_model()
        email = "moto.demo@tallerya.local"
        usuario, creado = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": "Sofía"})
        if creado:
            usuario.set_password(DEMO_CLAVE)
            usuario.save()
        perfil, _ = Motociclista.objects.get_or_create(celular="573009990001", defaults={"nombre": "Sofía", "usuario": usuario})
        if perfil.motos.exists():
            return
        hoy = timezone.localdate()

        def moto(linea, color, anio, lecturas, hechos):
            m = Moto.objects.create(motociclista=perfil, linea=LineaMoto.objects.get(nombre=linea), color=color,
                                    modelo=anio, km_inicial=lecturas[0][1], km_actual=lecturas[-1][1])
            for dias, km in lecturas:
                LecturaKm.objects.create(moto=m, km=km, fecha=hoy - timedelta(days=dias))
            for clave, km, dias in hechos:
                Mantenimiento.objects.create(moto=m, tarea=TareaMantenimiento.objects.get(clave=clave), km=km,
                                             fecha=hoy - timedelta(days=dias))

        moto("NKD 125", "#c62828", 2022, [(60, 14200), (30, 15100), (0, 16050)],
             [("aceite", 13700, 75), ("cadena-lubricar", 15400, 20), ("filtro-aire", 9000, 300),
              ("bujia", 9000, 300), ("pastillas-del", 11000, 200), ("llanta-tras", 4000, 600)])
        moto("NMAX 155", "#1f4fa8", 2024, [(45, 3100), (0, 4300)], [("aceite", 2000, 70)])
        self.stdout.write(f"Cuenta demo del garaje: {email} (clave en DEMO_CLAVE de cargar_demo.py)")
