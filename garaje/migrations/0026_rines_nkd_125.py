"""AKT NKD 125: rines de 18" adelante y atrás (llantas 2.75-18 y 3.0-18; manual de usuario NKD CBS, págs. 29 y 54)."""
from django.db import migrations


def corregir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(nombre="NKD 125", marca__nombre="AKT").update(
        rin_delantero=18, rin_trasero=18)


def revertir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(nombre="NKD 125", marca__nombre="AKT").update(
        rin_delantero=17, rin_trasero=17)


class Migration(migrations.Migration):
    dependencies = [("garaje", "0025_despiece_especificaciones")]
    operations = [migrations.RunPython(corregir, revertir)]
