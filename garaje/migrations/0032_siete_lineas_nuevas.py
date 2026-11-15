"""Siete líneas más vendidas en Colombia que faltaban (Andemos 2025): XR190L, DR150, XTZ150, Raider 125, FZ 2.0,
Hunk 125R y Boxer CT125. Fichas según el manual y el catálogo de partes de cada una (ver informes_noche/motos-nuevas.md)."""
from django.db import migrations

# marca, línea, tipo, cc, transmisión, refrigeración, freno del, freno tras, suspensión tras, rin del, rin tras, carenado
LINEAS = [
    ("Honda", "XR 190L", "enduro", 184, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("Suzuki", "DR 150", "enduro", 149, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("Yamaha", "XTZ 150", "enduro", 149, "cadena", "aire", "disco", "tambor", "mono", 19, 17, False),
    ("TVS", "Raider 125", "calle", 125, "cadena", "aire", "disco", "tambor", "mono", 17, 17, False),
    ("Yamaha", "FZ 2.0", "calle", 149, "cadena", "aire", "disco", "disco", "mono", 17, 17, False),
    ("Hero", "Hunk 125R", "calle", 125, "cadena", "aire", "disco", "tambor", "mono", 17, 17, False),
    ("Auteco Bajaj", "Boxer CT 125", "calle", 125, "cadena", "aire", "tambor", "tambor", "doble", 17, 17, False),
]
CAMPOS = ("tipo", "cilindraje", "transmision", "refrigeracion", "freno_delantero", "freno_trasero",
          "suspension_trasera", "rin_delantero", "rin_trasero", "carenado")


def agregar(apps, schema_editor):
    Marca = apps.get_model("talleres", "Marca")
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    for marca, nombre, *valores in LINEAS:
        m, _ = Marca.objects.get_or_create(nombre=marca)
        LineaMoto.objects.update_or_create(marca=m, nombre=nombre, defaults=dict(zip(CAMPOS, valores)))


def quitar(apps, schema_editor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    for marca, nombre, *_ in LINEAS:
        LineaMoto.objects.filter(marca__nombre=marca, nombre=nombre, motos__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("garaje", "0031_servicio_taller")]
    operations = [migrations.RunPython(agregar, quitar)]
