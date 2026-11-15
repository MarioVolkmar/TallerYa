"""Honda Dio 110: 90/100-10 adelante y atrás (manual de mantenimiento; catálogo SCV110F) → rin delantero 10."""
from django.db import migrations


def corregir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(marca__nombre="Honda", nombre="Dio 110").update(rin_delantero=10)


def revertir(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(marca__nombre="Honda", nombre="Dio 110").update(rin_delantero=12)


class Migration(migrations.Migration):
    dependencies = [("garaje", "0029_rines_eco_deluxe_dynamic")]
    operations = [migrations.RunPython(corregir, revertir)]
