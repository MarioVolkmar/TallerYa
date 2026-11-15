"""Hero Hunk 150 (2012) en el catálogo de líneas. Ficha según el catálogo de piezas HCML Colombia (ago-2012):
llantas 2.75-18 y 100/90-18, freno delantero de disco, trasero de tambor (hay versión de disco) y doble amortiguador."""
from django.db import migrations

HUNK = dict(tipo="calle", cilindraje=149, transmision="cadena", refrigeracion="aire", freno_delantero="disco",
            freno_trasero="tambor", suspension_trasera="doble", rin_delantero=18, rin_trasero=18, carenado=False)


def agregar(apps, schema_editor):
    Marca = apps.get_model("talleres", "Marca")
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    hero, _ = Marca.objects.get_or_create(nombre="Hero")
    LineaMoto.objects.update_or_create(marca=hero, nombre="Hunk 150", defaults=HUNK)


def quitar(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(marca__nombre="Hero", nombre="Hunk 150", motos__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("garaje", "0032_siete_lineas_nuevas")]
    operations = [migrations.RunPython(agregar, quitar)]
