"""Juego único de datos demo para la base LOCAL: solo cuentas @prueba.com, completas al 100 % y con el correo verificado.

Lo corre `manage.py preparar_demo_prueba` (idempotente: dos corridas dejan lo mismo). Contraseña común de todas las
cuentas: la variable de entorno PASSWORD_DEMO_PRUEBA o, si no existe, la que está en CLAVE_POR_DEFECTO (solo sirve en
local: el comando se niega a correr sin DEBUG, salvo --forzar). Nunca va a producción.

Cuentas (todas @prueba.com): admin, superadmin, usuario (motero), motero1…motero5, taller, taller2, taller3
(Valle de Aburrá), mecanicodomi, mecanico2, mecanico3 (a domicilio).
Imágenes: dibujadas con Pillow (talleres/demo_prueba_imagenes.py, domicilio/ilustraciones.py), guardadas en media/.
"""
import os
import secrets
from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from cupones.models import CodigoCupon, Cupon, Motociclista
from cuentas.models import Perfil, Suscripcion
from domicilio import ilustraciones
from domicilio.models import (FotoTrabajo, MecanicoDomicilio, PrecioMecanico, ResenaMecanico, SolicitudVisita,
                              TallerDomicilio, TipoServicio, Zona)
from logros.models import Canje
from garaje.models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from . import demo_prueba_imagenes as imagenes
from .models import (Barrio, FotoTaller, HorarioTaller, Marca, PrecioServicio, Resena, Servicio, SolicitudCita,
                     Taller)

CLAVE_POR_DEFECTO = "Prueba-TallerYa-26"  # solo local; cámbiala con PASSWORD_DEMO_PRUEBA
DOMINIOS_DEMO = ("@tallerya.local", "@demo.tallerya.test", "@demo.tallerya")
DOMINIO_PRUEBA = "@prueba.com"

# ---------------------------------------------------------------------------------------------------- cuentas
ADMINS = [("admin@prueba.com", "Admin", "de Prueba", False), ("superadmin@prueba.com", "Superadmin", "de Prueba", True)]

# (correo, nombre, apellido, celular, motos) — motos: (marca, línea, año, color, color2, apodo, km_inicial, km_actual, uso)
MOTEROS = [
    ("usuario@prueba.com", "Usuario", "de Prueba", "573009992000", []),  # si ya tiene motos solo se completa lo que falte
    ("motero1@prueba.com", "Andrea", "Londoño", "573105550101", [
        ("Honda", "XR 150L", 2021, "#c62828", "#1c2022", "La Roja", 9800, 21400, "ciudad"),
        ("Suzuki", "Gixxer 150", 2022, "#1565c0", "#1c2022", "Gixxy", 2100, 11900, "fines_semana")]),
    ("motero2@prueba.com", "Julián", "Restrepo", "573105550102", [
        ("AKT", "NKD 125", 2020, "#2e7d32", "#1c2022", "La Verde", 14500, 38200, "trabajo")]),
    ("motero3@prueba.com", "Carolina", "Zapata", "573105550103", [
        ("Honda", "Dio 110", 2023, "#f9a825", "#1c2022", "Dorita", 800, 7300, "ciudad")]),
    ("motero4@prueba.com", "Esteban", "Mejía", "573105550104", [
        ("Auteco Bajaj", "Pulsar NS 200", 2022, "#212121", "#e3a72f", "La Pulsar", 3200, 16800, "carretera"),
        ("Auteco Bajaj", "Boxer CT 125", 2019, "#6d4c41", "#1c2022", "La Boxer", 21000, 52400, "trabajo")]),
    ("motero5@prueba.com", "Luisa", "Ospina", "573105550105", [
        ("TVS", "Apache RTR 160", 2021, "#c62828", "#1c2022", "Apache", 6400, 24700, "ciudad")]),
]
PLUS = "motero1@prueba.com"

# Hoja de vida de las motos: (clave de tarea, hace cuántos km, hace cuántos días, ¿en taller?)
HOJA_VIDA = [("aceite", 1800, 70, True), ("filtro-aire", 5200, 190, False), ("bujia", 7000, 260, True), ("cadena-lubricar", 600, 20, False)]

# ---------------------------------------------------------------------------------------------------- talleres
TALLERES = [
    {"correo": "taller@prueba.com", "nombre": "Biela y Pistón Taller", "responsable": "Hernán Darío Villa", "tono": 0,
     "wa": "573105560001", "dir": "Carrera 70 # 44-18", "barrio": ("Laureles", "Medellín"), "coord": (6.24610, -75.59060),
     "desc": "Taller de barrio con 12 años en Laureles: mantenimiento, frenos, suspensión y sincronización con garantía por escrito.",
     "horario": ("Lun-Sáb 7:30am-7pm · Dom 9am-1pm", [(0, 5, time(7, 30), time(19)), (6, 6, time(9), time(13))]), "nivel": 2,
     "servicios": ["Cambio de aceite", "Frenos", "Kit de arrastre", "Mantenimiento general", "Suspensión", "Sistema eléctrico"],
     "marcas": ["Honda", "Yamaha", "Suzuki", "Auteco Bajaj"], "espec": ["frenos", "suspension", "arrastre"], "garantia": 3,
     "comp": ["presupuesto", "fotos", "piezas"], "domicilio": (["Laureles-Estadio", "La América", "Belén"], 25000),
     "equipo": [("Hernán Darío Villa", "Jefe de taller", 12, "Mantenimiento general"), ("Juliana Ruiz", "Técnico", 4, "Suspensión")],
     "cupon": ("20% en cambio de aceite", "Con filtro nuevo. No acumulable. Lunes a viernes.")},
    {"correo": "taller2@prueba.com", "nombre": "Pits Aburrá Motos", "responsable": "Gloria Elena Marín", "tono": 1,
     "wa": "573105560002", "dir": "Calle 36 # 51-27", "barrio": ("Santa María", "Itagüí"), "coord": (6.17420, -75.61120),
     "desc": "Especialistas en scooters, inyección electrónica y sistema eléctrico en Itagüí. Diagnóstico con escáner incluido en la revisión.",
     "horario": ("Lun-Vie 8am-6pm · Sáb 8am-2pm", [(0, 4, time(8), time(18)), (5, 5, time(8), time(14))]), "nivel": 2,
     "servicios": ["Cambio de aceite", "Sistema eléctrico", "Mantenimiento general", "Frenos", "Sincronización", "Llantas"],
     "marcas": ["Honda", "Yamaha", "TVS", "Hero", "AKT"], "espec": ["inyeccion", "scooters", "electrico"], "garantia": 2,
     "comp": ["presupuesto", "avisamos", "factura"], "domicilio": None,
     "equipo": [("Gloria Elena Marín", "Jefe de taller", 9, "Sistema eléctrico"), ("Anderson Cano", "Técnico", 5, "Inyección electrónica")],
     "cupon": ("Diagnóstico con escáner gratis", "Al hacer cualquier servicio de más de $80.000. Una vez por moto.")},
    {"correo": "taller3@prueba.com", "nombre": "Garaje Niquía Motos", "responsable": "Wilmar Tobón", "tono": 2,
     "wa": "573105560003", "dir": "Carrera 50 # 85-30", "barrio": ("Niquía", "Bello"), "coord": (6.33530, -75.54910),
     "desc": "Motos de trabajo y domiciliarios: cambio de aceite exprés, kit de arrastre, frenos y llantas sin hacerte perder el día.",
     "horario": ("Lun-Sáb 7am-6pm", [(0, 5, time(7), time(18))]), "nivel": 1,
     "servicios": ["Cambio de aceite", "Kit de arrastre", "Llantas", "Frenos", "Mantenimiento general", "Revisión técnico-mecánica"],
     "marcas": ["Auteco Bajaj", "AKT", "Honda", "Suzuki"], "espec": ["trabajo", "arrastre", "tecnomecanica"], "garantia": 1,
     "comp": ["presupuesto", "piezas", "factura"], "domicilio": None,
     "equipo": [("Wilmar Tobón", "Jefe de taller", 15, "Kit de arrastre"), ("Dairo Ríos", "Ayudante", 2, "Llantas")],
     "cupon": ("Lavado de cadena gratis", "Con el cambio de aceite. Para motos de trabajo. No acumulable.")},
]
PRECIOS_TALLER = {  # servicio → [(cilindraje, desde, hasta)]
    "Cambio de aceite": [("baja", 38000, 58000), ("media", 75000, 125000)],
    "Frenos": [("baja", 45000, 78000), ("media", 85000, 145000)],
    "Kit de arrastre": [("baja", 150000, 250000), ("media", 290000, 490000)],
    "Mantenimiento general": [("", 90000, 160000)],
    "Suspensión": [("media", 170000, 280000)],
    "Sistema eléctrico": [("", 40000, 70000)],
    "Sincronización": [("baja", 110000, 170000), ("media", 190000, 310000)],
    "Llantas": [("", 30000, 60000)],
    "Revisión técnico-mecánica": [("", 32000, 48000)],
}

# ---------------------------------------------------------------------------------------------------- mecánicos
MECANICOS = [
    {"correo": "mecanicodomi@prueba.com", "nombre": "Mecánico de prueba", "wa": "573105570001", "anios": 8, "tono": 0,
     "zonas": ["Laureles-Estadio", "La América", "Belén", "Guayabal"], "horario": "Lun-Sáb 7am-6pm", "tarifa": 20000,
     "servicios": ["Cambio de aceite", "Frenos", "Mantenimiento general", "Batería y arranque", "Diagnóstico"],
     "marcas": ["Honda", "Yamaha", "Suzuki"], "espec": ["frenos", "electrico"], "comp": ["presupuesto", "avisamos"], "garantia": 1,
     "desc": "Mecánico independiente con 8 años de experiencia: voy a donde estés con las herramientas y los repuestos básicos.",
     "herramientas": "Caja de herramientas completa, multímetro, gato de moto, compresor portátil",
     "cupon": ("Visita gratis en el primer servicio", "Solo zonas de Laureles y La América. Una vez por motero.")},
    {"correo": "mecanico2@prueba.com", "nombre": "Fredy Alzate", "wa": "573105570002", "anios": 11, "tono": 1,
     "zonas": ["Envigado", "Sabaneta", "Itagüí", "El Poblado"], "horario": "Lun-Vie 8am-5pm · Sáb 8am-1pm", "tarifa": 25000,
     "servicios": ["Cambio de aceite", "Kit de arrastre", "Inyección electrónica", "Sistema eléctrico", "Carburación"],
     "marcas": ["Honda", "Yamaha", "Auteco Bajaj", "TVS"], "espec": ["inyeccion", "carburacion", "arrastre"], "comp": ["fotos", "presupuesto"],
     "garantia": 2, "desc": "Atiendo en Envigado, Sabaneta e Itagüí. Especialista en carburación e inyección: te explico qué se daña y por qué.",
     "herramientas": "Escáner básico, juego de carburación, extractor de piñones, llave de torque",
     "cupon": ("$10.000 de descuento en la visita", "Para servicios de más de $80.000. Válido entre semana.")},
    {"correo": "mecanico3@prueba.com", "nombre": "Camilo Betancur", "wa": "573105570003", "anios": 6, "tono": 2,
     "zonas": ["Bello", "Copacabana", "Robledo", "Castilla"], "horario": "Todos los días 7am-7pm", "tarifa": 18000,
     "servicios": ["Cambio de aceite", "Llantas y despinche", "Batería y arranque", "Frenos", "Revisión antes de comprar moto usada"],
     "marcas": ["Auteco Bajaj", "AKT", "Honda", "Suzuki"], "espec": ["trabajo", "frenos"], "comp": ["avisamos", "piezas"], "garantia": 1,
     "desc": "Mecánico a domicilio en el norte del Valle de Aburrá: despinche, batería y revisión de motos usadas antes de que las compres.",
     "herramientas": "Kit de despinche, cargador de batería, gato, multímetro, linterna frontal",
     "cupon": ("Despinche gratis con cambio de llanta", "Solo mano de obra. No incluye la llanta.")},
]
PRECIOS_MEC = {
    "Cambio de aceite": [("baja", 30000, 48000), ("media", 60000, 100000)],
    "Frenos": [("baja", 40000, 70000), ("media", 75000, 125000)],
    "Mantenimiento general": [("", 80000, 140000)],
    "Batería y arranque": [("", 25000, 60000)],
    "Diagnóstico": [("", 30000, 50000)],
    "Kit de arrastre": [("baja", 130000, 220000), ("media", 260000, 430000)],
    "Inyección electrónica": [("", 60000, 110000)],
    "Sistema eléctrico": [("", 35000, 65000)],
    "Carburación": [("", 45000, 80000)],
    "Llantas y despinche": [("", 15000, 35000)],
    "Revisión antes de comprar moto usada": [("", 40000, 70000)],
}

# ---------------------------------------------------------------------------------------------------- actividad
# Citas a talleres: (taller, motero, estado, servicio, días desde hoy, detalle)
CITAS = [
    (0, 1, "pendiente", "Cambio de aceite", 2, "Ya le toca el aceite y quiero que revisen el ruido de la cadena."),
    (0, 2, "confirmada", "Frenos", 1, "Las pastillas delanteras chillan desde hace una semana."),
    (0, 0, "atendida", "Mantenimiento general", -12, "Revisión completa antes del viaje a la costa."),
    (0, 3, "reprogramada", "Cambio de aceite", 4, "Puedo ir en la tarde, después de las 3."),
    (0, 4, "cancelada", "Suspensión", -5, "La moto hace un golpeteo adelante cuando frena."),
    (1, 1, "atendida", "Sistema eléctrico", -20, "El tablero se apaga cuando acelero."),
    (1, 3, "confirmada", "Cambio de aceite", 3, "Scooter, primer servicio de los 5.000 km."),
    (1, 5, "pendiente", "Sincronización", 5, "Se siente falta de fuerza en subida."),
    (2, 2, "atendida", "Kit de arrastre", -30, "La cadena está muy estirada, la moto es de trabajo."),
    (2, 4, "atendida", "Llantas", -9, "Cambio de llanta trasera, está lisa."),
    (2, 5, "reprogramada", "Revisión técnico-mecánica", 6, "Necesito dejarla lista para la tecno."),
]
# Reseñas a talleres: (taller, motero, estrellas, comentario, respuesta, verificada)
RESENAS_TALLER = [
    (0, 0, 5, "Me explicaron cada cambio y me mandaron fotos de las piezas. La moto quedó como nueva para el viaje.",
     "¡Gracias por la confianza! Buen viaje y nos cuenta cómo le fue.", True),
    (0, 2, 4, "Buen precio y rápidos. Solo que tocó esperar un rato porque había mucha moto.", "Gracias, vamos a organizar mejor las citas.", False),
    (0, 3, 5, "Honestos: me dijeron qué se podía dejar para después y no me cobraron de más.", "", False),
    (1, 1, 5, "Encontraron la falla eléctrica que otros dos talleres no vieron. Muy profesionales.", "Nos alegra que quedara resuelto. ¡Gracias, Andrea!", True),
    (1, 3, 4, "Muy buen servicio para scooters. El precio fue el que cotizaron.", "", False),
    (1, 5, 5, "Me atendieron con cita y a la hora. Recomendado para inyección.", "Gracias por tu reseña, Luisa.", False),
    (2, 2, 5, "Cambio de kit de arrastre rápido y barato. Ideal para motos de trabajo.", "Cuando quiera, con gusto. ¡Gracias, Julián!", True),
    (2, 4, 4, "Llanta cambiada en menos de una hora. Faltó un poquito de aire en la nueva, pero lo corrigieron.", "Gracias por avisarnos, ya lo revisamos con el equipo.", True),
    (2, 0, 4, "Fui de paso a que revisaran la cadena de una de mis motos. Buena atención.", "", False),
]
# Visitas a mecánicos: (mecánico, motero, estado, servicio, zona, días, detalle)
VISITAS = [
    (0, 1, "pendiente", "Cambio de aceite", "Laureles-Estadio", 2, "Prefiero en el parqueadero del edificio, en la mañana."),
    (0, 0, "atendida", "Batería y arranque", "La América", -15, "No arranca desde el lunes."),
    (0, 3, "cotizada", "Frenos", "Belén", 3, "Frenos traseros de tambor, la scooter se arrastra al frenar."),
    (1, 4, "atendida", "Carburación", "Envigado", -18, "La Boxer se apaga en ralentí."),
    (1, 2, "confirmada", "Cambio de aceite", "Itagüí", 1, "Después de las 5 p. m. por favor."),
    (1, 5, "cancelada", "Inyección electrónica", "Sabaneta", -4, "Se resolvió sola, gracias."),
    (2, 2, "atendida", "Llantas y despinche", "Bello", -10, "Despinche en la vía, cerca a Niquía."),
    (2, 4, "pendiente", "Revisión antes de comprar moto usada", "Robledo", 4, "Una Pulsar 2019, la vendedora está en Robledo."),
    (2, 0, "cotizada", "Batería y arranque", "Castilla", 2, "La batería no sostiene la carga."),
]
RESENAS_MEC = [
    (0, 0, 5, "Llegó en 40 minutos y me cambió la batería en la puerta de la casa. Cobró lo que dijo.", "Gracias, ¡a la orden siempre!"),
    (0, 3, 4, "Muy puntual y amable. Me explicó por qué estaban gastados los frenos.", ""),
    (1, 4, 5, "Arregló la carburación de mi Boxer, que ya nadie quería tocar. Mil gracias.", "Gracias, Esteban. ¡Que le rinda!"),
    (1, 2, 5, "Trabajo limpio y con factura de los repuestos. Muy recomendado en Envigado.", ""),
    (2, 2, 4, "Me despinchó en plena vía y siguió mi ruta de reparto sin perder el día.", "Gracias, Julián. Para eso estamos."),
    (2, 4, 5, "Me revisó una moto usada antes de comprarla y me ahorró un mal negocio.", ""),
]


# ---------------------------------------------------------------------------------------------------- limpieza
def _demo_q():
    q = Q()
    for dom in DOMINIOS_DEMO:
        q |= Q(email__iendswith=dom)
    return q


def conjuntos_demo():
    """Qué se borraría: usuarios demo (sin superusuarios), talleres y mecánicos que no son de cuentas @prueba.com."""
    U = get_user_model()
    usuarios = U.objects.filter(_demo_q()).exclude(is_superuser=True).exclude(email__iendswith=DOMINIO_PRUEBA)
    talleres = Taller.objects.exclude(usuario__email__iendswith=DOMINIO_PRUEBA)
    mecs = MecanicoDomicilio.objects.exclude(usuario__email__iendswith=DOMINIO_PRUEBA)
    moteros = Motociclista.objects.filter(Q(usuario__in=usuarios) | Q(usuario__isnull=True))
    return usuarios, talleres, mecs, moteros


def resumen_demo():
    usuarios, talleres, mecs, moteros = conjuntos_demo()
    return {
        "usuarios": list(usuarios.values_list("email", flat=True)),
        "talleres": list(talleres.values_list("nombre", flat=True)),
        "mecanicos": list(mecs.values_list("nombre", flat=True)),
        "moteros": moteros.count(),
        "resenas": Resena.objects.filter(taller__in=talleres).count() + ResenaMecanico.objects.filter(mecanico__in=mecs).count(),
        "citas": SolicitudCita.objects.filter(taller__in=talleres).count() + SolicitudVisita.objects.filter(mecanico__in=mecs).count(),
        "cupones": Cupon.objects.filter(Q(taller__in=talleres) | Q(mecanico__in=mecs)).count(),
        "fotos": FotoTaller.objects.filter(taller__in=talleres).count() + FotoTrabajo.objects.filter(mecanico__in=mecs).count(),
    }


def limpiar_demo():
    """Borra todo lo demo (y los archivos de sus fotos). Devuelve el resumen de lo borrado."""
    resumen = resumen_demo()
    usuarios, talleres, mecs, moteros = conjuntos_demo()
    archivos = [f.name for f in (*(t.foto for t in talleres), *(m.foto for m in mecs)) if f]
    archivos += [f.imagen.name for f in FotoTaller.objects.filter(taller__in=talleres) if f.imagen]
    archivos += [f.video.name for f in FotoTaller.objects.filter(taller__in=talleres) if f.video]
    archivos += [f.imagen.name for f in FotoTrabajo.objects.filter(mecanico__in=mecs) if f.imagen]
    archivos += [p.avatar_foto.name for p in Perfil.objects.filter(usuario__in=usuarios) if p.avatar_foto]
    with transaction.atomic():
        cupones = Cupon.objects.filter(Q(taller__in=talleres) | Q(mecanico__in=mecs))
        Canje.objects.filter(codigo__in=CodigoCupon.objects.filter(Q(cupon__in=cupones) | Q(motociclista__in=moteros))).delete()
        moteros.delete()
        CodigoCupon.objects.filter(cupon__in=cupones).delete()
        talleres.delete()
        mecs.delete()
        usuarios.delete()
    for nombre in archivos:
        try:
            default_storage.delete(nombre)
        except OSError:
            pass
    return resumen


# ---------------------------------------------------------------------------------------------------- preparar
def _clave():
    return os.environ.get("PASSWORD_DEMO_PRUEBA") or CLAVE_POR_DEFECTO


def _usuario(correo, nombre, apellido, staff=False, superuser=False):
    U = get_user_model()
    u = U.objects.filter(email__iexact=correo).first()
    if not u:
        u = U(username=correo, email=correo)
    u.first_name = u.first_name or nombre
    u.last_name = u.last_name or apellido
    u.is_staff = staff or u.is_staff
    u.is_superuser = superuser or u.is_superuser
    u.is_active = True
    u.set_password(_clave())
    u.save()
    perfil, _ = Perfil.objects.get_or_create(usuario=u)
    perfil.correo_verificado = True
    perfil.terminos_aceptados = perfil.terminos_aceptados or timezone.now()
    perfil.guia_terminada = perfil.guia_terminada or timezone.now()
    if not perfil.avatar_foto:
        perfil.avatar_foto.save("avatar.jpg", ilustraciones.avatar((nombre[:1] + apellido.split()[-1][:1]), tono=len(correo)), save=False)
    perfil.save()
    return u


def _servicio_taller(nombre):
    return Servicio.objects.get_or_create(nombre=nombre)[0]


def _tipo_servicio(nombre):
    return TipoServicio.objects.get_or_create(nombre=nombre)[0]


def _marca(nombre):
    return Marca.objects.get_or_create(nombre=nombre)[0]


def _zona(nombre):
    return Zona.objects.filter(nombre=nombre).first() or Zona.objects.get_or_create(nombre=nombre, ciudad=nombre)[0]


def _taller(cfg, usuario):
    barrio = Barrio.objects.get_or_create(nombre=cfg["barrio"][0], ciudad=cfg["barrio"][1])[0]
    t = Taller.objects.filter(usuario=usuario).first() or Taller(usuario=usuario, barrio=barrio)
    t.nombre = cfg["nombre"]
    t.responsable = cfg["responsable"]
    t.whatsapp = cfg["wa"]
    t.direccion = t.direccion or cfg["dir"]
    t.descripcion = cfg["desc"]
    t.horario = cfg["horario"][0]
    t.nivel_precio = cfg["nivel"]
    t.especialidades = cfg["espec"]
    t.compromisos = cfg["comp"]
    t.garantia_meses = cfg["garantia"]
    t.equipo = [{"nombre": n, "rol": r, "anios": a, "especialidad": e,
                 "servicio": _servicio_taller(s).pk if (s := next((x for x in cfg["servicios"] if x == e), None)) else None}
                for n, r, a, e in cfg["equipo"]]
    t.latitud, t.longitud = Decimal(str(cfg["coord"][0])), Decimal(str(cfg["coord"][1]))
    t.ubicacion_exacta = True
    t.mostrar_precios = True
    t.activo = t.verificado = True
    t.save()
    if not t.foto:
        t.foto.save("fachada.jpg", imagenes.fachada(t.nombre, cfg["tono"]), save=True)
    if t.fotos.count() < 4:
        extra = [imagenes.interior(cfg["tono"]), ilustraciones.trabajo("Cambio de aceite"), ilustraciones.trabajo("Frenos"),
                 imagenes.fachada(t.nombre, cfg["tono"] + 1)]
        for i, (img, desc) in enumerate(zip(extra, ["Nuestro taller por dentro", "Cambio de aceite", "Revisión de frenos", "Entrada del taller"])):
            if not t.fotos.filter(orden=i).exists():
                FotoTaller.objects.create(taller=t, imagen=img, descripcion=desc, orden=i)
    if not t.horarios.exists():
        for d1, d2, abre, cierra in cfg["horario"][1]:
            for dia in range(d1, d2 + 1):
                HorarioTaller.objects.create(taller=t, dia=dia, abre=abre, cierra=cierra)
    t.servicios.set([_servicio_taller(s) for s in cfg["servicios"]])
    t.marcas.set([_marca(m) for m in cfg["marcas"]])
    for serv, filas in PRECIOS_TALLER.items():
        if serv not in cfg["servicios"]:
            continue
        for cil, desde, hasta in filas:
            PrecioServicio.objects.get_or_create(taller=t, servicio=_servicio_taller(serv), cilindraje=cil,
                                                 defaults={"desde": desde, "hasta": hasta})
    PrecioServicio.objects.filter(taller=t).update(actualizado=timezone.now())  # «precios confirmados»: sin aviso de vencidos
    titulo, cond = cfg["cupon"]
    Cupon.objects.update_or_create(taller=t, titulo=titulo, defaults={
        "condiciones": cond, "valido_hasta": timezone.localdate() + timedelta(days=120), "cupo": 100, "activo": True, "publico": True})
    if cfg["domicilio"]:
        zonas, tarifa = cfg["domicilio"]
        d, _ = TallerDomicilio.objects.get_or_create(taller=t, defaults={"activo": True, "tarifa_visita": tarifa, "urgencias": True})
        d.activo = True
        d.save()
        d.zonas.set([_zona(z) for z in zonas])
        d.servicios.set([_tipo_servicio(s) for s in ("Cambio de aceite", "Frenos", "Mantenimiento general")])
    return t


def _mecanico(cfg, usuario):
    m = MecanicoDomicilio.objects.filter(usuario=usuario).first() or MecanicoDomicilio(usuario=usuario)
    m.nombre = cfg["nombre"]
    m.whatsapp = cfg["wa"]
    m.anios_experiencia = cfg["anios"]
    m.horario = cfg["horario"]
    m.tarifa_visita = cfg["tarifa"]
    m.urgencias = True
    m.descripcion = cfg["desc"]
    m.especialidades = cfg["espec"]
    m.compromisos = cfg["comp"]
    m.garantia_meses = cfg["garantia"]
    m.herramientas = cfg["herramientas"]
    m.referencias = "Taller Biela y Pistón (Laureles) y clientes recurrentes de la zona; se pueden consultar por WhatsApp."
    m.estado = MecanicoDomicilio.Estado.APROBADO
    m.verificado = True
    m.mostrar_precios = True
    m.poner_cedula(f"98{cfg['wa'][-8:]}")  # cédula ficticia: solo se guarda la huella y 4 dígitos
    m.save()
    m.zonas.set([_zona(z) for z in cfg["zonas"]])
    m.servicios.set([_tipo_servicio(s) for s in cfg["servicios"]])
    m.marcas.set([_marca(x) for x in cfg["marcas"]])
    if not m.foto:
        m.foto.save("avatar.jpg", ilustraciones.avatar(m.iniciales, tono=cfg["tono"]), save=True)
    if m.fotos_trabajo.count() < 3:
        for s in cfg["servicios"][: 3 - m.fotos_trabajo.count()]:
            FotoTrabajo.objects.create(mecanico=m, imagen=ilustraciones.trabajo(s))
    for serv, filas in PRECIOS_MEC.items():
        if serv not in cfg["servicios"]:
            continue
        for cil, desde, hasta in filas:
            PrecioMecanico.objects.get_or_create(mecanico=m, servicio=_tipo_servicio(serv), cilindraje=cil,
                                                 defaults={"desde": desde, "hasta": hasta})
    PrecioMecanico.objects.filter(mecanico=m).update(actualizado=timezone.now())
    titulo, cond = cfg["cupon"]
    Cupon.objects.update_or_create(mecanico=m, titulo=titulo, defaults={
        "condiciones": cond, "valido_hasta": timezone.localdate() + timedelta(days=120), "cupo": 100, "activo": True, "publico": True})
    return m


def _linea(marca, nombre):
    return (LineaMoto.objects.filter(marca__nombre=marca, nombre=nombre).first()
            or LineaMoto.objects.filter(activo=True).first())


def _completar_moto(moto, talleres):
    """Llena lo que falte de una moto (placa, SOAT, tecno, lecturas y hoja de vida) sin tocar lo que ya tiene."""
    hoy = timezone.localdate()
    if moto.km_actual < moto.km_inicial:
        moto.km_actual = moto.km_inicial
    if moto.km_actual == moto.km_inicial:
        moto.km_actual = moto.km_inicial + 3500  # una moto sin recorrido no sirve para mostrar el plan
    moto.perfil_uso = moto.perfil_uso or ("ciudad", "fines_semana", "trabajo")[moto.pk % 3]
    moto.apodo = moto.apodo or f"Moto {moto.pk}"
    moto.placa = moto.placa or f"PRB{moto.pk % 100:02d}D"
    moto.soat_vence = moto.soat_vence or hoy + timedelta(days=95 + moto.pk % 7 * 20)
    moto.tecno_vence = moto.tecno_vence or hoy + timedelta(days=210 + moto.pk % 5 * 30)
    moto.matricula = moto.matricula or date(max(2000, moto.modelo), 3, 15)
    moto.save()
    if not moto.lecturas.exists():
        for atras, dias in ((0, 0), (900, 30), (2100, 75)):
            LecturaKm.objects.create(moto=moto, km=max(moto.km_inicial, moto.km_actual - atras), fecha=hoy - timedelta(days=dias))
    if not moto.mantenimientos.exists():
        for i, (clave, atras, dias, en_taller) in enumerate(HOJA_VIDA):
            tarea = TareaMantenimiento.objects.filter(clave=clave).first()
            if not tarea:
                continue
            Mantenimiento.objects.create(
                moto=moto, tarea=tarea, km=max(0, moto.km_actual - atras), fecha=hoy - timedelta(days=dias + i),
                taller=talleres[(moto.pk + i) % len(talleres)] if en_taller else None,
                taller_otro="" if en_taller else "Lo hice yo", notas="Servicio registrado en la hoja de vida.")


def _moteros(talleres):
    resultado = []
    for correo, nombre, apellido, celular, motos in MOTEROS:
        u = _usuario(correo, nombre, apellido)
        mot = Motociclista.objects.filter(usuario=u).first()
        if not mot:
            mot = Motociclista.objects.create(usuario=u, nombre=f"{nombre} {apellido}", celular=celular)
        if not motos and not mot.motos.exists():
            motos = [("Honda", "XR 150L", 2020, "#1565c0", "#1c2022", "La Azul", 5000, 18000, "ciudad")]
        for marca, linea, anio, color, color2, apodo, ki, ka, uso in motos:
            moto = Moto.objects.filter(motociclista=mot, apodo=apodo).first() or Moto(motociclista=mot, apodo=apodo)
            if not moto.pk:
                moto.linea, moto.modelo, moto.color, moto.color_secundario = _linea(marca, linea), anio, color, color2
                moto.km_inicial, moto.km_actual, moto.perfil_uso = ki, ka, uso
                moto.save()
        for moto in mot.motos.all():
            _completar_moto(moto, talleres)
        if correo == PLUS and not mot.es_plus:
            Suscripcion.objects.create(motociclista=mot, estado=Suscripcion.Estado.SOLICITADA, referencia_pago="DEMO").activar(30)
        resultado.append((u, mot))
    return resultado


def _moto_texto(mot):
    m = mot.motos.first()
    return str(m.linea) if m and m.linea else "Moto"


def _actividad(talleres, mecs, moteros):
    hoy = timezone.localdate()
    for ti, mi, estado, serv, dias, detalle in CITAS:
        t, (u, mot) = talleres[ti], moteros[mi]
        if SolicitudCita.objects.filter(taller=t, usuario=u, detalle=detalle).exists():
            continue
        c = SolicitudCita(taller=t, usuario=u, nombre=mot.nombre, telefono=mot.celular, moto=_moto_texto(mot),
                          servicio=_servicio_taller(serv), fecha_preferida=hoy + timedelta(days=dias), detalle=detalle,
                          estado=estado, token=secrets.token_urlsafe(16))
        if estado in ("confirmada", "atendida"):
            c.hora = time(9 + dias % 6, 0)
        if estado == "reprogramada":
            c.fecha_propuesta, c.hora_propuesta = hoy + timedelta(days=dias + 1), time(15, 30)
            c.nota_taller = "Ese día tenemos mucho trabajo en la mañana: ¿te sirve en la tarde?"
        if estado == "cancelada":
            c.motivo_cancelacion = "El motero canceló: resolvió el problema por su cuenta."
        if estado == "atendida":
            c.cotizacion_desde, c.cotizacion_hasta, c.cotizacion_incluye = 60000, 90000, "Mano de obra y repuestos básicos"
        c.save()
    for ti, mi, estrellas, comentario, respuesta, verificada in RESENAS_TALLER:
        t, (u, mot) = talleres[ti], moteros[mi]
        r = Resena.objects.filter(taller=t, usuario=u).first() or Resena(taller=t, usuario=u)
        r.nombre, r.estrellas, r.comentario, r.verificada, r.visible = mot.nombre.split()[0], estrellas, comentario, verificada, True
        r.respuesta, r.respondida_en = respuesta, (timezone.now() if respuesta else None)
        r.save()
    for mi_, ui, estado, serv, zona, dias, detalle in VISITAS:
        m, (u, mot) = mecs[mi_], moteros[ui]
        if SolicitudVisita.objects.filter(mecanico=m, usuario=u, detalle=detalle).exists():
            continue
        v = SolicitudVisita(mecanico=m, usuario=u, nombre=mot.nombre, telefono=mot.celular, moto=_moto_texto(mot),
                            servicio=_tipo_servicio(serv), zona=_zona(zona), detalle=detalle, estado=estado)
        if estado in ("cotizada", "confirmada", "atendida"):
            v.cotizacion_desde, v.cotizacion_hasta, v.cotizacion_incluye = 45000, 80000, "Visita, mano de obra y revisión"
            v.cotizacion_vence = hoy + timedelta(days=7)
            v.nota = "Llevo los repuestos básicos; si hace falta otra pieza te aviso antes."
        if estado in ("confirmada", "atendida"):
            v.fecha_propuesta, v.hora_propuesta = hoy + timedelta(days=dias), time(10, 0)
        v.save()
    for mi_, ui, estrellas, comentario, respuesta in RESENAS_MEC:
        m, (u, mot) = mecs[mi_], moteros[ui]
        r = ResenaMecanico.objects.filter(mecanico=m, usuario=u).first() or ResenaMecanico(mecanico=m, usuario=u)
        r.nombre, r.estrellas, r.comentario, r.visible = mot.nombre.split()[0], estrellas, comentario, True
        r.respuesta, r.respondida_en = respuesta, (timezone.now() if respuesta else None)
        r.save()


def preparar():
    """Crea o completa todas las cuentas @prueba.com. Devuelve {correo: objeto de su perfil} para verificar."""
    for correo, nombre, apellido, su in ADMINS:
        _usuario(correo, nombre, apellido, staff=True, superuser=su)
    talleres = [_taller(c, _usuario(c["correo"], c["responsable"].split()[0], c["responsable"].split()[-1])) for c in TALLERES]
    mecs = [_mecanico(c, _usuario(c["correo"], c["nombre"].split()[0], c["nombre"].split()[-1])) for c in MECANICOS]
    moteros = _moteros(talleres)
    _actividad(talleres, mecs, moteros)
    return talleres, mecs, moteros


def _pct_motero(u, mot):
    """El motero no tiene barra de progreso en la app: se mide con lo que el demo exige (correo, avatar, celular, motos, plan, hoja de vida)."""
    motos = list(mot.motos.all())
    pasos = [u.perfil.correo_verificado, bool(u.perfil.avatar_foto), bool(mot.celular), bool(motos),
             all(m.km_actual >= m.km_inicial and m.perfil_uso for m in motos),
             all(m.mantenimientos.exists() and m.lecturas.exists() for m in motos),
             bool(Resena.objects.filter(usuario=u).exists() or ResenaMecanico.objects.filter(usuario=u).exists()),
             bool(SolicitudCita.objects.filter(usuario=u).exists() or SolicitudVisita.objects.filter(usuario=u).exists())]
    return round(100 * sum(pasos) / len(pasos)), []


def verificar():
    """Tabla [(correo, rol, % perfil, faltantes)] con las mismas funciones que pintan «Por hacer» en los paneles."""
    from .views import _completitud
    filas = []
    for u in get_user_model().objects.filter(email__iendswith=DOMINIO_PRUEBA).order_by("email"):
        perfil_ok = u.perfil.correo_verificado and bool(u.perfil.avatar_foto)
        t, m, mot = getattr(u, "taller", None), getattr(u, "mecanico_domicilio", None), getattr(u, "motociclista", None)
        if u.is_staff:
            rol, pct, falta = "admin" if not u.is_superuser else "superadmin", 100 if perfil_ok else 50, []
        elif t:
            c = _completitud(t)
            rol, pct, falta = "taller", c["pct"], c["faltan"] + ([] if t.latitud and t.ubicacion_exacta else ["Ubicación"])
        elif m:
            pasos = m.pasos()
            rol, pct, falta = "mecánico", round(100 * sum(h for _, h, _ in pasos) / len(pasos)), [x for x, h, _ in pasos if not h]
        elif mot:
            rol = "motero"
            pct, falta = _pct_motero(u, mot)
        else:
            rol, pct, falta = "sin perfil", 0, ["Perfil"]
        filas.append((u.email, rol, pct, falta))
    return filas
