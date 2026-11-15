"""Yamaha Aerox 155: dos amortiguadores traseros (catálogo BVT2: "Amortiguador trasero completo", cantidad 2)."""
from django.db import migrations


def corregir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(nombre="Aerox 155", marca__nombre="Yamaha").update(
        suspension_trasera="doble")


def revertir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(nombre="Aerox 155", marca__nombre="Yamaha").update(
        suspension_trasera="mono")


class Migration(migrations.Migration):
    dependencies = [("garaje", "0026_rines_nkd_125")]
    operations = [migrations.RunPython(corregir, revertir)]
