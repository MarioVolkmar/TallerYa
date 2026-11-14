from datetime import date

from django.db import migrations

# Rotación de motos en Medellín, segundo semestre de 2026 (rige desde el 3 de agosto; cuenta el primer número de la placa).
FUENTE_URL = "https://www.elcolombiano.com/medellin/rotacion-pico-y-placa-medellin-segundo-semestre-de-2026-PP39145875"


def cargar(apps, schema_editor):
    apps.get_model("garaje", "ReglaPicoPlaca").objects.get_or_create(
        ciudad="Medellín", vigente_desde=date(2026, 8, 3),
        defaults=dict(digito="primero", lunes="5,8", martes="1,4", miercoles="0,2", jueves="3,6", viernes="7,9",
                      horario="5:00 a. m. a 8:00 p. m.", fuente="Alcaldía de Medellín (vía El Colombiano)", fuente_url=FUENTE_URL))


def quitar(apps, schema_editor):
    apps.get_model("garaje", "ReglaPicoPlaca").objects.filter(ciudad="Medellín", vigente_desde=date(2026, 8, 3)).delete()


class Migration(migrations.Migration):
    dependencies = [("garaje", "0013_pico_placa")]
    operations = [migrations.RunPython(cargar, quitar)]
