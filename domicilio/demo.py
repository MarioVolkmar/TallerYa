"""Mecánicos a domicilio de demostración (ficticios: nombres con «(demo)» y celulares 57300000010X que no existen).

Lo llama talleres/management/commands/cargar_demo.py (CARGAR_DEMO=1 en build.sh) y el comando
`manage.py cargar_demo_domicilio`. Idempotente: busca por nombre y no duplica.
"""
from django.contrib.auth import get_user_model

from talleres.models import Marca, Taller

from .models import FotoTrabajo, MecanicoDomicilio, PrecioMecanico, ResenaMecanico, TallerDomicilio, TipoServicio, Zona

# nombre, celular, años, urgencias, tarifa, horario, zonas, servicios, marcas, estado, verificado, descripción
MECANICOS = [
    ("Wilson Arango (demo)", "573000000101", 14, True, 30000, "Lun-Sáb 7am-7pm",
     ["Robledo", "Castilla", "Doce de Octubre", "Bello"],
     ["Mantenimiento general", "Frenos", "Sistema eléctrico", "Diagnóstico", "Batería y arranque"], ["AKT", "Auteco Bajaj", "Honda"],
     "aprobado", True, "Perfil de ejemplo. 14 años en motos de trabajo. Llevo herramienta, multímetro y escáner básico."),
    ("Yeison Cardona (demo)", "573000000102", 6, True, 25000, "Todos los días 6am-10pm",
     ["El Poblado", "Envigado", "Sabaneta", "Itagüí"],
     ["Llantas y despinche", "Batería y arranque", "Kit de arrastre", "Frenos"], ["Yamaha", "Suzuki"],
     "aprobado", False, "Perfil de ejemplo. Despinche y arranque de batería donde te varaste. Scooters y motos hasta 250 cc."),
    ("Luz Dary Gómez (demo)", "573000000103", 10, False, 40000, "Lun-Vie 8am-5pm",
     ["Laureles-Estadio", "La América", "Belén", "Guayabal"],
     ["Inyección electrónica", "Diagnóstico", "Sistema eléctrico"], ["Yamaha", "Honda", "TVS"],
     "aprobado", True, "Perfil de ejemplo. Especialista en inyección y fallas eléctricas. Diagnóstico con escáner en tu casa."),
    ("Jhon Fredy Ospina (demo)", "573000000104", 20, False, 20000, "Lun-Sáb 8am-6pm",
     ["Manrique", "Aranjuez", "Popular", "Santa Cruz", "Copacabana"],
     ["Carburación", "Mantenimiento general", "Cambio de aceite", "Kit de arrastre"], ["AKT", "Auteco Bajaj", "Suzuki"],
     "aprobado", False, "Perfil de ejemplo. Toda la vida en motos de carburador. Sincronización y mantenimiento sin salir de casa."),
    ("Andrés Zuluaga (demo)", "573000000105", 4, True, None, "Noches y fines de semana",
     ["La Estrella", "Caldas", "Itagüí", "Sabaneta"],
     ["Cambio de aceite", "Llantas y despinche", "Revisión antes de comprar moto usada"], [],
     "aprobado", False, "Perfil de ejemplo. Te acompaño a revisar una moto usada antes de comprarla."),
    ("Mauricio Henao (demo)", "573000000106", 8, False, 35000, "Lun-Sáb 9am-6pm",
     ["Buenos Aires", "Villa Hermosa", "La Candelaria (Centro)"],
     ["Suspensión", "Frenos", "Mantenimiento general"], ["KTM", "Yamaha"],
     "pendiente", False, "Perfil de ejemplo pendiente de revisión: no sale en el listado hasta que se apruebe."),
]

RESENAS = [  # (mecánico, estrellas, comentario): las firma la cuenta demo del garaje si existe
    ("Wilson Arango (demo)", 5, "Llegó en 40 minutos y encontró el corto en el arnés. Muy claro con el precio."),
    ("Luz Dary Gómez (demo)", 5, "Me escaneó la NMAX en el parqueadero del trabajo. Recomendada."),
    ("Yeison Cardona (demo)", 4, "Me despinchó en la vía a Las Palmas. Cobró lo acordado."),
]


# Lo que completa la ficha (mismas listas cerradas que el perfil del taller): especialidades, cómo trabaja,
# garantía (meses), herramientas. Se rellena también en perfiles demo ya creados si están vacíos.
FICHA = {
    "Wilson Arango (demo)": (["trabajo", "electrico", "frenos"], ["presupuesto", "fotos", "piezas"], 1,
                             "escáner básico, multímetro, gato de moto, llaves de torque"),
    "Yeison Cardona (demo)": (["scooters", "arrastre"], ["presupuesto", "avisamos"], None,
                              "compresor portátil, kit de despinche, arrancador de batería"),
    "Luz Dary Gómez (demo)": (["inyeccion", "electrico", "scooters"], ["fotos", "presupuesto", "factura"], 3,
                              "escáner multimarca, multímetro, probador de inyectores"),
    "Jhon Fredy Ospina (demo)": (["carburacion", "trabajo", "motor"], ["piezas", "presupuesto"], 1,
                                 "juego de llaves, sincronizador de carburador, gato de moto"),
    "Andrés Zuluaga (demo)": (["trabajo"], ["fotos", "avisamos"], None, "linterna, multímetro, lista de chequeo"),
    "Mauricio Henao (demo)": (["suspension", "alta"], ["presupuesto"], None, "herramienta de suspensión"),
}

# Precios «desde–hasta» de ejemplo (servicio, cilindraje, desde, hasta); cilindraje: "", baja, media, alta
PRECIOS = {
    "Wilson Arango (demo)": [("Mantenimiento general", "baja", 60000, 90000), ("Mantenimiento general", "media", 90000, 140000),
                             ("Frenos", "baja", 35000, 60000), ("Frenos", "media", 50000, 80000),
                             ("Sistema eléctrico", "", 40000, 120000)],
    "Yeison Cardona (demo)": [("Llantas y despinche", "baja", 15000, 25000), ("Llantas y despinche", "media", 20000, 35000),
                              ("Batería y arranque", "", 20000, 40000), ("Kit de arrastre", "baja", 30000, 45000)],
    "Luz Dary Gómez (demo)": [("Diagnóstico", "", 50000, 80000), ("Inyección electrónica", "baja", 80000, 150000),
                              ("Inyección electrónica", "media", 120000, 220000), ("Inyección electrónica", "alta", 180000, 320000)],
    "Jhon Fredy Ospina (demo)": [("Carburación", "baja", 40000, 70000), ("Cambio de aceite", "baja", 15000, 20000),
                                 ("Mantenimiento general", "baja", 55000, 85000)],
    "Andrés Zuluaga (demo)": [("Revisión antes de comprar moto usada", "", 50000, 70000), ("Cambio de aceite", "", 15000, 25000)],
}
RESPUESTAS = {  # mecánico → respuesta a su reseña demo
    "Wilson Arango (demo)": "¡Gracias, Sofía! Cualquier cosa con la moto, me escribes.",
}

# Talleres demo de cargar_demo que también van a domicilio: taller, zonas, servicios, tarifa, urgencias
TALLERES = [
    ("MotoServicio El Paisa", ["Belén", "Guayabal", "La América", "Laureles-Estadio"],
     ["Mantenimiento general", "Cambio de aceite", "Frenos", "Diagnóstico"], 30000, False),
    ("Clínica de Motos Bello", ["Bello", "Castilla", "Doce de Octubre", "Copacabana"],
     ["Batería y arranque", "Llantas y despinche", "Sistema eléctrico", "Mantenimiento general"], 25000, True),
]


def imagenes(stdout=None):
    """Avatar ilustrado y 3 ilustraciones de trabajos (según sus servicios) para los mecánicos demo que no tengan.
    Dibujos propios (domicilio/ilustraciones.py): sin fotos de personas ni imágenes de internet."""
    from . import ilustraciones
    n = 0
    for i, m in enumerate(MecanicoDomicilio.objects.filter(nombre__endswith="(demo)").prefetch_related("servicios")):
        if not m.foto:
            m.foto.save("avatar.jpg", ilustraciones.avatar(m.iniciales, tono=i), save=True)
            n += 1
        if not m.fotos_trabajo.exists():
            for s in list(m.servicios.all())[:3]:
                FotoTrabajo.objects.create(mecanico=m, imagen=ilustraciones.trabajo(s.nombre))
    return n


def cargar_talleres():
    """Activa «También atiendo a domicilio» en 2 talleres demo (si existen). Idempotente."""
    zonas = {z.nombre: z for z in Zona.objects.all()}
    servicios = {s.nombre: s for s in TipoServicio.objects.all()}
    n = 0
    for nombre, z, s, tarifa, urgencias in TALLERES:
        taller = Taller.objects.filter(nombre=nombre).first()
        if not taller:
            continue
        d, creado = TallerDomicilio.objects.get_or_create(taller=taller, defaults={
            "activo": True, "tarifa_visita": tarifa, "urgencias": urgencias})
        if creado:
            d.zonas.set([zonas[x] for x in z if x in zonas])
            d.servicios.set([servicios[x] for x in s if x in servicios])
            n += 1
    return n


def cargar(stdout=None):
    zonas = {z.nombre: z for z in Zona.objects.all()}
    servicios = {s.nombre: s for s in TipoServicio.objects.all()}
    creados = 0
    for (nombre, cel, anios, urg, tarifa, horario, z, s, marcas, estado, verif, desc) in MECANICOS:
        m, creado = MecanicoDomicilio.objects.get_or_create(nombre=nombre, defaults={
            "whatsapp": cel, "anios_experiencia": anios, "urgencias": urg, "tarifa_visita": tarifa, "horario": horario,
            "estado": estado, "verificado": verif, "descripcion": desc})
        if creado:
            creados += 1
            m.zonas.set([zonas[x] for x in z if x in zonas])
            m.servicios.set([servicios[x] for x in s if x in servicios])
            m.marcas.set([Marca.objects.get_or_create(nombre=x)[0] for x in marcas])
    usuario = get_user_model().objects.filter(username="moto.demo@tallerya.local").first()
    if usuario:
        for nombre, estrellas, comentario in RESENAS:
            if m := MecanicoDomicilio.objects.filter(nombre=nombre).first():
                ResenaMecanico.objects.get_or_create(mecanico=m, usuario=usuario, defaults={
                    "nombre": usuario.first_name or "Sofía", "estrellas": estrellas, "comentario": comentario})
    imagenes(stdout)
    servicios = {s.nombre: s for s in TipoServicio.objects.all()}
    for nombre, filas in PRECIOS.items():
        m = MecanicoDomicilio.objects.filter(nombre=nombre).first()
        if m and not m.precios.exists():
            PrecioMecanico.objects.bulk_create([PrecioMecanico(mecanico=m, servicio=servicios[s], cilindraje=c, desde=d, hasta=h)
                                                for s, c, d, h in filas if s in servicios])
    for nombre, texto in RESPUESTAS.items():
        ResenaMecanico.objects.filter(mecanico__nombre=nombre, respuesta="").update(respuesta=texto)
    for m in MecanicoDomicilio.objects.filter(nombre__endswith="(demo)", verificado=True, cedula_huella=""):
        m.poner_cedula(f"9{m.whatsapp[-9:]}")  # cédula ficticia (solo se guarda la huella y 4 dígitos)
        m.referencias = m.referencias or "Referencias de ejemplo (perfil demo)."
        m.save(update_fields=["cedula_huella", "cedula_ultimos", "referencias", "actualizado"])
    for nombre, (esp, comp, garantia, herramientas) in FICHA.items():
        MecanicoDomicilio.objects.filter(nombre=nombre, especialidades=[], compromisos=[], herramientas="").update(
            especialidades=esp, compromisos=comp, garantia_meses=garantia, herramientas=herramientas)
    MecanicoDomicilio.objects.filter(nombre="Mauricio Henao (demo)", nota_al_mecanico="").update(
        nota_al_mecanico="Perfil de ejemplo: sube una foto tuya y fotos de trabajos para revisarlo más rápido.")
    talleres = cargar_talleres()
    if stdout:
        stdout.write(f"Mecánicos a domicilio demo: {creados} nuevos ({len(MECANICOS)} en total); "
                     f"{talleres} taller(es) demo con domicilio.")
    return creados
