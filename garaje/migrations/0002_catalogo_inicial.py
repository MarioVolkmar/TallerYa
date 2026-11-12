"""Catálogo inicial de líneas populares en Colombia y plan de mantenimiento orientativo.

Las fichas e intervalos son aproximados y se ajustan desde el admin.
"""
from django.db import migrations

# marca, línea, tipo, cc, transmisión, refrigeración, freno del, freno tras, suspensión tras, rin del, rin tras, carenado
LINEAS = [
    ("AKT", "NKD 125", "calle", 125, "cadena", "aire", "disco", "tambor", "doble", 17, 17, False),
    ("AKT", "CR4 125", "calle", 125, "cadena", "aire", "disco", "tambor", "mono", 17, 17, False),
    ("AKT", "TT 125 DS", "enduro", 125, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("AKT", "Dynamic Pro 125", "scooter", 125, "cvt", "aire", "disco", "tambor", "mono", 12, 10, False),
    ("Auteco Bajaj", "Boxer CT 100", "calle", 100, "cadena", "aire", "tambor", "tambor", "doble", 17, 17, False),
    ("Auteco Bajaj", "Discover 125", "calle", 125, "cadena", "aire", "disco", "tambor", "doble", 17, 17, False),
    ("Auteco Bajaj", "Pulsar NS 200", "calle", 200, "cadena", "liquido", "disco", "disco", "mono", 17, 17, False),
    ("Auteco Bajaj", "Pulsar RS 200", "sport", 200, "cadena", "liquido", "disco", "disco", "mono", 17, 17, True),
    ("Honda", "CB 125F", "calle", 125, "cadena", "aire", "disco", "tambor", "doble", 18, 18, False),
    ("Honda", "XR 150L", "enduro", 150, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("Honda", "Dio 110", "scooter", 110, "cvt", "aire", "tambor", "tambor", "mono", 12, 10, False),
    ("Honda", "Wave 110S", "semi", 110, "cadena", "aire", "tambor", "tambor", "doble", 17, 17, False),
    ("Suzuki", "GN 125", "calle", 125, "cadena", "aire", "disco", "tambor", "doble", 18, 17, False),
    ("Suzuki", "Gixxer 150", "calle", 150, "cadena", "aire", "disco", "disco", "mono", 17, 17, False),
    ("Suzuki", "Best 125", "semi", 125, "cadena", "aire", "disco", "tambor", "doble", 17, 17, False),
    ("Yamaha", "NMAX 155", "scooter", 155, "cvt", "liquido", "disco", "disco", "doble", 13, 13, False),
    ("Yamaha", "XTZ 125", "enduro", 125, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("Yamaha", "FZ 25", "calle", 250, "cadena", "aire", "disco", "disco", "mono", 17, 17, False),
    ("Yamaha", "Crypton FI 115", "semi", 115, "cadena", "aire", "disco", "tambor", "doble", 17, 17, False),
    ("Yamaha", "MT-03", "calle", 321, "cadena", "liquido", "disco", "disco", "mono", 17, 17, False),
    ("TVS", "Apache RTR 160", "calle", 160, "cadena", "aire", "disco", "tambor", "mono", 17, 17, False),
    ("KTM", "Duke 200", "calle", 200, "cadena", "liquido", "disco", "disco", "mono", 17, 17, False),
    ("KTM", "RC 200", "sport", 200, "cadena", "liquido", "disco", "disco", "mono", 17, 17, True),
    ("Hero", "Eco Deluxe 100", "calle", 100, "cadena", "aire", "tambor", "tambor", "doble", 17, 17, False),
]

# clave, nombre, descripción, pieza, aplica, km, días, servicio, hazlo tú
TAREAS = [
    ("aceite", "Cambio de aceite", "Aceite de motor y limpieza de la malla o cambio de filtro de aceite.",
     "aceite", "todas", 2500, 120, "Cambio de aceite", False),
    ("cadena-lubricar", "Limpiar y lubricar la cadena", "Con lubricante para cadena. Revisa también la tensión.",
     "cadena", "cadena", 600, 15, "Mantenimiento general", True),
    ("kit-arrastre", "Cambio de kit de arrastre", "Cadena, piñón y corona se cambian juntos.",
     "cadena", "cadena", 18000, None, "Mantenimiento general", False),
    ("correa-cvt", "Revisión de correa y variador", "Correa CVT, rodillos y zapatas del clutch.",
     "correa", "cvt", 12000, None, "Mantenimiento general", False),
    ("filtro-aire", "Cambio de filtro de aire", "En zonas con mucho polvo, revísalo más seguido.",
     "filtro_aire", "todas", 6000, 365, "Mantenimiento general", False),
    ("bujia", "Cambio de bujía", "Una bujía gastada causa mal encendido y más consumo.",
     "bujia", "todas", 8000, None, "Sistema eléctrico", False),
    ("valvulas", "Calibración de válvulas", "Evita pérdida de potencia y ruidos en el motor.",
     "motor", "todas", 6000, None, "Mantenimiento general", False),
    ("pastillas-del", "Pastillas de freno delanteras", "Revisa el desgaste; cámbialas antes de llegar al metal.",
     "freno_del", "disco_del", 6000, None, "Frenos", False),
    ("bandas-del", "Bandas de freno delanteras", "Revisión y ajuste del freno de tambor.",
     "freno_del", "tambor_del", 8000, None, "Frenos", False),
    ("pastillas-tras", "Pastillas de freno traseras", "Revisa el desgaste; cámbialas antes de llegar al metal.",
     "freno_tras", "disco_tras", 8000, None, "Frenos", False),
    ("bandas-tras", "Bandas de freno traseras", "Revisión y ajuste del freno de tambor.",
     "freno_tras", "tambor_tras", 10000, None, "Frenos", False),
    ("liquido-frenos", "Cambio de líquido de frenos", "El líquido absorbe humedad y pierde eficacia con el tiempo.",
     "freno_del", "disco_del", 20000, 730, "Frenos", False),
    ("llanta-del", "Llanta delantera", "Revisa la profundidad del labrado y la presión cada semana.",
     "llanta_del", "todas", 15000, None, "Llantas", False),
    ("llanta-tras", "Llanta trasera", "Se gasta más rápido que la delantera.",
     "llanta_tras", "todas", 12000, None, "Llantas", False),
    ("suspension-del", "Aceite de barras de suspensión", "Cambio de aceite y retenedores de la telescópica.",
     "suspension_del", "todas", 20000, None, "Suspensión", False),
    ("suspension-tras", "Revisión de amortiguadores", "Fugas, rebote excesivo o golpes al pasar huecos.",
     "suspension_tras", "todas", 20000, None, "Suspensión", False),
    ("refrigerante", "Cambio de refrigerante", "Solo motos con radiador. Usa refrigerante, no agua.",
     "refrigeracion", "liquido", 24000, 730, "Mantenimiento general", False),
    ("bateria", "Revisión de batería", "Carga, bornes y nivel. Suele durar entre 2 y 3 años.",
     "bateria", "todas", None, 365, "Sistema eléctrico", False),
]


def cargar(apps, schema_editor):
    Marca = apps.get_model("talleres", "Marca")
    Servicio = apps.get_model("talleres", "Servicio")
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    Tarea = apps.get_model("garaje", "TareaMantenimiento")

    for marca, nombre, tipo, cc, trans, refr, fd, ft, susp, rd, rt, car in LINEAS:
        LineaMoto.objects.get_or_create(
            marca=Marca.objects.get_or_create(nombre=marca)[0], nombre=nombre,
            defaults=dict(tipo=tipo, cilindraje=cc, transmision=trans, refrigeracion=refr, freno_delantero=fd,
                          freno_trasero=ft, suspension_trasera=susp, rin_delantero=rd, rin_trasero=rt, carenado=car),
        )
    for orden, (clave, nombre, desc, pieza, aplica, km, dias, servicio, hazlo_tu) in enumerate(TAREAS):
        Tarea.objects.get_or_create(clave=clave, defaults=dict(
            nombre=nombre, descripcion=desc, pieza=pieza, aplica=aplica, intervalo_km=km, intervalo_dias=dias,
            servicio=Servicio.objects.get_or_create(nombre=servicio)[0], hazlo_tu=hazlo_tu, orden=orden,
        ))


class Migration(migrations.Migration):
    dependencies = [
        ("garaje", "0001_initial"),
        ("talleres", "0003_taller_usuario"),
    ]

    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
