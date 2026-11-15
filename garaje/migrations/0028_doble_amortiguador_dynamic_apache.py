"""Dos amortiguadores traseros según su catálogo de despiece:
- AKT Dynamic Pro 125 (AK 125SC PRO: "Amortiguador trasero sc pro", cantidad 2).
- TVS Apache RTR 160 (la 2V del catálogo: "Amortiguador (negro)", cantidad 2; la 4V es la monoamortiguador).
"""
from django.db import migrations

LINEAS = [("AKT", "Dynamic Pro 125"), ("TVS", "Apache RTR 160")]


def _poner(apps, valor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    for marca, nombre in LINEAS:
        LineaMoto.objects.filter(marca__nombre=marca, nombre=nombre).update(suspension_trasera=valor)


def corregir(apps, schema_editor):
    _poner(apps, "doble")


def revertir(apps, schema_editor):
    _poner(apps, "mono")


class Migration(migrations.Migration):
    dependencies = [("garaje", "0027_aerox_doble_amortiguador")]
    operations = [migrations.RunPython(corregir, revertir)]
