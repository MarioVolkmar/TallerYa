"""Dos perfiles de taller completos para el demo (cargar_demo): Taller Doble Leva (Belén) y Torque Sur Motos (Envigado).

Son ficticios (nombres comprobados contra negocios reales de Medellín/Envigado el 15-nov-2026) y el WhatsApp es el
mismo número de prueba de los demás talleres demo. Los precios son rangos orientativos de Medellín 2026: el criterio
está en informes_noche/talleres-demo.md. Fotos y videos de Pexels (licencia libre): ver talleres/demo/fuentes.txt.

Idempotente: si el taller ya existe solo se le llenan los campos estandarizados vacíos (completar_perfil). Las citas con servicio hecho solo se crean si existen las motos de
la cuenta demo del garaje (solo en desarrollo, DEBUG).
"""
from datetime import time, timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils import timezone

from .models import (Barrio, FotoTaller, HorarioTaller, Marca, PrecioServicio, Resena, Servicio, SolicitudCita,
                     Taller)

CARPETA = Path(__file__).resolve().parent / "demo"

# Servicios extra que estos perfiles necesitan para publicar precios (se suman a los del directorio).
SERVICIOS_EXTRA = ["Kit de arrastre", "Sincronización"]

# (servicio, cilindraje, desde, hasta) en COP. "" = cualquier cilindraje; baja ≤150 cc; media 150-400; alta >400.
PRECIOS_DOBLE_LEVA = [
    ("Cambio de aceite", "baja", 38000, 55000),
    ("Cambio de aceite", "media", 70000, 120000),
    ("Kit de arrastre", "baja", 140000, 240000),
    ("Kit de arrastre", "media", 280000, 480000),
    ("Frenos", "baja", 45000, 75000),
    ("Frenos", "media", 80000, 140000),
    ("Sincronización", "baja", 110000, 170000),
    ("Sincronización", "media", 180000, 300000),
    ("Revisión técnico-mecánica", "", 30000, 45000),
    ("Sistema eléctrico", "", 40000, 60000),
]
PRECIOS_TORQUE_SUR = [
    ("Cambio de aceite", "baja", 45000, 60000),
    ("Cambio de aceite", "media", 85000, 130000),
    ("Cambio de aceite", "alta", 170000, 290000),
    ("Kit de arrastre", "media", 300000, 520000),
    ("Kit de arrastre", "alta", 650000, 1300000),
    ("Frenos", "media", 90000, 150000),
    ("Frenos", "alta", 180000, 340000),
    ("Sincronización", "media", 200000, 320000),
    ("Sincronización", "alta", 380000, 650000),
    ("Suspensión", "media", 170000, 280000),
    ("Suspensión", "alta", 320000, 520000),
    ("Revisión técnico-mecánica", "", 35000, 50000),
    ("Sistema eléctrico", "", 50000, 70000),
]

TALLERES = [
    {
        "clave": "dobleleva",
        "datos": {
            "nombre": "Taller Doble Leva",
            "responsable": "Jhon Fredy Ospina",
            "direccion": "Carrera 76 # 30A-45, Belén Rosales",
            "barrio": ("Belén", "Medellín"),
            "horario": "Lun-Vie 8am-6pm · Sáb 8am-2pm",
            "nivel_precio": 1,
            "verificado": True, "destacado": True, "agenda_activa": True,
            "latitud": Decimal("6.229480"), "longitud": Decimal("-75.597310"),
            "descripcion": ("Taller familiar en Belén Rosales desde 2012. Motos de trabajo y scooters hasta 200 cc: "
                            "el mantenimiento que hace que tu moto no te deje tirado."),
            "equipo": [
                {"nombre": "Jhon Fredy Ospina", "rol": "Jefe de taller", "anios": 20,
                 "especialidad": "Inyección electrónica y carburación"},
                {"nombre": "Yésica Arango", "rol": "Técnica", "anios": 8,
                 "especialidad": "Frenos, suspensión y kit de arrastre"},
                {"nombre": "Mateo Cardona", "rol": "Técnico SENA", "anios": 4, "especialidad": "Scooters y transmisión CVT"},
            ],
            "especialidades": ["inyeccion", "carburacion", "scooters", "trabajo", "frenos", "arrastre"],
            "garantia_meses": 1,
            "compromisos": ["fotos", "piezas", "presupuesto"],
        },
        "servicios": ["Mantenimiento general", "Cambio de aceite", "Frenos", "Sistema eléctrico",
                      "Revisión técnico-mecánica", "Kit de arrastre", "Sincronización"],
        "marcas": ["AKT", "Auteco Bajaj", "Honda", "Yamaha", "Suzuki", "TVS"],
        "horarios": [(d, time(8), time(18)) for d in range(5)] + [(5, time(8), time(14))],
        "precios": PRECIOS_DOBLE_LEVA,
        "fotos": [("dobleleva-1.webp", "Sincronización de carburador"),
                  ("dobleleva-2.webp", "Freno de disco trasero revisado"),
                  ("dobleleva-3.webp", "Banco de trabajo"),
                  ("dobleleva-4.webp", "Ajuste de tornillería")],
        "video": ("dobleleva-video.mp4", "dobleleva-video.webp", "Un día en el taller"),
        "resenas": [
            ("Diana M.", 5, "Llevé la Crypton porque se apagaba en los semáforos. Le hicieron sincronización y me "
                            "mandaron fotos de todo. Desde ahí arranca de una. Precio justo.",
             "¡Gracias Diana! Era el sensor de temperatura sucio, ya sabes: cada 6.000 km revisión."),
            ("Esteban R.", 5, "Cambio de aceite rapidísimo, mientras me tomaba un tinto ya estaba lista.", ""),
            ("Paola G.", 4, "Buen trabajo con el kit de arrastre de mi NKD. Me tocó esperar un poco más de lo que "
                            "dijeron porque no tenían el piñón, pero me avisaron.",
             "Tienes razón Paola, ya tenemos más kits de AKT en bodega para que no se repita."),
            ("Wilmar C.", 5, "Soy domiciliario y la moto es mi herramienta. Aquí me la tienen a punto y no me "
                             "cobran cosas que no necesita.", ""),
            ("Luisa F.", 3, "El trabajo bien, pero el sábado estaba muy lleno y no había dónde sentarse.",
             "Gracias por decirnos, Luisa. Los sábados mejor separa cita por TallerYa y te esperamos a la hora."),
            ("Andrés V.", 5, "Me explicaron qué tenía la Dio y qué podía esperar. Honestos.", ""),
        ],
        "cupon": ("Pre-revisión técnico-mecánica gratis con tu cambio de aceite",
                  "Revisamos luces, frenos, llantas y emisiones antes de ir al CDA. Motos hasta 200 cc.", 60, 40),
    },
    {
        "clave": "torquesur",
        "datos": {
            "nombre": "Torque Sur Motos",
            "responsable": "Andrés Felipe Restrepo",
            "direccion": "Calle 38 Sur # 44-15, Envigado",
            "barrio": ("Centro", "Envigado"),
            "horario": "Lun-Sáb 7:30am-6:30pm",
            "nivel_precio": 2,
            "verificado": True, "destacado": False, "agenda_activa": True,
            "atiende_emergencias": True, "despinche_domicilio": True,
            "latitud": Decimal("6.171230"), "longitud": Decimal("-75.588940"),
            "descripcion": ("Taller de media y alta cilindrada en el centro de Envigado. Duke, Pulsar NS, FZ 25, MT-03, "
                            "Gixxer y trail: si la usas en carretera, aquí la dejamos lista."),
            "equipo": [
                {"nombre": "Andrés Felipe Restrepo", "rol": "Jefe de taller", "anios": 15, "especialidad": "KTM y Bajaj"},
                {"nombre": "Luisa Fernanda Gil", "rol": "Técnica eléctrica", "anios": 9,
                 "especialidad": "Sistema eléctrico y diagnóstico con escáner"},
                {"nombre": "Camilo Zapata", "rol": "Técnico", "anios": 7,
                 "especialidad": "Suspensiones y frenos de alto rendimiento"},
            ],
            "especialidades": ["alta", "trail", "suspension", "electrico", "arrastre", "tecnomecanica"],
            "garantia_meses": 2,
            "compromisos": ["presupuesto", "avisamos", "factura", "fotos"],
        },
        "servicios": ["Mantenimiento general", "Cambio de aceite", "Frenos", "Sistema eléctrico", "Suspensión",
                      "Llantas", "Revisión técnico-mecánica", "Kit de arrastre", "Sincronización"],
        "marcas": ["KTM", "Auteco Bajaj", "Yamaha", "Honda", "Suzuki", "Hero"],
        "horarios": [(d, time(7, 30), time(18, 30)) for d in range(6)],
        "precios": PRECIOS_TORQUE_SUR,
        "fotos": [("torquesur-1.webp", "Carburación y ajuste fino"),
                  ("torquesur-2.webp", "Mantenimiento en el elevador"),
                  ("torquesur-3.webp", "Centrado de rueda de radios"),
                  ("torquesur-4.webp", "Revisión de motor")],
        "video": ("torquesur-video.mp4", "torquesur-video.webp", "Ajuste de rueda trasera"),
        "resenas": [
            ("Santiago P.", 5, "Les llevé la Duke 200 con la suspensión rebotando. Quedó como nueva y me "
                               "explicaron cada cosa.", ""),
            ("Natalia H.", 4, "Muy profesionales con mi MT-03. No es el más barato, pero el trabajo vale la pena.",
             "Gracias Natalia. Usamos repuestos originales o equivalentes de buena marca, por eso el precio."),
            ("Julián O.", 5, "Me pinché un domingo por la Avenida El Poblado y vinieron a despincharme en 40 "
                             "minutos.", ""),
            ("Camila T.", 2, "Me cotizaron una cosa y al final salió más cara por un repuesto que no tenían en "
                             "cuenta.",
             "Camila, qué pena. Desde ahora te escribimos antes de cambiar cualquier pieza que no esté cotizada."),
            ("Mauricio L.", 5, "La revisión antes de la técnico-mecánica me salvó: pasé a la primera.", ""),
        ],
        "cupon": ("10% en kit de arrastre para motos de 150 a 400 cc",
                  "Incluye instalación. No acumulable con otras promociones.", 45, 30),
    },
]


def primero_o_crear(modelo, defaults=None, **filtro):
    """Como get_or_create, pero sin fallar si ya hay repetidos (p. ej. dos cupones con el mismo título creados a mano):
    usa el primero que encuentre y nunca borra nada. Devuelve (objeto, creado)."""
    existente = modelo.objects.filter(**filtro).order_by("pk").first()
    if existente:
        return existente, False
    return modelo.objects.create(**filtro, **(defaults or {})), True


def _archivo(campo, nombre, guardar=True):
    """Copia un archivo de talleres/demo/ al almacenamiento de medios (local o el de producción)."""
    with open(CARPETA / nombre, "rb") as f:
        campo.save(nombre, File(f), save=guardar)


def _cuenta(email, nombre):
    User = get_user_model()
    u, creado = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": nombre})
    if creado:  # sin contraseña utilizable: nadie inicia sesión con esta cuenta en producción
        u.set_unusable_password()
        u.save()
    return u


CAMPOS_PERFIL = ("equipo", "especialidades", "garantia_meses", "compromisos")


def completar_perfil(taller, datos):
    """Pasa un taller demo ya cargado a los campos estandarizados sin pisar lo que alguien haya editado: solo llena los
    campos vacíos, y la descripción larga de antes (que traía equipo y especialidades en texto) se cambia por la corta."""
    cambios = [c for c in CAMPOS_PERFIL if not getattr(taller, c) and datos.get(c)]
    for c in cambios:
        setattr(taller, c, datos[c])
    if len(taller.descripcion) > 300 and "Quiénes te atienden" in taller.descripcion:
        taller.descripcion = datos["descripcion"]
        cambios.append("descripcion")
    if cambios:
        taller.save(update_fields=cambios)
    return cambios


def cargar():
    """Crea los dos talleres completos si no existen. Devuelve los talleres creados."""
    from cupones.models import Cupon

    for t in TALLERES:  # los del directorio ya existen; se suman SERVICIOS_EXTRA (y lo que falte en una base vacía)
        for nombre in t["servicios"]:
            Servicio.objects.get_or_create(nombre=nombre)
        for nombre in t["marcas"]:
            Marca.objects.get_or_create(nombre=nombre)
    hoy = timezone.localdate()
    creados = []
    for t in TALLERES:
        datos = dict(t["datos"])
        barrio = primero_o_crear(Barrio, nombre=datos["barrio"][0], ciudad=datos["barrio"][1])[0]
        datos.update(barrio=barrio, whatsapp="573000000000", activo=True,
                     usuario=_cuenta(f"{t['clave']}.demo@tallerya.local", datos["nombre"]))
        existente = Taller.objects.filter(nombre=datos["nombre"]).order_by("pk").first()
        if existente:
            completar_perfil(existente, t["datos"])
            continue
        taller = Taller(**datos)
        _archivo(taller.foto, f"{t['clave']}-portada.webp", guardar=False)
        taller.save()
        taller.servicios.set(Servicio.objects.filter(nombre__in=t["servicios"]))
        taller.marcas.set(Marca.objects.filter(nombre__in=t["marcas"]))
        HorarioTaller.objects.bulk_create(HorarioTaller(taller=taller, dia=d, abre=a, cierra=c)
                                          for d, a, c in t["horarios"])
        servicios = {s.nombre: s for s in Servicio.objects.all()}
        PrecioServicio.objects.bulk_create(
            PrecioServicio(taller=taller, servicio=servicios[s], cilindraje=c, desde=d, hasta=h)
            for s, c, d, h in t["precios"])
        for i, (archivo, texto) in enumerate(t["fotos"]):
            f = FotoTaller(taller=taller, descripcion=texto, orden=i)
            _archivo(f.imagen, archivo, guardar=False)
            f.save()
        video, poster, texto = t["video"]
        f = FotoTaller(taller=taller, descripcion=texto, orden=1)  # el video sale segundo en la portada
        _archivo(f.video, video, guardar=False)
        _archivo(f.imagen, poster, guardar=False)
        f.save()
        for nombre, estrellas, comentario, respuesta in t["resenas"]:
            Resena.objects.create(taller=taller, nombre=nombre, estrellas=estrellas, comentario=comentario,
                                  respuesta=respuesta, respondida_en=timezone.now() if respuesta else None)
        titulo, condiciones, dias, cupo = t["cupon"]
        primero_o_crear(Cupon, titulo=titulo, defaults={
            "taller": taller, "condiciones": condiciones, "valido_hasta": hoy + timedelta(days=dias), "cupo": cupo})
        creados.append(taller)
    cargar_citas()
    return creados


def cargar_citas():
    """Citas de ejemplo en los dos talleres y un servicio hecho (verificado) en cada moto de la cuenta demo.

    Solo si existen esas motos (cuenta demo del garaje, solo en desarrollo) y una sola vez."""
    from garaje import servicio_taller as st
    from garaje.models import Moto, ServicioTaller, TareaMantenimiento

    leva = Taller.objects.filter(nombre="Taller Doble Leva").first()
    sur = Taller.objects.filter(nombre="Torque Sur Motos").first()
    motos = {m.linea.nombre: m for m in Moto.objects.filter(motociclista__celular="573009990001", linea__isnull=False)
             .select_related("linea", "motociclista__usuario")}
    if not (leva and sur) or ServicioTaller.objects.filter(taller__in=[leva, sur]).exists():
        return
    hoy = timezone.localdate()
    servicio = {s.nombre: s for s in Servicio.objects.all()}

    def cita(taller, nombre, moto, serv, dias, estado, hora, **extra):
        return SolicitudCita.objects.create(taller=taller, nombre=nombre, telefono="3000000000", moto=moto,
                                            servicio=servicio.get(serv), fecha_preferida=hoy + timedelta(days=dias),
                                            hora=time(*hora), estado=estado, **extra)

    E = SolicitudCita.Estado
    # Próximas y de hoy, de clientes de ejemplo (sin cuenta)
    cita(leva, "Wilmar C.", "AKT NKD 125", "Kit de arrastre", 0, E.CONFIRMADA, (9, 0), detalle="Suena la cadena")
    cita(leva, "Paola G.", "Honda Dio 110", "Cambio de aceite", 1, E.PENDIENTE, (10, 30))
    cita(leva, "Esteban R.", "Yamaha FZ 2.0", "Sincronización", 3, E.CONFIRMADA, (8, 0))
    cita(sur, "Santiago P.", "KTM Duke 200", "Suspensión", 0, E.CONFIRMADA, (11, 0), detalle="Rebota adelante")
    cita(sur, "Natalia H.", "Yamaha MT-03", "Frenos", 2, E.PENDIENTE, (15, 0))
    cita(sur, "Mauricio L.", "Bajaj Pulsar NS 200", "Revisión técnico-mecánica", -6, E.ATENDIDA, (9, 30))

    tareas = {t.clave: t for t in TareaMantenimiento.objects.all()}
    for taller, linea, serv, dias, km, claves, otros, costo, notas in [
        (leva, "NKD 125", "Cambio de aceite", -10, 15900, ["aceite", "filtro-aire"], "Ajuste y lubricación de cadena",
         165000, "Aceite 20W-50 semisintético. Filtro de aire muy sucio: revisarlo cada 4.000 km por el polvo."),
        (sur, "NMAX 155", "Mantenimiento general", -5, 4250, ["aceite", "aceite-caja"], "",
         98000, "Aceite 10W-40 sintético y aceite de transmisión final. Correa CVT en buen estado."),
    ]:
        moto = motos.get(linea)
        if not moto:
            continue
        usuario = moto.motociclista.usuario
        c = cita(taller, moto.motociclista.nombre, str(moto), serv, dias, E.CONFIRMADA, (9, 0), usuario=usuario)
        st.crear(taller, moto, origen="cita", cita=c, fecha=hoy + timedelta(days=dias), km=km,
                 tareas=[tareas[k] for k in claves if k in tareas], otros=otros, costo=costo, notas=notas)
