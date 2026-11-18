"""Mecánicos a domicilio de demostración (ficticios: nombres con «(demo)» y celulares 57300000010X que no existen).

Lo llama talleres/management/commands/cargar_demo.py (CARGAR_DEMO=1 en build.sh) y el comando
`manage.py cargar_demo_domicilio`. Idempotente: busca por nombre y no duplica.
"""
from django.contrib.auth import get_user_model

from talleres.models import Marca

from .models import MecanicoDomicilio, ResenaMecanico, TipoServicio, Zona

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
    if stdout:
        stdout.write(f"Mecánicos a domicilio demo: {creados} nuevos ({len(MECANICOS)} en total).")
    return creados
