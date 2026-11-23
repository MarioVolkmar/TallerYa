from django.db import migrations, models


def marcar(apps, schema_editor):
    # Las coordenadas que ya existen las puso el taller (GPS) o son de demostración: se toman como buenas
    apps.get_model("talleres", "Taller").objects.filter(latitud__isnull=False, longitud__isnull=False).update(ubicacion_exacta=True)


class Migration(migrations.Migration):
    dependencies = [("talleres", "0026_equipo_catalogo")]
    operations = [
        migrations.AddField(model_name="taller", name="ubicacion_exacta", field=models.BooleanField(default=False)),
        migrations.RunPython(marcar, migrations.RunPython.noop),
    ]
