"""Rines según los manuales del propietario:
- Hero Eco Deluxe 100: 2.75-18 adelante y atrás → 18/18.
- AKT Dynamic Pro 125 (2021): 120/70-12 adelante y 130/70-12 atrás → trasero 12.
"""
from django.db import migrations

CAMBIOS = [("Hero", "Eco Deluxe 100", {"rin_delantero": 18, "rin_trasero": 18}, {"rin_delantero": 17, "rin_trasero": 17}),
           ("AKT", "Dynamic Pro 125", {"rin_trasero": 12}, {"rin_trasero": 10})]


def corregir(apps, schema_editor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    for marca, nombre, nuevo, _ in CAMBIOS:
        LineaMoto.objects.filter(marca__nombre=marca, nombre=nombre).update(**nuevo)


def revertir(apps, schema_editor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    for marca, nombre, _, viejo in CAMBIOS:
        LineaMoto.objects.filter(marca__nombre=marca, nombre=nombre).update(**viejo)


class Migration(migrations.Migration):
    dependencies = [("garaje", "0028_doble_amortiguador_dynamic_apache")]
    operations = [migrations.RunPython(corregir, revertir)]
