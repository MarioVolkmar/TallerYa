"""Siembra datos demo realistas pero ficticios para probar TallerYa en local: python manage.py sembrar_demo

- 9 talleres en Medellín y el Valle de Aburrá (nombres inventados, barrios reales) con perfil, horarios, precios, fotos
  de talleres/demo/, reseñas y cupones (vigentes, vencidos y desactivados);
- 18 moteros con motos del catálogo, lecturas de km, mantenimientos, citas en distintos estados y códigos de cupón;
- hilos del foro con respuestas y un reporte por revisar;
- cuatro cuentas fijas (usuario, taller, admin y superadmin @prueba.com). Su clave NO está en el código: se lee de la
  variable TALLERYA_CLAVE_PRUEBA o de privado/cuentas-prueba.txt (línea «clave: ...»). Sin clave, no se crean.
- todas las cuentas quedan con el correo verificado.

Idempotente: lo que ya existe (por nombre o correo) no se duplica; las cuentas fijas se re-sincronizan (rol y clave).
Solo para desarrollo: se niega a correr con DEBUG apagado salvo con --forzar.
"""
import os
import random
from datetime import time, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from consola import reloj
from cuentas.models import Perfil
from cupones.models import CodigoCupon, Cupon, Motociclista
from foro.models import Pregunta, Reporte, Respuesta
from garaje.models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from talleres.demo_talleres import _archivo, primero_o_crear
from talleres.models import (Barrio, FotoTaller, HorarioTaller, Marca, PrecioServicio, Resena, Servicio,
                             SolicitudCita, Taller)

DOMINIO = "demo.tallerya.test"
FOTOS = ["dobleleva-1.webp", "torquesur-1.webp", "dobleleva-2.webp", "torquesur-2.webp", "dobleleva-3.webp",
         "torquesur-3.webp", "dobleleva-4.webp", "torquesur-4.webp", "dobleleva-portada.webp"]
HORARIO_SEMANA = [(d, time(8), time(18)) for d in range(5)] + [(5, time(8), time(14))]
HORARIO_LARGO = [(d, time(7, 30), time(19)) for d in range(6)] + [(6, time(9), time(13))]

# nombre, (barrio, ciudad), dirección, responsable, especialidades, servicios, marcas, nivel, activo, verificado, cuenta
TALLERES = [
    ("Biela y Pistón Taller", ("Laureles", "Medellín"), "Circular 74B # 39-21", "Hernán Darío Villa",
     ["inyeccion", "motor", "alta"], ["Mantenimiento general", "Cambio de aceite", "Sincronización", "Suspensión"],
     ["Yamaha", "KTM", "Suzuki"], 3, True, True, "taller@prueba.com"),
    ("El Arriero Motoservicio", ("Castilla", "Medellín"), "Carrera 68 # 98-14", "Luz Mery Agudelo",
     ["trabajo", "carburacion", "arrastre"], ["Mantenimiento general", "Cambio de aceite", "Kit de arrastre", "Llantas"],
     ["AKT", "Auteco Bajaj", "Hero"], 1, True, True, None),
    ("Rin Diecisiete Motos", ("Guayabal", "Medellín"), "Calle 10 Sur # 51-33", "Óscar Iván Restrepo",
     ["frenos", "suspension", "trail"], ["Frenos", "Suspensión", "Llantas", "Revisión técnico-mecánica"],
     ["Honda", "Yamaha", "Suzuki"], 2, True, False, None),
    ("Cuatro Tiempos Aranjuez", ("Aranjuez", "Medellín"), "Carrera 51 # 92-07", "Wilmar Alexis Zapata",
     ["carburacion", "trabajo", "motor"], ["Mantenimiento general", "Sincronización", "Cambio de aceite"],
     ["AKT", "Auteco Bajaj", "TVS"], 1, True, False, None),
    ("Chispa Eléctrica Motos", ("Centro", "Medellín"), "Calle 44 # 52-60, local 112", "Diana Patricia Gómez",
     ["electrico", "inyeccion", "electricas"], ["Sistema eléctrico", "Mantenimiento general"],
     ["Honda", "Yamaha", "AKT", "TVS"], 2, True, True, None),
    ("La Cadena Floja Taller", ("Buenos Aires", "Medellín"), "Calle 49 # 28-15", "Andrés Felipe Mesa",
     ["arrastre", "frenos", "scooters"], ["Kit de arrastre", "Frenos", "Cambio de aceite", "Llantas"],
     ["Yamaha", "Honda", "Suzuki"], 1, True, False, None),
    ("Moto Clínica San Marcos", ("San Marcos", "Envigado"), "Carrera 43A # 36 Sur-18", "Gloria Inés Arango",
     ["scooters", "inyeccion", "tecnomecanica"], ["Mantenimiento general", "Revisión técnico-mecánica", "Frenos"],
     ["Yamaha", "Honda", "Suzuki", "TVS"], 2, True, True, None),
    ("Pits del Sur", ("Ditaires", "Itagüí"), "Calle 36 # 61-40", "Jorge Eliécer Cano",
     ["alta", "suspension", "pintura"], ["Suspensión", "Latonería y pintura", "Mantenimiento general"],
     ["KTM", "Yamaha", "Auteco Bajaj"], 3, True, False, None),
    ("Taller Ruta Sesenta y Dos", ("Niquía", "Bello"), "Diagonal 55 # 62-110", "Yeison Albeiro Ríos",
     ["trabajo", "motor", "carburacion"], ["Mantenimiento general", "Cambio de aceite", "Kit de arrastre"],
     ["AKT", "Auteco Bajaj", "Hero", "TVS"], 1, False, False, None),  # por aprobar: sale en la insignia de la consola
]
PRECIOS = {  # servicio -> [(cilindraje, desde, hasta)] según nivel de precio 1..3 (multiplicador)
    "Cambio de aceite": [("baja", 38000, 55000), ("media", 75000, 120000)],
    "Kit de arrastre": [("baja", 150000, 240000), ("media", 280000, 460000)],
    "Frenos": [("baja", 45000, 75000), ("media", 85000, 140000)],
    "Sincronización": [("baja", 110000, 170000), ("media", 180000, 290000)],
    "Suspensión": [("media", 160000, 270000), ("alta", 320000, 520000)],
    "Revisión técnico-mecánica": [("", 30000, 45000)],
    "Sistema eléctrico": [("", 40000, 65000)],
    "Llantas": [("", 15000, 25000)],
    "Mantenimiento general": [("baja", 90000, 140000), ("media", 160000, 260000)],
    "Latonería y pintura": [("", 250000, 600000)],
}
COMPROMISOS = [["fotos", "presupuesto"], ["presupuesto", "piezas", "avisamos"], ["fotos", "factura", "presupuesto"]]
NOMBRES = ["Juliana Cardona", "Sebastián Henao", "Daniela Correa", "Camilo Osorio", "Natalia Betancur",
           "Brayan Muñoz", "Paola Quintero", "Esteban Londoño", "Marcela Úsuga", "Cristian Montoya",
           "Valeria Toro", "Duván Echeverri", "Laura Isaza", "Jhonatan Pérez", "Manuela Rendón", "Alejandro Giraldo",
           "Katherine Vélez", "Santiago Bedoya"]
MOTOS = [("NKD 125", "#c62828"), ("Boxer CT 100", "#1f1f1f"), ("NMAX 155", "#1f4fa8"), ("CB 125F", "#b71c1c"),
         ("Pulsar NS 200", "#f9a825"), ("XTZ 150", "#1565c0"), ("Gixxer 150", "#263238"), ("Apache RTR 160", "#d84315"),
         ("Wave 110S", "#9e9e9e"), ("FZ 2.0", "#37474f"), ("Discover 125", "#0d47a1"), ("TT 125 DS", "#2e7d32"),
         ("Dio 110", "#e91e63"), ("XR 150L", "#c62828"), ("Raider 125", "#455a64"), ("Best 125", "#6d4c41"),
         ("Crypton FI 115", "#283593"), ("Aerox 155", "#00838f")]
RESENAS = [
    (5, "Me explicaron todo antes de tocar la moto y el precio fue el que dijeron."),
    (4, "Buen trabajo, se demoraron un poco más de lo acordado pero quedó perfecta."),
    (5, "Mandaron fotos de las pastillas gastadas por WhatsApp. Así da gusto."),
    (3, "Arreglaron el problema, aunque tocó volver una vez por un ajuste."),
    (5, "Llevo dos años yendo y nunca me han metido gato por liebre."),
    (4, "Atención amable y el taller muy organizado."),
]
HILOS = [
    ("¿Qué aceite le echan a la Boxer CT 100 para trabajar todo el día?",
     "Hago domicilios en el Centro, unos 120 km diarios. ¿20W50 mineral o vale la pena el semisintético?",
     ["Con ese kilometraje, semisintético 20W50 y cambio cada 2.000 km. Revisa el nivel cada dos días.",
      "Yo uso mineral y cambio cada 1.500 km, me ha salido más barato."]),
    ("La NMAX pierde fuerza en las lomas de Belén",
     "Desde hace un mes siente como si patinara en subida, sobre todo con parrillero.",
     ["Suena a correa o rodillos del variador gastados. ¿Cuántos km lleva?",
      "A la mía le pasó a los 18.000 km: cambio de rodillos y quedó nueva."]),
    ("¿Cada cuánto se cambia el kit de arrastre de una NKD?",
     "El piñón ya se ve con los dientes medio torcidos y la cadena suena.",
     ["Depende de cómo la cuides; con lubricación cada 500 km dura 15.000 a 20.000 km.",
      "Si los dientes están en punta, cámbialo completo: piñón, corona y cadena juntos."]),
    ("Recomienden taller para revisar el ABS de una Pulsar NS 200",
     "Se prendió el testigo del ABS y no sé si es sensor o algo más grave.",
     ["Primero que le pasen escáner; muchas veces es el sensor sucio de barro.",
      "En el Centro hay talleres de eléctricos que leen el código en diez minutos."]),
]


class Command(BaseCommand):
    help = "Siembra datos demo realistas y ficticios (talleres, moteros, citas, cupones, foro y 4 cuentas fijas)."

    def add_arguments(self, parser):
        parser.add_argument("--forzar", action="store_true", help="Permite correr con DEBUG apagado (no recomendado).")

    def handle(self, *args, forzar=False, **opts):
        if not settings.DEBUG and not forzar:
            raise CommandError("sembrar_demo es solo para desarrollo (DEBUG). Usa --forzar si de verdad lo necesitas.")
        random.seed(2026)  # mismos datos en cada máquina
        self.hoy = reloj.hoy()
        with transaction.atomic():
            fijas = self.cuentas_fijas()
            talleres = self.talleres(fijas.get("taller@prueba.com"))
            moteros = self.moteros(talleres, fijas.get("usuario@prueba.com"))
            self.cupones(talleres, moteros)
            self.foro(moteros, talleres)
            n = self.verificar_todas()
        self.stdout.write(self.style.SUCCESS(
            f"Demo sembrado: {len(talleres)} talleres, {len(moteros)} moteros; {n} cuentas con correo verificado."))
        if not fijas:
            self.stdout.write(self.style.WARNING(
                "Sin clave para las cuentas fijas: define TALLERYA_CLAVE_PRUEBA o crea privado/cuentas-prueba.txt."))

    # ---------- Cuentas ----------
    def clave_prueba(self):
        clave = os.environ.get("TALLERYA_CLAVE_PRUEBA", "").strip()
        archivo = Path(settings.BASE_DIR) / "privado" / "cuentas-prueba.txt"
        if not clave and archivo.exists():
            for linea in archivo.read_text(encoding="utf-8").splitlines():
                if linea.lower().startswith("clave:"):
                    clave = linea.split(":", 1)[1].strip()
                    break
        return clave

    def cuenta(self, email, nombre, clave=None):
        User = get_user_model()
        u, creado = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": nombre})
        if clave:
            u.set_password(clave)  # a propósito sin validadores: son cuentas locales de prueba
            u.is_active = True
            u.save()
        elif creado:
            u.set_unusable_password()
            u.save()
        return u

    def cuentas_fijas(self):
        clave = self.clave_prueba()
        if not clave:
            return {}
        cuentas = {
            "usuario@prueba.com": self.cuenta("usuario@prueba.com", "Usuario de prueba", clave),
            "taller@prueba.com": self.cuenta("taller@prueba.com", "Taller de prueba", clave),
            "admin@prueba.com": self.cuenta("admin@prueba.com", "Admin de prueba", clave),
            "superadmin@prueba.com": self.cuenta("superadmin@prueba.com", "Superadmin de prueba", clave),
        }
        User = get_user_model()
        User.objects.filter(pk=cuentas["admin@prueba.com"].pk).update(is_staff=True, is_superuser=False)
        User.objects.filter(pk=cuentas["superadmin@prueba.com"].pk).update(is_staff=True, is_superuser=True)
        User.objects.filter(pk__in=[cuentas["usuario@prueba.com"].pk, cuentas["taller@prueba.com"].pk]).update(
            is_staff=False, is_superuser=False)
        return cuentas

    # ---------- Talleres ----------
    def talleres(self, cuenta_taller):
        servicios = {n: Servicio.objects.get_or_create(nombre=n)[0] for n in PRECIOS}
        resultado = []
        for i, (nombre, (barrio, ciudad), direccion, responsable, esp, servs, marcas, nivel, activo, verificado,
                cuenta) in enumerate(TALLERES):
            existente = Taller.objects.filter(nombre=nombre).first()
            if existente:
                if cuenta and cuenta_taller and existente.usuario_id != cuenta_taller.pk:
                    Taller.objects.filter(usuario=cuenta_taller).exclude(pk=existente.pk).update(usuario=None)
                    existente.usuario = cuenta_taller
                    existente.save(update_fields=["usuario"])
                resultado.append(existente)
                continue
            usuario = cuenta_taller if cuenta else None
            if usuario:
                Taller.objects.filter(usuario=usuario).update(usuario=None)
            t = Taller(
                nombre=nombre, barrio=primero_o_crear(Barrio, nombre=barrio, ciudad=ciudad)[0], direccion=direccion,
                responsable=responsable, whatsapp="573000000000", nivel_precio=nivel, activo=activo,
                verificado=verificado, destacado=(i == 0), usuario=usuario,
                horario="Lun-Sáb 7:30am-7pm · Dom 9am-1pm" if i % 3 == 0 else "Lun-Vie 8am-6pm · Sáb 8am-2pm",
                descripcion=f"Taller de barrio en {barrio}: {', '.join(s.lower() for s in servs[:3])}. "
                            "Presupuesto antes de empezar y repuestos de calidad.",
                equipo=[{"nombre": responsable, "rol": "Jefe de taller", "anios": 10 + i, "especialidad": servs[0]},
                        {"nombre": NOMBRES[(i * 3) % len(NOMBRES)].split()[0] + " " + ["Ruiz", "Gil", "Mejía"][i % 3],
                         "rol": "Técnico", "anios": 3 + i % 5, "especialidad": servs[-1]}],
                especialidades=esp, garantia_meses=[1, 2, 3][i % 3], compromisos=COMPROMISOS[i % 3],
            )
            _archivo(t.foto, FOTOS[i % len(FOTOS)], guardar=False)
            t.save()
            t.servicios.set([servicios[s] for s in servs])
            t.marcas.set(Marca.objects.filter(nombre__in=marcas))
            HorarioTaller.objects.bulk_create(HorarioTaller(taller=t, dia=d, abre=a, cierra=c)
                                              for d, a, c in (HORARIO_LARGO if i % 3 == 0 else HORARIO_SEMANA))
            factor = {1: 1.0, 2: 1.15, 3: 1.35}[nivel]
            PrecioServicio.objects.bulk_create(
                PrecioServicio(taller=t, servicio=servicios[s], cilindraje=c, desde=int(round(d * factor, -3)),
                               hasta=int(round(h * factor, -3)))
                for s in servs for c, d, h in PRECIOS[s])
            for j in range(2):
                f = FotoTaller(taller=t, descripcion=["Zona de trabajo", "Herramienta y repuestos"][j], orden=j)
                _archivo(f.imagen, FOTOS[(i + j + 3) % len(FOTOS)], guardar=False)
                f.save()
            resultado.append(t)
        return resultado

    # ---------- Moteros ----------
    def moteros(self, talleres, cuenta_usuario):
        publicados = [t for t in talleres if t.activo]
        tareas = {t.clave: t for t in TareaMantenimiento.objects.all()}
        lineas = {l.nombre: l for l in LineaMoto.objects.all()}
        servicios = list(Servicio.objects.filter(nombre__in=PRECIOS))
        estados = [SolicitudCita.Estado.ATENDIDA, SolicitudCita.Estado.CONFIRMADA, SolicitudCita.Estado.PENDIENTE,
                   SolicitudCita.Estado.CANCELADA, SolicitudCita.Estado.REPROGRAMADA]
        personas = [(n, f"{self.slug(n)}@{DOMINIO}", None) for n in NOMBRES]
        if cuenta_usuario:
            personas.insert(0, ("Usuario de prueba", cuenta_usuario.email, cuenta_usuario))
        resultado = []
        for i, (nombre, email, cuenta) in enumerate(personas):
            u = cuenta or self.cuenta(email, nombre.split()[0])
            if not u.last_name and " " in nombre and not cuenta:
                u.last_name = nombre.split(" ", 1)[1]
                u.save(update_fields=["last_name"])
            perfil = Motociclista.objects.filter(usuario=u).first()
            if perfil:
                resultado.append(perfil)
                continue
            perfil = Motociclista.objects.create(nombre=nombre, celular=f"57300999{2000 + i:04d}", usuario=u)
            resultado.append(perfil)
            n_motos = 2 if i % 4 == 0 else 1
            for k in range(n_motos):
                linea_nombre, color = MOTOS[(i + k * 7) % len(MOTOS)]
                linea = lineas.get(linea_nombre)
                km = 4000 + (i * 2300 + k * 5100) % 38000
                moto = Moto.objects.create(motociclista=perfil, linea=linea, color=color, modelo=2018 + (i + k) % 8,
                                           km_inicial=km - 1500, km_actual=km)
                for dias, delta in ((90, -1500), (40, -700), (0, 0)):
                    LecturaKm.objects.create(moto=moto, km=km + delta, fecha=self.hoy - timedelta(days=dias))
                for j, clave in enumerate(["aceite", "cadena-lubricar", "pastillas-del", "filtro-aire"][: 2 + i % 3]):
                    if clave in tareas:
                        Mantenimiento.objects.create(
                            moto=moto, tarea=tareas[clave], km=max(0, km - 600 * (j + 1)),
                            fecha=self.hoy - timedelta(days=25 * (j + 1)),
                            taller=publicados[(i + j) % len(publicados)] if j % 2 == 0 else None)
            moto_txt = str(perfil.motos.first().linea or "Moto")
            for j in range(1 + i % 3):  # citas en distintos estados, pasadas y futuras
                estado = estados[(i + j) % len(estados)]
                futura = estado in (SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.CONFIRMADA,
                                    SolicitudCita.Estado.REPROGRAMADA)
                SolicitudCita.objects.create(
                    taller=publicados[(i * 2 + j) % len(publicados)], nombre=nombre, telefono=perfil.celular[2:],
                    moto=moto_txt, servicio=servicios[(i + j) % len(servicios)], usuario=u, estado=estado,
                    fecha_preferida=self.hoy + timedelta(days=(3 + j) if futura else -(10 + 7 * j)),
                    hora=time(8 + (i + j) % 9) if estado != SolicitudCita.Estado.PENDIENTE else None,
                    detalle="Revisión general y lo que haga falta.",
                    motivo_cancelacion="No pude llevarla ese día." if estado == SolicitudCita.Estado.CANCELADA else "",
                    fecha_propuesta=self.hoy + timedelta(days=6) if estado == SolicitudCita.Estado.REPROGRAMADA else None,
                    hora_propuesta=time(15) if estado == SolicitudCita.Estado.REPROGRAMADA else None)
            if i % 2 == 0:  # reseña de un taller donde lo atendieron
                estrellas, comentario = RESENAS[i % len(RESENAS)]
                Resena.objects.create(taller=publicados[i % len(publicados)], usuario=u, nombre=nombre.split()[0],
                                      estrellas=estrellas, comentario=comentario)
        return resultado

    # ---------- Cupones ----------
    def cupones(self, talleres, moteros):
        publicados = [t for t in talleres if t.activo]
        planes = [
            ("10% en cambio de aceite y filtro", 45, True), ("Lavado de cadena gratis con tu mantenimiento", 30, True),
            ("Diagnóstico eléctrico a mitad de precio", 60, True), ("Revisión de frenos sin costo", -12, True),
            ("$15.000 de descuento en kit de arrastre", -30, True), ("2x1 en calibración de llantas", 20, False),
            ("Alineación de luces gratis para la técnico-mecánica", None, True),
        ]
        for k, (titulo, dias, activo) in enumerate(planes):
            cupon, creado = primero_o_crear(Cupon, titulo=titulo, defaults={
                "taller": publicados[k % len(publicados)], "activo": activo, "cupo": 40 if k % 2 == 0 else None,
                "valido_hasta": self.hoy + timedelta(days=dias) if dias is not None else None,
                "condiciones": "No acumulable con otras promociones. Presenta el código en el taller."})
            if not creado:
                continue
            for j, m in enumerate(moteros[k::4][:3]):  # algunos códigos entregados; uno canjeado
                CodigoCupon.objects.create(cupon=cupon, motociclista=m,
                                           canjeado_en=timezone.now() - timedelta(days=5) if j == 0 and dias and dias < 0 else None,
                                           canjeado_taller=cupon.taller if j == 0 and dias and dias < 0 else None)

    # ---------- Foro ----------
    def foro(self, moteros, talleres):
        autores = [m.usuario for m in moteros if m.usuario]
        cuenta_taller = next((t.usuario for t in talleres if t.usuario_id), None)
        for k, (titulo, cuerpo, respuestas) in enumerate(HILOS):
            pregunta, creada = primero_o_crear(Pregunta, titulo=titulo,
                                               defaults={"autor": autores[(k * 3) % len(autores)], "cuerpo": cuerpo})
            if not creada:
                continue
            for j, texto in enumerate(respuestas):
                autor = cuenta_taller if (j == 0 and cuenta_taller and k % 2 == 0) else autores[(k * 3 + j + 1) % len(autores)]
                Respuesta.objects.create(pregunta=pregunta, autor=autor, cuerpo=texto)
            if k == 1:
                Reporte.objects.get_or_create(usuario=autores[-1], pregunta=pregunta,
                                              defaults={"motivo": "Parece publicidad de un taller."})

    # ---------- Correo verificado ----------
    def verificar_todas(self):
        User = get_user_model()
        ahora = timezone.now()
        for u in User.objects.all():
            perfil = Perfil.de(u)
            cambios = []
            if not perfil.correo_verificado:
                perfil.correo_verificado = True
                cambios.append("correo_verificado")
            if not perfil.terminos_aceptados:
                perfil.terminos_aceptados = ahora
                cambios.append("terminos_aceptados")
            if cambios:
                perfil.save(update_fields=cambios)
        return User.objects.count()

    @staticmethod
    def slug(nombre):
        import unicodedata
        base = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
        return ".".join(base.split())
