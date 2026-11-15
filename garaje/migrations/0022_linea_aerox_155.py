"""Yamaha Aerox 155 en el catálogo de líneas (scooter deportivo, misma plataforma 155 cc VVA de la NMAX)."""
from django.db import migrations

AEROX = dict(nombre="Aerox 155", tipo="scooter", cilindraje=155, transmision="cvt", refrigeracion="liquido",
             freno_delantero="disco", freno_trasero="tambor", suspension_trasera="mono", rin_delantero=14, rin_trasero=14,
             carenado=False)


def agregar(apps, schema_editor):
    Marca = apps.get_model("talleres", "Marca")
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    yamaha, _ = Marca.objects.get_or_create(nombre="Yamaha")
    datos = dict(AEROX)
    LineaMoto.objects.update_or_create(marca=yamaha, nombre=datos.pop("nombre"), defaults=datos)


def quitar(apps, schema_editor):
    apps.get_model("garaje", "LineaMoto").objects.filter(marca__nombre="Yamaha", nombre="Aerox 155").delete()


class Migration(migrations.Migration):
    dependencies = [("garaje", "0021_codigo_ligado_a_registro")]
    operations = [migrations.RunPython(agregar, quitar)]
